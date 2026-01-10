"""
Session Control Service for JWT Invalidation

Implements global auth_epoch-based token invalidation for force logout.

How it works:
1. auth_epoch is stored in Redis (synced from MySQL auth_settings table)
2. All tokens issued have an "iat" (issued-at) timestamp
3. verify_token() checks: token.iat >= auth_epoch
4. To invalidate all tokens: increment auth_epoch to current timestamp
5. All tokens issued before the new epoch become invalid

Future extension:
- Per-user token_version for individual user force logout
- Not implemented now, but designed to be additive
"""

from datetime import datetime, timezone
from typing import Optional
from loguru import logger
import json

from app.core.redis_client import get_redis
from app.core.database import SessionLocal
from sqlalchemy import text


# Redis key for auth epoch (authoritative source during runtime)
AUTH_EPOCH_KEY = "auth:epoch"


def get_auth_epoch() -> int:
    """
    Get the current auth epoch from Redis.
    Falls back to MySQL if not in Redis.
    Returns Unix timestamp.
    """
    try:
        redis = get_redis()
        epoch = redis.get(AUTH_EPOCH_KEY)
        
        if epoch:
            return int(epoch)
        
        # Fallback: load from MySQL and cache in Redis
        return sync_auth_epoch_from_mysql()
        
    except Exception as e:
        logger.error(f"[SESSION_CONTROL] Error getting auth_epoch: {e}")
        # Return a very old epoch as fallback (don't block all logins)
        return 0


def sync_auth_epoch_from_mysql() -> int:
    """
    Load auth_epoch from MySQL and cache in Redis.
    Called on startup and when Redis cache is missing.
    """
    try:
        redis = get_redis()
        db = SessionLocal()
        
        try:
            result = db.execute(
                text("SELECT setting_value FROM auth_settings WHERE setting_key = 'auth_epoch'")
            )
            row = result.fetchone()
            
            if row:
                epoch = int(row[0])
                # Cache in Redis (no expiry - permanent until updated)
                redis.set(AUTH_EPOCH_KEY, str(epoch))
                logger.info(f"[SESSION_CONTROL] Synced auth_epoch from MySQL: {epoch}")
                return epoch
            else:
                # No epoch in DB, create one
                epoch = int(datetime.now(timezone.utc).timestamp())
                db.execute(
                    text("""
                        INSERT INTO auth_settings (setting_key, setting_value)
                        VALUES ('auth_epoch', :epoch)
                    """),
                    {"epoch": str(epoch)}
                )
                db.commit()
                redis.set(AUTH_EPOCH_KEY, str(epoch))
                logger.info(f"[SESSION_CONTROL] Created initial auth_epoch: {epoch}")
                return epoch
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"[SESSION_CONTROL] Error syncing auth_epoch from MySQL: {e}")
        return 0


def increment_auth_epoch() -> int:
    """
    Increment auth_epoch to current timestamp.
    This immediately invalidates ALL existing tokens.
    
    Returns the new epoch value.
    """
    try:
        redis = get_redis()
        db = SessionLocal()
        
        try:
            # New epoch is current timestamp
            new_epoch = int(datetime.now(timezone.utc).timestamp())
            
            # Update MySQL (source of truth for persistence)
            db.execute(
                text("""
                    UPDATE auth_settings 
                    SET setting_value = :epoch, updated_at = NOW()
                    WHERE setting_key = 'auth_epoch'
                """),
                {"epoch": str(new_epoch)}
            )
            db.commit()
            
            # Update Redis (authoritative during runtime)
            redis.set(AUTH_EPOCH_KEY, str(new_epoch))
            
            logger.warning(f"[SESSION_CONTROL] ⚠️ AUTH EPOCH INCREMENTED: {new_epoch} - All tokens invalidated!")
            
            return new_epoch
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"[SESSION_CONTROL] Failed to increment auth_epoch: {e}")
        raise


def is_token_valid_by_epoch(token_iat: int) -> bool:
    """
    Check if a token's issued-at time is valid against current auth_epoch.
    
    Args:
        token_iat: The "iat" claim from the JWT (Unix timestamp)
        
    Returns:
        True if token was issued after current epoch, False otherwise
    """
    current_epoch = get_auth_epoch()
    
    # Token is valid if it was issued at or after the current epoch
    is_valid = token_iat >= current_epoch
    
    if not is_valid:
        logger.debug(
            f"[SESSION_CONTROL] Token rejected: iat={token_iat} < epoch={current_epoch}"
        )
    
    return is_valid


# === Future Extension (not implemented now) ===
# Per-user token_version for individual force logout
#
# Redis key: auth:user:{user_id}:token_version
# Check in verify_token: token.token_version >= user's current token_version
# To force logout user: increment their token_version
#
# This is designed to be additive - implement when needed


def get_session_control_status() -> dict:
    """
    Get current session control status for admin dashboard.
    """
    try:
        epoch = get_auth_epoch()
        epoch_dt = datetime.fromtimestamp(epoch, tz=timezone.utc)
        
        return {
            "auth_epoch": epoch,
            "auth_epoch_iso": epoch_dt.isoformat(),
            "invalidation_method": "global_epoch",
            "per_user_logout_enabled": False,  # Future feature
        }
    except Exception as e:
        logger.error(f"[SESSION_CONTROL] Error getting status: {e}")
        return {
            "auth_epoch": 0,
            "auth_epoch_iso": None,
            "invalidation_method": "global_epoch",
            "per_user_logout_enabled": False,
            "error": str(e)
        }
