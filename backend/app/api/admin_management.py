"""
Admin Management API
Handles user management, IP blacklist, system toggles, and audit logs

RBAC Rules:
- ADMIN: Can view users, IPs, toggles, audit logs (read-only)
- SUPER_ADMIN: Can modify users, IPs, toggles (mutations)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import logging

from app.core.database import get_db
from app.core.rbac import require_admin, require_super_admin
from app.models.user import User
from app.core.redis_client import get_redis
from app.services.audit_service import AuditService, get_audit_service
from app.models.audit_log import AuditAction, ActionCategory

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


# ==================== LEGACY HELPER (DEPRECATED - USE RBAC) ====================
# The check_admin function is deprecated. Use require_admin or require_super_admin instead.


# ==================== USER MANAGEMENT ====================

@router.get("/users")
async def list_users(
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(require_admin),  # ADMIN or SUPER_ADMIN can view
    db: Session = Depends(get_db)
):
    """List all users (paginated) - Read Only"""
    
    
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
    http_request: Request,
    current_user: User = Depends(require_super_admin),  # SUPER_ADMIN only
    db: Session = Depends(get_db)
):
    """Disable user account - Requires SUPER_ADMIN"""
    
    
    try:
        # Don't allow self-disable
        if request.user_id == current_user.id:
            raise HTTPException(status_code=400, detail="Cannot disable your own account")
        
        db.execute(
            text("UPDATE users SET is_active = 0 WHERE id = :user_id"),
            {"user_id": request.user_id}
        )
        db.commit()
        
        # Log action using new AuditService
        AuditService.log_action(
            db=db,
            actor=current_user,
            action=AuditAction.DISABLE_USER,
            request=http_request,
            action_category=ActionCategory.USER_MANAGEMENT,
            target_type="user",
            target_id=str(request.user_id),
            changes={"reason": request.reason}
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
    http_request: Request,
    current_user: User = Depends(require_super_admin),  # SUPER_ADMIN only
    db: Session = Depends(get_db)
):
    """Enable user account - Requires SUPER_ADMIN"""
    
    
    try:
        db.execute(
            text("UPDATE users SET is_active = 1 WHERE id = :user_id"),
            {"user_id": user_id}
        )
        db.commit()
        
        # Log action using new AuditService
        AuditService.log_action(
            db=db,
            actor=current_user,
            action=AuditAction.ENABLE_USER,
            request=http_request,
            action_category=ActionCategory.USER_MANAGEMENT,
            target_type="user",
            target_id=str(user_id)
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
    current_user: User = Depends(require_admin),  # ADMIN or SUPER_ADMIN can view
    db: Session = Depends(get_db)
):
    """List all blacklisted IPs - Read Only"""
    
    
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
    http_request: Request,
    current_user: User = Depends(require_super_admin),  # SUPER_ADMIN only
    db: Session = Depends(get_db)
):
    """Add IP to blacklist - Requires SUPER_ADMIN"""
    
    
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
        
        # Log action using new AuditService
        AuditService.log_action(
            db=db,
            actor=current_user,
            action=AuditAction.BLACKLIST_IP,
            request=http_request,
            action_category=ActionCategory.SECURITY,
            target_type="ip",
            target_id=request.ip_address,
            changes={"reason": request.reason}
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
    http_request: Request,
    current_user: User = Depends(require_super_admin),  # SUPER_ADMIN only
    db: Session = Depends(get_db)
):
    """Remove IP from blacklist - Requires SUPER_ADMIN"""
    
    
    try:
        db.execute(
            text("UPDATE ip_blacklist SET is_active = 0 WHERE ip_address = :ip"),
            {"ip": ip_address}
        )
        db.commit()
        
        # Log action using new AuditService
        AuditService.log_action(
            db=db,
            actor=current_user,
            action=AuditAction.UNBLOCK_IP,
            request=http_request,
            action_category=ActionCategory.SECURITY,
            target_type="ip",
            target_id=ip_address
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
    current_user: User = Depends(require_admin)  # ADMIN or SUPER_ADMIN can view
):
    """Get all system toggles - Read Only"""
    
    
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
    http_request: Request,
    current_user: User = Depends(require_super_admin),  # SUPER_ADMIN only
    db: Session = Depends(get_db)
):
    """Set system toggle - Requires SUPER_ADMIN"""
    
    
    try:
        redis = get_redis()
        
        # Validate toggle name
        valid_toggles = ["login_enabled", "signup_enabled", "guest_enabled", "maintenance"]
        if request.toggle_name not in valid_toggles:
            raise HTTPException(status_code=400, detail="Invalid toggle name")
        
        key = f"system:{request.toggle_name}"
        value = "1" if request.enabled else "0"
        
        redis.set(key, value)
        
        # Log action using new AuditService
        AuditService.log_action(
            db=db,
            actor=current_user,
            action=AuditAction.MODIFY_TOGGLE,
            request=http_request,
            action_category=ActionCategory.CONFIG,
            target_type="toggle",
            target_id=request.toggle_name,
            changes={"enabled": request.enabled}
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
    current_user: User = Depends(require_admin),  # ADMIN or SUPER_ADMIN can view
    db: Session = Depends(get_db)
):
    """Get audit logs - Read Only"""
    
    
    try:
        # Query from new enhanced audit_logs table (with fallback to old table)
        result = db.execute(
            text("""
                SELECT a.id, a.actor_id, a.actor_email, a.actor_role, a.action, 
                       a.action_category, a.target_type, a.target_id, a.changes_json, 
                       a.ip_address, a.success, a.created_at
                FROM audit_logs a
                ORDER BY a.created_at DESC
                LIMIT :limit
            """),
            {"limit": limit}
        )
        
        logs = []
        for row in result:
            logs.append({
                "id": row[0],
                "actor_id": row[1],
                "actor_email": row[2],
                "actor_role": row[3],
                "action": row[4],
                "action_category": row[5],
                "target_type": row[6],
                "target_id": row[7],
                "changes": row[8],
                "ip_address": row[9],
                "success": bool(row[10]),
                "timestamp": str(row[11])
            })
        
        return {"logs": logs, "count": len(logs)}
    
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get logs")
