"""
Admin Session Control API

Provides endpoints for managing user sessions and force logout.
All endpoints require SUPER_ADMIN role and typed confirmation.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import require_super_admin, validate_confirmation, CONFIRMATION_CODES
from app.models.user import User
from app.services.session_control import (
    increment_auth_epoch,
    get_session_control_status,
    sync_auth_epoch_from_mysql
)
from app.services.audit_service import AuditService
from app.models.audit_log import AuditAction, ActionCategory


router = APIRouter(prefix="/admin/session", tags=["admin-session"])


# ==================== SCHEMAS ====================

class ForceLogoutAllRequest(BaseModel):
    """Request body for force logout all users"""
    confirmation: str  # Must type "LOGOUT_ALL" exactly
    reason: str


# ==================== ENDPOINTS ====================

@router.get("/status")
async def get_session_status(
    current_user: User = Depends(require_super_admin)
):
    """
    Get current session control status including auth_epoch.
    Read-only but requires SUPER_ADMIN to see security info.
    """
    return get_session_control_status()


@router.post("/sync-epoch")
async def sync_epoch_from_database(
    current_user: User = Depends(require_super_admin)
):
    """
    Sync auth_epoch from MySQL to Redis.
    Useful after database restore or Redis restart.
    """
    epoch = sync_auth_epoch_from_mysql()
    return {
        "success": True,
        "auth_epoch": epoch,
        "message": "Auth epoch synced from MySQL to Redis"
    }


@router.post("/force-logout-all")
async def force_logout_all_users(
    request: ForceLogoutAllRequest,
    http_request: Request,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """
    Force logout ALL users by incrementing auth_epoch.
    
    This is a DANGEROUS operation:
    - Immediately invalidates ALL existing tokens
    - All users must re-login
    - Use only for security incidents
    
    Requires:
    - SUPER_ADMIN role
    - Type "LOGOUT_ALL" as confirmation
    - Provide a reason for audit
    """
    # Validate typed confirmation
    if not validate_confirmation("force_logout_all", request.confirmation):
        AuditService.log_action(
            db=db,
            actor=current_user,
            action=AuditAction.FORCE_LOGOUT_ALL,
            request=http_request,
            action_category=ActionCategory.SECURITY,
            target_type="system",
            target_id="all_users",
            changes={"reason": request.reason, "confirmation_failed": True},
            success=False,
            error_message=f"Invalid confirmation code. Expected: {CONFIRMATION_CODES['force_logout_all']}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid confirmation. Type '{CONFIRMATION_CODES['force_logout_all']}' exactly to confirm."
        )
    
    try:
        # Get old epoch for logging
        old_status = get_session_control_status()
        old_epoch = old_status.get("auth_epoch", 0)
        
        # Increment epoch - this invalidates all tokens
        new_epoch = increment_auth_epoch()
        
        # Log the dangerous action
        AuditService.log_dangerous_action(
            db=db,
            actor=current_user,
            action=AuditAction.FORCE_LOGOUT_ALL,
            confirmation_code=request.confirmation,
            request=http_request,
            target_type="system",
            target_id="all_users",
            changes={
                "reason": request.reason,
                "old_epoch": old_epoch,
                "new_epoch": new_epoch
            },
            success=True
        )
        
        return {
            "success": True,
            "message": "⚠️ All user sessions invalidated. All users must re-login.",
            "old_epoch": old_epoch,
            "new_epoch": new_epoch,
            "actors": {
                "admin_id": current_user.id,
                "admin_email": current_user.email
            }
        }
        
    except Exception as e:
        # Log failure
        AuditService.log_action(
            db=db,
            actor=current_user,
            action=AuditAction.FORCE_LOGOUT_ALL,
            request=http_request,
            action_category=ActionCategory.SECURITY,
            target_type="system",
            target_id="all_users",
            changes={"reason": request.reason},
            success=False,
            error_message=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to force logout all users: {str(e)}"
        )
