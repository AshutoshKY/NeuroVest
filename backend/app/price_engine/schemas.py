"""
Price Range Schemas
"""

from pydantic import BaseModel, Field
from typing import Literal

class PriceRange(BaseModel):
    lower: float = Field(description="Lower bound of price range")
    upper: float = Field(description="Upper bound of price range")
    
class PriceEnvelopes(BaseModel):
    base_case: PriceRange
    bull_case: PriceRange  
    bear_case: PriceRange
    invalidation_level: float
    
class RangeMetadata(BaseModel):
    atr_14: float
    atr_percent: float
    volatility_regime: Literal["low", "normal", "high", "extreme"]
    trend_adjustment_applied: bool
    multiplier_used: float
