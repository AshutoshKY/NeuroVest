"""
Signal Engine Service
Orchestration layer that integrates with existing NeuroVest services
"""

import pandas as pd
import logging
from datetime import datetime
from typing import Optional

from app.services.stock_api_service import stock_api_service
from .schemas import (
    SignalResponse, PriceContext, TrendData, MomentumData,
    VolatilityData, StructureData, VolumeData, RelativeStrengthData,
    MarketContext, SignalSummary
)
from .signals import (
    classify_trend, classify_momentum, classify_volatility,
    classify_structure, classify_volume, generate_signal_summary
)

logger = logging.getLogger(__name__)


async def fetch_market_context() -> MarketContext:
    """
    Fetch market context (NIFTY, VIX)
    Integrates with existing stock_api_service
    """
    
    try:
        # Fetch NIFTY data (stock_api_service.get_historical_data is SYNC, not async)
        nifty_df = stock_api_service.get_historical_data("^NSEI", period="1mo", interval="1d")
        
        if nifty_df is not None and len(nifty_df) > 0:
            close_col = 'Close' if 'Close' in nifty_df.columns else 'close'
            nifty_close = nifty_df[close_col].iloc[-1]
            
            # Simple trend classification for NIFTY
            if len(nifty_df) >= 50:
                from .indicators import ema
                ema_20 = ema(nifty_df[close_col], 20).iloc[-1]
                ema_50 = ema(nifty_df[close_col], 50).iloc[-1]
                
                if nifty_close > ema_20 > ema_50:
                    nifty_trend = "bullish"
                elif nifty_close < ema_20 < ema_50:
                    nifty_trend = "bearish"
                else:
                    nifty_trend = "sideways"
            else:
                nifty_trend = "sideways"
        else:
            logger.warning("Could not fetch NIFTY data, using defaults")
            nifty_close = 22000.0
            nifty_trend = "sideways"
        
        # Fetch VIX data
        # Note: India VIX symbol might vary by provider
        try:
            vix_df = stock_api_service.get_historical_data("^INDIAVIX", period="5d", interval="1d")
            if vix_df is not None and len(vix_df) > 0:
                close_col = 'Close' if 'Close' in vix_df.columns else 'close'
                india_vix = vix_df[close_col].iloc[-1]
            else:
                # Fallback: default VIX
                india_vix = 15.0
        except:
            logger.warning("Could not fetch VIX data, using default")
            india_vix = 15.0
        
        # Classify VIX regime
        if india_vix < 12:
            vix_regime = "complacent"
        elif india_vix < 18:
            vix_regime = "normal"
        elif india_vix < 25:
            vix_regime = "elevated"
        else:
            vix_regime = "panic"
        
        # Determine macro bias
        if vix_regime in ["complacent", "normal"] and nifty_trend == "bullish":
            macro_bias = "risk_on"
        elif vix_regime in ["elevated", "panic"] or nifty_trend == "bearish":
            macro_bias = "risk_off"
        else:
            macro_bias = "neutral"
        
        return MarketContext(
            nifty_trend=nifty_trend,
            nifty_close=round(nifty_close, 2),
            india_vix=round(india_vix, 2),
            vix_regime=vix_regime,
            macro_bias=macro_bias
        )
        
    except Exception as e:
        logger.error(f"Error fetching market context: {e}")
        # Return defaults on error
        return MarketContext(
            nifty_trend="sideways",
            nifty_close=22000.0,
            india_vix=15.0,
            vix_regime="normal",
            macro_bias="neutral"
        )


async def build_full_signal(
    symbol: str,
    df: Optional[pd.DataFrame] = None,
    timeframe: str = "swing"
) -> SignalResponse:
    """
    Build complete signal for a symbol
    
    Args:
        symbol: Stock symbol (e.g., "RELIANCE.NS", "INFY")
        df: Optional pre-fetched DataFrame (if None, will fetch)
        timeframe: "swing" | "positional" | "intraday"
        
    Returns:
        Complete SignalResponse
    """
    
    logger.info(f"Building signal for {symbol} ({timeframe})")
    
    # Fetch data if not provided
    if df is None:
        # Determine period based on timeframe
        if timeframe == "swing":
            period = "3mo"  # Need enough for EMA 200
            interval = "1d"
        elif timeframe == "positional":
            period = "1y"
            interval = "1wk"
        else:  # intraday
            period = "5d"
            interval = "15m"
        
        # Fetch data using SYNC method (get_historical_data is not async)
        df = stock_api_service.get_historical_data(symbol, period=period, interval=interval)
        
        if df is None or len(df) < 50:
            raise ValueError(f"Insufficient data for {symbol}")
    
    # Handle column names (normalize to Title Case for consistency)
    df = df.rename(columns=lambda x: x.capitalize())
    
    # Ensure DataFrame has the required OHLCV columns
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Extract price context
    current_close = df['Close'].iloc[-1]
    prev_close = df['Close'].iloc[-2] if len(df) > 1 else current_close
    gap_percent = ((current_close - prev_close) / prev_close) * 100 if prev_close != 0 else 0
    
    price_context = PriceContext(
        last_close=round(current_close, 2),
        prev_close=round(prev_close, 2),
        gap_percent=round(gap_percent, 2),
        high=round(df['High'].iloc[-1], 2),
        low=round(df['Low'].iloc[-1], 2),
        open=round(df['Open'].iloc[-1], 2)
    )
    
    # Classify all signal components
    trend = classify_trend(df)
    momentum = classify_momentum(df)
    volatility = classify_volatility(df)
    structure = classify_structure(df)
    volume_data = classify_volume(df)
    
    # Generate signal summary
    signal_summary = generate_signal_summary(trend, momentum, volatility, structure, volume_data)
    
    # Fetch market context
    market_context = await fetch_market_context()
    
    # Relative strength (placeholder - will be implemented in Component 6)
    relative_strength = RelativeStrengthData(
        vs_nifty=1.0,
        vs_sector=1.0,
        sector_symbol="UNKNOWN",
        sector_trend="neutral",
        market_leadership="inline"
    )
    
    # Build complete signal response
    signal = SignalResponse(
        symbol=symbol,
        timeframe=timeframe,
        timestamp=datetime.utcnow(),
        price=price_context,
        trend=trend,
        momentum=momentum,
        volatility=volatility,
        structure=structure,
        volume=volume_data,
        relative_strength=relative_strength,
        market_context=market_context,
        signal_summary=signal_summary
    )
    
    logger.info(f"Signal generated: {symbol} - {signal_summary.directional_bias} (confidence: {signal_summary.confidence_score})")
    
    return signal


# Convenience function for quick signal generation
async def quick_signal(symbol: str) -> dict:
    """
    Generate signal and return as dict (for JSON serialization)
    """
    signal = await build_full_signal(symbol)
    return signal.dict()
