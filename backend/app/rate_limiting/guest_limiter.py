"""
Guest rate limiter - for unauthenticated users.
Uses multi-dimensional tracking: device fingerprint + session + IP + geo.
"""

from typing import Tuple
from fastapi import Request
from loguru import logger

from .base import BaseRateLimiter
from .config import rate_limit_config
from .tracking import TrackingUtils


class GuestRateLimiter(BaseRateLimiter):
    """
    Rate limiter for guest (unauthenticated) users.
    
    Tracking strategy:
    - Device fingerprint (prevents browser switching)
    - Session ID (prevents incognito bypass)
    - IP address (prevents device switching)
    - Geo location (optional analytics)
    
    Enforces limit across ALL tracking dimensions.
    User must wait if ANY dimension hits the limit.
    """
    
    @property
    def role(self) -> str:
        return "guest"
    
    async def check_limit(
        self,
        request: Request,
        identifier: any = None,  # Not used for guests
        limit_type: str = "analysis",
        max_requests: int = None,
        window_seconds: int = None
    ) -> Tuple[bool, int]:
        """
        Check guest rate limit across multiple tracking dimensions.
        
        Args:
            max_requests: REQUIRED - max requests for this limit_type
            window_seconds: REQUIRED - time window for this limit_type
        
        Returns (allowed, remaining) where remaining is based on 
        the dimension with the highest count.
        """
        # NO FALLBACKS - caller MUST provide correct values from config
        if max_requests is None or window_seconds is None:
            raise ValueError(
                f"max_requests and window_seconds are required. "
                f"Got max_requests={max_requests}, window_seconds={window_seconds}"
            )
        
        # Get all tracking keys for this guest
        tracking_keys = TrackingUtils.build_tracking_keys(
            request=request,
            user_id=None,  # Guests don't have user_id
            role=self.role,
            limit_type=limit_type
        )
        
        if not tracking_keys:
            logger.warning("[GUEST_LIMITER] No tracking keys generated!")
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
        
        context = TrackingUtils.get_request_context(request)
        logger.info(
            f"[GUEST_LIMITER] Check: limit_type={limit_type}, "
            f"count={max_count}/{max_requests}, remaining={remaining}, "
            f"allowed={allowed}, max_key={max_key}, context={context}"
        )
        
        return allowed, remaining
    
    async def increment(
        self,
        request: Request,
        identifier: any = None,  # Not used for guests
        limit_type: str = "analysis",
        window_seconds: int = None
    ) -> int:
        """
        Increment counters for ALL tracking dimensions.
        This ensures no dimension can be bypassed.
        
        CRITICAL: window_seconds MUST be passed from caller.
        Do NOT use hardcoded fallback - causes wrong TTL!
        """
        if window_seconds is None:
            raise ValueError(f"window_seconds is required for increment (limit_type={limit_type})")
        
        # Get all tracking keys
        tracking_keys = TrackingUtils.build_tracking_keys(
            request=request,
            user_id=None,
            role=self.role,
            limit_type=limit_type
        )
        
        # Increment all dimensions
        counts = []
        for key in tracking_keys:
            new_count = self._increment_count(key, window_seconds)
            counts.append(new_count)
        
        max_count = max(counts) if counts else 0
        
        context = TrackingUtils.get_request_context(request)
        logger.info(
            f"[GUEST_LIMITER] Incremented: limit_type={limit_type}, "
            f"new_count={max_count}, dimensions={len(tracking_keys)}, "
            f"context={context}"
        )
        
        return max_count


# Singleton instance
_guest_limiter = None


def get_guest_limiter() -> GuestRateLimiter:
    """Get guest rate limiter instance"""
    global _guest_limiter
    if _guest_limiter is None:
        _guest_limiter = GuestRateLimiter()
    return _guest_limiter
