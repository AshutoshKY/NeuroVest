"""
RSS feed scraper for Google News and other RSS sources.
"""
from typing import List, Dict, Any
import logging
from datetime import datetime
from app.scrapers.base_scraper import BaseScraper
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class RSSScraper(BaseScraper):
    """Scraper for RSS feeds."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize RSS scraper.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(delay_seconds=config.get('delay_seconds', 2))
        self.config = config
        self.name = config['name']
        self.base_url = config['url']
        self.max_articles = config.get('max_articles', 10)
        
        logger.info(f"Initialized RSS scraper: {self.name}")
    
    def parse_xml(self, xml: str) -> BeautifulSoup:
        """Parse XML content."""
        return BeautifulSoup(xml, 'xml')
    
    def scrape_latest_articles(self, max_articles: int = None) -> List[Dict[str, Any]]:
        """
        Scrape latest articles from RSS feed.
        
        Args:
            max_articles: Override max articles
            
        Returns:
            List of articles
        """
        max_articles = max_articles or self.max_articles
        articles = []
        
        try:
            logger.info(f"🔍 Fetching RSS feed: {self.name}")
            
            xml = self.get_page_content(self.base_url)
            if not xml:
                return articles
            
            soup = self.parse_xml(xml)
            items = soup.find_all('item')
            
            logger.info(f"Found {len(items)} items in RSS feed")
            
            for idx, item in enumerate(items[:max_articles], 1):
                try:
                    title = item.find('title').get_text(strip=True) if item.find('title') else "No Title"
                    link = item.find('link').get_text(strip=True) if item.find('link') else ""
                    pub_date = item.find('pubDate').get_text(strip=True) if item.find('pubDate') else datetime.now().isoformat()
                    description = item.find('description').get_text(strip=True) if item.find('description') else ""
                    
                    # Google News specific: description often contains HTML
                    if description and '<' in description:
                        desc_soup = BeautifulSoup(description, 'html.parser')
                        description = desc_soup.get_text(strip=True)
                    
                    if link:
                        # Fetch full content from the source URL
                        logger.info(f"📄 Fetching full content for: {title}")
                        full_content = self._fetch_full_content(link)
                        
                        # Use full content if available, otherwise fallback to description
                        content = full_content if full_content and len(full_content) > 100 else description
                        
                        articles.append({
                            'title': title,
                            'content': content or title,
                            'url': link,
                            'source': self.name,
                            'timestamp': pub_date,
                            'raw_html': str(item)
                        })
                except Exception as e:
                    logger.error(f"Error parsing RSS item {idx}: {e}")
                    continue
            
            logger.info(f"✅ {self.name} scraped {len(articles)} articles")
            return articles
            
        except Exception as e:
            logger.error(f"❌ Error scraping RSS {self.name}: {e}")
            return articles

    def _fetch_full_content(self, url: str) -> str:
        """
        Fetch and extract full text content from a URL.
        
        Args:
            url: The URL to scrape
            
        Returns:
            Extracted text content or None
        """
        try:
            # Use the base scraper's get_page_content which handles headers and timeouts
            html = self.get_page_content(url)
            if not html:
                return None
                
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove unwanted elements
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'ads']):
                tag.decompose()
            
            # Extract text from paragraphs
            paragraphs = soup.find_all('p')
            text_content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            return text_content
            
        except Exception as e:
            logger.warning(f"Failed to fetch full content from {url}: {e}")
            return None

    def test_selectors(self) -> Dict[str, Any]:
        """Test RSS feed connection."""
        try:
            xml = self.get_page_content(self.base_url)
            if not xml:
                return {'success': False, 'error': 'Failed to fetch XML'}
            
            soup = self.parse_xml(xml)
            items = soup.find_all('item')
            
            return {
                'success': True,
                'items_found': len(items),
                'sample_title': items[0].find('title').get_text() if items else None
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
