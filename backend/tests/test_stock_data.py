import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.data_ingestion import DataIngestionService

@pytest.fixture
def ingestion_service():
    return DataIngestionService()

@pytest.mark.asyncio
async def test_fetch_stock_data_success(ingestion_service):
    """Test fetching stock data from external API (Mocked)"""
    
    mock_ticker_data = MagicMock()
    mock_ticker_data.info = {
        "regularMarketPrice": 150.0,
        "dayHigh": 155.0,
        "dayLow": 149.0,
        "volume": 1000000
    }
    # Mock history dataframe
    mock_hist = MagicMock()
    mock_hist.empty = False
    mock_ticker_data.history.return_value = mock_hist
    
    with patch("yfinance.Ticker", return_value=mock_ticker_data) as mock_yf:
        data = await ingestion_service.fetch_stock_data("AAPL")
        
        assert data["current_price"] == 150.0
        assert data["day_high"] == 155.0
        assert data["day_low"] == 149.0
        
        mock_yf.assert_called_with("AAPL")

@pytest.mark.asyncio
async def test_fetch_stock_data_failure(ingestion_service):
    """Test handling of invalid ticker"""
    
    mock_ticker_data = MagicMock()
    mock_ticker_data.info = {} # Empty info
    
    with patch("yfinance.Ticker", return_value=mock_ticker_data):
        with pytest.raises(Exception):
            await ingestion_service.fetch_stock_data("INVALID")
