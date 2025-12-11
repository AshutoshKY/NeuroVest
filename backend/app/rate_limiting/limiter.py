"""
Unified Rate Limiter Facade.
Automatically selects appropriate limiter based on user role.
"""

from typing import Optional, Tuple, Dict
from fastapi import Request, HTTPException, status
from loguru import logger
import json

from .config import rate_limit_config, get_limits
from .guest_limiter import get_guest_limiter
from .user_limiter import get_user_limiter
from .admin_limiter import get_admin_limiter


class RateLimiter:
    """
    Unified rate limiter facade.
    Automatically routes to guest/user/admin limiter based on context.
    """
    
    def __init__(self):
        self.guest_limiter = get_guest_limiter()
        self.user_limiter = get_user_limiter()
        self.admin_limiter = get_admin_limiter()
    
    async def _validate_device_token(self, request: Request):
        """
        Validate device token before rate limiting.
        Ensures device token signature is valid.
        """
        from .device_token_service import get_device_token_service
        from .tracking import TrackingUtils
        
        device_token = TrackingUtils.get_device_token(request)
        if not device_token:
            # No device token provided - acceptable for now
            logger.debug("[RATE_LIMITER] No device token provided - continuing with IP tracking")
            return
        
        try:
            logger.debug("[RATE_LIMITER] Validating device token...")
            device_service = get_device_token_service()
            is_valid, error_msg, _ = device_service.validate_token(request, device_token)
            
            if not is_valid:
                logger.warning(f"[RATE_LIMITER] ❌ Device token validation failed: {error_msg}")
                raise HTTPException(
                    status_code=428,  # Precondition Required
                    detail=f"Device token validation failed: {error_msg}"
                )
            
            logger.info("[RATE_LIMITER] ✅ Device token valid")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[RATE_LIMITER] Device validation error: {e}")
            # Don't block on validation errors, just log
    
    def _get_user_role(self, user_id: Optional[int], is_admin: bool = False) -> str:
        """Determine user role"""
        if is_admin:
            return "admin"
        elif user_id:
            return "user"
        else:
            return "guest"
    
    def _get_limit_config(self, limits: dict, limit_type: str) -> dict:
        """
        Map limit_type to actual limit value, window, and time description.
        
        This fixes the bug where all limit types were using analysis limits.
        
        Args:
            limits: Dict from get_limits() with all limit values
            limit_type: Type of limit ('analysis', 'api_minute', 'auth_minute', etc.)
            
        Returns:
            Dict with 'limit', 'window', 'time_desc' keys
        """
        # Map limit_type to config
        if limit_type == "analysis":
            return {
                "limit": limits["analysis_limit"],
                "window": limits["analysis_window"],
                "time_desc": "per day"
            }
        elif limit_type == "api_minute":
            return {
                "limit": limits["api_minute_limit"],
                "window": 60,  # 1 minute in seconds
                "time_desc": "per minute"
            }
        elif limit_type == "auth_minute":
            return {
                "limit": limits.get("auth_minute_limit", limits["api_minute_limit"]),
                "window": 60,  # 1 minute in seconds
                "time_desc": "per minute"
            }
        elif limit_type == "api_hour":
            return {
                "limit": limits["api_hour_limit"],
                "window": 3600,  # 1 hour in seconds
                "time_desc": "per hour"
            }
        else:
            # Default to analysis limits for unknown types
            logger.warning(f"[RATE_LIMITER] Unknown limit_type: {limit_type}, using analysis limits")
            return {
                "limit": limits["analysis_limit"],
                "window": limits["analysis_window"],
                "time_desc": "per day"
            }

    
    async def check_and_enforce(
        self,
        request: Request,
        user_id: Optional[int] = None,
        is_admin: bool = False,
        limit_type: str = "analysis"
    ):
        """
        Check rate limit and raise HTTPException if exceeded.
        This is the main method to use in endpoints for enforcement.
        
        Args:
            request: FastAPI request
            user_id: User ID if authenticated  
            is_admin: True if user has admin role
            limit_type: Type of limit to check ('analysis', 'api_minute', 'auth_minute', etc.)
            
        Raises:
            HTTPException: If rate limit exceeded
        """
        if not rate_limit_config.RATE_LIMIT_ENABLED:
            logger.debug("[RATE_LIMITER] Rate limiting disabled")
            return
        
        # Validate device token first (if provided)
        await self._validate_device_token(request)
        
        role = self._get_user_role(user_id, is_admin)
        limits = get_limits(role)
        
        # Map limit_type to actual config values and time descriptions
        limit_config = self._get_limit_config(limits, limit_type)
        max_requests = limit_config["limit"]
        window_seconds = limit_config["window"]
        time_desc = limit_config["time_desc"]
        
        # Get appropriate limiter
        if role == "admin":
            limiter = self.admin_limiter
            identifier = user_id
        elif role == "user":
            limiter = self.user_limiter
            identifier = user_id
        else:  # guest
            limiter = self.guest_limiter
            identifier = None
        
        # Check limit
        allowed, remaining = await limiter.check_limit(
            request=request,
            identifier=identifier,
            limit_type=limit_type,
            max_requests=max_requests,
            window_seconds=window_seconds
        )
        
        if not allowed:
            detail = f"{role.title()} {limit_type} limit exceeded ({max_requests} {time_desc}). Try again later."
            logger.warning(f"[RATE_LIMITER] Blocked: {detail}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=detail,
                headers={"Retry-After": str(window_seconds // 60)}  # Minutes
            )
        
        logger.info(
            f"[RATE_LIMITER] Allowed: role={role}, limit_type={limit_type}, "
            f"remaining={remaining}/{max_requests} ({time_desc})"
        )
    
    async def check_limit(
        self,
        request: Request,
        user_id: Optional[int] = None,
        is_admin: bool = False,
        limit_type: str = "analysis"
    ) -> Tuple[bool, int]:
        """
        Check rate limit without raising exception.
        Returns (allowed, remaining).
        
        Use this for check-limit endpoints.
        """
        if not rate_limit_config.RATE_LIMIT_ENABLED:
            return True, 999
        
        # Validate device token (consistent with check_and_enforce)
        await self._validate_device_token(request)
        
        role = self._get_user_role(user_id, is_admin)
        limits = get_limits(role)
        
        # Map limit_type to actual config values (SAME FIX as check_and_enforce)
        limit_config = self._get_limit_config(limits, limit_type)
        max_requests = limit_config["limit"]
        window_seconds = limit_config["window"]
        
        # Get appropriate limiter
        if role == "admin":
            limiter = self.admin_limiter
            identifier = user_id
        elif role == "user":
            limiter = self.user_limiter
            identifier = user_id
        else:  # guest
            limiter = self.guest_limiter
            identifier = None
        
        return await limiter.check_limit(
            request=request,
            identifier=identifier,
            limit_type=limit_type,
            max_requests=max_requests,
            window_seconds=window_seconds  # ✅ Now passing correct window
        )
    
    async def increment(
        self,
        request: Request,
        user_id: Optional[int] = None,
        is_admin: bool = False,
        limit_type: str = "analysis"
    ) -> int:
        """
        Increment counter after successful operation.
        Call this ONLY after work completes successfully.
        
        Returns new count.
        """
        if not rate_limit_config.RATE_LIMIT_ENABLED:
            return 0
        
        role = self._get_user_role(user_id, is_admin)
        limits = get_limits(role)
        
        # Get correct window for this limit type
        limit_config = self._get_limit_config(limits, limit_type)
        window_seconds = limit_config["window"]
        
        # Get appropriate limiter
        if role == "admin":
            limiter = self.admin_limiter
            identifier = user_id
        elif role == "user":
            limiter = self.user_limiter
            identifier = user_id
        else:  # guest
            limiter = self.guest_limiter
            identifier = None
        
        return await limiter.increment(
            request=request,
            identifier=identifier,
            limit_type=limit_type,
            window_seconds=window_seconds  # ✅ Now passing correct window
        )


# Singleton instance
_rate_limiter = None


def get_rate_limiter() -> RateLimiter:
    """Get unified rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
