"""
Admin Health Monitoring Endpoints
Provides system health information for admin dashboard
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.services.system_health_monitor import system_health_monitor
from loguru import logger


router = APIRouter(prefix="/admin/health", tags=["Admin Health"])


@router.get("/summary")
async def get_health_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive health summary of all system components.
    Requires admin authentication.
    """
    # Check admin role
    if current_user.role != "admin":
        raise HTTPException(403, "Admin access required")
    
    try:
        summary = await system_health_monitor.get_health_summary(db)
        return summary
    except Exception as e:
        logger.error(f"[ADMIN] Health summary error: {e}")
        raise HTTPException(500, "Failed to get health summary")


@router.get("/history")
async def get_health_history(
    hours: int = 24,
    current_user: User = Depends(get_current_user)
):
    """
    Get historical health data for charts.
    Returns simulated data (production would use time-series DB).
    """
    if current_user.role != "admin":
        raise HTTPException(403, "Admin access required")
    
    # For now, return placeholder
    # In production, query time-series data from Redis or InfluxDB
    from datetime import datetime, timedelta
    
    history = []
    current_time = datetime.utcnow()
    
    for i in range(hours):
        timestamp = current_time - timedelta(hours=hours - i)
        history.append({
            "timestamp": timestamp.isoformat(),
            "mysql_latency_ms": 5,
            "redis_latency_ms": 2,
            "chromadb_latency_ms": 15
        })
    
    return {
        "hours": hours,
        "data_points": len(history),
        "history": history
    }
