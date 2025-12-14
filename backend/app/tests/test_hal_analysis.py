"""
End-to-end pipeline testing for HAL stock.
"""
import sys
sys.path.insert(0, '/app')

import time
import asyncio
from app.services.data_ingestion import data_ingestion_service  
from app.services.rag import rag_service
from app.services.embeddings import embedding_service


async def test_hal_complete_flow():
    """Test complete analysis flow for HAL stock."""
    ticker = "HAL"
    
    print("\n" + "="*60)
    print(f"END-TO-END PIPELINE TEST FOR {ticker}")
    print("="*60)
    
    # 1. Fetch stock data
    print(f"\n[1/4] Fetching stock data for {ticker}...")
    start_time = time.time()
    try:
        stock_data = await data_ingestion_service.fetch_stock_data(ticker)
        fetch_time = time.time() - start_time
        
        print(f"   ✓ Stock Data Retrieved ({fetch_time:.2f}s)")
        print(f"   Current Price: ₹{stock_data.get('current_price', 0):.2f}")
        print(f"   Provider: {stock_data.get('provider', 'Unknown')}")
    except Exception as e:
        print(f"   ✗ Failed: {str(e)}")
        stock_data = {}
        fetch_time = 0
    
    # 2. Scrape news
    print(f"\n[2/4] Scraping news articles for {ticker}...")
    start_time = time.time()
    try:
        report = await data_ingestion_service.fetch_news_for_ticker(ticker)
        scrape_time = time.time() - start_time
        
        print(f"   ✓ News Scraped ({scrape_time:.2f}s)")
        print(f"   Total Articles: {report.total_articles}")
        print(f"   Total Chunks: {report.total_chunks}")
        print(f"   Sources: {', '.join([s['source'] for s in report.sources if s['success']])}")
    except Exception as e:
        print(f"   ✗ Failed: {str(e)}")
        scrape_time = 0
        report = None
    
    # 3. Check ChromaDB
    print(f"\n[3/4] Checking vector database...")
    try:
        doc_count = embedding_service.get_collection_count()
        print(f"   ✓ ChromaDB Documents: {doc_count}")
    except Exception as e:
        print(f"   ✗ Failed: {str(e)}")
    
    # 4. Generate analysis
    print(f"\n[4/4] Generating AI analysis for {ticker}...")
    start_time = time.time()
    try:
        analysis = await rag_service.generate_analysis(
            query=f"Analyze {ticker} stock",
            ticker=ticker,
            n_results=10
        )
        analysis_time = time.time() - start_time
        
        print(f"   ✓ Analysis Generated ({analysis_time:.2f}s)")
        print(f"   Cached: {analysis.get('cached', False)}")
        print(f"   Sentiment: {analysis['sentiment']['classification'].upper()}")
        print(f"   Confidence: {analysis['sentiment'].get('confidence', 0):.2%}")
        print(f"   References: {len(analysis.get('references', []))}")
        
        # Print analysis excerpt
        print(f"\n   Analysis Preview:")
        analysis_text = analysis.get('analysis', '')
        lines = analysis_text.split('\n')
        for line in lines[:3]:
            if line.strip():
                print(f"   > {line.strip()[:70]}...")
        
        # Print key insights
        print(f"\n   Key Insights:")
        for i, insight in enumerate(analysis.get('key_insights', [])[:3], 1):
            print(f"   {i}. {insight}")
        
        # Print risk factors
        print(f"\n   Risk Factors:")
        for i, risk in enumerate(analysis.get('risk_factors', [])[:3], 1):
            print(f"   {i}. {risk}")
        
    except Exception as e:
        print(f"   ✗ Failed: {str(e)}")
        analysis_time = 0
        analysis = {}
    
    # 5. Test caching
    print(f"\n[BONUS] Testing cache...")
    start_time = time.time()
    try:
        cached_analysis = await rag_service.generate_analysis(
            query=f"Analyze {ticker} stock",
            ticker=ticker
        )
        cache_time = time.time() - start_time
        
        is_cached = cached_analysis.get('cached', False)
        print(f"   ✓ Cache {'HIT' if is_cached else 'MISS'} ({cache_time:.2f}s)")
        
        if is_cached and cache_time >= 1.0:
            print(f"   ⚠️  Warning: Cache response slower than expected")
        elif is_cached:
            print(f"   ✓ Cache performance optimal (< 1s)")
    except Exception as e:
        print(f"   ✗ Failed: {str(e)}")
        cache_time = 0
    
    # Summary
    print(f"\n" + "="*60)
    print("PERFORMANCE SUMMARY")
    print("="*60)
    print(f"   Stock Data Fetch:  {fetch_time:6.2f}s")
    print(f"   News Scraping:     {scrape_time:6.2f}s")
    print(f"   Analysis (first):  {analysis_time:6.2f}s")
    print(f"   Analysis (cached): {cache_time:6.2f}s")
    print(f"   {'─'*56}")
    print(f"   Total Time:        {fetch_time + scrape_time + analysis_time:6.2f}s")
    
    # Assessment
    print(f"\n" + "="*60)
    total_time = fetch_time + scrape_time + analysis_time
    if total_time > 0 and total_time < 60:
        print(f"✅ PASS: Complete analysis pipeline functional")
        print(f"   Performance: {'Excellent' if total_time < 30 else 'Good'}")
    elif total_time >= 60:
        print(f"⚠️  WARNING: Analysis took longer than expected ({total_time:.0f}s)")
    else:
        print(f"❌ FAIL: Pipeline errors detected")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(test_hal_complete_flow())
