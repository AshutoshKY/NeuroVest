"""
SRE Health Score Engine

Calculates health scores for all services using exact SRE formulas.
Each service gets a 0-100 score based on:
- Availability (35%)
- Error Rate (30%)
- Latency (20%)
- Saturation (15%)

Health States:
- Healthy: >= 90
- Degraded: 70-89
- Critical: < 70

AI/RAG Penalty:
- If empty_context_rate > 20% OR p95_retrieval > SLA: score × 0.85
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger

from app.core.redis_client import get_redis
from app.services.metrics_collector import MetricsCollector, InfraMetricsCollector


class HealthState(str, Enum):
    """Health state enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"


class TrendDirection(str, Enum):
    """Trend direction enumeration"""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


@dataclass
class ServiceSLA:
    """SLA configuration per service"""
    p95_latency_ms: float  # Target p95 latency
    max_error_rate_percent: float  # Error rate considered acceptable
    max_saturation_percent: float  # Saturation level before warning
    
    
# Default SLA configurations
DEFAULT_SLAS: Dict[str, ServiceSLA] = {
    "api": ServiceSLA(p95_latency_ms=200.0, max_error_rate_percent=1.0, max_saturation_percent=80.0),
    "redis": ServiceSLA(p95_latency_ms=5.0, max_error_rate_percent=0.5, max_saturation_percent=75.0),
    "mysql": ServiceSLA(p95_latency_ms=50.0, max_error_rate_percent=0.5, max_saturation_percent=80.0),
    "chromadb": ServiceSLA(p95_latency_ms=100.0, max_error_rate_percent=1.0, max_saturation_percent=85.0),
    "host": ServiceSLA(p95_latency_ms=0.0, max_error_rate_percent=0.0, max_saturation_percent=85.0),  # Host doesn't have latency/error
}

# RAG SLA for AI penalty
RAG_SLA = {
    "p95_retrieval_ms": 500.0,
    "max_empty_context_rate": 20.0
}


@dataclass
class HealthScoreComponents:
    """Health score breakdown"""
    availability_score: float  # 0-100
    error_score: float  # 0-100
    latency_score: float  # 0-100
    saturation_score: float  # 0-100
    
    # Raw metrics
    uptime_percent: float
    error_rate_percent: float
    p95_latency_ms: float
    saturation_percent: float
    
    # Computed
    weighted_score: float
    final_score: float  # After AI/RAG penalty if applicable
    health_state: HealthState
    
    # Optional AI penalty
    ai_penalty_applied: bool = False
    ai_penalty_reason: Optional[str] = None
    

@dataclass
class ServiceHealth:
    """Complete health status for a service"""
    name: str
    health_state: HealthState
    health_score: float
    error_rate_percent: float
    p95_latency_ms: float
    saturation_percent: float
    uptime_percent: float
    trend: TrendDirection
    last_updated: str
    
    # Detailed breakdown
    score_breakdown: Optional[HealthScoreComponents] = None
    interpretation: Optional[str] = None


class HealthScoreEngine:
    """
    SRE Health Score Engine
    
    Implements exact health score formulas:
    - A (Availability) = uptime_percentage
    - E (Error) = max(0, 100 - (error_rate × 10))
    - L (Latency) = max(0, 100 - ((p95 / SLA) × 100))
    - S (Saturation) = 100 - max(cpu%, memory%, connection%)
    
    Health Score = (0.35 × A) + (0.30 × E) + (0.20 × L) + (0.15 × S)
    """
    
    WEIGHTS = {
        "availability": 0.35,
        "error": 0.30,
        "latency": 0.20,
        "saturation": 0.15
    }
    
    @staticmethod
    def calculate_availability_score(uptime_percent: float) -> float:
        """A = uptime_percentage (clamped to 0-100)"""
        return min(100.0, max(0.0, uptime_percent))
    
    @staticmethod
    def calculate_error_score(error_rate_percent: float) -> float:
        """E = max(0, 100 - (error_rate × 10))"""
        # 1% errors → 90, 5% → 50, 10%+ → 0
        return max(0.0, 100.0 - (error_rate_percent * 10.0))
    
    @staticmethod
    def calculate_latency_score(p95_latency_ms: float, sla_latency_ms: float) -> float:
        """L = max(0, 100 - ((p95 / SLA) × 100))"""
        if sla_latency_ms <= 0:
            return 100.0  # No SLA = always healthy
        ratio = p95_latency_ms / sla_latency_ms
        return max(0.0, 100.0 - (ratio * 100.0))
    
    @staticmethod
    def calculate_saturation_score(
        cpu_percent: float = 0.0,
        memory_percent: float = 0.0,
        connection_percent: float = 0.0
    ) -> float:
        """S = 100 - max(cpu%, memory%, connection%)"""
        max_saturation = max(cpu_percent, memory_percent, connection_percent)
        return max(0.0, 100.0 - max_saturation)
    
    @classmethod
    def calculate_health_score(
        cls,
        uptime_percent: float,
        error_rate_percent: float,
        p95_latency_ms: float,
        sla_latency_ms: float,
        cpu_percent: float = 0.0,
        memory_percent: float = 0.0,
        connection_percent: float = 0.0,
        apply_ai_penalty: bool = False,
        empty_context_rate: float = 0.0,
        rag_p95_latency_ms: float = 0.0
    ) -> HealthScoreComponents:
        """
        Calculate complete health score with all components.
        
        Returns HealthScoreComponents with breakdown and final state.
        """
        # Component scores
        a = cls.calculate_availability_score(uptime_percent)
        e = cls.calculate_error_score(error_rate_percent)
        l = cls.calculate_latency_score(p95_latency_ms, sla_latency_ms)
        s = cls.calculate_saturation_score(cpu_percent, memory_percent, connection_percent)
        
        # Weighted score
        weighted = (
            cls.WEIGHTS["availability"] * a +
            cls.WEIGHTS["error"] * e +
            cls.WEIGHTS["latency"] * l +
            cls.WEIGHTS["saturation"] * s
        )
        
        # AI/RAG penalty
        final_score = weighted
        ai_penalty_applied = False
        ai_penalty_reason = None
        
        if apply_ai_penalty:
            if empty_context_rate > RAG_SLA["max_empty_context_rate"]:
                final_score = weighted * 0.85
                ai_penalty_applied = True
                ai_penalty_reason = f"Empty context rate {empty_context_rate:.1f}% exceeds {RAG_SLA['max_empty_context_rate']}% threshold"
            elif rag_p95_latency_ms > RAG_SLA["p95_retrieval_ms"]:
                final_score = weighted * 0.85
                ai_penalty_applied = True
                ai_penalty_reason = f"RAG p95 latency {rag_p95_latency_ms:.0f}ms exceeds {RAG_SLA['p95_retrieval_ms']}ms SLA"
        
        # Determine health state
        if final_score >= 90:
            health_state = HealthState.HEALTHY
        elif final_score >= 70:
            health_state = HealthState.DEGRADED
        else:
            health_state = HealthState.CRITICAL
        
        saturation_percent = max(cpu_percent, memory_percent, connection_percent)
        
        return HealthScoreComponents(
            availability_score=round(a, 2),
            error_score=round(e, 2),
            latency_score=round(l, 2),
            saturation_score=round(s, 2),
            uptime_percent=round(uptime_percent, 2),
            error_rate_percent=round(error_rate_percent, 2),
            p95_latency_ms=round(p95_latency_ms, 2),
            saturation_percent=round(saturation_percent, 2),
            weighted_score=round(weighted, 2),
            final_score=round(final_score, 2),
            health_state=health_state,
            ai_penalty_applied=ai_penalty_applied,
            ai_penalty_reason=ai_penalty_reason
        )
    
    @staticmethod
    def determine_health_state(score: float) -> HealthState:
        """Map score to health state"""
        if score >= 90:
            return HealthState.HEALTHY
        elif score >= 70:
            return HealthState.DEGRADED
        return HealthState.CRITICAL
    
    @staticmethod
    def generate_interpretation(
        service_name: str,
        components: HealthScoreComponents
    ) -> str:
        """Generate human-readable interpretation for degraded/critical services"""
        if components.health_state == HealthState.HEALTHY:
            return f"{service_name} is operating within normal parameters."
        
        issues = []
        
        # Check each component
        if components.availability_score < 99:
            issues.append(f"availability at {components.uptime_percent:.2f}%")
        
        if components.error_score < 90:
            issues.append(f"error rate at {components.error_rate_percent:.2f}%")
        
        if components.latency_score < 50:
            issues.append(f"p95 latency at {components.p95_latency_ms:.0f}ms (exceeds SLA)")
        
        if components.saturation_score < 50:
            issues.append(f"saturation at {components.saturation_percent:.0f}%")
        
        if components.ai_penalty_applied:
            issues.append(components.ai_penalty_reason)
        
        if not issues:
            return f"{service_name} is slightly degraded but within acceptable limits."
        
        state_verb = "degraded" if components.health_state == HealthState.DEGRADED else "critical"
        return f"{service_name} is {state_verb} due to: {'; '.join(issues)}."


class SREHealthService:
    """
    Main service for SRE health metrics.
    Aggregates data from metrics collectors and computes health scores.
    """
    
    @staticmethod
    def _get_redis_health() -> ServiceHealth:
        """Get Redis health metrics and calculate score"""
        try:
            metrics = InfraMetricsCollector.collect_redis_metrics()
            
            if not metrics.get("connected", False):
                return ServiceHealth(
                    name="Redis",
                    health_state=HealthState.CRITICAL,
                    health_score=0.0,
                    error_rate_percent=100.0,
                    p95_latency_ms=0.0,
                    saturation_percent=100.0,
                    uptime_percent=0.0,
                    trend=TrendDirection.DOWN,
                    last_updated=datetime.now(timezone.utc).isoformat(),
                    interpretation="Redis is DOWN - not responding to connections."
                )
            
            # Calculate saturation from memory - use real maxmemory from Redis
            memory_max = metrics.get("memory_max_mb") or 512  # Redis default if maxmemory not set
            memory_used = metrics.get("memory_used_mb", 0)
            memory_percent = (memory_used / memory_max * 100) if memory_max > 0 else 0
            
            # Connection saturation - get maxclients from Redis CONFIG if available
            # Default Redis maxclients is 10000
            max_clients = 10000
            connected_clients = metrics.get("connected_clients", 0)
            conn_percent = (connected_clients / max_clients * 100)
            
            sla = DEFAULT_SLAS["redis"]
            
            # Use real values from metrics - no fallbacks
            uptime_percent = metrics.get("uptime_percent", 0)  # 0 if not available
            latency_ms = metrics.get("latency_ms", 0)  # 0 if not available
            
            components = HealthScoreEngine.calculate_health_score(
                uptime_percent=uptime_percent,
                error_rate_percent=0.0,  # Redis doesn't expose error rate
                p95_latency_ms=latency_ms,
                sla_latency_ms=sla.p95_latency_ms,
                memory_percent=memory_percent,
                connection_percent=conn_percent
            )
            
            # Determine trend based on evictions
            evicted = metrics.get("evicted_keys", 0)
            trend = TrendDirection.UP if evicted > 10 else TrendDirection.STABLE
            
            return ServiceHealth(
                name="Redis",
                health_state=components.health_state,
                health_score=components.final_score,
                error_rate_percent=components.error_rate_percent,
                p95_latency_ms=components.p95_latency_ms,
                saturation_percent=components.saturation_percent,
                uptime_percent=components.uptime_percent,
                trend=trend,
                last_updated=datetime.now(timezone.utc).isoformat(),
                score_breakdown=components,
                interpretation=HealthScoreEngine.generate_interpretation("Redis", components)
            )
            
        except Exception as e:
            logger.error(f"[HEALTH_SCORE] Redis health check failed: {e}")
            return ServiceHealth(
                name="Redis",
                health_state=HealthState.CRITICAL,
                health_score=0.0,
                error_rate_percent=100.0,
                p95_latency_ms=0.0,
                saturation_percent=100.0,
                uptime_percent=0.0,
                trend=TrendDirection.DOWN,
                last_updated=datetime.now(timezone.utc).isoformat(),
                interpretation=f"Redis health check failed: {str(e)}"
            )
    
    @staticmethod
    def _get_mysql_health() -> ServiceHealth:
        """Get MySQL health metrics and calculate score"""
        try:
            metrics = InfraMetricsCollector.collect_mysql_metrics()
            
            if not metrics.get("connected", False):
                return ServiceHealth(
                    name="MySQL",
                    health_state=HealthState.CRITICAL,
                    health_score=0.0,
                    error_rate_percent=100.0,
                    p95_latency_ms=0.0,
                    saturation_percent=100.0,
                    uptime_percent=0.0,
                    trend=TrendDirection.DOWN,
                    last_updated=datetime.now(timezone.utc).isoformat(),
                    interpretation="MySQL is DOWN - not responding to connections."
                )
            
            # Connection saturation - use real max_connections from MySQL
            max_conn = metrics.get("max_connections", 151)  # MySQL default
            threads_connected = metrics.get("threads_connected", 0)
            conn_percent = (threads_connected / max_conn * 100) if max_conn > 0 else 0
            
            sla = DEFAULT_SLAS["mysql"]
            
            # Error rate from slow queries ratio
            total_queries = metrics.get("total_queries", 1)
            slow_queries = metrics.get("slow_queries", 0)
            error_rate = (slow_queries / total_queries * 100) if total_queries > 0 else 0
            
            # Use real values from metrics
            uptime_percent = metrics.get("uptime_percent", 0)
            latency_ms = metrics.get("latency_ms", 0)
            
            components = HealthScoreEngine.calculate_health_score(
                uptime_percent=uptime_percent,
                error_rate_percent=min(error_rate, 10),  # Cap at 10% for slow query "errors"
                p95_latency_ms=latency_ms,
                sla_latency_ms=sla.p95_latency_ms,
                connection_percent=conn_percent
                # Note: memory_percent not tracked for MySQL - only connection saturation
            )
            
            trend = TrendDirection.UP if slow_queries > 100 else TrendDirection.STABLE
            
            return ServiceHealth(
                name="MySQL",
                health_state=components.health_state,
                health_score=components.final_score,
                error_rate_percent=components.error_rate_percent,
                p95_latency_ms=components.p95_latency_ms,
                saturation_percent=components.saturation_percent,
                uptime_percent=components.uptime_percent,
                trend=trend,
                last_updated=datetime.now(timezone.utc).isoformat(),
                score_breakdown=components,
                interpretation=HealthScoreEngine.generate_interpretation("MySQL", components)
            )
            
        except Exception as e:
            logger.error(f"[HEALTH_SCORE] MySQL health check failed: {e}")
            return ServiceHealth(
                name="MySQL",
                health_state=HealthState.CRITICAL,
                health_score=0.0,
                error_rate_percent=100.0,
                p95_latency_ms=0.0,
                saturation_percent=100.0,
                uptime_percent=0.0,
                trend=TrendDirection.DOWN,
                last_updated=datetime.now(timezone.utc).isoformat(),
                interpretation=f"MySQL health check failed: {str(e)}"
            )
    
    @staticmethod
    def _get_chromadb_health() -> ServiceHealth:
        """Get ChromaDB health metrics and calculate score"""
        try:
            metrics = InfraMetricsCollector.collect_chromadb_metrics()
            
            if not metrics.get("connected", False):
                return ServiceHealth(
                    name="ChromaDB",
                    health_state=HealthState.CRITICAL,
                    health_score=0.0,
                    error_rate_percent=100.0,
                    p95_latency_ms=0.0,
                    saturation_percent=100.0,
                    uptime_percent=0.0,
                    trend=TrendDirection.DOWN,
                    last_updated=datetime.now(timezone.utc).isoformat(),
                    interpretation="ChromaDB is DOWN - vector database not responding."
                )
            
            sla = DEFAULT_SLAS["chromadb"]
            
            # Use real query latency from metrics
            query_latency_ms = metrics.get("avg_query_latency_ms", 0)
            
            # ChromaDB uptime not tracked - assume up if connected
            # Calculate based on connectivity: if connected, assume 100% for this check
            uptime_percent = 100.0 if metrics.get("connected") else 0.0
            
            components = HealthScoreEngine.calculate_health_score(
                uptime_percent=uptime_percent,
                error_rate_percent=0.0,  # No error rate tracked for ChromaDB
                p95_latency_ms=query_latency_ms,
                sla_latency_ms=sla.p95_latency_ms
            )
            
            return ServiceHealth(
                name="ChromaDB",
                health_state=components.health_state,
                health_score=components.final_score,
                error_rate_percent=components.error_rate_percent,
                p95_latency_ms=components.p95_latency_ms,
                saturation_percent=components.saturation_percent,
                uptime_percent=components.uptime_percent,
                trend=TrendDirection.STABLE,
                last_updated=datetime.now(timezone.utc).isoformat(),
                score_breakdown=components,
                interpretation=HealthScoreEngine.generate_interpretation("ChromaDB", components)
            )
            
        except Exception as e:
            logger.error(f"[HEALTH_SCORE] ChromaDB health check failed: {e}")
            return ServiceHealth(
                name="ChromaDB",
                health_state=HealthState.CRITICAL,
                health_score=0.0,
                error_rate_percent=100.0,
                p95_latency_ms=0.0,
                saturation_percent=100.0,
                uptime_percent=0.0,
                trend=TrendDirection.DOWN,
                last_updated=datetime.now(timezone.utc).isoformat(),
                interpretation=f"ChromaDB health check failed: {str(e)}"
            )
    
    @staticmethod
    def _get_api_health() -> ServiceHealth:
        """Get API/Backend health metrics and calculate score"""
        try:
            # Get request metrics
            request_metrics = MetricsCollector.get_request_metrics(minutes=5)
            
            # Get latency - use average from real metrics (p95 would need proper percentile tracking)
            avg_latency = request_metrics.get("average_latency_ms", 0)
            # Estimate p95 as 1.5x average - this is a reasonable statistical estimate
            p95_latency = avg_latency * 1.5 if avg_latency > 0 else 0
            
            # Try to get actual p95 if tracked in Redis
            try:
                redis = get_redis()
                p95_key = "metrics:latency:p95:api"
                stored_p95 = redis.get(p95_key)
                if stored_p95:
                    p95_latency = float(stored_p95)
            except:
                pass
            
            error_rate = request_metrics.get("error_rate_percent", 0)
            
            # Get real system metrics for saturation
            cpu_percent = 0.0
            memory_percent = 0.0
            try:
                import psutil
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory_percent = psutil.virtual_memory().percent
            except ImportError:
                # psutil not available - saturation metrics unavailable
                logger.warning("[HEALTH_SCORE] psutil not available for API saturation metrics")
            except Exception as e:
                logger.warning(f"[HEALTH_SCORE] Failed to get system metrics: {e}")
            
            sla = DEFAULT_SLAS["api"]
            
            # Calculate uptime based on whether API is responding
            # If we can get metrics, API is up
            uptime_percent = 100.0 if request_metrics.get("total_requests", 0) > 0 or not request_metrics.get("error") else 0.0
            
            components = HealthScoreEngine.calculate_health_score(
                uptime_percent=uptime_percent,
                error_rate_percent=error_rate,
                p95_latency_ms=p95_latency,
                sla_latency_ms=sla.p95_latency_ms,
                cpu_percent=cpu_percent,
                memory_percent=memory_percent
            )
            
            # Determine trend from error rate
            trend = TrendDirection.STABLE
            if error_rate > 5:
                trend = TrendDirection.UP
            
            return ServiceHealth(
                name="API",
                health_state=components.health_state,
                health_score=components.final_score,
                error_rate_percent=components.error_rate_percent,
                p95_latency_ms=components.p95_latency_ms,
                saturation_percent=components.saturation_percent,
                uptime_percent=components.uptime_percent,
                trend=trend,
                last_updated=datetime.now(timezone.utc).isoformat(),
                score_breakdown=components,
                interpretation=HealthScoreEngine.generate_interpretation("API", components)
            )
            
        except Exception as e:
            logger.error(f"[HEALTH_SCORE] API health check failed: {e}")
            return ServiceHealth(
                name="API",
                health_state=HealthState.CRITICAL,
                health_score=0.0,
                error_rate_percent=100.0,
                p95_latency_ms=0.0,
                saturation_percent=100.0,
                uptime_percent=0.0,
                trend=TrendDirection.DOWN,
                last_updated=datetime.now(timezone.utc).isoformat(),
                interpretation=f"API health check failed: {str(e)}"
            )
    
    @staticmethod  
    def _get_host_health() -> ServiceHealth:
        """Get Host/System health metrics"""
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=0.5)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk check
            try:
                disk = psutil.disk_usage('/')
                disk_percent = disk.percent
            except:
                disk_percent = 50.0
            
            sla = DEFAULT_SLAS["host"]
            
            # Host doesn't have latency or error rate - use saturation only
            saturation = max(cpu_percent, memory_percent, disk_percent)
            
            # Manual score for host (purely saturation based)
            if saturation < 70:
                score = 100 - saturation
            elif saturation < 85:
                score = 50
            else:
                score = 20
            
            if score >= 90:
                state = HealthState.HEALTHY
            elif score >= 70:
                state = HealthState.DEGRADED
            else:
                state = HealthState.CRITICAL
            
            trend = TrendDirection.STABLE
            if cpu_percent > 80 or memory_percent > 85:
                trend = TrendDirection.UP
            
            interpretation = "Host resources operating normally."
            if state != HealthState.HEALTHY:
                issues = []
                if cpu_percent > 70:
                    issues.append(f"CPU at {cpu_percent:.0f}%")
                if memory_percent > 80:
                    issues.append(f"Memory at {memory_percent:.0f}%")
                if disk_percent > 85:
                    issues.append(f"Disk at {disk_percent:.0f}%")
                interpretation = f"Host resources under pressure: {', '.join(issues)}"
            
            return ServiceHealth(
                name="Host",
                health_state=state,
                health_score=round(score, 2),
                error_rate_percent=0.0,
                p95_latency_ms=0.0,
                saturation_percent=round(saturation, 2),
                uptime_percent=100.0,
                trend=trend,
                last_updated=datetime.now(timezone.utc).isoformat(),
                interpretation=interpretation
            )
            
        except ImportError:
            # psutil not available - return error state, not fake healthy data
            logger.warning("[HEALTH_SCORE] psutil not available for Host health metrics")
            return ServiceHealth(
                name="Host",
                health_state=HealthState.DEGRADED,
                health_score=0.0,  # Unknown, not fake 95
                error_rate_percent=0.0,
                p95_latency_ms=0.0,
                saturation_percent=0.0,  # Unknown, not fake 30
                uptime_percent=0.0,  # Unknown, not fake 100
                trend=TrendDirection.STABLE,
                last_updated=datetime.now(timezone.utc).isoformat(),
                interpretation="Host metrics unavailable - psutil not installed. Install psutil for real metrics."
            )
        except Exception as e:
            logger.error(f"[HEALTH_SCORE] Host health check failed: {e}")
            return ServiceHealth(
                name="Host",
                health_state=HealthState.CRITICAL,
                health_score=0.0,
                error_rate_percent=0.0,
                p95_latency_ms=0.0,
                saturation_percent=0.0,
                uptime_percent=0.0,
                trend=TrendDirection.DOWN,
                last_updated=datetime.now(timezone.utc).isoformat(),
                interpretation=f"Host health check failed: {str(e)}"
            )
    
    @classmethod
    def get_all_services_health(cls) -> List[ServiceHealth]:
        """Get health for all services"""
        return [
            cls._get_api_health(),
            cls._get_redis_health(),
            cls._get_mysql_health(),
            cls._get_chromadb_health(),
            cls._get_host_health()
        ]
    
    @classmethod
    def get_service_matrix(cls) -> Dict[str, Any]:
        """Get service health matrix for dashboard"""
        services = cls.get_all_services_health()
        
        return {
            "services": [
                {
                    "name": s.name,
                    "health_state": s.health_state.value,
                    "health_score": s.health_score,
                    "error_rate_percent": s.error_rate_percent,
                    "p95_latency_ms": s.p95_latency_ms,
                    "saturation_percent": s.saturation_percent,
                    "uptime_percent": s.uptime_percent,
                    "trend": s.trend.value,
                    "interpretation": s.interpretation
                }
                for s in services
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    @classmethod
    def get_global_health(cls) -> Dict[str, Any]:
        """Get aggregated global system health"""
        services = cls.get_all_services_health()
        
        # Calculate global metrics
        scores = [s.health_score for s in services]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Global state is worst of all services
        states = [s.health_state for s in services]
        if HealthState.CRITICAL in states:
            global_state = HealthState.CRITICAL
        elif HealthState.DEGRADED in states:
            global_state = HealthState.DEGRADED
        else:
            global_state = HealthState.HEALTHY
        
        # Count incidents (degraded or critical services)
        incidents = sum(1 for s in services if s.health_state != HealthState.HEALTHY)
        
        # Get request metrics for global error rate and latency
        request_metrics = MetricsCollector.get_request_metrics(minutes=5)
        prev_metrics = MetricsCollector.get_request_metrics(minutes=10)  # Includes current + prev
        
        current_rps = request_metrics.get("requests_per_second", 0)
        # Estimate previous RPS
        prev_total = prev_metrics.get("total_requests", 0) - request_metrics.get("total_requests", 0)
        prev_rps = prev_total / (5 * 60) if prev_total > 0 else current_rps
        
        delta_percent = ((current_rps - prev_rps) / prev_rps * 100) if prev_rps > 0 else 0
        
        # User impact (based on error rate)
        error_rate = request_metrics.get("error_rate_percent", 0)
        if error_rate > 10:
            user_impact = {"affected_users": "major", "status": "major"}
        elif error_rate > 2:
            user_impact = {"affected_users": "partial", "status": "partial"}
        else:
            user_impact = {"affected_users": 0, "status": "none"}
        
        return {
            "global_health": global_state.value,
            "global_score": round(avg_score, 2),
            "user_impact": user_impact,
            "active_incidents": incidents,
            "global_error_rate": round(request_metrics.get("error_rate_percent", 0), 2),
            "p95_latency_ms": round(request_metrics.get("average_latency_ms", 0) * 1.5, 2),  # Estimated
            "rps": {
                "current": round(current_rps, 2),
                "previous": round(prev_rps, 2),
                "delta_percent": round(delta_percent, 2)
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    @classmethod
    def get_service_deep_dive(cls, service_name: str) -> Dict[str, Any]:
        """Get detailed metrics for a specific service"""
        service_map = {
            "api": cls._get_api_health,
            "redis": cls._get_redis_health,
            "mysql": cls._get_mysql_health,
            "chromadb": cls._get_chromadb_health,
            "host": cls._get_host_health
        }
        
        getter = service_map.get(service_name.lower())
        if not getter:
            return {"error": f"Unknown service: {service_name}"}
        
        health = getter()
        
        # Get raw metrics based on service
        raw_metrics = {}
        if service_name.lower() == "redis":
            raw_metrics = InfraMetricsCollector.collect_redis_metrics()
        elif service_name.lower() == "mysql":
            raw_metrics = InfraMetricsCollector.collect_mysql_metrics()
        elif service_name.lower() == "chromadb":
            raw_metrics = InfraMetricsCollector.collect_chromadb_metrics()
        elif service_name.lower() == "api":
            raw_metrics = MetricsCollector.get_request_metrics(minutes=60)
        
        return {
            "service": health.name,
            "health_state": health.health_state.value,
            "health_score": health.health_score,
            "score_breakdown": {
                "availability": health.score_breakdown.availability_score if health.score_breakdown else 100,
                "error": health.score_breakdown.error_score if health.score_breakdown else 100,
                "latency": health.score_breakdown.latency_score if health.score_breakdown else 100,
                "saturation": health.score_breakdown.saturation_score if health.score_breakdown else 100
            } if health.score_breakdown else None,
            "metrics": {
                "uptime_percent": health.uptime_percent,
                "error_rate_percent": health.error_rate_percent,
                "p95_latency_ms": health.p95_latency_ms,
                "saturation_percent": health.saturation_percent
            },
            "raw_metrics": raw_metrics,
            "interpretation": health.interpretation,
            "trend": health.trend.value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Singleton instance
sre_health_service = SREHealthService()


def get_sre_health_service() -> SREHealthService:
    return sre_health_service
