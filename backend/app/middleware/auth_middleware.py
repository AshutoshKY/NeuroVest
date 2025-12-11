"""
Authentication middleware for JWT verification and user context
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User, UserRole


# HTTP Bearer security scheme
security = HTTPBearer()


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    Checks cookies first, then Authorization header.
    Raises 401 if token is invalid or user not found.
    """
    # Try to get token from cookie first
    token = request.cookies.get("access_token")
    
    # If not in cookie, try Authorization header
    if not token and credentials:
        token = credentials.credentials
    
    # If still no token, raise error
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify token
    payload = verify_token(token, token_type="access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user_id from payload
    user_id: int = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Check if account is locked
    if user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account locked until {user.locked_until.isoformat()}"
        )
    
    # Attach user to request state for logging/tracking
    request.state.user = user
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current active user.
    Additional check for active status.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current admin user.
    Raises 403 if user is not admin.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_optional_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to get current user if authenticated, None otherwise.
    Reads JWT from httpOnly cookies (not Authorization header).
    Useful for endpoints that work with or without authentication.
    """
    # Try to get access_token from cookies
    token = request.cookies.get("access_token")
    
    if not token:
        return None
    
    try:
        payload = verify_token(token, token_type="access")
        if not payload:
            return None
        
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
        
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.is_active and not user.is_locked:
            request.state.user = user
            return user
        
        return None
    except Exception as e:
        # Log the exception for debugging
        from loguru import logger
        logger.debug(f"[get_optional_user] Exception: {e}")
        return None
