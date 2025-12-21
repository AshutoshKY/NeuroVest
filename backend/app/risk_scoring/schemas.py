"""
Risk Assessment Schema
"""

from pydantic import BaseModel, Field
from typing import List, Literal


class RiskAssessment(BaseModel):
    """Complete risk assessment"""
    risk_score: int = Field(ge=0, le=100, description="Total risk score")
    risk_level: Literal["low", "moderate", "high"]
    
    # Breakdown
    trend_risk: int = Field(ge=0, le=25, description="From weak trend")
    volatility_risk: int = Field(ge=0, le=20, description="From high volatility")
    market_risk: int = Field(ge=0, le=15, description="From adverse market regime")
    sector_risk: int = Field(ge=0, le=15, description="From sector weakness")
    conflict_risk: int = Field(ge=0, le=15, description="From signal conflicts")
    news_risk: int = Field(ge=0, le=10, description="From negative/uncertain news")
    
    # Conflicts detected
    conflicts: List[str] = Field(description="List of signal conflicts detected")
    
    # Recommendations
    notes: str = Field(description="Human-readable risk notes")
