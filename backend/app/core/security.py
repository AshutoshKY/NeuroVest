from datetime import datetime, timedelta
from typing import Optional
import re
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength.
    Returns: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        return False, "Password must contain at least one special character"
    
    return True, ""


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token using CURRENT key from key manager.
    Falls back to static key if key manager unavailable.
    """
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + (expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
    
    # CRITICAL: JWT expects exp and iat as integer timestamp, not datetime object
    # iat (issued-at) is used for auth_epoch validation (force logout)
    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),  # Required for auth_epoch validation
        "type": "access"
    })
    
    # Try to use key manager for rotation support
    try:
        from app.core.jwt_key_manager import get_jwt_key_manager
        key_manager = get_jwt_key_manager()
        secret_key = key_manager.get_current_key()
    except Exception as e:
        # Fallback to static key from settings
        from loguru import logger
        logger.warning(f"[JWT] Key manager unavailable, using static key: {e}")
        secret_key = settings.JWT_SECRET_KEY
    
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT refresh token using CURRENT key from key manager.
    Falls back to static key if key manager unavailable.
    """
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + (expires_delta or timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS))
    
    # CRITICAL: JWT expects exp and iat as integer timestamp, not datetime object
    # iat (issued-at) is used for auth_epoch validation (force logout)
    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),  # Required for auth_epoch validation
        "type": "refresh"
    })
    
    # Try to use key manager for rotation support
    try:
        from app.core.jwt_key_manager import get_jwt_key_manager
        key_manager = get_jwt_key_manager()
        secret_key = key_manager.get_current_key()
    except Exception as e:
        # Fallback to static key from settings
        from loguru import logger
        logger.warning(f"[JWT] Key manager unavailable, using static key: {e}")
        secret_key = settings.JWT_SECRET_KEY
    
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token (legacy - use verify_token instead)"""
    return verify_token(token, token_type="access")


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """
    Verify JWT token using any of the 3 valid keys (current, previous_1, previous_2).
    Tries keys in order until one succeeds.
    
    Returns payload if valid, None otherwise.
    """
    from loguru import logger
    
    # Try to use key manager with multiple keys
    verification_keys = []
    try:
        from app.core.jwt_key_manager import get_jwt_key_manager
        key_manager = get_jwt_key_manager()
        verification_keys = key_manager.get_verification_keys()
    except Exception as e:
        # Fallback to static key
        logger.warning(f"[JWT] Key manager unavailable, using static key: {e}")
        verification_keys = [settings.JWT_SECRET_KEY]
    
    # Try each key in order (current → previous_1 → previous_2)
    for i, secret_key in enumerate(verification_keys):
        try:
            payload = jwt.decode(token, secret_key, algorithms=[settings.JWT_ALGORITHM])
            
            # Verify token type
            if payload.get("type") != token_type:
                logger.debug(f"[JWT] Token type mismatch: expected={token_type}, got={payload.get('type')}")
                continue
            
            # Check expiration (with 5-minute grace period for clock skew)
            exp = payload.get("exp")
            if exp:
                exp_dt = datetime.utcfromtimestamp(exp)
                now_dt = datetime.utcnow()
                grace_period = timedelta(minutes=5)
                
                if exp_dt < (now_dt - grace_period):
                    logger.debug(f"[JWT] Token expired: exp={exp_dt}, now={now_dt}")
                    continue
            
            # Log successful verification
            # Determine which key verified (handle case where we only have 1 key pre-rotation)
            if len(verification_keys) == 1:
                key_status = "current"  # Only one key means it's the current key from manager
            else:
                key_status = ["current", "previous_1", "previous_2"][i]
            
            # ========== AUTH EPOCH CHECK (JWT Invalidation) ==========
            # Check if token was issued after current auth_epoch
            # This enables force logout by incrementing the epoch
            try:
                from app.services.session_control import is_token_valid_by_epoch
                token_iat = payload.get("iat")
                if token_iat:
                    if not is_token_valid_by_epoch(token_iat):
                        logger.warning(f"[JWT] ❌ Token invalidated by auth_epoch: iat={token_iat}")
                        continue
                else:
                    # Legacy tokens without iat - allow but log
                    logger.debug("[JWT] Token missing 'iat' claim - skipping epoch check")
            except Exception as e:
                # If epoch check fails, allow token (fail open for availability)
                logger.error(f"[JWT] Auth epoch check failed, allowing token: {e}")
            # ========== END AUTH EPOCH CHECK ==========
            
            logger.debug(f"[JWT] ✅ Token verified with {key_status} key")
            
            # Increment stats (non-critical, ignore errors)
            try:
                if len(verification_keys) > 1:
                    key_manager.increment_verification_stat(key_status)
            except:
                pass
            
            return payload
            
        except JWTError as e:
            # Try next key
            logger.debug(f"[JWT] Verification failed with key {i}: {e}")
            continue
    
    logger.warning(f"[JWT] ❌ Token verification failed with all {len(verification_keys)} keys")
    return None
