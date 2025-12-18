"""
Sentiment Impact Schemas
Pydantic models for news and sentiment analysis
"""

from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime


class NewsItem(BaseModel):
    """Single news item"""
    title: str
    content: str
    source: str
    published_at: datetime
    url: Optional[str] = None
    sentiment_score: float = Field(ge=-1.0, le=1.0, description="Raw sentiment from -1 to 1")


class SentimentImpact(BaseModel):
    """Analyzed impact of news on stock"""
    news_item: NewsItem
    relevance: Literal["high", "medium", "low"]
    relevance_type: Literal["company", "sector", "macro"]
    impact_level: Literal["major", "moderate", "minor"]
    direction: Literal["positive", "negative", "neutral"]
    novelty_score: float = Field(ge=0.0, le=1.0, description="How novel this news is (0=old, 1=brand new)")
    time_decay_factor: float = Field(ge=0.0, le=1.0, description="Time decay multiplier")
    effective_sentiment: float = Field(description="sentiment * novelty * time_decay")
    duration_estimate_days: int = Field(description="How long this impact will last")
    reasoning: str = Field(description="Why this news matters")


class SentimentContext(BaseModel):
    """Aggregated sentiment for a symbol"""
    symbol: str
    analyzed_at: datetime
    total_items: int
    positive_items: int
    negative_items: int
    neutral_items: int
    
    # Aggregated scores
    overall_sentiment: float = Field(ge=-1.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in sentiment based on volume and agreement")
    
    # Top impacts
    major_impacts: List[SentimentImpact]
    
    # Summary
    sentiment_regime: Literal["very_positive", "positive", "neutral", "negative", "very_negative"]
    risk_from_news: Literal["low", "moderate", "high"]
