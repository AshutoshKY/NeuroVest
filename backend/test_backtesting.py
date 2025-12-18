#!/usr/bin/env python3
"""
Backtesting Test Suite

Test the backtesting infrastructure:
1. Store snapshots
2. Track outcomes
3. Measure performance
4. Generate calibration recommendations
"""

from app.backtesting import (
    store_snapshot,
    update_outcome,
    get_snapshots_for_ticker,
    analyze_scenario_performance
)
from datetime import datetime, timedelta


def test_basic_snapshot_storage():
    """Test 1: Basic snapshot storage"""
    print("=== TEST 1: BASIC SNAPSHOT STORAGE ===")
    
    market_state = {
        "trend_bias": "bullish",
        "confidence": 0.75,
        "momentum": "strong",
        "current_price": 1550
    }
    
    price_zones = {
        "support": {"lower": 1500, "upper": 1535},
        "value_area": {"lower": 1535, "upper": 1570},
        "resistance": {"lower": 1570, "upper": 1600}
    }
    
    scenarios = [
{"id": "bull_1", "type": "bull", "probability": 0.65, "description": "Bullish continuation"},
        {"id": "base_1", "type": "base", "probability": 0.25, "description": "Range-bound"},
        {"id": "bear_1", "type": "bear", "probability": 0.10, "description": "Bearish reversal"}
    ]
    
    snapshot_id = store_snapshot(
        ticker="RELIANCE",
        market_state=market_state,
        price_zones=price_zones,
        scenarios=scenarios,
        signal_conflicts=[],
        risk_score=0.4,
        current_price=1550.0
    )
    
    print(f"✅ Stored snapshot: {snapshot_id}")
    print()
    return snapshot_id


def test_outcome_tracking(snapshot_id):
    """Test 2: Outcome tracking"""
    print("=== TEST 2: OUTCOME TRACKING ===")
    
    success = update_outcome(
        snapshot_id=snapshot_id,
        ticker="RELIANCE",
        activated_scenario_id="bull_1",  # Bull scenario activated
        activation_time=(datetime.utcnow() + timedelta(days=2)).isoformat(),
        max_favorable_excursion=1620.0,  # Went up to 1620
        max_adverse_excursion=1540.0,    # Lowest drop
        final_price=1610.0,               # Ended at 1610
        days_elapsed=7
    )
    
    print(f"✅ Outcome updated: {success}")
    print()


def test_retrieval():
    """Test 3: Snapshot retrieval"""
    print("=== TEST 3: SNAPSHOT RETRIEVAL ===")
    
    snapshots = get_snapshots_for_ticker("RELIANCE", include_outcomes_only=True)
    
    print(f"Retrieved {len(snapshots)} snapshots with outcomes")
    
    if snapshots:
        snap = snapshots[0]
        print(f"Sample snapshot:")
        print(f"  ID: {snap.snapshot_id}")
        print(f"  Scenarios: {len(snap.scenarios)}")
        print(f"  Price at snapshot: {snap.price_at_snapshot}")
        if snap.realized_outcome:
            print(f"  Activated scenario: {snap.realized_outcome['activated_scenario_id']}")
            print(f"  Price change: {snap.realized_outcome['price_change_pct']:.2f}%")
    
    print()


def test_performance_analysis():
    """Test 4: Performance analysis"""
    print("=== TEST 4: PERFORMANCE ANALYSIS ===")
    
    # Create multiple snapshots with outcomes for testing
    for i in range(5):
        market_state = {"trend_bias": "bullish", "confidence": 0.7, "current_price": 1550 + i*10}
        price_zones = {
            "support": {"lower": 1500, "upper": 1535},
            "value_area": {"lower": 1535, "upper": 1570},
            "resistance": {"lower": 1570, "upper": 1600}
        }
        scenarios = [
            {"id": f"bull_{i}", "type": "bull", "probability": 0.6},
            {"id": f"base_{i}", "type": "base", "probability": 0.3},
            {"id": f"bear_{i}", "type": "bear", "probability": 0.1}
        ]
        
        sid = store_snapshot("RELIANCE", market_state, price_zones, scenarios, [], 0.4, 1550.0 + i*10)
        
        # Simulate outcome (bull activated 60% of the time)
        activated = f"bull_{i}" if i < 3 else f"base_{i}"
        update_outcome(sid, "RELIANCE", activated, datetime.utcnow().isoformat(), 
                      1600.0, 1540.0, 1590.0, 7)
    
    # Analyze
    performance = analyze_scenario_performance("RELIANCE", lookback_days=30)
    
    print(f"Performance Analysis for RELIANCE:")
    print(f"  Total snapshots: {performance['total_snapshots']}")
    print(f"  Overall accuracy: {performance['overall_accuracy']:.1%}")
    print(f"  Activation rates: {performance['activation_rates']}")
    print(f"  Accuracy by type: {performance['accuracy_by_type']}")
    print()
    print("Calibration Recommendations:")
    for rec in performance['recommendations']:
        print(f"  • {rec}")
    print()


if __name__ == "__main__":
    print("BACKTESTING INFRASTRUCTURE TEST SUITE")
    print("=" * 70)
    print()
    
    # Run tests
    snapshot_id = test_basic_snapshot_storage()
    test_outcome_tracking(snapshot_id)
    test_retrieval()
    test_performance_analysis()
    
    print("=" * 70)
    print("ALL TESTS COMPLETE ✅")
