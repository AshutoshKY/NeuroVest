"""
Admin Metrics API

Provides endpoints for retrieving system and request metrics.
All endpoints require ADMIN role.
"""

from fastapi import APIRouter, Depends
from typing import Optional

from app.core.rbac import require_admin
from app.models.user import User
from app.services.metrics_collector import (
    MetricsCollector,
    InfraMetricsCollector
)


router = APIRouter(prefix="/admin/metrics", tags=["admin-metrics"])


@router.get("/requests")
async def get_request_metrics(
    minutes: int = 60,
    current_user: User = Depends(require_admin)
):
    """
    Get aggregated request metrics for the last N minutes.
    
    Returns:
    - total_requests: Total request count
    - requests_per_second: Average RPS
    - average_latency_ms: Average response time
    - error_rate_percent: Percentage of error responses
    - unique_users: Unique authenticated users
    """
    return MetricsCollector.get_request_metrics(minutes)


@router.get("/errors")
async def get_recent_errors(
    limit: int = 20,
    current_user: User = Depends(require_admin)
):
    """
    Get recent errors for debugging.
    Returns last N errors with endpoint, type, and message.
    """
    errors = MetricsCollector.get_recent_errors(limit)
    return {"errors": errors, "count": len(errors)}


@router.get("/infrastructure")
async def get_infrastructure_metrics(
    current_user: User = Depends(require_admin)
):
    """
    Get infrastructure health metrics for Redis, MySQL, and ChromaDB.
    """
    return InfraMetricsCollector.get_all_infrastructure_metrics()


@router.get("/infrastructure/redis")
async def get_redis_metrics(
    current_user: User = Depends(require_admin)
):
    """Get Redis-specific metrics"""
    return InfraMetricsCollector.collect_redis_metrics()


@router.get("/infrastructure/mysql")
async def get_mysql_metrics(
    current_user: User = Depends(require_admin)
):
    """Get MySQL-specific metrics"""
    return InfraMetricsCollector.collect_mysql_metrics()


@router.get("/infrastructure/chromadb")
async def get_chromadb_metrics(
    current_user: User = Depends(require_admin)
):
    """Get ChromaDB-specific metrics"""
    return InfraMetricsCollector.collect_chromadb_metrics()


@router.get("/overview")
async def get_metrics_overview(
    current_user: User = Depends(require_admin)
):
    """
    Get overview of all metrics for admin dashboard.
    Combines request metrics and infrastructure health.
    """
    request_metrics = MetricsCollector.get_request_metrics(60)  # Last hour
    infra_metrics = InfraMetricsCollector.get_all_infrastructure_metrics()
    
    # Calculate overall health
    redis_healthy = infra_metrics.get("redis", {}).get("connected", False)
    mysql_healthy = infra_metrics.get("mysql", {}).get("connected", False)
    chromadb_healthy = infra_metrics.get("chromadb", {}).get("connected", False)
    
    if redis_healthy and mysql_healthy and chromadb_healthy:
        overall_health = "healthy"
    elif redis_healthy and mysql_healthy:
        overall_health = "degraded"
    else:
        overall_health = "critical"
    
    return {
        "overall_health": overall_health,
        "request_metrics": request_metrics,
        "infrastructure": infra_metrics,
        "services": {
            "redis": {"status": "healthy" if redis_healthy else "down"},
            "mysql": {"status": "healthy" if mysql_healthy else "down"},
            "chromadb": {"status": "healthy" if chromadb_healthy else "down"}
        }
    }
