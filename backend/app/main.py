from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager
from sqlalchemy import text
from app.core.config import settings
from app.core.database import init_db
from app.core.logging_config import setup_logging
from app.api import auth, stocks, sentiment, news, admin, health, tracking
from app.services.data_ingestion import data_ingestion_service
# Import models to ensure tables are created

from app.models.analysis_cache import AnalysisCache

# Setup logging with centralized configuration
setup_logging(
    log_level=settings.LOG_LEVEL,
    format_type=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("=" * 80)
    logger.info("🚀 Starting AI Market Analysis Assistant", extra={
        "operation": "startup",
        "version": settings.APP_VERSION,
        "debug_mode": settings.DEBUG,
        "rate_limit_enabled": settings.RATE_LIMIT_ENABLED
    })
    logger.info(f"🔒 Rate Limiting Status: {'ENABLED' if settings.RATE_LIMIT_ENABLED else 'DISABLED'}")
    
    if settings.RATE_LIMIT_ENABLED:
        from app.rate_limiting.config import rate_limit_config
        logger.info("📊 Rate Limit Configuration:")
        logger.info(f"   Guest: {rate_limit_config.GUEST_ANALYSIS_LIMIT} analyses/day, {rate_limit_config.GUEST_API_MINUTE_LIMIT} API calls/min (TTL: 60s)")
        logger.info(f"   User:  {rate_limit_config.USER_ANALYSIS_LIMIT} analyses/day, {rate_limit_config.USER_API_MINUTE_LIMIT} API calls/min (TTL: 60s)")
        logger.info(f"   Admin: {rate_limit_config.ADMIN_ANALYSIS_LIMIT} analyses/day, {rate_limit_config.ADMIN_API_MINUTE_LIMIT} API calls/min (TTL: 60s)")
        logger.info(f"   ⏰ Analysis Window: {rate_limit_config.GUEST_ANALYSIS_WINDOW}s (24 hours)")
        logger.info(f"   ⏰ API Minute Window: 60s")
        logger.info(f"   ⏰ API Hour Window: 3600s")
    
    logger.info("=" * 80)
    
    # Initialize database
    try:
        logger.info("📊 Initializing database...", extra={"operation": "db_init"})
        init_db()
        logger.info("✅ Database initialized successfully", extra={
            "operation": "db_init",
            "status": "success"
        })
    except Exception as e:
        logger.error("❌ Database initialization failed", extra={
            "operation": "db_init",
            "status": "failure",
            "error": str(e)
        }, exc_info=True)
    
    # Start health monitor
    try:
        from app.services.health_monitor import health_monitor
        logger.info("🏥 Starting health monitor...", extra={"operation": "health_monitor_start"})
        await health_monitor.start_monitoring()
        logger.info("✅ Health monitor started", extra={
            "operation": "health_monitor_start",
            "status": "success",
            "check_interval": health_monitor.check_interval
        })
    except Exception as e:
        logger.error("❌ Failed to start health monitor", extra={
            "operation": "health_monitor_start",
            "status": "failure",
            "error": str(e)
        }, exc_info=True)
    
    # Initialize JWT key manager (sync from SQL to Redis)
    try:
        from app.core.jwt_key_manager import get_jwt_key_manager
        logger.info("🔑 Initializing JWT key manager...", extra={"operation": "jwt_key_manager_init"})
        key_manager = get_jwt_key_manager()
        key_manager.sync_from_sql()
        
        # Log current key stats
        stats = key_manager.get_stats()
        logger.info(f"✅ JWT key manager initialized: {stats}", extra={
            "operation": "jwt_key_manager_init",
            "status": "success"
        })
    except Exception as e:
        logger.error(f"❌ JWT key manager initialization failed: {e}", extra={
            "operation": "jwt_key_manager_init",
            "status": "failure",
            "error": str(e)
        }, exc_info=True)
    
    # Start background key rotation task
    try:
        from app.tasks.key_rotation_task import start_key_rotation_task
        logger.info("🔄 Starting JWT key rotation background task...", extra={"operation": "key_rotation_task_start"})
        start_key_rotation_task()
        logger.info("✅ Key rotation task started (runs hourly)", extra={
            "operation": "key_rotation_task_start",
            "status": "success"
        })
    except Exception as e:
        logger.error(f"❌ Failed to start key rotation task: {e}", extra={
            "operation": "key_rotation_task_start",
            "status": "failure",
            "error": str(e)
        }, exc_info=True)
    
    logger.info("=" * 80)
    logger.info("✅ Application startup complete - Ready to serve requests")
    logger.info("=" * 80)
    
    yield
    
    # Shutdown
    logger.info("=" * 80)
    logger.info("🛑 Shutting down application...", extra={"operation": "shutdown"})
    
    # Stop health monitor
    try:
        from app.services.health_monitor import health_monitor
        await health_monitor.stop_monitoring()
        logger.info("✅ Health monitor stopped")
    except Exception as e:
        logger.error(f"❌ Error stopping health monitor: {e}")
    
    logger.info("=" * 80)


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Add Request ID middleware (must be first to execute)
from app.core.request_middleware import RequestIDMiddleware
app.add_middleware(RequestIDMiddleware)

# Add Rate Limiting middleware 
# NOTE: Middlewares execute in REVERSE order of registration
# So this will run AFTER security middleware (which is registered next)
from app.middleware.rate_limit_middleware import APIRateLimitMiddleware
app.add_middleware(APIRateLimitMiddleware)
logger.info("✅ API rate limiting middleware enabled (with auth exemptions)")

# Add Security middleware (IP blacklist, system toggles, DDOS protection)
# This runs FIRST (before rate limiting) to avoid wasting counters on blocked IPs
from app.middleware.security_middleware import SecurityMiddleware
app.add_middleware(SecurityMiddleware)
logger.info("✅ Security middleware enabled (IP blacklist, system toggles, DDOS)")


# CORS middleware - Production ready
# Supports: Oracle Cloud backend + Streamlit Cloud frontend
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:8000", 
    "http://localhost:8502",
    "http://localhost:8501",  # Streamlit default
]

# Add production origins from environment (comma-separated)
import os
production_origins = os.getenv("ALLOWED_ORIGINS", "")
if production_origins:
    allowed_origins.extend([origin.strip() for origin in production_origins.split(",") if origin.strip()])

# Add wildcard for Streamlit Cloud subdomains (*.streamlit.app)
# Note: For production, specify exact domains instead of wildcards
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Specific origins
    allow_origin_regex=r"https://.*\.streamlit\.app",  # Streamlit Cloud wildcard
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],  # Expose request ID for debugging
    max_age=600,  # Cache preflight requests for 10 minutes
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


from app.api import (
    auth, health, stocks, sentiment, news, admin, tracking, user, user_stocks,
    admin_management, admin_health, admin_traffic, admin_history, admin_cache, device, security, admin_orchestrator
)

# Include routers
logger.info("[INIT] Registering API routers...")
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(health.router, tags=["Health"])
app.include_router(stocks.router, prefix="/stocks", tags=["Stocks"])
app.include_router(sentiment.router, prefix="/sentiment", tags=["Sentiment"])
app.include_router(news.router, prefix="/news", tags=["News"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(tracking.router, prefix="/tracking", tags=["Tracking"])
app.include_router(device.router, prefix="/api", tags=["Device"])  # New device router
app.include_router(security.router, prefix="/api", tags=["Security"])  # Security endpoints
app.include_router(user.router, prefix="/user", tags=["User"])
app.include_router(user_stocks.router, tags=["User Stocks"])
app.include_router(admin_management.router, prefix="/admin", tags=["Admin Management"])

# Phase 3: Admin Monitoring APIs
app.include_router(admin_health.router)
app.include_router(admin_traffic.router)
app.include_router(admin_history.router)
app.include_router(admin_cache.router)
app.include_router(admin_orchestrator.router)  # Smart Orchestrator Admin

# WebSocket endpoint for real-time analysis
from app.api.stocks_websocket import websocket_endpoint

@app.websocket("/ws/stocks/{ticker}/analysis")
async def ws_stock_analysis(websocket: WebSocket, ticker: str):
    """WebSocket endpoint for real-time stock analysis streaming."""
    await websocket_endpoint(websocket, ticker)



# Root endpoint
@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "AI Market Analysis Assistant API",
        "version": settings.APP_VERSION,
        "status": "running"
    }


# Health check
@app.get("/health")
def health_check():
    """Health check endpoint with detailed database status."""
    try:
        from app.services.embeddings import embedding_service
        from app.core.database import get_db
        
        # Check MySQL database connection
        mysql_connected = False
        mysql_error = None
        try:
            db = next(get_db())
            db.execute(text("SELECT 1"))
            mysql_connected = True
        except Exception as e:
            mysql_error = str(e)
        
        # Check ChromaDB (Vector DB)
        chroma_connected = False
        chroma_doc_count = 0
        chroma_error = None
        try:
            chroma_doc_count = embedding_service.get_collection_count()
            chroma_connected = True
        except Exception as e:
            chroma_error = str(e)
        
        # Overall status
        overall_status = "healthy" if (mysql_connected and chroma_connected) else "degraded"
        
        return {
            "status": overall_status,
            "databases": {
                "mysql": {
                    "connected": mysql_connected,
                    "status": "connected" if mysql_connected else "disconnected",
                    "error": mysql_error
                },
                "chromadb": {
                    "connected": chroma_connected,
                    "status": "connected" if chroma_connected else "disconnected",
                    "document_count": chroma_doc_count,
                    "error": chroma_error
                }
            },
            # Legacy fields for backward compatibility
            "database": "connected" if mysql_connected else "disconnected",
            "database_connected": mysql_connected,
            "vector_db_documents": chroma_doc_count
        }
    except Exception as e:
        return {
            "status": "error",
            "databases": {
                "mysql": {"connected": False, "status": "unknown", "error": str(e)},
                "chromadb": {"connected": False, "status": "unknown", "error": str(e)}
            },
            "database": "unknown",
            "database_connected": False,
            "vector_db_documents": 0,
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
