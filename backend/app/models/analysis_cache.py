"""
Database model for caching analysis results with enhanced historical tracking.
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, Text
from sqlalchemy.sql import func
from app.core.database import Base

class AnalysisCache(Base):
    """Cache for stock analysis results with full historical tracking."""
    
    __tablename__ = "analysis_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Analysis content (original)
    analysis_json = Column(JSON)  # Full analysis result
    sentiment_score = Column(Float)
    article_count = Column(Integer)
    
    # NEW: Price tracking (at analysis time)
    price = Column(Float)
    previous_close = Column(Float)
    day_high = Column(Float)
    day_low = Column(Float)
    volume = Column(Integer)
    
    # NEW: Technical Indicators (snapshot at analysis time)
    rsi = Column(Float)
    rsi_signal = Column(String(20))  # "Overbought", "Oversold", "Neutral"
    
    macd = Column(Float)
    macd_signal = Column(Float)
    macd_histogram = Column(Float)
    macd_trend = Column(String(20))  # "Bullish", "Bearish"
    
    bb_upper = Column(Float)
    bb_middle = Column(Float)
    bb_lower = Column(Float)
    bb_position = Column(String(50))  # "Above Upper", "Middle", "Below Lower"
    
    # NEW: Prediction tracking
    prediction_text = Column(Text)
    prediction_direction = Column(String(20))  # "Bullish", "Bearish", "Neutral"
    confidence = Column(Float)  # 0.0 to 1.0
    
    # NEW: Risk factors (for later analysis)
    risk_factors_json = Column(JSON)
    key_insights_json = Column(JSON)
    
    def __repr__(self):
        return f"<AnalysisCache {self.ticker} @ {self.timestamp}>"
