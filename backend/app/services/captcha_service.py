"""
CAPTCHA verification service
Supports hCaptcha and reCAPTCHA
"""
import httpx
import os
from typing import Optional
from loguru import logger


class CaptchaService:
    """CAPTCHA verification service"""
    
    def __init__(self):
        self.provider = os.getenv("CAPTCHA_PROVIDER", "hcaptcha")  # hcaptcha or recaptcha
        self.secret_key = os.getenv("CAPTCHA_SECRET_KEY", "")
        self.enabled = bool(self.secret_key)
        
        if self.enabled:
            logger.info(f"CAPTCHA enabled: {self.provider}")
        else:
            logger.warning("CAPTCHA disabled (no secret key)")
    
    async def verify_token(self, token: str, remote_ip: Optional[str] = None) -> tuple[bool, Optional[str]]:
        """
        Verify CAPTCHA token.
        
        Args:
            token: CAPTCHA response token from frontend
            remote_ip: Optional user IP address
        
        Returns:
            (success: bool, error_message: Optional[str])
        """
        if not self.enabled:
            # CAPTCHA disabled, allow through
            return True, None
        
        if not token:
            return False, "CAPTCHA token missing"
        
        try:
            # Determine verification URL based on provider
            if self.provider == "hcaptcha":
                verify_url = "https://hcaptcha.com/siteverify"
            else:  # recaptcha
                verify_url = "https://www.google.com/recaptcha/api/siteverify"
            
            # Prepare verification data
            data = {
                "secret": self.secret_key,
                "response": token
            }
            
            if remote_ip:
                data["remoteip"] = remote_ip
            
            # Send verification request
            async with httpx.AsyncClient() as client:
                response = await client.post(verify_url, data=data, timeout=10)
                result = response.json()
            
            # Check result
            success = result.get("success", False)
            
            if not success:
                error_codes = result.get("error-codes", [])
                error_msg = f"CAPTCHA verification failed: {', '.join(error_codes)}"
                logger.warning(f"[CAPTCHA] {error_msg}")
                return False, error_msg
            
            logger.info(f"[CAPTCHA] Verification successful")
            return True, None
            
        except Exception as e:
            logger.error(f"[CAPTCHA] Verification error: {e}")
            # On error, fail open (allow request)
            return True, None


# Global CAPTCHA service instance
_captcha_service: Optional[CaptchaService] = None


def get_captcha_service() -> CaptchaService:
    """Get CAPTCHA service instance"""
    global _captcha_service
    if _captcha_service is None:
        _captcha_service = CaptchaService()
    return _captcha_service


async def verify_captcha(token: str, remote_ip: Optional[str] = None) -> None:
    """
    Verify CAPTCHA token (helper function).
    Raises HTTPException if verification fails.
    """
    from fastapi import HTTPException, status
    
    service = get_captcha_service()
    success, error = await service.verify_token(token, remote_ip)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "CAPTCHA verification failed"
        )
