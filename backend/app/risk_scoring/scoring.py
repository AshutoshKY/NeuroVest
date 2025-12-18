"""
Risk Scoring Calculations
EXACT formula from implementation plan:

risk_score = 0
+ Trend Strength (0-25 points): Weak trend = more risk
+ Volatility (0-20 points): High volatility = more risk  
+ Market Regime (0-15 points): Risk-off or elevated VIX = more risk
+ Sector Weakness (0-15 points): Underperforming sector = more risk
+ Signal Conflicts (0-15 points): Contradictory signals = more risk
+ News Uncertainty (0-10 points): Negative news or high uncertainty = more risk

TOTAL: 0-100
- 0-30: Low Risk
- 31-60: Moderate Risk
- 61-100: High Risk
"""

from typing import List, Tuple
from app.signal_engine.schemas import SignalResponse, MarketContext
from .schemas import RiskAssessment


def detect_signal_conflicts(signal: SignalResponse) -> Tuple[int, List[str]]:
    """
    Detect conflicts between different signals
    
    Returns:
        (conflict_score_0_to_15, list_of_conflicts)
    """
    
    conflicts = []
    conflict_score = 0
    
    # Conflict 1: Trend vs Momentum
    if signal.trend.trend_state == "bullish" and signal.momentum.rsi_regime in ["oversold", "bearish_neutral"]:
        conflicts.append("Bullish trend but bearish momentum (RSI)")
        conflict_score += 5
    elif signal.trend.trend_state == "bearish" and signal.momentum.rsi_regime in ["overbought", "bullish_neutral"]:
        conflicts.append("Bearish trend but bullish momentum (RSI)")
        conflict_score += 5
    
    # Conflict 2: Trend vs Volume
    if signal.trend.trend_state != "sideways" and not signal.volume.volume_confirmation:
        conflicts.append("Trend not confirmed by volume")
        conflict_score += 5
    
    # Conflict 3: MACD vs Trend
    if signal.trend.trend_state == "bullish" and signal.momentum.macd.state == "negative":
        conflicts.append("Bullish trend but negative MACD")
        conflict_score += 3
    elif signal.trend.trend_state == "bearish" and signal.momentum.macd.state == "positive":
        conflicts.append("Bearish trend but positive MACD")
        conflict_score += 3
    
    # Conflict 4: RSI Extremes
    if signal.signal_summary.directional_bias == "bullish" and signal.momentum.rsi_regime == "overbought":
        conflicts.append("Bullish bias but RSI overbought (reversal risk)")
        conflict_score += 4
    elif signal.signal_summary.directional_bias == "bearish" and signal.momentum.rsi_regime == "oversold":
        conflicts.append("Bearish bias but RSI oversold (bounce risk)")
        conflict_score += 4
    
    return (min(conflict_score, 15), conflicts)


def calculate_risk_score(
    signal: SignalResponse,
    market_context: MarketContext,
    rs_vs_sector: float = 1.0,
    sentiment_score: float = 0.0
) -> RiskAssessment:
    """
    Calculate deterministic risk score (0-100)
    
    Args:
        signal: Complete signal data
        market_context: Market conditions
        rs_vs_sector: Relative strength vs sector
        sentiment_score: Overall sentiment  (-1 to 1)
        
    Returns:
        Complete risk assessment with breakdown
    """
    
    # 1. Trend Risk (0-25): Weak trend = high risk
    if signal.trend.strength == "weak":
        trend_risk = 25
    elif signal.trend.strength == "moderate":
        trend_risk = 12
    else:  # strong
        trend_risk = 0
    
    # Additional: Sideways trend adds risk
    if signal.trend.trend_state == "sideways":
        trend_risk = min(trend_risk + 10, 25)
    
    # 2. Volatility Risk (0-20): High volatility = high risk
    volatility_regime_scores = {
        "low": 0,
        "normal": 5,
        "high": 15,
        "extreme": 20
    }
    volatility_risk = volatility_regime_scores[signal.volatility.volatility_regime]
    
    # 3. Market Risk (0-15): Risk-off or elevated VIX
    market_risk = 0
    
    # VIX component
    if market_context.vix_regime == "panic":
        market_risk += 10
    elif market_context.vix_regime == "elevated":
        market_risk += 6
    elif market_context.vix_regime == "normal":
        market_risk += 2
    
    # Market trend component
    if market_context.nifty_trend == "bearish":
        market_risk = min(market_risk + 5, 15)
    
    # 4. Sector Risk (0-15): Underperforming sector
    sector_risk = 0
    
    if rs_vs_sector < 0.8:
        sector_risk = 15  # Strong underperformance
    elif rs_vs_sector < 0.9:
        sector_risk = 10  # Moderate underperformance
    elif rs_vs_sector < 1.0:
        sector_risk = 5   # Slight underperformance
    
    # 5. Signal Conflicts (0-15)
    conflict_score, conflicts = detect_signal_conflicts(signal)
    
    # 6. News Risk (0-10): Negative or uncertain news
    news_risk = 0
    
    if sentiment_score < -0.3:
        news_risk = 10  # Strongly negative
    elif sentiment_score < -0.1:
        news_risk = 6   # Moderately negative
    elif sentiment_score < 0.1:
        news_risk = 3   # Neutral/uncertain
    
    # Total risk score
    total_risk = (
        trend_risk +
        volatility_risk +
        market_risk +
        sector_risk +
        conflict_score +
        news_risk
    )
    
    # Ensure within bounds
    total_risk = min(100, max(0, total_risk))
    
    # Determine risk level
    if total_risk <= 30:
        risk_level = "low"
        notes = "Low risk environment. Favorable conditions for entering position."
    elif total_risk <= 60:
        risk_level = "moderate"
        notes = "Moderate risk. Consider position sizing and stop-loss carefully."
    else:
        risk_level = "high"
        notes = "High risk environment. Exercise caution. Consider reducing position size or avoiding trade."
    
    return RiskAssessment(
        risk_score=total_risk,
        risk_level=risk_level,
        trend_risk=trend_risk,
        volatility_risk=volatility_risk,
        market_risk=market_risk,
        sector_risk=sector_risk,
        conflict_risk=conflict_score,
        news_risk=news_risk,
        conflicts=conflicts,
        notes=notes
    )


def get_risk_level(risk_score: int) -> str:
    """
    Convert risk score to level
    
    0-30: Low
    31-60: Moderate
    61-100: High
    """
    if risk_score <= 30:
        return "low"
    elif risk_score <= 60:
        return "moderate"
    else:
        return "high"
