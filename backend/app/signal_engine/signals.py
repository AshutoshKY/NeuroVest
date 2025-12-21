"""
Signal Generation Logic
Deterministic signal classification and confidence scoring
"""

import pandas as pd
import numpy as np
from typing import Tuple
from .indicators import ema, rsi, macd, atr, bollinger_bands, detect_market_structure, find_support_resistance, calculate_pivot_point, analyze_volume
from .schemas import (
    TrendData, MomentumData, MACDData, VolatilityData,
    StructureData, VolumeData, SignalSummary
)


def classify_trend(df: pd.DataFrame) -> TrendData:
    """
    Classify trend based on EMA alignment
    
    Bullish: EMA20 > EMA50 > EMA200
    Bearish: EMA20 < EMA50 < EMA200
    Sideways: Mixed
    
    Strength based on spacing between EMAs
    """
    close_col = 'Close' if 'Close' in df.columns else 'close'
    
    ema_20 = ema(df[close_col], 20).iloc[-1]
    ema_50 = ema(df[close_col], 50).iloc[-1]
    ema_200 = ema(df[close_col], 200).iloc[-1]
    
    # Determine trend state
    if ema_20 > ema_50 > ema_200:
        trend_state = "bullish"
        alignment_score = 1.0
    elif ema_20 < ema_50 < ema_200:
        trend_state = "bearish"
        alignment_score = 1.0
    elif ema_20 > ema_50 and ema_50 < ema_200:
        # Weak bullish (short-term up, long-term down)
        trend_state = "bullish"
        alignment_score = 0.5
    elif ema_20 < ema_50 and ema_50 > ema_200:
        # Weak bearish (short-term down, long-term up)
        trend_state = "bearish"
        alignment_score = 0.5
    else:
        trend_state = "sideways"
        alignment_score = 0.0
    
    # Calculate strength based on EMA spacing
    current_price = df[close_col].iloc[-1]
    
    # Spacing as percentage of price
    spacing_20_50 = abs(ema_20 - ema_50) / current_price
    spacing_50_200 = abs(ema_50 - ema_200) / current_price
    
    avg_spacing = (spacing_20_50 + spacing_50_200) / 2
    
    if avg_spacing > 0.03:  # > 3% spacing
        strength = "strong"
    elif avg_spacing > 0.01:  # > 1% spacing
        strength = "moderate"
    else:
        strength = "weak"
    
    return TrendData(
        ema_20=round(ema_20, 2),
        ema_50=round(ema_50, 2),
        ema_200=round(ema_200, 2),
        trend_state=trend_state,
        strength=strength,
        ema_alignment_score=round(alignment_score, 2)
    )


def classify_momentum(df: pd.DataFrame) -> MomentumData:
    """
    Classify momentum using RSI and MACD
    
    RSI Regimes:
    - < 30: Oversold
    - 30-45: Bearish neutral
    - 45-55: Neutral
    - 55-70: Bullish neutral
    - > 70: Overbought
    """
    close_col = 'Close' if 'Close' in df.columns else 'close'
    
    rsi_val = rsi(df[close_col], 14).iloc[-1]
    
    # Classify RSI regime
    if rsi_val < 30:
        rsi_regime = "oversold"
    elif rsi_val < 45:
        rsi_regime = "bearish_neutral"
    elif rsi_val < 55:
        rsi_regime = "neutral"
    elif rsi_val < 70:
        rsi_regime = "bullish_neutral"
    else:
        rsi_regime = "overbought"
    
    # MACD
    macd_line, signal_line, histogram = macd(df[close_col])
    macd_val = macd_line.iloc[-1]
    signal_val = signal_line.iloc[-1]
    hist_val = histogram.iloc[-1]
    
    macd_state = "positive" if macd_val > 0 else "negative"
    
    return MomentumData(
        rsi_14=round(rsi_val, 2),
        rsi_regime=rsi_regime,
        macd=MACDData(
            value=round(macd_val, 2),
            signal=round(signal_val, 2),
            histogram=round(hist_val, 2),
            state=macd_state
        )
    )


def classify_volatility(df: pd.DataFrame) -> VolatilityData:
    """
    Classify volatility using ATR and Bollinger Bands
    
    Volatility Regimes:
    - Low: ATR < 1.5% of price
    - Normal: 1.5% - 2.5%
    - High: 2.5% - 4%
    - Extreme: > 4%
    """
    close_col = 'Close' if 'Close' in df.columns else 'close'
    
    atr_val = atr(df, 14).iloc[-1]
    current_price = df[close_col].iloc[-1]
    atr_percent = (atr_val / current_price) * 100
    
    # Classify volatility regime
    if atr_percent < 1.5:
        volatility_regime = "low"
    elif atr_percent < 2.5:
        volatility_regime = "normal"
    elif atr_percent < 4.0:
        volatility_regime = "high"
    else:
        volatility_regime = "extreme"
    
    # Bollinger Bands
    upper_band, middle_band, lower_band = bollinger_bands(df[close_col], 20, 2.0)
    bandwidth = ((upper_band.iloc[-1] - lower_band.iloc[-1]) / middle_band.iloc[-1]) * 100
    
    return VolatilityData(
        atr_14=round(atr_val, 2),
        atr_percent=round(atr_percent, 2),
        volatility_regime=volatility_regime,
        bollinger_bandwidth=round(bandwidth, 2)
    )


def classify_structure(df: pd.DataFrame) -> StructureData:
    """
    Classify market structure and find support/resistance
    """
    high_col = 'High' if 'High' in df.columns else 'high'
    low_col = 'Low' if 'Low' in df.columns else 'low'
    
    market_structure = detect_market_structure(df, lookback=20)
    
    # Get recent swing high/low
    recent_df = df.tail(20)
    swing_high = recent_df[high_col].max()
    swing_low = recent_df[low_col].min()
    
    # Find support and resistance
    support_levels, resistance_levels = find_support_resistance(df, num_levels=3)
    
    # Calculate pivot point
    pivot = calculate_pivot_point(df)
    
    return StructureData(
        market_structure=market_structure,
        swing_high=round(swing_high, 2),
        swing_low=round(swing_low, 2),
        support_levels=[round(s, 2) for s in support_levels],
        resistance_levels=[round(r, 2) for r in resistance_levels],
        pivot_point=pivot
    )


def classify_volume(df: pd.DataFrame) -> VolumeData:
    """
    Classify volume patterns
    """
    volume_ratio, confirmation, spike = analyze_volume(df, period=20)
    
    # Determine trend
    volume_col = 'Volume' if 'Volume' in df.columns else 'volume'
    recent_volumes = df[volume_col].tail(5)
    
    if recent_volumes.is_monotonic_increasing:
        volume_trend = "expanding"
    elif recent_volumes.is_monotonic_decreasing:
        volume_trend = "contracting"
    else:
        volume_trend = "stable"
    
    return VolumeData(
        today_vs_20d_avg=volume_ratio,
        volume_trend=volume_trend,
        volume_confirmation=confirmation,
        volume_spike=spike
    )


def calculate_confidence_score(
    trend: TrendData,
    momentum: MomentumData,
    volatility: VolatilityData,
    volume: VolumeData
) -> float:
    """
    Calculate confidence score (0.0 - 1.0)
    
    Weighted components:
    - Trend alignment: 35%
    - Momentum regime: 25%
    - Volume confirmation: 20%
    - Volatility (inverse): 20%
    
    Higher confidence = stronger alignment
    """
    
    # Trend component (0-1)
    trend_score = trend.ema_alignment_score
    if trend.strength == "strong":
        trend_score *= 1.0
    elif trend.strength == "moderate":
        trend_score *= 0.7
    else:  # weak
        trend_score *= 0.4
    
    # Momentum component (0-1)
    # Best: bullish_neutral or bearish_neutral (aligned with trend)
    # Worst: overbought/oversold (extremes)
    if momentum.rsi_regime in ["bullish_neutral", "bearish_neutral"]:
        momentum_score = 1.0
    elif momentum.rsi_regime == "neutral":
        momentum_score = 0.7
    else:  # oversold or overbought
        momentum_score = 0.4
    
    # Volume component (0-1)
    volume_score = 1.0 if volume.volume_confirmation else 0.3
    if volume.volume_spike:
        volume_score = min(volume_score + 0.2, 1.0)
    
    # Volatility component (0-1) - INVERSE (lower volatility = higher confidence)
    if volatility.volatility_regime == "low":
        volatility_score = 1.0
    elif volatility.volatility_regime == "normal":
        volatility_score = 0.7
    elif volatility.volatility_regime == "high":
        volatility_score = 0.4
    else:  # extreme
        volatility_score = 0.2
    
    # Weighted average
    confidence = (
        trend_score * 0.35 +
        momentum_score * 0.25 +
        volume_score * 0.20 +
        volatility_score * 0.20
    )
    
    return round(confidence, 2)


def determine_directional_bias(
    trend: TrendData,
    momentum: MomentumData,
    structure: StructureData
) -> str:
    """
    Determine directional bias based on multiple factors
    
    Returns: "bullish" | "bearish" | "neutral"
    """
    
    bullish_signals = 0
    bearish_signals = 0
    
    # Trend
    if trend.trend_state == "bullish":
        bullish_signals += 2  # Trend is strong signal
    elif trend.trend_state == "bearish":
        bearish_signals += 2
    
    # Momentum
    if momentum.rsi_regime in ["bullish_neutral", "oversold"]:
        bullish_signals += 1
    elif momentum.rsi_regime in ["bearish_neutral", "overbought"]:
        bearish_signals += 1
    
    if momentum.macd.state == "positive":
        bullish_signals += 1
    else:
        bearish_signals += 1
    
    # Structure
    if structure.market_structure == "higher_high":
        bullish_signals += 1
    elif structure.market_structure == "lower_low":
        bearish_signals += 1
    
    # Decide
    if bullish_signals > bearish_signals + 1:
        return "bullish"
    elif bearish_signals > bullish_signals + 1:
        return "bearish"
    else:
        return "neutral"


def identify_primary_signal(
    directional_bias: str,
    trend: TrendData,
    momentum: MomentumData,
    structure: StructureData,
    volume: VolumeData
) -> str:
    """
    Identify the primary reason for the directional bias
    """
    
    reasons = []
    
    # Trend
    if trend.strength == "strong":
        if directional_bias == "bullish" and trend.trend_state == "bullish":
            reasons.append(f"Strong EMA trend (20>{trend.ema_20:.0f} > 50>{trend.ema_50:.0f})")
        elif directional_bias == "bearish" and trend.trend_state == "bearish":
            reasons.append(f"Strong downtrend (EMA alignment)")
    
    # Momentum
    if momentum.rsi_regime == "bullish_neutral":
        reasons.append(f"RSI bullish ({momentum.rsi_14:.0f})")
    elif momentum.rsi_regime == "oversold":
        reasons.append(f"RSI oversold ({momentum.rsi_14:.0f}) - bounce setup")
    
    # Structure
    if structure.market_structure == "higher_high":
        reasons.append("Higher highs pattern")
    elif structure.market_structure == "lower_low":
        reasons.append("Lower lows pattern")
    
    # Volume
    if volume.volume_confirmation:
        reasons.append("Volume confirmation")
    
    # Return top 2 reasons or default
    if reasons:
        return " + ".join(reasons[:2])
    else:
        return "Mixed signals"


def generate_signal_summary(
    trend: TrendData,
    momentum: MomentumData,
    volatility: VolatilityData,
    structure: StructureData,
    volume: VolumeData
) -> SignalSummary:
    """
    Generate complete signal summary
    """
    
    # Determine bias
    directional_bias = determine_directional_bias(trend, momentum, structure)
    
    # Calculate confidence
    confidence_score = calculate_confidence_score(trend, momentum, volatility, volume)
    
    # Determine conviction
    if confidence_score > 0.65:
        conviction = "high"
    elif confidence_score > 0.45:
        conviction = "medium"
    else:
        conviction = "low"
    
    # Identify primary signal
    primary_signal = identify_primary_signal(directional_bias, trend, momentum, structure, volume)
    
    # Determine risk level (simplified - full version in risk_scoring.py)
    if volatility.volatility_regime in ["high", "extreme"] or trend.strength == "weak":
        risk_level = "high"
    elif volatility.volatility_regime == "normal" and trend.strength == "moderate":
        risk_level = "moderate"
    else:
        risk_level = "low"
    
    return SignalSummary(
        directional_bias=directional_bias,
        confidence_score=confidence_score,
        conviction=conviction,
        primary_signal=primary_signal,
        risk_level=risk_level
    )
