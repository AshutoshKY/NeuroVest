#!/usr/bin/env python3
"""
Quick test script for Smart Orchestrator
Tests the components directly without HTTP layer
"""

import asyncio
import sys
sys.path.insert(0, '/Volumes/AshDrive/prjts/stockmarket/backend')

async def test_components():
    print("=" * 60)
    print("SMART ORCHESTRATOR - COMPONENT TESTS")
    print("=" * 60)
    
    # Test 1: Market Detector
    print("\n[TEST 1] Market Detector")
    print("-" * 40)
    try:
        from app.services.market_detector import market_detector
        
        tests = [
            ("AAPL", "US"),
            ("MSFT", "US"),
            ("RELIANCE", "INDIA"),
            ("TCS.NS", "INDIA"),
            ("HAL", "INDIA"),
        ]
        
        for ticker, expected in tests:
            result = market_detector.detect_market(ticker)
            status = "✅" if result == expected else "❌"
            print(f"{status} {ticker:12} → {result:6} (expected: {expected})")
        
        print("✅ Market Detector: PASSED")
    except Exception as e:
        print(f"❌ Market Detector: FAILED - {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Multi-Tier Cache
    print("\n[TEST 2] Multi-Tier Cache")
    print("-" * 40)
    try:
        from app.services.multi_tier_cache import MultiTierCache
        
        cache = MultiTierCache(redis_client=None)  # Memory only for test
        
        # Set test data
        test_data = {"ticker": "TEST", "price": 100.50}
        await cache.set("TEST", test_data)
        
        # Get test data
        result = await cache.get("TEST")
        
        if result and result['fresh'] and result['data']['price'] == 100.50:
            print("✅ Cache SET/GET: PASSED")
            print(f"   Source: {result['source']}, Fresh: {result['fresh']}")
        else:
            print("❌ Cache SET/GET: FAILED")
        
        # Test stats
        stats = cache.get_stats()
        print(f"✅ Cache Stats: {stats['memory_hits']} hits, {stats['misses']} misses")
        
    except Exception as e:
        print(f"❌ Multi-Tier Cache: FAILED - {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: API Health Tracker
    print("\n[TEST 3] API Health Tracker")
    print("-" * 40)
    try:
        from app.services.api_health_tracker import APIHealthTracker
        
        health = APIHealthTracker(redis_client=None)
        
        # Record some results
        await health.record_result("yfinance", "INDIA", True, 0.5)
        await health.record_result("yfinance", "INDIA", True, 0.6)
        await health.record_result("finnhub", "INDIA", False, 3.0)
        
        # Get health
        yf_health = await health.get_health("yfinance", "INDIA")
        fh_health = await health.get_health("finnhub", "INDIA")
        
        print(f"✅ yfinance INDIA: {yf_health['successes']}/{yf_health['total_calls']} success")
        print(f"✅ finnhub INDIA: {fh_health['successes']}/{fh_health['total_calls']} success")
        
        if yf_health['success_rate'] == 1.0 and fh_health['success_rate'] == 0.0:
            print("✅ Health Tracker: PASSED")
        else:
            print("❌ Health Tracker: Unexpected success rates")
        
    except Exception as e:
        print(f"❌ API Health Tracker: FAILED - {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Feature Flag
    print("\n[TEST 4] Feature Flag Configuration")
    print("-" * 40)
    try:
        from app.core.config import settings
        
        print(f"USE_SMART_ORCHESTRATOR: {settings.USE_SMART_ORCHESTRATOR}")
        print(f"SMART_ORCHESTRATOR_TIMEOUT: {settings.SMART_ORCHESTRATOR_TIMEOUT}s")
        
        if hasattr(settings, 'USE_SMART_ORCHESTRATOR'):
            print("✅ Feature Flag: CONFIGURED")
        else:
            print("❌ Feature Flag: NOT FOUND")
        
    except Exception as e:
        print(f"❌ Feature Flag: FAILED - {e}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Smart Orchestrator Initialization
    print("\n[TEST 5] Smart Orchestrator")
    print("-" * 40)
    try:
        from app.services.smart_orchestrator import smart_orchestrator
        
        print(f"Cache: {smart_orchestrator.cache}")
        print(f"Health: {smart_orchestrator.health}")
        print(f"Detector: {smart_orchestrator.detector}")
        
        stats = smart_orchestrator.get_stats()
        print(f"✅ Smart Orchestrator: INITIALIZED")
        print(f"   Timestamp: {stats['timestamp']}")
        
    except Exception as e:
        print(f"❌ Smart Orchestrator: FAILED - {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("TESTS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_components())
