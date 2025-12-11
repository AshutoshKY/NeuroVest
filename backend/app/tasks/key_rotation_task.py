"""
Background task for JWT key rotation.
Runs every hour and rotates keys if:
- 24 hours have passed since last rotation
- Users are active (checked via Redis rate limit keys)
"""
import asyncio
from loguru import logger
from datetime import datetime


async def key_rotation_scheduler():
    """
    Background task that runs every hour.
    Rotates keys only when users are active and TTL has expired.
    """
    from app.core.jwt_key_manager import get_jwt_key_manager
    
    logger.info("[KEY_ROTATION_TASK] Starting background key rotation scheduler...")
    
    while True:
        try:
            key_manager = get_jwt_key_manager()
            
            # Check if rotation needed
            if key_manager.should_rotate():
                logger.info("[KEY_ROTATION_TASK] Rotation conditions met, attempting rotation...")
                success = key_manager.rotate_keys(force=False)
                
                if success:
                    logger.info("[KEY_ROTATION_TASK] ✅ Keys rotated successfully")
                    
                    # Log current stats
                    stats = key_manager.get_stats()
                    logger.info(f"[KEY_ROTATION_TASK] Stats: {stats}")
                else:
                    logger.info("[KEY_ROTATION_TASK] Rotation skipped (no user activity or error)")
            else:
                logger.debug("[KEY_ROTATION_TASK] Rotation not needed yet")
            
            # Sleep for 1 hour
            logger.debug("[KEY_ROTATION_TASK] Sleeping for 1 hour...")
            await asyncio.sleep(3600)  # 1 hour
            
        except Exception as e:
            logger.error(f"[KEY_ROTATION_TASK] ❌ Error in rotation task: {e}", exc_info=True)
            # Sleep 5 minutes on error, then retry
            logger.info("[KEY_ROTATION_TASK] Retrying in 5 minutes...")
            await asyncio.sleep(300)


def start_key_rotation_task():
    """Start the key rotation background task"""
    asyncio.create_task(key_rotation_scheduler())
    logger.info("[KEY_ROTATION_TASK] Background task scheduled")
