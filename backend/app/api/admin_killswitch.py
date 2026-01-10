"""
Admin Kill Switch API

Provides endpoints for managing global kill switches.
- GET: View all switch statuses (ADMIN or SUPER_ADMIN)
- POST: Activate/deactivate switches (SUPER_ADMIN only + typed confirmation)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.rbac import require_admin, require_super_admin
from app.models.user import User
from app.services.kill_switch import (
    KillSwitchType,
    get_all_switches,
    get_switch_status,
    activate_switch,
    deactivate_switch,
    validate_switch_confirmation,
    SWITCH_CONFIRMATION_CODES
)
from app.services.audit_service import AuditService
from app.models.audit_log import AuditAction, ActionCategory


router = APIRouter(prefix="/admin/killswitch", tags=["admin-killswitch"])


# ==================== SCHEMAS ====================

class ActivateSwitchRequest(BaseModel):
    """Request body for activating a kill switch"""
    switch_type: str  # e.g., "emergency_shutdown"
    confirmation: str  # Must type exact code
    reason: str


class DeactivateSwitchRequest(BaseModel):
    """Request body for deactivating a kill switch"""
    switch_type: str
    reason: Optional[str] = ""


# ==================== ENDPOINTS ====================

@router.get("/status")
async def get_all_switch_status(
    current_user: User = Depends(require_admin)  # ADMIN or SUPER_ADMIN can view
):
    """
    Get status of all kill switches.
    Read-only - ADMIN and SUPER_ADMIN can access.
    """
    switches = get_all_switches()
    return {
        "switches": {name: switch.to_dict() for name, switch in switches.items()},
        "confirmation_codes": SWITCH_CONFIRMATION_CODES  # Show codes for UI
    }


@router.get("/status/{switch_type}")
async def get_single_switch_status(
    switch_type: str,
    current_user: User = Depends(require_admin)  # ADMIN or SUPER_ADMIN can view
):
    """
    Get status of a specific kill switch.
    """
    try:
        switch_enum = KillSwitchType(switch_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid switch type. Valid types: {[s.value for s in KillSwitchType]}"
        )
    
    switch = get_switch_status(switch_enum)
    return switch.to_dict()


@router.post("/activate")
async def activate_kill_switch(
    request: ActivateSwitchRequest,
    http_request: Request,
    current_user: User = Depends(require_super_admin),  # SUPER_ADMIN only
    db: Session = Depends(get_db)
):
    """
    Activate a kill switch.
    
    This is a DANGEROUS operation that affects all users.
    Requires:
    - SUPER_ADMIN role
    - Typed confirmation matching the switch code
    - Reason for audit trail
    """
    # Validate switch type
    try:
        switch_enum = KillSwitchType(request.switch_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid switch type. Valid types: {[s.value for s in KillSwitchType]}"
        )
    
    # Validate typed confirmation
    if not validate_switch_confirmation(switch_enum, request.confirmation):
        expected = SWITCH_CONFIRMATION_CODES.get(switch_enum, "UNKNOWN")
        AuditService.log_action(
            db=db,
            actor=current_user,
            action=AuditAction.ENABLE_KILL_SWITCH,
            request=http_request,
            action_category=ActionCategory.SYSTEM,
            target_type="kill_switch",
            target_id=request.switch_type,
            changes={"reason": request.reason, "confirmation_failed": True},
            success=False,
            error_message=f"Invalid confirmation. Expected: {expected}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid confirmation. Type '{expected}' exactly to confirm."
        )
    
    try:
        # Activate the switch
        activate_switch(switch_enum, current_user.id, request.reason)
        
        # Log successful activation
        AuditService.log_dangerous_action(
            db=db,
            actor=current_user,
            action=AuditAction.ENABLE_KILL_SWITCH,
            confirmation_code=request.confirmation,
            request=http_request,
            target_type="kill_switch",
            target_id=request.switch_type,
            changes={"reason": request.reason, "state": "activated"}
        )
        
        # Get updated status
        new_status = get_switch_status(switch_enum)
        
        return {
            "success": True,
            "message": f"⚠️ Kill switch '{request.switch_type}' ACTIVATED",
            "switch": new_status.to_dict(),
            "actor": {
                "admin_id": current_user.id,
                "admin_email": current_user.email
            }
        }
        
    except Exception as e:
        AuditService.log_action(
            db=db,
            actor=current_user,
            action=AuditAction.ENABLE_KILL_SWITCH,
            request=http_request,
            action_category=ActionCategory.SYSTEM,
            target_type="kill_switch",
            target_id=request.switch_type,
            changes={"reason": request.reason},
            success=False,
            error_message=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate kill switch: {str(e)}"
        )


@router.post("/deactivate")
async def deactivate_kill_switch(
    request: DeactivateSwitchRequest,
    http_request: Request,
    current_user: User = Depends(require_super_admin),  # SUPER_ADMIN only
    db: Session = Depends(get_db)
):
    """
    Deactivate a kill switch.
    
    Requires SUPER_ADMIN role.
    No confirmation needed for deactivation (safer operation).
    """
    # Validate switch type
    try:
        switch_enum = KillSwitchType(request.switch_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid switch type. Valid types: {[s.value for s in KillSwitchType]}"
        )
    
    try:
        # Deactivate the switch
        deactivate_switch(switch_enum, current_user.id, request.reason or "")
        
        # Log deactivation
        AuditService.log_action(
            db=db,
            actor=current_user,
            action=AuditAction.DISABLE_KILL_SWITCH,
            request=http_request,
            action_category=ActionCategory.SYSTEM,
            target_type="kill_switch",
            target_id=request.switch_type,
            changes={"reason": request.reason, "state": "deactivated"}
        )
        
        return {
            "success": True,
            "message": f"✅ Kill switch '{request.switch_type}' DEACTIVATED",
            "actor": {
                "admin_id": current_user.id,
                "admin_email": current_user.email
            }
        }
        
    except Exception as e:
        AuditService.log_action(
            db=db,
            actor=current_user,
            action=AuditAction.DISABLE_KILL_SWITCH,
            request=http_request,
            action_category=ActionCategory.SYSTEM,
            target_type="kill_switch",
            target_id=request.switch_type,
            changes={"reason": request.reason},
            success=False,
            error_message=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate kill switch: {str(e)}"
        )
