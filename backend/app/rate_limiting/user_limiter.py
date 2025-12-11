"""
User rate limiter - for authenticated users.
Uses multi-dimensional tracking: user_id + device fingerprint + session +IP + geo + JWT.
"""

from typing import Tuple
from fastapi import Request
from loguru import logger

from .base import BaseRateLimiter
from .config import rate_limit_config
from .tracking import TrackingUtils


class UserRateLimiter(BaseRateLimiter):
    """
    Rate limiter for authenticated (non-admin) users.
    
    Tracking strategy:
    - User ID from JWT (primary identifier)
    - Device fingerprint (prevents device hopping)
    - Session ID (prevents session manipulation)
    - IP address (prevents proxy abuse)
    - Geo location (optional analytics)
    
    Enforces limit across ALL dimensions to prevent abuse.
    """
    
    @property
    def role(self) -> str:
        return "user"
    
    async def check_limit(
        self,
        request: Request,
        identifier: int,  # user_id from JWT
        limit_type: str = "analysis",
        max_requests: int = None,
        window_seconds: int = None
    ) -> Tuple[bool, int]:
        """
        Check user rate limit across multiple tracking dimensions.
        
        Args:
            identifier: user_id from authenticated JWT token
            max_requests: REQUIRED - max requests for this limit_type
            window_seconds: REQUIRED - time window for this limit_type
        
        Returns:
            Tuple[bool, int]: (allowed, remaining)
        """
        # NO FALLBACKS - caller MUST provide correct values from config
        if max_requests is None or window_seconds is None:
            raise ValueError(
                f"max_requests and window_seconds are required. "
                f"Got max_requests={max_requests}, window_seconds={window_seconds}"
            )
        
        if not identifier:
            raise ValueError("user_id required for UserRateLimiter")
       
        # Get all tracking keys for this user
        tracking_keys = TrackingUtils.build_tracking_keys(
            request=request,
            user_id=identifier,  # Include user_id in tracking
            role=self.role,
            limit_type=limit_type
        )
        
        if not tracking_keys:
            logger.warning(f"[USER_LIMITER] No tracking keys for user_id={identifier}!")
            return True, max_requests
        
        # Check all dimensions, use highest count
        max_count = 0
        max_key = None
        
        for key in tracking_keys:
            count = self._get_current_count(key)
            if count > max_count:
                max_count = count
                max_key = key
        
        allowed = max_count < max_requests
        remaining = max(0, max_requests - max_count)
        
        context = TrackingUtils.get_request_context(request, identifier)
        logger.info(
            f"[USER_LIMITER] Check: user_id={identifier}, limit_type={limit_type}, "
            f"count={max_count}/{max_requests}, remaining={remaining}, "
            f"allowed={allowed}, max_key={max_key}, context={context}"
        )
        
        return allowed, remaining
    
    async def increment(
        self,
        request: Request,
        identifier: int,  # user_id from JWT
        limit_type: str = "analysis",
        window_seconds: int = None
    ) -> int:
        """
        Increment counters for ALL tracking dimensions.
        Ensures comprehensive abuse prevention.
        """
        if window_seconds is None:
            window_seconds = rate_limit_config.USER_ANALYSIS_WINDOW
        
        if not identifier:
            raise ValueError("user_id required for UserRateLimiter")
        
        # Get all tracking keys
        tracking_keys = TrackingUtils.build_tracking_keys(
            request=request,
            user_id=identifier,
            role=self.role,
            limit_type=limit_type
        )
        
        # Increment all dimensions
        counts = []
        for key in tracking_keys:
            new_count = self._increment_count(key, window_seconds)
            counts.append(new_count)
        
        max_count = max(counts) if counts else 0
        
        context = TrackingUtils.get_request_context(request, identifier)
        logger.info(
            f"[USER_LIMITER] Incremented: user_id={identifier}, limit_type={limit_type}, "
            f"new_count={max_count}, dimensions={len(tracking_keys)}, "
            f"context={context}"
        )
        
        return max_count


# Singleton instance
_user_limiter = None


def get_user_limiter() -> UserRateLimiter:
    """Get user rate limiter instance"""
    global _user_limiter
    if _user_limiter is None:
        _user_limiter = UserRateLimiter()
    return _user_limiter
