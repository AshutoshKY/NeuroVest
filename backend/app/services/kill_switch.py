"""
Global Kill Switch System

Provides centralized control for emergency operations:
- Emergency shutdown (block all traffic except health checks)
- Block signups (disable new user registration)
- Block logins (disable authentication)
- Read-only DB mode (disable writes - future)
- Flush all sessions (force logout via auth_epoch)

All switches are backed by Redis for instant propagation.
MySQL auth_settings is used as fallback/persistence.

Admin restrictions:
- ADMIN can VIEW switch status
- SUPER_ADMIN can CHANGE switch status (with typed confirmation)
- Admin API endpoints BYPASS all kill switches for incident response
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone
from loguru import logger

from app.core.redis_client import get_redis


class KillSwitchType(str, Enum):
    """Available kill switch types"""
    EMERGENCY_SHUTDOWN = "emergency_shutdown"  # Block ALL traffic
    BLOCK_SIGNUPS = "block_signups"  # Disable new registrations
    BLOCK_LOGINS = "block_logins"  # Disable login (existing sessions still work)
    MAINTENANCE_MODE = "maintenance_mode"  # Return 503 with message
    READONLY_DB = "readonly_db"  # Block write operations (future)


@dataclass
class KillSwitch:
    """Kill switch state"""
    switch_type: KillSwitchType
    is_active: bool
    activated_by: Optional[int] = None  # User ID
    activated_at: Optional[datetime] = None
    reason: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "switch_type": self.switch_type.value,
            "is_active": self.is_active,
            "activated_by": self.activated_by,
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
            "reason": self.reason
        }


# Redis key pattern for kill switches
KILL_SWITCH_KEY_PREFIX = "killswitch:"
KILL_SWITCH_META_SUFFIX = ":meta"


# Paths that bypass kill switches (always accessible)
BYPASS_PATHS = [
    "/health",
    "/admin/",  # All admin endpoints bypass (for incident response)
    "/docs",
    "/openapi.json",
    "/redoc",
]


def _get_switch_key(switch_type: KillSwitchType) -> str:
    """Get Redis key for a kill switch"""
    return f"{KILL_SWITCH_KEY_PREFIX}{switch_type.value}"


def _get_meta_key(switch_type: KillSwitchType) -> str:
    """Get Redis key for kill switch metadata"""
    return f"{KILL_SWITCH_KEY_PREFIX}{switch_type.value}{KILL_SWITCH_META_SUFFIX}"


def is_switch_active(switch_type: KillSwitchType) -> bool:
    """
    Check if a kill switch is active.
    Fast Redis check - used by middleware.
    """
    try:
        redis = get_redis()
        key = _get_switch_key(switch_type)
        value = redis.get(key)
        # Handle both bytes and string returns from Redis
        if value is None:
            return False
        if isinstance(value, bytes):
            return value == b"1"
        return str(value) == "1"
    except Exception as e:
        logger.error(f"[KILL_SWITCH] Error checking {switch_type.value}: {e}")
        # Fail safe: if Redis is down, don't block traffic
        return False


def get_switch_status(switch_type: KillSwitchType) -> KillSwitch:
    """
    Get full status of a kill switch including metadata.
    Used by admin dashboard.
    """
    try:
        redis = get_redis()
        meta_key = _get_meta_key(switch_type)
        
        # Use the centralized is_switch_active function for consistency
        is_active = is_switch_active(switch_type)
        
        # Get metadata
        meta = redis.hgetall(meta_key)
        
        # Helper to get value from meta (handles both bytes and string keys)
        def get_meta_value(key: str):
            # Try bytes key first, then string key
            value = meta.get(key.encode()) or meta.get(key)
            if value is None:
                return None
            if isinstance(value, bytes):
                return value.decode()
            return str(value)
        
        activated_by_str = get_meta_value("activated_by")
        activated_by = int(activated_by_str) if activated_by_str and activated_by_str != "0" else None
        
        activated_at_str = get_meta_value("activated_at")
        activated_at = datetime.fromisoformat(activated_at_str) if activated_at_str else None
        
        reason = get_meta_value("reason")
        
        return KillSwitch(
            switch_type=switch_type,
            is_active=is_active,
            activated_by=activated_by,
            activated_at=activated_at,
            reason=reason
        )
    except Exception as e:
        logger.error(f"[KILL_SWITCH] Error getting status for {switch_type.value}: {e}")
        return KillSwitch(
            switch_type=switch_type,
            is_active=False,
            reason=f"Error: {str(e)}"
        )


def get_all_switches() -> Dict[str, KillSwitch]:
    """Get status of all kill switches"""
    return {
        switch_type.value: get_switch_status(switch_type)
        for switch_type in KillSwitchType
    }


def activate_switch(
    switch_type: KillSwitchType,
    user_id: int,
    reason: str
) -> bool:
    """
    Activate a kill switch.
    
    Args:
        switch_type: Which switch to activate
        user_id: SUPER_ADMIN user ID activating the switch
        reason: Reason for activation (for audit)
        
    Returns:
        True if activation successful
    """
    try:
        redis = get_redis()
        key = _get_switch_key(switch_type)
        meta_key = _get_meta_key(switch_type)
        now = datetime.now(timezone.utc)
        
        # Activate switch
        redis.set(key, "1")
        
        # Store metadata
        redis.hset(meta_key, mapping={
            "activated_by": str(user_id),
            "activated_at": now.isoformat(),
            "reason": reason
        })
        
        logger.warning(
            f"[KILL_SWITCH] ⚠️ ACTIVATED: {switch_type.value} "
            f"by user_id={user_id}, reason={reason}"
        )
        
        return True
        
    except Exception as e:
        logger.error(f"[KILL_SWITCH] Failed to activate {switch_type.value}: {e}")
        raise


def deactivate_switch(
    switch_type: KillSwitchType,
    user_id: int,
    reason: str = ""
) -> bool:
    """
    Deactivate a kill switch.
    
    Args:
        switch_type: Which switch to deactivate
        user_id: SUPER_ADMIN user ID deactivating the switch
        reason: Optional reason for deactivation
        
    Returns:
        True if deactivation successful
    """
    try:
        redis = get_redis()
        key = _get_switch_key(switch_type)
        meta_key = _get_meta_key(switch_type)
        
        # Deactivate switch
        redis.set(key, "0")
        
        # Clear metadata (keep small log trail)
        redis.delete(meta_key)
        
        logger.info(
            f"[KILL_SWITCH] ✅ DEACTIVATED: {switch_type.value} "
            f"by user_id={user_id}"
        )
        
        return True
        
    except Exception as e:
        logger.error(f"[KILL_SWITCH] Failed to deactivate {switch_type.value}: {e}")
        raise


def should_bypass_kill_switch(path: str) -> bool:
    """
    Check if a request path should bypass kill switches.
    Admin APIs always bypass for incident response capability.
    
    Args:
        path: Request path (e.g., "/admin/session/status")
        
    Returns:
        True if path should bypass kill switches
    """
    for bypass_path in BYPASS_PATHS:
        if path.startswith(bypass_path):
            return True
    return False


def get_active_blocks() -> List[str]:
    """
    Get list of currently active traffic blocks.
    Used by middleware to quickly check what's blocked.
    """
    active = []
    for switch_type in KillSwitchType:
        if is_switch_active(switch_type):
            active.append(switch_type.value)
    return active


# Confirmation codes for each switch (must match CONFIRMATION_CODES in rbac.py)
SWITCH_CONFIRMATION_CODES = {
    KillSwitchType.EMERGENCY_SHUTDOWN: "SHUTDOWN",
    KillSwitchType.BLOCK_SIGNUPS: "BLOCK",
    KillSwitchType.BLOCK_LOGINS: "BLOCK",
    KillSwitchType.MAINTENANCE_MODE: "MAINTENANCE",
    KillSwitchType.READONLY_DB: "READONLY",
}


def validate_switch_confirmation(switch_type: KillSwitchType, confirmation: str) -> bool:
    """Validate typed confirmation for a kill switch activation"""
    expected = SWITCH_CONFIRMATION_CODES.get(switch_type)
    if not expected:
        return False
    return confirmation.strip().upper() == expected.upper()
