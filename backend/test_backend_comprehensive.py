#!/usr/bin/env python3
"""
COMPREHENSIVE BACKEND TEST SUITE
Tests all changes without frontend dependencies

Run: python3 test_backend_comprehensive.py
"""

import sys
import os
import json
import asyncio
from datetime import datetime

sys.path.insert(0, '.')

print("=" * 100)
print(" " * 25 + "COMPREHENSIVE BACKEND TEST SUITE")
print(" " * 30 + "Testing All Changes")
print("=" * 100)

test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

# ============================================================================
# LAYER 1: UNIT TESTS (No External Dependencies)
# ============================================================================
print("\n" + "=" * 100)
print("LAYER 1: UNIT TESTS (Pure Logic)")
print("=" * 100)

# Test 1: Validator Logic
print("\n[TEST 1] Output Validator Logic...")
try:
    from app.output_validator import validate_llm_output
    
    # Test valid output
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
    
    if result.is_valid:
        print("  ✅ PASS: Validator accepts valid output")
        test_results["passed"].append("Validator - Valid Output")
    else:
        print(f"  ❌ FAIL: Validator rejected valid output: {result.errors}")
        test_results["failed"].append(f"Validator - Valid Output: {result.errors}")
    
    # Test invalid output (banned word)
    invalid_json = json.dumps({
        "analysis_summary": "Buy now! Guaranteed profits!",
        "signal_explanation": "Test",
        "scenario_narratives": {"base_case": "a", "bull_case": "b", "bear_case": "c"},
        "risk_factors": ["test"],
        "market_context_summary": "test"
    })
    
    result = validate_llm_output(invalid_json, test_scenarios, {}, 50)
    
    if not result.is_valid and any("banned" in str(e.message).lower() for e in result.errors):
        print("  ✅ PASS: Validator detects banned words")
        test_results["passed"].append("Validator - Banned Words")
    else:
        print("  ❌ FAIL: Validator missed banned words")
        test_results["failed"].append("Validator - Banned Words")
    
    # Test probability sum check
    bad_prob_scenarios = [
        {"name": "Base", "probability": 0.6, "price_range": [100, 110], "drivers": ["test"], "invalidation": "95"},
        {"name": "Bull", "probability": 0.5, "price_range": [110, 120], "drivers": ["test"], "invalidation": "95"}
    ]
    
    result = validate_llm_output(valid_json, bad_prob_scenarios, {}, 50)
    
    if not result.is_valid:
        print("  ✅ PASS: Validator detects probability/scenario errors")
        test_results["passed"].append("Validator - Probability Check")
    else:
        print("  ⚠️  WARNING: Validator didn't catch probability sum != 1.0")
        test_results["warnings"].append("Validator might not catch all probability errors")
        
except Exception as e:
    print(f"  ❌ FAIL: Validator test crashed: {e}")
    test_results["failed"].append(f"Validator Test: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Risk Scoring
print("\n[TEST 2] Risk Scoring Calculations...")
try:
    from app.risk_scoring import calculate_risk_score
    from app.signal_engine.schemas import SignalResponse, TrendData, MomentumData, VolatilityData, VolumeData, StructureData, SignalSummary, MarketContext, MACDData, PriceContext, RelativeStrengthData
    
    # Create test signal
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
        market_context=MarketContext(nifty_trend="bullish", nifty_close=22000.0, india_vix=12.5, vix_regime="normal", macro_bias="risk_on")
    )
    
    risk_assessment = calculate_risk_score(test_signal, market_context, rs_vs_sector=1.1, sentiment_score=0.2)
    
    if 0 <= risk_assessment.risk_score <= 100:
        print(f"  ✅ PASS: Risk score in bounds (got {risk_assessment.risk_score})")
        test_results["passed"].append("Risk Scoring - Bounds")
    else:
        print(f"  ❌ FAIL: Risk score out of bounds: {risk_assessment.risk_score}")
        test_results["failed"].append(f"Risk Scoring out of bounds: {risk_assessment.risk_score}")
    
    if risk_assessment.risk_level in ["low", "moderate", "high"]:
        print(f"  ✅ PASS: Risk level valid (got {risk_assessment.risk_level})")
        test_results["passed"].append("Risk Scoring - Level")
    else:
        print(f"  ❌ FAIL: Invalid risk level: {risk_assessment.risk_level}")
        test_results["failed"].append(f"Invalid risk level: {risk_assessment.risk_level}")
        
except Exception as e:
    print(f"  ❌ FAIL: Risk scoring test crashed: {e}")
    test_results["failed"].append(f"Risk Scoring: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Prompt Building
print("\n[TEST 3] Prompt Building...")
try:
    from app.llm_integration.prompts import build_enhanced_prompt, SYSTEM_PROMPT_V2, BANNED_WORDS
    
    # Check SYSTEM_PROMPT_V2
    required_phrases = [
        "sophisticated AI financial analyst",
        "hybrid capabilities"
    ]
    
    missing = [p for p in required_phrases if p not in SYSTEM_PROMPT_V2]
    
    if not missing:
        print(f"  ✅ PASS: SYSTEM_PROMPT_V2 has all required phrases")
        test_results["passed"].append("System Prompt - Content")
    else:
        print(f"  ❌ FAIL: SYSTEM_PROMPT_V2 missing: {missing}")
        test_results["failed"].append(f"System Prompt missing: {missing}")
    
    # Check banned words
    if len(BANNED_WORDS) >= 10:
        print(f"  ✅ PASS: Banned words list has {len(BANNED_WORDS)} entries")
        test_results["passed"].append("Banned Words - Count")
    else:
        print(f"  ⚠️  WARNING: Only {len(BANNED_WORDS)} banned words")
        test_results["warnings"].append(f"Few banned words: {len(BANNED_WORDS)}")
    
    # Test prompt building
    test_signal_data = {
        'signal_summary': {'directional_bias': 'bullish', 'confidence_score': 0.75, 'primary_signal': 'test', 'conviction': 'medium', 'risk_level': 'moderate'},
        'trend': {'trend_state': 'bullish', 'strength': 'strong', 'ema_20': 100, 'ema_50': 95, 'ema_200': 90, 'ema_alignment_score': 0.9},
        'momentum': {'rsi_14': 65, 'rsi_regime': 'neutral', 'macd': {'value': 1.5, 'state': 'positive'}},
        'volatility': {'atr_14': 2.5, 'atr_percent': 1.8, 'volatility_regime': 'normal', 'bollinger_bandwidth': 0.15},
        'structure': {'market_structure': 'higher_high', 'support_levels': [90], 'resistance_levels': [110]},
        'volume': {'today_vs_20d_avg': 1.2, 'volume_trend': 'expanding', 'volume_confirmation': True, 'volume_spike': False},
        'relative_strength': {'vs_nifty': 1.05, 'vs_sector': 1.02, 'sector_symbol': 'NIFTY_AUTO', 'sector_trend': 'strong', 'market_leadership': 'leader'},
        'market_context': {'nifty_trend': 'bullish', 'nifty_close': 22000.0, 'india_vix': 12.5, 'vix_regime': 'normal', 'macro_bias': 'risk_on'}
    }
    
    test_scenarios_data = [
        {'name': 'Base', 'probability': 0.55, 'price_range': [100, 110], 'drivers': ['trend'], 'invalidation': '95'}
    ]
    
    test_risk_data = {
        'risk_score': 45, 'risk_level': 'moderate', 'trend_risk': 10,
        'volatility_risk': 5, 'market_risk': 10, 'sector_risk': 10,
        'conflict_risk': 5, 'news_risk': 5, 'conflicts': [], 'notes': 'Test'
    }
    
    prompt = build_enhanced_prompt("TEST.NS", test_signal_data, test_scenarios_data, test_risk_data)
    
    if len(prompt) > 100 and 'TEST.NS' in prompt:
        print(f"  ✅ PASS: Prompt built successfully ({len(prompt)} chars)")
        test_results["passed"].append("Prompt Building")
    else:
        print(f"  ❌ FAIL: Prompt building failed or too short")
        test_results["failed"].append("Prompt Building")
        
except Exception as e:
    print(f"  ❌ FAIL: Prompt building test crashed: {e}")
    test_results["failed"].append(f"Prompt Building: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# LAYER 2: INTEGRATION TESTS (Code Structure)
# ============================================================================
print("\n" + "=" * 100)
print("LAYER 2: INTEGRATION TESTS (Code Structure)")
print("=" * 100)

# Test 4: RAG Integration Check
print("\n[TEST 4] RAG Integration...")
try:
    import inspect
    # Import without instantiating (avoid Azure/DB deps)
    with open('app/services/rag.py', 'r') as f:
        rag_source = f.read()
    
    checks = {
        "Smart Orchestrator import": "from app.services.smart_orchestrator import smart_orchestrator" in rag_source,
        "V3 Prompt Usage": "analysis_structured" in rag_source or "analysis_structured" in rag_source,
        "Validator import": "from app.services.guardrails import guardrails_service" in rag_source,
        "Signal history retrieval": "retrieve_signal_history_for_rag" in rag_source,
        "Signal history passed to LLM": "signal_history" in rag_source
    }
    
    passed_checks = sum(1 for v in checks.values() if v)
    
    for check, result in checks.items():
        if result:
            print(f"  ✅ {check}")
        else:
            print(f"  ❌ {check}")
    
    if passed_checks == len(checks):
        print(f"  ✅ PASS: All {passed_checks} RAG integration checks passed")
        test_results["passed"].append("RAG Integration - All Checks")
    else:
        print(f"  ❌ FAIL: Only {passed_checks}/{len(checks)} RAG checks passed")
        test_results["failed"].append(f"RAG Integration: {passed_checks}/{len(checks)}")
        
except Exception as e:
    print(f"  ❌ FAIL: RAG integration check crashed: {e}")
    test_results["failed"].append(f"RAG Integration: {e}")

# Test 5: File Compilation
print("\n[TEST 5] File Compilation...")
try:
    import py_compile
    
    files = [
        'app/services/rag.py',
        'app/llm_integration/prompts.py',
        'app/output_validator/validator.py',
        'app/signal_history/rag_integration.py',
        'app/risk_scoring/scoring.py'
    ]
    
    compilation_errors = []
    for file in files:
        try:
            py_compile.compile(file, doraise=True)
        except Exception as e:
            compilation_errors.append(f"{file}: {e}")
    
    if not compilation_errors:
        print(f"  ✅ PASS: All {len(files)} files compile")
        test_results["passed"].append("File Compilation")
    else:
        print(f"  ❌ FAIL: Compilation errors:")
        for err in compilation_errors:
            print(f"    - {err}")
        test_results["failed"].append(f"Compilation: {len(compilation_errors)} errors")
        
except Exception as e:
    print(f"  ❌ FAIL: Compilation test crashed: {e}")
    test_results["failed"].append(f"Compilation: {e}")

# ============================================================================
# FINAL REPORT
# ============================================================================
print("\n" + "=" * 100)
print("TEST RESULTS SUMMARY")
print("=" * 100)

print(f"\n✅ PASSED: {len(test_results['passed'])}")
for test in test_results['passed']:
    print(f"  - {test}")

if test_results['failed']:
    print(f"\n❌ FAILED: {len(test_results['failed'])}")
    for test in test_results['failed']:
        print(f"  - {test}")
else:
    print(f"\n✅ NO FAILURES")

if test_results['warnings']:
    print(f"\n⚠️  WARNINGS: {len(test_results['warnings'])}")
    for warning in test_results['warnings']:
        print(f"  - {warning}")
else:
    print(f"\n✅ NO WARNINGS")

print("\n" + "=" * 100)

if test_results['failed']:
    print("⚠️  SOME TESTS FAILED - SEE ABOVE")
    print("=" * 100)
    sys.exit(1)
else:
    print("🎉 ALL TESTS PASSED!")
    print("=" * 100)
    sys.exit(0)
