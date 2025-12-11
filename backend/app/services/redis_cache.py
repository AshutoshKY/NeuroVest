"""
Redis Cache Service
Provides fast, temporary caching for stock analysis with 1-hour TTL.
"""
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


# Toggle for testing: Set to False to disable Redis temporarily
REDIS_ENABLED = True

class RedisCache:
    """Redis-based caching service for stock analysis."""
    
    def __init__(self, host: str = "redis", port: int = 6379, db: int = 0):
        """Initialize Redis connection."""
        if not REDIS_ENABLED:
            self.client = None
            logger.info("⚠️ Redis disabled for testing")
            return

        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            self.client.ping()
            logger.info(f"✅ Connected to Redis at {host}:{port}")
        except RedisError as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.client = None
    
    def get_analysis(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get cached analysis for a stock.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Cached analysis dict or None if not found/expired
        """
        if not self.client:
            return None
        
        try:
            key = f"stock:analysis:{ticker.upper()}"
            
            logger.debug("🔎 Checking Redis cache", extra={
                "operation": "redis_get",
                "ticker": ticker,
                "key": key,
                "source": "Redis"
            })
            
            data = self.client.get(key)
            
            if data:
                cached_data = json.loads(data)
                ttl = self.client.ttl(key)
                
                logger.info("✅ Redis Cache HIT", extra={
                    "operation": "redis_get",
                    "ticker": ticker,
                    "source": "Redis",
                    "ttl_remaining": f"{ttl}s" if ttl > 0 else "unknown",
                    "cached_at": cached_data.get("cached_at", "unknown"),
                    "status": "cache_hit"
                })
                return cached_data
            else:
                logger.info("❌ Redis Cache MISS", extra={
                    "operation": "redis_get",
                    "ticker": ticker,
                    "source": "Redis",
                    "status": "cache_miss"
                })
                return None
                
        except Exception as e:
            logger.error(f"Error getting cached analysis for {ticker}: {e}")
            return None
    
    def set_analysis(
        self, 
        ticker: str, 
        analysis_data: Dict[str, Any],
        ttl_seconds: int = 3600  # 1 hour default
    ) -> bool:
        """
        Cache analysis for a stock with TTL.
        
        Args:
            ticker: Stock ticker symbol
            analysis_data: Complete analysis data to cache
            ttl_seconds: Time to live in seconds (default 3600 = 1 hour)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            key = f"stock:analysis:{ticker.upper()}"
            
            logger.debug("💾 Storing in Redis cache", extra={
                "operation": "redis_set",
                "ticker": ticker,
                "ttl_seconds": ttl_seconds,
                "source": "Redis"
            })
            
            # Add metadata
            cache_data = {
                **analysis_data,
                "cached_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(seconds=ttl_seconds)).isoformat()
            }
            
            # Store with TTL
            self.client.setex(
                key,
                ttl_seconds,
                json.dumps(cache_data, default=str)
            )
            
            logger.info("✅ Stored analysis in Redis", extra={
                "operation": "redis_set",
                "ticker": ticker,
                "source": "Redis",
                "ttl_seconds": ttl_seconds,
                "expires_at": (datetime.now() + timedelta(seconds=ttl_seconds)).isoformat(),
                "has_technical": "technical_analysis" in analysis_data,
                "has_historical": "thinking_steps" in analysis_data,
                "status": "success"
            })
            
            # Track trending
            self.track_trending(ticker)
            
            return True
            
        except Exception as e:
            logger.error(f"Error caching analysis for {ticker}: {e}")
            return False
    
    def delete_analysis(self, ticker: str) -> bool:
        """Delete cached analysis for a stock."""
        if not self.client:
            return False
        
        try:
            key = f"stock:analysis:{ticker.upper()}"
            self.client.delete(key)
            logger.info(f"🗑️  Deleted cache for {ticker}")
            return True
        except Exception as e:
            logger.error(f"Error deleting cache for {ticker}: {e}")
            return False
    
    def check_rate_limit(self, ticker: str, max_requests: int = 10) -> bool:
        """
        Check if ticker has exceeded rate limit.
        
        Args:
            ticker: Stock ticker
            max_requests: Maximum requests per hour
            
        Returns:
            True if within limit, False if exceeded
        """
        if not self.client:
            return True  # Allow if Redis unavailable
        
        try:
            hour_key = datetime.now().strftime("%Y%m%d%H")
            key = f"ratelimit:{ticker.upper()}:{hour_key}"
            
            current = self.client.incr(key)
            
            if current == 1:
                # First request this hour, set expiry
                self.client.expire(key, 3600)
            
            if current > max_requests:
                logger.warning(f"⚠️  Rate limit exceeded for {ticker}: {current}/{max_requests}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return True  # Allow on error
    
    def track_trending(self, ticker: str):
        """
        Track trending stocks using a 1-hour sliding window.
        Stores events as {ticker}:{timestamp} with score=timestamp.
        """
        if not self.client:
            return
        
        try:
            import time
            current_time = time.time()
            one_hour_ago = current_time - 3600
            key = "trending:window"
            
            # Add event: Member="TICKER:TIMESTAMP", Score=TIMESTAMP
            member = f"{ticker.upper()}:{current_time}"
            self.client.zadd(key, {member: current_time})
            
            # Remove old events (older than 1 hour)
            self.client.zremrangebyscore(key, 0, one_hour_ago)
            
            # Optional: Set hard TTL on the key itself to auto-expire if no activity for >1hr
            self.client.expire(key, 3700)
            
        except Exception as e:
            logger.error(f"Error tracking trending: {e}")
    
    def get_trending_stocks(self, limit: int = 10) -> List[tuple]:
        """
        Get most analyzed stocks in the last hour.
        Aggregates counts from the sliding window.
        """
        if not self.client:
            return []
        
        try:
            import time
            from collections import Counter
            
            current_time = time.time()
            one_hour_ago = current_time - 3600
            key = "trending:window"
            
            # 1. Cleanup old data first ensuring accurate read
            self.client.zremrangebyscore(key, 0, one_hour_ago)
            
            # 2. Get all valid events in window
            events = self.client.zrange(key, 0, -1)
            
            # 3. Aggregate counts in Python (Events are "TICKER:TIMESTAMP")
            counts = Counter()
            for event in events:
                # event is typically bytes, decode if needed (decode_responses=True handled in init)
                if ":" in event:
                    ticker = event.split(":")[0]
                    counts[ticker] += 1
            
            # 4. Sort by count desc, then ticker asc
            # most_common returns [(ticker, count), ...] sorted by count
            return counts.most_common(limit)
            
        except Exception as e:
            logger.error(f"Error getting trending stocks: {e}")
            return []
    
    def set_price(self, ticker: str, price: float, ttl: int = 300):
        """Cache latest price with 5-minute TTL."""
        if not self.client:
            return
        
        try:
            key = f"price:{ticker.upper()}"
            data = {
                "price": price,
                "timestamp": datetime.now().isoformat()
            }
            self.client.setex(key, ttl, json.dumps(data))
        except Exception as e:
            logger.error(f"Error caching price: {e}")
    
    def get_price(self, ticker: str) -> Optional[Dict]:
        """Get cached price."""
        if not self.client:
            return None
        
        try:
            key = f"price:{ticker.upper()}"
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Error getting cached price: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.client:
            return {"status": "disconnected"}
        
        try:
            info = self.client.info()
            return {
                "status": "connected",
                "total_keys": self.client.dbsize(),
                "memory_used": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": round(
                    info.get("keyspace_hits", 0) / 
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1) * 100, 
                    2
                )
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"status": "error", "message": str(e)}


# Global instance
redis_cache = RedisCache()
