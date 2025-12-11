"""
Admin Cache Management Endpoints
Flush and manage Redis cache
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Literal

from app.core.database import get_db
from app.core.redis_client import get_redis
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from loguru import logger


router = APIRouter(prefix="/admin/cache", tags=["Admin Cache"])
redis = get_redis()


class FlushSelectiveRequest(BaseModel):
    category: Literal["analysis", "rate_limits", "sessions", "trending", "stock_data"]


@router.post("/flush-all")
async def flush_all_cache(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Flush all Redis cache (requires confirmation)"""
    if current_user.role != "admin":
        raise HTTPException(403, "Admin access required")
    
    try:
        redis.flushdb()
        
        # Log to audit
        from sqlalchemy import text
        db.execute(
            text("""
                INSERT INTO admin_audit_logs (admin_user_id, action, target, ip_address)
                VALUES (:admin_id, 'flush_all_cache', 'Redis', :ip)
            """),
            {"admin_id": current_user.id, "ip": "system"}
        )
        db.commit()
        
        logger.warning(f"[ADMIN] All cache flushed by user {current_user.email}")
        
        return {"message": "All cache flushed successfully"}
    except Exception as e:
        logger.error(f"[ADMIN] Cache flush error: {e}")
        raise HTTPException(500, "Failed to flush cache")


@router.post("/flush-selective")
async def flush_selective_cache(
    request: FlushSelectiveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Flush specific category of cache"""
    if current_user.role != "admin":
        raise HTTPException(403, "Admin access required")
    
    try:
        # Define patterns for each category
        patterns = {
            "analysis": "analysis:*",
            "rate_limits": "ratelimit:*",
            "sessions": "session:*",
            "trending": "trending:*",
            "stock_data": "stock:price:*"
        }
        
        pattern = patterns.get(request.category)
        if not pattern:
            raise HTTPException(400, "Invalid category")
        
        # Delete keys matching pattern
        keys = redis.keys(pattern)
        if keys:
            redis.delete(*keys)
        
        # Log to audit
        from sqlalchemy import text
        db.execute(
            text("""
                INSERT INTO admin_audit_logs (admin_user_id, action, target, ip_address)
                VALUES (:admin_id, 'flush_selective_cache', :category, :ip)
            """),
            {"admin_id": current_user.id, "category": request.category, "ip": "system"}
        )
        db.commit()
        
        logger.warning(f"[ADMIN] {request.category} cache flushed by {current_user.email}")
        
        return {
            "message": f"Flushed {len(keys)} keys from {request.category}",
            "keys_deleted": len(keys)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ADMIN] Selective cache flush error: {e}")
        raise HTTPException(500, "Failed to flush selective cache")


@router.get("/stats")
async def get_cache_stats(
    current_user: User = Depends(get_current_user)
):
    """Get Redis cache statistics"""
    if current_user.role != "admin":
        raise HTTPException(403, "Admin access required")
    
    try:
        # Get Redis info
        info = redis.info("memory")
        total_keys = redis.dbsize()
        
        # Get category breakdown
        categories = {
            "analysis": len(redis.keys("analysis:*")),
            "rate_limits": len(redis.keys("ratelimit:*")),
            "sessions": len(redis.keys("session:*")),
            "trending": len(redis.keys("trending:*")),
            "stock_data": len(redis.keys("stock:price:*"))
        }
        
        memory_mb = round(info.get("used_memory", 0) / (1024 * 1024), 2)
        
        return {
            "total_keys": total_keys,
            "memory_mb": memory_mb,
            "categories": categories
        }
    except Exception as e:
        logger.error(f"[ADMIN] Cache stats error: {e}")
        raise HTTPException(500, "Failed to get cache stats")
