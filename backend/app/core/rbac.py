"""
RBAC (Role-Based Access Control) Dependencies for Admin Command Center

Role Hierarchy:
- USER: Regular user, no admin access
- ADMIN: Read-only monitoring access (can view dashboards, cannot mutate)
- SUPER_ADMIN: Full admin access including dangerous operations

Usage:
    @router.get("/admin/overview")
    async def get_overview(user: User = Depends(require_admin)):
        ...  # ADMIN and SUPER_ADMIN can access
    
    @router.post("/admin/kill-switch")
    async def activate_kill_switch(user: User = Depends(require_super_admin)):
        ...  # Only SUPER_ADMIN can access
"""

from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User, UserRole


class RBACError(HTTPException):
    """Custom exception for RBAC violations with audit-friendly details"""
    def __init__(self, required_role: str, actual_role: str, action: str = None):
        detail = f"Access denied. Required: {required_role}, Your role: {actual_role}"
        if action:
            detail += f". Action: {action}"
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency that requires ADMIN or SUPER_ADMIN role.
    Use for read-only monitoring endpoints.
    
    Returns the user if authorized.
    Raises 403 if user is not an admin.
    """
    if not current_user.is_admin:
        raise RBACError(
            required_role="admin or super_admin",
            actual_role=current_user.role if isinstance(current_user.role, str) else current_user.role.value,
            action="admin dashboard access"
        )
    return current_user


async def require_super_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency that requires SUPER_ADMIN role.
    Use for dangerous operations (kill switches, force logout, config changes).
    
    Returns the user if authorized.
    Raises 403 if user is not a super admin.
    """
    if not current_user.is_super_admin:
        raise RBACError(
            required_role="super_admin",
            actual_role=current_user.role if isinstance(current_user.role, str) else current_user.role.value,
            action="dangerous operation access"
        )
    return current_user


async def require_admin_or_self(
    user_id: int,
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency that allows:
    - Any ADMIN or SUPER_ADMIN
    - The user themselves (for self-service actions)
    
    Useful for endpoints like viewing own sessions.
    """
    if current_user.is_admin or current_user.id == user_id:
        return current_user
    
    raise RBACError(
        required_role="admin or self",
        actual_role=current_user.role if isinstance(current_user.role, str) else current_user.role.value,
        action=f"access user_id={user_id}"
    )


def get_role_display_name(role: str) -> str:
    """Get human-readable role name for audit logs"""
    role_names = {
        "user": "User",
        "admin": "Admin (Read-Only)",
        "super_admin": "Super Admin"
    }
    return role_names.get(role, role)


def can_perform_action(user: User, action: str) -> bool:
    """
    Check if user can perform a specific action.
    Returns boolean instead of raising exception.
    
    Actions:
    - view_dashboard: ADMIN, SUPER_ADMIN
    - view_users: ADMIN, SUPER_ADMIN
    - disable_user: SUPER_ADMIN
    - enable_user: SUPER_ADMIN
    - toggle_kill_switch: SUPER_ADMIN
    - force_logout: SUPER_ADMIN
    - modify_config: SUPER_ADMIN
    - view_audit_logs: ADMIN, SUPER_ADMIN
    - export_data: SUPER_ADMIN
    """
    admin_actions = {
        "view_dashboard",
        "view_users",
        "view_audit_logs",
        "view_metrics",
        "view_infrastructure",
        "view_security",
    }
    
    super_admin_actions = {
        "disable_user",
        "enable_user",
        "toggle_kill_switch",
        "force_logout",
        "force_logout_all",
        "modify_config",
        "blacklist_ip",
        "unblock_ip",
        "export_data",
        "modify_toggle",
    }
    
    if action in admin_actions:
        return user.is_admin  # Both ADMIN and SUPER_ADMIN
    
    if action in super_admin_actions:
        return user.is_super_admin  # Only SUPER_ADMIN
    
    return False


# Confirmation constants for dangerous actions
CONFIRMATION_CODES = {
    "emergency_shutdown": "SHUTDOWN",
    "force_logout_all": "LOGOUT_ALL",
    "block_logins": "BLOCK",
    "readonly_db": "READONLY",
    "flush_sessions": "FLUSH",
}


def validate_confirmation(action: str, confirmation: str) -> bool:
    """
    Validate typed confirmation for dangerous actions.
    User must type exact confirmation code.
    """
    expected = CONFIRMATION_CODES.get(action)
    if not expected:
        return False
    return confirmation.strip().upper() == expected.upper()
