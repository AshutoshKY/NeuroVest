"""
Generic web scraper that works with any website using CSS selectors from configuration.
"""
from typing import List, Dict, Any
import logging
from datetime import datetime
from app.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class GenericScraper(BaseScraper):
    """Configuration-driven scraper that works with any website."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize generic scraper with configuration.
        
        Args:
            config: Dictionary with scraper configuration including:
                - name: Source name
                - url: Base URL to scrape
                - selectors: CSS selectors for article elements
                - max_articles: Maximum articles to scrape
                - delay_seconds: Delay between requests
        """
        super().__init__(delay_seconds=config.get('delay_seconds', 2))
        self.config = config
        self.name = config['name']
        self.base_url = config['url']
        self.selectors = config['selectors']
        self.max_articles = config.get('max_articles', 10)
        
        logger.info(f"Initialized {self.name} scraper")
    
    def scrape_latest_articles(self, max_articles: int = None) -> List[Dict[str, Any]]:
        """
        Scrape latest articles using configured selectors.
        
        Args:
            max_articles: Override max articles from config
            
        Returns:
            List of article dictionaries
        """
        max_articles = max_articles or self.max_articles
        articles = []
        
        try:
            logger.info(f"🔍 Starting scrape: {self.name} from {self.base_url}")
            
            # Get main page
            html = self.get_page_content(self.base_url)
            if not html:
                logger.error(f"❌ Failed to fetch page: {self.base_url}")
                return articles
            
            soup = self.parse_html(html)
            
            # Find article links using configured selector
            article_links = soup.select(self.selectors['article_links'])[:max_articles]
            logger.info(f"Found {len(article_links)} article links")
            
            if not article_links:
                logger.warning(f"⚠️ No articles found with selector: {self.selectors['article_links']}")
                return articles
            
            # Scrape each article
            for idx, link in enumerate(article_links, 1):
                try:
                    article_url = link.get('href', '')
                    
                    # Make URL absolute if relative
                    if article_url and not article_url.startswith('http'):
                        # Handle different URL formats
                        if article_url.startswith('//'):
                            article_url = 'https:' + article_url
                        elif article_url.startswith('/'):
                            article_url = self.base_url.rstrip('/') + article_url
                        else:
                            article_url = self.base_url.rstrip('/') + '/' + article_url
                    
                    if not article_url:
                        logger.warning(f"Skipping article {idx}: No URL found")
                        continue
                    
                    # Get article title from link
                    title = link.get_text(strip=True)
                    
                    logger.info(f"📄 Fetching article {idx}/{len(article_links)}: {title[:50]}...")
                    
                    # Fetch full article
                    article_html = self.get_page_content(article_url)
                    if not article_html:
                        logger.warning(f"Failed to fetch article: {article_url}")
                        continue
                    
                    article_soup = self.parse_html(article_html)
                    
                    # Extract title (prefer page title over link text)
                    title_elem = article_soup.select_one(self.selectors.get('article_title', 'h1'))
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                    
                    # Extract content
                    content_elem = article_soup.select_one(self.selectors['article_content'])
                    content = content_elem.get_text(strip=True) if content_elem else ""
                    
                    # Extract timestamp if selector provided
                    timestamp = datetime.now().isoformat()
                    if 'timestamp' in self.selectors:
                        time_elem = article_soup.select_one(self.selectors['timestamp'])
                        if time_elem:
                            timestamp = time_elem.get_text(strip=True)
                    
                    if content:  # Only add if we got content
                        articles.append({
                            'title': title,
                            'content': content,
                            'url': article_url,
                            'source': self.name,
                            'timestamp': timestamp,
                            'raw_html': article_html
                        })
                        
                        logger.info(f"✅ Successfully scraped: {title[:50]}...")
                    else:
                        logger.warning(f"⚠️ No content found for: {title[:50]}...")
                    
                except Exception as e:
                    logger.error(f"❌ Error scraping article {idx}: {e}")
                    continue
            
            logger.info(f"✅ {self.name} scraping complete: {len(articles)}/{len(article_links)} articles")
            return articles
            
        except Exception as e:
            logger.error(f"❌ Error scraping {self.name}: {e}", exc_info=True)
            return articles
    
    def test_selectors(self) -> Dict[str, Any]:
        """
        Test if configured selectors work on the website.
        Useful for debugging configuration.
        
        Returns:
            Dictionary with test results
        """
        try:
            html = self.get_page_content(self.base_url)
            if not html:
                return {'success': False, 'error': 'Failed to fetch page'}
            
            soup = self.parse_html(html)
            
            results = {
                'success': True,
                'url': self.base_url,
                'selectors_tested': {}
            }
            
            for selector_name, selector_value in self.selectors.items():
                elements = soup.select(selector_value)
                results['selectors_tested'][selector_name] = {
                    'selector': selector_value,
                    'elements_found': len(elements),
                    'sample': elements[0].get_text(strip=True)[:100] if elements else None
                }
            
            return results
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
