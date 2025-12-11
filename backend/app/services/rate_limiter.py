"""
Rate limiting service using Redis
Implements IP-based, user-based, and device fingerprint-based rate limiting
"""
import redis
import hashlib
from typing import Optional, Tuple
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from loguru import logger

from app.core.redis_client import get_redis


class RateLimiter:
    """Rate limiting service"""
    
    def __init__(self, redis_client=None):
        """Initialize RateLimiter with Redis client."""
        self.redis = redis_client if redis_client else get_redis()
        logger.info("[RATE_LIMITER] Initialized")
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check X-Forwarded-For header first (for proxies)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"
    
    def _get_client_identifier(self, request: Request) -> str:
        """
        Generate unique client identifier from IP + User Agent + device fingerprint
        This prevents bypassing limits by changing browser
        """
        # Get IP (handle forwarded headers)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        # Get user agent
        user_agent = request.headers.get("User-Agent", "unknown")
        
        # Get device fingerprint from headers (sent by frontend)
        device_id = request.headers.get("X-Device-ID", "")
        
        # Create composite identifier
        # This ensures changing browser doesn't reset count
        composite = f"{client_ip}:{user_agent}:{device_id}"
        identifier_hash = hashlib.sha256(composite.encode()).hexdigest()[:16]
        
        return identifier_hash
    
    def _get_limit_key(
        self,
        limit_type: str,
        window_seconds: int,
        request: Request,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> str:
        """Build consistent cache key for rate limiting."""
        if user_id:
            return f"ratelimit:user:{user_id}:{limit_type}_{window_seconds}s"
        elif session_id:
            return f"ratelimit:session:{session_id}:{limit_type}_{window_seconds}s"
        else:
            client_ip = self._get_client_ip(request)
            ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:16]
            return f"ratelimit:ip:{ip_hash}:{limit_type}_{window_seconds}s"
    
    async def check_rate_limit(
        self,
        request: Request,
        limit_type: str,
        max_requests: int,
        window_seconds: int,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> Tuple[bool, int, int]:
        """
        Check if request is within rate limit using sliding window.
        Supports IP, user, and session-based tracking.
        
        Args:
            request: FastAPI request object
            limit_type: Type of limit (analysis, api_minute, api_hour, etc.)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            user_id: Optional user ID for user-based limits
            session_id: Optional session ID for session-based limits (prevents incognito bypass)
            
        Returns:
        LEGACY: Check AND INCREMENT rate limit (kept for backward compatibility).
        For new code, use check_limit_only() + increment_limit() pattern.
        
        Returns:
            Tuple[bool, int, int]: (allowed, new_count, retry_after_seconds)
        """
        key = self._get_limit_key(limit_type, window_seconds, request, user_id, session_id)
        
        try:
            current = self.redis.get(key)
            current_count = int(current) if current else 0
            
            # Check if limit exceeded
            if current_count >= max_requests:
                # Get TTL for retry-after header
                ttl = self.redis.ttl(key)
                retry_after = ttl if ttl > 0 else window_seconds
                
                logger.warning(
                    f"[RATE_LIMIT] Limit exceeded: {limit_type}, "
                    f"user_id={user_id}, count={current_count}/{max_requests}, "
                    f"retry_after={retry_after}s"
                )
                
                return False, current_count, retry_after
            
            # Increment counter
            pipe = self.redis.pipeline()
            pipe.incr(key)
            
            # Set expiry only if this is the first request
            if current_count == 0:
                pipe.expire(key, window_seconds)
            
            pipe.execute()
            
            new_count = current_count + 1
            
            logger.debug(
                f"[RATE_LIMIT] Request allowed: {limit_type}, "
                f"count={new_count}/{max_requests}"
            )
            
            return True, new_count, 0
            
        except Exception as e:
            logger.error(f"[RATE_LIMIT] Redis error: {e}")
            # On Redis failure, allow request (fail open)
            return True, 0, 0
    
    async def check_analysis_limit(
        self,
        request: Request,
        user_id: Optional[int] = None
    ) -> None:
        """
        Check analysis rate limit with MULTI-LAYER enforcement.
        
        ALL users are subject to:
        - IP-based limit (5/day per IP)
        - Session-based limit (5/day per device/browser)
        - User-based limit (5/day per account, if authenticated)
        
        This prevents bypass by:
        - Creating multiple accounts from same IP
        - Using incognito/clearing cookies (session tracking)
        - VPN switching (device fingerprinting)
        
        Raises HTTPException if ANY limit is exceeded.
        """
        session_id = request.headers.get("X-Session-ID")
        
        # AUTHENTICATED USERS: Only check user-based limit (5/day per account)
        if user_id:
            logger.info(f"[RATE_LIMIT] Authenticated user {user_id} - checking user limit only")
            allowed_user, count_user, retry_user = await self.check_rate_limit(
                request,
                limit_type="analysis",
                max_requests=5,
                window_seconds=86400,
                user_id=user_id,
                session_id=None
            )
            
            if not allowed_user:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"User analysis limit exceeded (5 per day). Try again in {retry_user // 3600} hours.",
                    headers={"Retry-After": str(retry_user)}
                )
            return  # Skip IP and session checks for authenticated users
        
        # UNAUTHENTICATED USERS: Check IP-based limit (5/day per IP)
        logger.info(f"[RATE_LIMIT] Guest user - checking IP and session limits")
        allowed_ip, count_ip, retry_ip = await self.check_rate_limit(
            request,
            limit_type="analysis",
            max_requests=5,
            window_seconds=86400,
            user_id=None,
            session_id=None  # IP only
        )
        
        if not allowed_ip:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"IP analysis limit exceeded (5 per day). Try again in {retry_ip // 3600} hours.",
                headers={"Retry-After": str(retry_ip)}
            )
        
        # Check Session-based limit (applies to everyone)
        if session_id:
            allowed_session, count_session, retry_session = await self.check_rate_limit(
                request,
                limit_type="analysis",
                max_requests=5,
                window_seconds=86400,
                user_id=None,
                session_id=session_id
            )
            
            if not allowed_session:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Device analysis limit exceeded (5 per day). Try again in {retry_session // 3600} hours.",
                    headers={"Retry-After": str(retry_session)}
                )
        
        # Check User-based limit (only for authenticated users)
        if user_id:
            allowed_user, count_user, retry_user = await self.check_rate_limit(
                request,
                limit_type="analysis",
                max_requests=5,
                window_seconds=86400,
                user_id=user_id,
                session_id=None  # User only
            )
            
            if not allowed_user:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"User analysis limit exceeded (5 per day). Try again in {retry_user // 3600} hours.",
                    headers={"Retry-After": str(retry_user)}
                )
    
    async def get_remaining_analyses(
        self,
        request: Request,
        user_id: Optional[int] = None
    ) -> Tuple[int, Optional[int]]:
        """
        Get remaining analysis count without incrementing counter.
        Returns (remaining analyses, reset_at_timestamp).
        Checks BOTH session and user keys to handle authentication mid-session.
        reset_at is Unix timestamp when the limit will reset (first_use + 24hrs).
        """
        max_requests = 5
        window_seconds = 86400  # 24 hours
        
        try:
            counts = []
            details = {}
            reset_at = None
            
            # Check user-based count if authenticated
            if user_id:
                user_key = f"ratelimit:user:{user_id}:analysis_{window_seconds}s"
                user_current = self.redis.get(user_key)
                user_count = int(user_current) if user_current else 0
                counts.append(user_count)
                details['user'] = user_count
                logger.debug(f"[RATE_LIMIT] User {user_id} count: {user_count}")
                
                # Get TTL to calculate reset_at
                if user_count > 0:
                    ttl = self.redis.ttl(user_key)
                    if ttl > 0:
                        reset_at = int(datetime.now().timestamp()) + ttl
            
            # Always check session-based count (handles case where analysis was done before login)
            session_id = request.headers.get("X-Session-ID")
            if session_id and not reset_at:  # Only check if we don't have reset_at from user
                session_key = f"ratelimit:session:{session_id}:analysis_{window_seconds}s"
                session_current = self.redis.get(session_key)
                session_count = int(session_current) if session_current else 0
                counts.append(session_count)
                details['session'] = session_count
                logger.debug(f"[RATE_LIMIT] Session {session_id[:8]}... count: {session_count}")
                
                # Get TTL to calculate reset_at
                if session_count > 0:
                    ttl = self.redis.ttl(session_key)
                    if ttl > 0:
                        reset_at = int(datetime.now().timestamp()) + ttl
            
            # If no counts found, check IP-based
            if not counts:
                client_ip = self._get_client_ip(request)
                ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:16]
                ip_key = f"ratelimit:ip:{ip_hash}:analysis_{window_seconds}s"
                ip_current = self.redis.get(ip_key)
                ip_count = int(ip_current) if ip_current else 0
                counts.append(ip_count)
                details['ip'] = ip_count
                
                # Get TTL to calculate reset_at
                if ip_count > 0:
                    ttl = self.redis.ttl(ip_key)
                    if ttl > 0:
                        reset_at = int(datetime.now().timestamp()) + ttl
            
            # Return remaining based on MAXIMUM usage across all keys
            # (prevents bypass by switching between session/user)
            max_count = max(counts) if counts else 0
            remaining = max(0, max_requests - max_count)
            
            logger.info(f"[RATE_LIMIT] Remaining analyses: {remaining}, counts: {details}, reset_at: {reset_at}")
            return remaining, reset_at
            
        except Exception as e:
            logger.error(f"[RATE_LIMIT] Error getting remaining count: {e}")
            return max_requests, None  # Return full limit on error
    
    async def check_api_limit(
        self,
        request: Request,
        user_id: Optional[int] = None
    ) -> None:
        """
        Check general API rate limits with DUAL limits:
        - 60 requests per minute
        - 200 requests per hour
        Both limits must be satisfied.
        """
        # Check per-minute limit (100/min)
        allowed_min, count_min, retry_min = await self.check_rate_limit(
            request,
            limit_type="api_minute",
            max_requests=100,
            window_seconds=60,  # 1 minute
            user_id=None
        )
        
        if not allowed_min:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"API rate limit exceeded (60 requests/minute). Try again in {retry_min} seconds.",
                headers={"Retry-After": str(retry_min)}
            )
        
        # Check per-hour limit (1000/hour)
        allowed_hour, count_hour, retry_hour = await self.check_rate_limit(
            request,
            limit_type="api_hour",
            max_requests=1000,
            window_seconds=3600,  # 1 hour
            user_id=None
        )
        
        if not allowed_hour:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"API rate limit exceeded (200 requests/hour). Try again in {retry_hour // 60} minutes.",
                headers={"Retry-After": str(retry_hour)}
            )
    
    async def check_health_limit(
        self,
        request: Request
    ) -> None:
        """
        Check health endpoint rate limits (higher limits):
        - 60 requests per minute
        - 500 requests per hour
        """
        # Per-minute limit (60/min)
        allowed_min, count_min, retry_min = await self.check_rate_limit(
            request,
            limit_type="health_minute",
            max_requests=60,
            window_seconds=60,
            user_id=None
        )
        
        if not allowed_min:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Health check rate limit exceeded (60/min). Try again in {retry_min} seconds.",
                headers={"Retry-After": str(retry_min)}
            )
        
        # Per-hour limit (500/hour)
        allowed_hour, count_hour, retry_hour = await self.check_rate_limit(
            request,
            limit_type="health_hour",
            max_requests=500,
            window_seconds=3600,
            user_id=None
        )
        
        if not allowed_hour:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Health check rate limit exceeded (500/hour). Try again in {retry_hour // 60} minutes.",
                headers={"Retry-After": str(retry_hour)}
            )


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        redis_client = get_redis()
        _rate_limiter = RateLimiter(redis_client)
    return _rate_limiter
