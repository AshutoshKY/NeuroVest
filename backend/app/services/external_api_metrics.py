"""
External API Metrics Service

Tracks external API calls (Stock APIs, News APIs) for the Admin Command Center:
- Call count per API
- Success/failure rates
- Latency metrics
- Error tracking

Storage: Redis with TTLs for automatic cleanup.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from loguru import logger
import json

from app.core.redis_client import get_redis


# Redis key patterns
EXT_API_PREFIX = "ext_api_metrics:"
HOURLY_KEY = f"{EXT_API_PREFIX}hourly:"
DAILY_KEY = f"{EXT_API_PREFIX}daily:"
ERRORS_KEY = f"{EXT_API_PREFIX}errors:"


class ExternalAPIMetricsService:
    """
    Tracks external API call metrics for admin dashboard.
    """
    
    RETENTION_HOURS = 48  # Keep hourly data for 2 days
    RETENTION_DAILY = 30  # Keep daily data for 30 days
    
    # Known external APIs
    KNOWN_APIS = {
        "alpha_vantage": {"name": "Alpha Vantage", "provider": "alphavantage.co", "category": "stock"},
        "finnhub": {"name": "Finnhub", "provider": "finnhub.io", "category": "stock"},
        "yahoo_finance": {"name": "Yahoo Finance", "provider": "yahoo.com", "category": "stock"},
        "yfinance": {"name": "yfinance", "provider": "yahoo.com (yfinance)", "category": "stock"},
        "marketstack": {"name": "Marketstack", "provider": "marketstack.com", "category": "stock"},
        "upstox": {"name": "Upstox", "provider": "upstox.com", "category": "stock"},
        "nse": {"name": "NSE Connect", "provider": "nseindia.com", "category": "stock"},
        "newsapi": {"name": "NewsAPI", "provider": "newsapi.org", "category": "news"},
        "google_news": {"name": "Google News RSS", "provider": "news.google.com", "category": "news"},
        "openai_gpt4": {"name": "OpenAI GPT-4", "provider": "openai.com", "category": "llm"},
        "openai_embedding": {"name": "OpenAI Embeddings", "provider": "openai.com", "category": "llm"},
        "azure_openai": {"name": "Azure OpenAI", "provider": "azure.com", "category": "llm"},
    }
    
    @staticmethod
    def record_call(
        api_name: str,
        success: bool,
        latency_ms: float,
        error_message: Optional[str] = None,
        ticker: Optional[str] = None
    ):
        """
        Record an external API call.
        
        Args:
            api_name: API identifier (e.g., 'alpha_vantage', 'finnhub')
            success: Whether the call succeeded
            latency_ms: Response time in milliseconds
            error_message: Error message if failed
            ticker: Optional ticker being queried
        """
        try:
            redis = get_redis()
            now = datetime.now(timezone.utc)
            hour_key = now.strftime("%Y%m%d%H")
            day_key = now.strftime("%Y%m%d")
            
            # Normalize API name
            api_key = api_name.lower().replace(" ", "_").replace("-", "_")
            
            # Hourly stats
            hourly_stats_key = f"{HOURLY_KEY}{api_key}:{hour_key}"
            pipe = redis.pipeline()
            
            pipe.hincrby(hourly_stats_key, "calls", 1)
            pipe.hincrbyfloat(hourly_stats_key, "total_latency_ms", latency_ms)
            
            if success:
                pipe.hincrby(hourly_stats_key, "success", 1)
            else:
                pipe.hincrby(hourly_stats_key, "failure", 1)
                
                # Store last error
                if error_message:
                    pipe.hset(hourly_stats_key, "last_error", error_message[:200])
            
            pipe.expire(hourly_stats_key, ExternalAPIMetricsService.RETENTION_HOURS * 3600)
            
            # Daily stats
            daily_stats_key = f"{DAILY_KEY}{api_key}:{day_key}"
            pipe.hincrby(daily_stats_key, "calls", 1)
            pipe.hincrbyfloat(daily_stats_key, "total_latency_ms", latency_ms)
            
            if success:
                pipe.hincrby(daily_stats_key, "success", 1)
            else:
                pipe.hincrby(daily_stats_key, "failure", 1)
                if error_message:
                    pipe.hset(daily_stats_key, "last_error", error_message[:200])
            
            pipe.expire(daily_stats_key, ExternalAPIMetricsService.RETENTION_DAILY * 86400)
            
            pipe.execute()
            
            logger.debug(f"[EXT_API_METRICS] {api_key}: success={success}, latency={latency_ms:.0f}ms")
            
        except Exception as e:
            logger.error(f"[EXT_API_METRICS] Failed to record call: {e}")
    
    @staticmethod
    def get_all_api_metrics(hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get metrics for all external APIs.
        
        Returns list of API metrics with:
        - name, provider, category
        - calls_24h, success_count, failure_count
        - success_rate, avg_latency, status
        - last_error
        """
        try:
            redis = get_redis()
            now = datetime.now(timezone.utc)
            results = []
            
            for api_key, api_info in ExternalAPIMetricsService.KNOWN_APIS.items():
                total_calls = 0
                total_success = 0
                total_failure = 0
                total_latency = 0.0
                last_error = None
                
                # Aggregate hourly data
                for i in range(hours):
                    hour = now - timedelta(hours=i)
                    hour_str = hour.strftime("%Y%m%d%H")
                    hourly_key = f"{HOURLY_KEY}{api_key}:{hour_str}"
                    
                    data = redis.hgetall(hourly_key)
                    if data:
                        total_calls += int(data.get("calls", 0))
                        total_success += int(data.get("success", 0))
                        total_failure += int(data.get("failure", 0))
                        total_latency += float(data.get("total_latency_ms", 0))
                        
                        if not last_error and data.get("last_error"):
                            last_error = data.get("last_error")
                
                # Calculate metrics
                avg_latency = total_latency / total_calls if total_calls > 0 else 0
                success_rate = (total_success / total_calls * 100) if total_calls > 0 else 100.0
                
                # Determine status
                if total_calls == 0:
                    status = "unknown"
                elif success_rate >= 95:
                    status = "healthy"
                elif success_rate >= 80:
                    status = "degraded"
                else:
                    status = "down"
                
                results.append({
                    "api_key": api_key,
                    "name": api_info["name"],
                    "provider": api_info["provider"],
                    "category": api_info["category"],
                    "calls_24h": total_calls,
                    "success_count": total_success,
                    "failure_count": total_failure,
                    "success_rate": round(success_rate, 2),
                    "avg_latency_ms": round(avg_latency, 2),
                    "status": status,
                    "last_error": last_error
                })
            
            # Sort by calls descending
            return sorted(results, key=lambda x: x["calls_24h"], reverse=True)
            
        except Exception as e:
            logger.error(f"[EXT_API_METRICS] Failed to get metrics: {e}")
            return []
    
    @staticmethod
    def get_api_summary() -> Dict[str, Any]:
        """Get summary stats across all external APIs."""
        metrics = ExternalAPIMetricsService.get_all_api_metrics()
        
        total_calls = sum(m["calls_24h"] for m in metrics)
        total_success = sum(m["success_count"] for m in metrics)
        total_failure = sum(m["failure_count"] for m in metrics)
        
        apis_with_calls = [m for m in metrics if m["calls_24h"] > 0]
        avg_latency = sum(m["avg_latency_ms"] * m["calls_24h"] for m in apis_with_calls) / total_calls if total_calls > 0 else 0
        
        healthy_count = len([m for m in metrics if m["status"] == "healthy"])
        degraded_count = len([m for m in metrics if m["status"] == "degraded"])
        down_count = len([m for m in metrics if m["status"] == "down"])
        
        return {
            "total_calls_24h": total_calls,
            "total_success": total_success,
            "total_failure": total_failure,
            "overall_success_rate": round((total_success / total_calls * 100) if total_calls > 0 else 100, 2),
            "avg_latency_ms": round(avg_latency, 2),
            "healthy_apis": healthy_count,
            "degraded_apis": degraded_count,
            "down_apis": down_count
        }


# Singleton
external_api_metrics = ExternalAPIMetricsService()
