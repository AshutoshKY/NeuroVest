"""
RSS News Aggregator for Indian Stock Market News.

Aggregates news from multiple proven RSS feeds identified in POC:
- Moneycontrol Top Stories (95% reliable)
- Economic Times Markets (95% reliable)
- Livemint Markets (90% reliable)

Proven 75% success rate in POC testing.
"""

import feedparser
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urlparse
import hashlib

logger = logging.getLogger(__name__)


class RSSNewsAggregator:
    """
    Production-ready RSS news aggregator for Indian financial news.
    
    Features:
    - Parallel feed fetching
    - Stock mention filtering
    - Smart deduplication
    - Date-based sorting
    - Reliability tracking
    """
    
    # Proven RSS feeds from POC
    FEEDS = [
        {
            'name': 'Moneycontrol',
            'url': 'https://www.moneycontrol.com/rss/latestnews.xml',
            'priority': 1,
            'reliability': 0.95
        },
        {
            'name': 'Economic Times',
            'url': 'https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms',
            'priority': 1,
            'reliability': 0.95
        },
        {
            'name': 'Livemint',
            'url': 'https://www.livemint.com/rss/markets',
            'priority': 2,
            'reliability': 0.90
        }
    ]
    
    def __init__(self):
        """Initialize RSS aggregator."""
        self.stats = {
            'feeds_attempted': 0,
            'feeds_succeeded': 0,
            'total_entries': 0,
            'filtered_entries': 0
        }
    
    async def get_news_for_stock(
        self,
        ticker: str,
        company_name: str,
        max_articles: int = 15  # Increased from 5 for comprehensive news coverage
    ) -> List[Dict[str, Any]]:
        """
        Get news articles for a specific stock from RSS feeds.
        
        Args:
            ticker: Stock ticker symbol (e.g., "RELIANCE")
            company_name: Full company name (e.g., "Reliance Industries")
            max_articles: Maximum number of articles to return
            
        Returns:
            List of article dictionaries with title, content, url, timestamp, source
        """
        start_time = datetime.now()
        
        logger.info(f"📡 [RSS_START] Fetching RSS news for {ticker}", extra={
            "operation": "rss_aggregator_start",
            "ticker": ticker,
            "company_name": company_name,
            "max_articles": max_articles,
            "feeds_count": len(self.FEEDS),
            "timestamp": start_time.isoformat()
        })
        
        # Fetch all feeds in parallel
        logger.debug(f"[RSS_FETCH] Starting parallel fetch of {len(self.FEEDS)} feeds")
        tasks = [self._fetch_feed(feed) for feed in self.FEEDS]
        all_entries = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine all successful entries
        combined_entries = []
        failed_feeds = []
        for idx, entries in enumerate(all_entries):
            feed_name = self.FEEDS[idx]['name']
            if isinstance(entries, Exception):
                logger.warning(f"⚠️  [RSS_FEED_FAIL] {feed_name} failed: {entries}", extra={
                    "operation": "rss_feed_failure",
                    "feed_name": feed_name,
                    "error": str(entries),
                    "ticker": ticker
                })
                failed_feeds.append(feed_name)
                continue
            logger.info(f"✅ [RSS_FEED_SUCCESS] {feed_name}: {len(entries)} entries", extra={
                "operation": "rss_feed_success",
                "feed_name": feed_name,
                "entries_count": len(entries),
                "ticker": ticker
            })
            combined_entries.extend(entries)
        
        self.stats['total_entries'] = len(combined_entries)
        
        if failed_feeds:
            logger.warning(f"[RSS_FEEDS_FAILED] {len(failed_feeds)}/{len(self.FEEDS)} feeds failed: {', '.join(failed_feeds)}")
        
        if not combined_entries:
            logger.error(f"❌ [RSS_NO_ENTRIES] No entries from ANY feed for {ticker}", extra={
                "operation": "rss_no_entries",
                "ticker": ticker,
                "failed_feeds": failed_feeds
            })
        
        # Filter for stock mentions
        logger.debug(f"[RSS_FILTER] Filtering {len(combined_entries)} entries for {ticker}/{company_name}")
        relevant = self._filter_for_stock(combined_entries, ticker, company_name)
        self.stats['filtered_entries'] = len(relevant)
        
        logger.info(f"📊 [RSS_FILTER_RESULT] {len(combined_entries)} → {len(relevant)} relevant ({len(relevant)/len(combined_entries)*100 if combined_entries else 0:.1f}%)", extra={
            "operation": "rss_aggregator",
            "ticker": ticker,
            "total_entries": len(combined_entries),
            "relevant_entries": len(relevant)
        })
        
        # Deduplicate by title similarity
        unique = self._deduplicate(relevant)
        
        # Sort by date (newest first)
        unique.sort(key=lambda x: x.get('published_timestamp', 0), reverse=True)
        
        # Take top N
        final = unique[:max_articles]
        
        duration = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ RSS aggregator completed: {len(final)} articles in {duration:.2f}s", extra={
            "operation": "rss_aggregator",
            "ticker": ticker,
            "articles_returned": len(final),
            "duration_seconds": duration,
            "success_rate": f"{len(final)}/{max_articles}"
        })
        
        return final
    
    async def _fetch_feed(self, feed_config: Dict) -> List[Dict]:
        """
        Fetch and parse a single RSS feed.
        
        Args:
            feed_config: Feed configuration dict
            
        Returns:
            List of parsed entries
        """
        self.stats['feeds_attempted'] += 1
        fetch_start = datetime.now()
        
        try:
            logger.debug(f"[FEED_FETCH_START] {feed_config['name']}", extra={
                "operation": "feed_fetch_start",
                "feed_name": feed_config['name'],
                "feed_url": feed_config['url'],
                "priority": feed_config['priority']
            })
            
            # Parse feed (feedparser handles the HTTP request)
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(
                None,
                feedparser.parse,
                feed_config['url']
            )
            
            fetch_duration = (datetime.now() - fetch_start).total_seconds()
            
            # Check for errors
            if feed.bozo and feed.bozo_exception:
                logger.warning(f"⚠️  [FEED_PARSE_ISSUE] {feed_config['name']}: {feed.bozo_exception}", extra={
                    "operation": "feed_parse_warning",
                    "feed_name": feed_config['name'],
                    "exception": str(feed.bozo_exception)
                })
            
            entries = feed.entries[:20]  # Limit to recent 20 entries
            
            if not entries:
                logger.warning(f"⚠️  [FEED_EMPTY] {feed_config['name']} returned no entries", extra={
                    "operation": "feed_empty",
                    "feed_name": feed_config['name'],
                    "feed_url": feed_config['url']
                })
                return []
            
            # Convert to our format
            parsed_entries = []
            for entry in entries:
                parsed = self._parse_entry(entry, feed_config)
                if parsed:
                    parsed_entries.append(parsed)
            
            self.stats['feeds_succeeded'] += 1
            
            logger.debug(f"✅ Feed {feed_config['name']}: {len(parsed_entries)} entries")
            
            return parsed_entries
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch feed {feed_config['name']}: {e}")
            return []
    
    def _parse_entry(self, entry: Any, feed_config: Dict) -> Optional[Dict]:
        """
        Parse a single RSS entry into our article format.
        
        Args:
            entry: feedparser entry object
            feed_config: Feed configuration
            
        Returns:
            Parsed article dict or None
        """
        try:
            title = entry.get('title', '').strip()
            if not title:
                return None
            
            # Extract content (try summary, then description, then title)
            content = (
                entry.get('summary', '') or
                entry.get('description', '') or
                title
            ).strip()
            
            # Clean HTML tags from content
            import re
            content = re.sub(r'<[^>]+>', '', content)
            content = re.sub(r'\s+', ' ', content).strip()
            
            # Parse date
            published_timestamp = 0
            published_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                from time import mktime
                published_timestamp = int(mktime(entry.published_parsed))
                published_date = datetime.fromtimestamp(published_timestamp).isoformat()
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                from time import mktime
                published_timestamp = int(mktime(entry.updated_parsed))
                published_date = datetime.fromtimestamp(published_timestamp).isoformat()
            else:
                # Use current time if no date available
                published_timestamp = int(datetime.now().timestamp())
                published_date = datetime.now().isoformat()
            
            url = entry.get('link', '')
            
            return {
                'title': title,
                'content': content,
                'url': url,
                'published_date': published_date,
                'published_timestamp': published_timestamp,
                'source': f"RSS - {feed_config['name']}",
                'source_feed': feed_config['name'],
                'priority': feed_config['priority'],
                'reliability': feed_config['reliability']
            }
            
        except Exception as e:
            logger.warning(f"Failed to parse entry: {e}")
            return None
    
    def _filter_for_stock(
        self,
        entries: List[Dict],
        ticker: str,
        company_name: str
    ) -> List[Dict]:
        """
        Filter entries for stock mentions.
        
        Looks for ticker or company name in title OR content.
        Uses case-insensitive matching.
        
        Args:
            entries: List of parsed entries
            ticker: Stock ticker
            company_name: Company name
            
        Returns:
            Filtered list
        """
        # CRITICAL FIX: Strip exchange suffixes (.NS, .BO, .BSE) from ticker
        # Articles say "Reliance" not "Reliance.NS"
        clean_ticker = ticker.replace('.NS', '').replace('.BO', '').replace('.BSE', '')
        
        ticker_lower = clean_ticker.lower()
        company_lower = company_name.lower() if company_name else ""
        
        logger.info(f"[RSS_FILTER_START] Filtering {len(entries)} entries for ticker='{clean_ticker}', company='{company_name}'")
        
        # Log first 3 article titles for debugging
        if entries:
            sample_titles = [entries[i]['title'][:80] for i in range(min(3, len(entries)))]
            logger.info(f"[RSS_SAMPLE_TITLES] Sample articles: {sample_titles}")
        
        # Also check for company name variations
        # e.g., "Reliance Industries" → ["reliance", "reliance industries"]
        company_parts = [company_lower] + [part for part in company_lower.split() if len(part) > 3] if company_name else []
        
        logger.debug(f"[RSS_FILTER] Search terms: ticker='{ticker_lower}', company_parts={company_parts}")
        
        relevant = []
        for idx, entry in enumerate(entries):
            title_lower = entry['title'].lower()
            content_lower = entry['content'].lower()
            
            # Check if ticker or company name appears
            ticker_in_title = ticker_lower in title_lower
            ticker_in_content = ticker_lower in content_lower
            company_match = any(part in title_lower or part in content_lower for part in company_parts) if company_parts else False
            
            matches = ticker_in_title or ticker_in_content or company_match
            
            if matches:
                logger.debug(f"[RSS_MATCH] Article {idx}: '{entry['title'][:50]}...' - ticker_title:{ticker_in_title}, ticker_content:{ticker_in_content}, company:{company_match}")
                relevant.append(entry)
        
        logger.info(f"[RSS_FILTER_END] Found {len(relevant)}/{len(entries)} relevant articles")
        return relevant
    
    def _deduplicate(self, articles: List[Dict]) -> List[Dict]:
        """
        Deduplicate articles by title similarity.
        
        Uses first 50 characters of normalized title as key.
        Keeps article with higher reliability score.
        
        Args:
            articles: List of articles
            
        Returns:
            Deduplicated list
        """
        seen = {}
        
        for article in articles:
            # Normalize title: lowercase, remove special chars, take first 50 chars
            import re
            normalized = re.sub(r'[^a-z0-9\s]', '', article['title'].lower())
            key = normalized[:50].strip()
            
            if not key:
                continue
            
            # Keep article with higher reliability or earlier if same
            if key not in seen or article['reliability'] > seen[key]['reliability']:
                seen[key] = article
        
        return list(seen.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about RSS fetching."""
        return self.stats.copy()


# Singleton instance
rss_aggregator = RSSNewsAggregator()
