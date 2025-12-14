"""
Intelligent News Service - Multi-Layer Approach
Orchestrates RSS, Direct Scrapers, and DuckDuckGo for optimal article discovery.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class IntelligentNewsService:
    """
    Intelligent multi-layer news acquisition system.
    
    Manages automatic fallback through news sources to ensure
    reliable article acquisition with maximum quality.
    """
    
    def __init__(self):
        """Initialize news service with all layers."""
        from app.scrapers.rss_news_aggregator import rss_aggregator
        from app.scrapers.web_scraper import web_scraper
        
        self.rss_aggregator = rss_aggregator
        self.web_scraper = web_scraper
        
        # Metrics tracking
        self.stats = {
            'rss': {'attempts': 0, 'successes': 0, 'articles': 0},
            'direct': {'attempts': 0, 'successes': 0, 'articles': 0},
            'fallback': {'attempts': 0, 'successes': 0, 'articles': 0}
        }
    
    async def get_news(
        self,
        ticker: str,
        company_name: str,
        min_articles: int = 3,
        max_articles: int = 15,  # Increased from 5 for comprehensive news coverage
        req_id: str = "unknown"  # Add req_id parameter
    ) -> List[Dict[str, Any]]:
        """
        Get news articles with intelligent multi-layer fallback.
        
        Strategy:
        1. Try RSS (fast, high quality)
        2. If insufficient, try direct scraper
        3. If still insufficient, use DuckDuckGo snippets
        4. Deduplicate across all layers
        5. Return top articles by quality
        
        Args:
            ticker: Stock ticker symbol
            company_name: Full company name
            min_articles: Minimum articles to acquire
            max_articles: Maximum articles to return
            
        Returns:
            List of news articles with metadata
        """
        start_time = datetime.now()
        all_articles = []  # Match variable name used throughout function
        
        logger.info(f"🎯 [NEWS_ORCHESTRATOR_START] Starting intelligent news acquisition for {ticker}", extra={
            "operation": "intelligent_news_start",
            "ticker": ticker,
            "company_name": company_name,
            "min_articles": min_articles,
            "max_articles": max_articles,
            "timestamp": start_time.isoformat()
        })
        
        # === LAYER 1: RSS Aggregator (Primary) ===
        layer_start = time.time()  # Initialize timer
        try:
            self.stats['rss']['attempts'] += 1
            
            logger.info(f"📡 [LAYER1_START] Trying RSS aggregator for {ticker}", extra={
                "operation": "layer1_rss_start",
                "ticker": ticker,
                "layer": 1,
                "layer_name": "RSS"
            })
            
            rss_articles = await self.rss_aggregator.get_news_for_stock(
                ticker=ticker,
                company_name=company_name,
                max_articles=max_articles # Keep max_articles for RSS if it supports it
            )
            
            if rss_articles:
                # Tag articles with layer info
                for article in rss_articles:
                    article['acquisition_layer'] = 'rss'
                    article['layer_priority'] = 1
                
                all_articles.extend(rss_articles) # Use all_articles
                self.stats['rss']['successes'] += 1
                self.stats['rss']['articles'] += len(rss_articles)
                
                layer1_duration = (time.time() - layer_start)
                logger.info(f"✅ [{req_id}] [LAYER1_SUCCESS] RSS returned {len(rss_articles)} articles in {layer1_duration:.2f}s", extra={
                    "operation": "layer1_rss_success",
                    "layer": 1,
                    "ticker": ticker,
                    "articles_count": len(rss_articles),
                    "duration_seconds": layer1_duration,
                    "sources": list(set([a.get('source_feed', 'unknown') for a in rss_articles])),
                    "req_id": req_id
                })
                
                # Early exit if enough articles are found from RSS
                if len(all_articles) >= min_articles:
                    logger.info(f"[{req_id}] [LAYER1_COMPLETE] RSS provided enough articles ({len(all_articles)}/{min_articles}). Skipping further layers.", extra={
                        "operation": "layer1_complete_early_exit",
                        "ticker": ticker,
                        "articles_count": len(all_articles),
                        "req_id": req_id
                    })
                    # Deduplicate and rank before returning
                    unique_articles = self._deduplicate_across_layers(all_articles)
                    ranked_articles = self._rank_by_quality(unique_articles)
                    final_articles = ranked_articles[:max_articles]
                    duration = (datetime.now() - start_time).total_seconds()
                    logger.info(f"✅ Intelligent news service completed for {ticker}: {len(final_articles)} articles in {duration:.2f}s", extra={
                        "operation": "intelligent_news_service",
                        "ticker": ticker,
                        "total_articles": len(final_articles),
                        "duration_seconds": duration,
                        "layers_used": self._get_layers_used(final_articles),
                        "success_rate": f"{len(final_articles)}/{max_articles}",
                        "req_id": req_id
                    })
                    return final_articles
            else:
                logger.warning(f"⚠️  [{req_id}] [LAYER1_EMPTY] RSS aggregator found no articles for {ticker}", extra={
                    "operation": "layer1_rss_empty",
                    "ticker": ticker,
                    "layer": 1,
                    "req_id": req_id
                })
                
        except Exception as e:
            layer1_duration = (time.time() - layer_start)
            logger.error(f"❌ [{req_id}] [LAYER1_FAIL] RSS aggregator failed for {ticker}: {e}", extra={
                "operation": "layer1_rss_failure",
                "layer": 1,
                "ticker": ticker,
                "error": str(e),
                "error_type": type(e).__name__,
                "duration_seconds": layer1_duration,
                "req_id": req_id
            })
        
        
        # === LAYER 2: Direct Scrapers (Targeted - NEW!) ===
        if len(all_articles) < min_articles:
            try:
                from app.scrapers.layer2_direct_scrapers import layer2_scrapers
                
                self.stats['layer2'] = self.stats.get('layer2', {'attempts': 0, 'successes': 0, 'failures': 0, 'articles': 0})
                self.stats['layer2']['attempts'] += 1
                
                layer2_start = datetime.now()
                logger.info(f"🌐 [{req_id}] [LAYER2_START] Need more articles ({len(all_articles)}/{min_articles}), trying direct scrapers for {ticker}", extra={
                    "operation": "layer2_direct_start",
                    "ticker": ticker,
                    "layer": 2,
                    "layer_name": "DirectScrapers",
                    "current_count": len(all_articles),
                    "target": min_articles,
                    "req_id": req_id
                })
                
                layer2_articles = await layer2_scrapers.scrape_all(ticker, company_name)
                
                if layer2_articles:
                    # Tag articles with layer info
                    for article in layer2_articles:
                        article['acquisition_layer'] = 'layer2_direct'
                        article['layer_priority'] = 2
                    
                    all_articles.extend(layer2_articles)
                    self.stats['layer2']['successes'] += 1
                    self.stats['layer2']['articles'] += len(layer2_articles)
                    
                    layer2_duration = (datetime.now() - layer2_start).total_seconds()
                    logger.info(f"✅ [{req_id}] [LAYER2_SUCCESS] Direct scrapers returned {len(layer2_articles)} articles in {layer2_duration:.2f}s", extra={
                        "operation": "layer2_direct_success",
                        "layer": 2,
                        "ticker": ticker,
                        "articles_count": len(layer2_articles),
                        "duration_seconds": layer2_duration,
                        "sources": list(set([a.get('source', 'unknown') for a in layer2_articles])),
                        "req_id": req_id
                    })
                    
                    # Early exit if enough articles
                    if len(all_articles) >= min_articles:
                        logger.info(f"[{req_id}] [LAYER2_COMPLETE] Direct scrapers provided enough articles. Skipping Layer 3.", extra={
                            "operation": "layer2_complete_early_exit",
                            "ticker": ticker,
                            "articles_count": len(all_articles),
                            "req_id": req_id
                        })
                        # Deduplicate and return
                        unique_articles = self._deduplicate_across_layers(all_articles)
                        ranked_articles = self._rank_by_quality(unique_articles)
                        final_articles = ranked_articles[:max_articles]
                        duration = (datetime.now() - start_time).total_seconds()
                        logger.info(f"✅ Intelligent news service completed for {ticker}: {len(final_articles)} articles in {duration:.2f}s", extra={
                            "operation": "intelligent_news_service",
                            "ticker": ticker,
                            "total_articles": len(final_articles),
                            "duration_seconds": duration,
                            "layers_used": self._get_layers_used(final_articles),
                            "req_id": req_id
                        })
                        return final_articles
                else:
                    logger.warning(f"⚠️  [{req_id}] [LAYER2_EMPTY] Direct scrapers found no articles", extra={
                        "operation": "layer2_direct_empty",
                        "ticker": ticker,
                        "layer": 2,
                        "req_id": req_id
                    })
            except Exception as e:
                self.stats['layer2']['failures'] += 1
                logger.error(f"❌ [{req_id}] [LAYER2_FAIL] Direct scrapers failed for {ticker}: {e}", extra={
                    "operation": "layer2_direct_failure",
                    "layer": 2,
                    "ticker": ticker,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "req_id": req_id
                })
        
        
        #=== LAYER 3: DuckDuckGo Web Scraper (Last Resort) ===
        if len(articles) < min_articles:
            try:
                self.stats['fallback']['attempts'] += 1
                
                logger.info(f"🔍 [LAYER3_START] Need more articles ({len(articles)}/{min_articles}), trying DuckDuckGo for {ticker}", extra={
                    "operation": "layer3_duckduckgo_start",
                    "ticker": ticker,
                    "layer": 3,
                    "layer_name": "DuckDuckGo"
                })
                
                # Build search query
                query = f"{company_name} {ticker} stock news"
                
                # Use existing web scraper (synchronous)
                # Run in executor to avoid blocking
                loop = asyncio.get_event_loop()
                fallback_articles = await loop.run_in_executor(
                    None,
                    self.web_scraper.search_and_scrape,
                    query,
                    max_articles - len(articles)
                )
                
                if fallback_articles:
                    # Tag articles with layer info
                    for article in fallback_articles:
                        article['acquisition_layer'] = 'fallback_web'
                        article['layer_priority'] = 3
                    
                    articles.extend(fallback_articles)
                    self.stats['fallback']['successes'] += 1
                    self.stats['fallback']['articles'] += len(fallback_articles)
                    
                    logger.info(f"✅ [LAYER3_SUCCESS] DuckDuckGo returned {len(fallback_articles)} articles", extra={
                        "operation": "layer3_duckduckgo_success",
                        "layer": 3,
                        "ticker": ticker,
                        "articles_count": len(fallback_articles)
                    })
                else:
                    logger.warning(f"⚠️  [LAYER3_EMPTY] DuckDuckGo found no articles for {ticker}")
                    
            except Exception as e:
                logger.error(f"❌ [LAYER3_FAIL] DuckDuckGo scraper failed for {ticker}: {e}", extra={
                    "operation": "layer3_duckduckgo_failure",
                    "layer": 3,
                    "ticker": ticker,
                    "error": str(e),
                    "error_type": type(e).__name__
                })
        
        # === CROSS-LAYER DEDUPLICATION ===
        unique_articles = self._deduplicate_across_layers(articles)
        
        # === RANK BY QUALITY ===
        ranked_articles = self._rank_by_quality(unique_articles)
        
        # === RETURN TOP N ===
        final_articles = ranked_articles[:max_articles]
        
        duration = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Intelligent news service completed for {ticker}: {len(final_articles)} articles in {duration:.2f}s", extra={
            "operation": "intelligent_news_service",
            "ticker": ticker,
            "total_articles": len(final_articles),
            "duration_seconds": duration,
            "layers_used": self._get_layers_used(final_articles),
            "success_rate": f"{len(final_articles)}/{max_articles}"
        })
        
        return final_articles
    
    def _deduplicate_across_layers(self, articles: List[Dict]) -> List[Dict]:
        """
        Deduplicate articles across all layers.
        
        Prefers articles from higher-priority layers (RSS > Direct > Fallback).
        Uses title similarity for deduplication.
        
        Args:
            articles: All articles from all layers
            
        Returns:
            Deduplicated list
        """
        # Sort by layer priority (lower = better)
        articles.sort(key=lambda x: x.get('layer_priority', 99))
        
        seen_titles = {}
        unique = []
        
        for article in articles:
            # Normalize title for comparison
            import re
            title_norm = re.sub(r'[^a-z0-9\s]', '', article.get('title', '').lower())
            title_key = title_norm[:50].strip()
            
            if not title_key:
                continue
            
            # Keep first occurrence (which is from highest-priority layer due to sorting)
            if title_key not in seen_titles:
                seen_titles[title_key] = True
                unique.append(article)
        
        logger.debug(f"Deduplication: {len(articles)} → {len(unique)} unique articles")
        
        return unique
    
    def _rank_by_quality(self, articles: List[Dict]) -> List[Dict]:
        """
        Rank articles by quality score.
        
        Quality factors:
        - Layer priority (RSS > Direct > Fallback)
        - Content length (longer = more complete)
        - Recency (newer = better)
        - Source reliability
        
        Args:
            articles: List of articles
            
        Returns:
            Sorted list by quality (best first)
        """
        def calculate_quality_score(article: Dict) -> float:
            """Calculate composite quality score."""
            # Layer score (lower priority number = higher score)
            layer_priority = article.get('layer_priority', 3)
            layer_score = (4 - layer_priority) / 3  # 1.0 for RSS, 0.33 for fallback
            
            # Content length score
            content_length = len(article.get('content', ''))
            length_score = min(1.0, content_length / 1000)  # Max out at 1000 chars
            
            # Recency score (if available)
            recency_score = 0.5  # Default
            if 'published_timestamp' in article:
                import time
                hours_old = (time.time() - article['published_timestamp']) / 3600
                recency_score = max(0, 1.0 - (hours_old / 168))  # Decay over 1 week
            
            # Reliability score
            reliability_score = article.get('reliability', 0.5)
            
            # Weighted combination
            total_score = (
                layer_score * 0.4 +
                length_score * 0.3 +
                recency_score * 0.2 +
                reliability_score * 0.1
            )
            
            return total_score
        
        # Add quality score to each article
        for article in articles:
            article['quality_score'] = calculate_quality_score(article)
        
        # Sort by quality score (highest first)
        articles.sort(key=lambda x: x['quality_score'], reverse=True)
        
        return articles
    
    def _get_layers_used(self, articles: List[Dict]) -> Dict[str, int]:
        """Get count of articles per layer."""
        layers = {}
        for article in articles:
            layer = article.get('acquisition_layer', 'unknown')
            layers[layer] = layers.get(layer, 0) + 1
        return layers
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about news acquisition."""
        return self.stats.copy()


# Singleton instance
intelligent_news_service = IntelligentNewsService()
