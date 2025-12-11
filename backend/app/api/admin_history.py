"""
Admin History and Logs Endpoints
View analysis history and failed login attempts
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta

from app.core.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from loguru import logger


router = APIRouter(prefix="/admin/history", tags=["Admin History"])


@router.get("/analyses")
async def get_analysis_history(
    hours: int = Query(24, ge=1, le=168),  # 1 hour to 7 days
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get analysis history for all users (admin only).
    Shows comprehensive stats and top stocks.
    """
    if current_user.role != "admin":
        raise HTTPException(403, "Admin access required")
    
    try:
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        offset = (page - 1) * limit
        
        # Get analyses with pagination
        result = db.execute(
            text("""
                SELECT 
                    ah.id,
                    ah.ticker,
                    ah.user_id,
                    u.email as user_email,
                    ah.sentiment,
                    ah.success,
                    ah.cached,
                    ah.latency_ms,
                    ah.timestamp,
                    ah.ip_address
                FROM analysis_history ah
                LEFT JOIN users u ON ah.user_id = u.id
                WHERE ah.timestamp >= :time_threshold
                ORDER BY ah.timestamp DESC
                LIMIT :limit OFFSET :offset
            """),
            {"time_threshold": time_threshold, "limit": limit, "offset": offset}
        )
        
        analyses = [{
            "id": row[0],
            "ticker": row[1],
            "user_id": row[2],
            "user_email": row[3] or "Guest",
            "sentiment": row[4],
            "success": row[5],
            "cached": row[6],
            "latency_ms": row[7],
            "timestamp": row[8].isoformat() if row[8] else None,
            "ip_address": row[9]
        } for row in result.fetchall()]
        
        # Get stats
        stats_result = db.execute(
            text("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
                    SUM(CASE WHEN cached = 1 THEN 1 ELSE 0 END) as cache_hits,
                    AVG(latency_ms) as avg_latency
                FROM analysis_history
                WHERE timestamp >= :time_threshold
            """),
            {"time_threshold": time_threshold}
        )
        stats = stats_result.fetchone()
        
        total = stats[0] or 0
        successes = stats[1] or 0
        cache_hits = stats[2] or 0
        avg_latency = round(stats[3], 2) if stats[3] else 0
        
        # Get top stocks
        top_stocks_result = db.execute(
            text("""
                SELECT ticker, COUNT(*) as count
                FROM analysis_history
                WHERE timestamp >= :time_threshold AND ticker IS NOT NULL
                GROUP BY ticker
                ORDER BY count DESC
                LIMIT 5
            """),
            {"time_threshold": time_threshold}
        )
        top_stocks = [{"ticker": row[0], "count": row[1]} for row in top_stocks_result.fetchall()]
        
        return {
            "page": page,
            "limit": limit,
            "total_analyses": total,
            "stats": {
                "success_rate": round((successes / total * 100), 2) if total > 0 else 0,
                "cache_hit_rate":  round((cache_hits / total * 100), 2) if total > 0 else 0,
                "avg_latency_ms": avg_latency
            },
            "top_stocks": top_stocks,
            "analyses": analyses
        }
    except Exception as e:
        logger.error(f"[ADMIN] Analysis history error: {e}")
        raise HTTPException(500, "Failed to get analysis history")


@router.get("/failed-logins")
async def get_failed_logins(
    hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get failed login attempts (for security monitoring)"""
    if current_user.role != "admin":
        raise HTTPException(403, "Admin access required")
    
    try:
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        
        result = db.execute(
            text("""
                SELECT 
                   ip_address,
                    email,
                    failure_reason,
                    timestamp
                FROM failed_login_attempts
                WHERE timestamp >= :time_threshold
                ORDER BY timestamp DESC
            """),
            {"time_threshold": time_threshold}
        )
        
        failed_logins = [{
            "ip": row[0],
            "email": row[1],
            "reason": row[2],
            "timestamp": row[3].isoformat() if row[3] else None
        } for row in result.fetchall()]
        
        return {
            "hours": hours,
            "count": len(failed_logins),
            "failed_logins": failed_logins
        }
    except Exception as e:
        logger.error(f"[ADMIN] Failed logins error: {e}")
        raise HTTPException(500, "Failed to get failed logins")
