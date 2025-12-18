"""
Test Endpoint - No Auth Required
For testing hybrid integration
"""

from fastapi import APIRouter
from app.services.rag import RAGService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test", tags=["testing"])

@router.get("/analysis/{query}")
async def test_analysis_no_auth(query: str):
    """
    Test analysis endpoint WITHOUT authentication
    For testing hybrid integration only
    
    This bypasses all auth/tracking middleware
    """
    logger.info(f"🧪 TEST ENDPOINT: Analysis request for {query} (NO AUTH)")
    
    try:
        rag_service = RAGService()
        
        # Pass ticker as-is - NO suffix additions
        # User explicitly requested NO .NS handling
        ticker = query  # "RELIANCE" → ticker="RELIANCE" (not "RELIANCE.NS")
        query_text = f"Latest analysis for {query}"
        
        logger.info(f"🔍 Extracted: query='{query_text}', ticker='{ticker}'")
        
        # Generate analysis (async generator)
        result = None
        event_count = 0
        # RAG expects (query_text, ticker) not just (query)
        async for event in rag_service.generate_analysis_with_steps(query_text, ticker=ticker):
            event_type, data = event
            event_count += 1
            logger.debug(f"[TEST_EVENT] Event {event_count}: type={event_type}, has_data={bool(data)}")
            if event_type == "final":  # FIXED: Generator yields 'final' not 'complete'
                result = data
                logger.info(f"[TEST_COMPLETE] Got final event with result: {bool(result)}")
                break
        
        logger.info(f"[TEST_AFTER_LOOP] Total events: {event_count}, result: {bool(result)}")
        
        if result:
            logger.info(f"✅ TEST ENDPOINT: Analysis complete for {query}")
            return {
                "success": True,
                "query": query,
                "ticker": ticker,
                "data": result,
                "test_mode": True,
                "note": "This endpoint bypasses authentication for testing only"
            }
        else:
            logger.error(f"❌ TEST ENDPOINT: No result for {query}")
            return {
                "success": False,
                "error": "No result generated",
                "query": query
            }
            
    except Exception as e:
        logger.error(f"❌ TEST ENDPOINT: Error for {query}: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "query": query
        }


@router.get("/signal/{symbol}")
async def test_signal_no_auth(symbol: str, timeframe: str = "swing"):
    """
    Test signal endpoint WITHOUT authentication
    For testing signal generation
    """
    logger.info(f"🧪 TEST ENDPOINT: Signal request for {symbol} {timeframe} (NO AUTH)")
    
    try:
        from app.signal_engine.service import build_full_signal
        
        signal = await build_full_signal(symbol, timeframe=timeframe)
        
        logger.info(f"✅ TEST ENDPOINT: Signal generated for {symbol}")
        
        return {
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe,
            "signal": signal.dict() if hasattr(signal, 'dict') else signal.model_dump(),
            "test_mode": True
        }
        
    except Exception as e:
        logger.error(f"❌ TEST ENDPOINT: Signal error for {symbol}: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "symbol": symbol
        }
