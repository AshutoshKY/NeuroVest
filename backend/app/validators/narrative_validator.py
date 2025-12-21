"""
Narrative Validator - Enforce LLM as Renderer Only

This validator ensures the LLM-generated narrative is DERIVED ONLY
from the structured state, with no new information introduced.

Rules:
1. Source Lock: Narrative may only reference structured JSON fields
2. Vocabulary Lock: NO indicators (EMA, RSI, MACD, SMA, etc.)
3. Tone Lock: Tone must match confidence level
4. No Advice: NO buy/sell/hold language
"""

import logging
import re
from typing import Dict, List, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# FORBIDDEN TERMS - These must NEVER appear in narrative
FORBIDDEN_INDICATORS = [
    'ema', 'sma', 'rsi', 'macd', 'adx', 'stoch', 'cci', 'atr',
    'bollinger', 'fibonacci', 'ichimoku', 'parabolic',
    'moving average', 'exponential', 'relative strength'
]

FORBIDDEN_FUNDAMENTAL = [
    'earnings', 'p/e', 'pe ratio', 'eps', 'revenue', 'profit',
    'balance sheet', 'cash flow', 'dividend', 'book value'
]

FORBIDDEN_ADVICE = [
    'buy', 'sell', 'hold', 'accumulate', 'distribute',
    'strong buy', 'strong sell', 'exit', 'enter'
]

ALL_FORBIDDEN_TERMS = FORBIDDEN_INDICATORS + FORBIDDEN_FUNDAMENTAL + FORBIDDEN_ADVICE


@dataclass
class ValidationResult:
    """Result of narrative validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
    def __bool__(self):
        return self.is_valid


def validate_narrative(narrative: Dict[str, Any], structured_state: Dict[str, Any]) -> ValidationResult:
    """
    Validate that narrative is derived only from structured state.
    
    Args:
        narrative: {
            "analysis_summary": str,
            "analysis_key_points": [str],
            "analysis_text": str,
            "prediction_summary": str,
            "prediction_key_points": [str],
            "prediction_text": str
        }
        structured_state: {
            "market_state": {...},
            "price_zones": {...},
            "scenarios": [...],
            "risk_factors": [...]
        }
        
    Returns:
        ValidationResult with is_valid, errors, warnings
    """
    errors = []
    warnings = []
    
    # Extract all narrative text
    narrative_texts = []
    if isinstance(narrative, dict):
        for key in ['analysis_summary', 'analysis_text', 'prediction_summary', 'prediction_text']:
            if key in narrative and narrative[key]:
                narrative_texts.append(str(narrative[key]).lower())
        
        if 'analysis_key_points' in narrative:
            narrative_texts.extend([str(p).lower() for p in narrative['analysis_key_points'] if p])
        if 'prediction_key_points' in narrative:
            narrative_texts.extend([str(p).lower() for p in narrative['prediction_key_points'] if p])
    elif isinstance(narrative, str):
        narrative_texts = [narrative.lower()]
    
    full_narrative = ' '.join(narrative_texts)
    
    logger.info("Starting narrative validation", extra={
        "operation": "narrative_validation_start",
        "narrative_length": len(full_narrative),
        "has_market_state": "market_state" in structured_state,
        "has_scenarios": "scenarios" in structured_state
    })
    
    # Rule 1: Check for forbidden terms
    found_forbidden = []
    for term in ALL_FORBIDDEN_TERMS:
        # Use word boundary regex to avoid false positives
        pattern = r'\b' + re.escape(term) + r'\b'
        if re.search(pattern, full_narrative):
            found_forbidden.append(term)
    
    if found_forbidden:
        errors.append(f"Forbidden terms found: {', '.join(found_forbidden)}")
        logger.error(f"Narrative contains forbidden terms: {found_forbidden}", extra={
            "operation": "narrative_validation_forbidden_terms",
            "forbidden_terms": found_forbidden
        })
    
    # Rule 2: Check for price references outside price_zones
    price_zones = structured_state.get("price_zones", {})
    if price_zones:
        support_lower = price_zones.get("support", {}).get("lower", 0)
        resistance_upper = price_zones.get("resistance", {}).get("upper", 0)
        
        # Extract price mentions from narrative (₹1234 or 1234.56)
        price_pattern = r'₹?(\d{1,5}(?:\.\d{1,2})?)'
        prices_mentioned = [float(m.group(1)) for m in re.finditer(price_pattern, full_narrative)]
        
        for price in prices_mentioned:
            if price < support_lower * 0.9 or price > resistance_upper * 1.1:
                warnings.append(f"Price {price} mentioned outside reasonable zone range")
    
    # Rule 3: Tone/Confidence match
    market_state = structured_state.get("market_state", {})
    confidence = market_state.get("confidence", 0.5)
    
    # Check for overconfident language if confidence is low
    if confidence < 0.5:
        overconfident_terms = ['definitely', 'certainly', 'guaranteed', 'sure', 'clear']
        for term in overconfident_terms:
            if term in full_narrative:
                warnings.append(f"Overconfident language '{term}' used with low confidence ({confidence:.2f})")
    
    # Rule 4: Check scenarios mentioned match structured scenarios
    scenarios = structured_state.get("scenarios", [])
    if scenarios:
        scenario_probs = [s.get("probability", 0) for s in scenarios]
        
        # Extract percentage mentions from narrative
        prob_pattern = r'(\d{1,2})%'
        probs_mentioned = [int(m.group(1)) / 100.0 for m in re.finditer(prob_pattern, full_narrative)]
        
        for mentioned_prob in probs_mentioned:
            # Check if mentioned probability matches any scenario (within 5%)
            if not any(abs(mentioned_prob - sp) < 0.05 for sp in scenario_probs):
                warnings.append(f"Probability {mentioned_prob*100:.0f}% mentioned not matching any scenario")
    
    # Rule 5: Check narrative doesn't contradict trend_bias
    trend_bias = market_state.get("trend_bias", "neutral")
    
    if trend_bias == "bullish":
        contradictory_terms = ['bearish', 'downtrend', 'decline', 'fall']
        for term in contradictory_terms:
            if term in full_narrative and 'not' not in full_narrative[max(0, full_narrative.find(term)-20):full_narrative.find(term)]:
                warnings.append(f"Bullish bias contradicted by term '{term}'")
    
    elif trend_bias == "bearish":
        contradictory_terms = ['bullish', 'uptrend', 'rally', 'rise']
        for term in contradictory_terms:
            if term in full_narrative and 'not' not in full_narrative[max(0, full_narrative.find(term)-20):full_narrative.find(term)]:
                warnings.append(f"Bearish bias contradicted by term '{term}'")
    
    # Final validation
    is_valid = len(errors) == 0
    
    logger.info(f"Narrative validation {'PASSED' if is_valid else 'FAILED'}", extra={
        "operation": "narrative_validation_complete",
        "is_valid": is_valid,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings
    })
    
    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings
    )


def enforce_narrative_regeneration(
    previous_narrative: Dict[str, Any],
    structured_state: Dict[str, Any],
    validation_result: ValidationResult
) -> str:
    """
    Generate a stricter prompt for LLM when narrative validation fails.
    
    Returns a string to append to the LLM prompt with explicit constraints.
    """
    constraints = []
    
    if validation_result.errors:
        constraints.append("CRITICAL VIOLATIONS DETECTED IN PREVIOUS RESPONSE:")
        for error in validation_result.errors:
            constraints.append(f"  - {error}")
        constraints.append("")
    
    constraints.append("MANDATORY CONSTRAINTS (FAILURE = REJECTED):")
    constraints.append("1. NEVER mention: EMA, SMA, RSI, MACD, or any technical indicators")
    constraints.append("2. ONLY reference price zones from structured data")
    constraints.append("3. ONLY use probabilities from pre-generated scenarios")
    constraints.append(f"4. Match tone to confidence level: {structured_state.get('market_state', {}).get('confidence', 0.5):.2f}")
    constraints.append("5. NO advice language (buy/sell/hold)")
    
    return "\n".join(constraints)
