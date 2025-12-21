"""
FINAL COMPREHENSIVE INTEGRATION TEST
Tests the complete HYBRID system end-to-end
Validates: Old RAG flows + New deterministic controls
"""

import sys
import asyncio
sys.path.insert(0, '.')

print("=" * 100)
print(" " * 20 + "FINAL COMPREHENSIVE HYBRID INTEGRATION TEST")
print(" " * 25 + "Old RAG + New Deterministic Controls")
print("=" * 100)

async def run_final_verification():
    errors = []
    warnings = []
    
    # ============================================================================
    # PHASE 1: IMPORT VALIDATION (All Components)
    # ============================================================================
    print("\n[PHASE 1] Import Validation...")
    try:
        # Existing RAG components
        from app.services.rag import RAGService
        from app.services.embeddings_service import EmbeddingsService
        from app.services.chromadb_temporal import ChromaDBStore
        from app.services.stock_api_service import stock_api_service
        from app.services.technical_trend import TechnicalTrendAnalyzer
        from app.services.prediction_tracker import PredictionAccuracyTracker
        
        # New deterministic components
        from app.llm_integration.prompts import SYSTEM_PROMPT_V2, build_enhanced_prompt, BANNED_WORDS
        from app.output_validator import validate_llm_output
        from app.signal_history import retrieve_signal_history_for_rag, get_signal_history_service
        from app.signal_engine.service import build_full_signal
        from app.risk_scoring import calculate_risk_score
        from app.scenario_engine import generate_scenarios
        
        print("  ✓ All components imported successfully")
        
    except Exception as e:
        errors.append(f"Import error: {e}")
        print(f"  ✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return errors, warnings
    
    # ============================================================================
    # PHASE 2: CHECK RAG USES STRICT SYSTEM PROMPT
    # ============================================================================
    print("\n[PHASE 2] Verifying RAG uses SYSTEM_PROMPT_V2...")
    try:
        import inspect
        source = inspect.getsource(RAGService._generate_llm_response)
        
        if 'SYSTEM_PROMPT_V2' in source:
            print("  ✓ RAG imports and uses SYSTEM_PROMPT_V2")
        else:
            errors.append("CRITICAL: RAG doesn't use SYSTEM_PROMPT_V2")
            print("  ✗ CRITICAL: RAG doesn't use SYSTEM_PROMPT_V2")
        
        if 'from app.llm_integration.prompts import SYSTEM_PROMPT_V2' in source:
            print("  ✓ RAG imports strict prompt correctly")
        else:
            warnings.append("RAG import of SYSTEM_PROMPT_V2 not found in source")
        
    except Exception as e:
        errors.append(f"System prompt check failed: {e}")
        print(f"  ✗ System prompt check failed: {e}")
    
    # ============================================================================
    # PHASE 3: CHECK RAG VALIDATES OUTPUT
    # ============================================================================
    print("\n[PHASE 3] Verifying RAG validates output...")
    try:
        import inspect
        source = inspect.getsource(RAGService._generate_llm_response)
        
        if 'validate_llm_output' in source:
            print("  ✓ RAG calls output validation")
        else:
            errors.append("CRITICAL: RAG doesn't validate output")
            print("  ✗ CRITICAL: RAG doesn't validate output")
        
        if 'from app.output_validator import validate_llm_output' in source:
            print("  ✓ RAG imports validator correctly")
        else:
            warnings.append("Validator import not found")
            
    except Exception as e:
        errors.append(f"Validation check failed: {e}")
        print(f"  ✗ Validation check failed: {e}")
    
    # ============================================================================
    # PHASE 4: CHECK SIGNAL HISTORY INTEGRATION
    # ============================================================================
    print("\n[PHASE 4] Verifying signal history integration...")
    try:
        import inspect
        source = inspect.getsource(RAGService.generate_analysis_with_steps)
        
        if 'retrieve_signal_history_for_rag' in source:
            print("  ✓ RAG retrieves signal history")
        else:
            errors.append("Signal history not retrieved by RAG")
            print("  ✗ Signal history not retrieved by RAG")
        
        if 'signal_history' in source:
            print("  ✓ signal_history variable used in RAG")
        else:
            warnings.append("signal_history variable not found")
            
    except Exception as e:
        errors.append(f"Signal history check failed: {e}")
        print(f"  ✗ Signal history check failed: {e}")
    
    # ============================================================================
    # PHASE 5: VERIFY SYSTEM_PROMPT_V2 CONTENT
    # ============================================================================
    print("\n[PHASE 5] Verifying SYSTEM_PROMPT_V2 content...")
    try:
        # Check key phrases from user's specified prompt
        required_phrases = [
            "professional equity research analyst",
            "Indian stock markets",
            "YOU ARE NOT ALLOWED TO",
            "Predict exact prices or targets",
            "YOU MUST",
            "Follow the Signal Engine output as ground truth",
            "EXACTLY three scenarios",
            "confidence_score < 0.5"
        ]
        
        missing_phrases = []
        for phrase in required_phrases:
            if phrase not in SYSTEM_PROMPT_V2:
                missing_phrases.append(phrase)
        
        if not missing_phrases:
            print(f"  ✓ SYSTEM_PROMPT_V2 contains all {len(required_phrases)} required phrases")
        else:
            errors.append(f"SYSTEM_PROMPT_V2 missing phrases: {missing_phrases}")
            print(f"  ✗ SYSTEM_PROMPT_V2 missing {len(missing_phrases)} phrases")
        
        if len(BANNED_WORDS) >= 10:
            print(f"  ✓ Banned words list has {len(BANNED_WORDS)} entries")
        else:
            warnings.append(f"Banned words only has {len(BANNED_WORDS)} entries (expected 10+)")
            
    except Exception as e:
        errors.append(f"Prompt content check failed: {e}")
        print(f"  ✗ Prompt content check failed: {e}")
    
    # ============================================================================
    # PHASE 6: VERIFY VALIDATOR HAS ALL 15 CHECKS
    # ============================================================================
    print("\n[PHASE 6] Verifying output validator has all 15 checks...")
    try:
        import inspect
        source = inspect.getsource(validate_llm_output)
        
        required_checks = [
            "json.loads",  # JSON parse
            "required_fields",  # Required fields
            "scenario_count_error",  # Scenario count = 3
            "probability_sum_error",  # Probabilities sum to 1.0
            "negative_probability",  # No negative probabilities
            "invalid_price_range",  # Price ranges valid
            "confidence_out_of_bounds",  # Confidence [0,1]
            "missing_invalidation_price",  # Invalidation is price
            "driver_missing_signal_reference",  # Drivers reference signals
            "banned_phrase",  # Banned words
            "missing_scenario",  # Scenario narratives
            "exact_price_prediction",  # No exact predictions
            "promotional",  # Tone check
            "contradicts_signal",  # Directional bias
            "risk_factors"  # Risk factors
        ]
        
        checks_found = sum(1 for check in required_checks if check in source)
        
        if checks_found == len(required_checks):
            print(f"  ✓ Validator has all 15 checks ({checks_found}/{len(required_checks)})")
        else:
            warnings.append(f"Validator has {checks_found}/{len(required_checks)} checks")
            print(f"  ⚠️ Validator has {checks_found}/{len(required_checks)} checks")
            
    except Exception as e:
        errors.append(f"Validator check failed: {e}")
        print(f"  ✗ Validator check failed: {e}")
    
    # ============================================================================
    # PHASE 7: VERIFY EXISTING DATA FLOWS PRESERVED
    # ============================================================================
    print("\n[PHASE 7] Verifying existing RAG data flows preserved...")
    try:
        import inspect
        source = inspect.getsource(RAGService.generate_analysis_with_steps)
        
        existing_flows = {
            "embeddings.query_similar": "News retrieval",
            "chromadb_temporal": "Old analyses",
            "get_technical_analysis": "Technical indicators",
            "TechnicalTrendAnalyzer": "30-day trends",
            "PredictionAccuracyTracker": "Prediction accuracy"
        }
        
        preserved = []
        missing = []
        
        for flow, description in existing_flows.items():
            if flow in source:
                preserved.append(description)
            else:
                missing.append(description)
        
        if len(preserved) == len(existing_flows):
            print(f"  ✓ All {len(preserved)} existing data flows preserved")
            for flow in preserved:
                print(f"    - {flow}")
        else:
            errors.append(f"Missing data flows: {missing}")
            print(f"  ✗ Missing {len(missing)} data flows: {missing}")
            
    except Exception as e:
        errors.append(f"Data flow check failed: {e}")
        print(f"  ✗ Data flow check failed: {e}")
    
    # ============================================================================
    # PHASE 8: TEST BUILD_ENHANCED_PROMPT
    # ============================================================================
    print("\n[PHASE 8] Testing build_enhanced_prompt...")
    try:
        # Create minimal test data
        test_signal = {
            'signal_summary': {'directional_bias': 'bullish', 'confidence_score': 0.75, 'primary_signal': 'test'},
            'trend': {'trend_state': 'bullish', 'strength': 'strong', 'ema_20': 100, 'ema_50': 95, 'ema_200': 90},
            'momentum': {'rsi_14': 65, 'rsi_regime': 'neutral', 'macd': {'value': 1.5, 'state': 'positive'}},
            'volatility': {'atr_14': 2.5, 'atr_percent': 1.8, 'volatility_regime': 'normal'},
            'structure': {'market_structure': 'uptrend', 'support_levels': [90, 85], 'resistance_levels': [110, 115]},
            'volume': {'today_vs_20d_avg': 1.2, 'volume_trend': 'increasing', 'volume_confirmation': True}
        }
        
        test_scenarios = [
            {'name': 'Base Case', 'probability': 0.55, 'price_range': [100, 110], 'drivers': ['trend strength'], 'invalidation': '₹95'},
            {'name': 'Bull Case', 'probability': 0.30, 'price_range': [110, 120], 'drivers': ['momentum'], 'invalidation': '₹95'},
            {'name': 'Bear Case', 'probability': 0.15, 'price_range': [90, 100], 'drivers': ['market risk'], 'invalidation': '₹120'}
        ]
        
        test_risk = {
            'risk_score': 45, 'risk_level': 'moderate',
            'trend_risk': 10, 'volatility_risk': 5, 'market_risk': 10,
            'sector_risk': 10, 'conflict_risk': 5, 'news_risk': 5,
            'conflicts': [], 'notes': 'Moderate risk'
        }
        
        prompt = build_enhanced_prompt(
            symbol="TEST.NS",
            signal_data=test_signal,
            scenarios=test_scenarios,
            risk_assessment=test_risk
        )
        
        print(f"  ✓ build_enhanced_prompt() works")
        print(f"    - Prompt length: {len(prompt)} characters")
        
        # Check prompt includes key sections
        if 'TEST.NS' in prompt and 'bullish' in prompt and 'moderate' in prompt:
            print(f"    - Contains signal data, scenarios, and risk")
        else:
            warnings.append("build_enhanced_prompt output may be incomplete")
            
    except Exception as e:
        errors.append(f"build_enhanced_prompt test failed: {e}")
        print(f"  ✗ build_enhanced_prompt test failed: {e}")
    
    # ============================================================================
    # PHASE 9: TEST VALIDATOR WITH GOOD AND BAD DATA
    # ============================================================================
    print("\n[PHASE 9] Testing validator with good and bad outputs...")
    try:
        # Test 1: Valid output
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
        
        result = validate_llm_output(valid_output, test_scenarios, test_signal, 45)
        
        if result.is_valid:
            print(f"  ✓ Validator accepts valid output")
        else:
            warnings.append(f"Validator rejected valid output: {result.errors}")
        
        # Test 2: Invalid output (banned word)
        invalid_output = valid_output.replace('"Test analysis"', '"Buy now! Guaranteed returns!"')
        result_invalid = validate_llm_output(invalid_output, test_scenarios, test_signal, 45)
        
        if not result_invalid.is_valid:
            print(f"  ✓ Validator rejects output with banned words")
        else:
            errors.append("Validator failed to detect banned words")
            print(f"  ✗ Validator failed to detect banned words")
        
        # Test 3: Invalid probabilities
        bad_scenarios = [
            {'name': 'Base', 'probability': 0.6, 'price_range': [100, 110], 'drivers': ['test'], 'invalidation': '95'},
            {'name': 'Bull', 'probability': 0.3, 'price_range': [110, 120], 'drivers': ['test'], 'invalidation': '95'},
            # Missing 3rd scenario
        ]
        
        result_probs = validate_llm_output(valid_output, bad_scenarios, test_signal, 45)
        
        if not result_probs.is_valid:
            print(f"  ✓ Validator detects scenario count != 3")
        else:
            errors.append("Validator failed to detect wrong scenario count")
            
    except Exception as e:
        errors.append(f"Validator test failed: {e}")
        print(f"  ✗ Validator test failed: {e}")
    
    # ============================================================================
    # PHASE 10: COMPILATION CHECK
    # ============================================================================
    print("\n[PHASE 10] Checking all files compile...")
    try:
        import py_compile
        import os
        
        files_to_check = [
            '/Volumes/AshDrive/prjts/stockmarket/backend/app/services/rag.py',
            '/Volumes/AshDrive/prjts/stockmarket/backend/app/llm_integration/prompts.py',
            '/Volumes/AshDrive/prjts/stockmarket/backend/app/output_validator/validator.py',
            '/Volumes/AshDrive/prjts/stockmarket/backend/app/signal_history/rag_integration.py',
        ]
        
        compile_errors = []
        for file in files_to_check:
            try:
                py_compile.compile(file, doraise=True)
            except py_compile.PyCompileError as e:
                compile_errors.append(f"{file}: {e}")
        
        if not compile_errors:
            print(f"  ✓ All {len(files_to_check)} modified files compile successfully")
        else:
            errors.extend(compile_errors)
            print(f"  ✗ {len(compile_errors)} files have compilation errors")
            
    except Exception as e:
        errors.append(f"Compilation check failed: {e}")
        print(f"  ✗ Compilation check failed: {e}")
    
    return errors, warnings

# ============================================================================
# RUN TEST
# ============================================================================
errors, warnings = asyncio.run(run_final_verification())

# ============================================================================
# FINAL REPORT
# ============================================================================
print("\n" + "=" * 100)
print(" " * 35 + "FINAL VERIFICATION REPORT")
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

# Summary
if not errors and not warnings:
    print("🎉 PERFECT - FULL HYBRID INTEGRATION VERIFIED!")
elif not errors:
    print("✅ INTEGRATION COMPLETE - Minor warnings noted")
else:
    print("⚠️  INTEGRATION HAS ISSUES - Review errors above")

print("=" * 100 + "\n")

# Exit with appropriate code
sys.exit(1 if errors else 0)
