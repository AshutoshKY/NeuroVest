"""
Redis client configuration for rate limiting and caching
"""
import redis
import os
from typing import Optional
from loguru import logger


class RedisClient:
    """Redis client singleton for rate limiting and caching"""
    
    _instance: Optional[redis.Redis] = None
    
    @classmethod
    def get_client(cls) -> redis.Redis:
        """Get Redis client instance (singleton)"""
        if cls._instance is None:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_db = int(os.getenv("REDIS_DB", "0"))
            
            try:
                cls._instance = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                cls._instance.ping()
                logger.info(f"✅ Redis connected: {redis_host}:{redis_port}")
            except Exception as e:
                logger.error(f"❌ Redis connection failed: {e}")
                raise
        
        return cls._instance
    
    @classmethod
    def close(cls):
        """Close Redis connection"""
        if cls._instance:
            cls._instance.close()
            cls._instance = None
            logger.info("Redis connection closed")


# Global Redis client getter
def get_redis() -> redis.Redis:
    """Get Redis client for dependency injection"""
    return RedisClient.get_client()
