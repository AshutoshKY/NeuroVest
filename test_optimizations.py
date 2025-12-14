"""
Quick test script to validate the optimized components.

Tests:
1. RSS Aggregator
2. Async Sentiment Analysis
3. ChromaDB Temporal Retrieval

Run: python3 test_optimizations.py
"""

import asyncio
import sys
import os
import time
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_rss_aggregator():
    """Test RSS news aggregator."""
    print("\n" + "="*80)
    print("TEST 1: RSS NEWS AGGREGATOR")
    print("="*80)
    
    try:
        from app.scrapers.rss_news_aggregator import rss_aggregator
        
        test_stocks = [
            ('RELIANCE', 'Reliance Industries'),
            ('TCS', 'Tata Consultancy Services'),
            ('HDFCBANK', 'HDFC Bank'),
        ]
        
        for ticker, company in test_stocks:
            print(f"\n📰 Testing {ticker} ({company})...")
            start = time.time()
            
            articles = await rss_aggregator.get_news_for_stock(
                ticker=ticker,
                company_name=company,
                max_articles=5
            )
            
            duration = time.time() - start
            
            print(f"  ✅ Found {len(articles)} articles in {duration:.2f}s")
            if articles:
                for i, article in enumerate(articles[:2], 1):
                    print(f"    {i}. {article['title'][:60]}... ({article['source_feed']})")
            
            stats = rss_aggregator.get_stats()
            print(f"  📊 Stats: {stats['feeds_succeeded']}/{stats['feeds_attempted']} feeds, "
                  f"{stats['filtered_entries']}/{stats['total_entries']} relevant")
        
        print("\n✅ RSS Aggregator Test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ RSS Aggregator Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_async_sentiment():
    """Test async parallel sentiment analysis."""
    print("\n" + "="*80)
    print("TEST 2: ASYNC PARALLEL SENTIMENT")
    print("="*80)
    
    try:
        from app.services.sentiment import sentiment_service
        
        test_texts = [
            "Reliance stock surges 5% on strong quarterly results",
            "HDFC Bank reports 20% profit growth, beats estimates",
            "TCS wins $500M contract from Fortune 500 company",
            "Market crash expected as global tensions rise",
            "Infosys announces massive layoffs amid restructuring"
        ]
        
        print(f"\n📊 Testing with {len(test_texts)} articles...")
        
        # Test async (parallel)
        print("\n  Testing ASYNC (parallel)...")
        start = time.time()
        results_async = await sentiment_service.analyze_batch_sentiment_async(
            texts=test_texts,
            ticker="TEST"
        )
        duration_async = time.time() - start
        
        print(f"  ✅ Async completed in {duration_async:.2f}s")
        for i, (text, result) in enumerate(zip(test_texts, results_async), 1):
            sentiment = result['classification']
            score = result['sentiment_score']
            print(f"    {i}. {sentiment} ({score:+.2f}): {text[:50]}...")
        
        # Aggregate
        aggregate = sentiment_service.aggregate_sentiment(results_async)
        print(f"\n  📊 Aggregate: {aggregate['classification']} "
              f"(score: {aggregate['aggregate_score']:.2f}, "
              f"Bull:{aggregate['bullish_count']}/Bear:{aggregate['bearish_count']}/Neut:{aggregate['neutral_count']})")
        
        print("\n✅ Async Sentiment Test PASSED")
        print(f"  Performance: {len(test_texts)} articles in {duration_async:.2f}s "
              f"({duration_async/len(test_texts):.2f}s per article in parallel)")
        return True
        
    except Exception as e:
        print(f"\n❌ Async Sentiment Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_intelligent_news_service():
    """Test intelligent news service orchestrator."""
    print("\n" + "="*80)
    print("TEST 3: INTELLIGENT NEWS SERVICE")
    print("="*80)
    
    try:
        from app.scrapers.intelligent_news_service import intelligent_news_service
        
        ticker = "RELIANCE"
        company = "Reliance Industries"
        
        print(f"\n🎯 Testing {ticker} ({company})...")
        start = time.time()
        
        articles = await intelligent_news_service.get_news(
            ticker=ticker,
            company_name=company,
            min_articles=3,
            max_articles=5
        )
        
        duration = time.time() - start
        
        print(f"  ✅ Got {len(articles)} articles in {duration:.2f}s")
        
        # Show layer breakdown
        layers = intelligent_news_service._get_layers_used(articles)
        print(f"  📊 Layers used: {layers}")
        
        if articles:
            for i, article in enumerate(articles[:3], 1):
                layer = article.get('acquisition_layer', 'unknown')
                quality = article.get('quality_score', 0)
                print(f"    {i}. [{layer}] (Q:{quality:.2f}) {article['title'][:50]}...")
        
        # Show stats
        stats = intelligent_news_service.get_stats()
        print(f"\n  📈 Service Stats:")
        for layer_name, layer_stats in stats.items():
            if layer_stats['attempts'] > 0:
                success_rate = (layer_stats['successes'] / layer_stats['attempts'] * 100)
                print(f"    {layer_name}: {layer_stats['successes']}/{layer_stats['attempts']} "
                      f"({success_rate:.0f}%), {layer_stats['articles']} articles")
        
        print("\n✅ Intelligent News Service Test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Intelligent News Service Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all tests."""
    print("\n" + "="*80)
    print("🧪 RUNNING OPTIMIZATION COMPONENT TESTS")
    print("="*80)
    print(f"Time: {datetime.now().isoformat()}")
    
    results = []
    
    # Test 1: RSS
    results.append(("RSS Aggregator", await test_rss_aggregator()))
    
    # Test 2: Sentiment
    results.append(("Async Sentiment", await test_async_sentiment()))
    
    # Test 3: Intelligent News Service
    results.append(("Intelligent News", await test_intelligent_news_service()))
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name:30} {status}")
    
    print(f"\n  TOTAL: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
