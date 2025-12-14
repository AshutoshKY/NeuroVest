"""
Smart Orchestrator Admin API
=============================

Admin endpoints for monitoring and managing the smart orchestrator:
- View API health statistics
- Get cache statistics
- Reset circuit breakers
- View trending stocks

Author: NeuroVest
Date: 2025-12-13
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/smartorchestrator", tags=["Admin - Smart Orchestrator"])


@router.get("/health", summary="Get API Health Status")
async def get_api_health():
    """
    Get health status and circuit breaker state for all APIs.
    
    Returns comprehensive health metrics including:
    - Success/failure rates per API
    - Circuit breaker states
    - Average response times
    - Last success/failure timestamps
    
    Example Response:
    ```json
    [
        {
            "api": "yfinance",
            "market": "INDIA",
            "total_calls": 1250,
            "successes": 1125,
            "failures": 125,
            "success_rate": 0.90,
            "circuit_open": false,
            "avg_response_time": 0.85
        },
        {
            "api": "finnhub",
            "market": "INDIA",
            "total_calls": 520,
            "successes": 0,
            "failures": 520,
            "success_rate": 0.0,
            "circuit_open": true
        }
    ]
    ```
    """
    try:
        from app.services.smart_orchestrator import smart_orchestrator
        
        health_stats = await smart_orchestrator.health.get_all_health_stats()
        
        return {
            "status": "success",
            "apis": health_stats,
            "total_apis_tracked": len(health_stats)
        }
        
    except Exception as e:
        logger.error(f"Error getting API health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get health stats: {str(e)}")


@router.get("/health/{api_name}/{market}", summary="Get Specific API Health")
async def get_specific_api_health(api_name: str, market: str):
    """
    Get health statistics for a specific API and market combination.
    
    Args:
        api_name: API name (e.g., "yfinance", "finnhub", "alpha_vantage")
        market: Market type ("US" or "INDIA")
    
    Returns:
        Detailed health metrics for the specified API+market
    """
    try:
        from app.services.smart_orchestrator import smart_orchestrator
        
        market_upper = market.upper()
        if market_upper not in ["US", "INDIA"]:
            raise HTTPException(status_code=400, detail="Market must be 'US' or 'INDIA'")
        
        health = await smart_orchestrator.health.get_health(api_name, market_upper)
        
        return {
            "status": "success",
            "health": health
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting health for {api_name}/{market}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/circuit-breaker/reset", summary="Reset Circuit Breaker")
async def reset_circuit_breaker(api_name: str, market: str):
    """
    Manually reset circuit breaker for a specific API.
    
    Use this to force-enable an API that has been circuit-broken.
    **WARNING**: Only use if you're confident the API has recovered.
    
    Args:
        api_name: API name
        market: Market type ("US" or "INDIA")
    """
    try:
        from app.services.smart_orchestrator import smart_orchestrator
        
        market_upper = market.upper()
        await smart_orchestrator.health.reset_health(api_name, market_upper)
        
        logger.info(f"🔄 Circuit breaker reset for {api_name}/{market_upper}")
        
        return {
            "status": "success",
            "message": f"Circuit breaker reset for {api_name}/{market_upper}",
            "api": api_name,
            "market": market_upper
        }
        
    except Exception as e:
        logger.error(f"Error resetting circuit breaker: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats", summary="Get Cache Statistics")
async def get_cache_stats():
    """
    Get multi-tier cache statistics.
    
    Returns metrics for:
    - Memory cache (Tier 1)
    - Redis cache (Tier 2)
    - Stale cache (Tier 3)
    - Hit/miss rates
    
    Example Response:
    ```json
    {
        "memory_hits": 450,
        "redis_hits": 320,
        "stale_hits": 15,
        "misses": 215,
        "total_requests": 1000,
        "hit_rate_percent": 78.5,
        "memory_cache_size": 125
    }
    ```
    """
    try:
        from app.services.smart_orchestrator import smart_orchestrator
        
        stats = smart_orchestrator.cache.get_stats()
        
        return {
            "status": "success",
            "cache_stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear", summary="Clear All Caches")
async def clear_all_caches():
    """
    Clear all cache tiers (Memory + Redis).
    
    **WARNING**: This will force fresh API calls for all subsequent requests.
    Use with caution in production.
    """
    try:
        from app.services.smart_orchestrator import smart_orchestrator
        
        await smart_orchestrator.cache.clear_all()
        
        logger.warning("🗑️  All caches cleared by admin")
        
        return {
            "status": "success",
            "message": "All caches cleared successfully"
        }
        
    except Exception as e:
        logger.error(f"Error clearing caches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", summary="Get Orchestrator Statistics")
async def get_orchestrator_stats():
    """
    Get comprehensive smart orchestrator statistics.
    
    Returns:
    - Cache performance metrics
    - API health summary
    - Feature flag status
    """
    try:
        from app.services.smart_orchestrator import smart_orchestrator
        from app.core.config import settings
        
        stats = smart_orchestrator.get_stats()
        health_stats = await smart_orchestrator.health.get_all_health_stats()
        
        # Calculate overall success rate
        total_calls = sum(h.get('total_calls', 0) for h in health_stats)
        total_successes = sum(h.get('successes', 0) for h in health_stats)
        overall_success_rate = (total_successes / total_calls * 100) if total_calls > 0 else 0
        
        return {
            "status": "success",
            "feature_flag_enabled": settings.USE_SMART_ORCHESTRATOR,
            "cache_stats": stats.get('cache_stats', {}),
            "api_health_summary": {
                "total_apis_tracked": len(health_stats),
                "total_calls": total_calls,
                "total_successes": total_successes,
                "overall_success_rate": round(overall_success_rate, 2),
                "apis_circuit_open": sum(1 for h in health_stats if h.get('circuit_open', False))
            },
            "timestamp": stats.get('timestamp')
        }
        
    except Exception as e:
        logger.error(f"Error getting orchestrator stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config", summary="Get Current Configuration")
async def get_configuration():
    """
    Get current smart orchestrator configuration.
    
    Shows:
    - Feature flag status
    - Timeout settings
    - API selection strategy
    - Cache TTLs
    """
    try:
        from app.core.config import settings
        from app.services.smart_orchestrator import SmartAPIOrchestrator
        
        return {
            "status": "success",
            "config": {
                "feature_flag_enabled": settings.USE_SMART_ORCHESTRATOR,
                "parallel_timeout_seconds": settings.SMART_ORCHESTRATOR_TIMEOUT,
                "api_strategy": SmartAPIOrchestrator.API_STRATEGY,
                "cache_ttls": {
                    "memory_ttl_seconds": 60,
                    "redis_fresh_ttl_seconds": 300,
                    "redis_stale_ttl_seconds": 3600
                },
                "circuit_breaker": {
                    "threshold": 0.30,
                    "recovery_time_seconds": 300
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))
