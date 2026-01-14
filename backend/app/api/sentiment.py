from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from app.services.sentiment import sentiment_service
from app.services.embeddings import get_embedding_service

router = APIRouter(prefix="/sentiment", tags=["sentiment"])


class SentimentResponse(BaseModel):
    """Sentiment analysis response schema."""
    ticker: str
    sentiment_score: float
    confidence: float
    classification: str
    reasoning: str
    key_factors: List[str]
    aggregate: Dict[str, Any]


class SectorSentiment(BaseModel):
    """Sector sentiment response schema."""
    sector: str
    aggregate_score: float
    aggregate_classification: str
    total_articles: int
    bullish_count: int
    bearish_count: int
    neutral_count: int


@router.get("/{ticker}", response_model=SentimentResponse)
def get_ticker_sentiment(ticker: str):
    """
    Get sentiment analysis for a specific ticker.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Sentiment analysis with score, confidence, and classification
    """
    try:
        # Retrieve recent news for ticker
        search_results = get_embedding_service().query_similar(
            query_text=f"news about {ticker} stock",
            n_results=5,
            filter_metadata={"ticker": ticker}
        )
        
        if not search_results["documents"]:
            raise HTTPException(
                status_code=404,
                detail=f"No recent news found for ticker: {ticker}"
            )
        
        # Analyze sentiment for each article
        sentiment_results = sentiment_service.analyze_batch_sentiment(
            search_results["documents"],
            ticker=ticker
        )
        
        # Aggregate sentiment
        aggregate = sentiment_service.aggregate_sentiment(sentiment_results)
        
        # Return primary sentiment with aggregate
        primary_sentiment = sentiment_results[0] if sentiment_results else {
            "sentiment_score": 0.0,
            "confidence": 0.0,
            "classification": "neutral",
            "reasoning": "",
            "key_factors": []
        }
        
        return {
            "ticker": ticker,
            **primary_sentiment,
            "aggregate": aggregate
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing sentiment: {str(e)}"
        )


@router.get("/sector/{sector}", response_model=SectorSentiment)
def get_sector_sentiment(sector: str):
    """
    Get aggregated sentiment for a sector.
    
    Args:
        sector: Sector name (e.g., 'defense', 'banking')
        
    Returns:
        Aggregated sector sentiment
    """
    try:
        # Retrieve recent news for sector
        search_results = get_embedding_service().query_similar(
            query_text=f"{sector} sector news",
            n_results=20
        )
        
        if not search_results["documents"]:
            raise HTTPException(
                status_code=404,
                detail=f"No recent news found for sector: {sector}"
            )
        
        # Analyze sentiment for all articles
        sentiment_results = sentiment_service.analyze_batch_sentiment(
            search_results["documents"]
        )
        
        # Aggregate sentiment
        aggregate = sentiment_service.aggregate_sentiment(sentiment_results)
        
        return {
            "sector": sector,
            **aggregate
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing sector sentiment: {str(e)}"
        )
