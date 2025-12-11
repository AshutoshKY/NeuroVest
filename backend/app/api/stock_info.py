"""
Stock Info Endpoint with Redis Caching

GET /stocks/info/{ticker}
Returns comprehensive stock information with 1-hour Redis caching
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import logging
import json
from datetime import datetime

# Import Redis client
try:
    from app.core.redis_client import get_redis_client
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter(tags=["stocks"])

# Cache TTL - 1 hour
CACHE_TTL = 3600  # seconds


class StockInfo(BaseModel):
    """Stock information response schema"""
    ticker: str
    name: str
    current_price: float
    currency: str
    day_change: float
    day_change_percent: float
    day_high: float
    day_low: float
    volume: int
    market_cap: float
    pe_ratio: Optional[float] = None
    trailing_pe: Optional[float] = None
    dividend_yield: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    average_volume: Optional[int] = None
    market_status: str
    timestamp: str


@router.get("/stocks/info/{ticker}", response_model=StockInfo)
async def get_stock_info(ticker: str):
    """
    Get comprehensive stock information with Redis caching
    
    Args:
        ticker: Stock ticker symbol (e.g., TCS.NS, HAL.NS, RELIANCE.NS)
        
    Returns:
        StockInfo: Comprehensive stock data including price, metrics, and ratios
        
    Cache:
        Redis cache with 1-hour TTL to reduce API calls
    """
    try:
        # Check Redis cache first
        cache_key = f"stock_info:{ticker}"
        redis = None
        
        if REDIS_AVAILABLE:
            redis = get_redis_client()
            if redis:
                try:
                    cached_data = redis.get(cache_key)
                    if cached_data:
                        logger.info(f"[CACHE HIT] Stock info for {ticker}")
                        data = json.loads(cached_data)
                        return JSONResponse(content=data)
                except Exception as e:
                    logger.warning(f"Redis cache read failed: {e}")
        
        # Cache miss or Redis unavailable - fetch from Yahoo Finance
        logger.info(f"[CACHE MISS] Fetching stock info for {ticker}")
        
        import yfinance as yf
        
        # Fetch stock data
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info or 'currentPrice' not in info:
            raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
        
        # Extract and structure data
        current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
        previous_close = info.get('previousClose', current_price)
        
        stock_data = {
            "ticker": ticker,
            "name": info.get('longName') or info.get('shortName', ticker),
            "current_price": current_price,
            "currency": info.get('currency', 'INR'),
            "day_change": current_price - previous_close,
            "day_change_percent": ((current_price - previous_close) / previous_close * 100) if previous_close > 0 else 0,
            "day_high": info.get('dayHigh') or info.get('regularMarketDayHigh', current_price),
            "day_low": info.get('dayLow') or info.get('regularMarketDayLow', current_price),
            "volume": info.get('volume') or info.get('regularMarketVolume', 0),
            "market_cap": info.get('marketCap', 0),
            "pe_ratio": info.get('trailingPE'),
            "trailing_pe": info.get('trailingPE'),
            "dividend_yield": info.get('dividendYield'),
            "week_52_high": info.get('fiftyTwoWeekHigh'),
            "week_52_low": info.get('fiftyTwoWeekLow'),
            "average_volume": info.get('averageVolume'),
            "market_status": "OPEN" if info.get('marketState') == 'REGULAR' else "CLOSED",
            "timestamp": datetime.now().isoformat()
        }
        
        # Cache the result in Redis (1 hour TTL)
        if redis:
            try:
                redis.setex(
                    cache_key,
                    CACHE_TTL,
                    json.dumps(stock_data)
                )
                logger.info(f"[CACHE SET] Stock info for {ticker} cached for {CACHE_TTL}s")
            except Exception as e:
                logger.warning(f"Redis cache write failed: {e}")
        
        return stock_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch stock info for {ticker}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch stock information: {str(e)}"
        )
