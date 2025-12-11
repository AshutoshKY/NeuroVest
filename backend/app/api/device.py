"""
Device Registration API Endpoints
"""

from typing import Dict, Optional
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
from loguru import logger

from app.rate_limiting.device_token_service import get_device_token_service


router = APIRouter(prefix="/device", tags=["device"])


class DeviceRegistrationRequest(BaseModel):
    """Request to register a device"""
    device_fingerprint: str
    captcha_token: Optional[str] = None


class DeviceRegistrationResponse(BaseModel):
    """Response from device registration"""
    device_token: Dict
    requires_captcha: bool
    warning_message: Optional[str] = None


@router.post("/register", response_model=DeviceRegistrationResponse)
async def register_device(
    data: DeviceRegistrationRequest,
    request: Request
):
    """
    Register a device and get signed token.
    
    Flow:
    1. Frontend sends device fingerprint
    2. Backend signs it with HMAC + IP + timestamp
    3. Returns signed token for frontend to store
    4. May require CAPTCHA if suspicious activity detected
    """
    device_service = get_device_token_service()
    
    # Register device
    result = device_service.register_device(
        request=request,
        device_fingerprint=data.device_fingerprint
    )
    
    warning = None
    if result["requires_captcha"]:
        if not data.captcha_token:
            # Need CAPTCHA but not provided
            raise HTTPException(
                status_code=428,  # Precondition Required
                detail="CAPTCHA verification required due to suspicious activity"
            )
        
        # TODO: Verify CAPTCHA token here
        # For now, just log
        logger.info(f"[DEVICE_API] CAPTCHA provided: {data.captcha_token[:16]}...")
        warning = "Suspicious activity detected - please verify you're human"
    
    logger.info(f"[DEVICE_API] Registered device successfully")
    
    return DeviceRegistrationResponse(
        device_token=result["device_token"],
        requires_captcha=result["requires_captcha"],
        warning_message=warning
    )


@router.post("/validate")
async def validate_device_token(
    device_token: Dict,
    request: Request
):
    """
    Validate a device token.
    
    Returns:
    - valid: true/false
    - error: error message if invalid
    - action: what frontend should do (re-register, show-captcha, etc.)
    """
    device_service = get_device_token_service()
    
    is_valid, error_msg, new_token = device_service.validate_token(
        request=request,
        device_token=device_token
    )
    
    if is_valid:
        return {
            "valid": True,
            "action": None
        }
    
    # Token invalid - determine action
    action = "re-register"  # Default
    requires_captcha = False
    
    if error_msg and "CAPTCHA" in error_msg:
        action = "show-captcha"
        requires_captcha = True
    elif error_msg and "IP changed" in error_msg:
        action = "show-warning-and-captcha"  # As per user request
        requires_captcha = True
    elif error_msg and "expired" in error_msg:
        action = "re-register"
        requires_captcha = False
    
    logger.info(
        f"[DEVICE_API] Token validation failed: {error_msg}, "
        f"action={action}, requires_captcha={requires_captcha}"
    )
    
    return {
        "valid": False,
        "error": error_msg,
        "action": action,
        "requires_captcha": requires_captcha
    }
