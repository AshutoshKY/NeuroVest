from pydantic import BaseModel
from typing import List, Optional

class BulkWatchlistRequest(BaseModel):
    """Request model for bulk watchlist data fetch"""
    tickers: List[str]

class StockDataResponse(BaseModel):
    """Individual stock data response"""
    ticker: str
    name: str
    current_price: float
    currency: str
    day_change: float
    day_change_percent: float
    day_high: float
    day_low: float
    volume: int
    market_cap: float
    pe_ratio: Optional[float] = None
    exchange: str
    market_status: str
    provider: str
    timestamp: str

class BulkWatchlistResponse(BaseModel):
    """Response model for bulk watchlist data"""
    stocks: List[StockDataResponse]
    cached_count: int
    fetched_count: int
    failed: List[str]
    total_time_ms: float
