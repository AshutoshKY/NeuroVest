"""
Health Monitor API Endpoints
Provides API access to data source health status
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
import logging

from app.services.health_monitor import health_monitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/sources", response_model=List[Dict[str, Any]])
async def get_all_sources_health():
    """
    Get health status of all data sources.
    
    Returns health metrics including uptime, response times, and recent checks.
    """
    try:
        logger.info("📊 Fetching health status for all sources", extra={
            "operation": "get_health_status",
            "endpoint": "/health/sources"
        })
        
        health_data = health_monitor.get_all_health_status()
        
        logger.info("✅ Health status fetched", extra={
            "operation": "get_health_status",
            "sources_count": len(health_data),
            "status": "success"
        })
        
        return health_data
        
    except Exception as e:
        logger.error("❌ Failed to fetch health status", extra={
            "operation": "get_health_status",
            "status": "failure",
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources/{source_name}", response_model=Dict[str, Any])
async def get_source_health(source_name: str):
    """
    Get health status of a specific data source.
    
    Args:
        source_name: Name of the data source
    """
    try:
        logger.debug(f"📊 Fetching health for {source_name}", extra={
            "operation": "get_source_health",
            "source": source_name
        })
        
        health_data = health_monitor.get_source_health(source_name)
        
        if not health_data:
            raise HTTPException(
                status_code=404,
                detail=f"Source '{source_name}' not found"
           )
        
        return health_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to fetch health for {source_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=Dict[str, Any])
async def get_health_summary():
    """
    Get overall health summary of all data sources.
    
    Returns aggregated statistics and overall uptime percentage.
    """
    try:
        logger.info("📊 Fetching health summary", extra={
            "operation": "get_health_summary"
        })
        
        summary = health_monitor.get_summary()
        
        logger.info("✅ Health summary fetched", extra={
            "operation": "get_health_summary",
            "overall_uptime": summary.get("overall_uptime_percentage"),
           "status": "success"
        })
        
        return summary
        
    except Exception as e:
        logger.error("❌ Failed to fetch health summary", extra={
            "operation": "get_health_summary",
            "status": "failure",
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-now")
async def trigger_health_check():
    """
    Trigger an immediate health check of all data sources.
    
    Normally checks run automatically every 5 minutes, but this endpoint
    allows manual triggering.
    """
    try:
        logger.info("🏥 Triggering manual health check", extra={
            "operation": "manual_health_check"
        })
        
        await health_monitor._check_all_sources()
        
        logger.info("✅ Manual health check completed", extra={
            "operation": "manual_health_check",
            "status": "success"
        })
        
        return {
            "message": "Health check triggered successfully",
            "summary": health_monitor.get_summary()
        }
        
    except Exception as e:
        logger.error("❌ Manual health check failed", extra={
            "operation": "manual_health_check",
            "status": "failure",
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=str(e))
