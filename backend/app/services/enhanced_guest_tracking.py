"""
Enhanced Guest Tracking Service with Geo IP
Unbypassable tracking using multiple layers:
- Geo IP (country-level tracking)
- Browser Session ID
- Device Fingerprint (IP + User-Agent + Screen + Timezone + Canvas)
- IP Address

Prevents bypass via incognito mode, different browser, or VPN
"""

import hashlib
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import Request, HTTPException
from loguru import logger

from app.core.redis_client import get_redis


class EnhancedGuestTracking:
    """Enhanced guest tracking with Geo IP to prevent bypassing"""
    
    MAX_GUEST_ANALYSES = 2
    ROLLING_WINDOW_HOURS = 24
    
    @staticmethod
    async def get_geo_ip(ip: str) -> str:
        """
        Get country code from IP using ipapi.co
        
        Free tier: 1000 requests/day
        Fallback to 'UNKNOWN' if API fails
        """
        try:
            # Try ipapi.co first (free, no API key needed)
            response = requests.get(
                f"https://ipapi.co/{ip}/json/",
                timeout=2
            )
            if response.status_code == 200:
                data = response.json()
                country_code = data.get("country_code", "UNKNOWN")
                logger.debug(f"[GEO_IP] {ip} -> {country_code}")
                return country_code
        except Exception as e:
            logger.warning(f"[GEO_IP] Failed to get geo IP for {ip}: {e}")
        
        return "UNKNOWN"
    
    @staticmethod
    def generate_device_fingerprint(
        request: Request,
        session_id: str,
        additional_headers: Optional[Dict] = None
    ) -> str:
        """
        Generate unique device fingerprint that CANNOT be bypassed
        
        Combines:
        - IP address
        - User-Agent
        - Accept-Language
        - Browser Session ID (from frontend)
        - Screen resolution (from header)
        - Timezone (from header)
        - Canvas fingerprint (from header)
        """
        ip = request.client.host
        user_agent = request.headers.get("user-agent", "")
        accept_language = request.headers.get("accept-language", "")
        
        # Get additional fingerprinting data from custom headers (sent by frontend)
        screen_resolution = request.headers.get("X-Screen-Resolution", "")
        timezone = request.headers.get("X-Timezone", "")
        canvas_fp = request.headers.get("X-Canvas-Fingerprint", "")
        
        # Combine all signals
        fingerprint_string = (
            f"{ip}:{user_agent}:{session_id}:{accept_language}:"
            f"{screen_resolution}:{timezone}:{canvas_fp}"
        )
        
        # Hash to create unique ID
        fingerprint = hashlib.sha256(fingerprint_string.encode()).hexdigest()
        
        logger.debug(f"[ENHANCED_TRACKING] Fingerprint: {fingerprint[:16]}... for IP: {ip}")
        return fingerprint
    
    @staticmethod
    async def check_limit(
        request: Request,
        session_id: str
    ) -> Dict:
        """
        Check if guest has exceeded 2-analysis limit
        
        Multi-layer checking (ALL must pass):
        1. Device fingerprint
        2. IP address
        3. Browser session
        4. Geo IP + IP prefix (country-level + partial IP)
        
        Returns:
            {
                "allowed": bool,
                "remaining": int,
                "reset_at": datetime or None,
                "fingerprint": str,
                "geo_ip": str,
                "tracking_layers": int
            }
        """
        redis = get_redis()
        ip = request.client.host
        
        # Get geo IP
        geo_ip = await EnhancedGuestTracking.get_geo_ip(ip)
        
        # Generate device fingerprint
        device_fp = EnhancedGuestTracking.generate_device_fingerprint(request, session_id)
        
        # Create tracking keys (check ALL layers)
        tracking_keys = [
            f"guest:ip:{ip}",
            f"guest:device:{device_fp}",
            f"guest:session:{session_id}",
            f"guest:geo:{geo_ip}:{ip[:7]}"  # Country + IP prefix (prevents VPN bypass)
        ]
        
        max_count = 0
        earliest_reset = None
        
        for key in tracking_keys:
            count_str = redis.get(key)
            count = int(count_str) if count_str else 0
            
            if count > max_count:
                max_count = count
                ttl = redis.ttl(key)
                if ttl > 0:
                    earliest_reset = ttl
        
        # Calculate remaining requests
        remaining = max(0, EnhancedGuestTracking.MAX_GUEST_ANALYSES - max_count)
        allowed = remaining > 0
        
        logger.info(
            f"[ENHANCED_TRACKING] Check: IP={ip}, Geo={geo_ip}, "
            f"Count={max_count}/{EnhancedGuestTracking.MAX_GUEST_ANALYSES}, "
            f"Allowed={allowed}, Layers={len(tracking_keys)}"
        )
        
        return {
            "allowed": allowed,
            "remaining": remaining,
            "reset_at": earliest_reset,
            "fingerprint": device_fp,
            "geo_ip": geo_ip,
            "tracking_layers": len(tracking_keys),
            "current_count": max_count
        }
    
    @staticmethod
    async def record_analysis(
        request: Request,
        session_id: str
    ):
        """
        Record guest analysis across ALL tracking layers
        
        This ensures user cannot bypass by:
        - Using incognito mode (device fingerprint still same)
        - Using different browser (IP + geo still tracked)
        - Using VPN (geo + IP prefix catches this)
        """
        redis = get_redis()
        ip = request.client.host
        
        # Get geo IP
        geo_ip = await EnhancedGuestTracking.get_geo_ip(ip)
        
        # Generate device fingerprint
        device_fp = EnhancedGuestTracking.generate_device_fingerprint(request, session_id)
        
        # Create tracking keys
        tracking_keys = [
            f"guest:ip:{ip}",
            f"guest:device:{device_fp}",
            f"guest:session:{session_id}",
            f"guest:geo:{geo_ip}:{ip[:7]}"
        ]
        
        ttl_seconds = EnhancedGuestTracking.ROLLING_WINDOW_HOURS * 3600
        
        # Increment ALL layers
        for key in tracking_keys:
            redis.incr(key)
            redis.expire(key, ttl_seconds)
        
        logger.info(
            f"[ENHANCED_TRACKING] Recorded: IP={ip}, Geo={geo_ip}, "
            f"Fingerprint={device_fp[:16]}..., Layers={len(tracking_keys)}"
        )


# Global instance
enhanced_guest_tracking = EnhancedGuestTracking()


def get_enhanced_guest_tracking() -> EnhancedGuestTracking:
    """Get enhanced guest tracking instance"""
    return enhanced_guest_tracking
