from typing import List, Dict, Any
import logging
from datetime import datetime
from app.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class MoneyControlScraper(BaseScraper):
    """Scraper for MoneyControl financial news."""
    
    def __init__(self):
        super().__init__(delay_seconds=2)
        self.base_url = "https://www.moneycontrol.com"
        self.defense_url = f"{self.base_url}/news/business/stocks"
    
    def scrape_latest_articles(self, max_articles: int = 10) -> List[Dict[str, Any]]:
        """Scrape latest stock market articles from MoneyControl."""
        articles = []
        
        try:
            html = self.get_page_content(self.defense_url)
            if not html:
                return articles
            
            soup = self.parse_html(html)
            
            # Find article links
            article_links = soup.select('li.clearfix h2 a')[:max_articles]
            
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
                    content_div = article_soup.select_one('div.content_wrapper')
                    content = content_div.get_text(strip=True) if content_div else ""
                    
                    # Extract timestamp
                    time_elem = article_soup.select_one('div.article_schedule')
                    timestamp = time_elem.get_text(strip=True) if time_elem else datetime.now().isoformat()
                    
                    articles.append({
                        'title': title,
                        'content': content,
                        'url': article_url,
                        'source': 'MoneyControl',
                        'timestamp': timestamp,
                        'raw_html': article_html
                    })
                    
                    logger.info(f"Scraped article: {title}")
                    
                except Exception as e:
                    logger.error(f"Error scraping individual article: {e}")
                    continue
            
            logger.info(f"Scraped {len(articles)} articles from MoneyControl")
            return articles
            
        except Exception as e:
            logger.error(f"Error scraping MoneyControl: {e}")
            return articles


# Global instance
moneycontrol_scraper = MoneyControlScraper()
