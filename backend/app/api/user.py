"""
User Features API
Handles watchlist, favorites, settings, and account management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import logging

from app.core.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["user"])


# ==================== SCHEMAS ====================

class AddToWatchlistRequest(BaseModel):
    ticker: str

class ReorderRequest(BaseModel):
    order: List[str]  # List of tickers in new order

class UpdateSettingsRequest(BaseModel):
    theme: Optional[str] = None
    default_country: Optional[str] = None
    email_notifications: Optional[bool] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class DeleteAccountRequest(BaseModel):
    password: str
    confirmation: str  # Must be "DELETE MY ACCOUNT"


# ==================== WATCHLIST ENDPOINTS ====================

@router.get("/watchlist")
async def get_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's watchlist with real-time prices (from Redis or fresh fetch)
    
    Returns:
        - watchlist: List of stocks with prices, day range, sentiment
        - count: Current count
        - max: Maximum allowed (10)
    """
    try:
        # Fetch watchlist from DB
        result = db.execute(
            text("SELECT ticker, position FROM user_watchlist WHERE user_id = :user_id ORDER BY position"),
            {"user_id": current_user.id}
        )
        watchlist_items = result.fetchall()
        
        watchlist_data = []
        
        for item in watchlist_items:
            ticker = item[0]
            
            # Try to get price from Redis first
            from app.core.redis_client import get_redis
            redis = get_redis()
            price_key = f"stock:price:{ticker}"
            price_data = redis.get(price_key)
            
            if price_data:
                import json
                price_data = json.loads(price_data)
            else:
                # Fetch fresh price
                try:
                    from app.services.data_ingestion import data_ingestion_service
                    stock_data = await data_ingestion_service.fetch_stock_data(ticker)
                    price_data = stock_data
                    
                    # Cache for 5 minutes
                    redis.setex(price_key, 300, json.dumps(price_data))
                except Exception as e:
                    logger.warning(f"Failed to fetch price for {ticker}: {e}")
                    price_data = {}
            
            # Get sentiment from last analysis (if cached)
            sentiment = "neutral"
            from app.services.redis_cache import redis_cache
            last_analysis = redis_cache.get_analysis(ticker)
            if last_analysis and "sentiment" in last_analysis:
                sentiment_data = last_analysis.get("sentiment", {})
                if isinstance(sentiment_data, dict):
                    sentiment = sentiment_data.get("classification", "neutral")
            
            # Extract price values from price_data BEFORE using them
            current_price = price_data.get("current_price", 0.0) if price_data else 0.0
            day_low = price_data.get("day_low", 0.0) if price_data else 0.0
            day_high = price_data.get("day_high", 0.0) if price_data else 0.0
            
            watchlist_data.append({
                "ticker": ticker,
                "price": current_price,  # ✅ Now properly extracted
                "day_range": f"{day_low}-{day_high}",  # ✅ Now properly extracted
                "sentiment": sentiment,
                "last_fetched": price_data.get("timestamp", "") if price_data else ""
            })
        
        return {
            "watchlist": watchlist_data,
            "count": len(watchlist_data),
            "max": 10
        }
    
    except Exception as e:
        logger.error(f"Error fetching watchlist: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch watchlist")


@router.post("/watchlist/add")
async def add_to_watchlist(
    request: AddToWatchlistRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add ticker to watchlist (max 10)
    
    Args:
        request: Ticker to add
        
    Returns:
        - success: True if added
        - count: New count
    """
    try:
        # Check current count
        result = db.execute(
            text("SELECT COUNT(*) as count FROM user_watchlist WHERE user_id = :user_id"),
            {"user_id": current_user.id}
        )
        count = result.scalar()
        
        if count >= 10:
            raise HTTPException(
                status_code=400,
                detail="Watchlist full (maximum 10 items)"
            )
        
        # Check if already exists
        result = db.execute(
            text("SELECT id FROM user_watchlist WHERE user_id = :user_id AND ticker = :ticker"),
            {"user_id": current_user.id, "ticker": request.ticker.upper()}
        )
        if result.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Ticker already in watchlist"
            )
        
        # Insert
        db.execute(
            text("INSERT INTO user_watchlist (user_id, ticker, position) VALUES (:user_id, :ticker, :position)"),
            {"user_id": current_user.id, "ticker": request.ticker.upper(), "position": count}
        )
        db.commit()
        
        logger.info(f"User {current_user.id} added {request.ticker} to watchlist")
        
        return {"success": True, "count": count + 1}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding to watchlist: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to add to watchlist")


@router.delete("/watchlist/{ticker}")
async def remove_from_watchlist(
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove ticker from watchlist"""
    try:
        result = db.execute(
            text("DELETE FROM user_watchlist WHERE user_id = :user_id AND ticker = :ticker"),
            {"user_id": current_user.id, "ticker": ticker.upper()}
        )
        db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Ticker not in watchlist")
        
        logger.info(f"User {current_user.id} removed {ticker} from watchlist")
        
        return {"success": True}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing from watchlist: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to remove from watchlist")


@router.post("/watchlist/reorder")
async def reorder_watchlist(
    request: ReorderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reorder watchlist (drag-and-drop support)"""
    try:
        for idx, ticker in enumerate(request.order):
            db.execute(
                text("UPDATE user_watchlist SET position = :position WHERE user_id = :user_id AND ticker = :ticker"),
                {"position": idx, "user_id": current_user.id, "ticker": ticker.upper()}
            )
        db.commit()
        
        logger.info(f"User {current_user.id} reordered watchlist")
        
        return {"success": True}
    
    except Exception as e:
        logger.error(f"Error reordering watchlist: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to reorder watchlist")


# ==================== FAVORITES ENDPOINTS ====================

@router.get("/favorites")
async def get_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's favorites (same structure as watchlist)"""
    try:
        # Fetch favorites from DB
        result = db.execute(
            text("SELECT ticker, position FROM user_favorites WHERE user_id = :user_id ORDER BY position"),
            {"user_id": current_user.id}
        )
        favorites_items = result.fetchall()
        
        favorites_data = []
        
        for item in favorites_items:
            ticker = item[0]
            
            # Try to get price from Redis first
            from app.core.redis_client import get_redis
            redis = get_redis()
            price_key = f"stock:price:{ticker}"
            price_data = redis.get(price_key)
            
            if price_data:
                import json
                price_data = json.loads(price_data)
            else:
                # Fetch fresh price
                try:
                    from app.services.data_ingestion import data_ingestion_service
                    stock_data = await data_ingestion_service.fetch_stock_data(ticker)
                    price_data = stock_data
                    
                    # Cache for 5 minutes
                    redis.setex(price_key, 300, json.dumps(price_data))
                except Exception as e:
                    logger.warning(f"Failed to fetch price for {ticker}: {e}")
                    price_data = {}
            
            # Get sentiment from last analysis
            sentiment = "neutral"
            from app.services.redis_cache import redis_cache
            last_analysis = redis_cache.get_analysis(ticker)
            if last_analysis and "sentiment" in last_analysis:
                sentiment_data = last_analysis.get("sentiment", {})
                sentiment = sentiment_data.get("classification", "neutral")
            
            favorites_data.append({
                "ticker": ticker,
                "price": price_data.get("current_price", 0.0),
                "day_range": f"{price_data.get('day_low', 0.0)}-{price_data.get('day_high', 0.0)}",
                "sentiment": sentiment,
                "last_fetched": price_data.get("timestamp", "")
            })
        
        return {
            "favorites": favorites_data,
            "count": len(favorites_data),
            "max": 10
        }
    
    except Exception as e:
        logger.error(f"Error fetching favorites: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch favorites")


@router.post("/favorites/add")
async def add_to_favorites(
    request: AddToWatchlistRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add ticker to favorites (max 10)"""
    try:
        # Check current count
        result = db.execute(
            text("SELECT COUNT(*) as count FROM user_favorites WHERE user_id = :user_id"),
            {"user_id": current_user.id}
        )
        count = result.scalar()
        
        if count >= 10:
            raise HTTPException(
                status_code=400,
                detail="Favorites full (maximum 10 items)"
            )
        
        # Check if already exists
        result = db.execute(
            text("SELECT id FROM user_favorites WHERE user_id = :user_id AND ticker = :ticker"),
            {"user_id": current_user.id, "ticker": request.ticker.upper()}
        )
        if result.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Ticker already in favorites"
            )
        
        # Insert
        db.execute(
            text("INSERT INTO user_favorites (user_id, ticker, position) VALUES (:user_id, :ticker, :position)"),
            {"user_id": current_user.id, "ticker": request.ticker.upper(), "position": count}
        )
        db.commit()
        
        logger.info(f"User {current_user.id} added {request.ticker} to favorites")
        
        return {"success": True, "count": count + 1}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding to favorites: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to add to favorites")


@router.delete("/favorites/{ticker}")
async def remove_from_favorites(
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove ticker from favorites"""
    try:
        result = db.execute(
            text("DELETE FROM user_favorites WHERE user_id = :user_id AND ticker = :ticker"),
            {"user_id": current_user.id, "ticker": ticker.upper()}
        )
        db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Ticker not in favorites")
        
        logger.info(f"User {current_user.id} removed {ticker} from favorites")
        
        return {"success": True}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing from favorites: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to remove from favorites")


@router.post("/favorites/reorder")
async def reorder_favorites(
    request: ReorderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reorder favorites (drag-and-drop support)"""
    try:
        for idx, ticker in enumerate(request.order):
            db.execute(
                text("UPDATE user_favorites SET position = :position WHERE user_id = :user_id AND ticker = :ticker"),
                {"position": idx, "user_id": current_user.id, "ticker": ticker.upper()}
            )
        db.commit()
        
        logger.info(f"User {current_user.id} reordered favorites")
        
        return {"success": True}
    
    except Exception as e:
        logger.error(f"Error reordering favorites: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to reorder favorites")


# ==================== SETTINGS ENDPOINTS ====================

@router.get("/settings")
async def get_settings(
    current_user: User = Depends(get_current_user)
):
    """Get user settings"""
    return {
        "theme": current_user.theme if hasattr(current_user, 'theme') else 'dark',
        "default_country": current_user.default_country if hasattr(current_user, 'default_country') else 'IN',
        "email_notifications": current_user.email_notifications if hasattr(current_user, 'email_notifications') else False,
        "daily_analysis_limit": current_user.daily_analysis_limit if hasattr(current_user, 'daily_analysis_limit') else 5
    }


@router.put("/settings")
async def update_settings(
    request: UpdateSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user settings"""
    try:
        updates = []
        params = {"user_id": current_user.id}
        
        if request.theme is not None:
            if request.theme not in ['dark', 'light']:
                raise HTTPException(status_code=400, detail="Theme must be 'dark' or 'light'")
            updates.append("theme = :theme")
            params["theme"] = request.theme
        
        if request.default_country is not None:
            updates.append("default_country = :country")
            params["country"] = request.default_country
        
        if request.email_notifications is not None:
            updates.append("email_notifications = :notifications")
            params["notifications"] = request.email_notifications
        
        if updates:
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = :user_id"  # nosec
            db.execute(text(query), params)
            db.commit()
            
            logger.info(f"User {current_user.id} updated settings")
        
        return {"success": True}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update settings")


# ==================== PASSWORD & ACCOUNT ====================

@router.put("/password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    try:
        # Verify current password
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        if not pwd_context.verify(request.current_password, current_user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        # Validate new password
        if len(request.new_password) < 8:
            raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
        
        # Hash new password
        new_hash = pwd_context.hash(request.new_password)
        
        db.execute(
            text("UPDATE users SET hashed_password = :hash WHERE id = :id"),
            {"hash": new_hash, "id": current_user.id}
        )
        db.commit()
        
        logger.info(f"User {current_user.id} changed password")
        
        return {"success": True, "message": "Password changed successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to change password")


@router.post("/delete-account")
async def delete_account(
    request: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft delete user account"""
    try:
        # Verify confirmation text
        if request.confirmation != "DELETE MY ACCOUNT":
            raise HTTPException(
                status_code=400,
                detail="Confirmation text must be exactly 'DELETE MY ACCOUNT'"
            )
        
        # Verify password
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        if not pwd_context.verify(request.password, current_user.hashed_password):
            raise HTTPException(status_code=400, detail="Password is incorrect")
        
        # Soft delete (set deleted_at timestamp)
        db.execute(
            text("UPDATE users SET deleted_at = :now, is_active = 0 WHERE id = :id"),
            {"now": datetime.now(), "id": current_user.id}
        )
        db.commit()
        
        logger.info(f"User {current_user.id} soft-deleted account")
        
        return {"success": True, "message": "Account deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting account: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete account")


# ==================== RECENT ANALYSES ====================

@router.get("/recent-analyses")
async def get_recent_analyses(
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get last 5 analyses (metadata only, no full analysis reload)
    
    Returns:
        - analyses: List of recent analyses (ticker, date, time, sentiment)
    """
    try:
        result = db.execute(
            text("""
                SELECT ticker, DATE(timestamp) as date, TIME(timestamp) as time, sentiment
                FROM analysis_history
                WHERE user_id = :user_id AND success = 1
                ORDER BY timestamp DESC
                LIMIT :limit
            """),
            {"user_id": current_user.id, "limit": limit}
        )
        
        analyses = []
        for row in result:
            analyses.append({
                "ticker": row[0],
                "date": str(row[1]),
                "time": str(row[2]),
                "sentiment": row[3] if row[3] else "neutral"
            })
        
        return {"analyses": analyses}
    
    except Exception as e:
        logger.error(f"Error fetching recent analyses: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch recent analyses")


# ==================== REMAINING REQUESTS ====================

@router.get("/remaining-requests")
async def get_remaining_requests(
    current_user: User = Depends(get_current_user)
):
    """
    Get user's remaining daily analysis requests
    
    Returns:
        - remaining: Number of requests remaining
        - limit: Daily limit
        - reset_at: When limit resets (midnight UTC or 24hrs from first request)
    """
    try:
        from app.core.redis_client import get_redis
        redis = get_redis()
        
        # Get user's daily limit (default 5, admins can customize 5-30)
        daily_limit = current_user.daily_analysis_limit if hasattr(current_user, 'daily_analysis_limit') else 5
        
        # Check current usage from Redis
        key = f"ratelimit:user:{current_user.id}:analysis_day"
        current_count = redis.get(key)
        current_count = int(current_count) if current_count else 0
        
        remaining = max(0, daily_limit - current_count)
        
        # Get TTL for reset time
        ttl = redis.ttl(key)
        reset_in_seconds = ttl if ttl > 0 else 86400  # 24 hours default
        
        return {
            "remaining": remaining,
            "limit": daily_limit,
            "used": current_count,
            "reset_in_seconds": reset_in_seconds
        }
    
    except Exception as e:
        logger.error(f"Error fetching remaining requests: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch remaining requests")
