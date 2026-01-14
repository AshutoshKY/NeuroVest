"""
Security Middleware for IP Blacklist, Kill Switches, and System Toggles
Enforces security controls on ALL requests before they reach endpoints
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
from sqlalchemy import text

from app.core.database import get_db
from app.core.redis_client import get_redis


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce:
    1. Kill switches (emergency shutdown, block signups/logins)
    2. IP blacklist (403 for blocked IPs)
    3. System toggles (login_enabled, signup_enabled, guest_enabled, maintenance_mode)
    4. DDOS protection (100 req/min per IP)
    """
    
    # Whitelist paths that should NOT be blocked (health checks, etc.)
    WHITELIST_PATHS = [
        "/health",
        "/docs",
        "/openapi.json"
    ]
    
    # Paths that check system toggles
    AUTH_PATHS = {
        "/auth/login": "system:login_enabled",
        "/auth/register": "system:signup_enabled",
    }
    
    async def dispatch(self, request: Request, call_next):
        """Process each request through security checks"""
        
        path = request.url.path
        if request.client:
            client_ip = request.client.host
        else:
            client_ip = "unknown"
        
        # Skip whitelist paths
        if any(path.startswith(wp) for wp in self.WHITELIST_PATHS):
            return await call_next(request)
        
        # ========== KILL SWITCH CHECK (Phase 3) ==========
        # Check kill switches first - highest priority security control
        try:
            from app.services.kill_switch import (
                is_switch_active, should_bypass_kill_switch, KillSwitchType
            )
            
            # Admin paths bypass kill switches (for incident response)
            if not should_bypass_kill_switch(path):
                # Check emergency shutdown (blocks ALL traffic)
                if is_switch_active(KillSwitchType.EMERGENCY_SHUTDOWN):
                    logger.warning(f"[KILL_SWITCH] Emergency shutdown: blocking {client_ip} -> {path}")
                    return JSONResponse(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        content={"detail": "System is in emergency shutdown mode. All services are temporarily unavailable."}
                    )
                
                # Check block_signups (for signup endpoints only)
                if is_switch_active(KillSwitchType.BLOCK_SIGNUPS) and path.startswith("/auth/register"):
                    logger.warning(f"[KILL_SWITCH] Signups blocked: {client_ip}")
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={"detail": "New registrations are temporarily disabled."}
                    )
                
                # Check block_logins (for login endpoints only)
                if is_switch_active(KillSwitchType.BLOCK_LOGINS) and path.startswith("/auth/login"):
                    logger.warning(f"[KILL_SWITCH] Logins blocked: {client_ip}")
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={"detail": "Login is temporarily disabled."}
                    )
                
                # Check maintenance mode (via kill switch)
                if is_switch_active(KillSwitchType.MAINTENANCE_MODE):
                    # Allow authenticated admin requests
                    is_admin = await self._is_user_admin(request)
                    if not is_admin:
                        logger.info(f"[KILL_SWITCH] Maintenance mode: blocking {client_ip}")
                        return JSONResponse(
                            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            content={"detail": "System is under maintenance. Please try again later."}
                        )
        except Exception as e:
            logger.error(f"[SECURITY] Kill switch check failed: {e}")
            # Fail open - don't block if kill switch check fails
        # ========== END KILL SWITCH CHECK ==========
        
        # 1. Check IP Blacklist
        try:
            if await self._is_ip_blocked(client_ip):
                logger.warning(f"[SECURITY] Blocked IP attempt: {client_ip} -> {path}")
                # Track security event for SOC dashboard
                self._track_security_event("blocked_ip")
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Access denied. Your IP address has been blocked."}
                )
        except Exception as e:
            logger.error(f"[SECURITY] IP blacklist check failed: {e}")
        
        # 2. Check Maintenance Mode (for non-admin users)
        try:
            if await self._is_maintenance_mode(request):
                # Check if user is admin
                is_admin = await self._is_user_admin(request)
                if not is_admin:
                    logger.info(f"[SECURITY] Maintenance mode: blocking {client_ip}")
                    return JSONResponse(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        content={"detail": "System is under maintenance. Please try again later."}
                    )
        except Exception as e:
            logger.error(f"[SECURITY] Maintenance mode check failed: {e}")
        
        # 3. Check System Toggles (login, signup, guest)
        try:
            for auth_path, toggle_key in self.AUTH_PATHS.items():
                if path.startswith(auth_path):
                    if not await self._is_feature_enabled(toggle_key):
                        feature_name = toggle_key.split(":")[-1].replace("_enabled", "")
                        logger.warning(f"[SECURITY] {feature_name} disabled, blocking: {client_ip}")
                        return JSONResponse(
                            status_code=status.HTTP_403_FORBIDDEN,
                            content={"detail": f"{feature_name.replace('_', ' ').title()} is temporarily disabled."}
                        )
        except Exception as e:
            logger.error(f"[SECURITY] System toggle check failed: {e}")
        
        # 4. Guest Analysis Toggle (for analysis endpoints)
        try:
            if "/stocks/" in path and "/analysis" in path:
                # Check if guest_enabled (if user is not authenticated)
                is_authenticated = await self._is_request_authenticated(request)
                if not is_authenticated:
                    if not await self._is_feature_enabled("system:guest_enabled"):
                        logger.warning(f"[SECURITY] Guest analysis disabled: {client_ip}")
                        return JSONResponse(
                            status_code=status.HTTP_403_FORBIDDEN,
                            content={"detail": "Guest analysis is temporarily disabled. Please sign up or log in."}
                        )
        except Exception as e:
            logger.error(f"[SECURITY] Guest toggle check failed: {e}")
        
        # 5. DDOS Protection (500 requests/minute per IP for dev)
        try:
            if await self._check_ddos_limit(client_ip):
                logger.warning(f"[SECURITY] DDOS detected: {client_ip} exceeded 500 req/min")
                # Track security event for SOC dashboard
                self._track_security_event("rate_limit")
                # Auto-block IP
                await self._auto_block_ip(client_ip, "DDOS attack (>500 req/min)")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Too many requests. Your IP has been temporarily blocked."}
                )
        except Exception as e:
            logger.error(f"[SECURITY] DDOS check failed: {e}")
        
        # All checks passed, proceed to endpoint
        response = await call_next(request)
        return response
    
    async def _is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is in blacklist and hasn't expired"""
        db = next(get_db())
        try:
            from datetime import datetime
            # Check if IP is blocked AND (permanent OR not expired yet)
            result = db.execute(
                text("""
                    SELECT id FROM ip_blacklist 
                    WHERE ip_address = :ip 
                    AND is_active = 1 
                    AND (expires_at IS NULL OR expires_at > :now)
                """),
                {"ip": ip, "now": datetime.now()}
            )
            return result.fetchone() is not None
        except Exception as e:
            logger.error(f"[SECURITY] DB check failed for IP {ip}: {e}")
            return False
    
    async def _is_maintenance_mode(self, request: Request) -> bool:
        """Check if system is in maintenance mode (Redis)"""
        redis = get_redis()
        mode = redis.get("system:maintenance")
        return mode == "1" or mode == "true" or mode == b"1"
    
    async def _is_user_admin(self, request: Request) -> bool:
        """Check if request is from admin user"""
        # Check Authorization header for JWT
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return False
        
        # TODO: Decode JWT and check role
        # For now, return False (will implement JWT check later)
        return False
    
    async def _is_feature_enabled(self, toggle_key: str) -> bool:
        """Check if feature is enabled (Redis)"""
        redis = get_redis()
        value = redis.get(toggle_key)
        
        # Default to enabled if key doesn't exist
        if value is None:
            return True
        
        return value == "1" or value == "true" or value == b"1"
    
    def _track_security_event(self, event_type: str):
        """
        Track security events for SOC dashboard
        Event types: rate_limit, blocked_ip, auth_failure, ddos, other
        """
        try:
            redis = get_redis()
            today = datetime.now().strftime("%Y-%m-%d")
            key = f"security:events:{today}:{event_type}"
            redis.incr(key)
            redis.expire(key, 86400 * 7)  # Keep for 7 days
        except Exception as e:
            logger.error(f"[SECURITY] Failed to track event {event_type}: {e}")
    
    async def _is_request_authenticated(self, request: Request) -> bool:
        """Check if request has valid JWT token"""
        auth_header = request.headers.get("Authorization")
        return auth_header is not None and auth_header.startswith("Bearer ")
    
    async def _check_ddos_limit(self, ip: str) -> bool:
        """
        Check if IP exceeded DDOS limit (500 requests/minute for dev, 100 for prod)
        Returns True if limit exceeded
        """
        redis = get_redis()
        key = f"ddos:{ip}:{int(datetime.now().timestamp() // 60)}"
        
        count = redis.incr(key)
        redis.expire(key, 60)  # 1 minute window
        
        # 500 for development, reduce to 100 in production
        return count > 500
    
    async def _auto_block_ip(self, ip: str, reason: str):
        """Auto-block IP with tiered banning system"""
        db = next(get_db())
        try:
            from datetime import datetime, timedelta
            
            # Check how many times this IP has been blocked before
            result = db.execute(
                text("SELECT COUNT(*) as offense_count FROM ip_blacklist WHERE ip_address = :ip"),
                {"ip": ip}
            )
            offense_count = result.fetchone()[0] + 1  # +1 for current offense
            
            # Tiered banning: 1st = 30min, 2nd = 24h, 3rd+ = permanent
            if offense_count == 1:
                expires_at = datetime.now() + timedelta(minutes=30)
                ban_duration = "30 minutes"
            elif offense_count == 2:
                expires_at = datetime.now() + timedelta(hours=24)
                ban_duration = "24 hours"
            else:
                expires_at = None  # Permanent
                ban_duration = "permanent"
            
            db.execute(
                text("""
                    INSERT INTO ip_blacklist (ip_address, reason, blocked_by_user_id, auto_flagged, is_active, expires_at)
                    VALUES (:ip, :reason, NULL, 1, 1, :expires_at)
                    ON DUPLICATE KEY UPDATE 
                        reason = :reason,
                        blocked_at = :now,
                        is_active = 1,
                        expires_at = :expires_at
                """),
                {"ip": ip, "reason": f"{reason} (offense #{offense_count})", "now": datetime.now(), "expires_at": expires_at}
            )
            db.commit()
            logger.warning(f"[SECURITY] Auto-blocked IP: {ip} ({reason}) - Offense #{offense_count}, Ban: {ban_duration}")
        except Exception as e:
            logger.error(f"[SECURITY] Failed to auto-block IP {ip}: {e}")
            db.rollback()


# Import datetime at module level
from datetime import datetime
