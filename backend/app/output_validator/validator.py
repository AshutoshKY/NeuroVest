"""
Output Validator
Validates LLM output against rules to prevent hallucination
"""

import json
from typing import Dict, List
from .schemas import ValidationError, ValidationResult
from app.llm_integration.prompts import BANNED_WORDS


def validate_llm_output(
    llm_output: str,
    scenarios: list,
    signal_data: dict,
    risk_score: int
) -> ValidationResult:
    """
    Validate LLM output for correctness and adherence to rules
    
    Checks:
    1. Valid JSON structure
    2. All required fields present
    3. No banned words/phrases
    4. Probabilities match scenarios (if mentioned)
    5. No hallucinated price predictions
    6. Tone is appropriate
    
    Returns:
        ValidationResult with errors and warnings
    """
    
    errors = []
    warnings = []
    validated_data = {}
    
    # 1. Check if valid JSON
    try:
        parsed = json.loads(llm_output)
        validated_data = parsed
    except json.JSONDecodeError as e:
        errors.append(ValidationError(
            error_type="json_parse_error",
            message=f"Invalid JSON: {str(e)}",
            severity="error"
        ))
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
    
    # 2. Check required fields
    required_fields = [
        "analysis_summary",
        "signal_explanation",
        "scenario_narratives",
        "risk_factors",
        "market_context_summary"
    ]
    
    for field in required_fields:
        if field not in parsed:
            errors.append(ValidationError(
                error_type="missing_field",
                message=f"Required field '{field}' is missing",
                severity="error"
            ))
    
    # 3. CRITICAL NEW: Check exactly 3 scenarios in scenarios list
    if scenarios and len(scenarios) != 3:
        errors.append(ValidationError(
            error_type="scenario_count_error",
            message=f"Expected exactly 3 scenarios, got {len(scenarios)}",
            severity="error"
        ))
    
    # 4. CRITICAL NEW: Check probabilities sum to 1.0 (±0.01 tolerance)
    if scenarios:
        total_prob = sum(s.get('probability', 0) for s in scenarios)
        if abs(total_prob - 1.0) > 0.01:
            errors.append(ValidationError(
                error_type="probability_sum_error",
                message=f"Probabilities sum to {total_prob:.3f}, must equal 1.0 (±0.01)",
                severity="error"
            ))
    
    # 5. CRITICAL NEW: Check all probabilities are non-negative
    if scenarios:
        for i, scenario in enumerate(scenarios):
            prob = scenario.get('probability', 0)
            if prob < 0:
                errors.append(ValidationError(
                    error_type="negative_probability",
                    message=f"Scenario {i} has negative probability: {prob}",
                    severity="error"
                ))
    
    # 6. CRITICAL NEW: Check price ranges are within envelopes
    if scenarios:
        for scenario in scenarios:
            scenario_name = scenario.get('name', '').lower().replace(' ', '_')
            price_range = scenario.get('price_range', [])
            
            if len(price_range) != 2:
                errors.append(ValidationError(
                    error_type="invalid_price_range",
                    message=f"Scenario '{scenario_name}' has invalid price range format",
                    severity="error"
                ))
                continue
            
            low, high = price_range
            
            # Price range must be [low, high] with low < high
            if low >= high:
                errors.append(ValidationError(
                    error_type="invalid_price_range_order",
                    message=f"Scenario '{scenario_name}': low ({low}) must be < high ({high})",
                    severity="error"
                ))
    
    # 7. CRITICAL NEW: Check confidence is in [0, 1] if present
    if "confidence" in parsed:
        conf = parsed["confidence"]
        if not (0 <= conf <= 1):
            errors.append(ValidationError(
                error_type="confidence_out_of_bounds",
                message=f"Confidence {conf} must be in range [0, 1]",
                severity="error"
            ))
    
    # 8. CRITICAL NEW: Check invalidation is a price level (numeric) for each scenario
    if scenarios:
        for scenario in scenarios:
            invalidation = scenario.get('invalidation', '')
            # Try to extract numeric value
            import re
            numbers = re.findall(r'[\d,.]+', str(invalidation))
            if not numbers:
                errors.append(ValidationError(
                    error_type="missing_invalidation_price",
                    message=f"Scenario '{scenario.get('name')}' invalidation must include a price level",
                    severity="error"
                ))
    
    # 9. CRITICAL NEW: Check drivers reference signal data
    if scenarios and signal_data:
        # Get all signal keys that exist
        valid_signal_keys = set()
        if 'trend' in signal_data:
            valid_signal_keys.update(['trend', 'ema', 'moving average'])
        if 'momentum' in signal_data:
            valid_signal_keys.update(['momentum', 'rsi', 'macd'])
        if 'volatility' in signal_data:
            valid_signal_keys.update(['volatility', 'atr'])
        if 'volume' in signal_data:
            valid_signal_keys.update(['volume'])
        if 'structure' in signal_data:
            valid_signal_keys.update(['structure', 'support', 'resistance'])
        
        for scenario in scenarios:
            drivers = scenario.get('drivers', [])
            for driver in drivers:
                driver_lower = driver.lower()
                # Check if driver mentions ANY valid signal
                has_signal_reference = any(key in driver_lower for key in valid_signal_keys)
                if not has_signal_reference:
                    warnings.append(ValidationError(
                        error_type="driver_missing_signal_reference",
                        message=f"Driver '{driver}' doesn't reference any signal data",
                        severity="warning"
                    ))
    
    # 10. Check for banned words
    full_text = json.dumps(parsed).lower()
    
    for banned_word in BANNED_WORDS:
        if banned_word.lower() in full_text:
            errors.append(ValidationError(
                error_type="banned_phrase",
                message=f"Output contains banned phrase: '{banned_word}'",
                severity="error"
            ))
    
    # 11. Check scenario narratives structure
    if "scenario_narratives" in parsed:
        required_scenarios = ["base_case", "bull_case", "bear_case"]
        for scenario_key in required_scenarios:
            if scenario_key not in parsed["scenario_narratives"]:
                errors.append(ValidationError(
                    error_type="missing_scenario",
                    message=f"Missing scenario narrative for '{scenario_key}'",
                    severity="error"
                ))
    
    # 12. Check for exact price predictions (regex-based)
    import re
    
    # Look for patterns like "will reach 1500", "target of 2000", etc.
    price_prediction_patterns = [
        r"will reach (?:₹|rs\.?|inr)?\s*\d+",
        r"target (?:of |price )(?:₹|rs\.?|inr)?\s*\d+",
        r"expect (?:₹|rs\.?|inr)?\s*\d+ (?:by|in)",
        r"predicting (?:₹|rs\.?|inr)?\s*\d+"
    ]
    
    for pattern in price_prediction_patterns:
        if re.search(pattern, full_text, re.IGNORECASE):
            errors.append(ValidationError(
                error_type="exact_price_prediction",
                message=f"Output appears to make exact price predictions",
                severity="error"
            ))
            break
    
    # 13. Check tone (warnings only)
    promotional_words = ["amazing", "incredible", "unmissable", "hot tip", "insider"]
    for word in promotional_words:
        if word.lower() in full_text:
            warnings.append(ValidationError(
                error_type="tone_warning",
                message=f"Output contains promotional language: '{word}'",
                severity="warning"
            ))
    
    # 14. Check if directional bias is respected
    if signal_data:
        bias = signal_data.get('signal_summary', {}).get('directional_bias', '').lower()
        
        contradictions = {
            "bullish": ["bearish outlook", "expect decline", "downward pressure"],
            "bearish": ["bullish outlook", "expect rally", "upward momentum"],
        }
        
        if bias in contradictions:
            for phrase in contradictions[bias]:
                if phrase in full_text:
                    errors.append(ValidationError(
                        error_type="contradicts_signal",
                        message=f"Output contradicts {bias} signal: contains '{phrase}'",
                        severity="error"
                    ))
    
    # 15. Check risk factors are mentioned
    if "risk_factors" in parsed and isinstance(parsed["risk_factors"], list):
        if len(parsed["risk_factors"]) == 0:
            warnings.append(ValidationError(
                error_type="missing_risk_factors",
                message="No risk factors mentioned (should highlight risks)",
                severity="warning"
            ))
    
    # Determine overall validity
    is_valid = len(errors) == 0
    
    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        validated_output=validated_data if is_valid else {}
    )


def check_probability_adherence(
    llm_output_text: str,
    scenarios: list
) -> List[str]:
    """
    Check if LLM mentions probabilities and if they match scenarios
    
    Returns:
        List of issues found (empty if all good)
    """
    
    import re
    
    issues = []
    
    # Extract percentages from text
    percentages = re.findall(r'(\d+)%', llm_output_text)
    
    scenario_probs = [int(s['probability'] * 100) for s in scenarios]
    
    for pct_str in percentages:
        pct = int(pct_str)
        
        # Check if this percentage is one of our scenarios
        if pct not in scenario_probs and pct not in [100 - sum(scenario_probs)]:  # Allow complement
            # Allow small rounding differences (±1%)
            if not any(abs(pct - sp) <= 1 for sp in scenario_probs):
                issues.append(f"Mentioned {pct}% which doesn't match any scenario probability")
    
    return issues
