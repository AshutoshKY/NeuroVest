from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, Enum as SQLEnum, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    """
    User role enumeration.
    - USER: Regular user with standard access
    - ADMIN: Read-only monitoring access (can view admin dashboard, cannot mutate)
    - SUPER_ADMIN: Full admin access including dangerous operations (kill switches, force logout)
    """
    USER = "user"  # lowercase to match MySQL enum
    ADMIN = "admin"  # lowercase to match MySQL enum
    SUPER_ADMIN = "super_admin"  # New role for dangerous operations


class User(Base):
    """User model for authentication and personalization."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    
    # Authentication & Authorization
    # Using String instead of SQLEnum to avoid MySQL enum type conflicts
    role = Column(String(15), default=UserRole.USER.value, nullable=False, index=True)  # Increased for 'super_admin'
    is_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Account lockout (security)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # User preferences
    watchlist = Column(JSON, default=list)  # List of ticker symbols
    risk_appetite = Column(String(50), default="moderate")  # low, moderate, high
    trading_style = Column(String(50), default="long-term")  # intraday, swing, long-term
    preferred_sectors = Column(JSON, default=list)  # List of sectors
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    login_history = relationship("LoginHistory", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.email}>"
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin or super_admin role (can view admin dashboard)"""
        return self.role in (UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value, "admin", "super_admin")
    
    @property
    def is_super_admin(self) -> bool:
        """Check if user has super_admin role (can perform dangerous operations)"""
        return self.role in (UserRole.SUPER_ADMIN.value, "super_admin")
    
    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked"""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    def to_dict(self):
        """Convert user to dictionary (without sensitive data)"""
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role.value,
            "is_verified": self.is_verified,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class RefreshToken(Base):
    """Refresh token model for JWT token management with session tracking"""
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    token = Column(String(500), nullable=False, index=True, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    revoked = Column(Boolean, default=False, nullable=False)
    
    # Session tracking fields
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    device_type = Column(String(50), nullable=True)  # Mobile, Desktop, Tablet, Bot
    os = Column(String(100), nullable=True)  # iOS 15.0, Windows 11, etc.
    browser = Column(String(100), nullable=True)  # Chrome 108, Safari 16.1, etc.
    device_name = Column(String(150), nullable=True)  # iPhone 12, Windows PC, etc.
    
    # Relationships
    user = relationship("User", back_populates="refresh_tokens")
    
    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, device={self.device_name}, revoked={self.revoked})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not revoked)"""
        return not self.revoked and not self.is_expired
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "device_type": self.device_type,
            "device_name": self.device_name,
            "os": self.os,
            "browser": self.browser,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }


class LoginHistory(Base):
    """Login history tracking for security monitoring"""
    __tablename__ = "login_history"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Timestamp
    login_time = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    logout_time = Column(DateTime(timezone=True), nullable=True)
    
    # Network information
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    
    # Device information
    user_agent = Column(Text, nullable=True)
    device_type = Column(String(50), nullable=True)  # Mobile, Desktop, Tablet, Bot
    os = Column(String(100), nullable=True)  # iOS 15.0, Windows 11, etc.
    browser = Column(String(100), nullable=True)  # Chrome 108, Safari 16.1, etc.
    device_name = Column(String(150), nullable=True)  # iPhone 12, Windows PC, etc.
    
    # Geolocation
    location_city = Column(String(100), nullable=True)
    location_region = Column(String(100), nullable=True)
    location_country = Column(String(100), nullable=True)
    location_lat = Column(Float, nullable=True)
    location_lon = Column(Float, nullable=True)
    
    # Session tracking
    session_id = Column(String(255), nullable=True, index=True)
    device_token = Column(String(255), nullable=True)
    
    # Login status
    login_success = Column(Boolean, nullable=False, default=True)
    failure_reason = Column(String(255), nullable=True)  # If login_success = False
    
    # Relationships
    user = relationship("User", back_populates="login_history")
    
    def __repr__(self):
        status = "SUCCESS" if self.login_success else "FAILED"
        return f"<LoginHistory(id={self.id}, user_id={self.user_id}, status={status}, time={self.login_time})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "login_time": self.login_time.isoformat() if self.login_time else None,
            "logout_time": self.logout_time.isoformat() if self.logout_time else None,
            "ip_address": self.ip_address,
            "device_type": self.device_type,
            "device_name": self.device_name,
            "os": self.os,
            "browser": self.browser,
            "location": self.format_location(),
            "location_country": self.location_country,
            "login_success": self.login_success,
            "failure_reason": self.failure_reason
        }
    
    def format_location(self) -> str:
        """Format location as a readable string"""
        parts = []
        if self.location_city:
            parts.append(self.location_city)
        if self.location_region:
            parts.append(self.location_region)
        if self.location_country:
            parts.append(self.location_country)
        
        if parts:
            return ", ".join(parts)
        return "Unknown Location"
