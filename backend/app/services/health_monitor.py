"""
Data Source Health Monitor
Monitors uptime and health of external data sources (RSS, DuckDuckGo, Stock APIs)
using periodic health checks. Stores status in-memory without database persistence.
"""
import asyncio
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status enum"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Single health check result"""
    timestamp: str
    status: HealthStatus
    response_time_ms: Optional[int]
    error_message: Optional[str] = None


@dataclass
class DataSourceHealth:
    """Health status of a data source"""
    source_name: str
    source_type: str  # 'rss', 'search', 'stock_api'
    current_status: HealthStatus
    last_check: str
    uptime_percentage: float
    avg_response_time_ms: int
    total_checks: int
    successful_checks: int
    failed_checks: int
    last_success: Optional[str]
    last_failure: Optional[str]
    last_error: Optional[str]
    recent_checks: List[HealthCheck]  # Last 10 checks


class DataSourceHealthMonitor:
    """
    Monitors health of external data sources with periodic pings.
    All data stored in-memory, resets on service restart.
    """
    
    def __init__(self, check_interval_seconds: int = 300):  # Default: 5 minutes
        """
        Initialize health monitor.
        
        Args:
            check_interval_seconds: Interval between health checks
        """
        self.check_interval = check_interval_seconds
        self.sources: Dict[str, DataSourceHealth] = {}
        self.monitoring_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Initialize sources
        self._initialize_sources()
        
        logger.info(f"✅ Health Monitor initialized with {check_interval_seconds}s interval")
    
    def _initialize_sources(self):
        """Initialize all data sources to monitor"""
        # Stock APIs - ALL 4
        stock_apis = [
            ("Finnhub API", "stock_api"),
            ("Alpha Vantage API", "stock_api"),
            ("Marketstack API", "stock_api"),
            ("Yahoo Finance API", "stock_api"),
        ]
        
        # Search engines
        search_engines = [
            ("DuckDuckGo Search", "search"),
        ]
        
        # RSS feeds (can add more later)
        rss_feeds = [
            ("Moneycontrol RSS", "rss"),
            ("Economic Times RSS", "rss"),
        ]
        
        all_sources = stock_apis + search_engines + rss_feeds
        
        for source_name, source_type in all_sources:
            self.sources[source_name] = DataSourceHealth(
                source_name=source_name,
                source_type=source_type,
                current_status=HealthStatus.UNKNOWN,
                last_check="Never",
                uptime_percentage=0.0,
                avg_response_time_ms=0,
                total_checks=0,
                successful_checks=0,
                failed_checks=0,
                last_success=None,
                last_failure=None,
                last_error=None,
                recent_checks=[]
            )
    
    async def start_monitoring(self):
        """Start background monitoring task"""
        if self._running:
            logger.warning("⚠️  Health monitor already running")
            return
        
        self._running = True
        logger.info("🚀 Starting health monitor background task")
        
        # Run immediate check
        await self._check_all_sources()
        
        # Start periodic checks
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        """Stop background monitoring"""
        self._running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("🛑 Health monitor stopped")
    
    async def _monitoring_loop(self):
        """Background loop for periodic health checks"""
        while self._running:
            try:
                await asyncio.sleep(self.check_interval)
                await self._check_all_sources()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
    
    async def _check_all_sources(self):
        """Check health of all data sources"""
        logger.info("🏥 Running health checks on all data sources")
        
        tasks = []
        for source_name in self.sources.keys():
            tasks.append(self._check_source_health(source_name))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log summary
        healthy = sum(1 for s in self.sources.values() if s.current_status == HealthStatus.HEALTHY)
        degraded = sum(1 for s in self.sources.values() if s.current_status == HealthStatus.DEGRADED)
        down = sum(1 for s in self.sources.values() if s.current_status == HealthStatus.DOWN)
        
        logger.info(f"📊 Health check complete: {healthy} healthy, {degraded} degraded, {down} down")
    
    async def _check_source_health(self, source_name: str):
        """Check health of a specific data source"""
        source = self.sources.get(source_name)
        if not source:
            return
        
        start_time = time.time()
        
        try:
            # Perform health check based on source type
            if source.source_type == "stock_api":
                success, error = await self._ping_stock_api(source_name)
            elif source.source_type == "search":
                success, error = await self._ping_search_engine(source_name)
            elif source.source_type == "rss":
                success, error = await self._ping_rss_feed(source_name)
            else:
                success, error = False, "Unknown source type"
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Update source health
            self._update_source_health(
                source_name=source_name,
                success=success,
                response_time_ms=response_time_ms,
                error_message=error
            )
            
            status_emoji = "✅" if success else "❌"
            logger.info(f"{status_emoji} {source_name}: {response_time_ms}ms", extra={
                "operation": "health_check",
                "source": source_name,
                "status": "success" if success else "failure",
                "response_time_ms": response_time_ms
            })
            
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            self._update_source_health(
                source_name=source_name,
                success=False,
                response_time_ms=response_time_ms,
                error_message=str(e)
            )
            
            logger.error(f"❌ {source_name} health check failed: {e}")
    
    async def _ping_stock_api(self, api_name: str) -> tuple[bool, Optional[str]]:
        """Ping a stock API to check health"""
        try:
            # Import the actual stock API service
            from app.services.stock_api_service import StockAPIService
            
            # Create service instance
            stock_service = StockAPIService()
            
            # Map API name to provider name in the service
            provider_map = {
                "Finnhub API": "Finnhub",
                "Alpha Vantage API": "Alpha Vantage",
                "Marketstack API": "Marketstack",
                "Yahoo Finance API": "Yahoo Finance"
            }
            
            provider_name = provider_map.get(api_name)
            if not provider_name:
                return False, "Unknown API name"
            
            # Use a simple test ticker
            test_ticker = "RELIANCE"
            
            # Try to get data from specific provider
            try:
                data = await stock_service.get_stock_data_from_provider(test_ticker, provider_name)
                
                if data and 'current_price' in data and data['current_price'] > 0:
                    return True, None
                else:
                    return False, "No valid data returned"
                    
            except Exception as e:
                error_msg = str(e)
                # Check if it's an API key issue
                if "api key" in error_msg.lower() or "not found" in error_msg.lower():
                    return False, f"API key missing or invalid"
                return False, error_msg
                
        except Exception as e:
            return False, f"Service error: {str(e)}"
    
    async def _ping_search_engine(self, engine_name: str) -> tuple[bool, Optional[str]]:
        """Ping DuckDuckGo search to check health"""
        try:
            # Run synchronous DDGS in thread pool
            import asyncio
            
            def run_search():
                ddgs = DDGS()
                results = list(ddgs.text("stock market", max_results=1, backend="html"))
                return results
            
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, run_search)
            
            if results and len(results) > 0:
                return True, None
            else:
                return False, "No results returned"
                
        except Exception as e:
            return False, str(e)
    
    async def _ping_rss_feed(self, feed_name: str) -> tuple[bool, Optional[str]]:
        """Ping an RSS feed to check health"""
        try:
            # Map feed names to URLs
            rss_urls = {
                "Moneycontrol RSS": "https://www.moneycontrol.com/rss/latestnews.xml",
                "Economic Times RSS": "https://economictimes.indiatimes.com/rssfeedstopstories.cms"
            }
            
            url = rss_urls.get(feed_name)
            if not url:
                return False, "Unknown RSS feed"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        # Check if content looks like XML/RSS
                        content = await response.text()
                        if "<rss" in content.lower() or "<feed" in content.lower():
                            return True, None
                        else:
                            return False, "Invalid RSS format"
                    else:
                        return False, f"HTTP {response.status}"
                        
        except Exception as e:
            return False, str(e)
    
    def _update_source_health(self, source_name: str, success: bool, 
                             response_time_ms: int, error_message: Optional[str] = None):
        """Update health status for a source"""
        source = self.sources.get(source_name)
        if not source:
            return
        
        # Create health check record
        check = HealthCheck(
            timestamp=datetime.now().isoformat(),
            status=HealthStatus.HEALTHY if success else HealthStatus.DOWN,
            response_time_ms=response_time_ms if success else None,
            error_message=error_message
        )
        
        # Add to recent checks (keep last 10)
        source.recent_checks.append(check)
        if len(source.recent_checks) > 10:
            source.recent_checks.pop(0)
        
        # Update counters
        source.total_checks += 1
        if success:
            source.successful_checks += 1
            source.last_success = check.timestamp
        else:
            source.failed_checks += 1
            source.last_failure = check.timestamp
            source.last_error = error_message
        
        # Calculate uptime percentage
        source.uptime_percentage = (source.successful_checks / source.total_checks) * 100
        
        # Update average response time (only from successful checks)
        if success:
            if source.avg_response_time_ms == 0:
                source.avg_response_time_ms = response_time_ms
            else:
                # Rolling average
                source.avg_response_time_ms = int(
                    (source.avg_response_time_ms + response_time_ms) / 2
                )
        
        # Determine current status based on recent checks
        recent_failures = sum(1 for c in source.recent_checks[-5:] 
                            if c.status == HealthStatus.DOWN)
        
        if recent_failures == 0:
            source.current_status = HealthStatus.HEALTHY
        elif recent_failures <= 2:
            source.current_status = HealthStatus.DEGRADED
        else:
            source.current_status = HealthStatus.DOWN
        
        source.last_check = check.timestamp
    
    def get_all_health_status(self) -> List[Dict[str, Any]]:
        """Get health status of all sources"""
        return [
            {
                **asdict(source),
                'recent_checks': [asdict(check) for check in source.recent_checks]
            }
            for source in self.sources.values()
        ]
    
    def get_source_health(self, source_name: str) -> Optional[Dict[str, Any]]:
        """Get health status of a specific source"""
        source = self.sources.get(source_name)
        if not source:
            return None
        
        return {
            **asdict(source),
            'recent_checks': [asdict(check) for check in source.recent_checks]
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get overall health summary"""
        total = len(self.sources)
        healthy = sum(1 for s in self.sources.values() if s.current_status == HealthStatus.HEALTHY)
        degraded = sum(1 for s in self.sources.values() if s.current_status == HealthStatus.DEGRADED)
        down = sum(1 for s in self.sources.values() if s.current_status == HealthStatus.DOWN)
        unknown = sum(1 for s in self.sources.values() if s.current_status == HealthStatus.UNKNOWN)
        
        overall_uptime = sum(s.uptime_percentage for s in self.sources.values()) / total if total > 0 else 0
        
        # Category-level aggregates
        stock_apis = [s for s in self.sources.values() if s.source_type == "stock_api"]
        scraping_news = [s for s in self.sources.values() if s.source_type in ["search", "rss"]]
        
        def calculate_category_stats(sources):
            if not sources:
                return {"count": 0, "healthy": 0, "degraded": 0, "down": 0, "uptime_percentage": 0, "avg_response_time_ms": 0}
            
            return {
                "count": len(sources),
                "healthy": sum(1 for s in sources if s.current_status == HealthStatus.HEALTHY),
                "degraded": sum(1 for s in sources if s.current_status == HealthStatus.DEGRADED),
                "down": sum(1 for s in sources if s.current_status == HealthStatus.DOWN),
                "uptime_percentage": round(sum(s.uptime_percentage for s in sources) / len(sources), 2),
                "avg_response_time_ms": round(sum(s.avg_response_time_ms for s in sources) / len(sources), 0) if sources else 0
            }
        
        return {
            "total_sources": total,
            "healthy": healthy,
            "degraded": degraded,
            "down": down,
            "unknown": unknown,
            "overall_uptime_percentage": round(overall_uptime, 2),
            "last_check": max(
                (s.last_check for s in self.sources.values() if s.last_check != "Never"),
                default="Never"
            ),
            # Category aggregates
            "categories": {
                "stock_apis": calculate_category_stats(stock_apis),
                "scraping_news": calculate_category_stats(scraping_news)
            }
        }


# Global instance
health_monitor = DataSourceHealthMonitor(check_interval_seconds=300)  # 5 minutes
