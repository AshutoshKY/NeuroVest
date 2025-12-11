"""
Request ID middleware for tracing requests through the system.
"""
import uuid
import logging
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable

# Context variable to store request ID
request_id_contextvar: ContextVar[str] = ContextVar("request_id", default="")

logger = logging.getLogger(__name__)


def get_request_id() -> str:
    """Get the current request ID from context."""
    return request_id_contextvar.get()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID tracking to all requests."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Set in context
        request_id_contextvar.set(request_id)
        
        # Log incoming request
        logger.info(f"📨 Incoming request", extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "operation": "incoming_request"
        })
        
        # Process request
        try:
            response = await call_next(request)
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            # Log response
            logger.info(f"📤 Response sent", extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "operation": "outgoing_response"
            })
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Request failed", extra={
                "request_id": request_id,
                "error": str(e),
                "operation": "request_error"
            }, exc_info=True)
            raise
