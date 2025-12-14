from fastapi import APIRouter, HTTPException, Query, Depends, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.data_ingestion import data_ingestion_service
from app.services.rag import rag_service
from app.middleware.auth_middleware import get_optional_user
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(tags=["stocks"])

# Track active analyses per user to prevent concurrent requests (saves OpenAI costs)
active_analyses: Dict[int, Dict[str, Any]] = {}  # {user_id: {"ticker": str, "task": asyncio.Task}}


class StockData(BaseModel):
    """Stock data response schema."""
    ticker: str
    exchange: str
    current_price: float
    previous_close: float
    day_high: float
    day_low: float
    volume: int
    currency: Optional[str] = "INR"
    timestamp: str


class StockAnalysis(BaseModel):
    """Stock analysis response schema."""
    ticker: str
    analysis: str
    reasoning: str
    prediction: Optional[str] = "No prediction available."
    risk_factors: List[str]
    sentiment: Dict[str, Any]
    references: List[Dict[str, str]]
    key_insights: List[str]
    disclaimer: str
    current_price: Optional[float] = 0.0
    currency: Optional[str] = "INR"
    previous_close: Optional[float] = 0.0
    day_high: Optional[float] = 0.0
    day_low: Optional[float] = 0.0
    volume: Optional[int] = 0
    historical_data: Optional[Dict[str, Any]] = {}
    
    # NEW: Structured data fields
    analysis_structured: Optional[Dict[str, Any]] = None
    prediction_structured: Optional[Dict[str, Any]] = None


import json
from pathlib import Path

# Load stocks data
STOCKS_FILE = Path(__file__).parent.parent.parent / "data" / "stocks.json"
try:
    with open(STOCKS_FILE, "r") as f:
        ALL_STOCKS = json.load(f)
        logger.info(f"✅ Loaded {len(ALL_STOCKS)} stocks from stocks.json", extra={
            "operation": "load_stocks",
            "count": len(ALL_STOCKS),
            "status": "success"
        })
except Exception as e:
    logger.error("❌ Error loading stocks.json", extra={
        "operation": "load_stocks",
        "status": "failure",
        "error": str(e)
    })
    ALL_STOCKS = []

@router.get("/search")
async def search_stocks(
    q: str = Query(..., description="Search query for stock ticker or name"),
    country: str = Query("All", description="Country filter (India, United States, All)")
):
    """
    Search for stocks by ticker or name with optional country filter.
    
    Args:
        q: Search query (ticker symbol or name)
        country: Country filter (e.g., "India", "United States", "All")
        
    Returns:
        List of matching stocks
    """
    if not q:
        return {"results": []}
        
    try:
        logger.info(f"🔍 Searching stocks", extra={
            "operation": "search_stocks",
            "query": q,
            "country": country
        })
        
        # Dynamic Search via API (Alpha Vantage)
        from app.services.stock_api_service import stock_api_service
        results = await stock_api_service.search_symbol(q, country)
        
        # Fallback to local list if API fails or returns nothing
        if not results:
            logger.info("API search returned no results, using local fallback", extra={
                "operation": "search_stocks",
                "query": q,
                "fallback": "local"
            })
            query_upper = q.upper()
            for stock in ALL_STOCKS:
                if query_upper in stock["ticker"] or query_upper in stock["name"].upper():
                    results.append({
                        "ticker": stock["ticker"],
                        "name": stock["name"],
                        "exchange": "NSE",
                        "sector": "Unknown"
                    })
                    if len(results) >= 10:
                        break
        
        logger.info(f"✅ Search complete", extra={
            "operation": "search_stocks",
            "query": q,
            "results_count": len(results),
            "status": "success"
        })
        return {"results": results}
        
    except Exception as e:
        logger.error("❌ Stock search failed", extra={
            "operation": "search_stocks",
            "query": q,
            "status": "failure",
            "error": str(e)
        })
        return {"results": []}


@router.get("/info/{ticker}")
async def get_stock_info(ticker: str):
    """
    Get comprehensive stock information with Redis caching (1-hour TTL)
    Uses multi-API fallback: Yahoo Finance → Alpha Vantage → Finnhub → Marketstack
    
    Args:
        ticker: Stock ticker symbol (e.g., TCS.NS, HAL.NS, RELIANCE.NS)
        
    Returns:
        Comprehensive stock data including:
        - Current price, day change (% and absolute)
        - Day high/low, volume
        - Market cap, P/E ratio
        - 52-week high/low
        - Market status
        
    Cache:
        Redis cache with 1-hour (3600s) TTL to reduce API calls
        and improve performance for multiple users
    """
    try:
        # Check Redis cache first (1-hour TTL)
        cache_key = f"stock_info:{ticker}"
        
        from app.core.redis_client import get_redis
        redis = get_redis()
        
        if redis:
            try:
                cached_data = redis.get(cache_key)
                if cached_data:
                    import json
                    logger.info(f"[CACHE HIT] Stock info for {ticker}", extra={
                        "operation": "get_stock_info",
                        "ticker": ticker,
                        "cache": "hit"
                    })
                    return json.loads(cached_data)
            except Exception as e:
                logger.warning(f"[CACHE] Redis read failed: {e}", extra={
                    "operation": "get_stock_info",
                    "ticker": ticker,
                    "cache": "error"
                })
        
        # Cache miss - fetch using StockAPIService with fallback
        logger.info(f"[CACHE MISS] Fetching stock info for {ticker}", extra={
            "operation": "get_stock_info",
            "ticker": ticker,
            "cache": "miss"
        })
        
        from app.services.stock_api_service import stock_api_service
        import yfinance as yf
        from datetime import datetime
        
        # Strip .NS or .BO suffix for API service (it adds it back)
        clean_ticker = ticker.replace('.NS', '').replace('.BO', '')
        
        # Try stock API service first (has Alpha Vantage, Finnhub, etc.)
        stock_data = None
        try:
            api_data = await stock_api_service.get_stock_data(clean_ticker)
            if api_data and api_data.get('current_price', 0) > 0:
                logger.info(f"✅ StockAPIService succeeded for {ticker}")
                
                # Calculate day change
                current_price = api_data.get('current_price', 0)
                previous_close = api_data.get('previous_close', current_price)
                
                stock_data = {
                    "ticker": ticker,
                    "name": clean_ticker,  # Will try to get name from yfinance below
                    "current_price": float(current_price),
                    "currency": api_data.get('currency', 'INR'),
                    "day_change": float(current_price - previous_close),
                    "day_change_percent": float(((current_price - previous_close) / previous_close * 100)) if previous_close > 0 else 0.0,
                    "day_high": float(api_data.get('day_high', current_price)),
                    "day_low": float(api_data.get('day_low', current_price)),
                    "volume": int(api_data.get('volume', 0)),
                    "market_cap": 0.0,  # Will try to get from yfinance
                    "pe_ratio": None,  # Will try to get from yfinance
                    "trailing_pe": None,
                    "dividend_yield": None,
                    "week_52_high": None,
                    "week_52_low": None,
                    "average_volume": int(api_data.get('volume', 0)),
                    "market_status": "OPEN",
                    "timestamp": datetime.now().isoformat(),
                    "provider": api_data.get('provider', 'Multi-API')
                }
        except Exception as e:
            logger.warning(f"StockAPIService failed for {ticker}: {e}")
        
        # Fallback to yfinance for additional data (name, market cap, PE ratio)
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if info and (stock_data is None or stock_data.get('current_price', 0) == 0):
                # yfinance is primary source
                current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
                previous_close = info.get('previousClose', current_price)
                
                if current_price > 0:
                    logger.info(f"✅ yfinance succeeded for {ticker}")
                    stock_data = {
                        "ticker": ticker,
                        "name": info.get('longName') or info.get('shortName', clean_ticker),
                        "current_price": float(current_price),
                        "currency": info.get('currency', 'INR'),
                        "day_change": float(current_price - previous_close),
                        "day_change_percent": float(((current_price - previous_close) / previous_close * 100)) if previous_close > 0 else 0.0,
                        "day_high": float(info.get('dayHigh') or info.get('regularMarketDayHigh', current_price)),
                        "day_low": float(info.get('dayLow') or info.get('regularMarketDayLow', current_price)),
                        "volume": int(info.get('volume') or info.get('regularMarketVolume', 0)),
                        "market_cap": float(info.get('marketCap', 0)),
                        "pe_ratio": float(info.get('trailingPE')) if info.get('trailingPE') else None,
                        "trailing_pe": float(info.get('trailingPE')) if info.get('trailingPE') else None,
                        "dividend_yield": float(info.get('dividendYield')) if info.get('dividendYield') else None,
                        "week_52_high": float(info.get('fiftyTwoWeekHigh')) if info.get('fiftyTwoWeekHigh') else None,
                        "week_52_low": float(info.get('fiftyTwoWeekLow')) if info.get('fiftyTwoWeekLow') else None,
                        "average_volume": int(info.get('averageVolume', 0)),
                        "market_status": "OPEN" if info.get('marketState') == 'REGULAR' else "CLOSED",
                        "timestamp": datetime.now().isoformat(),
                        "provider": "Yahoo Finance"
                    }
            elif stock_data and info:
                # Enrich existing data with yfinance info
                stock_data["name"] = info.get('longName') or info.get('shortName', stock_data.get('name', clean_ticker))
                stock_data["market_cap"] = float(info.get('marketCap', 0))
                stock_data["pe_ratio"] = float(info.get('trailingPE')) if info.get('trailingPE') else None
                stock_data["trailing_pe"] = float(info.get('trailingPE')) if info.get('trailingPE') else None
                stock_data["week_52_high"] = float(info.get('fiftyTwoWeekHigh')) if info.get('fiftyTwoWeekHigh') else None
                stock_data["week_52_low"] = float(info.get('fiftyTwoWeekLow')) if info.get('fiftyTwoWeekLow') else None
                stock_data["market_status"] = "OPEN" if info.get('marketState') == 'REGULAR' else "CLOSED"
        except Exception as e:
            logger.warning(f"yfinance enrichment failed for {ticker}: {e}")
        
        # If all methods failed
        if not stock_data or stock_data.get('current_price', 0) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Stock {ticker} not found or all APIs failed. Try again later."
            )
        
        # Cache for 1 hour (3600 seconds)
        if redis:
            try:
                import json
                redis.setex(
                    cache_key,
                    3600,  # 1 hour TTL
                    json.dumps(stock_data)
                )
                logger.info(f"[CACHE SET] Stock info for {ticker} cached for 1 hour", extra={
                    "operation": "get_stock_info",
                    "ticker": ticker,
                    "cache": "set",
                    "ttl": 3600,
                    "provider": stock_data.get('provider', 'unknown')
                })
            except Exception as e:
                logger.warning(f"[CACHE] Redis write failed: {e}", extra={
                    "operation": "get_stock_info",
                    "ticker": ticker,
                    "cache": "write_error"
                })
        
        return stock_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Failed to fetch stock info for {ticker}: {str(e)}", extra={
            "operation": "get_stock_info",
            "ticker": ticker,
            "status": "error",
            "error": str(e)
        })
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch stock information: {str(e)}"
        )

@router.post("/watchlist-data")
async def get_bulk_watchlist_data(request: Request):
    """
    BULK ENDPOINT: Fetch real-time data for multiple stocks in a single request
    
    POST Body: {"tickers": ["TCS", "HAL", "RELIANCE"]}
    
    Returns: {stocks: [...], cached_count: 2, fetched_count: 1, failed: [], total_time_ms: 245.3}
    
    Features:
        - Parallel fetching for all stocks
        - Redis caching (1-hour TTL per ticker)
        - Multi-API fallback (Yahoo→AlphaVantage→Finnhub)
        - Graceful partial failures
    """
    import time
    import json
    from datetime import datetime
    
    start_time = time.time()
    
    try:
        body = await request.json()
        tickers = body.get('tickers', [])
        
        if not tickers:
            raise HTTPException(status_code=400, detail="No tickers provided")
        
        logger.info(f"[BULK] Fetching data for {len(tickers)} stocks")
        
        from app.core.redis_client import get_redis
        from app.services.stock_api_service import stock_api_service
        import yfinance as yf
        
        redis = get_redis()
        cached_count = 0
        fetched_count = 0
        failed_tickers = []
        results = []
        
        async def fetch_stock_data(ticker: str) -> Optional[Dict]:
            nonlocal cached_count, fetched_count
            
            ticker_with_exchange = ticker if '.' in ticker else f"{ticker}.NS"
            cache_key = f"stock_info:{ticker_with_exchange}"
            
            # Check Redis cache
            if redis:
                try:
                    cached = redis.get(cache_key)
                    if cached:
                        cached_count += 1
                        return json.loads(cached)
                except Exception:
                    pass
            
            fetched_count += 1
            clean_ticker = ticker.replace('.NS', '').replace('.BO', '')
            stock_data = None
            
            # Try StockAPIService
            try:
                api_data = await stock_api_service.get_stock_data(clean_ticker)
                if api_data and api_data.get('current_price', 0) > 0:
                    current_price = api_data.get('current_price', 0)
                    previous_close = api_data.get('previous_close', current_price)
                    
                    stock_data = {
                        "ticker": ticker,
                        "name": clean_ticker,
                        "current_price": float(current_price),
                        "currency": api_data.get('currency', 'INR'),
                        "day_change": float(current_price - previous_close),
                        "day_change_percent": float(((current_price - previous_close) / previous_close * 100)) if previous_close > 0 else 0.0,
                        "day_high": float(api_data.get('day_high', current_price)),
                        "day_low": float(api_data.get('day_low', current_price)),
                        "volume": int(api_data.get('volume', 0)),
                        "market_cap": 0.0,
                        "pe_ratio": None,
                        "exchange": api_data.get('exchange', 'NSE'),
                        "market_status": "OPEN",
                        "provider": api_data.get('provider', 'Multi-API'),
                        "timestamp": datetime.now().isoformat()
                    }
            except Exception:
                pass
            
            # Fallback to yfinance
            try:
                stock = yf.Ticker(ticker_with_exchange)
                info = stock.info
                
                if info and (stock_data is None or stock_data.get('current_price', 0) == 0):
                    current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
                    previous_close = info.get('previousClose', current_price)
                    
                    if current_price > 0:
                        stock_data = {
                            "ticker": ticker,
                            "name": info.get('longName') or info.get('shortName', clean_ticker),
                            "current_price": float(current_price),
                            "currency": info.get('currency', 'INR'),
                            "day_change": float(current_price - previous_close),
                            "day_change_percent": float(((current_price - previous_close) / previous_close * 100)) if previous_close > 0 else 0.0,
                            "day_high": float(info.get('dayHigh') or info.get('regularMarketDayHigh', current_price)),
                            "day_low": float(info.get('dayLow') or info.get('regularMarketDayLow', current_price)),
                            "volume": int(info.get('volume') or info.get('regularMarketVolume', 0)),
                            "market_cap": float(info.get('marketCap', 0)),
                            "pe_ratio": float(info.get('trailingPE')) if info.get('trailingPE') else None,
                            "exchange": "NSE" if ".NS" in ticker_with_exchange else "BSE",
                            "market_status": "OPEN" if info.get('marketState') == 'REGULAR' else "CLOSED",
                            "provider": "Yahoo Finance",
                            "timestamp": datetime.now().isoformat()
                        }
                elif stock_data and info:
                    stock_data["name"] = info.get('longName') or info.get('shortName', stock_data.get('name', clean_ticker))
                    stock_data["market_cap"] = float(info.get('marketCap', 0))
                    stock_data["pe_ratio"] = float(info.get('trailingPE')) if info.get('trailingPE') else None
            except Exception:
                pass
            
            # Cache the result
            if stock_data and redis:
                try:
                    redis.setex(cache_key, 3600, json.dumps(stock_data))
                except Exception:
                    pass
            
            return stock_data
        
        # Fetch all in parallel
        tasks = [fetch_stock_data(ticker) for ticker in tickers]
        stock_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(stock_results):
            if isinstance(result, Exception) or not result:
                failed_tickers.append(tickers[i])
            elif result:
                results.append(result)
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        logger.info(f"[BULK] {len(results)}/{len(tickers)} stocks, {cached_count} cached, {fetched_count} fetched in {elapsed_ms:.0f}ms")
        
        return {
           "stocks": results,
            "cached_count": cached_count,
            "fetched_count": fetched_count,
            "failed": failed_tickers,
            "total_time_ms": round(elapsed_ms, 2)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BULK] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Bulk fetch failed: {str(e)}")






@router.get("/{ticker}/data", response_model=StockData)
async def get_stock_data(ticker: str, provider: Optional[str] = Query(None, description="Specific provider to use (e.g., 'Finnhub', 'Alpha Vantage')")):
    """
    Get real-time stock data for a ticker.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'HAL', 'BEL')
        provider: Optional specific provider to query
        
    Returns:
        Real-time stock data
    """
    try:
        from app.services.stock_api_service import stock_api_service
        
        if provider:
            # Test specific provider
            try:
                stock_data = await stock_api_service.get_stock_data_from_provider(ticker, provider)
            except Exception as provider_error:
                # Return informative error instead of 500
                raise HTTPException(
                    status_code=404,
                    detail=f"{provider} failed for {ticker}: {str(provider_error)}"
                )
        else:
            # Use priority-based fallback
            stock_data = await data_ingestion_service.fetch_stock_data(ticker)
        
        if not stock_data:
            raise HTTPException(
                status_code=404,
                detail=f"Stock data not found for ticker: {ticker}"
            )
        
        return stock_data
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching stock data: {str(e)}"
        )


@router.get("/{ticker}/analysis", response_model=StockAnalysis)
async def get_stock_analysis(
    ticker: str,
    request: Request,
    current_user: Optional[Any] = Depends(get_optional_user)
):
    """
    Get AI-powered analysis and predictions for a stock.
    
    **Rate Limits:**
    - 5 analyses per day per IP/device
    - 5 analyses per day per authenticated user
    
    **Request Cancellation:**
    - If user starts new analysis while previous is running, previous is cancelled
    - Prevents wasting OpenAI tokens on abandoned analyses
    
    Args:
        ticker: Stock ticker symbol (Indian stocks: RELIANCE, TCS, INFY, etc.)
        
    Returns:
        Comprehensive AI analysis with sentiment and predictions
    """
    from app.services.rate_limiter import get_rate_limiter
    
    # Check rate limits (5 per IP, 5 per user)
    rate_limiter = get_rate_limiter()
    user_id = current_user.id if current_user else None
    
    # Regular rate limiting (applies to all users with IP + Session + User tracking)
    # This enforces 5/day for authenticated users, 5/day for guests (IP-based)
    await rate_limiter.check_analysis_limit(request, user_id)
    
    # CANCEL PREVIOUS ANALYSIS if user starts new one (prevents OpenAI cost waste)
    if user_id and user_id in active_analyses:
        old_analysis = active_analyses[user_id]
        old_ticker = old_analysis["ticker"]
        old_task = old_analysis["task"]
        
        # Cancel the previous task
        if not old_task.done():
            old_task.cancel()
            logger.warning(
                f"[CANCELLED] User {user_id} started new analysis for {ticker}, "
                f"cancelled previous analysis for {old_ticker} (saves OpenAI tokens)"
            )
        
        # Clean up
        del active_analyses[user_id]
    
    # Create analysis task
    async def perform_analysis_task():
        """Wrapper for analysis that can be cancelled"""
        # Fetch real-time stock data first
        stock_data = await data_ingestion_service.fetch_stock_data(ticker)
        
        # Fetch historical data (5 days)
        from app.services.stock_api_service import stock_api_service as api_service
        historical_data = await api_service.get_stock_history(ticker, days=5)
        
        # Generate analysis using RAG
        # Get full company name for better search results
        defense_stocks = {
            "HAL": "Hindustan Aeronautics Limited",
            "BEL": "Bharat Electronics Limited",
            "BDL": "Bharat Dynamics Limited",
            "MDL": "Mazagon Dock Shipbuilders",
            "GRSE": "Garden Reach Shipbuilders",
            "BEML": "BEML Limited",
            "COCHINSHIP": "Cochin Shipyard Limited"
        }
        # Get full company name for better RAG query
        company_name = defense_stocks.get(ticker, ticker)
        
        # Trigger on-demand ingestion to ensure fresh data
        # This makes the system dynamic for ANY stock
        try:
            logger.info(f"📥 Triggering on-demand ingestion", extra={
                "operation": "ingest_for_ticker",
                "ticker": ticker,
                "company_name": company_name
            })
            await data_ingestion_service.ingest_for_ticker(ticker, company_name)
        except Exception as e:
            # Don't fail the request if ingestion fails, just log it
            logger.warning("⚠️ On-demand ingestion failed", extra={
                "operation": "ingest_for_ticker",
                "ticker": ticker,
                "status": "failure",
                "error": str(e)
            })

        # Generate analysis using RAG
        rag_query = f"Analyze the current market sentiment, risks, and growth potential for {company_name} ({ticker}) based on recent news."
        analysis = await rag_service.generate_analysis(rag_query, ticker=ticker)
        
        # Add ticker to response
        analysis["ticker"] = ticker
        analysis["historical_data"] = historical_data
        
        # Fetch multi-period historical data for candlestick charts
        multi_period_data = api_service.get_historical_data_multi_period(ticker)
        
        # Convert DataFrames to JSON-serializable format
        historical_data_multi = {}
        for period, df in multi_period_data.items():
            if df is not None and not df.empty:
                historical_data_multi[period] = {
                    "timestamps": [int(ts.timestamp()) for ts in df.index],
                    "opens": df['Open'].tolist(),
                    "highs": df['High'].tolist(),
                    "lows": df['Low'].tolist(),
                    "closes": df['Close'].tolist(),
                    "volumes": df['Volume'].tolist()
                }
            else:
                historical_data_multi[period] = None
        
        analysis["historical_data_multi"] = historical_data_multi
        
        # Add stock data to analysis
        if stock_data:
            for key, value in stock_data.items():
                if key not in analysis:
                    analysis[key] = value
        
        logger.info(f"✅ Analysis completed for {ticker}")
        
        return analysis
    
    # Create the task and track it
    task = asyncio.create_task(perform_analysis_task())
    if user_id:
        active_analyses[user_id] = {"ticker": ticker, "task": task}
    
    try:
        # Wait for the analysis to complete
        result = await task
        
        # INSERT INTO analysis_history AFTER successful completion
        if user_id and result:
            try:
                from sqlalchemy import text
                from app.core.database import get_db
                
                db = next(get_db())
                
                # Extract sentiment from result
                sentiment_classification = "neutral"
                if "sentiment" in result and isinstance(result["sentiment"], dict):
                    sentiment_classification = result["sentiment"].get("classification", "neutral")
                elif "analysis" in result and isinstance(result.get("analysis"), dict):
                    sentiment_data = result["analysis"].get("sentiment", {})
                    if isinstance(sentiment_data, dict):
                        sentiment_classification = sentiment_data.get("classification", "neutral")
                
                db.execute(
                    text("""
                        INSERT INTO analysis_history 
                        (ticker, user_id, ip_address, sentiment, success, cached, latency_ms, timestamp)
                        VALUES (:ticker, :user_id, :ip, :sentiment, 1, 0, 0, NOW())
                    """),
                    {
                        "ticker": ticker,
                        "user_id": user_id,
                        "ip": request.client.host if request else "unknown",
                        "sentiment": sentiment_classification
                    }
                )
                db.commit()
                logger.info(f"✅ [HISTORY] Inserted: {ticker} (user={user_id}, sentiment={sentiment_classification})")
            except Exception as e:
                logger.error(f"❌ [HISTORY] Failed to insert analysis_history: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        return result
        
    except asyncio.CancelledError:
        # Analysis was cancelled (user started new analysis)
        logger.info(f"[CANCELLED] Analysis for {ticker} was cancelled by user")
        raise HTTPException(
            status_code=499,  # Client Closed Request
            detail=f"Analysis for {ticker} was cancelled (user started new analysis)"
        )
    except Exception as e:
        logger.error(f"❌ Analysis failed for {ticker}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis generation failed: {str(e)}"
        )
    finally:
        # Clean up active analysis tracking
        if user_id and user_id in active_analyses:
            # Only delete if this is still the active task for this user
            if active_analyses[user_id].get("ticker") == ticker:
                del active_analyses[user_id]


@router.get("/{ticker}/analysis-with-steps")
async def get_stock_analysis_with_steps(ticker: str):
    """
    Get AI-powered analysis with progressive thinking steps.
    NOW WITH REDIS CACHE: Checks cache FIRST before any expensive operations!
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Analysis with thinking_steps array showing progress
    """
    try:
        # PRIORITY 1: Check Redis cache FIRST (before any expensive operations!)
        from app.services.redis_cache import redis_cache
        
        cached_analysis = redis_cache.get_analysis(ticker)
        if cached_analysis:
            # INSTANT RESPONSE from cache (<100ms)
            logger.info(f"⚡ API-level cache HIT for {ticker} - returning instantly")
            redis_cache.track_trending(ticker)
            
            # Ensure all required fields are present
            response = {
                **cached_analysis,
                "ticker": ticker,
                "cached": True,
                "cache_hit": True,
                "thinking_steps": cached_analysis.get("thinking_steps", []),
                # These should already be in cached_analysis from when it was stored
                "current_price": cached_analysis.get("current_price", 0.0),
                "currency": cached_analysis.get("currency", "INR"),
                "previous_close": cached_analysis.get("previous_close", 0.0),
                "day_high": cached_analysis.get("day_high", 0.0),
                "day_low": cached_analysis.get("day_low", 0.0),
                "volume": cached_analysis.get("volume", 0),
                "historical_data": cached_analysis.get("historical_data", {}),
                "stock_data": cached_analysis.get("stock_data", {})
            }
            
            return response
        
        # Cache MISS - proceed with full analysis flow
        logger.info(f"❌ Cache MISS for {ticker} - generating fresh analysis")
        
        # Fetch stock data
        stock_data = await data_ingestion_service.fetch_stock_data(ticker)
        
        # Fetch historical data
        from app.services.stock_api_service import stock_api_service as api_service
        historical_data = await api_service.get_stock_history(ticker, days=5)
        
        # Get company name
        defense_stocks = {
            "HAL": "Hindustan Aeronautics Limited",
            "BEL": "Bharat Electronics Limited",
            "LT": "Larsen & Toubro",
            "BDL": "Bharat Dynamics Limited",
            "COCHINSHIP": "Cochin Shipyard Limited"
        }
        company_name = defense_stocks.get(ticker, ticker)
        
        # Trigger on-demand ingestion
        try:
            logger.info(f"📥 Triggering on-demand ingestion", extra={
                "operation": "ingest_for_ticker",
                "ticker": ticker,
                "company_name": company_name
            })
            await data_ingestion_service.ingest_for_ticker(ticker, company_name)
        except Exception as e:
            logger.warning("⚠️ On-demand ingestion failed", extra={
                "operation": "ingest_for_ticker",
                "ticker": ticker,
                "status": "failure",
                "error": str(e)
            })

        # Collect thinking steps
        thinking_steps = []
        final_analysis = None
        
        rag_query = f"Analyze the current market sentiment, risks, and growth potential for {company_name} ({ticker}) based on recent news."
        
        async for step_type, data in rag_service.generate_analysis_with_steps(rag_query, ticker=ticker):
            if step_type == "step":
                thinking_steps.append(data)
            elif step_type == "final":
                final_analysis = data
        
        if not final_analysis:
            raise HTTPException(status_code=500, detail="Analysis generation failed")
        
        # Add ticker and historical data
        final_analysis["ticker"] = ticker
        final_analysis["historical_data"] = historical_data
        final_analysis["thinking_steps"] = thinking_steps
        
        # Merge stock data if available
        if stock_data:
            final_analysis["current_price"] = stock_data.get("current_price", 0.0)
            final_analysis["currency"] = stock_data.get("currency", "INR")
            final_analysis["previous_close"] = stock_data.get("previous_close", 0.0)
            final_analysis["day_high"] = stock_data.get("day_high", 0.0)
            final_analysis["day_low"] = stock_data.get("day_low", 0.0)
            final_analysis["volume"] = stock_data.get("volume", 0)
        
        # CRITICAL: Cache the COMPLETE analysis in Redis (with historical_data, thinking_steps, stock_data)
        try:
            from app.services.redis_cache import redis_cache
            redis_cache.set_analysis(ticker, final_analysis, ttl_seconds=3600)
            logger.info(f"💾 API: Cached complete analysis for {ticker} in Redis")
        except Exception as e:
            logger.error(f"API: Redis cache storage failed: {e}")
        
        return final_analysis
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating analysis: {str(e)}"
        )


@router.get("/{ticker}/analysis-stream")
async def stream_stock_analysis(
    ticker: str,
    request: Request,
    current_user: Optional[Any] = Depends(get_optional_user)
):
    """
    Stream AI-powered analysis with real-time thinking steps via SSE.
    
    **Smart Rate Limiting:**
    - Cached analyses (trending stocks) = FREE (no quota usage)
    - Fresh analyses = Counts against daily limit
    
    **Rate Limits:**
    - Guests: 2 analyses per day (IP + Session based)
    - Authenticated: 5 analyses per day (IP + Session + User based)
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Server-Sent Events stream with progressive thinking steps and final analysis
    """
    from app.services.rate_limiter import get_rate_limiter
    from fastapi.responses import StreamingResponse
    import json
    
    # Extract user_id from authenticated user (via dependency injection)
    user_id = current_user.id if current_user else None
    logger.info(f"[ANALYSIS_REQUEST] ticker={ticker}, user_id={user_id}")
    
    # Don't check rate limit yet - check cache first!
    from app.core.config import settings
    
    
    async def generate_sse():
        """Generate Server-Sent Events for real-time analysis streaming"""
        try:
            # Determine if user is admin
            is_admin = current_user.is_admin if current_user and hasattr(current_user, 'is_admin') else False
            
            # === CRITICAL: CHECK CACHE FIRST (before rate limiting) ===
            # This allows users to access cached analyses for FREE, even when at limit
            from app.services.redis_cache import redis_cache
            from datetime import datetime
            
            cached_analysis = redis_cache.get_analysis(ticker)
            if cached_analysis:
                # CACHE HIT = FREE! No rate limit check needed
                logger.info(f"⚡ SSE cache HIT for {ticker} (FREE - no quota usage, bypasses rate limit)")
                redis_cache.track_trending(ticker)
                
                # Send cached step
                yield f"data: {json.dumps({'type': 'step', 'step': {'description': '⚡ Loaded from cache (FREE)', 'timestamp': datetime.now().isoformat()}})}\n\n"
                
                # Send final cached data
                yield f"data: {json.dumps({'type': 'final', 'analysis': cached_analysis})}\n\n"
                return  # Exit early - no rate limit needed!
            
            # === CACHE MISS - NOW check rate limit (since we'll do actual analysis) ===
            logger.info(f"[CACHE_MISS] {ticker} - checking rate limit before analysis")
            
            from app.rate_limiting import get_rate_limiter
            rate_limiter = get_rate_limiter()
            
            # Check limit WITHOUT incrementing (will raise HTTPException if limit exceeded)
            await rate_limiter.check_and_enforce(
                request=request,
                user_id=user_id,
                is_admin=is_admin,
                limit_type="analysis"
            )

            # Stream start event
            yield f"data: {json.dumps({'type': 'start', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # CACHE MISS - Increment rate limit since we'll do actual analysis
            logger.info(f"[CACHE_MISS] {ticker} - incrementing rate limit for user_id={user_id}")
            
            # Increment rate limit counter (analysis will proceed)
            # The check_and_enforce above already validated we're under limit
            await rate_limiter.increment(
                request=request,
                user_id=user_id,
                is_admin=is_admin,
                limit_type="analysis"
            )
            logger.info(f"[RATE_LIMIT] Incremented analysis count for user_id={user_id or 'guest'}")

            
            # Fetch real-time stock data first
            stock_data = await data_ingestion_service.fetch_stock_data(ticker)
            
            # Fetch historical data (5 days)
            from app.services.stock_api_service import stock_api_service as api_service
            historical_data = await api_service.get_stock_history(ticker, days=5)
            
            # Get full company name for better search results
            defense_stocks = {
                "HAL": "Hindustan Aeronautics Limited",
                "BEL": "Bharat Electronics Limited",
                "BDL": "Bharat Dynamics Limited",
                "MDL": "Mazagon Dock Shipbuilders",
                "GRSE": "Garden Reach Shipbuilders",
                "BEML": "BEML Limited",
                "COCHINSHIP": "Cochin Shipyard Limited",
                "LT": "Larsen & Toubro",
                "ICICIBANK": "ICICI Bank Limited"
            }
            company_name = defense_stocks.get(ticker, ticker)
            
            # Trigger on-demand ingestion to ensure fresh data
            try:
                await data_ingestion_service.ingest_for_ticker(ticker, company_name)
            except Exception as e:
                # Send error as SSE event but don't fail
                error_msg = {"type": "warning", "message": f"On-demand ingestion warning: {str(e)}"}
                yield f"data: {json.dumps(error_msg)}\n\n"
            
            # Generate analysis using RAG with progressive steps
            rag_query = f"Analyze the current market sentiment, risks, and growth potential for {company_name} ({ticker}) based on recent news."
            
            async for step_type, data in rag_service.generate_analysis_with_steps(rag_query, ticker=ticker, stock_data=stock_data):
                if step_type == "step":
                    # Stream thinking step
                    step_event = {"type": "step", "step": data}
                    yield f"data: {json.dumps(step_event)}\n\n"
                    
                elif step_type == "final":
                    # Add ticker and historical data
                    final_analysis = data
                    final_analysis["ticker"] = ticker
                    final_analysis["historical_data"] = historical_data
                    
                    # Fetch multi-period historical data for candlestick charts
                    multi_period_data = api_service.get_historical_data_multi_period(ticker)
                    
                    # Convert DataFrames to JSON-serializable format
                    historical_data_multi = {}
                    for period, df in multi_period_data.items():
                        if df is not None and not df.empty:
                            historical_data_multi[period] = {
                                "timestamps": [int(ts.timestamp()) for ts in df.index],
                                "opens": df['Open'].tolist(),
                                "highs": df['High'].tolist(),
                                "lows": df['Low'].tolist(),
                                "closes": df['Close'].tolist(),
                                "volumes": df['Volume'].tolist()
                            }
                        else:
                            historical_data_multi[period] = None
                    
                    final_analysis["historical_data_multi"] = historical_data_multi
                    
                    # Merge stock data if available
                    if stock_data:
                        final_analysis["current_price"] = stock_data.get("current_price", 0.0)
                        final_analysis["currency"] = stock_data.get("currency", "INR")
                        final_analysis["previous_close"] = stock_data.get("previous_close", 0.0)
                        final_analysis["day_high"] = stock_data.get("day_high", 0.0)
                        final_analysis["day_low"] = stock_data.get("day_low", 0.0)
                        final_analysis["volume"] = stock_data.get("volume", 0)
                    
                    # CRITICAL: Cache the COMPLETE analysis in Redis
                    try:
                        from app.services.redis_cache import redis_cache
                        redis_cache.set_analysis(ticker, final_analysis, ttl_seconds=3600)
                        logger.info(f"💾 SSE: Cached complete analysis for {ticker} in Redis")
                    except Exception as e:
                        logger.error(f"SSE: Redis cache storage failed: {e}")
                    
                    # Stream final analysis
                    final_event = {"type": "final", "analysis": final_analysis}
                    yield f"data: {json.dumps(final_event)}\n\n"
                    # Complete without errors
                    logger.info(f"✅ Analysis COMPLETE for {ticker}")
                    
            # End event
            yield f"data: {json.dumps({'type': 'end'})}\n\n"
                    
        except HTTPException as e:
            # HTTPException (rate limit, etc.) - re-raise to FastAPI
            raise
        except Exception as e:
            # Log error
            logger.error(f"❌ Analysis FAILED for {ticker}: {e}", exc_info=True)
            
            # Send error event
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
            
    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.get("/{ticker}/logs")
def get_stock_logs(ticker: str, limit: int = 10):
    """
    Get recent operation logs for a specific ticker.
    """
    try:
        from app.core.database import get_db
        from app.models.operation_log import OperationLog
        from sqlalchemy import desc
        
        db = next(get_db())
        
        # Filter logs where details contains the ticker
        # This is a simple text search in the JSON details
        logs = db.query(OperationLog).filter(
            OperationLog.details.contains(ticker)
        ).order_by(desc(OperationLog.timestamp)).limit(limit).all()
        
        return {
            "logs": [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "operation": log.operation_type,
                    "source": log.source,
                    "status": log.status,
                    "message": log.error_message or f"Processed {log.chunks_count or 0} chunks"
                }
                for log in logs
            ]
        }
    except Exception as e:
        logger.error("❌ Error fetching stock logs", extra={
            "operation": "get_stock_logs",
            "ticker": ticker,
            "status": "failure",
            "error": str(e)
        })
        return {"logs": []}

@router.get("/{ticker}/history")
async def get_stock_history_analyses(
    ticker: str,
    limit: int = 30
):
    """Get historical analyses for a stock from ChromaDB vector database."""
    try:
        from app.services.rag import rag_service
        
        # Retrieve historical analyses from ChromaDB (get more than needed)
        historical_analyses = rag_service.retrieve_historical_analyses(ticker, top_k=limit + 1)
        
        if not historical_analyses:
            return {
                'ticker': ticker,
                'total_analyses': 0,
                'analyses': []
            }
        
        # Exclude the most recent analysis (which is likely the current run)
        # Only show truly "past" analyses by skipping the first (newest) one
        if len(historical_analyses) > 1:
            historical_analyses = historical_analyses[1:]  # Skip the most recent
        else:
            # If there's only one analysis, return empty (it's the current one)
            return {
                'ticker': ticker,
                'total_analyses': 0,
                'analyses': []
            }
        
        # Parse and format the results
        history_data = []
        for doc in historical_analyses:
            try:
                metadata = doc.get('metadata', {})
                content = doc.get('text', '')
                
                # Extract key information from metadata
                import json
                
                # Parse JSON fields
                risk_factors = []
                key_insights = []
                try:
                    if metadata.get('risk_factors'):
                        risk_factors = json.loads(metadata['risk_factors']) if isinstance(metadata['risk_factors'], str) else metadata['risk_factors']
                    if metadata.get('key_insights'):
                        key_insights = json.loads(metadata['key_insights']) if isinstance(metadata['key_insights'], str) else metadata['key_insights']
                except:
                    pass
                
                history_data.append({
                    'timestamp': metadata.get('timestamp'),
                    'date': metadata.get('date'),
                    'sentiment': metadata.get('sentiment_classification', 'unknown'),
                    'sentiment_score': float(metadata.get('sentiment_score', 0)),
                    'confidence': float(metadata.get('confidence', 0)),
                    'price': float(metadata.get('price', 0)) if metadata.get('price') else None,
                    'previous_close': float(metadata.get('previous_close', 0)) if metadata.get('previous_close') else None,
                    'day_high': float(metadata.get('day_high', 0)) if metadata.get('day_high') else None,
                    'day_low': float(metadata.get('day_low', 0)) if metadata.get('day_low') else None,
                    'volume': int(metadata.get('volume', 0)) if metadata.get('volume') else None,
                    'rsi': float(metadata.get('rsi', 0)) if metadata.get('rsi') else None,
                    'macd_trend': metadata.get('macd_trend', 'N/A'),
                    'bb_position': metadata.get('bb_position', 'N/A'),
                    'prediction_direction': metadata.get('prediction_direction', 'N/A'),
                    'prediction_summary': metadata.get('prediction_summary', ''),
                    'risk_factors': risk_factors,
                    'key_insights': key_insights,
                    'content_preview': content[:200] + '...' if len(content) > 200 else content
                })
            except Exception as e:
                logger.error(f"Error parsing historical analysis: {e}")
                continue
        
        return {
            'ticker': ticker,
            'total_analyses': len(history_data),
            'analyses': history_data
        }
    except Exception as e:
        logger.error(f"Error fetching historical analyses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending")
async def get_trending_stocks(limit: int = 10):
    """
    Get most analyzed stocks from Redis cache.
    Shows which stocks users are analyzing most frequently.
    """
    try:
        from app.services.redis_cache import redis_cache
        
        trending = redis_cache.get_trending_stocks(limit)
        
        return {
            "trending_stocks": [
                {
                    "ticker": ticker,
                    "analysis_count": int(count),
                    "rank": idx + 1
                }
                for idx, (ticker, count) in enumerate(trending)
            ],
            "total": len(trending)
        }
    except Exception as e:
        logger.error(f"Error fetching trending stocks: {e}")
        raise HTTPException(status_code=500, detail=str(e))
