"""
Signal Engine Schemas
Pydantic models for canonical signal output
"""

from pydantic import BaseModel, Field, validator
from typing import List, Literal, Optional
from datetime import datetime


class PriceContext(BaseModel):
    """Current price data and gaps"""
    last_close: float
    prev_close: float
    gap_percent: float
    high: float
    low: float
    open: float


class TrendData(BaseModel):
    """Trend indicators and classification"""
    ema_20: float
    ema_50: float
    ema_200: float
    trend_state: Literal["bullish", "bearish", "sideways"]
    strength: Literal["strong", "moderate", "weak"]
    ema_alignment_score: float = Field(ge=0.0, le=1.0, description="0-1, how well EMAs are aligned")


class MACDData(BaseModel):
    """MACD indicator data"""
    value: float
    signal: float
    histogram: float
    state: Literal["positive", "negative"]


class MomentumData(BaseModel):
    """Momentum indicators"""
    rsi_14: float = Field(ge=0.0, le=100.0)
    rsi_regime: Literal["oversold", "bearish_neutral", "neutral", "bullish_neutral", "overbought"]
    macd: MACDData


class VolatilityData(BaseModel):
    """Volatility measurements"""
    atr_14: float
    atr_percent: float = Field(description="ATR as % of price")
    volatility_regime: Literal["low", "normal", "high", "extreme"]
    bollinger_bandwidth: float = Field(description="BB upper - BB lower as % of middle")


class StructureData(BaseModel):
    """Market structure and support/resistance"""
    market_structure: Literal["higher_high", "lower_low", "range", "consolidation"]
    swing_high: float
    swing_low: float
    support_levels: List[float] = Field(max_items=3)
    resistance_levels: List[float] = Field(max_items=3)
    pivot_point: float


class VolumeData(BaseModel):
    """Volume analysis"""
    today_vs_20d_avg: float = Field(description="Today's volume / 20-day average")
    volume_trend: Literal["expanding", "contracting", "stable"]
    volume_confirmation: bool = Field(description="Volume supports price action")
    volume_spike: bool = Field(description="Volume > 2x average")


class RelativeStrengthData(BaseModel):
    """Relative strength vs market and sector"""
    vs_nifty: float = Field(default=1.0, description="Relative strength vs NIFTY, 1.0 = equal")
    vs_sector: float = Field(default=1.0, description="Relative strength vs sector")
    sector_symbol: str = Field(default="UNKNOWN")
    sector_trend: Literal["strong", "weak", "neutral"] = Field(default="neutral")
    market_leadership: Literal["leader", "inline", "laggard"] = Field(default="inline")


class MarketContext(BaseModel):
    """Overall market conditions"""
    nifty_trend: Literal["bullish", "bearish", "sideways"]
    nifty_close: float
    india_vix: float
    vix_regime: Literal["complacent", "normal", "elevated", "panic"]
    macro_bias: Literal["risk_on", "risk_off", "neutral"]
    breadth_indicator: Optional[float] = Field(None, description="Advance/Decline ratio")


class SignalSummary(BaseModel):
    """High-level signal summary"""
    directional_bias: Literal["bullish", "bearish", "neutral"]
    confidence_score: float = Field(ge=0.0, le=1.0, description="0.0-1.0")
    conviction: Literal["high", "medium", "low"]
    primary_signal: str = Field(description="Main reason for bias")
    risk_level: Literal["low", "moderate", "high"]


class SignalResponse(BaseModel):
    """
    CANONICAL SIGNAL SCHEMA
    This is the single source of truth for all signals
    CANNOT be overridden by AI
    """
    symbol: str
    timeframe: Literal["swing", "positional", "intraday"]
    timestamp: datetime
    
    price: PriceContext
    trend: TrendData
    momentum: MomentumData
    volatility: VolatilityData
    structure: StructureData
    volume: VolumeData
    relative_strength: RelativeStrengthData
    market_context: MarketContext
    signal_summary: SignalSummary
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "RELIANCE.NS",
                "timeframe": "swing",
                "timestamp": "2025-01-18T10:30:00Z",
                "signal_summary": {
                    "directional_bias": "bullish",
                    "confidence_score": 0.67,
                    "conviction": "medium",
                    "primary_signal": "EMA alignment + RSI regime",
                    "risk_level": "moderate"
                }
            }
        }
