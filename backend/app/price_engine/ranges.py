"""
ATR-based price range calculations
Note: Full implementation is in the COMPLETE_IMPLEMENTATION_PLAN.md
This is a simplified version for Part 1
"""

import math
from typing import Tuple
from app.signal_engine.schemas import SignalResponse
from .schemas import PriceRange, PriceEnvelopes, RangeMetadata


def calculate_price_ranges(signal: SignalResponse, timeframe_days: int = 7) -> PriceEnvelopes:
    """
    Calculate price envelopes using ATR
    
    Simplified implementation - uses ATR multipliers based on volatility regime
    """
    
    base_price = signal.price.last_close
    atr = signal.volatility.atr_14
    atr_percent = signal.volatility.atr_percent
    
    # Get multipliers based on volatility
    if atr_percent < 1.5:
        lower_mult, upper_mult = (1.0, 1.5)
    elif atr_percent < 2.5:
        lower_mult, upper_mult = (1.2, 1.8)
    else:
        lower_mult, upper_mult = (1.5, 2.2)
    
    # Adjust for timeframe
    timeframe_adjustment = math.sqrt(timeframe_days / 5)
    lower_mult *= timeframe_adjustment
    upper_mult *= timeframe_adjustment
    
    # Calculate base envelope
    base_lower = round(base_price - (lower_mult * atr), 2)
    base_upper = round(base_price + (upper_mult * atr), 2)
    
    # Bull case: Above base range
    bull_lower = base_upper
    bull_upper = round(base_upper + (1.5 * atr), 2)
    
    # Bear case: Below base range
    bear_upper = base_lower
    bear_lower = round(base_lower - (1.5 * atr), 2)
    
    # Invalidation
    if signal.signal_summary.directional_bias == "bullish":
        invalidation = round(base_price - (1.5 * atr), 2)
    elif signal.signal_summary.directional_bias == "bearish":
        invalidation = round(base_price + (1.5 * atr), 2)
    else:
        invalidation = round(base_lower * 0.97, 2)
    
    return PriceEnvelopes(
        base_case=PriceRange(lower=base_lower, upper=base_upper),
        bull_case=PriceRange(lower=bull_lower, upper=bull_upper),
        bear_case=PriceRange(lower=bear_lower, upper=bear_upper),
        invalidation_level=invalidation
    )

def get_range_metadata(signal: SignalResponse, envelopes: PriceEnvelopes) -> RangeMetadata:
    """Get metadata about range calculation"""
    
    return RangeMetadata(
        atr_14=signal.volatility.atr_14,
        atr_percent=signal.volatility.atr_percent,
        volatility_regime=signal.volatility.volatility_regime,
        trend_adjustment_applied=True,
        multiplier_used=1.5
    )
