from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Watchlist(Base):
    """User watchlist for tracking stocks"""
    __tablename__ = "watchlist"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    ticker = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    exchange = Column(String(50))
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def to_dict(self):
        return {
            "id": self.id,
            "ticker": self.ticker,
            "name": self.name,
            "exchange": self.exchange,
            "added_at": self.added_at.isoformat() if self.added_at else None
        }


class Favourite(Base):
    """User favourite stocks"""
    __tablename__ = "favourites"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    ticker = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    exchange = Column(String(50))
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def to_dict(self):
        return {
            "id": self.id,
            "ticker": self.ticker,
            "name": self.name,
            "exchange": self.exchange,
            "added_at": self.added_at.isoformat() if self.added_at else None
        }


class AnalysisHistory(Base):
    """User analysis history - uses existing analysis_history table"""
    __tablename__ = "analysis_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)  # Can be null for guest analyses
    ticker = Column(String(20), nullable=False)
    name = Column(String(255), nullable=True)
    analysis_data = Column(JSON, nullable=True)
    created_at = Column('timestamp', DateTime(timezone=True), server_default=func.now())  # Map timestamp to created_at
    
    def to_dict(self):
        return {
            "id": self.id,
            "ticker": self.ticker,
            "name": self.name,
            "analysis_data": self.analysis_data,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
