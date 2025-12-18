"""
Backtesting Infrastructure - Scenario Snapshot Storage & Performance Analysis

This module enables tracking of scenarios and their realized outcomes
for performance measurement and calibration.
"""

# Only export snapshot functions (engine.py has old incompatible code)
from .snapshot import (
    ScenarioSnapshot,
    store_snapshot,
    update_outcome,
    get_snapshots_for_ticker,
    analyze_scenario_performance,
    export_snapshots_to_json
)

__all__ = [
    'ScenarioSnapshot',
    'store_snapshot',
    'update_outcome',
    'get_snapshots_for_ticker',
    'analyze_scenario_performance',
    'export_snapshots_to_json'
]
