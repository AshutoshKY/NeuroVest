"""
AI Metrics Service

Tracks AI/LLM usage for the Admin Command Center:
- Token usage (prompt/completion/total)
- Cost tracking per request
- Latency metrics
- Guardrail rejection tracking

Storage: Redis with TTLs for automatic cleanup.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
from loguru import logger
import json

from app.core.redis_client import get_redis


class AIProvider(str, Enum):
    """AI providers used by the application"""
    AZURE_OPENAI = "azure_openai"
    OPENAI = "openai"


class AIUsageType(str, Enum):
    """Types of AI usage"""
    RAG_ANALYSIS = "rag_analysis"  # Main stock analysis
    SENTIMENT = "sentiment"  # Sentiment analysis
    EMBEDDING = "embedding"  # Vector embeddings


# Cost per 1K tokens (Azure OpenAI pricing - GPT-4)
# Update these based on actual pricing
COST_PER_1K_TOKENS = {
    AIProvider.AZURE_OPENAI: {
        "prompt": 0.03,  # $0.03 per 1K prompt tokens
        "completion": 0.06,  # $0.06 per 1K completion tokens
    },
    AIProvider.OPENAI: {
        "prompt": 0.03,
        "completion": 0.06,
    }
}


# Redis key patterns
AI_METRICS_PREFIX = "ai_metrics:"
HOURLY_STATS_KEY = f"{AI_METRICS_PREFIX}hourly:"
DAILY_STATS_KEY = f"{AI_METRICS_PREFIX}daily:"
GUARDRAIL_KEY = f"{AI_METRICS_PREFIX}guardrails:"
REQUEST_LOG_KEY = f"{AI_METRICS_PREFIX}requests:"


@dataclass
class AIRequestMetrics:
    """Metrics for a single AI request"""
    request_id: str
    usage_type: AIUsageType
    provider: AIProvider
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    cost_usd: float
    ticker: Optional[str] = None
    user_id: Optional[int] = None
    success: bool = True
    error: Optional[str] = None
    timestamp: Optional[str] = None
    
    def to_dict(self) -> dict:
        return asdict(self)


class AIMetricsService:
    """
    Centralized AI metrics collection and retrieval.
    """
    
    RETENTION_HOURS = 24 * 7  # Keep detailed data for 7 days
    RETENTION_DAILY = 30  # Keep daily aggregates for 30 days
    
    @staticmethod
    def calculate_cost(
        provider: AIProvider,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """Calculate cost in USD for token usage"""
        pricing = COST_PER_1K_TOKENS.get(provider, COST_PER_1K_TOKENS[AIProvider.OPENAI])
        prompt_cost = (prompt_tokens / 1000) * pricing["prompt"]
        completion_cost = (completion_tokens / 1000) * pricing["completion"]
        return round(prompt_cost + completion_cost, 6)
    
    @staticmethod
    def record_request(
        request_id: str,
        usage_type: AIUsageType,
        provider: AIProvider,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        ticker: Optional[str] = None,
        user_id: Optional[int] = None,
        success: bool = True,
        error: Optional[str] = None
    ):
        """
        Record a single AI request's metrics.
        Called after each LLM call.
        """
        try:
            redis = get_redis()
            now = datetime.now(timezone.utc)
            hour_key = now.strftime("%Y%m%d%H")
            day_key = now.strftime("%Y%m%d")
            
            total_tokens = prompt_tokens + completion_tokens
            cost_usd = AIMetricsService.calculate_cost(provider, prompt_tokens, completion_tokens)
            
            metrics = AIRequestMetrics(
                request_id=request_id,
                usage_type=usage_type,
                provider=provider,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
                ticker=ticker,
                user_id=user_id,
                success=success,
                error=error,
                timestamp=now.isoformat()
            )
            
            # Store in hourly aggregates
            hourly_key = f"{HOURLY_STATS_KEY}{hour_key}"
            pipe = redis.pipeline()
            
            # Increment counters
            pipe.hincrby(hourly_key, "total_requests", 1)
            pipe.hincrby(hourly_key, "prompt_tokens", prompt_tokens)
            pipe.hincrby(hourly_key, "completion_tokens", completion_tokens)
            pipe.hincrby(hourly_key, "total_tokens", total_tokens)
            pipe.hincrbyfloat(hourly_key, "total_cost_usd", cost_usd)
            pipe.hincrbyfloat(hourly_key, "total_latency_ms", latency_ms)
            
            if not success:
                pipe.hincrby(hourly_key, "errors", 1)
            
            # Track by usage type
            pipe.hincrby(hourly_key, f"type:{usage_type.value}", 1)
            
            # Set TTL
            pipe.expire(hourly_key, AIMetricsService.RETENTION_HOURS * 3600)
            
            # Store daily aggregate too
            daily_key = f"{DAILY_STATS_KEY}{day_key}"
            pipe.hincrby(daily_key, "total_requests", 1)
            pipe.hincrby(daily_key, "total_tokens", total_tokens)
            pipe.hincrbyfloat(daily_key, "total_cost_usd", cost_usd)
            pipe.expire(daily_key, AIMetricsService.RETENTION_DAILY * 86400)
            
            # Store recent request details (capped list)
            request_data = json.dumps({
                "request_id": request_id,
                "usage_type": usage_type.value,
                "tokens": total_tokens,
                "cost": cost_usd,
                "latency_ms": latency_ms,
                "ticker": ticker,
                "success": success,
                "timestamp": now.isoformat()
            })
            request_list_key = f"{REQUEST_LOG_KEY}{day_key}"
            pipe.lpush(request_list_key, request_data)
            pipe.ltrim(request_list_key, 0, 499)  # Keep last 500 requests
            pipe.expire(request_list_key, AIMetricsService.RETENTION_DAILY * 86400)
            
            pipe.execute()
            
            logger.debug(
                f"[AI_METRICS] Recorded: {usage_type.value} | "
                f"tokens={total_tokens} | cost=${cost_usd:.4f} | latency={latency_ms:.0f}ms"
            )
            
        except Exception as e:
            logger.error(f"[AI_METRICS] Failed to record metrics: {e}")
    
    @staticmethod
    def record_guardrail_rejection(
        reason: str,
        ticker: Optional[str] = None,
        user_id: Optional[int] = None,
        query: Optional[str] = None
    ):
        """Record when a request is rejected by guardrails"""
        try:
            redis = get_redis()
            now = datetime.now(timezone.utc)
            day_key = now.strftime("%Y%m%d")
            
            guardrail_key = f"{GUARDRAIL_KEY}{day_key}"
            
            # Increment rejection counter by reason
            redis.hincrby(guardrail_key, f"reason:{reason}", 1)
            redis.hincrby(guardrail_key, "total", 1)
            redis.expire(guardrail_key, AIMetricsService.RETENTION_DAILY * 86400)
            
            logger.info(
                f"[AI_METRICS] Guardrail rejection: {reason} | ticker={ticker}"
            )
            
        except Exception as e:
            logger.error(f"[AI_METRICS] Failed to record guardrail rejection: {e}")
    
    @staticmethod
    def get_hourly_stats(hours: int = 24) -> List[Dict]:
        """Get hourly AI usage stats for the last N hours"""
        try:
            redis = get_redis()
            now = datetime.now(timezone.utc)
            stats = []
            
            for i in range(hours):
                hour = now - timedelta(hours=i)
                hour_key = hour.strftime("%Y%m%d%H")
                key = f"{HOURLY_STATS_KEY}{hour_key}"
                
                data = redis.hgetall(key)
                if data:
                    # Keys are strings because Redis client uses decode_responses=True
                    total_requests = int(data.get("total_requests", 0))
                    total_latency = float(data.get("total_latency_ms", 0))
                    
                    stats.append({
                        "hour": hour.strftime("%Y-%m-%d %H:00"),
                        "total_requests": total_requests,
                        "prompt_tokens": int(data.get("prompt_tokens", 0)),
                        "completion_tokens": int(data.get("completion_tokens", 0)),
                        "total_tokens": int(data.get("total_tokens", 0)),
                        "total_cost_usd": float(data.get("total_cost_usd", 0)),
                        "avg_latency_ms": total_latency / total_requests if total_requests > 0 else 0,
                        "errors": int(data.get("errors", 0)),
                        "rag_requests": int(data.get("type:rag_analysis", 0)),
                        "sentiment_requests": int(data.get("type:sentiment", 0))
                    })
            
            return stats
            
        except Exception as e:
            logger.error(f"[AI_METRICS] Failed to get hourly stats: {e}")
            return []
    
    @staticmethod
    def get_daily_summary() -> Dict:
        """Get summary of today's AI usage"""
        try:
            redis = get_redis()
            now = datetime.now(timezone.utc)
            day_key = now.strftime("%Y%m%d")
            
            # Get daily stats
            daily_data = redis.hgetall(f"{DAILY_STATS_KEY}{day_key}")
            guardrail_data = redis.hgetall(f"{GUARDRAIL_KEY}{day_key}")
            
            # Keys are strings because Redis client uses decode_responses=True
            total_requests = int(daily_data.get("total_requests", 0)) if daily_data else 0
            total_tokens = int(daily_data.get("total_tokens", 0)) if daily_data else 0
            total_cost = float(daily_data.get("total_cost_usd", 0)) if daily_data else 0
            
            guardrail_rejections = int(guardrail_data.get("total", 0)) if guardrail_data else 0
            
            return {
                "date": now.strftime("%Y-%m-%d"),
                "total_requests": total_requests,
                "total_tokens": total_tokens,
                "total_cost_usd": round(total_cost, 4),
                "avg_tokens_per_request": total_tokens // total_requests if total_requests > 0 else 0,
                "guardrail_rejections": guardrail_rejections,
                "timestamp": now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"[AI_METRICS] Failed to get daily summary: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def get_recent_requests(limit: int = 50) -> List[Dict]:
        """Get recent AI request details"""
        try:
            redis = get_redis()
            now = datetime.now(timezone.utc)
            day_key = now.strftime("%Y%m%d")
            
            request_list_key = f"{REQUEST_LOG_KEY}{day_key}"
            requests = redis.lrange(request_list_key, 0, limit - 1)
            
            # Strings already decoded because Redis client uses decode_responses=True
            return [json.loads(r) if isinstance(r, str) else json.loads(r.decode()) for r in requests]
            
        except Exception as e:
            logger.error(f"[AI_METRICS] Failed to get recent requests: {e}")
            return []
    
    @staticmethod
    def get_guardrail_stats() -> Dict:
        """Get guardrail rejection statistics"""
        try:
            redis = get_redis()
            now = datetime.now(timezone.utc)
            day_key = now.strftime("%Y%m%d")
            
            guardrail_data = redis.hgetall(f"{GUARDRAIL_KEY}{day_key}")
            
            if not guardrail_data:
                return {"date": now.strftime("%Y-%m-%d"), "total": 0, "by_reason": {}}
            
            by_reason = {}
            total = 0
            
            for key, value in guardrail_data.items():
                # Keys are strings because Redis client uses decode_responses=True
                key_str = key if isinstance(key, str) else key.decode()
                count = int(value)
                
                if key_str == "total":
                    total = count
                elif key_str.startswith("reason:"):
                    reason = key_str.replace("reason:", "")
                    by_reason[reason] = count
            
            return {
                "date": now.strftime("%Y-%m-%d"),
                "total": total,
                "by_reason": by_reason
            }
            
        except Exception as e:
            logger.error(f"[AI_METRICS] Failed to get guardrail stats: {e}")
            return {"error": str(e)}


# Singleton instance
ai_metrics_service = AIMetricsService()


def get_ai_metrics_service() -> AIMetricsService:
    return ai_metrics_service
