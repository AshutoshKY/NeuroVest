"""
Scenario Snapshot Storage & Outcome Tracking

This module provides the core backtesting functionality:
1. Store scenario snapshots when generated
2. Track realized market outcomes
3. Measure scenario prediction accuracy
4. Enable calibration of the scenario engine

CRITICAL: This enables measuring the accuracy of our deterministic scenario engine.
Without this, we cannot validate that our probability calculations are correct.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)


@dataclass
class ScenarioSnapshot:
    """
    A snapshot of scenarios at a specific point in time.
    
    This captures:
    - What scenarios were generated
    - What the market state was
    - What actually happened after
    """
    snapshot_id: str
    timestamp: str  # ISO format
    ticker: str
    
    # Input state (what we knew)
    market_state: Dict[str, Any]
    price_zones: Dict[str, Any]
    scenarios: List[Dict[str, Any]]
    signal_conflicts: List[Dict[str, Any]]
    risk_score: float
    
    # Current price at time of snapshot
    price_at_snapshot: float
    
    # Outcome (what actually happened) - populated later
    realized_outcome: Optional[Dict[str, Any]] = None
    outcome_measured_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ScenarioSnapshot':
        """Create from dictionary"""
        return cls(**data)


# In-memory storage (for MVP - replace with DB later)
_snapshot_storage: Dict[str, List[ScenarioSnapshot]] = {}


def store_snapshot(
    ticker: str,
    market_state: Dict[str, Any],
    price_zones: Dict[str, Any],
    scenarios: List[Dict[str, Any]],
    signal_conflicts: List[Dict[str, Any]],
    risk_score: float,
    current_price: float
) -> str:
    """
    Store a scenario snapshot.
    
    Args:
        ticker: Stock symbol
        market_state: Current market state from signal engine
        price_zones: Price zones (support, value, resistance)
        scenarios: Generated scenarios from scenario_engine
        signal_conflicts: Any signal conflicts detected
        risk_score: Risk assessment score
        current_price: Current market price
        
    Returns:
        snapshot_id: Unique identifier for this snapshot
    """
    import uuid
    
    snapshot_id = f"snapshot_{ticker}_{uuid.uuid4().hex[:12]}"
    timestamp = datetime.utcnow().isoformat()
    
    snapshot = ScenarioSnapshot(
        snapshot_id=snapshot_id,
        timestamp=timestamp,
        ticker=ticker,
        market_state=market_state,
        price_zones=price_zones,
        scenarios=scenarios,
        signal_conflicts=signal_conflicts,
        risk_score=risk_score,
        price_at_snapshot=current_price,
        realized_outcome=None,
        outcome_measured_at=None
    )
    
    # Store in memory
    if ticker not in _snapshot_storage:
        _snapshot_storage[ticker] = []
    
    _snapshot_storage[ticker].append(snapshot)
    
    logger.info(f"📸 Stored scenario snapshot: {snapshot_id}", extra={
        "operation": "snapshot_stored",
        "snapshot_id": snapshot_id,
        "ticker": ticker,
        "scenario_count": len(scenarios),
        "price": current_price
    })
    
    return snapshot_id


def update_outcome(
    snapshot_id: str,
    ticker: str,
    activated_scenario_id: Optional[str],
    activation_time: Optional[str],
    max_favorable_excursion: float,
    max_adverse_excursion: float,
    final_price: float,
    days_elapsed: int
) -> bool:
    """
    Update a snapshot with the realized outcome.
    
    Args:
        snapshot_id: ID of the snapshot to update
        ticker: Stock symbol
        activated_scenario_id: Which scenario actually happened (None if none matched)
        activation_time: When the scenario activated
        max_favorable_excursion: Highest price reached
        max_adverse_excursion: Lowest price reached
        final_price: Final price at measurement time
        days_elapsed: Days since snapshot
        
    Returns:
        bool: Success status
    """
    if ticker not in _snapshot_storage:
        logger.warning(f"No snapshots found for ticker: {ticker}")
        return False
    
    # Find the snapshot
    snapshot = None
    for snap in _snapshot_storage[ticker]:
        if snap.snapshot_id == snapshot_id:
            snapshot = snap
            break
    
    if not snapshot:
        logger.warning(f"Snapshot not found: {snapshot_id}")
        return False
    
    # Update outcome
    snapshot.realized_outcome = {
        "activated_scenario_id": activated_scenario_id,
        "activation_time": activation_time,
        "max_favorable_excursion": max_favorable_excursion,
        "max_adverse_excursion": max_adverse_excursion,
        "final_price": final_price,
        "price_change_pct": ((final_price - snapshot.price_at_snapshot) / snapshot.price_at_snapshot) * 100,
        "days_elapsed": days_elapsed
    }
    snapshot.outcome_measured_at = datetime.utcnow().isoformat()
    
    logger.info(f"✅ Updated outcome for snapshot: {snapshot_id}", extra={
        "operation": "outcome_updated",
        "snapshot_id": snapshot_id,
        "ticker": ticker,
        "activated_scenario": activated_scenario_id,
        "price_change": snapshot.realized_outcome["price_change_pct"]
    })
    
    return True


def get_snapshots_for_ticker(
    ticker: str,
    include_outcomes_only: bool = False,
    limit: Optional[int] = None
) -> List[ScenarioSnapshot]:
    """
    Retrieve snapshots for a ticker.
    
    Args:
        ticker: Stock symbol
        include_outcomes_only: Only return snapshots with measured outcomes
        limit: Maximum number of snapshots to return (most recent first)
        
    Returns:
        List of snapshots
    """
    if ticker not in _snapshot_storage:
        return []
    
    snapshots = _snapshot_storage[ticker]
    
    # Filter if needed
    if include_outcomes_only:
        snapshots = [s for s in snapshots if s.realized_outcome is not None]
    
    # Sort by timestamp (most recent first)
    snapshots = sorted(snapshots, key=lambda s: s.timestamp, reverse=True)
    
    # Limit if needed
    if limit:
        snapshots = snapshots[:limit]
    
    return snapshots


def analyze_scenario_performance(
    ticker: str,
    lookback_days: int = 30
) -> Dict[str, Any]:
    """
    Analyze the performance of scenario predictions.
    
    This measures:
    - How often each scenario type activated
    - Accuracy of probability estimates
    - Calibration metrics
    
    Args:
        ticker: Stock symbol
        lookback_days: Number of days to look back
        
    Returns:
        Performance metrics dictionary
    """
    snapshots = get_snapshots_for_ticker(ticker, include_outcomes_only=True)
    
    if not snapshots:
        return {
            "ticker": ticker,
            "error": "No snapshots with outcomes available",
            "total_snapshots": 0
        }
    
    # Filter by lookback period
    cutoff_date = (datetime.utcnow() - timedelta(days=lookback_days)).isoformat()
    snapshots = [s for s in snapshots if s.timestamp >= cutoff_date]
    
    if not snapshots:
        return {
            "ticker": ticker,
            "error": f"No snapshots in last {lookback_days} days",
            "total_snapshots": 0
        }
    
    # Analyze
    total_snapshots = len(snapshots)
    scenario_activations = {"bull": 0, "base": 0, "bear": 0, "none": 0}
    predicted_probs = {"bull": [], "base": [], "bear": []}
    accuracy_by_type = {"bull": {"correct": 0, "total": 0}, "base": {"correct": 0, "total": 0}, "bear": {"correct": 0, "total": 0}}
    
    for snapshot in snapshots:
        # Find which scenario activated
        activated_id = snapshot.realized_outcome.get("activated_scenario_id")
        
        if activated_id:
            # Find the activated scenario
            activated_scenario = None
            for scenario in snapshot.scenarios:
                if scenario.get("id") == activated_id:
                    activated_scenario = scenario
                    break
            
            if activated_scenario:
                scenario_type = activated_scenario.get("type", "unknown")
                scenario_activations[scenario_type] = scenario_activations.get(scenario_type, 0) + 1
                
                # Check if most likely scenario was correct
                scenarios_sorted = sorted(snapshot.scenarios, key=lambda s: s.get("probability", 0), reverse=True)
                most_likely = scenarios_sorted[0] if scenarios_sorted else None
                
                if most_likely and most_likely.get("id") == activated_id:
                    accuracy_by_type[scenario_type]["correct"] += 1
                
                accuracy_by_type[scenario_type]["total"] += 1
        else:
            scenario_activations["none"] += 1
        
        # Collect predicted probabilities
        for scenario in snapshot.scenarios:
            s_type = scenario.get("type")
            if s_type in predicted_probs:
                predicted_probs[s_type].append(scenario.get("probability", 0))
    
    # Calculate metrics
    activation_rates = {
        k: v / total_snapshots if total_snapshots > 0 else 0
        for k, v in scenario_activations.items()
    }
    
    accuracy_rates = {}
    for s_type, counts in accuracy_by_type.items():
        if counts["total"] > 0:
            accuracy_rates[s_type] = counts["correct"] / counts["total"]
        else:
            accuracy_rates[s_type] = 0
    
    avg_predicted_probs = {
        k: (sum(v) / len(v) if len(v) > 0 else 0)
        for k, v in predicted_probs.items()
    }
    
    # Overall accuracy
    total_predictions = sum(counts["total"] for counts in accuracy_by_type.values())
    correct_predictions = sum(counts["correct"] for counts in accuracy_by_type.values())
    overall_accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
    
    return {
        "ticker": ticker,
        "lookback_days": lookback_days,
        "total_snapshots": total_snapshots,
        "snapshots_with_outcomes": len(snapshots),
        
        "scenario_activations": scenario_activations,
        "activation_rates": activation_rates,
        
        "accuracy_by_type": accuracy_rates,
        "overall_accuracy": overall_accuracy,
        
        "avg_predicted_probabilities": avg_predicted_probs,
        
        "calibration_note": "Compare activation_rates with avg_predicted_probabilities to check calibration",
        
        "recommendations": _generate_calibration_recommendations(
            activation_rates,
            avg_predicted_probs,
            accuracy_rates
        )
    }


def _generate_calibration_recommendations(
    activation_rates: Dict[str, float],
    avg_predicted_probs: Dict[str, float],
    accuracy_rates: Dict[str, float]
) -> List[str]:
    """
    Generate recommendations for scenario engine calibration.
    
    Args:
        activation_rates: How often each scenario actually happened
        avg_predicted_probs: Average predicted probabilities
        accuracy_rates: Accuracy of predictions by type
        
    Returns:
        List of calibration recommendations
    """
    recommendations = []
    
    for scenario_type in ["bull", "base", "bear"]:
        actual_rate = activation_rates.get(scenario_type, 0)
        predicted_prob = avg_predicted_probs.get(scenario_type, 0)
        accuracy = accuracy_rates.get(scenario_type, 0)
        
        # Check calibration
        diff = abs(actual_rate - predicted_prob)
        
        if diff > 0.15:  # More than 15% off
            if actual_rate > predicted_prob:
                recommendations.append(
                    f"{scenario_type.upper()}: Under-predicting (actual: {actual_rate:.2%}, predicted: {predicted_prob:.2%}). "
                    f"Consider increasing {scenario_type} scenario probabilities."
                )
            else:
                recommendations.append(
                    f"{scenario_type.upper()}: Over-predicting (actual: {actual_rate:.2%}, predicted: {predicted_prob:.2%}). "
                    f"Consider decreasing {scenario_type} scenario probabilities."
                )
        
        # Check accuracy
        if accuracy < 0.4 and actual_rate > 0.1:  # Low accuracy and meaningful sample
            recommendations.append(
                f"{scenario_type.upper()}: Low accuracy ({accuracy:.1%}). "
                f"Review trigger conditions and invalidation levels."
            )
    
    if not recommendations:
        recommendations.append("✅ Scenario engine appears well-calibrated. Continue monitoring.")
    
    return recommendations


def export_snapshots_to_json(ticker: str, filepath: str) -> bool:
    """
    Export snapshots to JSON file for external analysis.
    
    Args:
        ticker: Stock symbol
        filepath: Path to save JSON file
        
    Returns:
        Success status
    """
    snapshots = get_snapshots_for_ticker(ticker)
    
    if not snapshots:
        logger.warning(f"No snapshots to export for {ticker}")
        return False
    
    data = {
        "ticker": ticker,
        "export_timestamp": datetime.utcnow().isoformat(),
        "snapshot_count": len(snapshots),
        "snapshots": [snap.to_dict() for snap in snapshots]
    }
    
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"📤 Exported {len(snapshots)} snapshots to {filepath}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to export snapshots: {e}")
        return False
