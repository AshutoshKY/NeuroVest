from typing import List, Dict, Any
import logging
from datetime import datetime
from app.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class EconomicTimesScraper(BaseScraper):
    """Scraper for Economic Times financial news."""
    
    def __init__(self):
        super().__init__(delay_seconds=2)
        self.base_url = "https://economictimes.indiatimes.com"
        self.markets_url = f"{self.base_url}/markets/stocks/news"
    
    def scrape_latest_articles(self, max_articles: int = 10) -> List[Dict[str, Any]]:
        """Scrape latest market articles from Economic Times."""
        articles = []
        
        try:
            html = self.get_page_content(self.markets_url)
            if not html:
                return articles
            
            soup = self.parse_html(html)
            
            # Find article links
            article_links = soup.select('div.eachStory h3 a')[:max_articles]
            
            for link in article_links:
                try:
                    article_url = link.get('href', '')
                    if not article_url.startswith('http'):
                        article_url = self.base_url + article_url
                    
                    title = link.get_text(strip=True)
                    
                    # Fetch full article
                    article_html = self.get_page_content(article_url)
                    if not article_html:
                        continue
                    
                    article_soup = self.parse_html(article_html)
                    
                    # Extract content
                    content_div = article_soup.select_one('div.artText')
                    content = content_div.get_text(strip=True) if content_div else ""
                    
                    # Extract timestamp
                    time_elem = article_soup.select_one('time')
                    timestamp = time_elem.get('datetime', datetime.now().isoformat()) if time_elem else datetime.now().isoformat()
                    
                    articles.append({
                        'title': title,
                        'content': content,
                        'url': article_url,
                        'source': 'Economic Times',
                        'timestamp': timestamp,
                        'raw_html': article_html
                    })
                    
                    logger.info(f"Scraped article: {title}")
                    
                except Exception as e:
                    logger.error(f"Error scraping individual article: {e}")
                    continue
            
            logger.info(f"Scraped {len(articles)} articles from Economic Times")
            return articles
            
        except Exception as e:
            logger.error(f"Error scraping Economic Times: {e}")
            return articles


# Global instance
economictimes_scraper = EconomicTimesScraper()
