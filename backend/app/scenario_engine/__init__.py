"""
MARKET-GRADE Scenario Engine

Deterministic probabilistic scenario generation for market state machine.

CRITICAL: This is the SOURCE OF TRUTH for scenarios.
The LLM MUST NOT generate scenarios - it only renders narratives.
"""

# Import market-grade deterministic generator
from .generator import generate_scenarios

__all__ = ['generate_scenarios']
