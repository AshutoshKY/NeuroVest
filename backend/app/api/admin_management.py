"""
Admin Management API
Handles user management, IP blacklist, system toggles, and audit logs
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import logging

from app.core.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.core.redis_client import get_redis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# ==================== SCHEMAS ====================

class DisableUserRequest(BaseModel):
    user_id: int
    reason: str

class BlacklistIPRequest(BaseModel):
    ip_address: str
    reason: str

class SystemToggleRequest(BaseModel):
    toggle_name: str  # e.g., "login_enabled", "signup_enabled"
    enabled: bool


# ==================== HELPER: CHECK ADMIN ====================

def check_admin(current_user: User):
    """Check if user is admin, raise 403 if not"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )


async def log_admin_action(
    db: Session,
    admin_user_id: int,
    action: str,
    target: str,
    changes_json: str,
    ip_address: str
):
    """Log admin action to audit_logs"""
    try:
        db.execute(
            text("""
                INSERT INTO admin_audit_logs 
                (admin_user_id, action, target, changes_json, ip_address, timestamp)
                VALUES (:admin_id, :action, :target, :changes, :ip, NOW())
            """),
            {
                "admin_id": admin_user_id,
                "action": action,
                "target": target,
                "changes": changes_json,
                "ip": ip_address
            }
        )
        db.commit()
    except Exception as e:
        logger.error(f"Failed to log admin action: {e}")


# ==================== USER MANAGEMENT ====================

@router.get("/users")
async def list_users(
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all users (paginated)"""
    check_admin(current_user)
    
    try:
        offset = (page - 1) * limit
        
        result = db.execute(
            text("""
                SELECT id, email, full_name, role, is_active, deleted_at, created_at
                FROM users
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            {"limit": limit, "offset": offset}
        )
        
        users = []
        for row in result:
            users.append({
                "id": row[0],
                "email": row[1],
                "full_name": row[2],
                "role": row[3],
                "is_active": bool(row[4]),
                "deleted_at": str(row[5]) if row[5] else None,
                "created_at": str(row[6])
            })
        
        # Get total count
        count_result = db.execute(text("SELECT COUNT(*) FROM users"))
        total = count_result.scalar()
        
        return {
            "users": users,
            "page": page,
            "limit": limit,
            "total": total
        }
    
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail="Failed to list users")


@router.post("/users/disable")
async def disable_user(
    request: DisableUserRequest,
    current_user: User = Depends(get_current_user),
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    """Disable user account"""
    check_admin(current_user)
    
    try:
        # Don't allow self-disable
        if request.user_id == current_user.id:
            raise HTTPException(status_code=400, detail="Cannot disable your own account")
        
        db.execute(
            text("UPDATE users SET is_active = 0 WHERE id = :user_id"),
            {"user_id": request.user_id}
        )
        db.commit()
        
        # Log action
        await log_admin_action(
            db,
            current_user.id,
            "disable_user",
            f"user_id:{request.user_id}",
            f'{{"reason": "{request.reason}"}}',
            http_request.client.host if http_request else "unknown"
        )
        
        logger.info(f"Admin {current_user.id} disabled user {request.user_id}")
        
        return {"success": True, "message": "User disabled"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling user: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to disable user")


@router.post("/users/enable")
async def enable_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    """Enable user account"""
    check_admin(current_user)
    
    try:
        db.execute(
            text("UPDATE users SET is_active = 1 WHERE id = :user_id"),
            {"user_id": user_id}
        )
        db.commit()
        
        # Log action
        await log_admin_action(
            db,
            current_user.id,
            "enable_user",
            f"user_id:{user_id}",
            "{}",
            http_request.client.host if http_request else "unknown"
        )
        
        logger.info(f"Admin {current_user.id} enabled user {user_id}")
        
        return {"success": True, "message": "User enabled"}
    
    except Exception as e:
        logger.error(f"Error enabling user: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to enable user")


# ==================== IP BLACKLIST MANAGEMENT ====================

@router.get("/ip-blacklist")
async def list_blacklisted_ips(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all blacklisted IPs"""
    check_admin(current_user)
    
    try:
        result = db.execute(
            text("""
                SELECT ip_address, reason, blocked_by_user_id, auto_flagged, blocked_at, is_active
                FROM ip_blacklist
                ORDER BY blocked_at DESC
            """)
        )
        
        ips = []
        for row in result:
            ips.append({
                "ip_address": row[0],
                "reason": row[1],
                "blocked_by": row[2],
                "auto_flagged": bool(row[3]),
                "blocked_at": str(row[4]),
                "is_active": bool(row[5])
            })
        
        return {"ips": ips, "count": len(ips)}
    
    except Exception as e:
        logger.error(f"Error listing blacklisted IPs: {e}")
        raise HTTPException(status_code=500, detail="Failed to list IPs")


@router.post("/ip-blacklist/add")
async def add_ip_to_blacklist(
    request: BlacklistIPRequest,
    current_user: User = Depends(get_current_user),
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    """Add IP to blacklist"""
    check_admin(current_user)
    
    try:
        db.execute(
            text("""
                INSERT INTO ip_blacklist (ip_address, reason, blocked_by_user_id, auto_flagged, is_active)
                VALUES (:ip, :reason, :admin_id, 0, 1)
                ON DUPLICATE KEY UPDATE 
                    reason = :reason,
                    blocked_by_user_id = :admin_id,
                    blocked_at = NOW(),
                    is_active = 1
            """),
            {
                "ip": request.ip_address,
                "reason": request.reason,
                "admin_id": current_user.id
            }
        )
        db.commit()
        
        # Log action
        await log_admin_action(
            db,
            current_user.id,
            "blacklist_ip",
            request.ip_address,
            f'{{"reason": "{request.reason}"}}',
            http_request.client.host if http_request else "unknown"
        )
        
        logger.info(f"Admin {current_user.id} blacklisted IP {request.ip_address}")
        
        return {"success": True, "message": "IP blacklisted"}
    
    except Exception as e:
        logger.error(f"Error blacklisting IP: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to blacklist IP")


@router.delete("/ip-blacklist/{ip_address}")
async def remove_ip_from_blacklist(
    ip_address: str,
    current_user: User = Depends(get_current_user),
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    """Remove IP from blacklist"""
    check_admin(current_user)
    
    try:
        db.execute(
            text("UPDATE ip_blacklist SET is_active = 0 WHERE ip_address = :ip"),
            {"ip": ip_address}
        )
        db.commit()
        
        # Log action
        await log_admin_action(
            db,
            current_user.id,
            "unblock_ip",
            ip_address,
            "{}",
            http_request.client.host if http_request else "unknown"
        )
        
        logger.info(f"Admin {current_user.id} unblocked IP {ip_address}")
        
        return {"success": True, "message": "IP removed from blacklist"}
    
    except Exception as e:
        logger.error(f"Error removing IP from blacklist: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to remove IP")


# ==================== SYSTEM TOGGLES ====================

@router.get("/system-toggles")
async def get_system_toggles(
    current_user: User = Depends(get_current_user)
):
    """Get all system toggles"""
    check_admin(current_user)
    
    try:
        redis = get_redis()
        
        toggles = {
            "login_enabled": redis.get("system:login_enabled") != b"0",
            "signup_enabled": redis.get("system:signup_enabled") != b"0",
            "guest_enabled": redis.get("system:guest_enabled") != b"0",
            "maintenance_mode": redis.get("system:maintenance") == b"1"
        }
        
        return toggles
    
    except Exception as e:
        logger.error(f"Error getting system toggles: {e}")
        raise HTTPException(status_code=500, detail="Failed to get toggles")


@router.post("/system-toggles")
async def set_system_toggle(
    request: SystemToggleRequest,
    current_user: User = Depends(get_current_user),
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    """Set system toggle"""
    check_admin(current_user)
    
    try:
        redis = get_redis()
        
        # Validate toggle name
        valid_toggles = ["login_enabled", "signup_enabled", "guest_enabled", "maintenance"]
        if request.toggle_name not in valid_toggles:
            raise HTTPException(status_code=400, detail="Invalid toggle name")
        
        key = f"system:{request.toggle_name}"
        value = "1" if request.enabled else "0"
        
        redis.set(key, value)
        
        # Log action
        await log_admin_action(
            db,
            current_user.id,
            "set_system_toggle",
            request.toggle_name,
            f'{{"enabled": {str(request.enabled).lower()}}}',
            http_request.client.host if http_request else "unknown"
        )
        
        logger.info(f"Admin {current_user.id} set {request.toggle_name} to {request.enabled}")
        
        return {"success": True, "message": f"Toggle {request.toggle_name} set to {request.enabled}"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting system toggle: {e}")
        raise HTTPException(status_code=500, detail="Failed to set toggle")


# ==================== AUDIT LOGS ====================

@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get audit logs"""
    check_admin(current_user)
    
    try:
        result = db.execute(
            text("""
                SELECT a.id, a.admin_user_id, u.email, a.action, a.target, a.changes_json, 
                       a.ip_address, a.timestamp
                FROM admin_audit_logs a
                LEFT JOIN users u ON a.admin_user_id = u.id
                ORDER BY a.timestamp DESC
                LIMIT :limit
            """),
            {"limit": limit}
        )
        
        logs = []
        for row in result:
            logs.append({
                "id": row[0],
                "admin_user_id": row[1],
                "admin_email": row[2],
                "action": row[3],
                "target": row[4],
                "changes": row[5],
                "ip_address": row[6],
                "timestamp": str(row[7])
            })
        
        return {"logs": logs, "count": len(logs)}
    
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get logs")
