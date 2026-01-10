import pytest
import json
from datetime import datetime
from app.output_validator import validate_llm_output
from app.risk_scoring import calculate_risk_score
from app.signal_engine.schemas import (
    SignalResponse, TrendData, MomentumData, VolatilityData, VolumeData, 
    StructureData, SignalSummary, MarketContext, MACDData, PriceContext, 
    RelativeStrengthData
)
from app.llm_integration.prompts import SYSTEM_PROMPT_V3_PROBABILISTIC

# -----------------------------------------------------------------------------
# Test 1: Validator Logic
# -----------------------------------------------------------------------------

def test_validator_with_valid_output():
    """Test validator accepts correct JSON structure"""
    valid_json = json.dumps({
        "analysis_summary": "Test summary",
        "signal_explanation": "Based on trend strength and momentum",
        "scenario_narratives": {
            "base_case": "Trend continues",
            "bull_case": "Breakout scenario",
            "bear_case": "Reversal risk"
        },
        "risk_factors": ["Volatility", "Market risk"],
        "market_context_summary":  "Market context"
    })
    
    test_scenarios = [
        {"name": "Base", "probability": 0.55, "price_range": [100, 110], "drivers": ["trend"], "invalidation": "95"},
        {"name": "Bull", "probability": 0.30, "price_range": [110, 120], "drivers": ["momentum"], "invalidation": "95"},
        {"name": "Bear", "probability": 0.15, "price_range": [90, 100], "drivers": ["risk"], "invalidation": "115"}
    ]
    
    result = validate_llm_output(valid_json, test_scenarios, {}, 50)
    assert result.is_valid is True, f"Validator failed: {result.errors}"

def test_validator_banned_words():
    """Test validator rejects banned words"""
    invalid_json = json.dumps({
        "analysis_summary": "Buy now! Guaranteed profits!", # Banned: buy, guaranteed
        "signal_explanation": "Test",
        "scenario_narratives": {"base_case": "a", "bull_case": "b", "bear_case": "c"},
        "risk_factors": ["test"],
        "market_context_summary": "test"
    })
    
    # Needs valid scenarios to pass other checks first
    test_scenarios = [
        {"name": "Base", "probability": 0.55, "price_range": [100, 110], "drivers": ["trend"], "invalidation": "95"},
        {"name": "Bull", "probability": 0.30, "price_range": [110, 120], "drivers": ["momentum"], "invalidation": "95"},
        {"name": "Bear", "probability": 0.15, "price_range": [90, 100], "drivers": ["risk"], "invalidation": "115"}
    ]
    
    result = validate_llm_output(invalid_json, test_scenarios, {}, 50)
    assert result.is_valid is False
    assert any("banned" in str(e.message).lower() for e in result.errors)

# -----------------------------------------------------------------------------
# Test 2: Risk Scoring Logic
# -----------------------------------------------------------------------------

def test_risk_scoring_bounds():
    """Test risk score classification and bounds"""
    # 1. Create Context
    market_context = MarketContext(
        nifty_trend="bullish", 
        nifty_close=22000.0, 
        india_vix=12.5, 
        vix_regime="normal", 
        macro_bias="risk_on"
    )

    # 2. Create Signal
    test_signal = SignalResponse(
        symbol="TEST",
        timeframe="swing",
        timestamp=datetime.now(),
        signal_summary=SignalSummary(directional_bias="bullish", confidence_score=0.75, primary_signal="trend", conviction="medium", risk_level="moderate"),
        price=PriceContext(last_close=100.0, prev_close=99.0, gap_percent=1.0, high=101.0, low=99.0, open=99.5),
        trend=TrendData(trend_state="bullish", strength="strong", ema_20=100, ema_50=95, ema_200=90, ema_alignment_score=0.9),
        momentum=MomentumData(rsi_14=65, rsi_regime="neutral", macd=MACDData(value=1.5, signal=1.2, histogram=0.3, state="positive")),
        volatility=VolatilityData(atr_14=2.5, atr_percent=1.8, volatility_regime="normal", bollinger_bandwidth=0.15),
        volume=VolumeData(today_vs_20d_avg=1.2, volume_trend="expanding", volume_confirmation=True, volume_spike=False),
        structure=StructureData(market_structure="higher_high", swing_high=110.0, swing_low=90.0, support_levels=[90, 85], resistance_levels=[110, 115], pivot_point=100.0),
        relative_strength=RelativeStrengthData(vs_nifty=1.05, vs_sector=1.02, sector_symbol="NIFTY_AUTO", sector_trend="strong", market_leadership="leader"),
        market_context=market_context
    )
    
    # 3. Calculate Risk
    risk_assessment = calculate_risk_score(test_signal, market_context, rs_vs_sector=1.1, sentiment_score=0.2)
    
    assert 0 <= risk_assessment.risk_score <= 100
    assert risk_assessment.risk_level in ["low", "moderate", "high"]

# -----------------------------------------------------------------------------
# Test 3: Prompt Content
# -----------------------------------------------------------------------------

def test_v3_prompt_content():
    """Ensure V3 prompt contains critical production instructions"""
    prompt = SYSTEM_PROMPT_V3_PROBABILISTIC
    
    assert len(prompt) > 500, "Prompt is dangerously short"
    assert "CRITICAL: YOUR ROLE IS RENDERER ONLY" in prompt, "Missing critical RENDERER instruction"
    assert "NEVER use advisory language" in prompt
    assert "CONFIDENCE CALIBRATION" in prompt
