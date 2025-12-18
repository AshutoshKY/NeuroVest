"""
Strat Pattern Detection
Based on trading-utils repository pattern detection

The Strat is a price action methodology by Rob Smith
Patterns numbered 1, 2-up, 2-down, 3
"""

import pandas as pd
from typing import Literal, Optional
from pydantic import BaseModel


class StratPattern(BaseModel):
    """Detected Strat pattern"""
    pattern: Literal["1", "2_up", "2_down", "3"]
    description: str
    bias: Literal["bullish", "bearish", "neutral"]


def detect_strat_pattern(df: pd.DataFrame) -> Optional[StratPattern]:
    """
    Detect Strat pattern from recent price action
    
    Simplified logic:
    - 1 = Inside bar (current high < prev high AND current low > prev low)
    - 2-up = Bullish outside bar
    - 2-down = Bearish outside bar  
    - 3 = Outside inside combination
    
    Args:
        df: DataFrame with OHLC data
        
    Returns:
        StratPattern or None
    """
    
    if len(df) < 3:
        return None
    
    try:
        # Normalize column names
        df.columns = [col.capitalize() for col in df.columns]
        
        # Get last 3 bars
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        prev2 = df.iloc[-3]
        
        curr_high = curr['High']
        curr_low = curr['Low']
        prev_high = prev['High']
        prev_low = prev['Low']
        
        # Pattern 1: Inside bar
        if curr_high < prev_high and curr_low > prev_low:
            return StratPattern(
                pattern="1",
                description="Inside bar - consolidation",
                bias="neutral"
            )
        
        # Pattern 2-up: Bullish outside bar
        if curr_high > prev_high and curr_low < prev_low:
            if curr['Close'] > curr['Open']:  # Bullish candle
                return StratPattern(
                    pattern="2_up",
                    description="Bullish outside bar - expansion up",
                    bias="bullish"
                )
        
        # Pattern 2-down: Bearish outside bar
        if curr_high > prev_high and curr_low < prev_low:
            if curr['Close'] < curr['Open']:  # Bearish candle
                return StratPattern(
                    pattern="2_down",
                    description="Bearish outside bar - expansion down",
                    bias="bearish"
                )
        
        # Pattern 3: Outside + inside combination (simplified)
        # Check if we have outside bar followed by inside bar
        prev_is_outside = (prev_high > prev2['High'] and prev_low < prev2['Low'])
        curr_is_inside = (curr_high < prev_high and curr_low > prev_low)
        
        if prev_is_outside and curr_is_inside:
            return StratPattern(
                pattern="3",
                description="Outside-inside pattern - potential reversal",
                bias="neutral"
            )
        
        return None
        
    except Exception as e:
        return None
