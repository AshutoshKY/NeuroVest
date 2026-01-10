"""
Admin Dashboard API

Unified endpoint providing a comprehensive system overview for the admin dashboard.
Aggregates data from all admin services for single-fetch dashboard loading.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
from datetime import datetime, timezone
from loguru import logger

from app.core.rbac import require_admin
from app.models.user import User
from app.services.metrics_collector import MetricsCollector, InfraMetricsCollector
from app.services.ai_metrics import AIMetricsService
from app.services.kill_switch import get_all_switches
from app.services.session_control import get_session_control_status
from app.core.redis_client import get_redis


router = APIRouter(prefix="/admin/dashboard", tags=["admin-dashboard"])


@router.get("/overview")
async def get_dashboard_overview(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get comprehensive admin dashboard overview.
    
    Single endpoint to fetch all key metrics for the main admin dashboard.
    Returns:
    - System health status
    - Infrastructure metrics (Redis, MySQL, ChromaDB)
    - Request/traffic metrics
    - AI/RAG usage and costs
    - Kill switch states
    - Session control status
    - Active user counts
    """
    try:
        # 1. Infrastructure Health
        infra = InfraMetricsCollector.get_all_infrastructure_metrics()
        
        # Determine overall health
        health_checks = [
            infra.get("redis", {}).get("connected", False),
            infra.get("mysql", {}).get("connected", False),
            infra.get("chromadb", {}).get("connected", False)
        ]
        overall_health = "healthy" if all(health_checks) else "degraded" if any(health_checks) else "down"
        
        # 2. Request Metrics (last hour)
        request_metrics = MetricsCollector.get_request_metrics(minutes=60)
        
        # 3. AI Metrics (today)
        ai_summary = AIMetricsService.get_daily_summary()
        
        # 4. Kill Switch Status
        kill_switches = get_all_switches()
        active_switches = [name for name, switch in kill_switches.items() if switch.is_active]
        
        # 5. Session Status
        session_status = get_session_control_status()
        
        # 6. Active Users (from Redis)
        redis = get_redis()
        active_users = 0
        rate_limited_users = 0
        try:
            # Count unique rate limit keys as proxy for active users
            keys = redis.keys("ratelimit:*:user:*")
            active_users = len(set(k.decode().split(":")[2] for k in keys if b"user" in k))
            
            # Count blacklisted IPs
            blacklisted = redis.scard("security:ip_blacklist") or 0
        except Exception:
            blacklisted = 0
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_health": overall_health,
            
            # System Status
            "system": {
                "uptime": "N/A",  # Would need to track startup time
                "active_kill_switches": len(active_switches),
                "kill_switch_names": active_switches,
                "auth_epoch": session_status.get("auth_epoch"),
                "maintenance_mode": "maintenance_mode" in active_switches
            },
            
            # Infrastructure
            "infrastructure": {
                "redis": {
                    "status": "healthy" if infra.get("redis", {}).get("connected") else "down",
                    "memory_mb": infra.get("redis", {}).get("memory_used_mb", 0),
                    "connections": infra.get("redis", {}).get("connected_clients", 0),
                    "hit_rate": infra.get("redis", {}).get("hit_rate_percent", 0)
                },
                "mysql": {
                    "status": "healthy" if infra.get("mysql", {}).get("connected") else "down",
                    "connections": infra.get("mysql", {}).get("threads_connected", 0),
                    "tables": infra.get("mysql", {}).get("table_count", 0),
                    "rows": infra.get("mysql", {}).get("total_rows", 0)
                },
                "chromadb": {
                    "status": "healthy" if infra.get("chromadb", {}).get("connected") else "down",
                    "documents": infra.get("chromadb", {}).get("document_count", 0),
                    "collections": len(infra.get("chromadb", {}).get("collections", []))
                }
            },
            
            # Traffic
            "traffic": {
                "requests_per_second": request_metrics.get("requests_per_second", 0),
                "total_requests_1h": request_metrics.get("total_requests", 0),
                "avg_latency_ms": request_metrics.get("average_latency_ms", 0),
                "error_rate_percent": request_metrics.get("error_rate_percent", 0),
                "unique_users_1h": request_metrics.get("unique_users", 0)
            },
            
            # AI/LLM
            "ai": {
                "requests_today": ai_summary.get("total_requests", 0),
                "tokens_today": ai_summary.get("total_tokens", 0),
                "cost_today_usd": ai_summary.get("total_cost_usd", 0),
                "guardrail_rejections": ai_summary.get("guardrail_rejections", 0)
            },
            
            # Security
            "security": {
                "blacklisted_ips": blacklisted,
                "active_users": active_users,
                "rate_limited_count": rate_limited_users
            },
            
            # Actor Info
            "accessed_by": {
                "admin_id": current_user.id,
                "admin_email": current_user.email,
                "role": current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
            }
        }
        
    except Exception as e:
        logger.error(f"[ADMIN_DASHBOARD] Overview failed: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.get("/quick-stats")
async def get_quick_stats(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get quick stats for dashboard header KPI cards.
    Lightweight endpoint for frequent polling.
    """
    try:
        # Get minimal data for KPIs
        request_metrics = MetricsCollector.get_request_metrics(minutes=5)
        ai_summary = AIMetricsService.get_daily_summary()
        kill_switches = get_all_switches()
        
        active_switches = sum(1 for s in kill_switches.values() if s.is_active)
        
        return {
            "rps": request_metrics.get("requests_per_second", 0),
            "error_rate": request_metrics.get("error_rate_percent", 0),
            "ai_requests": ai_summary.get("total_requests", 0),
            "ai_cost": ai_summary.get("total_cost_usd", 0),
            "active_switches": active_switches,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"[ADMIN_DASHBOARD] Quick stats failed: {e}")
        return {"error": str(e)}


@router.get("/alerts")
async def get_system_alerts(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get active system alerts and warnings.
    """
    alerts = []
    
    try:
        # Check kill switches
        kill_switches = get_all_switches()
        for name, switch in kill_switches.items():
            if switch.is_active:
                alerts.append({
                    "severity": "critical" if name == "emergency_shutdown" else "warning",
                    "type": "kill_switch",
                    "message": f"Kill switch '{name}' is ACTIVE",
                    "details": {"reason": switch.reason},
                    "timestamp": switch.activated_at.isoformat() if switch.activated_at else None
                })
        
        # Check infrastructure
        infra = InfraMetricsCollector.get_all_infrastructure_metrics()
        
        if not infra.get("redis", {}).get("connected"):
            alerts.append({
                "severity": "critical",
                "type": "infrastructure",
                "message": "Redis is DOWN",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        if not infra.get("mysql", {}).get("connected"):
            alerts.append({
                "severity": "critical",
                "type": "infrastructure",
                "message": "MySQL is DOWN",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        if not infra.get("chromadb", {}).get("connected"):
            alerts.append({
                "severity": "warning",
                "type": "infrastructure",
                "message": "ChromaDB is DOWN",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        # Check error rate
        metrics = MetricsCollector.get_request_metrics(minutes=5)
        error_rate = metrics.get("error_rate_percent", 0)
        if error_rate > 10:
            alerts.append({
                "severity": "critical" if error_rate > 25 else "warning",
                "type": "traffic",
                "message": f"High error rate: {error_rate:.1f}%",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        return {
            "alert_count": len(alerts),
            "alerts": alerts,
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"[ADMIN_DASHBOARD] Alerts failed: {e}")
        return {"error": str(e), "alert_count": 0, "alerts": []}
