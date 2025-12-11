"""
SQLAlchemy model for JWT key rotation storage.
Stores JWT signing keys with dual Redis+SQL persistence for graceful restarts.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import enum

from app.core.database import Base


class KeyStatus(str, enum.Enum):
    """JWT key status lifecycle"""
    CURRENT = "current"      # Active signing key
    PREVIOUS_1 = "previous_1"  # Valid for verification (1 rotation ago)
    PREVIOUS_2 = "previous_2"  # Valid for verification (2 rotations ago)
    EXPIRED = "expired"      # No longer valid


class JWTKey(Base):
    """
    JWT signing key with rotation support.
    
    Lifecycle:
    - New key: status=CURRENT, used for signing
    - After 24hrs rotation: CURRENT -> PREVIOUS_1
    - After 48hrs: PREVIOUS_1 -> PREVIOUS_2
    - After 72hrs: PREVIOUS_2 -> EXPIRED (deleted from Redis)
    
    This ensures tokens valid for 24hrs can be verified even after 2 rotations.
    """
    __tablename__ = "jwt_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key_id = Column(
        String(50), 
        unique=True, 
        nullable=False,
        comment="Unique identifier (e.g., '2024-12-11T18:00:00Z')"
    )
    secret_key = Column(
        Text, 
        nullable=False,
        comment="Base64-encoded JWT secret (urlsafe)"
    )
    status = Column(
        Enum(KeyStatus),
        nullable=False,
        default=KeyStatus.CURRENT,
        index=True,
        comment="Key lifecycle status"
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="When key was generated"
    )
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="When key becomes invalid (created_at + 72hrs)"
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Soft delete flag"
    )
    last_used_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last time this key verified a token"
    )
    
    def __repr__(self):
        return f"<JWTKey(key_id={self.key_id}, status={self.status}, created_at={self.created_at})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if key has expired"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def age_hours(self) -> float:
        """Get age of key in hours"""
        delta = datetime.utcnow() - self.created_at
        return delta.total_seconds() / 3600
    
    def to_dict(self):
        """Convert to dictionary for Redis storage"""
        return {
            "key_id": self.key_id,
            "secret_key": self.secret_key,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "is_active": self.is_active
        }
