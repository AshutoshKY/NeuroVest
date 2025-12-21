"""
Sentiment Impact Analysis
Analyzes news sentiment with novelty detection and time decay

Based on COMPLETE_IMPLEMENTATION_PLAN_PART_2.md Component 5
"""

from .schemas import NewsItem, SentimentImpact, SentimentContext
from .impact_analyzer import analyze_news_impact
from .time_decay import calculate_time_decay

__all__ = [
    'NewsItem',
    'SentimentImpact', 
    'SentimentContext',
    'analyze_news_impact',
    'calculate_time_decay'
]
