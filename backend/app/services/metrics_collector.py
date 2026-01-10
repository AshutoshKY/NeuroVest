"""
Metrics Collector Service

Collects and stores metrics for the Admin Command Center:
- Request metrics (latency, error rates, RPS)
- Infrastructure metrics (Redis, MySQL, ChromaDB)
- System metrics (CPU, memory - future)

All metrics are stored in Redis with TTLs for automatic cleanup.
Designed for real-time dashboard updates.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from loguru import logger
import time
import json

from app.core.redis_client import get_redis


# Redis key patterns for metrics
METRICS_PREFIX = "metrics:"
REQUEST_METRICS_PREFIX = f"{METRICS_PREFIX}request:"
INFRA_METRICS_PREFIX = f"{METRICS_PREFIX}infra:"
AGGREGATE_METRICS_PREFIX = f"{METRICS_PREFIX}aggregate:"


class MetricsCollector:
    """
    Centralized metrics collection and retrieval.
    Thread-safe, uses Redis for storage.
    """
    
    # Metric retention periods
    RETENTION_MINUTES = 60  # Keep minute-level data for 1 hour
    RETENTION_HOURS = 24  # Keep hour-level data for 24 hours
    
    @staticmethod
    def record_request_metric(
        endpoint: str,
        method: str,
        status_code: int,
        latency_ms: float,
        user_id: Optional[int] = None,
        is_error: bool = False
    ):
        """
        Record a single request metric.
        Called from middleware after each request.
        """
        try:
            redis = get_redis()
            now = datetime.now(timezone.utc)
            minute_key = now.strftime("%Y%m%d%H%M")
            hour_key = now.strftime("%Y%m%d%H")
            
            # === Per-minute aggregation ===
            minute_stats_key = f"{REQUEST_METRICS_PREFIX}minute:{minute_key}"
            
            # Increment counters
            pipe = redis.pipeline()
            pipe.hincrby(minute_stats_key, "total_requests", 1)
            pipe.hincrbyfloat(minute_stats_key, "total_latency_ms", latency_ms)
            
            if is_error or status_code >= 400:
                pipe.hincrby(minute_stats_key, "error_count", 1)
            
            if status_code >= 200 and status_code < 300:
                pipe.hincrby(minute_stats_key, "success_count", 1)
            
            # Track unique users
            if user_id:
                pipe.sadd(f"{REQUEST_METRICS_PREFIX}users:{minute_key}", user_id)
            
            # Set TTL (only on first write)
            pipe.expire(minute_stats_key, MetricsCollector.RETENTION_MINUTES * 60)
            pipe.execute()
            
            # === Per-endpoint tracking ===
            endpoint_key = f"{REQUEST_METRICS_PREFIX}endpoint:{endpoint.replace('/', '_')}:{hour_key}"
            
            redis.hincrby(endpoint_key, "count", 1)
            redis.hincrbyfloat(endpoint_key, "total_latency", latency_ms)
            redis.expire(endpoint_key, MetricsCollector.RETENTION_HOURS * 3600)
            
        except Exception as e:
            logger.error(f"[METRICS] Failed to record request metric: {e}")
    
    @staticmethod
    def record_error(
        endpoint: str,
        error_type: str,
        error_message: str
    ):
        """Record an error for tracking"""
        try:
            redis = get_redis()
            now = datetime.now(timezone.utc)
            hour_key = now.strftime("%Y%m%d%H")
            
            # Store recent errors (capped list)
            error_data = json.dumps({
                "endpoint": endpoint,
                "type": error_type,
                "message": error_message[:500],  # Truncate long messages
                "timestamp": now.isoformat()
            })
            
            error_list_key = f"{REQUEST_METRICS_PREFIX}errors:{hour_key}"
            redis.lpush(error_list_key, error_data)
            redis.ltrim(error_list_key, 0, 99)  # Keep last 100 errors
            redis.expire(error_list_key, MetricsCollector.RETENTION_HOURS * 3600)
            
        except Exception as e:
            logger.error(f"[METRICS] Failed to record error: {e}")
    
    @staticmethod
    def get_request_metrics(minutes: int = 60) -> Dict[str, Any]:
        """
        Get aggregated request metrics for the last N minutes.
        Used by admin dashboard.
        """
        try:
            redis = get_redis()
            now = datetime.now(timezone.utc)
            
            total_requests = 0
            total_latency = 0.0
            total_errors = 0
            total_success = 0
            unique_users = set()
            
            # Aggregate minute-level data
            for i in range(minutes):
                minute = now - timedelta(minutes=i)
                minute_key = minute.strftime("%Y%m%d%H%M")
                stats_key = f"{REQUEST_METRICS_PREFIX}minute:{minute_key}"
                
                stats = redis.hgetall(stats_key)
                if stats:
                    # Keys are strings because Redis client uses decode_responses=True
                    total_requests += int(stats.get("total_requests", 0))
                    total_latency += float(stats.get("total_latency_ms", 0))
                    total_errors += int(stats.get("error_count", 0))
                    total_success += int(stats.get("success_count", 0))
                
                # Get unique users
                users_key = f"{REQUEST_METRICS_PREFIX}users:{minute_key}"
                users = redis.smembers(users_key)
                unique_users.update(users)
            
            avg_latency = total_latency / total_requests if total_requests > 0 else 0
            error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
            rps = total_requests / (minutes * 60) if minutes > 0 else 0
            
            return {
                "period_minutes": minutes,
                "total_requests": total_requests,
                "requests_per_second": round(rps, 2),
                "average_latency_ms": round(avg_latency, 2),
                "error_count": total_errors,
                "error_rate_percent": round(error_rate, 2),
                "success_count": total_success,
                "unique_users": len(unique_users),
                "timestamp": now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"[METRICS] Failed to get request metrics: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def get_recent_errors(limit: int = 20) -> List[Dict]:
        """Get recent errors for dashboard"""
        try:
            redis = get_redis()
            now = datetime.now(timezone.utc)
            hour_key = now.strftime("%Y%m%d%H")
            
            error_list_key = f"{REQUEST_METRICS_PREFIX}errors:{hour_key}"
            errors = redis.lrange(error_list_key, 0, limit - 1)
            
            return [json.loads(e.decode()) for e in errors]
            
        except Exception as e:
            logger.error(f"[METRICS] Failed to get recent errors: {e}")
            return []


class InfraMetricsCollector:
    """
    Infrastructure metrics collection for Redis, MySQL, ChromaDB.
    """
    
    @staticmethod
    def collect_redis_metrics() -> Dict[str, Any]:
        """Collect Redis server metrics"""
        try:
            redis = get_redis()
            info = redis.info()
            
            return {
                "connected": True,
                "version": info.get("redis_version", "unknown"),
                "memory_used_mb": round(info.get("used_memory", 0) / (1024 * 1024), 2),
                "memory_peak_mb": round(info.get("used_memory_peak", 0) / (1024 * 1024), 2),
                "connected_clients": info.get("connected_clients", 0),
                "commands_per_sec": info.get("instantaneous_ops_per_sec", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate_percent": round(
                    info.get("keyspace_hits", 0) / 
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1) * 100, 
                    2
                ),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"[METRICS] Failed to collect Redis metrics: {e}")
            return {"connected": False, "error": str(e)}
    
    @staticmethod
    def collect_mysql_metrics() -> Dict[str, Any]:
        """Collect MySQL database metrics"""
        try:
            from app.core.database import SessionLocal
            from sqlalchemy import text
            
            db = SessionLocal()
            try:
                # Check connection
                db.execute(text("SELECT 1"))
                
                # Get status variables
                result = db.execute(text("SHOW GLOBAL STATUS WHERE Variable_name IN ('Threads_connected', 'Questions', 'Uptime', 'Slow_queries', 'Connections')"))
                status = {row[0]: row[1] for row in result.fetchall()}
                
                # Get table stats
                result = db.execute(text("""
                    SELECT 
                        COUNT(*) as table_count,
                        SUM(table_rows) as total_rows
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE()
                """))
                table_stats = result.fetchone()
                
                return {
                    "connected": True,
                    "threads_connected": int(status.get("Threads_connected", 0)),
                    "total_queries": int(status.get("Questions", 0)),
                    "slow_queries": int(status.get("Slow_queries", 0)),
                    "total_connections": int(status.get("Connections", 0)),
                    "uptime_seconds": int(status.get("Uptime", 0)),
                    "table_count": table_stats[0] if table_stats else 0,
                    "total_rows": int(table_stats[1]) if table_stats and table_stats[1] else 0,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"[METRICS] Failed to collect MySQL metrics: {e}")
            return {"connected": False, "error": str(e)}
    
    @staticmethod
    def collect_chromadb_metrics() -> Dict[str, Any]:
        """Collect ChromaDB vector database metrics"""
        try:
            from app.services.embeddings import embedding_service
            
            # Get collection counts
            collection_count = embedding_service.get_collection_count()
            
            return {
                "connected": True,
                "document_count": collection_count,
                "collections": ["stock_news", "stock_analysis"],  # Known collections
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"[METRICS] Failed to collect ChromaDB metrics: {e}")
            return {"connected": False, "error": str(e)}
    
    @staticmethod
    def get_all_infrastructure_metrics() -> Dict[str, Any]:
        """Get metrics for all infrastructure components"""
        return {
            "redis": InfraMetricsCollector.collect_redis_metrics(),
            "mysql": InfraMetricsCollector.collect_mysql_metrics(),
            "chromadb": InfraMetricsCollector.collect_chromadb_metrics()
        }


# Singleton instances
metrics_collector = MetricsCollector()
infra_metrics_collector = InfraMetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    return metrics_collector


def get_infra_metrics_collector() -> InfraMetricsCollector:
    return infra_metrics_collector
