import pytest
from unittest.mock import MagicMock, patch
from app.services.sentiment import SentimentService

@pytest.fixture
def sentiment_service():
    return SentimentService()

@pytest.mark.asyncio
async def test_analyze_news_sentiment_positive(sentiment_service):
    """Test sentiment analysis logic (Mocking NewsAPI/LLM)"""
    
    # Mock the internal fetch method
    with patch.object(sentiment_service, '_fetch_news', return_value=[
        {"title": "Stock hits all time high", "summary": "Great earnings report"}
    ]):
        # Mock VADER or LLM analyzer
        with patch.object(sentiment_service, '_analyze_text', return_value=0.8):
            
            score, summary = await sentiment_service.analyze_ticker("AAPL")
            
            assert score > 0
            assert "positive" in str(summary).lower() or score > 0.5

@pytest.mark.asyncio
async def test_analyze_news_sentiment_no_news(sentiment_service):
    """Test handling of no news found"""
    with patch.object(sentiment_service, '_fetch_news', return_value=[]):
        score, summary = await sentiment_service.analyze_ticker("UNKNOWN")
        
        assert score == 0
        assert "no news" in str(summary).lower()
