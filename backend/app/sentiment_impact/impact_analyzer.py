"""
News Impact Analyzer
Classifies relevance, impact level, and duration of news items
"""

from typing import Tuple, Literal
from .schemas import NewsItem, SentimentImpact
from datetime import datetime
import re


def classify_relevance(news: NewsItem, symbol: str) -> Tuple[Literal["high", "medium", "low"], Literal["company", "sector", "macro"]]:
    """
    Classify how relevant news is to the symbol
    
    Returns:
        (relevance_level, relevance_type)
    """
    
    # Extract company name from symbol (e.g., "RELIANCE" from "RELIANCE.NS")
    company_name = symbol.split('.')[0].upper()
    
    # Combine title and content for analysis
    text = (news.title + " " + news.content).upper()
    
    # Company-specific keywords
    company_keywords = [company_name]
    
    # Check for direct company mention
    if any(keyword in text for keyword in company_keywords):
        return ("high", "company")
    
    # Sector keywords (simplified - should be expanded)
    sector_keywords = {
        "RELIANCE": ["oil", "telecom", "jio", "retail"],
        "INFY": ["it", "tech", "software", "infosys"],
        "TCS": ["it", "tech", "software", "tata"],
        "HDFC": ["bank", "finance", "lending"],
        "ICICI": ["bank", "finance", "lending"]
    }
    
    # Check for sector mention
    if company_name in sector_keywords:
        if any(keyword in text.lower() for keyword in sector_keywords[company_name]):
            return ("medium", "sector")
    
    # Macro keywords
    macro_keywords = ["rbi", "inflation", "gdp", "nifty", "sensex", "market", "economy"]
    if any(keyword in text.lower() for keyword in macro_keywords):
        return ("low", "macro")
    
    # Default
    return ("low", "macro")


def determine_impact_level(
    relevance: Literal["high", "medium", "low"],
    sentiment_score: float
) -> Literal["major", "moderate", "minor"]:
    """
    Determine impact level based on relevance and sentiment strength
    
    Major: High relevance + strong sentiment (|score| > 0.5)
    Moderate: High relevance + weak sentiment, or Medium relevance + strong sentiment
    Minor: Everything else
    """
    
    sentiment_strength = abs(sentiment_score)
    
    if relevance == "high" and sentiment_strength > 0.5:
        return "major"
    elif relevance == "high" or (relevance == "medium" and sentiment_strength > 0.5):
        return "moderate"
    else:
        return "minor"


def estimate_duration(
    impact_level: Literal["major", "moderate", "minor"],
    relevance_type: Literal["company", "sector", "macro"]
) -> int:
    """
    Estimate how many days this news impact will last
    
    Company news: 5-20 days depending on impact
    Sector news: 3-10 days
    Macro news: 1-5 days
    """
    
    base_duration = {
        "company": {"major": 20, "moderate": 10, "minor": 5},
        "sector": {"major": 10, "moderate": 5, "minor": 3},
        "macro": {"major": 5, "moderate": 3, "minor": 1}
    }
    
    return base_duration[relevance_type][impact_level]


def generate_reasoning(
    news: NewsItem,
    relevance: Literal["high", "medium", "low"],
    relevance_type: Literal["company", "sector", "macro"],
    impact_level: Literal["major", "moderate", "minor"],
    direction: Literal["positive", "negative", "neutral"]
) -> str:
    """Generate human-readable reasoning for why this news matters"""
    
    relevance_text = {
        "high": "directly mentions the company",
        "medium": "relates to the company's sector",
        "low": "is general market news"
    }
    
    impact_text = {
        "major": "significant",
        "moderate": "moderate",
        "minor": "minor"
    }
    
    direction_text = {
        "positive": "favorable",
        "negative": "unfavorable",
        "neutral": "neutral"
    }
    
    return f"{impact_text[impact_level].capitalize()} {direction_text[direction]} impact - news {relevance_text[relevance]}"


def analyze_news_impact(
    news: NewsItem,
    symbol: str,
    novelty_score: float = 1.0,
    time_decay_factor: float = 1.0
) -> SentimentImpact:
    """
    Analyze the impact of a news item on a symbol
    
    Args:
        news: News item to analyze
        symbol: Stock symbol
        novelty_score: How novel this news is (0-1, from novelty detector)
        time_decay_factor: Time decay multiplier (0-1, from time decay calculator)
        
    Returns:
        Complete sentiment impact analysis
    """
    
    # Classify relevance
    relevance, relevance_type = classify_relevance(news, symbol)
    
    # Determine impact level
    impact_level = determine_impact_level(relevance, news.sentiment_score)
    
    # Determine direction
    if news.sentiment_score > 0.15:
        direction = "positive"
    elif news.sentiment_score < -0.15:
        direction = "negative"
    else:
        direction = "neutral"
    
    # Estimate duration
    duration = estimate_duration(impact_level, relevance_type)
    
    # Calculate effective sentiment (with novelty and time decay)
    effective_sentiment = news.sentiment_score * novelty_score * time_decay_factor
    
    # Generate reasoning
    reasoning = generate_reasoning(news, relevance, relevance_type, impact_level, direction)
    
    return SentimentImpact(
        news_item=news,
        relevance=relevance,
        relevance_type=relevance_type,
        impact_level=impact_level,
        direction=direction,
        novelty_score=novelty_score,
        time_decay_factor=time_decay_factor,
        effective_sentiment=round(effective_sentiment, 3),
        duration_estimate_days=duration,
        reasoning=reasoning
    )
