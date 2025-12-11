"""
Guest tracking and utility endpoints
"""
from typing import Optional, Any
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from loguru import logger

from app.core.database import get_db
from app.services.guest_tracking import get_guest_tracking
from app.services.encryption_service import get_encryption_service
from app.middleware.auth_middleware import get_optional_user

router = APIRouter(tags=["tracking"])


@router.get("/guest/check-limit")
async def check_guest_limit(
    request: Request,
    guest_jwt_id: str = None,
    db: Session = Depends(get_db)
):
    """
    DEPRECATED: Use /tracking/user/check-limit instead.
    
    This endpoint is kept for backwards compatibility but redirects to the new
    unified rate limiting system.
    """
    logger.warning(
        "[DEPRECATED] /guest/check-limit called - redirecting to /user/check-limit. "
        "Please update frontend to use /tracking/user/check-limit directly."
    )
    
    # Redirect to new unified system
    return await check_user_limit(request, current_user=None)


@router.get("/user/check-limit")
async def check_user_limit(
    request: Request,
    current_user: Optional[Any] = Depends(get_optional_user)
):
    """
    Check user's analysis limit with multi-dimensional tracking.
    
    Returns remaining analyses and when they reset (rolling 24-hour window).
    Works for guests, users, and admins with appropriate limits.
    """
    from app.rate_limiting import get_rate_limiter, get_limits
    from app.core.redis_client import get_redis
    from datetime import datetime
    import hashlib
    
    # Determine user role
    user_id = current_user.id if current_user else None
    is_admin = current_user.is_admin if current_user and hasattr(current_user, 'is_admin') else False
    role = "admin" if is_admin else ("user" if user_id else "guest")
    
    # Get limits for this role
    limits = get_limits(role)
    
    # Check limit without incrementing
    rate_limiter = get_rate_limiter()
    allowed, remaining = await rate_limiter.check_limit(
        request=request,
        user_id=user_id,
        is_admin=is_admin,
        limit_type="analysis"
    )
    
    # Calculate reset_at from Redis TTL (rolling 24-hour window)
    reset_at = None
    try:
        from app.rate_limiting.tracking import TrackingUtils
        import hashlib
        redis = get_redis()
        
        # Try to build tracking keys using the same method as rate limiter
        tracking_keys = []
        try:
            tracking_keys = TrackingUtils.build_tracking_keys(
                request=request,
                user_id=user_id,
                role=role,
                limit_type="analysis"
            )
            logger.debug(f"[CHECK_LIMIT] Built {len(tracking_keys)} tracking keys")
        except ValueError as e:
            # Missing tracking headers - build fallback keys manually
            logger.warning(f"[CHECK_LIMIT] TrackingUtils failed: {e}. Building fallback keys...")
            
            # Build fallback keys without strict validation
            prefix = f"rate_limit:{role}"
            
            # Try session-based key
            session_id = request.headers.get("X-Session-ID")
            if session_id:
                tracking_keys.append(f"{prefix}:session:{session_id}:analysis")
            
            # Try IP-based key
            try:
                client_ip = TrackingUtils.get_client_ip(request)
                ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:16]
                tracking_keys.append(f"{prefix}:ip:{ip_hash}:analysis")
            except:
                pass
            
            # For users, try user-based key
            if user_id:
                tracking_keys.append(f"{prefix}:user:{user_id}:analysis")
            
            logger.info(f"[CHECK_LIMIT] Built {len(tracking_keys)} fallback keys")
        
        # Check all tracking keys for the one with the highest TTL
        max_ttl = -1
        for redis_key in tracking_keys:
            try:
                ttl = redis.ttl(redis_key)
                logger.debug(f"[CHECK_LIMIT] Key {redis_key}: TTL={ttl}s")
                if ttl > max_ttl:
                    max_ttl = ttl
            except Exception as key_error:
                logger.error(f"[CHECK_LIMIT] Error checking key {redis_key}: {key_error}")
        
        # Calculate reset timestamp from the highest TTL found
        if max_ttl > 0:
            reset_at = int(datetime.now().timestamp()) + max_ttl
            logger.info(f"[CHECK_LIMIT] ✅ Found TTL={max_ttl}s, reset_at={reset_at}")
        else:
            logger.debug(f"[CHECK_LIMIT] No active rate limit found (all keys have TTL <= 0)")
        
    except Exception as e:
        logger.error(f"[CHECK_LIMIT] Failed to get TTL: {e}", exc_info=True)
    
    logger.info(
        f"[CHECK_LIMIT] role={role}, user_id={user_id}, "
        f"remaining={remaining}/{limits['analysis_limit']}, allowed={allowed}, reset_at={reset_at}"
    )
    
    return {
        "remaining": remaining,
        "limit": limits["analysis_limit"],
        "role": role,
        "reset_at": reset_at  # Unix timestamp when limit resets (first_use + 24hrs)
    }


@router.post("/guest/record")
async def record_guest_request(
    request: Request,
    guest_jwt_id: str = None,
    db: Session = Depends(get_db)
):
    """
    Record a guest analysis request
    """
    guest_service = get_guest_tracking()
    
    # Check if allowed first
    check_result = await guest_service.check_guest_limit(
        request=request,
        guest_jwt_id=guest_jwt_id
    )
    
    if not check_result["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=f"Guest limit exceeded. {check_result['remaining']} requests remaining. "
                   f"Reset at: {check_result['reset_at']}"
        )
    
    # Record the request
    await guest_service.record_guest_request(
        request=request,
        guest_jwt_id=guest_jwt_id
    )
    
    return {"success": True, "remaining": check_result["remaining"] - 1}


@router.get("/encryption/public-key")
async def get_public_key():
    """
    Get RSA public key for client-side encryption
    """
    encryption_service = get_encryption_service()
    
    return {
        "public_key": encryption_service.get_public_key_pem()
    }
