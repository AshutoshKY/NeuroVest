"""
Database model for time-series technical indicator storage.
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Index
from sqlalchemy.sql import func
from app.core.database import Base

class TechnicalIndicatorHistory(Base):
    """Time-series storage of technical indicators for pattern analysis."""
    
    __tablename__ = "technical_indicator_history"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), index=True)
    timestamp = Column(DateTime(timezone=True), index=True)
    
    # OHLCV Data
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Integer)
    
    # Technical Indicators
    rsi_14 = Column(Float)
    rsi_signal = Column(String(20))
    
    macd = Column(Float)
    macd_signal = Column(Float)
    macd_histogram = Column(Float)
    
    bb_upper = Column(Float)
    bb_middle = Column(Float)
    bb_lower = Column(Float)
    bb_width = Column(Float)  # Volatility measure
    
    # Composite index for efficient time-series queries
    __table_args__ = (
        Index('idx_ticker_timestamp', 'ticker', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<TechnicalIndicatorHistory {self.ticker} @ {self.timestamp}>"
