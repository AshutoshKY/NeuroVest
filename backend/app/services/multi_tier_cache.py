"""
Multi-Tier Cache Service
=========================

Implements 3-tier caching for stock data:
- Tier 1: Memory cache (60s TTL, instant access)
- Tier 2: Redis cache (5min TTL, fast access)
- Tier 3: Stale cache (1hour TTL, emergency fallback)

Author: NeuroVest
Date: 2025-12-13
"""

import json
import time
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MultiTierCache:
    """
    Multi-tier caching system for stock data.
    
    Tier 1: Memory (Python dict) - 60s TTL, <5ms access
    Tier 2: Redis - 300s TTL, ~20ms access
    Tier 3: Stale Redis - 3600s TTL, fallback only
    
    Usage:
        cache = MultiTierCache(redis_client)
        
        # Get from cache
        result = await cache.get("RELIANCE")
        if result and result['fresh']:
            return result['data']
        
        # Set in cache
        await cache.set("RELIANCE", stock_data)
    """
    
    # TTL configurations (seconds)
    MEMORY_TTL = 60        # 1 minute - instant but limited scope
    REDIS_FRESH_TTL = 300  # 5 minutes - fresh data
    REDIS_STALE_TTL = 3600 # 1 hour - emergency fallback
    
    def __init__(self, redis_client=None):
        """
        Initialize multi-tier cache.
        
        Args:
            redis_client: Redis client instance (optional)
        """
        self.redis = redis_client
        self.memory_cache: Dict[str, Tuple[Dict, float]] = {}  # {key: (data, timestamp)}
        
        # Statistics
        self.stats = {
            "memory_hits": 0,
            "redis_hits": 0,
            "stale_hits": 0,
            "misses": 0,
            "sets": 0
        }
        
        logger.info(f"MultiTierCache initialized (Redis: {'✅' if redis_client else '❌'})")
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get data from cache tiers.
        
        Args:
            key: Cache key (e.g., ticker symbol)
            
        Returns:
            Dict with {data: {...}, source: str, fresh: bool, age_seconds: float}
            or None if not found
        """
        current_time = time.time()
        
        # TIER 1: Memory Cache
        if key in self.memory_cache:
            data, cached_at = self.memory_cache[key]
            age = current_time - cached_at
            
            if age < self.MEMORY_TTL:
                self.stats["memory_hits"] += 1
                logger.debug(f"[CACHE] Memory HIT: {key} (age: {age:.1f}s)")
                
                return {
                    "data": data,
                    "source": "memory",
                    "fresh": True,
                    "age_seconds": age,
                    "cached_at": datetime.fromtimestamp(cached_at).isoformat()
                }
            else:
                # Expired, remove from memory
                del self.memory_cache[key]
        
        # TIER 2 & 3: Redis Cache
        if self.redis:
            try:
                # Try fresh key first
                redis_key_fresh = f"stock:fresh:{key}"
                cached_data = self.redis.get(redis_key_fresh)
                
                if cached_data:
                    data = json.loads(cached_data)
                    cached_at = data.get('_cached_at', current_time)
                    age = current_time - cached_at
                    
                    if age < self.REDIS_FRESH_TTL:
                        # Fresh data found
                        self.stats["redis_hits"] += 1
                        logger.debug(f"[CACHE] Redis FRESH HIT: {key} (age: {age:.1f}s)")
                        
                        # Update memory cache
                        self.memory_cache[key] = (data, cached_at)
                        
                        return {
                            "data": data,
                            "source": "redis_fresh",
                            "fresh": True,
                            "age_seconds": age,
                            "cached_at": datetime.fromtimestamp(cached_at).isoformat()
                        }
                
                # Try stale key (fallback)
                redis_key_stale = f"stock:stale:{key}"
                cached_data = self.redis.get(redis_key_stale)
                
                if cached_data:
                    data = json.loads(cached_data)
                    cached_at = data.get('_cached_at', current_time)
                    age = current_time - cached_at
                    
                    self.stats["stale_hits"] += 1
                    logger.warning(f"[CACHE] Redis STALE HIT: {key} (age: {age:.1f}s)")
                    
                    return {
                        "data": data,
                        "source": "redis_stale",
                        "fresh": False,  # Mark as stale
                        "age_seconds": age,
                        "cached_at": datetime.fromtimestamp(cached_at).isoformat()
                    }
                    
            except Exception as e:
                logger.error(f"[CACHE] Redis error: {e}")
        
        # Cache miss
        self.stats["misses"] += 1
        logger.debug(f"[CACHE] MISS: {key}")
        return None
    
    async def set(self, key: str, data: Dict[str, Any], ttl_override: Optional[int] = None) -> bool:
        """
        Set data in all cache tiers.
        
        Args:
            key: Cache key
            data: Data to cache
            ttl_override: Optional TTL override (seconds)
            
        Returns:
            True if successful
        """
        current_time = time.time()
        
        # Add timestamp to data
        data_with_meta = {
            **data,
            '_cached_at': current_time,
            '_cache_key': key
        }
        
        try:
            # TIER 1: Memory Cache
            self.memory_cache[key] = (data_with_meta, current_time)
            
            # TIER 2 & 3: Redis Cache
            if self.redis:
                fresh_ttl = ttl_override or self.REDIS_FRESH_TTL
                stale_ttl = self.REDIS_STALE_TTL
                
                data_json = json.dumps(data_with_meta, default=str)
                
                # Set fresh key (5 min)
                redis_key_fresh = f"stock:fresh:{key}"
                self.redis.setex(redis_key_fresh, fresh_ttl, data_json)
                
                # Set stale key (1 hour) - for fallback
                redis_key_stale = f"stock:stale:{key}"
                self.redis.setex(redis_key_stale, stale_ttl, data_json)
                
                logger.debug(f"[CACHE] SET: {key} (fresh: {fresh_ttl}s, stale: {stale_ttl}s)")
            else:
                logger.debug(f"[CACHE] SET (memory only): {key}")
            
            self.stats["sets"] += 1
            return True
            
        except Exception as e:
            logger.error(f"[CACHE] Set error for {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete from all cache tiers.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful
        """
        try:
            # Delete from memory
            if key in self.memory_cache:
                del self.memory_cache[key]
            
            # Delete from Redis
            if self.redis:
                self.redis.delete(f"stock:fresh:{key}")
                self.redis.delete(f"stock:stale:{key}")
            
            logger.debug(f"[CACHE] DELETED: {key}")
            return True
            
        except Exception as e:
            logger.error(f"[CACHE] Delete error for {key}: {e}")
            return False
    
    async def clear_all(self) -> bool:
        """Clear all cache tiers (use with caution!)."""
        try:
            # Clear memory
            self.memory_cache.clear()
            
            # Clear Redis (pattern delete)
            if self.redis:
                # Delete all stock:* keys
                for key in self.redis.scan_iter("stock:*"):
                    self.redis.delete(key)
            
            logger.warning("[CACHE] ALL CLEARED")
            return True
            
        except Exception as e:
            logger.error(f"[CACHE] Clear all error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = (
            self.stats["memory_hits"] +
            self.stats["redis_hits"] +
            self.stats["stale_hits"] +
            self.stats["misses"]
        )
        
        hit_rate = 0.0
        if total_requests > 0:
            total_hits = (
                self.stats["memory_hits"] +
                self.stats["redis_hits"] +
                self.stats["stale_hits"]
            )
            hit_rate = (total_hits / total_requests) * 100
        
        return {
            **self.stats,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "memory_cache_size": len(self.memory_cache),
            "memory_ttl_seconds": self.MEMORY_TTL,
            "redis_fresh_ttl_seconds": self.REDIS_FRESH_TTL,
            "redis_stale_ttl_seconds": self.REDIS_STALE_TTL
        }
    
    def reset_stats(self):
        """Reset statistics counters."""
        self.stats = {
            "memory_hits": 0,
            "redis_hits": 0,
            "stale_hits": 0,
            "misses": 0,
            "sets": 0
        }
        logger.info("[CACHE] Stats reset")
    
    def __repr__(self) -> str:
        stats = self.get_stats()
        return (
            f"MultiTierCache("
            f"hits={stats['memory_hits']+stats['redis_hits']+stats['stale_hits']}, "
            f"misses={stats['misses']}, "
            f"hit_rate={stats['hit_rate_percent']:.1f}%, "
            f"memory_size={stats['memory_cache_size']})"
        )


# Helper function to create cache instance
def create_multi_tier_cache(redis_client=None) -> MultiTierCache:
    """
    Create MultiTierCache instance with Redis client.
    
    Args:
        redis_client: Redis client (will attempt to get from app if None)
        
    Returns:
        MultiTierCache instance
    """
    if redis_client is None:
        try:
            from app.core.redis_client import get_redis
            redis_client = get_redis()
        except Exception as e:
            logger.warning(f"Could not get Redis client: {e}. Using memory-only cache.")
    
    return MultiTierCache(redis_client)
