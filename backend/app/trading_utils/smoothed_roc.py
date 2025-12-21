"""
Smoothed Rate of Change (ROC)
From trading-utils repository

Smoothed ROC reduces noise in traditional ROC indicator
"""

import pandas as pd
import numpy as np
from typing import Optional


def calculate_smoothed_roc(
    df: pd.DataFrame,
    period: int = 14,
    smooth_period: int = 3
) -> Optional[pd.Series]:
    """
    Calculate Smoothed Rate of Change
    
    Formula:
    1. ROC = ((Close - Close[n]) / Close[n]) * 100
    2. Smoothed ROC = EMA(ROC, smooth_period)
    
    Args:
        df: DataFrame with Close prices
        period: ROC lookback period
        smooth_period: Smoothing period for EMA
        
    Returns:
        Series of smoothed ROC values or None
    """
    
    if len(df) < period + smooth_period:
        return None
    
    try:
        # Normalize column names
        df.columns = [col.capitalize() for col in df.columns]
        
        close = df['Close']
        
        # Calculate ROC
        roc = ((close - close.shift(period)) / close.shift(period)) * 100
        
        # Smooth with EMA
        smooth_roc = roc.ewm(span=smooth_period, adjust=False).mean()
        
        return smooth_roc
        
    except Exception as e:
        return None


def get_roc_signal(smoothed_roc: pd.Series) -> str:
    """
    Get trading signal from smoothed ROC
    
    Returns:
        "bullish", "bearish", or "neutral"
    """
    
    if smoothed_roc is None or len(smoothed_roc) < 2:
        return "neutral"
    
    try:
        current = smoothed_roc.iloc[-1]
        previous = smoothed_roc.iloc[-2]
        
        # Bullish: ROC crossing above 0 or accelerating upward
        if current > 0 and previous <= 0:
            return "bullish"
        
        if current > previous and current > 2:
            return "bullish"
        
        # Bearish: ROC crossing below 0 or accelerating downward
        if current < 0 and previous >= 0:
            return "bearish"
        
        if current < previous and current < -2:
            return "bearish"
        
        return "neutral"
        
    except:
        return "neutral"
