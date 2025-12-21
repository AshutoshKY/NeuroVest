"""
Power of 3 Detection
Based on ICT (Inner Circle Trader) methodology

Power of 3 refers to the 3 phases of market movement:
1. Accumulation
2. Manipulation
3. Distribution
"""

import pandas as pd
from typing import Literal, Optional
from pydantic import BaseModel


class PowerOf3Phase(BaseModel):
    """Current Power of 3 phase"""
    phase: Literal["accumulation", "manipulation", "distribution"]
    description: str
    confidence: float


def detect_power_of_3(df: pd.DataFrame, lookback: int = 20) -> Optional[PowerOf3Phase]:
    """
    Detect current Power of 3 phase
    
    Simplified logic:
    - Accumulation: Low volatility, range-bound
    - Manipulation: Sharp moves outside range (stop hunts)
    - Distribution: Breakout with volume
    
    Args:
        df: DataFrame with OHLC + Volume
        lookback: Periods to analyze
        
    Returns:
        PowerOf3Phase or None
    """
    
    if len(df) < lookback:
        return None
    
    try:
        # Normalize column names
        df.columns = [col.capitalize() for col in df.columns]
        
        recent = df.tail(lookback)
        
        # Calculate range statistics
        high_low_range = recent['High'].max() - recent['Low'].min()
        avg_close = recent['Close'].mean()
        range_percent = (high_low_range / avg_close) * 100
        
        # Calculate volatility (simplified)
        closes = recent['Close']
        volatility = closes.std() / closes.mean() * 100
        
        # Volume analysis
        if 'Volume' in recent.columns:
            avg_volume = recent['Volume'].mean()
            recent_volume = recent['Volume'].tail(5).mean()
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
        else:
            volume_ratio = 1.0
        
        # Detect phase
        # Accumulation: Low volatility, tight range
        if volatility < 2.0 and range_percent < 5.0:
            return PowerOf3Phase(
                phase="accumulation",
                description="Low volatility consolidation - smart money accumulating",
                confidence=min(0.8, 1.0 - (volatility / 2.0))
            )
        
        # Manipulation: High volatility, low volume (stop hunts)
        if volatility > 3.0 and volume_ratio < 1.2:
            return PowerOf3Phase(
                phase="manipulation",
                description="Sharp moves without volume - potential manipulation/stop hunt",
                confidence=min(0.7, volatility / 5.0)
            )
        
        # Distribution: Breakout with volume
        if volatility > 2.5 and volume_ratio > 1.5:
            return PowerOf3Phase(
                phase="distribution",
                description="High volatility with volume - distribution phase",
                confidence=min(0.8, (volume_ratio - 1.0) / 2.0)
            )
        
        # Default to accumulation if unclear
        return PowerOf3Phase(
            phase="accumulation",
            description="Unclear phase - defaulting to accumulation",
            confidence=0.5
        )
        
    except Exception as e:
        return None
