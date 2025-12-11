"""
OTP (One-Time Password) Service for Email Verification
Uses Redis for temporary storage with 5-minute expiration
"""
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger

from app.core.redis_client import get_redis_client


class OTPService:
    """Service for generating and verifying OTPs"""
    
    OTP_LENGTH = 6
    OTP_TTL_SECONDS = 300  # 5 minutes
    MAX_ATTEMPTS = 3
    
    @staticmethod
    def generate_otp() -> str:
        """Generate a random 6-digit OTP"""
        return ''.join(secrets.choice(string.digits) for _ in range(OTPService.OTP_LENGTH))
    
    @staticmethod
    async def create_and_store_otp(email: str, purpose: str = "signup") -> str:
        """
        Create OTP and store in Redis
        
        Args:
            email: User email address
            purpose: 'signup', 'login', or 'password_reset'
            
        Returns:
            The generated OTP
        """
        redis = get_redis_client()
        otp = OTPService.generate_otp()
        
        # Redis keys
        otp_key = f"otp:{purpose}:{email}"
        attempts_key = f"otp_attempts:{purpose}:{email}"
        
        # Store OTP with TTL
        await redis.setex(otp_key, OTPService.OTP_TTL_SECONDS, otp)
        
        # Reset attempts counter
        await redis.setex(attempts_key, OTPService.OTP_TTL_SECONDS, "0")
        
        logger.info(f"[OTP] Generated OTP for {email} (purpose: {purpose})")
        return otp
    
    @staticmethod
    async def verify_otp(email: str, otp: str, purpose: str = "signup") -> bool:
        """
        Verify OTP
        
        Args:
            email: User email address
            otp: OTP to verify
            purpose: Must match the purpose used when creating
            
        Returns:
            True if OTP is valid, False otherwise
        """
        redis = get_redis_client()
        
        otp_key = f"otp:{purpose}:{email}"
        attempts_key = f"otp_attempts:{purpose}:{email}"
        
        # Check if OTP exists
        stored_otp = await redis.get(otp_key)
        if not stored_otp:
            logger.warning(f"[OTP] No OTP found for {email} (purpose: {purpose})")
            return False
        
        # Check attempts
        attempts = await redis.get(attempts_key)
        attempts = int(attempts) if attempts else 0
        
        if attempts >= OTPService.MAX_ATTEMPTS:
            logger.warning(f"[OTP] Max attempts exceeded for {email}")
            # Delete OTP after max attempts
            await redis.delete(otp_key)
            await redis.delete(attempts_key)
            return False
        
        # Increment attempts
        await redis.incr(attempts_key)
        
        # Verify OTP
        if stored_otp.decode() == otp:
            logger.info(f"[OTP] Verification successful for {email}")
            # Delete OTP after successful verification
            await redis.delete(otp_key)
            await redis.delete(attempts_key)
            return True
        
        logger.warning(f"[OTP] Invalid OTP for {email} (attempt {attempts + 1}/{OTPService.MAX_ATTEMPTS})")
        return False
    
    @staticmethod
    async def get_remaining_time(email: str, purpose: str = "signup") -> Optional[int]:
        """
        Get remaining time for OTP validity
        
        Returns:
            Remaining seconds, or None if OTP doesn't exist
        """
        redis = get_redis_client()
        otp_key = f"otp:{purpose}:{email}"
        
        ttl = await redis.ttl(otp_key)
        return ttl if ttl > 0 else None


# Singleton instance
_otp_service = OTPService()


def get_otp_service() -> OTPService:
    """Get OTP service instance"""
    return _otp_service
