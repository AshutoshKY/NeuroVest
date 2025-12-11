import requests
from bs4 import BeautifulSoup
import time
import logging
from typing import List, Dict, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for web scrapers."""
    
    def __init__(self, delay_seconds: int = 2):
        """
        Initialize scraper.
        
        Args:
            delay_seconds: Delay between requests for rate limiting
        """
        self.delay_seconds = delay_seconds
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    @abstractmethod
    def scrape_latest_articles(self, max_articles: int = 10) -> List[Dict[str, Any]]:
        """
        Scrape latest articles.
        
        Args:
            max_articles: Maximum number of articles to scrape
            
        Returns:
            List of article dictionaries with title, content, url, timestamp
        """
        pass
    
    def get_page_content(self, url: str) -> str:
        """
        Fetch page content with error handling.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or empty string on error
        """
        try:
            time.sleep(self.delay_seconds)
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return ""
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content."""
        return BeautifulSoup(html, 'lxml')
    
    def extract_text(self, soup: BeautifulSoup, selector: str) -> str:
        """
        Extract text from soup using CSS selector.
        
        Args:
            soup: BeautifulSoup object
            selector: CSS selector
            
        Returns:
            Extracted text or empty string
        """
        try:
            element = soup.select_one(selector)
            return element.get_text(strip=True) if element else ""
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ""
