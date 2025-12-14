"""
Smart API Orchestrator
======================

Intelligent multi-API orchestration with:
- Market-aware API selection (US vs India)
- Parallel execution with timeout control
- Multi-source data collation and merging
- Circuit breaker integration
- Multi-tier caching

CRITICAL: Maintains 100% backward compatibility with StockAPIService
All return formats MUST match existing service to avoid breaking:
- RAG system (technical indicators)
- Analysis pipeline
- API routes

Author: NeuroVest
Date: 2025-12-13
"""

import asyncio
import aiohttp
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from app.services.market_detector import market_detector, MarketType
from app.services.multi_tier_cache import MultiTierCache, create_multi_tier_cache
from app.services.api_health_tracker import APIHealthTracker, create_api_health_tracker

logger = logging.getLogger(__name__)


class SmartAPIOrchestrator:
    """
    Intelligent API orchestration with market awareness and health tracking.
    
    Key Features:
    - Detects market (US/India) automatically
    - Selects appropriate APIs per market
    - Executes API calls in parallel
    - Merges data from multiple sources
    - Circuit breaker prevents wasting time on failing APIs
    - Multi-tier caching (Memory/Redis/Stale)
    
    BACKWARD COMPATIBILITY:
    - All methods return same format as StockAPIService
    - Existing code using StockAPIService will work unchanged
    """
    
    # API selection strategy based on POC results
    # CRITICAL: Names must match exactly with sources.yaml API names
    API_STRATEGY = {
        "US": {
            "primary": ["Finnhub", "Yahoo Finance"],
            "fallback": ["Marketstack"]
        },
        "INDIA": {
            "primary": ["Yahoo Finance", "Alpha Vantage"],  # Yahoo Finance (yfinance) best for India
            "fallback": ["Marketstack"]
        }
    }
    
    # Timeout configuration
    PARALLEL_TIMEOUT = 5.0  # 5 seconds max for parallel calls
    PER_API_TIMEOUT = 3.0   # 3 seconds max per API
    
    def __init__(self, stock_api_service=None, redis_client=None):
        """
        Initialize Smart API Orchestrator.
        
        Args:
            stock_api_service: Existing StockAPIService instance (for API calls)
            redis_client: Redis client for caching (optional)
        """
        # Get existing service if not provided
        if stock_api_service is None:
            from app.services.stock_api_service import stock_api_service as sas
            stock_api_service = sas
        
        self.stock_api_service = stock_api_service
        
        # Initialize components
        self.cache = create_multi_tier_cache(redis_client)
        self.health = create_api_health_tracker(redis_client)
        self.detector = market_detector
        
        logger.info("✅ SmartAPIOrchestrator initialized")
    
    async def get_stock_data_enhanced(self, ticker: str) -> Dict[str, Any]:
        """
        Enhanced stock data fetching with smart orchestration.
        
        CRITICAL: Returns SAME format as StockAPIService.get_stock_data()
        to ensure RAG, analysis, and API routes continue working.
        
        Return Format (MUST MATCH):
        {
            'ticker': str,
            'exchange': str,
            'current_price': float,
            'previous_close': float,
            'day_high': float,
            'day_low': float,
            'volume': int,
            'currency': str,
            'timestamp': str,
            'provider': str  # May include multiple if merged
        }
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Stock data dictionary (same format as legacy service)
        """
        start_time = time.time()
        
        try:
            # Step 1: Check multi-tier cache
            cached = await self.cache.get(ticker)
            if cached and cached.get('fresh'):
                logger.info(f"⚡ [SMART] Cache HIT: {ticker} ({cached['source']}, {cached['age_seconds']:.1f}s old)")
                return cached['data']
            
            # Step 2: Detect market
            market = self.detector.detect_market(ticker)
            logger.info(f"📍 [SMART] Market: {ticker} → {market}")
            
            # Step 3: Select APIs based on market and health
            selected_apis = await self._select_apis(ticker, market)
            
            if not selected_apis:
                # All APIs circuit-broken, use stale cache if available
                if cached:
                    logger.warning(f"⚠️  [SMART] All APIs unavailable, using stale cache for {ticker}")
                    return {**cached['data'], '_warning': 'Using cached data (APIs unavailable)'}
                
                # No cache either, fallback to legacy (bypass feature flag)
                logger.warning(f"⚠️  [SMART] No cache, falling back to legacy for {ticker}")
                return await self.stock_api_service._get_stock_data_legacy(ticker)
            
            logger.info(f"🎯 [SMART] Selected APIs for {ticker}: {selected_apis}")
            
            # Step 4: Execute parallel API calls
            results = await self._execute_parallel(ticker, selected_apis, market)
            
            # Step 5: Merge results
            merged_data = await self._merge_results(results, ticker, market)
            
            if merged_data:
                # Success! Cache and return
                await self.cache.set(ticker, merged_data)
                
                elapsed = time.time() - start_time
                logger.info(f"✅ [SMART] Success: {ticker} from {merged_data.get('provider', 'merged')} ({elapsed:.2f}s)")
                
                return merged_data
            
            # Step 6: Fallback strategies
            # Try stale cache
            if cached:
                logger.warning(f"⚠️  [SMART] APIs failed, using stale cache for {ticker}")
                return {**cached['data'], '_warning': 'Using cached data (APIs failed)'}
            
            # Last resort: legacy service (bypass feature flag)
            logger.warning(f"⚠️  [SMART] Falling back to legacy service for {ticker}")
            return await self.stock_api_service._get_stock_data_legacy(ticker)
            
        except Exception as e:
            logger.error(f"❌ [SMART] Error for {ticker}: {e}")
            
            # On error, always fallback to legacy (bypass feature flag)
            try:
                return await self.stock_api_service._get_stock_data_legacy(ticker)
            except Exception as legacy_error:
                logger.error(f"❌ [SMART] Legacy also failed for {ticker}: {legacy_error}")
                raise Exception(f"Failed to fetch data for {ticker} from all providers")
    
    async def _select_apis(self, ticker: str, market: MarketType) -> List[str]:
        """
        Select which APIs to call based on market and health.
        
        Strategy:
        - US stocks: Finnhub + yfinance
        - Indian stocks: yfinance + Alpha Vantage
        - Skip APIs with open circuit breakers
        - Always include at least one API
        """
        strategy = self.API_STRATEGY.get(market, self.API_STRATEGY["INDIA"])
        
        selected = []
        
        # Check primary APIs
        for api_name in strategy["primary"]:
            # Check circuit breaker
            should_skip = await self.health.should_skip_api(api_name, market)
            
            if not should_skip:
                selected.append(api_name)
            else:
                logger.debug(f"⛔ [SMART] Skipping {api_name} for {market} (circuit open)")
        
        # If no primary APIs available, try fallback
        if not selected:
            logger.warning(f"⚠️  [SMART] No primary APIs available for {market}, trying fallback")
            
            for api_name in strategy.get("fallback", []):
                should_skip = await self.health.should_skip_api(api_name, market)
                
                if not should_skip:
                    selected.append(api_name)
                    break  # Just one fallback
        
        return selected
    
    async def _execute_parallel(
        self,
        ticker: str,
        api_names: List[str],
        market: MarketType
    ) -> List[Dict[str, Any]]:
        """
        Execute API calls in parallel with timeout.
        
        Uses existing StockAPIService methods to call each API,
        ensuring compatibility and reusing existing logic.
        """
        tasks = []
        
        for api_name in api_names:
            task = self._call_api_with_tracking(ticker, api_name, market)
            tasks.append(task)
        
        try:
            # Execute in parallel with overall timeout
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.PARALLEL_TIMEOUT
            )
            
            # Filter out exceptions
            valid_results = []
            for result in results:
                if not isinstance(result, Exception) and result is not None:
                    valid_results.append(result)
            
            return valid_results
            
        except asyncio.TimeoutError:
            logger.warning(f"⏱️  [SMART] Parallel execution timeout for {ticker}")
            return []
        except Exception as e:
            logger.error(f"❌ [SMART] Parallel execution error for {ticker}: {e}")
            return []
    
    async def _call_api_with_tracking(
        self,
        ticker: str,
        api_name: str,
        market: MarketType
    ) -> Optional[Dict[str, Any]]:
        """
        Call specific API and track result in health system.
        
        CRITICAL: Uses existing StockAPIService._fetch_from_api()
        to maintain compatibility with existing API implementations.
        """
        start_time = time.time()
        
        try:
            # Find API config
            api_config = None
            for api in self.stock_api_service.apis:
                if api['name'].lower() == api_name.lower():
                    api_config = api
                    break
            
            if not api_config:
                logger.warning(f"⚠️  [SMART] API config not found: {api_name}")
                await self.health.record_result(api_name, market, False, 0.0)
                return None
            
            # Call API using existing service method
            timeout = aiohttp.ClientTimeout(total=self.PER_API_TIMEOUT)
            
            # Use existing _fetch_from_api method
            data = await asyncio.wait_for(
                self.stock_api_service._fetch_from_api(api_config, ticker),
                timeout=self.PER_API_TIMEOUT
            )
            
            elapsed = time.time() - start_time
            
            if data and data.get('current_price', 0) > 0:
                # Success
                await self.health.record_result(api_name, market, True, elapsed)
                logger.debug(f"✅ [SMART] {api_name}: {ticker} ({elapsed:.2f}s)")
                
                # Add metadata
                return {
                    **data,
                    '_api_source': api_name,
                    '_response_time': elapsed
                }
            else:
                # No valid data
                await self.health.record_result(api_name, market, False, elapsed)
                logger.debug(f"❌ [SMART] {api_name}: {ticker} - No valid data")
                return None
                
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            await self.health.record_result(api_name, market, False, elapsed)
            logger.debug(f"⏱️  [SMART] {api_name}: {ticker} - Timeout")
            return None
            
        except Exception as e:
            elapsed = time.time() - start_time
            await self.health.record_result(api_name, market, False, elapsed)
            logger.debug(f"❌ [SMART] {api_name}: {ticker} - {str(e)[:100]}")
            return None
    
    async def _merge_results(
        self,
        results: List[Dict[str, Any]],
        ticker: str,
        market: MarketType
    ) -> Optional[Dict[str, Any]]:
        """
        Merge data from multiple API sources.
        
        Strategy:
        1. Start with most complete result (most non-null fields)
        2. Fill missing fields from other results
        3. Track which APIs contributed
        
        CRITICAL: Returns format matching StockAPIService.get_stock_data()
        """
        if not results:
            return None
        
        # Score results by completeness
        scored_results = []
        for result in results:
            score = self._calculate_quality_score(result)
            scored_results.append((score, result))
        
        # Sort by score (highest first)
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # Start with best result
        best_score, best_result = scored_results[0]
        merged = dict(best_result)
        
        # Track sources
        sources = [best_result.get('_api_source', 'unknown')]
        
        # Fill missing fields from other results
        fields_to_merge = [
            'current_price', 'previous_close', 'day_high', 'day_low',
            'volume', 'currency', 'exchange'
        ]
        
        for score, result in scored_results[1:]:
            for field in fields_to_merge:
                if not merged.get(field) and result.get(field):
                    merged[field] = result[field]
                    merged[f'_{field}_source'] = result.get('_api_source')
            
            if result.get('_api_source'):
                sources.append(result.get('_api_source'))
        
        # Clean up internal metadata and format output
        # MUST match StockAPIService.get_stock_data() return format
        final_result = {
            'ticker': ticker,
            'exchange': merged.get('exchange', 'NSE' if market == 'INDIA' else 'US'),
            'current_price': float(merged.get('current_price', 0)),
            'previous_close': float(merged.get('previous_close', 0)),
            'day_high': float(merged.get('day_high', 0)),
            'day_low': float(merged.get('day_low', 0)),
            'volume': int(merged.get('volume', 0)),
            'currency': merged.get('currency', 'INR' if market == 'INDIA' else 'USD'),
            'timestamp': merged.get('timestamp', datetime.now().isoformat()),
            'provider': f"Smart ({'+'.join(set(sources))})"  # e.g., "Smart (yfinance+alpha_vantage)"
        }
        
        return final_result
    
    def _calculate_quality_score(self, data: Dict[str, Any]) -> float:
        """
        Calculate quality score for API response.
        
        Scoring (0-100):
        - Completeness: 50 points (% of required fields)
        - Response time: 30 points (faster = better)
        - Freshness: 20 points (newer = better)
        """
        score = 0.0
        
        # Completeness (50 points)
        required_fields = ['current_price', 'previous_close', 'day_high', 'day_low', 'volume']
        populated = sum(1 for f in required_fields if data.get(f))
        completeness = (populated / len(required_fields)) * 50
        score += completeness
        
        # Response time (30 points)
        # Faster = better (0-3 seconds range)
        response_time = data.get('_response_time', 2.0)
        time_score = max(0, 30 - (response_time * 10))
        score += time_score
        
        # Freshness (20 points) - assume all real-time
        score += 20
        
        return score
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        return {
            "cache_stats": self.cache.get_stats(),
            "timestamp": datetime.now().isoformat()
        }


# Global instance (created on-demand)
_smart_orchestrator_instance: Optional[SmartAPIOrchestrator] = None


def get_smart_orchestrator() -> SmartAPIOrchestrator:
    """
    Get global Smart Orchestrator instance.
    
    Returns:
        SmartAPIOrchestrator instance (singleton)
    """
    global _smart_orchestrator_instance
    
    if _smart_orchestrator_instance is None:
        _smart_orchestrator_instance = SmartAPIOrchestrator()
    
    return _smart_orchestrator_instance


# Create global instance for easy import
smart_orchestrator = get_smart_orchestrator()
