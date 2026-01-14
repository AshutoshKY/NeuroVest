"""
Admin Dashboard API

Unified endpoint providing a comprehensive system overview for the admin dashboard.
Aggregates data from all admin services for single-fetch dashboard loading.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any, List
from datetime import datetime, timezone
from loguru import logger

from app.core.rbac import require_admin
from app.models.user import User
from app.services.metrics_collector import MetricsCollector, InfraMetricsCollector
from app.services.ai_metrics import AIMetricsService
from app.services.external_api_metrics import ExternalAPIMetricsService
from app.services.kill_switch import get_all_switches
from app.services.session_control import get_session_control_status
from app.services.health_score import SREHealthService, HealthState
from app.core.redis_client import get_redis


router = APIRouter(prefix="/admin/dashboard", tags=["admin-dashboard"])


@router.get("/overview")
async def get_dashboard_overview(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get comprehensive admin dashboard overview.
    
    Single endpoint to fetch all key metrics for the main admin dashboard.
    Returns:
    - System health status
    - Infrastructure metrics (Redis, MySQL, ChromaDB)
    - Request/traffic metrics
    - AI/RAG usage and costs
    - Kill switch states
    - Session control status
    - Active user counts
    """
    try:
        # 1. Infrastructure Health
        infra = InfraMetricsCollector.get_all_infrastructure_metrics()
        
        # Determine overall health
        health_checks = [
            infra.get("redis", {}).get("connected", False),
            infra.get("mysql", {}).get("connected", False),
            infra.get("chromadb", {}).get("connected", False)
        ]
        overall_health = "healthy" if all(health_checks) else "degraded" if any(health_checks) else "down"
        
        # 2. Request Metrics (last hour)
        request_metrics = MetricsCollector.get_request_metrics(minutes=60)
        
        # 3. AI Metrics (today)
        ai_summary = AIMetricsService.get_daily_summary()
        
        # 4. Kill Switch Status
        kill_switches = get_all_switches()
        active_switches = [name for name, switch in kill_switches.items() if switch.is_active]
        
        # 5. Session Status
        session_status = get_session_control_status()
        
        # 6. Active Users (from Redis)
        redis = get_redis()
        active_users = 0
        guest_sessions = 0
        rate_limited_users = 0
        try:
            # Count unique authenticated users from rate limit keys (pattern: rate_limit:user:user:<id>:*)
            user_keys = redis.keys("rate_limit:user:user:*")
            unique_user_ids = set()
            for k in user_keys:
                key_str = k if isinstance(k, str) else k.decode()
                parts = key_str.split(":")
                if len(parts) >= 4:
                    unique_user_ids.add(parts[3])  # user id
            active_users = len(unique_user_ids)
            
            # Count guest sessions (pattern: rate_limit:guest:session:*)
            guest_keys = redis.keys("rate_limit:guest:session:*")
            guest_session_ids = set()
            for k in guest_keys:
                key_str = k if isinstance(k, str) else k.decode()
                parts = key_str.split(":")
                if len(parts) >= 4:
                    guest_session_ids.add(parts[3])  # session id
            guest_sessions = len(guest_session_ids)
            
            # Count blacklisted IPs
            blacklisted = redis.scard("security:ip_blacklist") or 0
        except Exception as e:
            logger.debug(f"[ADMIN_DASHBOARD] Error counting users: {e}")
            blacklisted = 0
        
        # Fetch security events from Redis
        try:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            security_events_today = {
                "rate_limit": int(redis.get(f"security:events:{today}:rate_limit") or 0),
                "blocked_ip": int(redis.get(f"security:events:{today}:blocked_ip") or 0),
                "auth_failure": int(redis.get(f"security:events:{today}:auth_failure") or 0),
                "invalid_token": int(redis.get(f"security:events:{today}:invalid_token") or 0),
                "other": int(redis.get(f"security:events:{today}:other") or 0)
            }
        except Exception as e:
            logger.debug(f"[ADMIN_DASHBOARD] Error fetching security events: {e}")
            security_events_today = {"rate_limit": 0, "blocked_ip": 0, "auth_failure": 0, "invalid_token": 0, "other": 0}
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_health": overall_health,
            
            # System Status
            "system": {
                "uptime": "N/A",  # Would need to track startup time
                "active_kill_switches": len(active_switches),
                "kill_switch_names": active_switches,
                "auth_epoch": session_status.get("auth_epoch"),
                "maintenance_mode": "maintenance_mode" in active_switches
            },
            
            # Infrastructure
            "infrastructure": {
                "redis": {
                    "status": "healthy" if infra.get("redis", {}).get("connected") else "down",
                    "memory_mb": infra.get("redis", {}).get("memory_used_mb", 0),
                    "connections": infra.get("redis", {}).get("connected_clients", 0),
                    "hit_rate": infra.get("redis", {}).get("hit_rate_percent", 0)
                },
                "mysql": {
                    "status": "healthy" if infra.get("mysql", {}).get("connected") else "down",
                    "connections": infra.get("mysql", {}).get("threads_connected", 0),
                    "tables": infra.get("mysql", {}).get("table_count", 0),
                    "rows": infra.get("mysql", {}).get("total_rows", 0)
                },
                "chromadb": {
                    "status": "healthy" if infra.get("chromadb", {}).get("connected") else "down",
                    "documents": infra.get("chromadb", {}).get("document_count", 0),
                    "collections": len(infra.get("chromadb", {}).get("collections", []))
                }
            },
            
            # Traffic (with hourly history for charts)
            "traffic": {
                "requests_per_second": request_metrics.get("requests_per_second", 0),
                "total_requests_1h": request_metrics.get("total_requests", 0),
                "avg_latency_ms": request_metrics.get("average_latency_ms", 0),
                "error_rate_percent": request_metrics.get("error_rate_percent", 0),
                "unique_users_1h": request_metrics.get("unique_users", 0),
                "hourly_history": MetricsCollector.get_hourly_history(hours=8)
            },
            
            # AI/LLM
            "ai": {
                "requests_today": ai_summary.get("total_requests", 0),
                "tokens_today": ai_summary.get("total_tokens", 0),
                "cost_today_usd": ai_summary.get("total_cost_usd", 0),
                "guardrail_rejections": ai_summary.get("guardrail_rejections", 0)
            },
            
            # Security (events are fetched before this return block)
            "security": {
                "blacklisted_ips": blacklisted,
                "active_users": active_users,
                "guest_sessions": guest_sessions,
                "rate_limited_count": rate_limited_users,
                "events_today": security_events_today
            },
            
            # Actor Info
            "accessed_by": {
                "admin_id": current_user.id,
                "admin_email": current_user.email,
                "role": current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
            }
        }
        
    except Exception as e:
        logger.error(f"[ADMIN_DASHBOARD] Overview failed: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.get("/quick-stats")
async def get_quick_stats(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get quick stats for dashboard header KPI cards.
    Lightweight endpoint for frequent polling.
    """
    try:
        # Get minimal data for KPIs
        request_metrics = MetricsCollector.get_request_metrics(minutes=5)
        ai_summary = AIMetricsService.get_daily_summary()
        kill_switches = get_all_switches()
        
        active_switches = sum(1 for s in kill_switches.values() if s.is_active)
        
        return {
            "rps": request_metrics.get("requests_per_second", 0),
            "error_rate": request_metrics.get("error_rate_percent", 0),
            "ai_requests": ai_summary.get("total_requests", 0),
            "ai_cost": ai_summary.get("total_cost_usd", 0),
            "active_switches": active_switches,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"[ADMIN_DASHBOARD] Quick stats failed: {e}")
        return {"error": str(e)}


@router.get("/alerts")
async def get_system_alerts(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get active system alerts and warnings.
    """
    alerts = []
    
    try:
        # Check kill switches
        kill_switches = get_all_switches()
        for name, switch in kill_switches.items():
            if switch.is_active:
                alerts.append({
                    "severity": "critical" if name == "emergency_shutdown" else "warning",
                    "type": "kill_switch",
                    "message": f"Kill switch '{name}' is ACTIVE",
                    "details": {"reason": switch.reason},
                    "timestamp": switch.activated_at.isoformat() if switch.activated_at else None
                })
        
        # Check infrastructure
        infra = InfraMetricsCollector.get_all_infrastructure_metrics()
        
        if not infra.get("redis", {}).get("connected"):
            alerts.append({
                "severity": "critical",
                "type": "infrastructure",
                "message": "Redis is DOWN",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        if not infra.get("mysql", {}).get("connected"):
            alerts.append({
                "severity": "critical",
                "type": "infrastructure",
                "message": "MySQL is DOWN",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        if not infra.get("chromadb", {}).get("connected"):
            alerts.append({
                "severity": "warning",
                "type": "infrastructure",
                "message": "ChromaDB is DOWN",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        # Check error rate
        metrics = MetricsCollector.get_request_metrics(minutes=5)
        error_rate = metrics.get("error_rate_percent", 0)
        if error_rate > 10:
            alerts.append({
                "severity": "critical" if error_rate > 25 else "warning",
                "type": "traffic",
                "message": f"High error rate: {error_rate:.1f}%",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        return {
            "alert_count": len(alerts),
            "alerts": alerts,
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"[ADMIN_DASHBOARD] Alerts failed: {e}")
        return {"error": str(e), "alert_count": 0, "alerts": []}


@router.get("/hourly-traffic")
async def get_hourly_traffic(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get hourly traffic data for the last 24 hours.
    Returns request counts per hour for traffic trend visualization.
    """
    try:
        redis = get_redis()
        now = datetime.now(timezone.utc)
        
        hourly_data = []
        labels = []
        
        # Get last 24 hours of data
        for i in range(23, -1, -1):
            hour = now.replace(minute=0, second=0, microsecond=0)
            hour = hour.replace(hour=(hour.hour - i) % 24)
            
            # Get request count for this hour from Redis
            hour_key = f"metrics:requests:hour:{hour.strftime('%Y-%m-%d:%H')}"
            count = redis.get(hour_key) or 0
            
            hourly_data.append(int(count) if count else 0)
            labels.append(hour.strftime('%H:00'))
        
        return {
            "labels": labels,
            "data": hourly_data,
            "timestamp": now.isoformat()
        }
        
    except Exception as e:
        logger.error(f"[ADMIN_DASHBOARD] Hourly traffic failed: {e}")
        # Return empty data with labels
        now = datetime.now(timezone.utc)
        labels = [f"{(now.hour - i) % 24:02d}:00" for i in range(23, -1, -1)]
        return {"labels": labels, "data": [0] * 24, "timestamp": now.isoformat()}


@router.get("/audit-log")
async def get_audit_log(
    limit: int = 50,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get recent system audit logs.
    """
    try:
        from app.core.database import SessionLocal
        from app.models.audit_log import AuditLog
        from sqlalchemy import desc
        
        db = SessionLocal()
        try:
            logs = db.query(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit).all()
            
            # Convert to dict list using model's to_dict method
            log_entries = [log.to_dict() for log in logs]
            
            return {
                "logs": log_entries,
                "count": len(log_entries),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"[ADMIN_DASHBOARD] Audit log failed: {e}")
        return {"logs": [], "error": str(e)}


# ==================== USER MANAGEMENT SECTION ====================

@router.get("/users/search")
async def search_users(
    query: str = "",
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Search and list all users with activity summary.
    
    Returns REAL data from database:
    - User info (id, email, full_name, created_at, is_active)
    - Active session status
    - Last login time
    - Total logins count
    """
    try:
        from app.core.database import SessionLocal
        from app.models.user import LoginHistory, RefreshToken
        # Fix import path for AnalysisHistory
        from app.models.user_stocks import AnalysisHistory
        from sqlalchemy import func, or_
        
        db = SessionLocal()
        redis = get_redis()
        
        try:
            # Build query
            user_query = db.query(User)
            
            # Apply search filter if provided
            if query:
                search_pattern = f"%{query}%"
                user_query = user_query.filter(
                    or_(
                        User.email.ilike(search_pattern),
                        User.full_name.ilike(search_pattern)
                    )
                )
            
            # Get total count
            total_users = user_query.count()
            
            # Pagination
            offset = (page - 1) * limit
            users = user_query.order_by(User.id.desc()).offset(offset).limit(limit).all()
            
            # Build response with activity data
            user_list = []
            for user in users:
                # Get last login
                last_login = db.query(LoginHistory).filter(
                    LoginHistory.user_id == user.id,
                    LoginHistory.login_success == True
                ).order_by(LoginHistory.login_time.desc()).first()
                
                # Get total logins
                total_logins = db.query(func.count(LoginHistory.id)).filter(
                    LoginHistory.user_id == user.id,
                    LoginHistory.login_success == True
                ).scalar() or 0
                
                # Check if user has active session
                active_sessions = db.query(func.count(RefreshToken.id)).filter(
                    RefreshToken.user_id == user.id,
                    RefreshToken.revoked == False,
                    RefreshToken.expires_at > datetime.now(timezone.utc)
                ).scalar() or 0
                
                # Get analysis count
                analysis_count = db.query(func.count(AnalysisHistory.id)).filter(
                    AnalysisHistory.user_id == user.id
                ).scalar() or 0
                
                user_list.append({
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name or "",
                    "is_active": user.is_active,
                    "is_admin": user.is_admin,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "last_login": last_login.login_time.isoformat() if last_login else None,
                    "total_logins": total_logins,
                    "active_sessions": active_sessions,
                    "has_active_session": active_sessions > 0,
                    "analysis_count": analysis_count
                })
            
            return {
                "users": user_list,
                "total_users": total_users,
                "page": page,
                "limit": limit,
                "total_pages": (total_users + limit - 1) // limit,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"[ADMIN_DASHBOARD] Search users failed: {e}")
        return {
            "users": [],
            "total_users": 0,
            "page": page,
            "limit": limit,
            "total_pages": 0,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.get("/users/{user_id}/details")
async def get_user_details(
    user_id: int,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get detailed activity information for a specific user.
    
    Returns REAL data from database:
    - User profile
    - Login history (IPs, devices, locations, times)
    - Analysis history (symbols analyzed, timestamps)
    - Active sessions
    - Activity trends
    """
    try:
        from app.core.database import SessionLocal
        from app.models.user import LoginHistory, RefreshToken
        # Fix import path for AnalysisHistory
        from app.models.user_stocks import AnalysisHistory
        from sqlalchemy import func, desc
        
        db = SessionLocal()
        redis = get_redis()
        
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"error": "User not found", "user_id": user_id}
            
            # Get login history (last 50)
            login_records = db.query(LoginHistory).filter(
                LoginHistory.user_id == user_id
            ).order_by(desc(LoginHistory.login_time)).limit(50).all()
            
            login_history = []
            unique_ips = set()
            unique_devices = set()
            
            for record in login_records:
                if record.ip_address:
                    unique_ips.add(record.ip_address)
                if record.device_name:
                    unique_devices.add(record.device_name)
                    
                login_history.append({
                    "id": record.id,
                    "login_time": record.login_time.isoformat() if record.login_time else None,
                    "logout_time": record.logout_time.isoformat() if record.logout_time else None,
                    "ip_address": record.ip_address,
                    "device_name": record.device_name,
                    "device_type": record.device_type,
                    "browser": record.browser_name,
                    "os": record.os_name,
                    "location": record.location_country,
                    "success": record.login_success
                })
            
            # Get active sessions
            active_tokens = db.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False,
                RefreshToken.expires_at > datetime.now(timezone.utc)
            ).all()
            
            active_sessions = [{
                "id": t.id,
                "device": t.device_name,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "expires_at": t.expires_at.isoformat() if t.expires_at else None
            } for t in active_tokens]
            
            # Get analysis history (last 30)
            analyses = db.query(AnalysisHistory).filter(
                AnalysisHistory.user_id == user_id
            ).order_by(desc(AnalysisHistory.created_at)).limit(30).all()
            
            analysis_history = [{
                "id": a.id,
                "symbol": a.symbol,
                "analysis_type": a.analysis_type if hasattr(a, 'analysis_type') else "full",
                "created_at": a.created_at.isoformat() if a.created_at else None
            } for a in analyses]
            
            # Calculate activity trends (logins per day for last 7 days)
            seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
            daily_logins = db.query(
                func.date(LoginHistory.login_time),
                func.count(LoginHistory.id)
            ).filter(
                LoginHistory.user_id == user_id,
                LoginHistory.login_time >= seven_days_ago,
                LoginHistory.login_success == True
            ).group_by(func.date(LoginHistory.login_time)).all()
            
            activity_trend = [{"date": str(d[0]), "logins": d[1]} for d in daily_logins]
            
            # Total statistics
            total_logins = db.query(func.count(LoginHistory.id)).filter(
                LoginHistory.user_id == user_id,
                LoginHistory.login_success == True
            ).scalar() or 0
            
            total_analyses = db.query(func.count(AnalysisHistory.id)).filter(
                AnalysisHistory.user_id == user_id
            ).scalar() or 0
            
            return {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name or "",
                    "is_active": user.is_active,
                    "is_admin": user.is_admin,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                },
                "stats": {
                    "total_logins": total_logins,
                    "total_analyses": total_analyses,
                    "unique_ips_count": len(unique_ips),
                    "unique_devices_count": len(unique_devices),
                    "active_sessions_count": len(active_sessions)
                },
                "unique_ips": list(unique_ips),
                "unique_devices": list(unique_devices),
                "login_history": login_history,
                "active_sessions": active_sessions,
                "analysis_history": analysis_history,
                "activity_trend": activity_trend,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"[ADMIN_DASHBOARD] Get user details failed: {e}")
        return {
            "error": str(e),
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.post("/users/{user_id}/force-logout")
async def force_logout_user(
    user_id: int,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Force logout a user by revoking all their active sessions.
    
    This revokes all refresh tokens and clears any cached auth data.
    """
    try:
        from app.core.database import SessionLocal
        from app.models.user import RefreshToken, LoginHistory
        # Fix import path for AnalysisHistory
        from app.models.user_stocks import AnalysisHistory
        
        db = SessionLocal()
        
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found", "user_id": user_id}
            
            # Revoke all active tokens
            revoked_count = db.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False
            ).update({"revoked": True})
            
            # Update logout_time for active login records
            db.query(LoginHistory).filter(
                LoginHistory.user_id == user_id,
                LoginHistory.logout_time == None,
                LoginHistory.login_success == True
            ).update({"logout_time": datetime.now(timezone.utc)})
            
            db.commit()
            
            # Clear any cached auth data from Redis
            redis = get_redis()
            try:
                for key in redis.scan_iter(f"auth:*:{user_id}:*"):
                    redis.delete(key)
            except:
                pass
            
            logger.info(f"[ADMIN_DASHBOARD] Force logout user {user_id} by admin {current_user.id}, revoked {revoked_count} tokens")
            
            return {
                "success": True,
                "user_id": user_id,
                "revoked_sessions": revoked_count,
                "message": f"Successfully logged out user {user.email}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"[ADMIN_DASHBOARD] Force logout user failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Delete a user and all their data.
    
    WARNING: This is destructive and cannot be undone!
    Deletes: User account, login history, analysis history, refresh tokens.
    """
    try:
        from app.core.database import SessionLocal
        from app.models.user import RefreshToken, LoginHistory
        # Fix import path for AnalysisHistory
        from app.models.user_stocks import AnalysisHistory
        
        db = SessionLocal()
        
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found", "user_id": user_id}
            
            # Prevent deleting self or other admins
            if user_id == current_user.id:
                return {"success": False, "error": "Cannot delete yourself", "user_id": user_id}
            
            if user.is_admin:
                return {"success": False, "error": "Cannot delete admin users", "user_id": user_id}
            
            user_email = user.email
            
            # Delete related data first (foreign key constraints)
            deleted_tokens = db.query(RefreshToken).filter(RefreshToken.user_id == user_id).delete()
            deleted_logins = db.query(LoginHistory).filter(LoginHistory.user_id == user_id).delete()
            deleted_analyses = db.query(AnalysisHistory).filter(AnalysisHistory.user_id == user_id).delete()
            
            # Delete user
            db.delete(user)
            db.commit()
            
            logger.info(f"[ADMIN_DASHBOARD] Deleted user {user_id} ({user_email}) by admin {current_user.id}")
            
            return {
                "success": True,
                "user_id": user_id,
                "email": user_email,
                "deleted_counts": {
                    "refresh_tokens": deleted_tokens,
                    "login_history": deleted_logins,
                    "analysis_history": deleted_analyses
                },
                "message": f"Successfully deleted user {user_email}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"[ADMIN_DASHBOARD] Delete user failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@router.get("/active-sessions")
async def get_all_active_sessions(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get all active user sessions across ALL users.
    For admin User Intelligence page.
    Deduplicates sessions by email (keeps latest session per user).
    """
    try:
        from app.core.database import SessionLocal
        from app.models.user import RefreshToken, User as UserModel, LoginHistory
        from sqlalchemy import desc, func
        from app.utils.ip_geolocation import IPGeolocation
        from datetime import timedelta
        
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            
            # AUTO-CLEANUP: Revoke tokens not used in last 12 hours
            stale_cutoff = now - timedelta(hours=12)
            stale_tokens = db.query(RefreshToken).filter(
                RefreshToken.revoked == False,
                RefreshToken.last_used_at < stale_cutoff
            ).all()
            
            if stale_tokens:
                logger.info(f"[ADMIN] Auto-revoking {len(stale_tokens)} stale tokens (not used in 12h)")
                for token in stale_tokens:
                    token.revoked = True
                db.commit()
            
            # Get all active (non-revoked) sessions
            sessions = db.query(RefreshToken, UserModel).join(
                UserModel, RefreshToken.user_id == UserModel.id
            ).filter(
                RefreshToken.revoked == False
            ).order_by(desc(RefreshToken.last_used_at)).all()
            
            # Filter valid sessions, deduplicate by user (keep latest)
            seen_users = set()
            result = []
            redis = get_redis()
            
            for token, user in sessions:
                if not token.is_valid:
                    continue
                
                # Deduplicate - keep only latest session per user
                if user.id in seen_users:
                    continue
                seen_users.add(user.id)
                
                # Get request count from Redis
                user_request_key = f"metrics:user_requests:{user.id}"
                request_count = int(redis.get(user_request_key) or 0)
                
                # Check if rate limited - check all rate limit keys
                is_rate_limited = False
                if token.ip_address:
                    is_rate_limited = redis.exists(f"blocked_rate:{token.ip_address}") or \
                                      redis.exists(f"ratelimit:blocked:{token.ip_address}")
                
                # Get location
                location = IPGeolocation.get_location(token.ip_address) if token.ip_address else {}
                
                # Determine device type from os, browser, device_name
                device_type = token.device_type
                device_name = token.device_name or "Unknown Device"
                os_str = (token.os or "").lower()
                browser_str = (token.browser or "").lower()
                name_lower = device_name.lower()
                
                if not device_type:
                    # Detect from OS first
                    if "ios" in os_str or "iphone" in name_lower:
                        device_type = "mobile"
                    elif "android" in os_str or "android" in name_lower:
                        device_type = "mobile"
                    elif "ipad" in os_str or "ipad" in name_lower or "tablet" in name_lower:
                        device_type = "tablet"
                    elif "mac" in os_str or "mac" in name_lower:
                        device_type = "desktop"  # Mac is desktop
                    elif "windows" in os_str or "windows" in name_lower:
                        device_type = "desktop"
                    elif "linux" in os_str or "linux" in name_lower:
                        device_type = "desktop"
                    elif "mobile" in browser_str:
                        device_type = "mobile"
                    else:
                        device_type = "desktop"  # Default to desktop
                
                result.append({
                    "user_id": user.id,
                    "email": user.email,
                    "role": user.role,
                    "session_id": token.id,
                    "ip": token.ip_address or "Unknown",
                    "device": device_type,
                    "browser": f"{token.browser or 'Unknown'} {token.os or ''}".strip(),
                    "device_name": device_name,
                    "location": IPGeolocation.format_location(location),
                    "login_time": token.created_at.isoformat() if token.created_at else None,
                    "last_active": token.last_used_at.isoformat() if token.last_used_at else None,
                    "request_count": request_count,
                    "is_rate_limited": is_rate_limited
                })
            
            # Get totals for stats
            unique_ips = len(set(s["ip"] for s in result))
            rate_limited_count = len([s for s in result if s["is_rate_limited"]])
            
            # Device breakdown from actual data (case-insensitive)
            device_breakdown = {
                "desktop": len([s for s in result if s["device"].lower() == "desktop"]),
                "mobile": len([s for s in result if s["device"].lower() == "mobile"]),
                "tablet": len([s for s in result if s["device"].lower() == "tablet"])
            }
            
            # Get geolocation breakdown
            locations = {}
            for s in result:
                loc = s["location"] or "Unknown"
                locations[loc] = locations.get(loc, 0) + 1
            
            # Get real login/logout counts from LoginHistory
            now = datetime.now(timezone.utc)
            day_ago = now - timedelta(hours=24)
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)
            
            # Unique active users (those who logged in successfully)
            unique_users_24h = db.query(func.count(func.distinct(LoginHistory.user_id))).filter(
                LoginHistory.login_time >= day_ago,
                LoginHistory.login_success == True
            ).scalar() or 0
            
            unique_users_week = db.query(func.count(func.distinct(LoginHistory.user_id))).filter(
                LoginHistory.login_time >= week_ago,
                LoginHistory.login_success == True
            ).scalar() or 0
            
            unique_users_month = db.query(func.count(func.distinct(LoginHistory.user_id))).filter(
                LoginHistory.login_time >= month_ago,
                LoginHistory.login_success == True
            ).scalar() or 0
            
            # Login count (24h)
            logins_24h = db.query(func.count(LoginHistory.id)).filter(
                LoginHistory.login_time >= day_ago,
                LoginHistory.login_success == True
            ).scalar() or 0
            
            # Logout count (24h) - count records with logout_time set
            logouts_24h = db.query(func.count(LoginHistory.id)).filter(
                LoginHistory.logout_time >= day_ago
            ).scalar() or 0
            
            # Get rate limited count from Redis (scan for blocked keys)
            rate_limited_ips = 0
            try:
                for key in redis.scan_iter("blocked_rate:*"):
                    rate_limited_ips += 1
                for key in redis.scan_iter("ratelimit:blocked:*"):
                    rate_limited_ips += 1
            except:
                pass
            
            # JWT resets (from Redis - count auth_epoch changes)
            jwt_resets = int(redis.get("metrics:jwt_resets:24h") or 0)
            
            # JWT token refreshes (from Redis - count successful token refreshes)
            jwt_refreshes = int(redis.get("metrics:jwt_refreshes:24h") or 0)
            
            # Year unique users  
            year_ago = now - timedelta(days=365)
            unique_users_year = db.query(func.count(func.distinct(LoginHistory.user_id))).filter(
                LoginHistory.login_time >= year_ago,
                LoginHistory.login_success == True
            ).scalar() or 0
            
            # Total registered users
            total_registered_users = db.query(func.count(UserModel.id)).scalar() or 0
            
            # Failed logins (24h)
            failed_logins_24h = db.query(func.count(LoginHistory.id)).filter(
                LoginHistory.login_time >= day_ago,
                LoginHistory.login_success == False
            ).scalar() or 0
            
            # Total logins/logouts all time
            total_logins = db.query(func.count(LoginHistory.id)).filter(
                LoginHistory.login_success == True
            ).scalar() or 0
            
            total_logouts = db.query(func.count(LoginHistory.id)).filter(
                LoginHistory.logout_time.isnot(None)
            ).scalar() or 0
            
            # Active right now (logged in within last hour)
            hour_ago = now - timedelta(hours=1)
            active_now = db.query(func.count(func.distinct(LoginHistory.user_id))).filter(
                LoginHistory.login_time >= hour_ago,
                LoginHistory.login_success == True
            ).scalar() or 0
            
            return {
                "sessions": result,
                "total_sessions": len(result),
                "unique_ips": unique_ips,
                "rate_limited_count": rate_limited_ips,
                "device_breakdown": device_breakdown,
                "locations": locations,
                "activity": {
                    "logins_24h": logins_24h,
                    "logouts_24h": logouts_24h,
                    "rate_limited_24h": rate_limited_ips,
                    "jwt_resets_24h": jwt_resets,
                    "jwt_refreshes_24h": jwt_refreshes,
                    "failed_logins_24h": failed_logins_24h,
                    "unique_users_24h": unique_users_24h,
                    "unique_users_week": unique_users_week,
                    "unique_users_month": unique_users_month,
                    "unique_users_year": unique_users_year,
                    "total_registered_users": total_registered_users,
                    "total_logins": total_logins,
                    "total_logouts": total_logouts,
                    "active_now": active_now
                },
                # Behavioral analytics from real tracked data
                "behavioral_stats": MetricsCollector.get_user_behavioral_stats(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"[ADMIN_DASHBOARD] Active sessions failed: {e}")
        return {
            "sessions": [],
            "total_sessions": 0,
            "unique_ips": 0,
            "rate_limited_count": 0,
            "device_breakdown": {"desktop": 0, "mobile": 0, "tablet": 0},
            "locations": {},
            "activity": {
                "logins_24h": 0,
                "logouts_24h": 0,
                "rate_limited_24h": 0,
                "jwt_resets_24h": 0,
                "failed_logins_24h": 0,
                "unique_users_24h": 0,
                "unique_users_week": 0,
                "unique_users_month": 0,
                "unique_users_year": 0,
                "total_registered_users": 0,
                "total_logins": 0,
                "total_logouts": 0,
                "active_now": 0
            },
            "error": str(e)
        }



@router.post("/logout-user/{user_id}")
async def admin_logout_user(
    user_id: int,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Force logout a specific user by revoking all their sessions.
    Admin only.
    """
    try:
        from app.core.database import SessionLocal
        from app.models.user import RefreshToken
        
        db = SessionLocal()
        try:
            sessions = db.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False
            ).all()
            
            count = 0
            for session in sessions:
                session.revoked = True
                count += 1
            
            db.commit()
            
            logger.info(f"[ADMIN] Admin {current_user.email} force logged out user {user_id}, revoked {count} sessions")
            
            return {
                "ok": True,
                "message": f"Logged out user {user_id}, revoked {count} sessions",
                "revoked_count": count
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"[ADMIN_DASHBOARD] Logout user failed: {e}")
        return {"ok": False, "error": str(e)}


@router.get("/internal-apis")
async def get_internal_apis_metrics(
    hours: int = 24,
    current_user: User = Depends(require_admin)
) -> List[Dict[str, Any]]:
    """
    Get metrics for internal API endpoints.
    Returns call counts, avg latency, and error rates per endpoint.
    """
    return MetricsCollector.get_endpoint_metrics(hours=hours)


@router.get("/external-apis")
async def get_external_apis_metrics(
    hours: int = 24,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get metrics for external API calls (Stock APIs, News APIs, LLM APIs).
    Returns per-API metrics including call counts, success rates, and latencies.
    """
    try:
        # Get external API metrics
        api_metrics = ExternalAPIMetricsService.get_all_api_metrics(hours=hours)
        summary = ExternalAPIMetricsService.get_api_summary()
        
        # Get AI Metrics from dedicated service for more detailed LLM data
        ai_stats = AIMetricsService.get_daily_summary()
        
        # Categorize APIs
        stock_apis = [m for m in api_metrics if m["category"] == "stock"]
        news_apis = [m for m in api_metrics if m["category"] == "news"]
        llm_apis = [m for m in api_metrics if m["category"] == "llm"]
        
        # Enhance LLM APIs with AI Metrics data
        for api in llm_apis:
            if "openai" in api["api_key"].lower() or "azure" in api["api_key"].lower():
                api["tokens_today"] = ai_stats.get("total_tokens", 0)
                api["cost_today_usd"] = ai_stats.get("total_cost_usd", 0)
        
        return {
            "stock_apis": stock_apis,
            "news_apis": news_apis,
            "llm_apis": llm_apis,
            "summary": summary,
            "ai_stats": ai_stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"[ADMIN_DASHBOARD] External APIs metrics failed: {e}")
        return {
            "stock_apis": [],
            "news_apis": [],
            "llm_apis": [],
            "summary": {},
            "error": str(e)
        }


# ==================== SRE DASHBOARD ENDPOINTS ====================

@router.get("/sre-overview")
async def get_sre_overview(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get global system health overview for SRE dashboard.
    
    Returns:
    - Global health state (healthy/degraded/critical)
    - Global health score (0-100)
    - User impact indicator
    - Active incidents count
    - Global error rate, p95 latency, RPS with delta
    """
    try:
        return SREHealthService.get_global_health()
    except Exception as e:
        logger.error(f"[ADMIN_DASHBOARD] SRE overview failed: {e}")
        return {
            "global_health": "critical",
            "global_score": 0,
            "user_impact": {"affected_users": "unknown", "status": "unknown"},
            "active_incidents": 0,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.get("/service-matrix")
async def get_service_matrix(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get service health matrix for SRE dashboard.
    
    Returns per-service:
    - Health state (healthy/degraded/critical)
    - Health score (0-100)
    - Error rate %
    - p95 latency
    - Saturation %
    - Uptime %
    - Trend direction
    """
    try:
        return SREHealthService.get_service_matrix()
    except Exception as e:
        logger.error(f"[ADMIN_DASHBOARD] Service matrix failed: {e}")
        return {
            "services": [],
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.get("/service/{service_name}/deep-dive")
async def get_service_deep_dive(
    service_name: str,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get detailed metrics for a specific service.
    
    Args:
        service_name: One of 'api', 'redis', 'mysql', 'chromadb', 'host'
    
    Returns:
    - Health score breakdown (availability, error, latency, saturation)
    - Raw metrics
    - Interpretation text
    - Trend direction
    """
    try:
        return SREHealthService.get_service_deep_dive(service_name)
    except Exception as e:
        logger.error(f"[ADMIN_DASHBOARD] Service deep dive failed for {service_name}: {e}")
        return {
            "service": service_name,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.get("/rag-observability")
async def get_rag_observability(
    hours: int = 24,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get RAG/AI observability metrics for SRE dashboard.
    
    Returns:
    - Retrieval success %
    - Empty context rate
    - Avg docs per query
    - Latency breakdown (embedding, retrieval, LLM, total, p95)
    - SLA violation %
    """
    try:
        return AIMetricsService.get_rag_observability(hours=hours)
    except Exception as e:
        logger.error(f"[ADMIN_DASHBOARD] RAG observability failed: {e}")
        return {
            "retrieval_success_percent": 0.0,
            "empty_context_rate": 0.0,
            "avg_docs_per_query": 0.0,
            "latency_breakdown": {
                "embedding_ms": 0.0,
                "retrieval_ms": 0.0,
                "llm_ms": 0.0,
                "total_ms": 0.0,
                "p95_ms": 0.0
            },
            "sla_violation_percent": 0.0,
            "total_queries": 0,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.get("/user-impact")
async def get_user_impact(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get user impact metrics showing how infrastructure issues affect users.
    
    Returns:
    - Failed user requests %
    - Slow user requests % (p95 > SLA)
    - Top impacted endpoints
    - Correlated service degradation
    """
    try:
        # Get request metrics
        request_metrics = MetricsCollector.get_request_metrics(minutes=5)
        endpoint_metrics = MetricsCollector.get_endpoint_metrics(hours=1)
        
        # Get service health for correlation
        service_matrix = SREHealthService.get_service_matrix()
        degraded_services = [
            s["name"] for s in service_matrix.get("services", [])
            if s.get("health_state") != "healthy"
        ]
        
        # Calculate user impact metrics
        total_requests = request_metrics.get("total_requests", 0)
        error_count = request_metrics.get("error_count", 0)
        
        failed_percent = (error_count / total_requests * 100) if total_requests > 0 else 0
        
        # Estimate slow requests (assume requests > avg * 2 are slow)
        avg_latency = request_metrics.get("average_latency_ms", 100)
        sla_threshold = 200  # 200ms SLA
        
        # Find top impacted endpoints (those with highest error rates or latency)
        top_impacted = []
        for ep in endpoint_metrics[:5]:  # Top 5
            latency = ep.get("avg_latency", 0)
            if latency > sla_threshold:
                top_impacted.append({
                    "endpoint": ep.get("endpoint", "unknown"),
                    "avg_latency_ms": round(latency, 2),
                    "calls": ep.get("calls_24h", 0),
                    "status": "slow" if latency > sla_threshold else "normal"
                })
        
        return {
            "failed_requests_percent": round(failed_percent, 2),
            "slow_requests_percent": round(min(100, failed_percent * 2), 2),  # Rough estimate
            "total_requests_5m": total_requests,
            "top_impacted_endpoints": top_impacted,
            "degraded_services": degraded_services,
            "has_user_impact": failed_percent > 1 or len(degraded_services) > 0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"[ADMIN_DASHBOARD] User impact failed: {e}")
        return {
            "failed_requests_percent": 0.0,
            "slow_requests_percent": 0.0,
            "total_requests_5m": 0,
            "top_impacted_endpoints": [],
            "degraded_services": [],
            "has_user_impact": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.get("/sre-unified-overview")
async def get_sre_unified_overview(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    UNIFIED SRE OVERVIEW ENDPOINT - Powers the main Overview page.
    
    Combines all critical data in a single call:
    - System state (health, score, primary degradation reason)
    - User impact (failed %, slow %, affected users)
    - Change detection (15m deltas for traffic, errors, latency)
    - Golden signals (RPS, error rate, p95 latency, saturation)
    - Service health matrix
    - AI/RAG health summary
    - Active alerts
    - Recent events (last 24h)
    """
    try:
        now = datetime.now(timezone.utc)
        
        # ==================== GATHER DATA FROM ALL SOURCES ====================
        
        # Get service health matrix
        service_matrix = SREHealthService.get_service_matrix()
        services = service_matrix.get("services", [])
        
        # Get request metrics for current and previous windows (15 min each)
        current_metrics = MetricsCollector.get_request_metrics(minutes=15)
        # For delta comparison, we look at 15-30 minutes ago
        extended_metrics = MetricsCollector.get_request_metrics(minutes=30)
        
        # Get RAG observability
        rag_data = AIMetricsService.get_rag_observability(hours=24)
        
        # Get AI daily summary
        ai_summary = AIMetricsService.get_daily_summary()
        
        # Get infrastructure metrics
        infra = InfraMetricsCollector.get_all_infrastructure_metrics()
        
        # ==================== CALCULATE GLOBAL HEALTH STATE ====================
        
        # Calculate global health from services
        scores = [s.get("health_score", 0) for s in services]
        avg_score = sum(scores) / len(scores) if scores else 100
        
        # Determine health state
        if avg_score >= 90:
            global_health = "healthy"
        elif avg_score >= 70:
            global_health = "degraded"
        else:
            global_health = "critical"
        
        # Find primary degradation reason
        primary_reason = None
        degraded_services = [s for s in services if s.get("health_state") != "healthy"]
        if degraded_services:
            # Find the worst-performing service
            worst = min(degraded_services, key=lambda s: s.get("health_score", 100))
            interpretation = worst.get("interpretation", "")
            if interpretation:
                primary_reason = interpretation
            else:
                primary_reason = f"{worst.get('name')} is {worst.get('health_state')}"
        
        # Check for additional reasons
        current_error_rate = current_metrics.get("error_rate_percent", 0)
        if current_error_rate > 5 and not primary_reason:
            primary_reason = f"Elevated error rate ({current_error_rate:.1f}%) in last 15m"
        
        # Check AI/RAG issues
        if rag_data.get("empty_context_rate", 0) > 20 and not primary_reason:
            primary_reason = f"High empty context rate ({rag_data['empty_context_rate']:.1f}%) in RAG queries"
        
        # ==================== CALCULATE DELTA METRICS (15m windows) ====================
        
        # Current window (0-15 min)
        current_requests = current_metrics.get("total_requests", 0)
        current_errors = current_metrics.get("error_count", 0)
        current_avg_latency = current_metrics.get("average_latency_ms", 0)
        
        # Previous window (15-30 min) - calculated by subtracting
        extended_requests = extended_metrics.get("total_requests", 0)
        extended_errors = extended_metrics.get("error_count", 0)
        extended_avg_latency = extended_metrics.get("average_latency_ms", 0)
        
        prev_requests = max(0, extended_requests - current_requests)
        prev_errors = max(0, extended_errors - current_errors)
        
        # Calculate deltas
        traffic_delta = ((current_requests - prev_requests) / prev_requests * 100) if prev_requests > 0 else 0
        
        current_error_pct = (current_errors / current_requests * 100) if current_requests > 0 else 0
        prev_error_pct = (prev_errors / prev_requests * 100) if prev_requests > 0 else 0
        error_delta = current_error_pct - prev_error_pct
        
        latency_delta = ((current_avg_latency - extended_avg_latency) / extended_avg_latency * 100) if extended_avg_latency > 0 else 0
        
        # ==================== CALCULATE GOLDEN SIGNALS ====================
        
        # RPS (requests per second)
        rps_current = current_metrics.get("requests_per_second", 0)
        rps_prev = prev_requests / (15 * 60) if prev_requests > 0 else rps_current
        rps_delta = ((rps_current - rps_prev) / rps_prev * 100) if rps_prev > 0 else 0
        
        # Error Rate
        error_rate_current = current_error_rate
        error_rate_sla = 1.0  # 1% SLA
        
        # p95 Latency (estimate as 1.5x average)
        p95_latency = current_avg_latency * 1.5 if current_avg_latency > 0 else 0
        p95_sla = 200  # 200ms SLA
        
        # Saturation - max of all services
        saturations = [s.get("saturation_percent", 0) for s in services]
        saturation_current = max(saturations) if saturations else 0
        saturation_sla = 80  # 80% SLA
        
        # ==================== COMPILE USER IMPACT ====================
        
        failed_requests_pct = current_error_pct
        # Count slow requests as those with latency > SLA
        slow_requests_pct = min(100, (p95_latency / p95_sla * 10)) if p95_latency > p95_sla * 0.5 else 0
        
        # Estimate active users affected (from active sessions if available)
        affected_users = 0
        if failed_requests_pct > 5 or slow_requests_pct > 10:
            # If there's impact, estimate affected users
            try:
                redis = get_redis()
                active_tokens = redis.scard("auth:active_tokens") or 0
                affected_users = int(active_tokens * (failed_requests_pct + slow_requests_pct) / 100)
            except:
                pass
        
        # ==================== GATHER ALERTS ====================
        
        alerts = []
        
        # Kill switch alerts
        kill_switches = get_all_switches()
        for name, switch in kill_switches.items():
            if switch.is_active:
                alerts.append({
                    "severity": "critical" if name == "emergency_shutdown" else "warning",
                    "service": "system",
                    "message": f"Kill switch '{name}' is ACTIVE",
                    "time": switch.activated_at.isoformat() if switch.activated_at else now.isoformat(),
                    "link": "/admin/controls"
                })
        
        # Infrastructure down alerts
        if not infra.get("redis", {}).get("connected"):
            alerts.append({
                "severity": "critical",
                "service": "Redis",
                "message": "Redis is DOWN - not responding",
                "time": now.isoformat(),
                "link": "/admin/infrastructure"
            })
        
        if not infra.get("mysql", {}).get("connected"):
            alerts.append({
                "severity": "critical",
                "service": "MySQL",
                "message": "MySQL is DOWN - database unavailable",
                "time": now.isoformat(),
                "link": "/admin/infrastructure"
            })
        
        if not infra.get("chromadb", {}).get("connected"):
            alerts.append({
                "severity": "warning",
                "service": "ChromaDB",
                "message": "ChromaDB is DOWN - RAG queries will fail",
                "time": now.isoformat(),
                "link": "/admin/infrastructure"
            })
        
        # High error rate alert
        if current_error_rate > 5:
            alerts.append({
                "severity": "critical" if current_error_rate > 10 else "warning",
                "service": "API",
                "message": f"High error rate: {current_error_rate:.1f}%",
                "time": now.isoformat(),
                "link": "/admin/infrastructure"
            })
        
        # Degraded service alerts
        for svc in degraded_services:
            if svc.get("health_state") == "critical":
                alerts.append({
                    "severity": "critical",
                    "service": svc.get("name"),
                    "message": svc.get("interpretation", f"{svc.get('name')} is critical"),
                    "time": now.isoformat(),
                    "link": "/admin/infrastructure"
                })
        
        # ==================== GATHER RECENT EVENTS ====================
        
        recent_events = []
        
        # Get audit log for recent events
        try:
            from app.core.database import SessionLocal
            from app.models.audit_log import AuditLog
            from sqlalchemy import desc
            
            db = SessionLocal()
            try:
                recent_logs = db.query(AuditLog).filter(
                    AuditLog.created_at >= now - timedelta(hours=24)
                ).order_by(desc(AuditLog.created_at)).limit(10).all()
                
                for log in recent_logs:
                    recent_events.append({
                        "type": "config_change" if "kill_switch" in (log.action or "").lower() else "action",
                        "message": f"{log.action}: {log.target_type or ''} {log.target_id or ''}".strip(),
                        "time": log.created_at.isoformat() if log.created_at else now.isoformat(),
                        "success": log.success
                    })
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"[SRE_OVERVIEW] Failed to get recent events: {e}")
        
        # ==================== AI/RAG HEALTH SUMMARY ====================
        
        ai_total_requests = ai_summary.get("total_requests", 0)
        ai_tokens = ai_summary.get("total_tokens", 0)
        ai_cost = ai_summary.get("total_cost_usd", 0)
        
        ai_rag_health = {
            "success_percent": rag_data.get("retrieval_success_percent", 100),
            "empty_context_percent": rag_data.get("empty_context_rate", 0),
            "p95_retrieval_ms": rag_data.get("latency_breakdown", {}).get("p95_ms", 0),
            "tokens_per_request": ai_summary.get("avg_tokens_per_request", 0),
            "cost_per_request_usd": round(ai_cost / ai_total_requests, 4) if ai_total_requests > 0 else 0,
            "total_requests_today": ai_total_requests,
            "sla_threshold_ms": 500
        }
        
        # ==================== BUILD RESPONSE ====================
        
        return {
            "system_state": {
                "health": global_health,
                "score": round(avg_score, 1),
                "primary_reason": primary_reason,
                "active_incidents": len([s for s in services if s.get("health_state") == "critical"]),
                "last_checked": now.isoformat()
            },
            "user_impact": {
                "failed_requests_percent": round(failed_requests_pct, 2),
                "slow_requests_percent": round(slow_requests_pct, 2),
                "active_users_affected": affected_users,
                "status": "major" if failed_requests_pct > 10 else "partial" if failed_requests_pct > 2 else "none",
                "window_minutes": 15
            },
            "change_detection": {
                "traffic_delta_percent": round(traffic_delta, 1),
                "error_delta_percent": round(error_delta, 2),
                "latency_delta_percent": round(latency_delta, 1),
                "window_minutes": 15
            },
            "golden_signals": {
                "rps": {
                    "current": round(rps_current, 2),
                    "sla": None,
                    "delta_percent": round(rps_delta, 1),
                    "status": "normal"
                },
                "error_rate": {
                    "current": round(error_rate_current, 2),
                    "sla": error_rate_sla,
                    "delta_percent": round(error_delta, 2),
                    "status": "critical" if error_rate_current > 5 else "warning" if error_rate_current > error_rate_sla else "normal"
                },
                "p95_latency_ms": {
                    "current": round(p95_latency, 0),
                    "sla": p95_sla,
                    "delta_percent": round(latency_delta, 1),
                    "status": "critical" if p95_latency > p95_sla * 1.5 else "warning" if p95_latency > p95_sla else "normal"
                },
                "saturation_percent": {
                    "current": round(saturation_current, 0),
                    "sla": saturation_sla,
                    "delta_percent": 0,  # Would need historical saturation
                    "status": "critical" if saturation_current > 90 else "warning" if saturation_current > saturation_sla else "normal"
                }
            },
            "service_matrix": services,
            "ai_rag_health": ai_rag_health,
            "alerts": alerts,
            "recent_events": recent_events,
            "timestamp": now.isoformat()
        }
        
    except Exception as e:
        logger.error(f"[ADMIN_DASHBOARD] Unified SRE overview failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "system_state": {
                "health": "critical",
                "score": 0,
                "primary_reason": f"Failed to compute health: {str(e)}",
                "active_incidents": 1,
                "last_checked": datetime.now(timezone.utc).isoformat()
            },
            "user_impact": {
                "failed_requests_percent": 0,
                "slow_requests_percent": 0,
                "active_users_affected": 0,
                "status": "unknown",
                "window_minutes": 15
            },
            "change_detection": {
                "traffic_delta_percent": 0,
                "error_delta_percent": 0,
                "latency_delta_percent": 0,
                "window_minutes": 15
            },
            "golden_signals": {},
            "service_matrix": [],
            "ai_rag_health": {},
            "alerts": [],
            "recent_events": [],
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.get("/historical-metrics")
async def get_historical_metrics(
    hours: int = 8,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get historical metrics for charts and graphs.
    
    Returns REAL data from Redis aggregated by hour:
    - Traffic (requests per hour)
    - Errors (error count and rate per hour)
    - Latency (avg latency per hour)
    
    This data powers the SRE dashboard charts.
    """
    try:
        # Get real hourly history from metrics collector
        hourly_history = MetricsCollector.get_hourly_history(hours=hours)
        
        # Transform for charts
        traffic_data = []
        latency_data = []
        error_data = []
        
        for entry in hourly_history:
            hour = entry.get("hour", "")
            traffic_data.append({
                "hour": hour,
                "requests": entry.get("requests", 0),
                "errors": entry.get("errors", 0)
            })
            latency_data.append({
                "hour": hour,
                "avg_latency_ms": entry.get("avg_latency_ms", 0)
            })
            error_data.append({
                "hour": hour,
                "error_rate_percent": entry.get("error_rate_percent", 0),
                "errors": entry.get("errors", 0)
            })
        
        return {
            "traffic": traffic_data,
            "latency": latency_data,
            "errors": error_data,
            "period_hours": hours,
            "data_points": len(hourly_history),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"[ADMIN_DASHBOARD] Historical metrics failed: {e}")
        return {
            "traffic": [],
            "latency": [],
            "errors": [],
            "period_hours": hours,
            "data_points": 0,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# ==================== USER MANAGEMENT SECTION ====================

@router.get("/users/search")
async def search_users(
    query: str = "",
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Search and list all users with activity summary.
    
    Returns REAL data from database:
    - User info (id, email, full_name, created_at, is_active)
    - Active session status
    - Last login time
    - Total logins count
    """
    try:
        from app.core.database import SessionLocal
        from app.models.user import LoginHistory, RefreshToken, AnalysisHistory
        from sqlalchemy import func, or_
        
        db = SessionLocal()
        redis = get_redis()
        
        try:
            # Build query
            user_query = db.query(User)
            
            # Apply search filter if provided
            if query:
                search_pattern = f"%{query}%"
                user_query = user_query.filter(
                    or_(
                        User.email.ilike(search_pattern),
                        User.full_name.ilike(search_pattern)
                    )
                )
            
            # Get total count
            total_users = user_query.count()
            
            # Pagination
            offset = (page - 1) * limit
            users = user_query.order_by(User.id.desc()).offset(offset).limit(limit).all()
            
            # Build response with activity data
            user_list = []
            for user in users:
                # Get last login
                last_login = db.query(LoginHistory).filter(
                    LoginHistory.user_id == user.id,
                    LoginHistory.login_success == True
                ).order_by(LoginHistory.login_time.desc()).first()
                
                # Get total logins
                total_logins = db.query(func.count(LoginHistory.id)).filter(
                    LoginHistory.user_id == user.id,
                    LoginHistory.login_success == True
                ).scalar() or 0
                
                # Check if user has active session
                active_sessions = db.query(func.count(RefreshToken.id)).filter(
                    RefreshToken.user_id == user.id,
                    RefreshToken.revoked == False,
                    RefreshToken.expires_at > datetime.now(timezone.utc)
                ).scalar() or 0
                
                # Get analysis count
                analysis_count = db.query(func.count(AnalysisHistory.id)).filter(
                    AnalysisHistory.user_id == user.id
                ).scalar() or 0
                
                user_list.append({
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name or "",
                    "is_active": user.is_active,
                    "is_admin": user.is_admin,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "last_login": last_login.login_time.isoformat() if last_login else None,
                    "total_logins": total_logins,
                    "active_sessions": active_sessions,
                    "has_active_session": active_sessions > 0,
                    "analysis_count": analysis_count
                })
            
            return {
                "users": user_list,
                "total_users": total_users,
                "page": page,
                "limit": limit,
                "total_pages": (total_users + limit - 1) // limit,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"[ADMIN_DASHBOARD] Search users failed: {e}")
        return {
            "users": [],
            "total_users": 0,
            "page": page,
            "limit": limit,
            "total_pages": 0,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.get("/users/{user_id}/details")
async def get_user_details(
    user_id: int,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get detailed activity information for a specific user.
    
    Returns REAL data from database:
    - User profile
    - Login history (IPs, devices, locations, times)
    - Analysis history (symbols analyzed, timestamps)
    - Active sessions
    - Activity trends
    """
    try:
        from app.core.database import SessionLocal
        from app.models.user import LoginHistory, RefreshToken, AnalysisHistory
        from sqlalchemy import func, desc
        
        db = SessionLocal()
        redis = get_redis()
        
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"error": "User not found", "user_id": user_id}
            
            # Get login history (last 50)
            login_records = db.query(LoginHistory).filter(
                LoginHistory.user_id == user_id
            ).order_by(desc(LoginHistory.login_time)).limit(50).all()
            
            login_history = []
            unique_ips = set()
            unique_devices = set()
            
            for record in login_records:
                if record.ip_address:
                    unique_ips.add(record.ip_address)
                if record.device_name:
                    unique_devices.add(record.device_name)
                    
                login_history.append({
                    "id": record.id,
                    "login_time": record.login_time.isoformat() if record.login_time else None,
                    "logout_time": record.logout_time.isoformat() if record.logout_time else None,
                    "ip_address": record.ip_address,
                    "device_name": record.device_name,
                    "device_type": record.device_type,
                    "browser": record.browser_name,
                    "os": record.os_name,
                    "location": record.location_country,
                    "success": record.login_success
                })
            
            # Get active sessions
            active_tokens = db.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False,
                RefreshToken.expires_at > datetime.now(timezone.utc)
            ).all()
            
            active_sessions = [{
                "id": t.id,
                "device": t.device_name,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "expires_at": t.expires_at.isoformat() if t.expires_at else None
            } for t in active_tokens]
            
            # Get analysis history (last 30)
            analyses = db.query(AnalysisHistory).filter(
                AnalysisHistory.user_id == user_id
            ).order_by(desc(AnalysisHistory.created_at)).limit(30).all()
            
            analysis_history = [{
                "id": a.id,
                "symbol": a.symbol,
                "analysis_type": a.analysis_type if hasattr(a, 'analysis_type') else "full",
                "created_at": a.created_at.isoformat() if a.created_at else None
            } for a in analyses]
            
            # Calculate activity trends (logins per day for last 7 days)
            seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
            daily_logins = db.query(
                func.date(LoginHistory.login_time),
                func.count(LoginHistory.id)
            ).filter(
                LoginHistory.user_id == user_id,
                LoginHistory.login_time >= seven_days_ago,
                LoginHistory.login_success == True
            ).group_by(func.date(LoginHistory.login_time)).all()
            
            activity_trend = [{"date": str(d[0]), "logins": d[1]} for d in daily_logins]
            
            # Total statistics
            total_logins = db.query(func.count(LoginHistory.id)).filter(
                LoginHistory.user_id == user_id,
                LoginHistory.login_success == True
            ).scalar() or 0
            
            total_analyses = db.query(func.count(AnalysisHistory.id)).filter(
                AnalysisHistory.user_id == user_id
            ).scalar() or 0
            
            return {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name or "",
                    "is_active": user.is_active,
                    "is_admin": user.is_admin,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                },
                "stats": {
                    "total_logins": total_logins,
                    "total_analyses": total_analyses,
                    "unique_ips_count": len(unique_ips),
                    "unique_devices_count": len(unique_devices),
                    "active_sessions_count": len(active_sessions)
                },
                "unique_ips": list(unique_ips),
                "unique_devices": list(unique_devices),
                "login_history": login_history,
                "active_sessions": active_sessions,
                "analysis_history": analysis_history,
                "activity_trend": activity_trend,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"[ADMIN_DASHBOARD] Get user details failed: {e}")
        return {
            "error": str(e),
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.post("/users/{user_id}/force-logout")
async def force_logout_user(
    user_id: int,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Force logout a user by revoking all their active sessions.
    
    This revokes all refresh tokens and clears any cached auth data.
    """
    try:
        from app.core.database import SessionLocal
        from app.models.user import RefreshToken, LoginHistory
        
        db = SessionLocal()
        
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found", "user_id": user_id}
            
            # Revoke all active tokens
            revoked_count = db.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False
            ).update({"revoked": True})
            
            # Update logout_time for active login records
            db.query(LoginHistory).filter(
                LoginHistory.user_id == user_id,
                LoginHistory.logout_time == None,
                LoginHistory.login_success == True
            ).update({"logout_time": datetime.now(timezone.utc)})
            
            db.commit()
            
            # Clear any cached auth data from Redis
            redis = get_redis()
            try:
                for key in redis.scan_iter(f"auth:*:{user_id}:*"):
                    redis.delete(key)
            except:
                pass
            
            logger.info(f"[ADMIN_DASHBOARD] Force logout user {user_id} by admin {current_user.id}, revoked {revoked_count} tokens")
            
            return {
                "success": True,
                "user_id": user_id,
                "revoked_sessions": revoked_count,
                "message": f"Successfully logged out user {user.email}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"[ADMIN_DASHBOARD] Force logout user failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Delete a user and all their data.
    
    WARNING: This is destructive and cannot be undone!
    Deletes: User account, login history, analysis history, refresh tokens.
    """
    try:
        from app.core.database import SessionLocal
        from app.models.user import RefreshToken, LoginHistory, AnalysisHistory
        
        db = SessionLocal()
        
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found", "user_id": user_id}
            
            # Prevent deleting self or other admins
            if user_id == current_user.id:
                return {"success": False, "error": "Cannot delete yourself", "user_id": user_id}
            
            if user.is_admin:
                return {"success": False, "error": "Cannot delete admin users", "user_id": user_id}
            
            user_email = user.email
            
            # Delete related data first (foreign key constraints)
            deleted_tokens = db.query(RefreshToken).filter(RefreshToken.user_id == user_id).delete()
            deleted_logins = db.query(LoginHistory).filter(LoginHistory.user_id == user_id).delete()
            deleted_analyses = db.query(AnalysisHistory).filter(AnalysisHistory.user_id == user_id).delete()
            
            # Delete user
            db.delete(user)
            db.commit()
            
            logger.info(f"[ADMIN_DASHBOARD] Deleted user {user_id} ({user_email}) by admin {current_user.id}")
            
            return {
                "success": True,
                "user_id": user_id,
                "email": user_email,
                "deleted_counts": {
                    "refresh_tokens": deleted_tokens,
                    "login_history": deleted_logins,
                    "analysis_history": deleted_analyses
                },
                "message": f"Successfully deleted user {user_email}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"[ADMIN_DASHBOARD] Delete user failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
