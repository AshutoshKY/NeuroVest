"""
Device Token Service
Handles device registration, token signing, validation, and suspicious activity detection.
"""

import hmac
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from fastapi import Request
from loguru import logger

from app.core.redis_client import get_redis
from .device_token_config import device_token_config


class DeviceTokenService:
    """Service for device token management with server-side validation"""
    
    def __init__(self):
        self.redis = get_redis()
        # Get or generate secret key on init
        self.secret_key = device_token_config.get_or_generate_secret(self.redis)
        logger.info(f"[DEVICE_TOKEN] Initialized with secret (first 8 chars): {self.secret_key[:8]}...")
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _generate_signature(
        self,
        device_fp: str,
        ip_address: str,
        timestamp: str
    ) -> str:
        """
        Generate HMAC-SHA256 signature for device token.
        
        Signature = HMAC-SHA256(secret, device_fp + ip + timestamp)
        """
        message = f"{device_fp}:{ip_address}:{timestamp}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def register_device(
        self,
        request: Request,
        device_fingerprint: str
    ) -> Dict:
        """
        Register a device and issue signed token.
        
        Returns:
            {
                "device_token": {...},  # Signed token to store
                "requires_captcha": bool
            }
        """
        ip_address = self._get_client_ip(request)
        timestamp = datetime.utcnow().isoformat()
        
        # Generate signature
        signature = self._generate_signature(device_fingerprint, ip_address, timestamp)
        
        # Create token
        device_token = {
            "device_fp": device_fingerprint,
            "signature": signature,
            "issued_at": timestamp,
            "issued_ip": ip_address,
            "version": "1.0"
        }
        
        # Track device registration for suspicious activity detection
        if device_token_config.TRACK_DEVICE_ACTIVITY:
            self._track_device_activity(device_fingerprint, "registration", ip_address)
        
        # Check if suspicious activity
        requires_captcha = self._is_suspicious_activity(device_fingerprint)
        
        logger.info(
            f"[DEVICE_TOKEN] Registered device {device_fingerprint[:16]}... "
            f"from IP {ip_address}, suspicious={requires_captcha}"
        )
        
        return {
            "device_token": device_token,
            "requires_captcha": requires_captcha
        }
    
    def validate_token(
        self,
        request: Request,
        device_token: Dict
    ) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Validate device token.
        
        Returns:
            (is_valid, error_message, new_token_if_needed)
            
        Validation checks:
        1. Signature valid (not tampered)
        2. Not expired (< 90 days)
        3. IP matches or handled appropriately
        """
        try:
            device_fp = device_token.get("device_fp")
            signature = device_token.get("signature")
            issued_at = device_token.get("issued_at")
            issued_ip = device_token.get("issued_ip")
            
            if not all([device_fp, signature, issued_at, issued_ip]):
                return False, "Invalid token format", None
            
            # Check expiry
            issued_time = datetime.fromisoformat(issued_at)
            age = datetime.utcnow() - issued_time
            if age.total_seconds() > device_token_config.DEVICE_TOKEN_TTL_SECONDS:
                return False, "Token expired", None
            
            # Validate signature
            expected_signature = self._generate_signature(device_fp, issued_ip, issued_at)
            if not hmac.compare_digest(signature, expected_signature):
                logger.warning(f"[DEVICE_TOKEN] Invalid signature for {device_fp[:16]}...")
                return False, "Invalid signature (tampered token)", None
            
            # Check IP match
            current_ip = self._get_client_ip(request)
            if current_ip != issued_ip:
                # IP changed - requires re-registration with CAPTCHA
                logger.info(
                    f"[DEVICE_TOKEN] IP changed for {device_fp[:16]}... "
                    f"({issued_ip} → {current_ip})"
                )
                
                # Track IP change
                self._track_device_activity(device_fp, "ip_change", current_ip)
                
                # Check if this is suspicious (too many IP changes)
                ip_changes = self._count_device_activity(device_fp, "ip_change")
                if ip_changes > device_token_config.DEVICE_IP_CHANGE_LIMIT:
                    return False, "Too many IP changes - CAPTCHA required", None
                
                return False, "IP changed - re-registration required", None
            
            # Token valid
            return True, None, None
            
        except Exception as e:
            logger.error(f"[DEVICE_TOKEN] Validation error: {e}")
            return False, f"Validation error: {str(e)}", None
    
    def _track_device_activity(
        self,
        device_fp: str,
        activity_type: str,
        metadata: str
    ):
        """Track device activity for suspicious pattern detection"""
        key = f"device_activity:{device_fp}:{activity_type}"
        
        # Store as sorted set with timestamp as score
        timestamp = datetime.utcnow().timestamp()
        member = f"{timestamp}:{metadata}"
        
        self.redis.zadd(key, {member: timestamp})
        
        # Remove old entries (older than 24h)
        cutoff = timestamp - device_token_config.SUSPICIOUS_ACTIVITY_WINDOW
        self.redis.zremrangebyscore(key, 0, cutoff)
        
        # Set expiry on key
        self.redis.expire(key, device_token_config.SUSPICIOUS_ACTIVITY_WINDOW + 3600)
    
    def _count_device_activity(
        self,
        device_fp: str,
        activity_type: str
    ) -> int:
        """Count recent device activity"""
        key = f"device_activity:{device_fp}:{activity_type}"
        
        # Count entries in last 24h
        timestamp = datetime.utcnow().timestamp()
        cutoff = timestamp - device_token_config.SUSPICIOUS_ACTIVITY_WINDOW
        
        count = self.redis.zcount(key, cutoff, timestamp)
        return count
    
    def _is_suspicious_activity(self, device_fp: str) -> bool:
        """
        Detect suspicious patterns.
        
        Suspicious if:
        - >10 registrations in 24h
        - >5 IP changes in 24h
        """
        if not device_token_config.TRACK_DEVICE_ACTIVITY:
            return False
        
        registrations = self._count_device_activity(device_fp, "registration")
        ip_changes = self._count_device_activity(device_fp, "ip_change")
        
        suspicious = (
            registrations > device_token_config.DEVICE_REREGISTRATION_LIMIT or
            ip_changes > device_token_config.DEVICE_IP_CHANGE_LIMIT
        )
        
        if suspicious:
            logger.warning(
                f"[DEVICE_TOKEN] Suspicious activity detected: {device_fp[:16]}... "
                f"(registrations={registrations}, ip_changes={ip_changes})"
            )
        
        return suspicious


# Singleton instance
_device_token_service = None


def get_device_token_service() -> DeviceTokenService:
    """Get device token service instance"""
    global _device_token_service
    if _device_token_service is None:
        _device_token_service = DeviceTokenService()
    return _device_token_service
