"""
Audit Service for Admin Command Center

Provides centralized, async-safe audit logging for all admin actions.
Designed for high reliability - failures won't block main operations.
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import Request
from typing import Optional, Dict, Any
from loguru import logger
import asyncio
from contextlib import contextmanager

from app.models.audit_log import AuditLog, ActionCategory, AuditAction
from app.models.user import User
from app.core.database import get_db


class AuditService:
    """
    Service for logging admin actions with high reliability.
    All methods are designed to not raise exceptions - failures are logged.
    """
    
    @staticmethod
    def get_client_ip(request: Request) -> str:
        """Extract client IP from request, handling proxies"""
        # Check X-Forwarded-For header (when behind proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"
    
    @staticmethod
    def log_action(
        db: Session,
        actor: User,
        action: str,
        request: Request = None,
        action_category: str = None,
        target_type: str = None,
        target_id: str = None,
        changes: Dict[str, Any] = None,
        payload: Dict[str, Any] = None,
        success: bool = True,
        error_message: str = None
    ) -> Optional[AuditLog]:
        """
        Log an admin action to the audit_logs table.
        
        Args:
            db: Database session
            actor: User performing the action
            action: Action type (use AuditAction constants)
            request: FastAPI request for IP/user-agent extraction
            action_category: Category (use ActionCategory constants)
            target_type: What type of entity was targeted (user, ip, toggle)
            target_id: ID of the targeted entity
            changes: Dictionary of changes made
            payload: Full request payload for hash computation
            success: Whether action succeeded
            error_message: Error message if failed
            
        Returns:
            AuditLog entry if created, None if failed
        """
        try:
            ip_address = None
            user_agent = None
            
            if request:
                ip_address = AuditService.get_client_ip(request)
                user_agent = request.headers.get("User-Agent")
            
            audit_entry = AuditLog.create_log(
                actor_id=actor.id,
                actor_role=actor.role if isinstance(actor.role, str) else actor.role.value,
                actor_email=actor.email,
                ip_address=ip_address,
                user_agent=user_agent,
                action=action,
                action_category=action_category,
                target_type=target_type,
                target_id=target_id,
                changes=changes,
                payload=payload,
                success=success,
                error_message=error_message
            )
            
            db.add(audit_entry)
            db.commit()
            db.refresh(audit_entry)
            
            logger.info(
                f"[AUDIT] {action} by {actor.email} "
                f"(role={actor.role}) on {target_type}:{target_id} "
                f"from {ip_address} - {'SUCCESS' if success else 'FAILED'}"
            )
            
            return audit_entry
            
        except SQLAlchemyError as e:
            logger.error(f"[AUDIT] Failed to log action {action}: {e}")
            db.rollback()
            return None
        except Exception as e:
            logger.error(f"[AUDIT] Unexpected error logging {action}: {e}")
            return None
    
    @staticmethod
    def log_dangerous_action(
        db: Session,
        actor: User,
        action: str,
        confirmation_code: str,
        request: Request = None,
        target_type: str = None,
        target_id: str = None,
        changes: Dict[str, Any] = None,
        success: bool = True,
        error_message: str = None
    ) -> Optional[AuditLog]:
        """
        Log a dangerous action that required typed confirmation.
        Adds confirmation code to the changes payload.
        """
        full_changes = changes.copy() if changes else {}
        full_changes["_confirmation"] = {
            "code_provided": confirmation_code,
            "actor_role": actor.role if isinstance(actor.role, str) else actor.role.value
        }
        
        return AuditService.log_action(
            db=db,
            actor=actor,
            action=action,
            request=request,
            action_category=ActionCategory.SYSTEM,
            target_type=target_type,
            target_id=target_id,
            changes=full_changes,
            success=success,
            error_message=error_message
        )
    
    @staticmethod
    def log_failed_access(
        db: Session,
        actor: User,
        action: str,
        required_role: str,
        request: Request = None
    ) -> Optional[AuditLog]:
        """Log a failed access attempt due to RBAC"""
        return AuditService.log_action(
            db=db,
            actor=actor,
            action=action,
            request=request,
            action_category=ActionCategory.SECURITY,
            target_type="rbac",
            target_id=f"required:{required_role}",
            changes={"attempted_action": action, "required_role": required_role},
            success=False,
            error_message=f"Access denied: requires {required_role}"
        )


# Singleton instance
audit_service = AuditService()


def get_audit_service() -> AuditService:
    """Get the audit service instance"""
    return audit_service
