"""
Indicator Calculations
Pure mathematical functions for technical indicators
NO interpretation, NO LLM involvement
"""

import pandas as pd
import numpy as np
from typing import Tuple, List


def ema(series: pd.Series, period: int) -> pd.Series:
    """
    Exponential Moving Average
    
    Args:
        series: Price series (usually Close)
        period: EMA period
        
    Returns:
        EMA series
    """
    return series.ewm(span=period, adjust=False).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Relative Strength Index (Wilder's method)
    
    Args:
        series: Price series
        period: RSI period (default 14)
        
    Returns:
        RSI series (0-100)
    """
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    rsi_values = 100 - (100 / (1 + rs))
    
    return rsi_values


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Average True Range
    
    Args:
        df: DataFrame with High, Low, Close columns (case-insensitive)
        period: ATR period
        
    Returns:
        ATR series
    """
    # Handle both uppercase and lowercase column names
    high_col = 'High' if 'High' in df.columns else 'high'
    low_col = 'Low' if 'Low' in df.columns else 'low'
    close_col = 'Close' if 'Close' in df.columns else 'close'
    
    high_low = df[high_col] - df[low_col]
    high_close = (df[high_col] - df[close_col].shift()).abs()
    low_close = (df[low_col] - df[close_col].shift()).abs()
    
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr_values = tr.ewm(alpha=1/period, adjust=False).mean()
    
    return atr_values


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Moving Average Convergence Divergence
    
    Args:
        series: Price series
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line period
        
    Returns:
        (macd_line, signal_line, histogram)
    """
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Bollinger Bands
    
    Args:
        series: Price series
        period: Moving average period
        std_dev: Standard deviation multiplier
        
    Returns:
        (upper_band, middle_band, lower_band)
    """
    middle_band = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    
    upper_band = middle_band + (std * std_dev)
    lower_band = middle_band - (std * std_dev)
    
    return upper_band, middle_band, lower_band


def detect_market_structure(df: pd.DataFrame, lookback: int = 20) -> str:
    """
    Detect market structure pattern
    
    Args:
        df: DataFrame with High, Low, Close
        lookback: Periods to analyze
        
    Returns:
        "higher_high" | "lower_low" | "range" | "consolidation"
    """
    # Handle column names
    high_col = 'High' if 'High' in df.columns else 'high'
    low_col = 'Low' if 'Low' in df.columns else 'low'
    
    recent_df = df.tail(lookback)
    
    # Find swing highs and lows
    highs = recent_df[high_col].rolling(window=3, center=True).max()
    lows = recent_df[low_col].rolling(window=3, center=True).min()
    
    swing_highs = recent_df[high_col][recent_df[high_col] == highs].dropna()
    swing_lows = recent_df[low_col][recent_df[low_col] == lows].dropna()
    
    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return "consolidation"
    
    # Check if making higher highs
    if swing_highs.iloc[-1] > swing_highs.iloc[-2] and swing_lows.iloc[-1] > swing_lows.iloc[-2]:
        return "higher_high"
    
    # Check if making lower lows
    if swing_highs.iloc[-1] < swing_highs.iloc[-2] and swing_lows.iloc[-1] < swing_lows.iloc[-2]:
        return "lower_low"
    
    # Check volatility for consolidation vs range
    recent_range = recent_df[high_col].max() - recent_df[low_col].min()
    atr_val = atr(recent_df).iloc[-1]
    
    if recent_range < atr_val * 3:
        return "consolidation"
    
    return "range"


def find_support_resistance(df: pd.DataFrame, num_levels: int = 3) -> Tuple[List[float], List[float]]:
    """
    Find support and resistance levels using pivot points
    
    Args:
        df: DataFrame with High, Low, Close
        num_levels: Number of levels to find
        
    Returns:
        (support_levels, resistance_levels)
    """
    # Handle column names
    high_col = 'High' if 'High' in df.columns else 'high'
    low_col = 'Low' if 'Low' in df.columns else 'low'
    close_col = 'Close' if 'Close' in df.columns else 'close'
    
    # Use recent 50 periods
    recent_df = df.tail(50)
    
    # Find local highs and lows
    highs = recent_df[high_col].rolling(window=5, center=True).max()
    lows = recent_df[low_col].rolling(window=5, center=True).min()
    
    resistance_candidates = recent_df[high_col][recent_df[high_col] == highs].dropna().unique()
    support_candidates = recent_df[low_col][recent_df[low_col] == lows].dropna().unique()
    
    # Sort and get top N
    resistance_levels = sorted(resistance_candidates, reverse=True)[:num_levels]
    support_levels = sorted(support_candidates, reverse=True)[:num_levels]
    
    return support_levels, resistance_levels


def calculate_pivot_point(df: pd.DataFrame) -> float:
    """
    Calculate classic pivot point from previous period
    
    Pivot = (High + Low + Close) / 3
    """
    # Handle column names
    high_col = 'High' if 'High' in df.columns else 'high'
    low_col = 'Low' if 'Low' in df.columns else 'low'
    close_col = 'Close' if 'Close' in df.columns else 'close'
    
    prev_high = df[high_col].iloc[-2]
    prev_low = df[low_col].iloc[-2]
    prev_close = df[close_col].iloc[-2]
    
    pivot = (prev_high + prev_low + prev_close) / 3
    return round(pivot, 2)


def analyze_volume(df: pd.DataFrame, period: int = 20) -> Tuple[float, bool, bool]:
    """
    Analyze volume patterns
    
    Args:
        df: DataFrame with Volume and Close
        period: Lookback period for average
        
    Returns:
        (volume_ratio, confirmation, spike)
        - volume_ratio: Today's volume / average volume
        - confirmation: Volume supports price action
        - spike: Volume > 2x average
    """
    # Handle column names
    volume_col = 'Volume' if 'Volume' in df.columns else 'volume'
    close_col = 'Close' if 'Close' in df.columns else 'close'
    
    recent_df = df.tail(period + 1)
    
    avg_volume = recent_df[volume_col].iloc[:-1].mean()
    today_volume = recent_df[volume_col].iloc[-1]
    
    volume_ratio = today_volume / avg_volume if avg_volume > 0 else 1.0
    
    # Check if volume confirms price action
    price_change = recent_df[close_col].iloc[-1] - recent_df[close_col].iloc[-2]
    volume_change = today_volume - recent_df[volume_col].iloc[-2]
    
    # Confirmation: both price and volume moving in same direction
    confirmation = (price_change > 0 and volume_change > 0) or (price_change < 0 and volume_change > 0)
    
    # Spike: volume > 2x average
    spike = bool(volume_ratio > 2.0)
    
    return round(volume_ratio, 2), confirmation, spike
