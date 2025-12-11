"""
Authentication API endpoints
Handles user registration, login, logout, token refresh, and user info
Production-ready with request tracking, rate limiting, and CORS support
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from loguru import logger

from app.core.database import get_db
from app.core.security import (
    get_password_hash,
    verify_password,
    validate_password_strength,
    create_access_token,
    create_refresh_token,
    verify_token
)
from app.models.user import User, UserRole, RefreshToken
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token, RefreshTokenRequest
from app.middleware.auth_middleware import get_current_user, get_current_admin
from app.utils.aes_decryption import get_aes_decryptor
from app.services.login_tracker import LoginTracker
from app.utils.device_parser import DeviceParser



router = APIRouter(tags=["authentication"])


def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    - Validates password strength
    - Checks for duplicate email
    - Creates user with hashed password
    - Tracks registration IP and details
    """
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "unknown")
    
    # Get raw JSON body
    try:
        raw_data = await request.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    
    # Decrypt if encrypted
    if any(key.endswith('_encrypted') for key in raw_data.keys()):
        logger.debug(f"[AUTH] Encrypted registration payload detected, decrypting...")
        decryptor = get_aes_decryptor()
        raw_data = decryptor.decrypt_auth_payload(raw_data)
    
    # Now validate with Pydantic
    try:
        user_data = UserCreate(**raw_data)
    except Exception as e:
        logger.error(f"[AUTH] Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    
    logger.info(f"[AUTH] Registration attempt: email={user_data.email}, ip={client_ip}")
    
    # Validate password strength
    is_valid, error_msg = validate_password_strength(user_data.password)
    if not is_valid:
        logger.warning(f"[AUTH] Weak password for {user_data.email}: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        logger.warning(f"[AUTH] Duplicate registration attempt: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=UserRole.USER,
        is_verified=False,  # TODO: Implement email verification
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"[AUTH] User registered successfully: id={new_user.id}, email={new_user.email}, ip={client_ip}")
    
    # TODO: Send verification email
    
    return new_user


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.
    
    - Verifies credentials
    - Implements account lockout after 5 failed attempts
    - Creates access and refresh tokens
    - Tracks login IP and device info
    """
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "unknown")
    
    # Get raw JSON body
    try:
        raw_data = await request.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    
    # Decrypt if encrypted
    if any(key.endswith('_encrypted') for key in raw_data.keys()):
        logger.debug(f"[AUTH] Encrypted login payload detected, decrypting...")
        decryptor = get_aes_decryptor()
        raw_data = decryptor.decrypt_auth_payload(raw_data)
    
    # Validate with Pydantic
    try:
        credentials = UserLogin(**raw_data)
    except Exception as e:
        logger.error(f"[AUTH] Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    
    logger.info(f"[AUTH] Login attempt: email={credentials.email}, ip={client_ip}")
    
    # Get user
    user = db.query(User).filter(User.email == credentials.email).first()
    
    # Check if user exists
    if not user:
        logger.warning(f"[AUTH] Login failed - user not found: {credentials.email}")
        # Record failed login
        try:
            await LoginTracker.record_login_attempt(
                db=db,
                user_id=None,  # User not found
                ip_address=client_ip,
                user_agent=user_agent,
                success=False,
                failure_reason="Invalid email"
            )
        except Exception as e:
            logger.error(f"[AUTH] Error recording failed login: {e}")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if account is locked
    if user.is_locked:
        logger.warning(f"[AUTH] Login attempt on locked account: {user.email}, locked_until={user.locked_until}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account locked due to multiple failed attempts. Try again after {user.locked_until.isoformat()}"
        )
    
    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        # Increment failed attempts
        user.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            logger.warning(f"[AUTH] Account locked after 5 failed attempts: {user.email}")
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account locked due to multiple failed login attempts. Try again in 30 minutes."
            )
        
        db.commit()
        logger.warning(f"[AUTH] Invalid password for {user.email}, attempts={user.failed_login_attempts}")
        
        # Record failed login
        try:
            await LoginTracker.record_login_attempt(
                db=db,
                user_id=user.id,
                ip_address=client_ip,
                user_agent=user_agent,
                success=False,
                failure_reason="Invalid password"
            )
        except Exception as e:
            logger.error(f"[AUTH] Error recording failed login: {e}")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        logger.warning(f"[AUTH] Inactive user login attempt: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    # Reset failed attempts on successful login
    user.failed_login_attempts = 0
    user.locked_until = None
    
    # Create tokens (role is already a string, not enum)
    # CRITICAL: sub (user_id) must be string per JWT spec
    token_data = {"sub": str(user.id), "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token_str = create_refresh_token(token_data)
    
    # Parse device information
    device_info = DeviceParser.parse_user_agent(user_agent)
    
    # Store refresh token in database with device info
    refresh_token = RefreshToken(
        user_id=user.id,
        token=refresh_token_str,
        expires_at=datetime.utcnow() + timedelta(days=7),
        ip_address=client_ip,
        device_type=device_info.get('device_type'),
        os=device_info.get('os'),
        browser=device_info.get('browser'),
        device_name=device_info.get('device_name')
    )
    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)
    
    # Record successful login in history
    try:
        await LoginTracker.record_login_attempt(
            db=db,
            user_id=user.id,
            ip_address=client_ip,
            user_agent=user_agent,
            success=True,
            session_id=request.headers.get("X-Session-ID"),
            device_token=request.headers.get("X-Device-Token")
        )
        
        # Enforce session limit (max 2 active sessions)
        await LoginTracker.enforce_session_limit(db, user.id, refresh_token.id)
    except Exception as e:
        logger.error(f"[AUTH] Error in login tracking: {e}")
        # Don't fail login if tracking fails
    
    logger.info(f"[AUTH] Login successful: user_id={user.id}, email={user.email}, device={device_info.get('device_name')}, ip={client_ip}")
    
    # Create response
    from fastapi.responses import JSONResponse
    response = JSONResponse(content={
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer"
    })
    
    # Set tokens as httpOnly cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=24 * 60 * 60  # 24 hours (matches JWT expiration)
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token_str,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=7 * 24 * 60 * 60  # 7 days
    )
    
    return response


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    response: Response,
    token_request: RefreshTokenRequest = None,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    - Reads refresh token from httpOnly cookie (or request body as fallback)
    - Validates refresh token
    - Checks if token is revoked
    - Issues new access and refresh tokens
    """
    client_ip = get_client_ip(request)
    
    # Get refresh token from cookie (preferred) or request body (fallback)
    refresh_token_value = request.cookies.get("refresh_token")
    if not refresh_token_value and token_request:
        refresh_token_value = token_request.refresh_token
    
    if not refresh_token_value:
        logger.warning(f"[AUTH] No refresh token provided from ip={client_ip}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided"
        )
    
    # Verify refresh token
    payload = verify_token(refresh_token_value, token_type="refresh")
    if not payload:
        logger.warning(f"[AUTH] Invalid refresh token from ip={client_ip}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Check if token exists and is not revoked
    stored_token = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token_value
    ).first()
    
    if not stored_token or not stored_token.is_valid:
        logger.warning(f"[AUTH] Revoked or expired refresh token used")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid or has been revoked"
        )
    
    # Get user
    user = db.query(User).filter(User.id == stored_token.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    token_data = {"sub": str(user.id), "role": user.role}
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
    
    # Preserve session information from old token
    old_device_info = {
        'ip_address': stored_token.ip_address,
        'device_type': stored_token.device_type,
        'os': stored_token.os,
        'browser': stored_token.browser,
        'device_name': stored_token.device_name
    }
    
    # Delete old refresh token to prevent duplicate key error
    # (Since token content is deterministic, same user data = same token)
    db.delete(stored_token)
    db.flush()  # Ensure deletion happens before insert
    
    # Store new refresh token with preserved device info
    new_token_record = RefreshToken(
        user_id=user.id,
        token=new_refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=7),
        ip_address=old_device_info['ip_address'],
        device_type=old_device_info['device_type'],
        os=old_device_info['os'],
        browser=old_device_info['browser'],
        device_name=old_device_info['device_name']
    )
    db.add(new_token_record)
    db.commit()
    db.refresh(new_token_record)
    
    # Update session activity
    try:
        user_agent = request.headers.get("User-Agent", "unknown")
        await LoginTracker.update_session_info(
            db=db,
            token_id=new_token_record.id,
            ip_address=client_ip,
            user_agent=user_agent
        )
    except Exception as e:
        logger.error(f"[AUTH] Error updating session info: {e}")
    
    logger.info(f"[AUTH] Token refreshed: user_id={user.id}, email={user.email}")
    
    # Create response with new tokens in cookies
    from fastapi.responses import JSONResponse
    json_response = JSONResponse(content={
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    })
    
    # Set new tokens as httpOnly cookies
    json_response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=24 * 60 * 60  # 24 hours (matches JWT expiration)
    )
    
    json_response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=7 * 24 * 60 * 60  # 7 days
    )
    
    return json_response


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout user by revoking refresh token.
    Reads refresh_token from httpOnly cookie.
    """
    # Get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")
    
    if refresh_token:
        # Revoke refresh token
        token = db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token,
            RefreshToken.user_id == current_user.id
        ).first()
        
        if token:
            token.revoked = True
            db.commit()
    
    # Clear cookies
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    
    logger.info(f"[AUTH] User logged out: user_id={current_user.id}")
    
    return {
        "ok": True,
        "message": "Logged out successfully"
    }


@router.patch("/update-profile", response_model=UserResponse)
async def update_profile(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update user profile (full_name)
    """
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    
    full_name = data.get('full_name')
    if not full_name or not full_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Full name is required"
        )
    
    # Update user
    current_user.full_name = full_name.strip()
    db.commit()
    db.refresh(current_user)
    
    logger.info(f"[AUTH] Profile updated for user_id={current_user.id}")
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_verified=current_user.is_verified,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


@router.patch("/change-password")
async def change_password(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Change user password
    """
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    
    # Decrypt if encrypted
    if any(key.endswith('_encrypted') for key in data.keys()):
        logger.debug(f"[AUTH] Encrypted password change payload detected, decrypting...")
        decryptor = get_aes_decryptor()
        data = decryptor.decrypt_auth_payload(data)
    
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password and new password are required"
        )
    
    # Verify current password
    if not verify_password(current_password, current_user.hashed_password):
        logger.warning(f"[AUTH] Incorrect current password for user_id={current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password strength
    is_valid, error_msg = validate_password_strength(new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    logger.info(f"[AUTH] Password changed for user_id={current_user.id}")
    
    return {
        "ok": True,
        "message": "Password updated successfully"
    }


@router.delete("/delete-account")
async def delete_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Permanently delete user account and all associated data
    """
    user_id = current_user.id
    email = current_user.email
    
    # Delete user (cascade will handle related data)
    db.delete(current_user)
    db.commit()
    
    logger.info(f"[AUTH] Account deleted: user_id={user_id}, email={email}")
    
    return {
        "ok": True,
        "message": "Account deleted successfully"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information.
    """
    return current_user


@router.get("/admin/users", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    List all users (admin only).
    """
    users = db.query(User).offset(skip).limit(limit).all()
    logger.info(f"[AUTH] Admin {current_user.email} listed users")
    return users
