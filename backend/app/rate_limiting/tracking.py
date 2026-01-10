"""
Tracking utilities for rate limiting.
Provides device fingerprinting, geo IP, session, and JWT tracking.
"""

from typing import Optional, Dict, Set
from fastapi import Request
from loguru import logger
import hashlib


class TrackingUtils:
    """Utilities for tracking user identity across multiple dimensions"""
    
    @staticmethod
    def get_device_fingerprint(request: Request) -> Optional[str]:
        """
        Get device fingerprint from device token.
        Parses X-Device-Token header (JSON) and extracts device_fp field.
        """
        import json
        
        token_str = request.headers.get("X-Device-Token")
        logger.debug(f"[TRACKING] X-Device-Token header: {token_str[:50] if token_str else 'MISSING'}...")
        
        if token_str:
            try:
                device_token = json.loads(token_str)
                device_fp = device_token.get("device_fp")
                if device_fp:
                    logger.info(f"[TRACKING] ✅ Device fingerprint: {device_fp[:16]}...")
                    return device_fp
                else:
                    logger.warning("[TRACKING] ⚠️ Device token missing 'device_fp' field")
            except (json.JSONDecodeError, AttributeError) as e:
                logger.warning(f"[TRACKING] ⚠️ Failed to parse device token: {e}")
        else:
            logger.debug("[TRACKING] ⚠️ No X-Device-Token header present")
        
        return None
    
    @staticmethod
    def get_device_token(request: Request) -> Optional[Dict]:
        """
        Get full device token from header for validation.
        Returns the parsed device token dict.
        """
        import json
        
        token_str = request.headers.get("X-Device-Token")
        if token_str:
            try:
                device_token = json.loads(token_str)
                return device_token
            except json.JSONDecodeError as e:
                logger.warning(f"[TRACKING] Failed to parse device token: {e}")
        return None
    
    @staticmethod
    def get_session_id(request: Request) -> Optional[str]:
        """
        Get session ID from X-Session-ID header.
        """
        session_id = request.headers.get("X-Session-ID")
        if session_id:
            logger.info(f"[TRACKING] ✅ Session ID: {session_id[:16]}...")
        else:
            logger.debug("[TRACKING] ⚠️ No X-Session-ID header present")
        return session_id
    
    @staticmethod
    def get_client_ip(request: Request) -> str:
        """
        Get client IP from request, checking forwarded headers first.
        """
        # Check for forwarded IP (from proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # First IP in the list is the original client
            client_ip = forwarded_for.split(",")[0].strip()
            logger.debug(f"[TRACKING] Client IP (X-Forwarded-For): {client_ip}")
            return client_ip
        
        # Fallback to direct connection IP
        try:
            if request.client:
                client_ip = request.client.host
            else:
                client_ip = "unknown"
        except Exception as e:
            print(f"DEBUG: request.client error: {e}, type: {type(getattr(request, 'client', 'MISSING'))}")
            client_ip = "unknown"
            
        logger.info(f"[TRACKING] ✅ Client IP (direct): {client_ip}")
        return client_ip
    
    @staticmethod
    def get_geo_location(request: Request) -> Optional[str]:
        """
        Get geo location from IP.
        Can use headers from reverse proxy (Cloudflare, etc.)
        or implement IP geolocation lookup.
        """
        # Try to get from Cloudflare headers
        country = request.headers.get("CF-IPCountry")
        if country:
            logger.debug(f"[TRACKING] Geo location: {country}")
            return country
        
        # TODO: Implement IP geolocation lookup if needed
        # For now, derive from IP
        client_ip = TrackingUtils.get_client_ip(request)
        # Placeholder: would use MaxMind GeoIP or similar
        return None
    
    @staticmethod
    def get_ip_hash(request: Request) -> str:
        """Get hashed IP for privacy"""
        ip = TrackingUtils.get_client_ip(request)
        ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16]
        return ip_hash
    
    @staticmethod
    def build_tracking_keys(
        request: Request,
        user_id: Optional[int] = None,
        role: str = "guest",
        limit_type: str = "analysis"
    ) -> Set[str]:
        """
        Build all tracking keys for a request.
        
        **STRICT MODE**: All tracking dimensions REQUIRED (no fallbacks).
        - Guests: device_fp + session_id + IP
        - Users/Admins: user_id + device_fp + session_id + IP
        
        Raises ValueError if required headers missing.
        
        Returns set of Redis keys to check/increment.
        
        Tracking dimensions:
        - Device fingerprint (prevents browser switching)
        - Session ID (prevents incognito mode)
        - IP address (prevents device switching)
        - User ID (for authenticated users)
        
        Args:
            request: FastAPI request
            user_id: User ID if authenticated
            role: 'guest', 'user', or 'admin'
            limit_type: Type of limit (analysis, api_minute, etc.)
        
        Returns:
            Set of Redis keys
            
        Raises:
            ValueError: If required tracking headers are missing
        """
        keys = set()
        prefix = f"rate_limit:{role}"
        
        # Extract all tracking data
        fingerprint = TrackingUtils.get_device_fingerprint(request)
        session_id = TrackingUtils.get_session_id(request)
        ip_hash = TrackingUtils.get_ip_hash(request)
        
        # STRICT VALIDATION: Check required headers
        missing_headers = []
        
        if not fingerprint:
            missing_headers.append("X-Device-Token")
        if not session_id:
            missing_headers.append("X-Session-ID")
        
        # For authenticated users, user_id is also required
        if role in ["user", "admin"] and not user_id:
            missing_headers.append("user_id (JWT)")
        
        # If any required headers missing, raise error
        if missing_headers:
            error_msg = f"Missing required tracking headers: {', '.join(missing_headers)}"
            logger.warning(
                f"[TRACKING] ⚠️ STRICT VALIDATION FAILED: {error_msg} "
                f"(role={role}, endpoint={request.url.path})"
            )
            raise ValueError(error_msg)
        
        # Build tracking keys for all dimensions
        
        # 1. Device fingerprint tracking (all users)
        keys.add(f"{prefix}:device:{fingerprint}:{limit_type}")
        
        # 2. Session tracking (all users)
        keys.add(f"{prefix}:session:{session_id}:{limit_type}")
        
        # 3. IP-based tracking (all users)
        keys.add(f"{prefix}:ip:{ip_hash}:{limit_type}")
        
        # 4. Geo location tracking (optional, for analytics)
        # Removed as per strict mode, no fallbacks
        # geo = TrackingUtils.get_geo_location(request)
        # if geo:
        #     keys.add(f"{prefix}:geo:{geo}:{limit_type}")
        
        # 5. User ID tracking (authenticated users only)
        if user_id:
            keys.add(f"{prefix}:user:{user_id}:{limit_type}")
        
        logger.debug(
            f"[TRACKING] Built {len(keys)} tracking keys for {role} "
            f"(user_id={user_id}, limit_type={limit_type})"
        )
        
        return keys
    
    @staticmethod
    def get_request_context(request: Request, user_id: Optional[int] = None) -> Dict:
        """
        Get full context of a request for logging/debugging.
        
        Returns dict with all tracking dimensions.
        """
        return {
            "user_id": user_id,
            "device_fingerprint": TrackingUtils.get_device_fingerprint(request),
            "session_id": TrackingUtils.get_session_id(request),
            "client_ip": TrackingUtils.get_client_ip(request),
            "geo_location": TrackingUtils.get_geo_location(request),
        }
