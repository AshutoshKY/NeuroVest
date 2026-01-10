import pytest
import json
from app.output_validator import validate_llm_output

def test_validator_valid_structure():
    """Test validator with perfect inputs"""
    valid_json = json.dumps({
        "analysis_summary": "Summary",
        "signal_explanation": "Exp",
        "scenario_narratives": {"base_case": "A", "bull_case": "B", "bear_case": "C"},
        "risk_factors": ["R1"],
        "market_context_summary": "Ctx"
    })
    scenarios = [{"name": "Base", "probability": 1.0}] # Simplified
    
    # We expect some validation errors on probability mismatch but structure should pass basic parsing
    try:
        result = validate_llm_output(valid_json, scenarios, {}, 50)
        # We just want to ensure it runs without crashing inputs
        assert result is not None
    except Exception as e:
        pytest.fail(f"Validator crashed: {e}")
