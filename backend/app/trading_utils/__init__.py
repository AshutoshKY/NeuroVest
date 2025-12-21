"""
Trading Utils Integration
Integrates pattern recognition from trading-utils repository
Simplified versions of key patterns
"""

from .strat_patterns import detect_strat_pattern, StratPattern
from .power_of_3 import detect_power_of_3, PowerOf3Phase
from .smoothed_roc import calculate_smoothed_roc

__all__ = [
    'detect_strat_pattern',
    'StratPattern',
    'detect_power_of_3',
    'PowerOf3Phase',
    'calculate_smoothed_roc'
]
