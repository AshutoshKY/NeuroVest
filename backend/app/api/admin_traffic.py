"""
Admin Traffic Analytics Endpoints  
Provides traffic statistics, geo-distribution, and trending data
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.redis_client import get_redis
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from loguru import logger


router = APIRouter(prefix="/admin/traffic", tags=["Admin Traffic"])
redis = get_redis()


@router.get("/realtime")
async def get_realtime_traffic(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get real-time traffic metrics (last 5 minutes)"""
    if current_user.role != "admin":
        raise HTTPException(403, "Admin access required")
    
    try:
        # Get active users (sessions active in last 5 mins)
        five_mins_ago = datetime.utcnow() - timedelta(minutes=5)
        result = db.execute(
            text("""
                SELECT COUNT(DISTINCT user_id) as active_users
                FROM active_sessions
                WHERE last_activity >= :time_threshold AND is_active = 1
            """),
            {"time_threshold": five_mins_ago}
        )
        active_users = result.scalar() or 0
        
        # Get requests last hour from Redis (if tracked)
        requests_last_hour = int(redis.get("traffic:requests:last_hour") or 0)
        
        # Get analyses last hour from analysis_history
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        result = db.execute(
            text("""
                SELECT COUNT(*) as analyses_count
                FROM analysis_history
                WHERE timestamp >= :time_threshold
            """),
            {"time_threshold": one_hour_ago}
        )
        analyses_last_hour = result.scalar() or 0
        
        return {
            "active_users_5min": active_users,
            "requests_last_hour": requests_last_hour,
            "analyses_last_hour": analyses_last_hour,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"[ADMIN] Realtime traffic error: {e}")
        raise HTTPException(500, "Failed to get realtime traffic")


@router.get("/hourly")
async def get_hourly_traffic(
    hours: int = 24,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get hourly traffic breakdown"""
    if current_user.role != "admin":
        raise HTTPException(403, "Admin access required")
    
    try:
        # Query traffic_stats table
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        result = db.execute(
            text("""
                SELECT hour_timestamp, total_requests, unique_ips, total_analyses
                FROM traffic_stats
                WHERE hour_timestamp >= :time_threshold
                ORDER BY hour_timestamp DESC
            """),
            {"time_threshold": time_threshold}
        )
        
        hourly_data = [{
            "hour": row[0].isoformat(),
            "requests": row[1],
            "unique_ips": row[2],
            "analyses": row[3]
        } for row in result.fetchall()]
        
        return {
            "hours": hours,
            "data_points": len(hourly_data),
            "hourly_data": hourly_data
        }
    except Exception as e:
        logger.error(f"[ADMIN] Hourly traffic error: {e}")
        raise HTTPException(500, "Failed to get hourly traffic")


@router.get("/daily")
async def get_daily_traffic(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get daily traffic aggregation"""
    if current_user.role != "admin":
        raise HTTPException(403, "Admin access required")
    
    try:
        # Aggregate hourly data into daily
        time_threshold = datetime.utcnow() - timedelta(days=days)
        result = db.execute(
            text("""
                SELECT 
                    DATE(hour_timestamp) as day,
                    SUM(total_requests) as requests,
                    SUM(total_analyses) as analyses
                FROM traffic_stats
                WHERE hour_timestamp >= :time_threshold
                GROUP BY DATE(hour_timestamp)
                ORDER BY day DESC
            """),
            {"time_threshold": time_threshold}
        )
        
        daily_data = [{
            "date": row[0].isoformat() if row[0] else None,
            "requests": row[1] or 0,
            "analyses": row[2] or 0
        } for row in result.fetchall()]
        
        return {
            "days": days,
            "data_points": len(daily_data),
            "daily_data": daily_data
        }
    except Exception as e:
        logger.error(f"[ADMIN] Daily traffic error: {e}")
        raise HTTPException(500, "Failed to get daily traffic")


@router.get("/geo-distribution")
async def get_geo_distribution(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get geographic distribution of requests"""
    if current_user.role != "admin":
        raise HTTPException(403, "Admin access required")
    
    # For now return placeholder
    # Production: integrate with IP geolocation service
    return {
        "countries": [
            {"country": "India", "code": "IN", "requests": 1250},
            {"country": "United States", "code": "US", "requests": 450},
            {"country": "United Kingdom", "code": "GB", "requests": 180}
        ]
    }


@router.get("/top-ips")
async def get_top_ips(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get top IPs by request count"""
    if current_user.role != "admin":
        raise HTTPException(403, "Admin access required")
    
    try:
        # Get from analysis_history (most active IPs)
        result = db.execute(
            text("""
                SELECT 
                    ip_address,
                    COUNT(*) as request_count,
                    MAX(timestamp) as last_seen
                FROM analysis_history
                WHERE ip_address IS NOT NULL
                GROUP BY ip_address
                ORDER BY request_count DESC
                LIMIT :limit
            """),
            {"limit": limit}
        )
        
        top_ips = [{
            "ip": row[0],
            "requests": row[1],
            "last_seen": row[2].isoformat() if row[2] else None
        } for row in result.fetchall()]
        
        return {
            "limit": limit,
            "count": len(top_ips),
            "top_ips": top_ips
        }
    except Exception as e:
        logger.error(f"[ADMIN] Top IPs error: {e}")
        raise HTTPException(500, "Failed to get top IPs")


@router.get("/popular-stocks")
async def get_popular_stocks(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get most analyzed stocks"""
    if current_user.role != "admin":
        raise HTTPException(403, "Admin access required")
    
    try:
        # Get from Redis trending or analysis_history
        result = db.execute(
            text("""
                SELECT 
                    ticker,
                    COUNT(*) as analysis_count,
                    COUNT(DISTINCT user_id) as unique_users,
                    MAX(timestamp) as last_analyzed
                FROM analysis_history
                WHERE ticker IS NOT NULL
                GROUP BY ticker
                ORDER BY analysis_count DESC
                LIMIT :limit
            """),
            {"limit": limit}
        )
        
        popular_stocks = [{
            "ticker": row[0],
            "analysis_count": row[1],
            "unique_users": row[2],
            "last_analyzed": row[3].isoformat() if row[3] else None
        } for row in result.fetchall()]
        
        return {
            "limit": limit,
            "count": len(popular_stocks),
            "popular_stocks": popular_stocks
        }
    except Exception as e:
        logger.error(f"[ADMIN] Popular stocks error: {e}")
        raise HTTPException(500, "Failed to get popular stocks")
