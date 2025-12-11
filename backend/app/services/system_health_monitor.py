"""
System Health Monitor for Admin Dashboard
Comprehensive health checking of all core services and APIs
"""
import time
import asyncio
from typing import Dict, Any
from datetime import datetime
from loguru import logger
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.redis_client import get_redis


class SystemHealthMonitor:
    """Monitor health of MySQL, Redis, ChromaDB, and external APIs"""
    
    def __init__(self):
        self.redis = get_redis()
    
    async def check_mysql(self, db: Session) -> Dict[str, Any]:
        """Check MySQL database health"""
        try:
            start = time.time()
            db.execute(text("SELECT 1"))
            latency_ms = int((time.time() - start) * 1000)
            
            # Get connection count
            result = db.execute(text("SHOW STATUS LIKE 'Threads_connected'"))
            connections = int(result.fetchone()[1])
            
            return {
                "status": "healthy",
                "latency_ms": latency_ms,
                "active_connections": connections
            }
        except Exception as e:
            logger.error(f"[HEALTH] MySQL check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis health"""
        try:
            start = time.time()
            self.redis.ping()
            latency_ms = int((time.time() - start) * 1000)
            
            info = self.redis.info("memory")
            memory_mb = round(info.get("used_memory", 0) / (1024 * 1024), 2)
            total_keys = self.redis.dbsize()
            
            return {
                "status": "healthy",
                "latency_ms": latency_ms,
                "memory_mb": memory_mb,
                "total_keys": total_keys
            }
        except Exception as e:
            logger.error(f"[HEALTH] Redis check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def check_chromadb(self) -> Dict[str, Any]:
        """Check ChromaDB health"""
        try:
            from app.services.rag import rag_service
            
            start = time.time()
            count = rag_service.collection.count() if hasattr(rag_service, 'collection') else 0
            latency_ms = int((time.time() - start) * 1000)
            
            return {
                "status": "healthy",
                "latency_ms": latency_ms,
                "document_count": count
            }
        except Exception as e:
            logger.error(f"[HEALTH] ChromaDB check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def get_openai_stats(self) -> Dict[str, Any]:
        """Get OpenAI usage statistics"""
        try:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            requests_today = int(self.redis.get(f"openai:requests:{today}") or 0)
            tokens_today = int(self.redis.get(f"openai:tokens:{today}") or 0)
            cost_usd = round((tokens_today / 1000) * 0.03, 2)  # $0.03 per 1K tokens
            
            return {
                "status": "healthy",
                "requests_today": requests_today,
                "tokens_today": tokens_today,
                "estimated_cost_usd": cost_usd
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def get_health_summary(self, db: Session) -> Dict[str, Any]:
        """Get comprehensive system health"""
        mysql, redis, chromadb = await asyncio.gather(
            self.check_mysql(db),
            self.check_redis(),
            self.check_chromadb()
        )
        
        openai = await self.get_openai_stats()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "mysql": mysql,
                "redis": redis,
                "chromadb": chromadb,
                "openai": openai
            }
        }


# Global instance
system_health_monitor = SystemHealthMonitor()
