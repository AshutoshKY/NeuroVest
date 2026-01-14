"""
Admin AI Metrics API

Provides endpoints for viewing AI/LLM usage metrics:
- Token consumption and costs
- Request latency
- Guardrail rejection rates
- Usage by type (RAG vs Sentiment)
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.core.rbac import require_admin
from app.models.user import User
from app.services.ai_metrics import (
    AIMetricsService,
    ai_metrics_service
)


router = APIRouter(prefix="/admin/ai", tags=["admin-ai"])


@router.get("/summary")
async def get_ai_summary(
    current_user: User = Depends(require_admin)
):
    """
    Get summary of today's AI usage.
    
    Returns:
    - Total requests
    - Total tokens consumed
    - Total cost in USD
    - Guardrail rejection count
    """
    return ai_metrics_service.get_daily_summary()


@router.get("/hourly")
async def get_hourly_stats(
    hours: int = Query(24, ge=1, le=168, description="Number of hours to retrieve"),
    current_user: User = Depends(require_admin)
):
    """
    Get hourly AI usage statistics.
    
    Returns list of hourly breakdowns including:
    - Token usage (prompt/completion)
    - Request counts by type
    - Cost and latency metrics
    """
    stats = ai_metrics_service.get_hourly_stats(hours)
    
    # Calculate totals
    totals = {
        "total_requests": sum(s["total_requests"] for s in stats),
        "total_tokens": sum(s["total_tokens"] for s in stats),
        "total_cost_usd": round(sum(s["total_cost_usd"] for s in stats), 4),
        "total_errors": sum(s["errors"] for s in stats)
    }
    
    return {
        "hours_requested": hours,
        "data_points": len(stats),
        "totals": totals,
        "hourly": stats
    }


@router.get("/requests")
async def get_recent_requests(
    limit: int = Query(50, ge=1, le=200, description="Number of requests to retrieve"),
    current_user: User = Depends(require_admin)
):
    """
    Get recent AI request details.
    
    Returns individual request data including:
    - Request ID, type, tokens, cost
    - Ticker (if applicable)
    - Latency and success status
    """
    requests = ai_metrics_service.get_recent_requests(limit)
    return {
        "count": len(requests),
        "requests": requests
    }


@router.get("/guardrails")
async def get_guardrail_stats(
    current_user: User = Depends(require_admin)
):
    """
    Get guardrail rejection statistics.
    
    Returns:
    - Total rejections today
    - Breakdown by rejection reason
    """
    return ai_metrics_service.get_guardrail_stats()


@router.get("/cost-breakdown")
async def get_cost_breakdown(
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    current_user: User = Depends(require_admin)
):
    """
    Get cost breakdown over time.
    
    Returns daily cost totals for trend analysis.
    """
    from datetime import datetime, timezone, timedelta
    from app.core.redis_client import get_redis
    
    redis = get_redis()
    now = datetime.now(timezone.utc)
    daily_costs = []
    
    for i in range(days):
        day = now - timedelta(days=i)
        day_key = day.strftime("%Y%m%d")
        key = f"ai_metrics:daily:{day_key}"
        
        data = redis.hgetall(key)
        if data:
            daily_costs.append({
                "date": day.strftime("%Y-%m-%d"),
                "requests": int(data.get(b"total_requests", 0)),
                "tokens": int(data.get(b"total_tokens", 0)),
                "cost_usd": round(float(data.get(b"total_cost_usd", 0)), 4)
            })
        else:
            daily_costs.append({
                "date": day.strftime("%Y-%m-%d"),
                "requests": 0,
                "tokens": 0,
                "cost_usd": 0
            })
    
    # Calculate totals
    total_cost = sum(d["cost_usd"] for d in daily_costs)
    total_requests = sum(d["requests"] for d in daily_costs)
    total_tokens = sum(d["tokens"] for d in daily_costs)
    
    return {
        "period_days": days,
        "totals": {
            "cost_usd": round(total_cost, 4),
            "requests": total_requests,
            "tokens": total_tokens,
            "avg_cost_per_request": round(total_cost / total_requests, 6) if total_requests > 0 else 0
        },
        "daily": daily_costs
    }


@router.get("/overview")
async def get_ai_overview(
    current_user: User = Depends(require_admin)
):
    """
    Get comprehensive AI metrics overview.
    
    Combines daily summary, recent activity, and guardrail stats.
    """
    summary = ai_metrics_service.get_daily_summary()
    guardrails = ai_metrics_service.get_guardrail_stats()
    recent = ai_metrics_service.get_recent_requests(10)
    
    # Get last 24 hours for trend
    hourly = ai_metrics_service.get_hourly_stats(24)
    
    # Calculate trends
    tokens_24h = sum(h["total_tokens"] for h in hourly)
    cost_24h = sum(h["total_cost_usd"] for h in hourly)
    requests_24h = sum(h["total_requests"] for h in hourly)
    
    return {
        "today": summary,
        "last_24h": {
            "requests": requests_24h,
            "tokens": tokens_24h,
            "cost_usd": round(cost_24h, 4)
        },
        "guardrails": guardrails,
        "recent_activity": recent,
        "healthy": True  # Could add health checks here
    }
