"""
Security API endpoints
Handles login history and active session management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Dict
from loguru import logger

from app.core.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.services.login_tracker import LoginTracker


router = APIRouter(prefix="/security", tags=["security"])


def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_current_token_id_from_cookie(request: Request, db: Session) -> int:
    """Extract current refresh token ID from cookie"""
    from app.models.user import RefreshToken
    
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        return None
    
    token_record = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token
    ).first()
    
    return token_record.id if token_record else None


@router.get("/login-history", response_model=List[Dict])
async def get_login_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get login history for the current user
    
    - Shows last 50 login attempts (successful and failed)
    - Includes device info, location, and IP address
    - Ordered by most recent first
    """
    try:
        history = await LoginTracker.get_login_history(
            db=db,
            user_id=current_user.id,
            limit=limit
        )
        
        logger.info(f"[SECURITY_API] Fetched {len(history)} login history records for user {current_user.id}")
        return history
        
    except Exception as e:
        logger.error(f"[SECURITY_API] Error fetching login history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch login history"
        )


@router.get("/active-sessions", response_model=List[Dict])
async def get_active_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get active sessions for the current user
    
    - Shows all active (non-revoked, non-expired) sessions
    - Includes device info, location, last activity
    - Marks current session with 'is_current' flag
    """
    try:
        sessions = await LoginTracker.get_active_sessions(
            db=db,
            user_id=current_user.id
        )
        
        # Mark current session
        current_token_id = get_current_token_id_from_cookie(request, db)
        for session in sessions:
            session['is_current'] = (session['id'] == current_token_id)
        
        logger.info(f"[SECURITY_API] Fetched {len(sessions)} active sessions for user {current_user.id}")
        return sessions
        
    except Exception as e:
        logger.error(f"[SECURITY_API] Error fetching active sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch active sessions"
        )


@router.post("/revoke-session/{token_id}")
async def revoke_session(
    token_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke a specific session
    
    - Cannot revoke the current session (use logout instead)
    - Only user can revoke their own sessions
    """
    try:
        # Check if trying to revoke current session
        current_token_id = get_current_token_id_from_cookie(request, db)
        if token_id == current_token_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot revoke current session. Use logout instead."
            )
        
        success = await LoginTracker.revoke_session(
            db=db,
            user_id=current_user.id,
            token_id=token_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or already revoked"
            )
        
        logger.info(f"[SECURITY_API] User {current_user.id} revoked session {token_id}")
        
        return {
            "ok": True,
            "message": "Session revoked successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SECURITY_API] Error revoking session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke session"
        )


@router.post("/revoke-all-sessions")
async def revoke_all_other_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke all sessions except the current one
    
    - Useful for "logout from all other devices"
    - Keeps current session active
    """
    try:
        current_token_id = get_current_token_id_from_cookie(request, db)
        
        if not current_token_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not identify current session"
            )
        
        count = await LoginTracker.revoke_all_other_sessions(
            db=db,
            user_id=current_user.id,
            current_token_id=current_token_id
        )
        
        logger.info(f"[SECURITY_API] User {current_user.id} revoked {count} other sessions")
        
        return {
            "ok": True,
            "message": f"Successfully logged out from {count} other device(s)",
            "revoked_count": count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SECURITY_API] Error revoking all sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke sessions"
        )
