"""
API Health Tracker with Circuit Breaker
========================================

Tracks API success/failure rates and implements circuit breaker pattern
to prevent wasting time on consistently failing APIs.

Author: NeuroVest
Date: 2025-12-13
"""

import json
import time
import logging
from typing import Dict, Any, Optional, List
from collections import deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class APIHealthTracker:
    """
    Track API health and implement circuit breaker pattern.
    
    Features:
    - Success/failure rate tracking
    - Circuit breaker (opens if success rate < threshold)
    - Time-window failure tracking
    - Per-API per-market tracking (e.g., "finnhub_india", "yfinance_us")
    
    Circuit Breaker States:
    - CLOSED: Normal operation, all APIs available
    - OPEN: API failing too much, skip it temporarily
    - HALF_OPEN: Testing if API recovered
    """
    
    # Configuration
    CIRCUIT_BREAKER_THRESHOLD = 0.30  # Open if success rate < 30%
    CIRCUIT_RECOVERY_TIME = 300       # Try recovery after 5 minutes
    MAX_RECENT_CALLS = 100            # Track last 100 calls per API
    TIME_WINDOW_MINUTES = 5           # Track failures in 5-min window
    TIME_WINDOW_FAILURE_THRESHOLD = 10  # Open circuit if 10+ failures in window
    
    def __init__(self, redis_client=None):
        """
        Initialize API health tracker.
        
        Args:
            redis_client: Redis client for persistence (optional)
        """
        self.redis = redis_client
        
        # In-memory tracking (fallback if no Redis)
        self.health_data: Dict[str, Dict[str, Any]] = {}
        
        # Recent calls buffer (for circuit breaker)
        self.recent_calls: Dict[str, deque] = {}
        
        # Time-window failures
        self.time_window_failures: Dict[str, List[float]] = {}
        
        logger.info(f"APIHealthTracker initialized (Redis: {'✅' if redis_client else '❌'})")
    
    def _get_api_key(self, api_name: str, market: str) -> str:
        """Generate key for API+market combination."""
        return f"{api_name.lower()}_{market.lower()}"
    
    async def record_result(self, api_name: str, market: str, success: bool, response_time: float = 0.0):
        """
        Record API call result.
        
        Args:
            api_name: Name of API (e.g., "finnhub", "yfinance")
            market: Market ("US", "INDIA")
            success: Whether call succeeded
            response_time: Response time in seconds
        """
        key = self._get_api_key(api_name, market)
        current_time = time.time()
        
        try:
            # Update Redis if available
            if self.redis:
                # Get current data
                redis_key = f"api_health:{key}"
                data = self.redis.hgetall(redis_key)
                
                if not data:
                    # Initialize
                    data = {
                        "total_calls": "0",
                        "successes": "0",
                        "failures": "0",
                        "success_rate": "1.0",
                        "circuit_open": "false",
                        "last_failure": "0",
                        "last_success": "0",
                        "avg_response_time": "0.0"
                    }
                
                # Update counters
                total_calls = int(data.get("total_calls", 0)) + 1
                successes = int(data.get("successes", 0)) + (1 if success else 0)
                failures = int(data.get("failures", 0)) + (0 if success else 1)
                success_rate = successes / total_calls if total_calls > 0 else 1.0
                
                # Update response time (rolling average)
                prev_avg = float(data.get("avg_response_time", 0.0))
                new_avg = (prev_avg * (total_calls - 1) + response_time) / total_calls
                
                # Update Redis hash
                self.redis.hset(redis_key, mapping={
                    "total_calls": str(total_calls),
                    "successes": str(successes),
                    "failures": str(failures),
                    "success_rate": f"{success_rate:.4f}",
                    "last_failure": str(current_time) if not success else data.get("last_failure", "0"),
                    "last_success": str(current_time) if success else data.get("last_success", "0"),
                    "avg_response_time": f"{new_avg:.3f}"
                })
                
                # Set expiry (24 hours)
                self.redis.expire(redis_key, 86400)
                
            else:
                # Fallback to memory
                if key not in self.health_data:
                    self.health_data[key] = {
                        "total_calls": 0,
                        "successes": 0,
                        "failures": 0,
                        "success_rate": 1.0,
                        "circuit_open": False
                    }
                
                data = self.health_data[key]
                data["total_calls"] += 1
                if success:
                    data["successes"] += 1
                else:
                    data["failures"] += 1
                data["success_rate"] = data["successes"] / data["total_calls"]
            
            # Update recent calls buffer
            if key not in self.recent_calls:
                self.recent_calls[key] = deque(maxlen=self.MAX_RECENT_CALLS)
            
            self.recent_calls[key].append(1 if success else 0)
            
            # Update time-window failures
            if not success:
                await self._record_time_window_failure(key, current_time)
            
            # Check circuit breaker
            await self._check_circuit_breaker(key)
            
            logger.debug(f"[HEALTH] {key}: {'✅' if success else '❌'} ({response_time:.2f}s)")
            
        except Exception as e:
            logger.error(f"[HEALTH] Error recording result for {key}: {e}")
    
    async def _record_time_window_failure(self, key: str, timestamp: float):
        """Record failure in time window."""
        if key not in self.time_window_failures:
            self.time_window_failures[key] = []
        
        # Add failure
        self.time_window_failures[key].append(timestamp)
        
        # Clean old failures (outside window)
        cutoff = timestamp - (self.TIME_WINDOW_MINUTES * 60)
        self.time_window_failures[key] = [
            ts for ts in self.time_window_failures[key]
            if ts > cutoff
        ]
    
    async def _check_circuit_breaker(self, key: str):
        """Check if circuit breaker should open."""
        try:
            # Get recent success rate
            if key in self.recent_calls and len(self.recent_calls[key]) >= 10:
                recent_success_rate = sum(self.recent_calls[key]) / len(self.recent_calls[key])
                
                # Open circuit if success rate too low
                if recent_success_rate < self.CIRCUIT_BREAKER_THRESHOLD:
                    await self._open_circuit(key, f"Success rate {recent_success_rate:.1%} < {self.CIRCUIT_BREAKER_THRESHOLD:.1%}")
            
            # Check time-window failures
            if key in self.time_window_failures:
                failure_count = len(self.time_window_failures[key])
                
                if failure_count >= self.TIME_WINDOW_FAILURE_THRESHOLD:
                    await self._open_circuit(key, f"{failure_count} failures in {self.TIME_WINDOW_MINUTES} minutes")
                    
        except Exception as e:
            logger.error(f"[HEALTH] Circuit breaker check error for {key}: {e}")
    
    async def _open_circuit(self, key: str, reason: str):
        """Open circuit breaker for API."""
        try:
            if self.redis:
                redis_key = f"api_health:{key}"
                self.redis.hset(redis_key, "circuit_open", "true")
                self.redis.hset(redis_key, "circuit_opened_at", str(time.time()))
                self.redis.hset(redis_key, "circuit_reason", reason)
            else:
                if key in self.health_data:
                    self.health_data[key]["circuit_open"] = True
                    self.health_data[key]["circuit_opened_at"] = time.time()
            
            logger.warning(f"⛔ [CIRCUIT BREAKER] OPENED for {key}: {reason}")
            
        except Exception as e:
            logger.error(f"[HEALTH] Error opening circuit for {key}: {e}")
    
    async def should_skip_api(self, api_name: str, market: str) -> bool:
        """
        Check if API should be skipped due to circuit breaker.
        
        Args:
            api_name: Name of API
            market: Market type
            
        Returns:
            True if API should be skipped
        """
        key = self._get_api_key(api_name, market)
        
        try:
            circuit_open = False
            circuit_opened_at = 0.0
            
            if self.redis:
                redis_key = f"api_health:{key}"
                data = self.redis.hgetall(redis_key)
                
                if data:
                    circuit_open = data.get("circuit_open", "false") == "true"
                    circuit_opened_at = float(data.get("circuit_opened_at", 0))
            else:
                if key in self.health_data:
                    circuit_open = self.health_data[key].get("circuit_open", False)
                    circuit_opened_at = self.health_data[key].get("circuit_opened_at", 0.0)
            
            if circuit_open:
                # Check if recovery time has passed
                if time.time() - circuit_opened_at >= self.CIRCUIT_RECOVERY_TIME:
                    # Try recovery (close circuit, allow one test call)
                    await self._close_circuit(key)
                    logger.info(f"🔄 [CIRCUIT BREAKER] Testing recovery for {key}")
                    return False  # Allow call to test recovery
                else:
                    logger.debug(f"⛔ [CIRCUIT BREAKER] Skipping {key} (circuit open)")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"[HEALTH] Error checking circuit for {key}: {e}")
            return False  # Don't skip on error
    
    async def _close_circuit(self, key: str):
        """Close circuit breaker (allow API calls again)."""
        try:
            if self.redis:
                redis_key = f"api_health:{key}"
                self.redis.hset(redis_key, "circuit_open", "false")
                self.redis.hdel(redis_key, "circuit_opened_at")
            else:
                if key in self.health_data:
                    self.health_data[key]["circuit_open"] = False
                    if "circuit_opened_at" in self.health_data[key]:
                        del self.health_data[key]["circuit_opened_at"]
            
            logger.info(f"✅ [CIRCUIT BREAKER] CLOSED for {key}")
            
        except Exception as e:
            logger.error(f"[HEALTH] Error closing circuit for {key}: {e}")
    
    async def get_health(self, api_name: str, market: str) -> Dict[str, Any]:
        """
        Get health status for specific API+market.
        
        Args:
            api_name: Name of API
            market: Market type
            
        Returns:
            Health data dictionary
        """
        key = self._get_api_key(api_name, market)
        
        try:
            if self.redis:
                redis_key = f"api_health:{key}"
                data = self.redis.hgetall(redis_key)
                
                if data:
                    return {
                        "api": api_name,
                        "market": market,
                        "total_calls": int(data.get("total_calls", 0)),
                        "successes": int(data.get("successes", 0)),
                        "failures": int(data.get("failures", 0)),
                        "success_rate": float(data.get("success_rate", 0.0)),
                        "circuit_open": data.get("circuit_open", "false") == "true",
                        "avg_response_time": float(data.get("avg_response_time", 0.0)),
                        "last_failure": float(data.get("last_failure", 0)),
                        "last_success": float(data.get("last_success", 0))
                    }
            else:
                if key in self.health_data:
                    return {
                        "api": api_name,
                        "market": market,
                        **self.health_data[key]
                    }
            
            # No data
            return {
                "api": api_name,
                "market": market,
                "total_calls": 0,
                "successes": 0,
                "failures": 0,
                "success_rate": 1.0,
                "circuit_open": False
            }
            
        except Exception as e:
            logger.error(f"[HEALTH] Error getting health for {key}: {e}")
            return {"error": str(e)}
    
    async def get_all_health_stats(self) -> List[Dict[str, Any]]:
        """Get health stats for all APIs."""
        stats = []
        
        try:
            if self.redis:
                # Get all api_health:* keys
                for redis_key in self.redis.scan_iter("api_health:*"):
                    key_parts = redis_key.decode().replace("api_health:", "").split("_")
                    if len(key_parts) >= 2:
                        api_name = key_parts[0]
                        market = key_parts[1].upper()
                        health = await self.get_health(api_name, market)
                        stats.append(health)
            else:
                for key in self.health_data:
                    api_name, market = key.split("_")
                    health = await self.get_health(api_name, market.upper())
                    stats.append(health)
            
            return stats
            
        except Exception as e:
            logger.error(f"[HEALTH] Error getting all stats: {e}")
            return []
    
    async def reset_health(self, api_name: str, market: str):
        """Reset health tracking for specific API."""
        key = self._get_api_key(api_name, market)
        
        try:
            if self.redis:
                redis_key = f"api_health:{key}"
                self.redis.delete(redis_key)
            
            if key in self.health_data:
                del self.health_data[key]
            
            if key in self.recent_calls:
                self.recent_calls[key].clear()
            
            if key in self.time_window_failures:
                del self.time_window_failures[key]
            
            logger.info(f"[HEALTH] Reset health for {key}")
            
        except Exception as e:
            logger.error(f"[HEALTH] Error resetting health for {key}: {e}")


# Helper function to create health tracker
def create_api_health_tracker(redis_client=None) -> APIHealthTracker:
    """
    Create APIHealthTracker instance.
    
    Args:
        redis_client: Redis client (will attempt to get from app if None)
        
    Returns:
        APIHealthTracker instance
    """
    if redis_client is None:
        try:
            from app.core.redis_client import get_redis
            redis_client = get_redis()
        except Exception as e:
            logger.warning(f"Could not get Redis client: {e}. Using memory-only tracking.")
    
    return APIHealthTracker(redis_client)
