import pytest
from app.risk_scoring import calculate_risk_score
from app.signal_engine.schemas import (
    SignalResponse, TrendData, MomentumData, VolatilityData, VolumeData, 
    StructureData, SignalSummary, MarketContext, MACDData, PriceContext, 
    RelativeStrengthData
)
from datetime import datetime

def test_risk_scoring_high_risk():
    """Test that weak trend + high volatility = high risk"""
    market_context = MarketContext(nifty_trend="bearish", nifty_close=22000.0, india_vix=25.0, vix_regime="panic", macro_bias="risk_off")

    test_signal = SignalResponse(
        symbol="TEST",
        timeframe="swing",
        timestamp=datetime.now(),
        signal_summary=SignalSummary(directional_bias="bullish", confidence_score=0.4, primary_signal="trend", conviction="low", risk_level="high"),
        price=PriceContext(last_close=100.0, prev_close=99.0, gap_percent=1.0, high=101.0, low=99.0, open=99.5),
        trend=TrendData(trend_state="sideways", strength="weak", ema_20=100, ema_50=95, ema_200=90, ema_alignment_score=0.1),
        momentum=MomentumData(rsi_14=45, rsi_regime="neutral", macd=MACDData(value=-1.0, signal=-0.5, histogram=-0.5, state="negative")),
        volatility=VolatilityData(atr_14=5.0, atr_percent=5.0, volatility_regime="extreme", bollinger_bandwidth=0.5),
        volume=VolumeData(today_vs_20d_avg=0.5, volume_trend="contracting", volume_confirmation=False, volume_spike=False),
        structure=StructureData(market_structure="lower_low", swing_high=110.0, swing_low=90.0, support_levels=[80], resistance_levels=[120], pivot_point=100.0),
        relative_strength=RelativeStrengthData(vs_nifty=0.8, vs_sector=0.9, sector_symbol="NIFTY_IT", sector_trend="weak", market_leadership="laggard"),
        market_context=market_context
    )
    
    risk = calculate_risk_score(test_signal, market_context, rs_vs_sector=0.8, sentiment_score=-0.5)
    
    assert risk.risk_score > 60
    assert risk.risk_level == "high"
