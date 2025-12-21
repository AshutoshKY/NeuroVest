"""
Signal Engine API Routes
FastAPI endpoints for signal generation
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Literal, List
import logging

from app.signal_engine.service import build_full_signal, quick_signal
from app.price_engine.ranges import calculate_price_ranges
from app.scenario_engine import generate_scenarios
from app.risk_scoring import calculate_risk_score
from app.signal_history import get_signal_history_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/signal", tags=["signals"])


@router.get("/{symbol}")
async def get_signal(
    symbol: str,
    timeframe: Literal["swing", "positional", "intraday"] = Query(default="swing")
):
    """
    Generate deterministic signal for a symbol
    
    Args:
        symbol: Stock symbol (e.g., "RELIANCE.NS", "INFY")
        timeframe: Analysis timeframe
        
    Returns:
        Complete SignalResponse with all indicators and classification
    """
    
    try:
        logger.info(f"API request: Generate signal for {symbol} ({timeframe})")
        
        # Generate signal
        signal = await build_full_signal(symbol, timeframe=timeframe)
        
        # CRITICAL: Store signal in history for future analysis
        try:
            # Calculate additional components needed for storage
            timeframe_days = 7 if timeframe == "swing" else 21
            envelopes = calculate_price_ranges(signal, timeframe_days=timeframe_days)
            scenarios = generate_scenarios(signal, envelopes, risk_score=50, timeframe_days=timeframe_days)
            risk_assessment = calculate_risk_score(signal, signal.market_context)
            
            # Store in signal history
            history_service = get_signal_history_service()
            signal_id = history_service.store_signal(signal, scenarios, risk_assessment.risk_score)
            logger.info(f"✅ Stored signal in history: {signal_id}")
        except Exception as e:
            logger.error(f"⚠️ Failed to store signal in history: {e}")
            # Continue even if storage fails
        
        return {
            "success": True,
            "data": signal.dict()
        }
        
    except ValueError as e:
        logger.error(f"ValueError generating signal for {symbol}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error generating signal for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error generating signal")


@router.post("/batch")
async def get_batch_signals(
    symbols: List[str],
    timeframe: Literal["swing", "positional", "intraday"] = Query(default="swing")
):
    """
    Generate signals for multiple symbols
    
    Useful for watchlist screening
    """
    
    try:
        results = []
        errors = []
        
        for symbol in symbols:
            try:
                # Generate signal
                signal = await build_full_signal(symbol, timeframe=timeframe)
                
                # Store signal in history
                try:
                    timeframe_days = 7 if timeframe == "swing" else 21
                    envelopes = calculate_price_ranges(signal, timeframe_days=timeframe_days)
                    scenarios = generate_scenarios(signal, envelopes, risk_score=50, timeframe_days=timeframe_days)
                    risk_assessment = calculate_risk_score(signal, signal.market_context)
                    
                    history_service = get_signal_history_service()
                    signal_id = history_service.store_signal(signal, scenarios, risk_assessment.risk_score)
                    logger.debug(f"Stored {symbol} signal: {signal_id}")
                except Exception as store_err:
                    logger.warning(f"Failed to store {symbol} signal: {store_err}")
                
                results.append({
                    "symbol": symbol,
                    "signal": signal.dict()
                })
            except Exception as e:
                logger.error(f"Error generating signal for {symbol}: {e}")
                errors.append({
                    "symbol": symbol,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "results": results,
            "errors": errors,
            "total_requested": len(symbols),
            "successful": len(results),
            "failed": len(errors)
        }
        
    except Exception as e:
        logger.error(f"Error in batch signal generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{symbol}/summary")
async def get_signal_summary(symbol: str):
    """
    Get just the signal summary (lighter response)
    
    Returns only: directional_bias, confidence_score, conviction, primary_signal
    """
    
    try:
        signal = await build_full_signal(symbol)
        
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "directional_bias": signal.signal_summary.directional_bias,
                "confidence_score": signal.signal_summary.confidence_score,
                "conviction": signal.signal_summary.conviction,
                "primary_signal": signal.signal_summary.primary_signal,
                "risk_level": signal.signal_summary.risk_level,
                "timestamp": signal.timestamp.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating signal summary for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
