"""
Enhanced data ingestion service with async scraping and comprehensive logging.
"""
import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path
from app.core.config import settings
from app.scrapers.scraper_factory import load_scrapers
from app.services.preprocessing import preprocessing_service
from app.services.embeddings import embedding_service
from app.services.stock_api_service import stock_api_service

from app.core.database import get_db
from sqlalchemy.orm import Session
import time

logger = logging.getLogger(__name__)


class IngestionReport:
    """Report of ingestion operation results."""
    
    def __init__(self):
        self.sources = []
        self.total_articles = 0
        self.total_chunks = 0
        self.total_errors = 0
        self.start_time = datetime.now()
        self.end_time = None
        
    def add_source_result(self, source: str, success: bool, articles: int, chunks: int = 0, error: str = None):
        """Add result for a data source."""
        self.sources.append({
            'source': source,
            'success': success,
            'articles_count': articles,
            'chunks_count': chunks,
            'error': error
        })
        
        if success:
            self.total_articles += articles
            self.total_chunks += chunks
        else:
            self.total_errors += 1
    
    def complete(self):
        """Mark report as complete."""
        self.end_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        duration = (self.end_time - self.start_time).total_seconds() if self.end_time else 0
        
        return {
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': duration,
            'sources': self.sources,
            'total_articles': self.total_articles,
            'total_chunks': self.total_chunks,
            'total_errors': self.total_errors,
            'success_rate': (len([s for s in self.sources if s['success']]) / len(self.sources) * 100) if self.sources else 0
        }


class DataIngestionService:
    """Service for ingesting data from multiple sources with async support."""
    
    def __init__(self):
        """Initialize data ingestion service."""
        self.data_dir = Path(settings.DATA_DIR)
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        
        # Create directories
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    

    async def fetch_stock_data(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch stock data using multi-API service with fallback.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Stock data dictionary
        """
        start_time = time.time()
        
        try:
            logger.info("📊 Fetching stock data", extra={
                "operation": "fetch_stock_data",
                "ticker": ticker
            })
            
            data = await stock_api_service.get_stock_data(ticker)
            
            duration_ms = int((time.time() - start_time) * 1000)
            

            
            logger.info("✅ Stock data fetched successfully", extra={
                "operation": "fetch_stock_data",
                "ticker": ticker,
                "provider": data.get('provider', 'Unknown'),
                "duration_ms": duration_ms,
                "status": "success"
            })
            
            return data
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            logger.error("❌ Failed to fetch stock data", extra={
                "operation": "fetch_stock_data",
                "ticker": ticker,
                "duration_ms": duration_ms,
                "status": "failure",
                "error": str(e)
            })
            

            
            return {}
    
    async def scrape_single_source(self, scraper) -> Dict[str, Any]:
        """
        Scrape from a single source asynchronously.
        
        Args:
            scraper: Scraper instance
            
        Returns:
            Result dictionary
        """
        start_time = time.time()
        source_name = scraper.name
        
        try:
            logger.info(f"🌐 Starting {source_name}...")
            
            # Scrape articles (runs in executor since it's not async)
            loop = asyncio.get_event_loop()
            articles = await loop.run_in_executor(
                None,
                scraper.scrape_latest_articles
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            logger.info("✅ Scraping completed", extra={
                "operation": "scrape_single_source",
                "source": source_name,
                "articles_count": len(articles),
                "duration_ms": duration_ms,
                "status": "success"
            })
            

            
            return {
                'source': source_name,
                'success': True,
                'articles': articles,
                'count': len(articles),
                'error': None
            }
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            
            logger.error("❌ Scraping failed", extra={
                "operation": "scrape_single_source",
                "source": source_name,
                "duration_ms": duration_ms,
                "status": "failure",
                "error": error_msg
            })
            

            
            return {
                'source': source_name,
                'success': False,
                'articles': [],
                'count': 0,
                'error': error_msg
            }
    
    async def scrape_all_sources(self) -> List[Dict[str, Any]]:
        """
        Scrape all configured sources in parallel.
        
        Returns:
            List of results from each source
        """
        scrapers = []  # Initialize at the start to prevent UnboundLocalError
        logger.info("🚀 Starting parallel scraping", extra={
            "operation": "scrape_all_sources",
            "scraper_count": len(scrapers) if scrapers else 0
        })
        
        # Load all enabled scrapers
        scrapers = load_scrapers()
        
        if not scrapers:
            logger.warning("No scrapers loaded", extra={
                "operation": "scrape_all_sources",
                "status": "warning"
            })
            return []
        
        logger.info(f"Loaded {len(scrapers)} scrapers")
        
        # Scrape all sources in parallel
        tasks = [self.scrape_single_source(scraper) for scraper in scrapers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Scraping task failed: {result}")
            else:
                valid_results.append(result)
        
        successful = len([r for r in valid_results if r['success']])
        total_articles = sum(r['count'] for r in valid_results if r['success'])
        
        logger.info("✅ Parallel scraping complete", extra={
            "operation": "scrape_all_sources",
            "successful_sources": successful,
            "total_sources": len(valid_results),
            "total_articles": total_articles,
            "status": "success"
        })
        
        return valid_results
    
    async def fetch_api_news(self) -> List[Dict[str, Any]]:
        """
        Fetch news from stock APIs for tracked tickers.
        
        Returns:
            List of results
        """
        logger.info("📡 Fetching news from Stock APIs...")
        
        # Tracked defense stocks
        tickers = ["HAL", "BEL", "BDL", "MDL", "GRSE", "BEML"]
        results = []
        
        for ticker in tickers:
            try:
                # Fetch news for ticker
                news_items = await stock_api_service.get_company_news(ticker)
                
                if not news_items:
                    continue
                
                # Convert to article format
                articles = []
                for item in news_items:
                    # Finnhub format
                    article = {
                        'title': item.get('headline', ''),
                        'content': item.get('summary', ''),
                        'url': item.get('url', ''),
                        'timestamp': datetime.fromtimestamp(item.get('datetime', 0)).isoformat(),
                        'source': item.get('source', 'Finnhub'),
                        'raw_html': item.get('summary', '')  # Use summary as raw content
                    }
                    articles.append(article)
                
                results.append({
                    'source': f"Finnhub - {ticker}",
                    'success': True,
                    'articles': articles,
                    'count': len(articles),
                    'error': None
                })
                
                logger.info(f"✅ Fetched {len(articles)} news items for {ticker} from API")
                
            except Exception as e:
                logger.error(f"❌ Failed to fetch API news for {ticker}: {e}")
                results.append({
                    'source': f"Finnhub - {ticker}",
                    'success': False,
                    'articles': [],
                    'count': 0,
                    'error': str(e)
                })
        
        return results

    async def ingest_for_ticker(self, ticker: str, company_name: str = None) -> int:
        """
        On-demand ingestion for a specific ticker.
        Tries Scraper V2 (Web Search) first, then falls back to V1 (RSS).
        
        Args:
            ticker: Stock ticker symbol
            company_name: Optional full company name for better search
            
        Returns:
            Number of articles ingested
        """
        logger.info("🔄 Starting on-demand ingestion", extra={
            "operation": "ingest_for_ticker",
            "ticker": ticker,
            "company_name": company_name or ticker
        })
        
        # Construct search query
        search_term = f"{company_name} {ticker}" if company_name else ticker
        
        # --- STRATEGY 1: Intelligent News Service (RSS-First with Fallback) ---
        try:
            logger.info("🎯 Trying Intelligent News Service (RSS-first)", extra={
                "operation": "ingest_for_ticker",
                "ticker": ticker,
                "strategy": "intelligent_news_service"
            })
            from app.scrapers.intelligent_news_service import intelligent_news_service
            
            # Get news through intelligent multi-layer system
            # This will try: RSS → Direct Scraper → DuckDuckGo
            articles = await intelligent_news_service.get_news(
                ticker=ticker,
                company_name=company_name or ticker,
                min_articles=3,
                max_articles=5
            )
            
            if articles:
                # Inject ticker context for metadata tagging
                for article in articles:
                    article['ticker_context'] = ticker
                    
                chunks = self.process_and_store_articles(articles, "Intelligent News Service")
                logger.info("✅ Intelligent News Service succeeded", extra={
                    "operation": "ingest_for_ticker",
                    "ticker": ticker,
                    "strategy": "intelligent_news_service",
                    "articles_count": len(articles),
                    "chunks_count": chunks,
                    "status": "success",
                    "layers_used": intelligent_news_service._get_layers_used(articles)
                })
                return len(articles)
            else:
                logger.warning("⚠️  Intelligent News Service found no articles, falling back to RSS", extra={
                    "operation": "ingest_for_ticker",
                    "ticker": ticker,
                })
                
        except Exception as e:
            logger.error(f"❌ Intelligent News Service failed: {e}", exc_info=True, extra={
                "operation": "ingest_for_ticker",
                "ticker": ticker,
                "strategy": "intelligent_news_service",
                "error": str(e),
                "error_type": type(e).__name__,
                "fallback": "rss"
            })

        # --- STRATEGY 2: Scraper V1 (Google News RSS Fallback) ---
        try:
            logger.info("📡 Trying RSS scraper (V1)", extra={
                "operation": "ingest_for_ticker",
                "ticker": ticker,
                "strategy": "rss"
            })
            
            encoded_query = f"{search_term} stock news india".replace(" ", "+")
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
            
            config = {
                'name': f"RSS Fallback: {ticker}",
                'url': rss_url,
                'max_articles': 15,  # BUG FIX: Changed from 5 to 15
                'delay_seconds': 1
            }
            
            from app.scrapers.rss_scraper import RSSScraper
            scraper = RSSScraper(config)
            
            result = await self.scrape_single_source(scraper)
            
            if result['success'] and result['articles']:
                chunks = self.process_and_store_articles(
                    result['articles'],
                    result['source']
                )
                logger.info("✅ RSS scraper succeeded", extra={
                    "operation": "ingest_for_ticker",
                    "ticker": ticker,
                    "strategy": "rss",
                    "articles_count": len(result['articles']),
                    "chunks_count": chunks,
                    "status": "success"
                })
                return len(result['articles'])
            else:
                logger.warning("⚠️ RSS scraper found no articles", extra={
                    "operation": "ingest_for_ticker",
                    "ticker": ticker,
                    "strategy": "rss"
                })
                return 0
                
        except Exception as e:
            logger.error("❌ RSS scraper failed", extra={
                "operation": "ingest_for_ticker",
                "ticker": ticker,
                "strategy": "rss",
                "status": "failure",
                "error": str(e)
            })
            return 0

    def process_and_store_articles(self, articles: List[Dict[str, Any]], source_name: str) -> int:
        """
        Process articles and store in vector database.
        
        Args:
            articles: List of raw articles
            source_name: Name of the source
            
        Returns:
            Number of chunks stored
        """
        start_time = time.time()
        chunks_stored = 0
        
        try:
            # DEDUPLICATION: Remove duplicate URLs
            seen_urls = set()
            unique_articles = []
            duplicates_removed = 0
            
            for article in articles:
                url = article.get('url', '')
                if url and url in seen_urls:
                    duplicates_removed += 1
                    continue
                if url:
                    seen_urls.add(url)
                unique_articles.append(article)
            
            if duplicates_removed > 0:
                logger.info(f"🔄 Removed {duplicates_removed} duplicate URLs from {source_name}")
            
            documents = []
            metadatas = []
            ids = []
            
            for idx, article in enumerate(unique_articles):
                try:
                    # Process article
                    processed = preprocessing_service.process_article(
                        raw_html=article.get('raw_html', article.get('content', '')),
                        source=article.get('source', source_name),
                        url=article.get('url', '')
                    )
                    
                    # Extract tickers
                    tickers = processed['metadata'].get('tickers', [])
                    
                    # CRITICAL FIX: Ensure the target ticker is included in metadata
                    # Preprocessing might miss it if it's not in the hardcoded list or regex
                    # Since we searched for this specific ticker, we tag the content with it
                    target_ticker = article.get('ticker_context') # Passed from ingest_for_ticker
                    if target_ticker and target_ticker not in tickers:
                        tickers.append(target_ticker)
                    
                    # Store each chunk
                    for chunk_idx, chunk in enumerate(processed['chunks']):
                        doc_id = f"{source_name}_{idx}_{chunk_idx}_{int(datetime.now().timestamp())}"
                        
                        metadata = {
                            'title': article.get('title', ''),
                            'source': processed['metadata']['source'],
                            'url': processed['metadata']['url'],
                            'timestamp': article.get('timestamp', datetime.now().isoformat()),
                            'ticker': tickers[0] if tickers else "",
                            'all_tickers': ",".join(tickers),
                            'keywords': ",".join(processed['metadata'].get('keywords', [])[:10])
                        }
                        
                        documents.append(chunk)
                        metadatas.append(metadata)
                        ids.append(doc_id)
                    
                except Exception as e:
                    logger.error(f"Error processing article: {e}")
                    continue
            
            # Add to vector database
            if documents:
                embedding_service.add_documents(documents, metadatas, ids)
                chunks_stored = len(documents)
                
                duration_ms = int((time.time() - start_time) * 1000)
                
                logger.info("✅ Articles stored successfully", extra={
                    "operation": "process_and_store_articles",
                    "source": source_name,
                    "chunks_count": chunks_stored,
                    "duration_ms": duration_ms,
                    "status": "success"
                })
                

            
            return chunks_stored
            
        except Exception as e:
            logger.error("❌ Error storing articles", extra={
                "operation": "process_and_store_articles",
                "source": source_name,
                "status": "failure",
                "error": str(e)
            })
            

            
            return 0
    
    async def run_ingestion_pipeline(self) -> IngestionReport:
        """
        Run complete data ingestion pipeline with async scraping.
        
        Returns:
            Ingestion report
        """
        logger.info("=" * 80)
        logger.info("🚀 STARTING DATA INGESTION PIPELINE")
        logger.info("=" * 80)
        
        report = IngestionReport()
        
        try:
            # Scrape all sources in parallel
            scrape_results = await self.scrape_all_sources()
            
            # Fetch news from APIs
            api_news_results = await self.fetch_api_news()
            scrape_results.extend(api_news_results)
            
            # Process and store articles from each source
            for result in scrape_results:
                if result['success'] and result['articles']:
                    chunks = self.process_and_store_articles(
                        result['articles'],
                        result['source']
                    )
                    
                    report.add_source_result(
                        source=result['source'],
                        success=True,
                        articles=result['count'],
                        chunks=chunks
                    )
                else:
                    report.add_source_result(
                        source=result['source'],
                        success=False,
                        articles=0,
                        error=result.get('error')
                    )
            
            # Get final stats
            total_docs = embedding_service.get_collection_count()
            
            report.complete()
            
            logger.info("=" * 80)
            logger.info(f"✅ INGESTION COMPLETE")
            logger.info(f"   Articles: {report.total_articles}")
            logger.info(f"   Chunks: {report.total_chunks}")
            logger.info(f"   Errors: {report.total_errors}")
            logger.info(f"   Total in DB: {total_docs}")
            logger.info(f"   Duration: {report.to_dict()['duration_seconds']:.2f}s")
            logger.info("=" * 80)
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Ingestion pipeline failed: {e}", exc_info=True)
            report.complete()
            return report
    



# Global instance
data_ingestion_service = DataIngestionService()
