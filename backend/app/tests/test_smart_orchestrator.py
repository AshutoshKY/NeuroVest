"""
Smart Orchestrator Test Suite
==============================

Tests for the smart API orchestrator to ensure:
1. Backward compatibility with existing code
2. Proper market detection
3. Cache functionality
4. Health tracking
5. Feature flag routing

Run: pytest backend/app/tests/test_smart_orchestrator.py -v
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Test imports
from app.services.market_detector import market_detector
from app.services.multi_tier_cache import MultiTierCache
from app.services.api_health_tracker import APIHealthTracker
from app.services.smart_orchestrator import SmartAPIOrchestrator


class TestMarketDetector:
    """Test market detection logic."""
    
    def test_detect_us_stocks(self):
        """Test US stock detection."""
        assert market_detector.detect_market("AAPL") == "US"
        assert market_detector.detect_market("MSFT") == "US"
        assert market_detector.detect_market("GOOGL") == "US"
    
    def test_detect_indian_stocks_with_suffix(self):
        """Test Indian stock detection with suffix."""
        assert market_detector.detect_market("RELIANCE.NS") == "INDIA"
        assert market_detector.detect_market("TCS.NS") == "INDIA"
        assert market_detector.detect_market("INFY.BO") == "INDIA"
    
    def test_detect_indian_stocks_without_suffix(self):
        """Test Indian stock detection without suffix."""
        assert market_detector.detect_market("RELIANCE") == "INDIA"
        assert market_detector.detect_market("TCS") == "INDIA"
        assert market_detector.detect_market("HAL") == "INDIA"
    
    def test_normalize_ticker(self):
        """Test ticker normalization."""
        assert market_detector.normalize_ticker("RELIANCE", "INDIA") == "RELIANCE.NS"
        assert market_detector.normalize_ticker("AAPL", "US") == "AAPL"
        assert market_detector.normalize_ticker("TCS.NS", "INDIA") == "TCS.NS"


@pytest.mark.asyncio
class TestMultiTierCache:
    """Test multi-tier caching."""
    
    async def test_cache_miss(self):
        """Test cache miss scenario."""
        cache = MultiTierCache(redis_client=None)
        result = await cache.get("NONEXISTENT")
        assert result is None
    
    async def test_cache_set_and_get(self):
        """Test setting and getting from cache."""
        cache = MultiTierCache(redis_client=None)
        
        test_data = {
            "ticker": "TEST",
            "current_price": 100.50,
            "volume": 1000000
        }
        
        # Set
        await cache.set("TEST", test_data)
        
        # Get
        result = await cache.get("TEST")
        assert result is not None
        assert result['fresh'] is True
        assert result['source'] == 'memory'
        assert result['data']['ticker'] == "TEST"
        assert result['data']['current_price'] == 100.50
    
    async def test_cache_expiry(self):
        """Test cache expiration."""
        cache = MultiTierCache(redis_client=None)
        cache.MEMORY_TTL = 0.1  # 100ms for testing
        
        test_data = {"ticker": "TEST"}
        await cache.set("TEST", test_data)
        
        # Immediate get should work
        result = await cache.get("TEST")
        assert result is not None
        
        # Wait for expiry
        await asyncio.sleep(0.2)
        
        # Should be expired from memory (no Redis in test)
        result = await cache.get("TEST")
        assert result is None
    
    def test_cache_stats(self):
        """Test cache statistics."""
        cache = MultiTierCache(redis_client=None)
        stats = cache.get_stats()
        
        assert 'memory_hits' in stats
        assert 'redis_hits' in stats
        assert 'misses' in stats
        assert 'hit_rate_percent' in stats


@pytest.mark.asyncio
class TestAPIHealthTracker:
    """Test API health tracking."""
    
    async def test_record_success(self):
        """Test recording successful API call."""
        health = APIHealthTracker(redis_client=None)
        
        await health.record_result("yfinance", "INDIA", success=True, response_time=0.5)
        
        stats = await health.get_health("yfinance", "INDIA")
        assert stats['total_calls'] == 1
        assert stats['successes'] == 1
        assert stats['failures'] == 0
        assert stats['success_rate'] == 1.0
    
    async def test_record_failure(self):
        """Test recording failed API call."""
        health = APIHealthTracker(redis_client=None)
        
        await health.record_result("finnhub", "INDIA", success=False, response_time=3.0)
        
        stats = await health.get_health("finnhub", "INDIA")
        assert stats['total_calls'] == 1
        assert stats['successes'] == 0
        assert stats['failures'] == 1
        assert stats['success_rate'] == 0.0
    
    async def test_circuit_breaker_opens(self):
        """Test circuit breaker opens after failures."""
        health = APIHealthTracker(redis_client=None)
        health.CIRCUIT_BREAKER_THRESHOLD = 0.3
        health.MAX_RECENT_CALLS = 10
        
        # Record 10 failures
        for _ in range(10):
            await health.record_result("bad_api", "INDIA", success=False)
        
        # Circuit should be open
        should_skip = await health.should_skip_api("bad_api", "INDIA")
        assert should_skip is True
    
    async def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery."""
        health = APIHealthTracker(redis_client=None)
        health.CIRCUIT_RECOVERY_TIME = 0.1  # 100ms for testing
        
        # Open circuit
        for _ in range(10):
            await health.record_result("recovering_api", "US", success=False)
        
        # Verify circuit is open
        assert await health.should_skip_api("recovering_api", "US") is True
        
        # Wait for recovery time
        await asyncio.sleep(0.2)
        
        # Circuit should allow test call
        should_skip = await health.should_skip_api("recovering_api", "US")
        assert should_skip is False


@pytest.mark.asyncio
class TestSmartOrchestrator:
    """Test smart orchestrator integration."""
    
    async def test_initialization(self):
        """Test orchestrator initialization."""
        # Mock StockAPIService
        mock_service = Mock()
        mock_service.apis = []
        
        orchestrator = SmartAPIOrchestrator(stock_api_service=mock_service)
        
        assert orchestrator.stock_api_service == mock_service
        assert orchestrator.cache is not None
        assert orchestrator.health is not None
        assert orchestrator.detector is not None
    
    async def test_api_selection_for_india(self):
        """Test API selection for Indian stocks."""
        mock_service = Mock()
        mock_service.apis = []
        
        orchestrator = SmartAPIOrchestrator(stock_api_service=mock_service)
        
        apis = await orchestrator._select_apis("RELIANCE", "INDIA")
        
        # Should select yfinance + alpha_vantage for India
        assert "yfinance" in apis or "alpha_vantage" in apis
    
    async def test_api_selection_for_us(self):
        """Test API selection for US stocks."""
        mock_service = Mock()
        mock_service.apis = []
        
        orchestrator = SmartAPIOrchestrator(stock_api_service=mock_service)
        
        apis = await orchestrator._select_apis("AAPL", "US")
        
        # Should select finnhub + yfinance for US
        assert "finnhub" in apis or "yfinance" in apis
    
    async def test_data_merge(self):
        """Test data merging from multiple sources."""
        mock_service = Mock()
        orchestrator = SmartAPIOrchestrator(stock_api_service=mock_service)
        
        # Mock results from two APIs
        results = [
            {
                'current_price': 100.50,
                'previous_close': 99.00,
                'day_high': 101.00,
                'day_low': None,  # Missing
                'volume': 1000000,
                '_api_source': 'api1',
                '_response_time': 0.5
            },
            {
                'current_price': None,  # Missing
                'previous_close': 99.00,
                'day_high': None,  # Missing
                'day_low': 98.50,  # Has this
                'volume': 1000000,
                '_api_source': 'api2',
                '_response_time': 0.7
            }
        ]
        
        merged = await orchestrator._merge_results(results, "TEST", "INDIA")
        
        # Should have data from both sources
        assert merged is not None
        assert merged['current_price'] == 100.50  # From api1
        assert merged['day_low'] == 98.50  # From api2
        assert 'api1' in merged['provider'] or 'api2' in merged['provider']
    
    def test_quality_score_calculation(self):
        """Test quality scoring for results."""
        mock_service = Mock()
        orchestrator = SmartAPIOrchestrator(stock_api_service=mock_service)
        
        # Complete result with fast response
        good_result = {
            'current_price': 100,
            'previous_close': 99,
            'day_high': 101,
            'day_low': 98,
            'volume': 1000000,
            '_response_time': 0.5
        }
        
        # Incomplete result with slow response
        bad_result = {
            'current_price': 100,
            '_response_time': 2.5
        }
        
        good_score = orchestrator._calculate_quality_score(good_result)
        bad_score = orchestrator._calculate_quality_score(bad_result)
        
        # Good result should have higher score
        assert good_score > bad_score


@pytest.mark.asyncio
class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""
    
    async def test_return_format_matches_legacy(self):
        """Test that smart orchestrator returns same format as legacy."""
        mock_service = Mock()
        mock_service.apis = []
        
        # Mock _fetch_from_api to return data
        async def mock_fetch(api, ticker):
            return {
                'ticker': ticker,
                'exchange': 'NSE',
                'current_price': 100.50,
                'previous_close': 99.00,
                'day_high': 101.00,
                'day_low': 98.50,
                'volume': 1000000,
                'currency': 'INR',
                'timestamp': '2025-12-13T00:00:00',
                'provider': 'yfinance'
            }
        
        mock_service._fetch_from_api = mock_fetch
        mock_service.apis = [{'name': 'yfinance'}]
        
        orchestrator = SmartAPIOrchestrator(stock_api_service=mock_service)
        
        # Call enhanced method
        result = await orchestrator.get_stock_data_enhanced("TEST")
        
        # Verify it has all required fields
        required_fields = [
            'ticker', 'exchange', 'current_price', 'previous_close',
            'day_high', 'day_low', 'volume', 'currency', 'timestamp', 'provider'
        ]
        
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
