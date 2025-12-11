"""
Rate Limiting Module

Clean, structured rate limiting with separate limiters for guests, users, and admins.
Multi-dimensional tracking: device fingerprint + geo IP + JWT + session for all roles.
Config-based limits, single source of truth, no code duplication.

Architecture:
- config.py: Centralized limit configuration
- tracking.py: Multi-dimensional tracking utilities  
- base.py: Base class with common functionality
- guest_limiter.py: Guest rate limiting (2/day default)
- user_limiter.py: User rate limiting (5/day default)
- admin_limiter.py: Admin rate limiting (100/day default)
- limiter.py: Unified facade that routes to appropriate limiter

Usage:
    from app.rate_limiting import get_rate_limiter
    
    limiter = get_rate_limiter()
    
    # Before operation: Check and enforce limit
    await limiter.check_and_enforce(request, user_id, is_admin)
    
    # Perform operation...
    
    # After success: Increment counter
    await limiter.increment(request, user_id, is_admin)
"""

from .config import rate_limit_config, get_limits
from .tracking import TrackingUtils
from .limiter import RateLimiter, get_rate_limiter
from .guest_limiter import get_guest_limiter
from .user_limiter import get_user_limiter
from .admin_limiter import get_admin_limiter

__all__ = [
    "rate_limit_config",
    "get_limits",
    "TrackingUtils",
    "RateLimiter",
    "get_rate_limiter",
    "get_guest_limiter",
    "get_user_limiter",
    "get_admin_limiter",
]
