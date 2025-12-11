"""
Base rate limiter with common functionality.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple
from fastapi import Request
from loguru import logger
import hashlib

from app.core.redis_client import get_redis


class BaseRateLimiter(ABC):
    """Abstract base class for rate limiters"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client if redis_client else get_redis()
        self.prefix = "rate_limit"
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _get_session_id(self, request: Request) -> Optional[str]:
        """Extract session ID from request headers"""
        return request.headers.get("X-Session-ID")
    
    def _build_redis_key(self, identifier: str, limit_type: str) -> str:
        """Build Redis key for rate limiting"""
        return f"{self.prefix}:{self.role}:{identifier}:{limit_type}"
    
    def _get_current_count(self, key: str) -> int:
        """Get current count from Redis"""
        current = self.redis.get(key)
        return int(current) if current else 0
    
    def _increment_count(self, key: str, window_seconds: int) -> int:
        """
        Increment count and ALWAYS set TTL.
        
        PROPER FIX: Set TTL on EVERY increment,not just first one.
        This ensures:
        1. Old keys from testing get TTL
        2. TTL is refreshed on each request (sliding window)
        3. Keys definitely expire after window_seconds
        """
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds)  # ALWAYS set TTL
        
        result = pipe.execute()
        new_count = result[0] if result else 1
        
        logger.debug(f"[RATE_LIMIT] Incremented {key}: count={new_count}, ttl_set={window_seconds}s")
        
        return new_count
    
    @property
    @abstractmethod
    def role(self) -> str:
        """Role name (guest, user, admin)"""
        pass
    
    @abstractmethod
    async def check_limit(
        self,
        request: Request,
        identifier: any,
        limit_type: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int]:
        """
        Check if request is within limit.
        
        Returns:
            Tuple[bool, int]: (allowed, remaining)
        """
        pass
    
    @abstractmethod
    async def increment(
        self,
        request: Request,
        identifier: any,
        limit_type: str,
        window_seconds: int
    ) -> int:
        """
        Increment counter after successful operation.
        
        Returns:
            int: New count
        """
        pass
    
    async def get_remaining(
        self,
        request: Request,
        identifier: any,
        limit_type: str,
        max_requests: int
    ) -> int:
        """Get remaining requests without incrementing"""
        key = self._build_redis_key(str(identifier), limit_type)
        current = self._get_current_count(key)
        remaining = max(0, max_requests - current)
        return remaining
