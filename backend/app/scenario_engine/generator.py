"""
MARKET-GRADE Scenario Generator - Deterministic Probabilistic Scenarios

CRITICAL: This module is the SOURCE OF TRUTH for scenario generation.
The LLM must NEVER generate scenarios - it only renders narratives.

Architecture:
  RAW DATA → SIGNAL ENGINE → SCENARIO ENGINE → RISK ENGINE → STRUCTURED JSON → LLM RENDERER
  
Rules:
- Scenarios MUST sum to 1.0
- Triggers MUST reference price_zones only
- NO indicators in descriptions
- Fully deterministic (same input = same output)
- Backtestable and auditable
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


def generate_scenarios(
    market_state: Dict[str, Any],
    price_zones: Dict[str, Any],
    signal_conflicts: List[Dict[str, Any]],
    risk_score: float
) -> List[Dict[str, Any]]:
    """
    Generate 2-4 probabilistic scenarios deterministically.
    
    Args:
        market_state: {
            "trend_bias": "bullish|neutral|bearish",
            "confidence": 0.0-1.0,
            "momentum": "...",
            "volatility": "..."
        }
        price_zones: {
            "support": {"lower": float, "upper": float},
            "value_area": {"lower": float, "upper": float},
            "resistance": {"lower": float, "upper": float},
            "current_price": float
        }
        signal_conflicts: List of conflicting signals (if any)
        risk_score: 0.0-1.0
        
    Returns:
        List of scenarios, each with:
        - id: unique versioned ID
        - type: "bull|base|bear"
        - description: plain English
        - probability: 0.0-1.0
        - trigger_conditions: exact price logic
        - invalidation_level: exact price logic
        - derived_from: metadata showing derivation
    """
    
    trend_bias = market_state.get("trend_bias", "neutral")
    confidence = market_state.get("confidence", 0.5)
    has_conflicts = len(signal_conflicts) > 0
    
    # Extract prices
    support_lower = price_zones.get("support", {}).get("lower", 0)
    support_upper = price_zones.get("support", {}).get("upper", 0)
    value_lower = price_zones.get("value_area", {}).get("lower", 0)
    value_upper = price_zones.get("value_area", {}).get("upper", 0)
    resistance_lower = price_zones.get("resistance", {}).get("lower", 0)
    resistance_upper = price_zones.get("resistance", {}).get("upper", 0)
    current_price = price_zones.get("current_price", 0)
    
    logger.info(f"Generating scenarios: trend={trend_bias}, conf={confidence:.2f}, conflicts={has_conflicts}", extra={
        "operation": "scenario_generation_start",
        "trend_bias": trend_bias,
        "confidence": confidence,
        "has_conflicts": has_conflicts,
        "risk_score": risk_score
    })
    
    # DETERMINISTIC PROBABILITY CALCULATION
    scenarios = []
    
    # Rule 1: Bullish Bias
    if trend_bias == "bullish":
        if confidence >= 0.7 and not has_conflicts:
            # Strong bullish: Primary bull 65-70%
            prob_bull = 0.65 + (confidence - 0.7) * 0.5  # Max 0.70
            prob_base = 0.25
            prob_bear = 1.0 - prob_bull - prob_base
            
            scenarios.append(_create_bull_scenario(
                scenario_id=f"bull_continuation_v1_{uuid.uuid4().hex[:8]}",
                probability=prob_bull,
                price_zones=price_zones,
                confidence=confidence,
                is_primary=True
            ))
            scenarios.append(_create_base_scenario(
                scenario_id=f"range_consolidation_v1_{uuid.uuid4().hex[:8]}",
                probability=prob_base,
                price_zones=price_zones,
                confidence=confidence,
                is_primary=False
            ))
            scenarios.append(_create_bear_scenario(
                scenario_id=f"bear_reversal_v1_{uuid.uuid4().hex[:8]}",
                probability=prob_bear,
                price_zones=price_zones,
                confidence=confidence,
                is_primary=False
            ))
            
        elif confidence >= 0.5 or has_conflicts:
            # Moderate bullish or conflicts: compress probabilities
            prob_bull = 0.50 if not has_conflicts else 0.45
            prob_base = 0.35 if not has_conflicts else 0.40
            prob_bear = 1.0 - prob_bull - prob_base
            
            scenarios.append(_create_bull_scenario(
                scenario_id=f"bull_continuation_v1_{uuid.uuid4().hex[:8]}",
                probability=prob_bull,
                price_zones=price_zones,
                confidence=confidence,
                is_primary=True
            ))
            scenarios.append(_create_base_scenario(
                scenario_id=f"range_consolidation_v1_{uuid.uuid4().hex[:8]}",
                probability=prob_base,
                price_zones=price_zones,
                confidence=confidence,
                is_primary=False
            ))
            scenarios.append(_create_bear_scenario(
                scenario_id=f"bear_reversal_v1_{uuid.uuid4().hex[:8]}",
                probability=prob_bear,
                price_zones=price_zones,
                confidence=confidence,
                is_primary=False
            ))
        else:
            # Weak bullish: almost neutral
            prob_bull = 0.40
            prob_base = 0.40
            prob_bear = 0.20
            
            scenarios.append(_create_bull_scenario(
                scenario_id=f"bull_continuation_v1_{uuid.uuid4().hex[:8]}",
                probability=prob_bull,
                price_zones=price_zones,
                confidence=confidence,
                is_primary=False
            ))
            scenarios.append(_create_base_scenario(
                scenario_id=f"range_consolidation_v1_{uuid.uuid4().hex[:8]}",
                probability=prob_base,
                price_zones=price_zones,
                confidence=confidence,
                is_primary=True
            ))
            scenarios.append(_create_bear_scenario(
                scenario_id=f"bear_reversal_v1_{uuid.uuid4().hex[:8]}",
                probability=prob_bear,
                price_zones=price_zones,
                confidence=confidence,
                is_primary=False
            ))
    
    # Rule 2: Bearish Bias
    elif trend_bias == "bearish":
        if confidence >= 0.7 and not has_conflicts:
            prob_bear = 0.65 + (confidence - 0.7) * 0.5
            prob_base = 0.25
            prob_bull = 1.0 - prob_bear - prob_base
            
            scenarios.append(_create_bear_scenario(
                scenario_id=f"bear_continuation_v1_{uuid.uuid4().hex[:8]}",
                probability=prob_bear,
                price_zones=price_zones,
                confidence=confidence,
                is_primary=True
            ))
            scenarios.append(_create_base_scenario(
                scenario_id=f"range_consolidation_v1_{uuid.uuid4().hex[:8]}",
                probability=prob_base,
                price_zones=price_zones,
                confidence=confidence,
                is_primary=False
            ))
            scenarios.append(_create_bull_scenario(
                scenario_id=f"bull_reversal_v1_{uuid.uuid4().hex[:8]}",
                probability=prob_bull,
                price_zones=price_zones,
                confidence=confidence,
                is_primary=False
            ))
        else:
            prob_bear = 0.50 if not has_conflicts else 0.45
            prob_base = 0.35 if not has_conflicts else 0.40
            prob_bull = 1.0 - prob_bear - prob_base
            
            scenarios.append(_create_bear_scenario(
                scenario_id=f"bear_continuation_v1_{uuid.uuid4().hex[:8]}",
                probability=prob_bear,
                price_zones=price_zones,
                confidence=confidence,
                is_primary=True
            ))
            scenarios.append(_create_base_scenario(
                scenario_id=f"range_consolidation_v1_{uuid.uuid4().hex[:8]}",
                probability=prob_base,
                price_zones=price_zones,
                confidence=confidence,
                is_primary=False
            ))
            scenarios.append(_create_bull_scenario(
                scenario_id=f"bull_reversal_v1_{uuid.uuid4().hex[:8]}",
                probability=prob_bull,
                price_zones=price_zones,
                confidence=confidence,
                is_primary=False
            ))
    
    # Rule 3: Neutral Bias
    else:
        # Neutral: balanced probabilities
        prob_base = 0.50
        prob_bull = 0.25
        prob_bear = 0.25
        
        scenarios.append(_create_base_scenario(
            scenario_id=f"range_consolidation_v1_{uuid.uuid4().hex[:8]}",
            probability=prob_base,
            price_zones=price_zones,
            confidence=confidence,
            is_primary=True
        ))
        scenarios.append(_create_bull_scenario(
            scenario_id=f"bull_breakout_v1_{uuid.uuid4().hex[:8]}",
            probability=prob_bull,
            price_zones=price_zones,
            confidence=confidence,
            is_primary=False
        ))
        scenarios.append(_create_bear_scenario(
            scenario_id=f"bear_breakdown_v1_{uuid.uuid4().hex[:8]}",
            probability=prob_bear,
            price_zones=price_zones,
            confidence=confidence,
            is_primary=False
        ))
    
    # VALIDATION: Probabilities MUST sum to 1.0
    total_prob = sum(s["probability"] for s in scenarios)
    if abs(total_prob - 1.0) > 0.001:
        logger.error(f"CRITICAL: Probabilities don't sum to 1.0: {total_prob}", extra={
            "operation": "scenario_validation_failed",
            "total_probability": total_prob,
            "scenarios": len(scenarios)
        })
        # Normalize to force sum to 1.0
        for scenario in scenarios:
            scenario["probability"] = scenario["probability"] / total_prob
    
    logger.info(f"Generated {len(scenarios)} scenarios, probabilities: {[s['probability'] for s in scenarios]}", extra={
        "operation": "scenario_generation_complete",
        "scenario_count": len(scenarios),
        "probabilities": [round(s["probability"], 3) for s in scenarios],
        "total_prob": round(sum(s["probability"] for s in scenarios), 3)
    })
    
    return scenarios


def _create_bull_scenario(scenario_id: str, probability: float, price_zones: Dict, confidence: float, is_primary: bool) -> Dict:
    """Create bullish scenario"""
    value_upper = price_zones.get("value_area", {}).get("upper", 0)
    resistance_lower = price_zones.get("resistance", {}).get("lower", 0)
    resistance_upper = price_zones.get("resistance", {}).get("upper", 0)
    support_lower = price_zones.get("support", {}).get("lower", 0)
    
    return {
        "id": scenario_id,
        "type": "bull",
        "description": "Bullish continuation toward resistance structure",
        "probability": round(probability, 3),
        "trigger_conditions": f"Hold above {value_upper:.2f} and break {resistance_lower:.2f}",
        "invalidation_level": f"Daily close below {support_lower:.2f}",
        "target_zone": f"{resistance_lower:.2f} - {resistance_upper:.2f}",
        "derived_from": {
            "trend_bias": "bullish",
            "confidence": round(confidence, 2),
            "price_zone_reference": "value_area_high to resistance",
            "is_primary": is_primary,
            "generated_at": datetime.utcnow().isoformat()
        }
    }


def _create_bear_scenario(scenario_id: str, probability: float, price_zones: Dict, confidence: float, is_primary: bool) -> Dict:
    """Create bearish scenario"""
    value_lower = price_zones.get("value_area", {}).get("lower", 0)
    support_lower = price_zones.get("support", {}).get("lower", 0)
    support_upper = price_zones.get("support", {}).get("upper", 0)
    resistance_upper = price_zones.get("resistance", {}).get("upper", 0)
    
    return {
        "id": scenario_id,
        "type": "bear",
        "description": "Bearish reversal breakdown below support",
        "probability": round(probability, 3),
        "trigger_conditions": f"Break below {value_lower:.2f} with momentum",
        "invalidation_level": f"Daily close above {resistance_upper:.2f}",
        "target_zone": f"{support_lower:.2f} - {support_upper:.2f}",
        "derived_from": {
            "trend_bias": "bearish",
            "confidence": round(confidence, 2),
            "price_zone_reference": "value_area_low to support",
            "is_primary": is_primary,
            "generated_at": datetime.utcnow().isoformat()
        }
    }


def _create_base_scenario(scenario_id: str, probability: float, price_zones: Dict, confidence: float, is_primary: bool) -> Dict:
    """Create range-bound scenario"""
    value_lower = price_zones.get("value_area", {}).get("lower", 0)
    value_upper = price_zones.get("value_area", {}).get("upper", 0)
    resistance_lower = price_zones.get("resistance", {}).get("lower", 0)
    support_upper = price_zones.get("support", {}).get("upper", 0)
    
    return {
        "id": scenario_id,
        "type": "base",
        "description": "Range-bound consolidation within value area",
        "probability": round(probability, 3),
        "trigger_conditions": f"Trade within {value_lower:.2f} - {value_upper:.2f}",
        "invalidation_level": f"Breakout above {resistance_lower:.2f} or below {support_upper:.2f}",
        "target_zone": f"{value_lower:.2f} - {value_upper:.2f}",
        "derived_from": {
            "trend_bias": "neutral",
            "confidence": round(confidence, 2),
            "price_zone_reference": "value_area",
            "is_primary": is_primary,
            "generated_at": datetime.utcnow().isoformat()
        }
    }
