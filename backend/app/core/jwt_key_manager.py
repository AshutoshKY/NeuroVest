"""
JWT Key Manager - Central coordination for key rotation with dual Redis+SQL storage.

This module manages the lifecycle of JWT signing keys:
- Stores keys in both Redis (fast) and MySQL (persistent)
- Maintains 3 active keys: current, previous_1, previous_2
- Rotates keys every 24 hours when users are active
- Ensures seamless backend restarts without user logout
"""
import secrets
import base64
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from redis.exceptions import RedisError

from app.core.database import SessionLocal
from app.core.redis_client import get_redis
from app.models.jwt_key import JWTKey, KeyStatus


class JWTKeyManager:
    """
    Manages JWT signing keys with dual Redis+SQL storage.
    Supports graceful key rotation without user logout.
    """
    
    # Redis key constants
    REDIS_KEY_CURRENT = "jwt:keys:current"
    REDIS_KEY_PREVIOUS_1 = "jwt:keys:previous_1"
    REDIS_KEY_PREVIOUS_2 = "jwt:keys:previous_2"
    REDIS_LAST_ROTATION = "jwt:keys:last_rotation"
    REDIS_STATS_PREFIX = "jwt:stats:verifications:"
    
    # Key TTL constants
    KEY_ROTATION_HOURS = 24
    KEY_EXPIRY_HOURS = 72  # 3 rotations (24 * 3)
    
    def __init__(self):
        """Initialize JWT Key Manager"""
        self.redis = get_redis()
        self._db = None
    
    @property
    def db(self) -> Session:
        """Lazy database session"""
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    def __del__(self):
        """Cleanup database session"""
        if self._db:
            self._db.close()
    
    # ==================== KEY GENERATION ====================
    
    def _generate_secret_key(self) -> str:
        """
        Generate cryptographically secure JWT secret key.
        Returns: Base64-encoded urlsafe secret (256 bits)
        """
        random_bytes = secrets.token_bytes(32)  # 256 bits
        return base64.urlsafe_b64encode(random_bytes).decode('utf-8')
    
    def _create_key_id(self) -> str:
        """
        Create unique key identifier from timestamp.
        Format: YYYY-MM-DDTHH:MM:SSZ
        """
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # ==================== STORAGE OPERATIONS ====================
    
    def _store_in_redis(self, key_data: Dict, status: KeyStatus) -> None:
        """Store key in Redis with appropriate key name"""
        redis_key = {
            KeyStatus.CURRENT: self.REDIS_KEY_CURRENT,
            KeyStatus.PREVIOUS_1: self.REDIS_KEY_PREVIOUS_1,
            KeyStatus.PREVIOUS_2: self.REDIS_KEY_PREVIOUS_2
        }.get(status)
        
        if not redis_key:
            logger.warning(f"[JWT_KEYS] Invalid status for Redis storage: {status}")
            return
        
        try:
            # Store as JSON with 7-day TTL (longer than any key lifecycle)
            self.redis.setex(
                redis_key,
                7 * 24 * 60 * 60,  # 7 days
                json.dumps(key_data)
            )
            logger.debug(f"[JWT_KEYS] Stored {status.value} key in Redis: {redis_key}")
        except RedisError as e:
            logger.error(f"[JWT_KEYS] Failed to store in Redis: {e}")
            # Don't raise - SQL is primary storage, Redis is cache
    
    def _load_from_redis(self, status: KeyStatus) -> Optional[str]:
        """Load key secret from Redis"""
        redis_key = {
            KeyStatus.CURRENT: self.REDIS_KEY_CURRENT,
            KeyStatus.PREVIOUS_1: self.REDIS_KEY_PREVIOUS_1,
            KeyStatus.PREVIOUS_2: self.REDIS_KEY_PREVIOUS_2
        }.get(status)
        
        if not redis_key:
            return None
        
        try:
            data = self.redis.get(redis_key)
            if data:
                key_data = json.loads(data)
                return key_data.get("secret_key")
        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"[JWT_KEYS] Failed to load from Redis: {e}")
        
        return None
    
    def _load_from_sql(self, status: KeyStatus) -> Optional[JWTKey]:
        """Load key from SQL database"""
        try:
            return self.db.query(JWTKey).filter(
                JWTKey.status == status,
                JWTKey.is_active == True
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"[JWT_KEYS] SQL query failed: {e}")
            return None
    
    # ==================== PUBLIC API ====================
    
    def sync_from_sql(self) -> None:
        """
        Load keys from SQL to Redis on startup.
        Called when backend starts to restore state.
        """
        logger.info("[JWT_KEYS] Syncing keys from SQL to Redis...")
        
        try:
            # Load all active keys from SQL
            active_keys = self.db.query(JWTKey).filter(
                JWTKey.is_active == True,
                JWTKey.status.in_([KeyStatus.CURRENT, KeyStatus.PREVIOUS_1, KeyStatus.PREVIOUS_2])
            ).all()
            
            if not active_keys:
                logger.warning("[JWT_KEYS] No active keys found in SQL, generating initial key...")
                self._generate_initial_key()
                return
            
            # Store each key in Redis
            for key in active_keys:
                self._store_in_redis(key.to_dict(), key.status)
            
            logger.info(f"[JWT_KEYS] ✅ Loaded {len(active_keys)} keys from SQL to Redis")
            
        except SQLAlchemyError as e:
            logger.error(f"[JWT_KEYS] ❌ Failed to sync from SQL: {e}")
            # Generate new key if sync fails
            self._generate_initial_key()
    
    def _generate_initial_key(self) -> None:
        """Generate the first JWT key (on initial deployment)"""
        logger.info("[JWT_KEYS] Generating initial JWT key...")
        
        secret_key = self._generate_secret_key()
        key_id = self._create_key_id()
        created_at = datetime.utcnow()
        expires_at = created_at + timedelta(hours=self.KEY_EXPIRY_HOURS)
        
        # Store in SQL
        try:
            jwt_key = JWTKey(
                key_id=key_id,
                secret_key=secret_key,
                status=KeyStatus.CURRENT,
                created_at=created_at,
                expires_at=expires_at,
                is_active=True
            )
            self.db.add(jwt_key)
            self.db.commit()
            
            # Store in Redis
            self._store_in_redis(jwt_key.to_dict(), KeyStatus.CURRENT)
            
            # Set last rotation time
            self.redis.set(self.REDIS_LAST_ROTATION, int(created_at.timestamp()))
            
            logger.info(f"[JWT_KEYS] ✅ Initial key generated: {key_id}")
            
        except SQLAlchemyError as e:
            logger.error(f"[JWT_KEYS] ❌ Failed to create initial key: {e}")
            self.db.rollback()
            raise RuntimeError("Unable to initialize JWT keys")
    
    def get_current_key(self) -> str:
        """
        Get active signing key (CURRENT).
        
        Returns:
            str: JWT secret key for signing tokens
        """
        # Try Redis first (fast)
        secret_key = self._load_from_redis(KeyStatus.CURRENT)
        if secret_key:
            return secret_key
        
        logger.warning("[JWT_KEYS] Current key not in Redis, loading from SQL...")
        
        # Fallback to SQL
        jwt_key = self._load_from_sql(KeyStatus.CURRENT)
        if not jwt_key:
            raise RuntimeError("No current JWT key available")
        
        # Cache in Redis
        self._store_in_redis(jwt_key.to_dict(), KeyStatus.CURRENT)
        
        return jwt_key.secret_key
    
    def get_verification_keys(self) -> List[str]:
        """
        Get all valid keys for verification [current, previous_1, previous_2].
        
        Returns:
            List[str]: List of 1-3 valid secret keys
        """
        keys = []
        
        # Try to load all 3 keys
        for status in [KeyStatus.CURRENT, KeyStatus.PREVIOUS_1, KeyStatus.PREVIOUS_2]:
            # Try Redis first
            secret_key = self._load_from_redis(status)
            
            # Fallback to SQL
            if not secret_key:
                jwt_key = self._load_from_sql(status)
                if jwt_key:
                    secret_key = jwt_key.secret_key
                    # Cache in Redis for future requests
                    self._store_in_redis(jwt_key.to_dict(), status)
            
            if secret_key:
                keys.append(secret_key)
        
        if not keys:
            raise RuntimeError("No verification keys available")
        
        logger.debug(f"[JWT_KEYS] Loaded {len(keys)} verification keys")
        return keys
    
    def should_rotate(self) -> bool:
        """
        Check if key rotation is needed.
        
        Returns:
            bool: True if rotation should happen
        """
        try:
            # Get last rotation time
            last_rotation = self.redis.get(self.REDIS_LAST_ROTATION)
            if not last_rotation:
                logger.warning("[JWT_KEYS] No last rotation time found")
                return True
            
            last_rotation_ts = int(last_rotation)
            last_rotation_dt = datetime.utcfromtimestamp(last_rotation_ts)
            hours_since_rotation = (datetime.utcnow() - last_rotation_dt).total_seconds() / 3600
            
            # Rotate if >= 24 hours
            if hours_since_rotation >= self.KEY_ROTATION_HOURS:
                logger.info(f"[JWT_KEYS] Rotation needed: {hours_since_rotation:.1f} hours since last rotation")
                return True
            
            logger.debug(f"[JWT_KEYS] Rotation not needed: {hours_since_rotation:.1f} hours since last rotation")
            return False
            
        except (RedisError, ValueError) as e:
            logger.error(f"[JWT_KEYS] Error checking rotation: {e}")
            return False
    
    def _check_user_activity(self) -> bool:
        """
        Check if any users have been active recently.
        Looks for recent rate limit keys in Redis.
        
        Returns:
            bool: True if users active in last hour
        """
        try:
            # Check for any rate limit keys (indicating recent activity)
            rate_limit_keys = self.redis.keys("rate_limit:*")
            
            if rate_limit_keys:
                logger.info(f"[JWT_KEYS] Found {len(rate_limit_keys)} active sessions")
                return True
            
            logger.info("[JWT_KEYS] No active sessions found")
            return False
            
        except RedisError as e:
            logger.error(f"[JWT_KEYS] Failed to check user activity: {e}")
            # Default to true to allow rotation
            return True
    
    def rotate_keys(self, force: bool = False) -> bool:
        """
        Rotate keys if TTL expired and users active.
        
        Args:
            force: Force rotation regardless of conditions
        
        Returns:
            bool: True if rotation happened, False if skipped
        """
        # Check if rotation needed
        if not force and not self.should_rotate():
            return False
        
        # Check user activity
        if not force and not self._check_user_activity():
            logger.info("[JWT_KEYS] Skipping rotation - no user activity")
            return False
        
        logger.info("[JWT_KEYS] ===== Starting key rotation =====")
        
        try:
            # Generate new key
            new_secret_key = self._generate_secret_key()
            new_key_id = self._create_key_id()
            created_at = datetime.utcnow()
            expires_at = created_at + timedelta(hours=self.KEY_EXPIRY_HOURS)
            
            # SQL transaction for atomic rotation
            try:
                # Demote current → previous_1
                current_key = self.db.query(JWTKey).filter(
                    JWTKey.status == KeyStatus.CURRENT,
                    JWTKey.is_active == True
                ).first()
                
                if current_key:
                    current_key.status = KeyStatus.PREVIOUS_1
                
                # Demote previous_1 → previous_2
                previous_1_key = self.db.query(JWTKey).filter(
                    JWTKey.status == KeyStatus.PREVIOUS_1,
                    JWTKey.is_active == True
                ).first()
                
                if previous_1_key and previous_1_key.id != (current_key.id if current_key else None):
                    previous_1_key.status = KeyStatus.PREVIOUS_2
                
                # Mark previous_2 → expired
                previous_2_key = self.db.query(JWTKey).filter(
                    JWTKey.status == KeyStatus.PREVIOUS_2,
                    JWTKey.is_active == True
                ).first()
                
                if previous_2_key:
                    previous_2_key.status = KeyStatus.EXPIRED
                    previous_2_key.is_active = False
                
                # Insert new current key
                new_key = JWTKey(
                    key_id=new_key_id,
                    secret_key=new_secret_key,
                    status=KeyStatus.CURRENT,
                    created_at=created_at,
                    expires_at=expires_at,
                    is_active=True
                )
                self.db.add(new_key)
                
                # Commit SQL transaction
                self.db.commit()
                
                logger.info(f"[JWT_KEYS] ✅ SQL rotation complete: new key = {new_key_id}")
                
                # Update Redis
                self._sync_redis_after_rotation()
                
                # Update last rotation time
                self.redis.set(self.REDIS_LAST_ROTATION, int(created_at.timestamp()))
                
                logger.info("[JWT_KEYS] ===== ✅ Key rotation successful =====")
                return True
                
            except SQLAlchemyError as e:
                logger.error(f"[JWT_KEYS] ❌ SQL rotation failed: {e}")
                self.db.rollback()
                return False
                
        except Exception as e:
            logger.error(f"[JWT_KEYS] ❌ Rotation error: {e}", exc_info=True)
            return False
    
    def _sync_redis_after_rotation(self) -> None:
        """Sync Redis with SQL after rotation"""
        logger.info("[JWT_KEYS] Syncing Redis after rotation...")
        
        for status in [KeyStatus.CURRENT, KeyStatus.PREVIOUS_1, KeyStatus.PREVIOUS_2]:
            jwt_key = self._load_from_sql(status)
            if jwt_key:
                self._store_in_redis(jwt_key.to_dict(), status)
    
    def increment_verification_stat(self, key_status: str) -> None:
        """Increment verification stat counter for monitoring"""
        try:
            key = f"{self.REDIS_STATS_PREFIX}{key_status}"
            self.redis.incr(key)
        except RedisError:
            pass  # Stats are non-critical
    
    def get_stats(self) -> Dict:
        """Get key rotation statistics"""
        try:
            current_key = self._load_from_sql(KeyStatus.CURRENT)
            last_rotation = self.redis.get(self.REDIS_LAST_ROTATION)
            
            stats = {
                "current_key_id": current_key.key_id if current_key else None,
                "current_key_age_hours": current_key.age_hours if current_key else None,
                "last_rotation": int(last_rotation) if last_rotation else None,
                "verifications": {
                    "current": int(self.redis.get(f"{self.REDIS_STATS_PREFIX}current") or 0),
                    "previous_1": int(self.redis.get(f"{self.REDIS_STATS_PREFIX}previous_1") or 0),
                    "previous_2": int(self.redis.get(f"{self.REDIS_STATS_PREFIX}previous_2") or 0),
                }
            }
            return stats
        except Exception as e:
            logger.error(f"[JWT_KEYS] Failed to get stats: {e}")
            return {}


# Singleton instance
_jwt_key_manager: Optional[JWTKeyManager] = None


def get_jwt_key_manager() -> JWTKeyManager:
    """Get JWT key manager singleton instance"""
    global _jwt_key_manager
    if _jwt_key_manager is None:
        _jwt_key_manager = JWTKeyManager()
    return _jwt_key_manager
