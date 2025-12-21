"""
COMPREHENSIVE PARTS 1+2+3 INTEGRATION TEST
Tests the complete NeuroVest pipeline end-to-end
"""

import sys
import asyncio
sys.path.insert(0, '.')

print("=" * 100)
print(" " * 25 + "PARTS 1+2+3 COMPREHENSIVE INTEGRATION TEST")
print(" " * 30 + "Complete Pipeline Verification")
print("=" * 100)

async def run_comprehensive_test():
    errors = []
    warnings = []
    
    # ============================================================================
    # PHASE 1: IMPORT VALIDATION
    # ============================================================================
    print("\n[PHASE 1] Import Validation...")
    try:
        # Part 1 imports
        from app.signal_engine.service import build_full_signal
        from app.pipelines.orchestrator import pipeline_orchestrator
        from app.price_engine.ranges import calculate_price_ranges
        from app.scenario_engine import generate_scenarios
        
        # Part 2 imports
        from app.sentiment_impact import analyze_news_impact, NewsItem
        from app.relative_strength import calculate_relative_strength
        from app.risk_scoring import calculate_risk_score
        from app.llm_integration import SYSTEM_PROMPT_V2, BANNED_WORDS, build_enhanced_prompt
        from app.output_validator import validate_llm_output
        
        # Part 3 imports
        from app.signal_history import get_signal_history_service, retrieve_signal_history_for_rag
        from app.backtesting import BacktestEngine, BacktestConfig
        from app.trading_utils import detect_strat_pattern, detect_power_of_3, calculate_smoothed_roc
        
        # API routes
        from app.api.routes.signal import router
        
        print("  ✓ All modules imported successfully (Parts 1+2+3)")
        
    except Exception as e:
        errors.append(f"Import error: {e}")
        print(f"  ✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return errors, warnings
    
    # ============================================================================
    # PHASE 2: SIGNAL GENERATION (Part 1)
    # ============================================================================
    print("\n[PHASE 2] Testing Signal Generation (Part 1)...")
    signal = None
    try:
        # Test signal generation with mock data
        import pandas as pd
        import numpy as np
        
        # Create mock DataFrame
        dates = pd.date_range('2024-01-01', periods=200, freq='D')
        np.random.seed(42)
        
        mock_df = pd.DataFrame({
            'Date': dates,
            'Open': 1500 + np.random.randn(200).cumsum(),
            'High': 1510 + np.random.randn(200).cumsum(),
            'Low': 1490 + np.random.randn(200).cumsum(),
            'Close': 1500 + np.random.randn(200).cumsum(),
            'Volume': np.random.randint(1000000, 5000000, 200)
        })
        mock_df.set_index('Date', inplace=True)
        
        # Generate signal with mock data
        signal = await build_full_signal("TEST.NS", df=mock_df, timeframe="swing")
        
        print(f"  ✓ Signal generated successfully")
        print(f"    - Symbol: {signal.symbol}")
        print(f"    - Directional Bias: {signal.signal_summary.directional_bias}")
        print(f"    - Confidence: {signal.signal_summary.confidence_score:.2f}")
        print(f"    - Trend: {signal.trend.trend_state}")
        
    except Exception as e:
        errors.append(f"Signal generation error: {e}")
        print(f"  ✗ Signal generation failed: {e}")
        import traceback
        traceback.print_exc()
    
    # ============================================================================
    # PHASE 3: PRICE RANGES & SCENARIOS (Part 1)
    # ============================================================================
    print("\n[PHASE 3] Testing Price Ranges & Scenarios (Part 1)...")
    envelopes = None
    scenarios = None
    
    if signal:
        try:
            # Calculate price ranges
            envelopes = calculate_price_ranges(signal, timeframe_days=7)
            print(f"  ✓ Price ranges calculated")
            print(f"    - Base: ₹{envelopes.base_case.lower:.0f} - ₹{envelopes.base_case.upper:.0f}")
            
            # Generate scenarios
            scenarios = generate_scenarios(signal, envelopes, risk_score=50, timeframe_days=7)
            print(f"  ✓ Scenarios generated")
            total_prob = sum(s.probability for s in scenarios.scenarios)
            print(f"    - Total probability: {total_prob:.2f} (should be 1.00)")
            
            if abs(total_prob - 1.0) > 0.01:
                warnings.append(f"Scenario probabilities don't sum to 1.0: {total_prob}")
                
        except Exception as e:
            errors.append(f"Price/Scenario error: {e}")
            print(f"  ✗ Price ranges or scenarios failed: {e}")
    
    # ============================================================================
    # PHASE 4: RISK SCORING (Part 2)
    # ============================================================================
    print("\n[PHASE 4] Testing Risk Scoring (Part 2)...")
    risk_assessment = None
    
    if signal:
        try:
            risk_assessment = calculate_risk_score(signal, signal.market_context, rs_vs_sector=1.0)
            print(f"  ✓ Risk assessment calculated")
            print(f"    - Total Risk: {risk_assessment.risk_score}/100 ({risk_assessment.risk_level})")
            print(f"    - Conflicts: {len(risk_assessment.conflicts)}")
            
            # Validate risk score is within bounds
            if not (0 <= risk_assessment.risk_score <= 100):
                errors.append(f"Risk score out of bounds: {risk_assessment.risk_score}")
                
        except Exception as e:
            errors.append(f"Risk scoring error: {e}")
            print(f"  ✗ Risk scoring failed: {e}")
    
    # ============================================================================
    # PHASE 5: LLM PROMPT BUILDING (Part 2)
    # ============================================================================
    print("\n[PHASE 5] Testing LLM Prompt Building (Part 2)...")
    
    if signal and scenarios and risk_assessment:
        try:
            signal_dict = signal.dict()
            scenario_dicts = [s.dict() for s in scenarios.scenarios]
            risk_dict = risk_assessment.dict()
            
            prompt = build_enhanced_prompt(
                symbol="TEST.NS",
                signal_data=signal_dict,
                scenarios=scenario_dicts,
                risk_assessment=risk_dict
            )
            
            print(f"  ✓ LLM prompt built")
            print(f"    - Length: {len(prompt)} characters")
            print(f"    - Contains scenarios: {'scenarios' in prompt.lower()}")
            print(f"    - Contains risk: {'risk' in prompt.lower()}")
            print(f"    - BANNED_WORDS count: {len(BANNED_WORDS)}")
            
        except Exception as e:
            errors.append(f"LLM prompt error: {e}")
            print(f"  ✗ LLM prompt building failed: {e}")
    
    # ============================================================================
    # PHASE 6: OUTPUT VALIDATION (Part 2)
    # ============================================================================
    print("\n[PHASE 6] Testing Output Validator (Part 2)...")
    
    if scenarios and signal:
        try:
            # Test with valid output
            valid_output = """{
                "analysis_summary": "Test analysis",
                "signal_explanation": "Test explanation",
                "scenario_narratives": {
                    "base_case": "Base scenario",
                    "bull_case": "Bull scenario",
                    "bear_case": "Bear scenario"
                },
                "risk_factors": ["risk1", "risk2"],
                "market_context_summary": "Market context"
            }"""
            
            result = validate_llm_output(
                valid_output,
                [s.dict() for s in scenarios.scenarios],
                signal.dict(),
                50
            )
            
            print(f"  ✓ Output validator works")
            print(f"    - Valid output passes: {result.is_valid}")
            print(f"    - Errors: {len(result.errors)}")
            
            # Test banned word detection
            invalid_output = valid_output.replace('"Test analysis"', '"Buy now! Guaranteed returns!"')
            result_invalid = validate_llm_output(
                invalid_output,
                [s.dict() for s in scenarios.scenarios],
                signal.dict(),
                50
            )
            
            if not result_invalid.is_valid:
                print(f"    - Banned word detection: Works ✓")
            else:
                warnings.append("Banned word detection may not be working")
                
        except Exception as e:
            errors.append(f"Output validator error: {e}")
            print(f"  ✗ Output validator failed: {e}")
    
    # ============================================================================
    # PHASE 7: SIGNAL STORAGE (Part 3 - CRITICAL)
    # ============================================================================
    print("\n[PHASE 7] Testing Signal Storage (Part 3 - CRITICAL)...")
    signal_id = None
    
    if signal and scenarios and risk_assessment:
        try:
            history_service = get_signal_history_service()
            signal_id = history_service.store_signal(signal, scenarios, risk_assessment.risk_score)
            
            print(f"  ✓ Signal stored in ChromaDB")
            print(f"    - Signal ID: {signal_id}")
            
        except Exception as e:
            errors.append(f"CRITICAL: Signal storage failed: {e}")
            print(f"  ✗ CRITICAL: Signal storage failed: {e}")
            import traceback
            traceback.print_exc()
    
    # ============================================================================
    # PHASE 8: SIGNAL RETRIEVAL (Part 3)
    # ============================================================================
    print("\n[PHASE 8] Testing Signal Retrieval (Part 3)...")
    
    if signal_id:
        try:
            history_service = get_signal_history_service()
            retrieved_signals = history_service.get_signals(
                symbol="TEST.NS",
                timeframe="swing",
                days_back=1,
                limit=10
            )
            
            print(f"  ✓ Signals retrieved from ChromaDB")
            print(f"    - Count: {len(retrieved_signals)}")
            
            if len(retrieved_signals) == 0:
                warnings.append("No signals retrieved (may be expected if stored in different timeframe)")
                
        except Exception as e:
            errors.append(f"Signal retrieval error: {e}")
            print(f"  ✗ Signal retrieval failed: {e}")
    
    # ============================================================================
    # PHASE 9: RAG INTEGRATION (Part 3 - CRITICAL)
    # ============================================================================
    print("\n[PHASE 9] Testing RAG Integration (Part 3 - CRITICAL)...")
    
    try:
        # Test RAG integration function signature
        import inspect
        from app.services.rag import RAGService
        
        sig = inspect.signature(RAGService._generate_llm_response)
        params = list(sig.parameters.keys())
        
        if 'signal_history' in params:
            print(f"  ✓ RAG service has signal_history parameter")
        else:
            errors.append("CRITICAL: RAG service missing signal_history parameter")
            print(f"  ✗ CRITICAL: RAG service missing signal_history parameter")
        
        # Test retrieval function
        if signal_id:
            signal_summaries = retrieve_signal_history_for_rag("TEST.NS", days_back=1, max_signals=5)
            print(f"  ✓ RAG retrieval function works")
            print(f"    - Retrieved: {len(signal_summaries)} signal summaries")
            
    except Exception as e:
        errors.append(f"RAG integration error: {e}")
        print(f"  ✗ RAG integration test failed: {e}")
    
    # ============================================================================
    # PHASE 10: TRADING UTILS (Part 3)
    # ============================================================================
    print("\n[PHASE 10] Testing Trading Utils (Part 3)...")
    
    try:
        import pandas as pd
        import numpy as np
        
        # Create test data
        test_df = pd.DataFrame({
            'Open': np.random.randn(30).cumsum() + 100,
            'High': np.random.randn(30).cumsum() + 102,
            'Low': np.random.randn(30).cumsum() + 98,
            'Close': np.random.randn(30).cumsum() + 100,
            'Volume': np.random.randint(1000000, 5000000, 30)
        })
        
        # Test Strat patterns
        strat = detect_strat_pattern(test_df)
        print(f"  ✓ Strat pattern detection works")
        if strat:
            print(f"    - Pattern: {strat.pattern}")
        
        # Test Power of 3
        po3 = detect_power_of_3(test_df)
        print(f"  ✓ Power of 3 detection works")
        if po3:
            print(f"    - Phase: {po3.phase}")
        
        # Test Smoothed ROC
        roc = calculate_smoothed_roc(test_df)
        print(f"  ✓ Smoothed ROC calculation works")
        if roc is not None:
            print(f"    - ROC values calculated")
            
    except Exception as e:
        errors.append(f"Trading utils error: {e}")
        print(f"  ✗ Trading utils failed: {e}")
    
    # ============================================================================
    # PHASE 11: API ROUTE INTEGRATION (Part 3 - CRITICAL)
    # ============================================================================
    print("\n[PHASE 11] Testing API Route Integration...")
    
    try:
        from app.api.routes.signal import router
        
        # Check if router has the storage imports
        import inspect
        source = inspect.getsource(router.get_signal)
        
        if 'get_signal_history_service' in source:
            print(f"  ✓ API route has signal storage integration")
        else:
            errors.append("CRITICAL: API route missing signal storage")
            print(f"  ✗ CRITICAL: API route missing signal storage")
            
        if 'store_signal' in source:
            print(f"  ✓ API route calls store_signal()")
        else:
            errors.append("CRITICAL: API route doesn't call store_signal()")
            print(f"  ✗ CRITICAL: API route doesn't call store_signal()")
            
    except Exception as e:
        errors.append(f"API route check error: {e}")
        print(f"  ✗ API route check failed: {e}")
    
    return errors, warnings

# ============================================================================
# RUN TEST
# ============================================================================
errors, warnings = asyncio.run(run_comprehensive_test())

# ============================================================================
# FINAL REPORT
# ============================================================================
print("\n" + "=" * 100)
print(" " * 40 + "FINAL REPORT")
print("=" * 100)

if errors:
    print(f"\n🔴 ERRORS FOUND: {len(errors)}")
    for i, error in enumerate(errors, 1):
        print(f"  {i}. {error}")
else:
    print(f"\n✅ NO ERRORS FOUND")

if warnings:
    print(f"\n⚠️  WARNINGS: {len(warnings)}")
    for i, warning in enumerate(warnings, 1):
        print(f"  {i}. {warning}")
else:
    print(f"\n✅ NO WARNINGS")

print("\n" + "=" * 100)

if not errors:
    print("🎉 ALL TESTS PASSED - PARTS 1+2+3 WORKING CORRECTLY!")
else:
    print("⚠️  SOME TESTS FAILED - REVIEW ERRORS ABOVE")

print("=" * 100 + "\n")

# Exit with appropriate code
sys.exit(1 if errors else 0)
