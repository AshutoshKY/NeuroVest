from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.services.embeddings import get_embedding_service

router = APIRouter(prefix="/news", tags=["news"])


class NewsArticle(BaseModel):
    """News article schema."""
    title: str
    source: str
    timestamp: str
    ticker: str
    url: str
    snippet: str


class NewsFeed(BaseModel):
    """News feed response schema."""
    articles: List[NewsArticle]
    total: int


@router.get("/feed", response_model=NewsFeed)
def get_news_feed(
    ticker: Optional[str] = Query(None, description="Filter by ticker"),
    limit: int = Query(20, ge=1, le=100, description="Number of articles to return")
):
    """
    Get personalized news feed.
    
    Args:
        ticker: Optional ticker filter
        limit: Number of articles to return
        
    Returns:
        News feed with articles
    """
    try:
        # Build filter
        filter_metadata = {"ticker": ticker} if ticker else None
        
        # Query recent news
        search_results = get_embedding_service().query_similar(
            query_text="latest market news",
            n_results=limit,
            filter_metadata=filter_metadata
        )
        
        # Format articles
        articles = []
        for doc, metadata in zip(search_results["documents"], search_results["metadatas"]):
            articles.append({
                "title": metadata.get("title", ""),
                "source": metadata.get("source", ""),
                "timestamp": metadata.get("timestamp", ""),
                "ticker": metadata.get("ticker", ""),
                "url": metadata.get("url", ""),
                "snippet": doc[:200] + "..." if len(doc) > 200 else doc
            })
        
        return {
            "articles": articles,
            "total": len(articles)
        }
        
    except Exception as e:
        return {
            "articles": [],
            "total": 0
        }


@router.get("/{ticker}", response_model=NewsFeed)
def get_ticker_news(
    ticker: str,
    limit: int = Query(10, ge=1, le=50, description="Number of articles to return")
):
    """
    Get news for a specific ticker.
    
    Args:
        ticker: Stock ticker symbol
        limit: Number of articles to return
        
    Returns:
        News articles for the ticker
    """
    return get_news_feed(ticker=ticker, limit=limit)
