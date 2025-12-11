# Rate Limiting Configuration

"""
Centralized configuration for all rate limiting across the application.
Define limits for guests, users, and admins separately.
"""

from pydantic_settings import BaseSettings
from typing import Dict


class RateLimitConfig(BaseSettings):
    """Rate limiting configuration"""
    
    # ============================================
    # GUEST USER LIMITS (Unauthenticated)
    # ============================================
    GUEST_ANALYSIS_LIMIT: int = 2  # analyses per day
    GUEST_ANALYSIS_WINDOW: int = 86400  # 24 hours in seconds
    
    GUEST_API_MINUTE_LIMIT: int = 30  # API calls per minute
    GUEST_AUTH_MINUTE_LIMIT: int = 50  # Auth endpoint calls per minute (increased for login/refresh/validate)
    GUEST_API_HOUR_LIMIT: int = 500  # API calls per hour
    
    # ============================================
    # AUTHENTICATED USER LIMITS
    # ============================================
    USER_ANALYSIS_LIMIT: int = 5  # analyses per day
    USER_ANALYSIS_WINDOW: int = 86400  # 24 hours in seconds
    
    USER_API_MINUTE_LIMIT: int = 60  # API calls per minute
    USER_AUTH_MINUTE_LIMIT: int = 20  # Auth endpoint calls per minute
    USER_API_HOUR_LIMIT: int = 1000  # API calls per hour
    
    # ============================================
    # ADMIN LIMITS (Privileged)
    # ============================================
    ADMIN_ANALYSIS_LIMIT: int = 100  # analyses per day
    ADMIN_ANALYSIS_WINDOW: int = 86400  # 24 hours in seconds
    
    ADMIN_API_MINUTE_LIMIT: int = 200  # API calls per minute  
    ADMIN_AUTH_MINUTE_LIMIT: int = 50  # Auth endpoint calls per minute
    ADMIN_API_HOUR_LIMIT: int = 5000  # API calls per hour
    
    # ============================================
    # ENFORCEMENT STRATEGIES
    # ============================================
    # For guests: Combine IP + Session tracking
    GUEST_USE_IP_TRACKING: bool = True
    GUEST_USE_SESSION_TRACKING: bool = True
    
    # For users: Only user_id tracking (allow multiple devices)
    USER_USE_IP_TRACKING: bool = False
    USER_USE_SESSION_TRACKING: bool = False
    
    # For admins: No IP/session limits
    ADMIN_USE_IP_TRACKING: bool = False
    ADMIN_USE_SESSION_TRACKING: bool = False
    
    # ============================================
    # GENERAL SETTINGS
    # ============================================
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REDIS_PREFIX: str = "rate_limit"
    
    class Config:
        env_prefix = "RATE_LIMIT_"
        env_file = ".env"


# Global config instance
rate_limit_config = RateLimitConfig()


def get_limits(user_role: str = "guest") -> Dict[str, int]:
    """
    Get rate limits for a specific user role.
    
    Args:
        user_role: One of 'guest', 'user', 'admin'
        
    Returns:
        Dictionary with limit values
    """
    if user_role == "admin":
        return {
            "analysis_limit": rate_limit_config.ADMIN_ANALYSIS_LIMIT,
            "analysis_window": rate_limit_config.ADMIN_ANALYSIS_WINDOW,
            "api_minute_limit": rate_limit_config.ADMIN_API_MINUTE_LIMIT,
            "api_hour_limit": rate_limit_config.ADMIN_API_HOUR_LIMIT,
        }
    elif user_role == "user":
        return {
            "analysis_limit": rate_limit_config.USER_ANALYSIS_LIMIT,
            "analysis_window": rate_limit_config.USER_ANALYSIS_WINDOW,
            "api_minute_limit": rate_limit_config.USER_API_MINUTE_LIMIT,
            "api_hour_limit": rate_limit_config.USER_API_HOUR_LIMIT,
        }
    else:  # guest
        return {
            "analysis_limit": rate_limit_config.GUEST_ANALYSIS_LIMIT,
            "analysis_window": rate_limit_config.GUEST_ANALYSIS_WINDOW,
            "api_minute_limit": rate_limit_config.GUEST_API_MINUTE_LIMIT,
            "api_hour_limit": rate_limit_config.GUEST_API_HOUR_LIMIT,
        }
