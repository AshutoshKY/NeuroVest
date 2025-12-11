
"""
Guest user tracking service
Multi-layer tracking: Device fingerprinting + Guest JWT + IP + localStorage
Allows 2 free analysis requests per device with 24-hour rolling window
"""
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import Request
from loguru import logger

from app.core.redis_client import get_redis


class GuestTrackingService:
    """Service for tracking guest user analysis requests"""
    
    MAX_GUEST_REQUESTS = 2
    ROLLING_WINDOW_HOURS = 24
    
    @staticmethod
    def generate_device_fingerprint(request: Request, additional_data: Optional[Dict] = None) -> str:
        """
        Generate unique device fingerprint from request
        
        Combines:
        - IP address
        - User-Agent
        - Accept-Language
        - Screen resolution (from frontend)
        - Timezone (from frontend)
        - Canvas fingerprint (from frontend)
        """
        ip = request.client.host
        user_agent = request.headers.get("user-agent", "unknown")
        accept_lang = request.headers.get("accept-language", "unknown")
        
        # Additional data from frontend (optional)
        screen_res = ""
        timezone = ""
        canvas = ""
        
        if additional_data:
            screen_res = additional_data.get("screen_resolution", "")
            timezone = additional_data.get("timezone", "")
            canvas = additional_data.get("canvas_fingerprint", "")
        
        # Combine all factors
        fingerprint_data = f"{ip}:{user_agent}:{accept_lang}:{screen_res}:{timezone}:{canvas}"
        
        # Hash to create unique ID
        fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()
        
        logger.debug(f"[GUEST_TRACKING] Generated fingerprint: {fingerprint[:16]}... for IP: {ip}")
        return fingerprint
    
    @staticmethod
    async def check_guest_limit(
        request: Request,
        device_fingerprint: Optional[str] = None,
        guest_jwt_id: Optional[str] = None
    ) -> Dict:
        """
        Check if guest user can make another request
        
        Returns:
            {
                "allowed": bool,
                "remaining": int,
                "reset_at": datetime or None,
                "fingerprint": str
            }
        """
        redis = get_redis()
        
        # Generate fingerprint if not provided
        if not device_fingerprint:
            device_fingerprint = GuestTrackingService.generate_device_fingerprint(request)
        
        # Create tracking keys (check multiple layers)
        keys = [
            f"guest:fingerprint:{device_fingerprint}",
            f"guest:ip:{request.client.host}",
        ]
        
        if guest_jwt_id:
            keys.append(f"guest:jwt:{guest_jwt_id}")
        
        # Check all keys - if any hit limit, deny
        max_count = 0
        earliest_timestamp = None
        
        for key in keys:
            # Get request log (list of timestamps)
            request_log = redis.lrange(key, 0, -1)
            
            if request_log:
                # Parse timestamps
                timestamps = [datetime.fromisoformat(ts if isinstance(ts, str) else ts.decode()) for ts in request_log]
                
                # Filter timestamps within rolling window
                cutoff = datetime.utcnow() - timedelta(hours=GuestTrackingService.ROLLING_WINDOW_HOURS)
                valid_timestamps = [ts for ts in timestamps if ts > cutoff]
                
                count = len(valid_timestamps)
                if count > max_count:
                    max_count = count
                    if valid_timestamps:
                        earliest_timestamp = min(valid_timestamps)
        
        # Calculate remaining requests
        remaining = max(0, GuestTrackingService.MAX_GUEST_REQUESTS - max_count)
        allowed = remaining > 0
        
        # Calculate reset time
        reset_at = None
        if earliest_timestamp and max_count >= GuestTrackingService.MAX_GUEST_REQUESTS:
            reset_at = earliest_timestamp + timedelta(hours=GuestTrackingService.ROLLING_WINDOW_HOURS)
        
        logger.info(f"[GUEST_TRACKING] Check limit: fingerprint={device_fingerprint[:16]}..., "
                   f"allowed={allowed}, remaining={remaining}, count={max_count}")
        
        return {
            "allowed": allowed,
            "remaining": remaining,
            "reset_at": reset_at,
            "fingerprint": device_fingerprint,
            "current_count": max_count,
            "limit": GuestTrackingService.MAX_GUEST_REQUESTS
        }
    
    @staticmethod
    async def record_guest_request(
        request: Request,
        device_fingerprint: Optional[str] = None,
        guest_jwt_id: Optional[str] = None
    ):
        """
        Record a guest request
        """
        redis = get_redis()
        
        if not device_fingerprint:
            device_fingerprint = GuestTrackingService.generate_device_fingerprint(request)
        
        timestamp = datetime.utcnow().isoformat()
        ttl_seconds = GuestTrackingService.ROLLING_WINDOW_HOURS * 3600
        
        # Record in all tracking layers
        keys = [
            f"guest:fingerprint:{device_fingerprint}",
            f"guest:ip:{request.client.host}",
        ]
        
        if guest_jwt_id:
            keys.append(f"guest:jwt:{guest_jwt_id}")
        
        for key in keys:
            # Add timestamp to list
            redis.rpush(key, timestamp)
            
            # Set expiration
            redis.expire(key, ttl_seconds)
            
            # Trim list to keep only recent entries (optimization)
            redis.ltrim(key, -10, -1)  # Keep last 10 entries
        
        logger.info(f"[GUEST_TRACKING] Recorded request: fingerprint={device_fingerprint[:16]}..., "
                   f"IP={request.client.host}")


# Singleton instance
_guest_tracking = GuestTrackingService()


def get_guest_tracking() -> GuestTrackingService:
    """Get guest tracking service instance"""
    return _guest_tracking
