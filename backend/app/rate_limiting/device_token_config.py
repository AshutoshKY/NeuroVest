"""
Device Token Configuration
Auto-generates secret key on first run, stores in Redis for persistence.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import secrets
import os


class DeviceTokenConfig(BaseSettings):
    """Device token configuration with auto-generated secret"""
    
    # Secret key for HMAC signing (auto-generated if not set)
    DEVICE_TOKEN_SECRET: str = ""
    
    # Token lifetime
    DEVICE_TOKEN_TTL_DAYS: int = 90  # 90 days as requested
    DEVICE_TOKEN_TTL_SECONDS: int = 90 * 24 * 3600  # 7,776,000 seconds
    
    # Security thresholds
    DEVICE_IP_CHANGE_LIMIT: int = 5  # Max IP changes per 24h before CAPTCHA
    DEVICE_REREGISTRATION_LIMIT: int = 10  # Max re-registrations per 24h
    
    # CAPTCHA settings
    ENABLE_CAPTCHA: bool = True
    CAPTCHA_ON_IP_CHANGE: bool = True  # Show CAPTCHA when IP changes
    CAPTCHA_ON_SUSPICIOUS: bool = True  # Show CAPTCHA on suspicious patterns
    
    # Suspicious pattern detection
    TRACK_DEVICE_ACTIVITY: bool = True
    SUSPICIOUS_ACTIVITY_WINDOW: int = 86400  # 24 hours
    
    class Config:
        env_prefix = "DEVICE_TOKEN_"
        env_file = ".env"
    
    def get_or_generate_secret(self, redis_client) -> str:
        """
        Get secret key from Redis or generate new one.
        Stores in Redis for persistence across restarts.
        """
        if self.DEVICE_TOKEN_SECRET:
            # Use from env if set
            return self.DEVICE_TOKEN_SECRET
        
        # Try to get from Redis
        secret_key = "device_token:secret_key"
        stored_secret = redis_client.get(secret_key)
        
        if stored_secret:
            return stored_secret
        
        # Generate new secret (256-bit for HMAC-SHA256)
        new_secret = secrets.token_hex(32)  # 32 bytes = 256 bits
        
        # Store in Redis (no expiry - persist forever)
        redis_client.set(secret_key, new_secret)
        
        return new_secret


# Global instance
device_token_config = DeviceTokenConfig()
