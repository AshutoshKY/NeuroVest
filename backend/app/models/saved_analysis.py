"""Saved Analysis Model - Allows users to save up to 10 analysis results."""
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class SavedAnalysis(Base):
    """Saved stock analysis for users."""
    __tablename__ = "saved_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_email = Column(String(255), ForeignKey('users.email', ondelete='CASCADE'), nullable=False)
    ticker = Column(String(20), nullable=False)
    title = Column(String(100), nullable=True)  # Optional custom title
    analysis_data = Column(JSON, nullable=False)  # Full analysis result
    saved_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Indexes
    __table_args__ = (
        Index('idx_saved_analyses_user', 'user_email'),
        Index('idx_saved_analyses_saved_at', 'saved_at'),
        # Removed unique constraint to allow multiple analyses per stock
    )

    def to_dict(self):
        """Convert to dictionary."""
        # Extract key info from analysis_data for list view
        analysis = self.analysis_data or {}
        
        # Extract confidence from nested sentiment object
        sentiment_data = analysis.get("sentiment", {})
        if isinstance(sentiment_data, dict):
            confidence = sentiment_data.get("average_confidence") or sentiment_data.get("confidence") or analysis.get("confidence") or 0
        else:
            confidence = analysis.get("confidence", 0)
        
        return {
            "id": str(self.id),
            "ticker": self.ticker,
            "name": analysis.get("name", self.ticker),  # Stock name from analysis data
            "title": self.title,
            "sentiment": sentiment_data.get("classification") if isinstance(sentiment_data, dict) else analysis.get("sentiment", "Unknown"),
            "price": analysis.get("price") or analysis.get("current_price", 0),
            "currency": analysis.get("currency", "INR"),
            "confidence": confidence,
            "analysis_data": analysis,  # Include for frontend access
            "saved_at": self.saved_at.isoformat() if self.saved_at else None,
        }

    def to_full_dict(self):
        """Convert to full dictionary including all analysis data."""
        return {
            **self.to_dict(),
            "analysis_data": self.analysis_data
        }
