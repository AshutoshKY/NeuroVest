"""
Metrics Middleware

Records request metrics (latency, status, endpoint) for each request.
Designed to be lightweight - non-blocking, fail-silent.
"""

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect request metrics.
    Runs after each request completion.
    """
    
    # Paths to skip (high-frequency, low-value)
    SKIP_PATHS = [
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/favicon.ico",
    ]
    
    async def dispatch(self, request: Request, call_next):
        """Record request metrics after processing"""
        
        path = request.url.path
        
        # Skip metrics for certain paths
        if any(path.startswith(sp) for sp in self.SKIP_PATHS):
            return await call_next(request)
        
        # Record start time
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        # Get user ID from request state if available (auth middleware sets request.state.user)
        # NOTE: Must handle DetachedInstanceError - user object may be detached from session after call_next()
        user_id = None
        try:
            user = getattr(request.state, "user", None)
            if user is not None:
                # Access the id carefully - it may trigger a lazy load on a detached object
                user_id = getattr(user, "id", None)
        except Exception:
            # Silently ignore - user tracking is best-effort
            pass
        
        # Record metrics (non-blocking, fail-silent)
        try:
            from app.services.metrics_collector import MetricsCollector
            
            is_error = response.status_code >= 400
            
            MetricsCollector.record_request_metric(
                endpoint=path,
                method=request.method,
                status_code=response.status_code,
                latency_ms=latency_ms,
                user_id=user_id,
                is_error=is_error
            )
            
            # Log slow requests
            if latency_ms > 5000:  # > 5 seconds
                logger.warning(
                    f"[METRICS] Slow request: {request.method} {path} "
                    f"took {latency_ms:.0f}ms"
                )
                
        except Exception as e:
            # Don't fail the request if metrics recording fails
            logger.debug(f"[METRICS] Failed to record metrics: {e}")
        
        return response
