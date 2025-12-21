"""
Signal Validator
================

Market-grade validation for signal outputs to ensure:
- Realistic confidence levels (0.3-0.85)
- Proper probability distributions (sum to 1.0)
- No narrative drift (narrative only explains signals)
- Price zone sanity
- Scenario completeness
"""

import re
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of validation check."""
    valid: bool
    errors: List[str]
    warnings: List[str]
    
    def __bool__(self):
        return self.valid


class ValidationError(Exception):
    """Raised when signal validation fails."""
    pass


# Constants
ALLOWED_TRENDS = ["bullish", "bearish", "neutral"]
ALLOWED_MOMENTUM = ["strong", "neutral", "weak"]
ALLOWED_VOLATILITY = ["low", "medium", "high"]

MIN_CONFIDENCE = 0.3
MAX_CONFIDENCE = 0.85

PROBABILITY_TOLERANCE = 0.05

# Forbidden terms that indicate narrative drift
FORBIDDEN_INDICATORS = [
    "ema", "sma", "rsi", "macd", "adx", "stochastic", "fibonacci",
    "ichimoku", "atr", "obv", "vwap", "pivot"
]

FORBIDDEN_FUNDAMENTALS = [
    "earnings", "eps", "revenue", "profit", "ebitda", "pe ratio",
    "fii", "dii", "gdp", "inflation", "interest rate", "fed"
]

FORBIDDEN_ADVISORY = [
    "buy", "sell", "invest", "should", "must", "recommend",
    "accumulate", "book profit", "exit", "enter"
]


def validate_signal(signal: Dict[str, Any]) -> ValidationResult:
    """
    Complete signal validation.
    
    Args:
        signal: Full signal output from LLM
        
    Returns:
        ValidationResult with status and any errors/warnings
    """
    errors = []
    warnings = []
    
    try:
        # 1. Market state validation
        ms_result = validate_market_state(signal.get("market_state", {}))
        errors.extend(ms_result.errors)
        warnings.extend(ms_result.warnings)
        
        # 2. Price zones validation
        pz_result = validate_price_zones(signal.get("price_zones", {}))
        errors.extend(pz_result.errors)
        warnings.extend(pz_result.warnings)
        
        # 3. Scenarios validation
        scenarios_result = validate_scenarios(signal.get("scenarios", []))
        errors.extend(scenarios_result.errors)
        warnings.extend(scenarios_result.warnings)
        
        # 4. Probability validation
        prob_result = validate_probabilities(signal.get("scenarios", []))
        errors.extend(prob_result.errors)
        warnings.extend(prob_result.warnings)
        
        # 5. Narrative drift validation (CRITICAL)
        if "narrative" in signal:
            narrative_result = validate_narrative_drift(signal, signal["narrative"])
            errors.extend(narrative_result.errors)
            warnings.extend(narrative_result.warnings)
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
        
    except Exception as e:
        return ValidationResult(
            valid=False,
            errors=[f"Validation exception: {str(e)}"],
            warnings=[]
        )


def validate_market_state(ms: Dict[str, Any]) -> ValidationResult:
    """
    Validate market_state structure and constraints.
    
    Rules:
    - trend_bias must be in {bullish, bearish, neutral}
    - momentum_state must be in {strong, neutral, weak}
    - volatility_state must be in {low, medium, high}
    - confidence must be 0.3 <= conf <= 0.85 (never 1.0!)
    """
    errors = []
    warnings = []
    
    # Check required fields
    if not ms:
        errors.append("market_state is missing or empty")
        return ValidationResult(False, errors, warnings)
    
    # Validate trend_bias
    trend = ms.get("trend_bias", "").lower()
    if trend not in ALLOWED_TRENDS:
        errors.append(f"Invalid trend_bias '{trend}'. Must be one of {ALLOWED_TRENDS}")
    
    # Validate momentum_state
    momentum = ms.get("momentum_state", "").lower()
    if momentum not in ALLOWED_MOMENTUM:
        errors.append(f"Invalid momentum_state '{momentum}'. Must be one of {ALLOWED_MOMENTUM}")
    
    # Validate volatility_state
    volatility = ms.get("volatility_state", "").lower()
    if volatility not in ALLOWED_VOLATILITY:
        errors.append(f"Invalid volatility_state '{volatility}'. Must be one of {ALLOWED_VOLATILITY}")
    
    # Validate confidence (CRITICAL)
    conf = ms.get("confidence", 0)
    if not isinstance(conf, (int, float)):
        errors.append(f"Confidence must be numeric, got {type(conf)}")
    elif conf < MIN_CONFIDENCE:
        errors.append(f"Confidence {conf} too low (min {MIN_CONFIDENCE}). Signals below 0.3 are noise.")
    elif conf > MAX_CONFIDENCE:
        errors.append(f"Confidence {conf} too high (max {MAX_CONFIDENCE}). Market uncertainty means confidence cannot exceed 0.85.")
    elif conf == 1.0:
        errors.append("Confidence = 1.0 is FORBIDDEN. Markets are never 100% certain.")
    
    if MIN_CONFIDENCE <= conf <= MAX_CONFIDENCE:
        # Good confidence, but check if it matches trend strength
        if trend == "bullish" and conf < 0.5:
            warnings.append(f"Bullish trend with low confidence ({conf}) - consider 'neutral' instead")
    
    return ValidationResult(len(errors) == 0, errors, warnings)


def validate_price_zones(zones: Dict[str, Any]) -> ValidationResult:
    """
    Validate price_zones for proper ordering and no overlaps.
    
    Rules:
    - support[1] < support[0] <= value_area[0]
    - value_area[0] < value_area[1] <= resistance[0]
    - resistance[0] < resistance[1]
    - No overlapping ranges
    """
    errors = []
    warnings = []
    
    if not zones:
        errors.append("price_zones is missing or empty")
        return ValidationResult(False, errors, warnings)
    
    support = zones.get("support", [])
    value_area = zones.get("value_area", [])
    resistance = zones.get("resistance", [])
    
    # Check structure
    if len(support) != 2:
        errors.append(f"support must have exactly 2 values, got {len(support)}")
    if len(value_area) != 2:
        errors.append(f"value_area must have exactly 2 values, got {len(value_area)}")
    if len(resistance) != 2:
        errors.append(f"resistance must have exactly 2 values, got {len(resistance)}")
    
    if errors:  # Can't validate ordering if structure is wrong
        return ValidationResult(False, errors, warnings)
    
    # Validate ordering
    if support[1] >= support[0]:
        errors.append(f"support range inverted: {support[1]} >= {support[0]}")
    
    if value_area[1] <= value_area[0]:
        errors.append(f"value_area range inverted: {value_area[1]} <= {value_area[0]}")
    
    if resistance[1] <= resistance[0]:
        errors.append(f"resistance range inverted: {resistance[1]} <= {resistance[0]}")
    
    # Validate relationships
    if support[0] > value_area[0]:
        errors.append(f"support upper ({support[0]}) above value_area lower ({value_area[0]})")
    
    if value_area[1] > resistance[0]:
        errors.append(f"value_area upper ({value_area[1]}) above resistance lower ({resistance[0]})")
    
    # Warn about narrow ranges
    support_width = support[0] - support[1]
    if support_width < 10:
        warnings.append(f"Support range very narrow ({support_width})")
    
    return ValidationResult(len(errors) == 0, errors, warnings)


def validate_scenarios(scenarios: List[Dict[str, Any]]) -> ValidationResult:
    """
    Validate scenarios for completeness.
    
    Rules:
    - Minimum 2 scenarios required
    - Each must have: description, probability > 0, trigger_conditions, invalidation_level
    """
    errors = []
    warnings = []
    
    if not scenarios or len(scenarios) < 2:
        errors.append(f"Must have at least 2 scenarios, got {len(scenarios)}")
        return ValidationResult(False, errors, warnings)
    
    for i, scenario in enumerate(scenarios):
        # Check required fields
        if not scenario.get("description"):
            errors.append(f"Scenario {i}: missing description")
        
        prob = scenario.get("probability", 0)
        if not isinstance(prob, (int, float)) or prob <= 0:
            errors.append(f"Scenario {i}: probability must be > 0, got {prob}")
        
        if not scenario.get("trigger_conditions"):
            errors.append(f"Scenario {i}: missing trigger_conditions")
        
        if not scenario.get("invalidation_level"):
            errors.append(f"Scenario {i}: missing invalidation_level")
    
    return ValidationResult(len(errors) == 0, errors, warnings)


def validate_probabilities(scenarios: List[Dict[str, Any]]) -> ValidationResult:
    """
    Validate that scenario probabilities sum to 1.0.
    
    Rule: Sum must be 1.0 ± PROBABILITY_TOLERANCE (0.05)
    """
    errors = []
    warnings = []
    
    if not scenarios:
        errors.append("No scenarios to validate probabilities")
        return ValidationResult(False, errors, warnings)
    
    total = sum(s.get("probability", 0) for s in scenarios)
    
    if abs(total - 1.0) > PROBABILITY_TOLERANCE:
        errors.append(f"Probabilities sum to {total:.3f}, must be 1.0 (±{PROBABILITY_TOLERANCE})")
    elif abs(total - 1.0) > 0.01:
        warnings.append(f"Probabilities sum to {total:.3f}, close but not exact")
    
    return ValidationResult(len(errors) == 0, errors, warnings)


def validate_narrative_drift(signal: Dict[str, Any], narrative: Any) -> ValidationResult:
    """
    CRITICAL: Validate that narrative only explains signals, never re-reasons.
    
    Rules:
    - Narrative must NOT introduce technical indicators (EMA, RSI, MACD, etc.)
    - Narrative must NOT introduce fundamentals (earnings, FII, GDP, etc.)
    - Narrative must NOT use advisory language (buy, sell, invest, etc.)
    - Narrative must NOT contradict market_state
    - All prices mentioned must be in price_zones
    """
    errors = []
    warnings = []
    
    # Handle both old (string) and new (dict) narrative formats
    if isinstance(narrative, str):
        all_text = narrative.lower()
    elif isinstance(narrative, dict):
        all_text = " ".join([
            narrative.get("analysis_summary", ""),
            " ".join(narrative.get("analysis_key_points", [])),
            narrative.get("analysis_text", ""),
            narrative.get("prediction_summary", ""),
            " ".join(narrative.get("prediction_key_points", [])),
            narrative.get("prediction_text", "")
        ]).lower()
    else:
        errors.append(f"Narrative must be string or dict, got {type(narrative)}")
        return ValidationResult(False, errors, warnings)
    
    # Check for forbidden technical indicators
    for term in FORBIDDEN_INDICATORS:
        if term in all_text:
            errors.append(f"Narrative introduces technical indicator '{term}' not in structured signals")
    
    # Check for forbidden fundamentals
    for term in FORBIDDEN_FUNDAMENTALS:
        if term in all_text:
            errors.append(f"Narrative introduces fundamental '{term}' not in structured signals")
    
    # Check for advisory language
    for term in FORBIDDEN_ADVISORY:
        if re.search(r'\b' + term + r'\b', all_text):
            errors.append(f"Narrative uses advisory language '{term}' which is FORBIDDEN")
    
    # Check consistency with market_state
    market_state = signal.get("market_state", {})
    trend = market_state.get("trend_bias", "").lower()
    
    if trend == "bullish":
        # Narrative shouldn't emphasize bearish outcomes
        bearish_emphasis = all_text.count("bearish") + all_text.count("downside") + all_text.count("decline")
        bullish_emphasis = all_text.count("bullish") + all_text.count("upside") + all_text.count("rally")
        
        if bearish_emphasis > bullish_emphasis:
            warnings.append("Narrative emphasizes bearish outcomes despite bullish trend_bias")
    
    return ValidationResult(len(errors) == 0, errors, warnings)
