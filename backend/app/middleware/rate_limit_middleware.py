"""
API Rate Limiting Middleware
Applies rate limits to ALL API endpoints for DDoS protection.
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from loguru import logger
import uuid
from typing import Optional

from app.rate_limiting import get_rate_limiter


class APIRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Global API rate limiting middleware.
    
    Rate Limits:
    - Auth endpoints (/auth/*): 10 requests/minute
    - General endpoints: 30 requests/minute
    - Health/docs included for DDoS protection
    
    **Exemptions** (no strict header validation):
    - Device initialization: /api/device/*, /tracking/encryption/public-key
    - Auth: /auth/*
    - Docs: /docs, /redoc, /openapi.json, /health
    
    **NOT Exempt** (requires device/session/JWT):
    - /stocks/* (trending, search, analysis) - app features
    """
    
    # Exemptions from strict header validation (can proceed without device/session tokens)
    # ONLY initialization and auth endpoints - everything else requires full validation
    VALIDATION_EXEMPT_PATHS = {
        # Device initialization endpoints (needed BEFORE token exists)
        "/api/device/register",            # Register new device
        "/api/device/validate",             # Validate device token
        "/tracking/encryption/public-key",  # Get public key for registration
        
        # Auth endpoints (login flow)
        "/auth/login",                      # Login
        "/auth/register",                   # Register account
        "/auth/logout",                     # Logout
        "/auth/me",                         # Get current user
        "/auth/refresh",                    # Refresh token
        
        # Documentation & health (infrastructure)
        "/docs",                            # API docs
        "/redoc",                           # ReDoc
        "/openapi.json",                    # OpenAPI schema
        "/health",                          # Health check
    }

    
    async def dispatch(self, request: Request, call_next):
        """Apply API-level rate limiting to all requests"""
        
        # Generate request trace ID for logging
        trace_id = str(uuid.uuid4())[:8]
        request.state.trace_id = trace_id
        
        # Determine if this path is exempt from strict validation
        is_exempt = request.url.path in self.VALIDATION_EXEMPT_PATHS
        
        # Get user context (if authenticated)
        user_id = None
        is_admin = False
        if hasattr(request.state, 'user') and request.state.user:
            user_id = request.state.user.id
            is_admin = request.state.user.is_admin
        
        # Determine limit type based on endpoint
        # The actual limit VALUE is determined by RateLimiter based on user role
        if request.url.path.startswith("/auth/"):
            limit_type = "auth_minute"  # Auth endpoints (login, register, etc)
        else:
            limit_type = "api_minute"   # General API endpoints
        
        # Apply rate limiting
        # RateLimiter will check limits from config based on role (guest/user/admin)
        try:
            rate_limiter = get_rate_limiter()
            
            # Increment counter after successful check
            await rate_limiter.increment(
                request=request,
                user_id=user_id,
                is_admin=is_admin,
                limit_type=limit_type
            )
            
        except ValueError as e:
            # Missing required headers (strict validation failed)
            if is_exempt:
                # Exempt path - allow through even without headers
                logger.info(
                    f"[API_RATE_LIMIT] [{trace_id}] Exempt path allowed without headers: "
                    f"{request.url.path}"
                )
            else:
                # Not exempt - reject with detailed error
                error_detail = {
                    "error": "Something seems broken",
                    "detail": str(e),
                    "trace_id": trace_id,
                    "path": request.url.path
                }
                logger.warning(
                    f"[API_RATE_LIMIT] [{trace_id}] Missing headers rejected: "
                    f"{request.url.path}, error={e}"
                )
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=error_detail
                )
        
        except HTTPException as e:
            # Rate limit exceeded (429) or device token validation failed (428)
            logger.warning(
                f"[API_RATE_LIMIT] [{trace_id}] Request blocked: "
                f"status={e.status_code}, detail={e.detail}, path={request.url.path}"
            )
            # Add trace_id to error response
            error_detail = {
                "detail": e.detail,
                "trace_id": trace_id
            }
            return JSONResponse(
                status_code=e.status_code,
                content=error_detail,
                headers=e.headers or {}
            )
        
        except Exception as e:
            # Unexpected error - log but don't block request
            logger.error(
                f"[API_RATE_LIMIT] [{trace_id}] Unexpected error: {e}, "
                f"allowing request to proceed"
            )
        
        # Continue to endpoint
        response = await call_next(request)
        
        # Add trace_id to response headers for debugging
        response.headers["X-Trace-ID"] = trace_id
        
        return response
