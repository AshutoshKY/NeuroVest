"""
Layer 2 Direct Scrapers - Direct scraping of major financial websites.

Provides targeted scraping of MoneyControl, Economic Times, and Livemint
for stock-specific news when RSS feeds don't have enough results.

Uses BeautifulSoup + lxml for robust HTML parsing.
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from datetime import datetime
from loguru import logger


class Layer2DirectScrapers:
    """Direct scrapers for major Indian financial news websites."""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.timeout = aiohttp.ClientTimeout(total=15)
    
    async def scrape_moneycontrol(self, ticker: str, company_name: str) -> List[Dict[str, Any]]:
        """
        Scrape MoneyControl news for a stock.
        
        URL pattern: https://www.moneycontrol.com/news/tags/{company-slug}.html
        """
        try:
            # Convert company name to slug (e.g., "Reliance Industries" -> "reliance-industries")
            company_slug = company_name.lower().replace(' ', '-').replace('.', '')
            url = f"https://www.moneycontrol.com/news/tags/{company_slug}.html"
            
            logger.info(f"[LAYER2_MC] Scraping MoneyControl: {url}")
            
            async with aiohttp.ClientSession(headers=self.headers, timeout=self.timeout) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.warning(f"[LAYER2_MC] Failed: HTTP {response.status}")
                        return []
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')
                    
                    articles = []
                    
                    # Find news items (MoneyControl structure)
                    news_items = soup.find_all('li', class_='clearfix')[:10]  # Top 10
                    
                    for item in news_items:
                        try:
                            title_tag = item.find('h2') or item.find('a')
                            link_tag = item.find('a')
                            
                            if not title_tag or not link_tag:
                                continue
                            
                            title = title_tag.get_text().strip()
                            link = link_tag.get('href', '')
                            
                            if not link.startswith('http'):
                                link = f"https://www.moneycontrol.com{link}"
                            
                            # Extract snippet if available
                            snippet_tag = item.find('p')
                            snippet = snippet_tag.get_text().strip() if snippet_tag else title
                            
                            articles.append({
                                'title': title,
                                'url': link,
                                'snippet': snippet,
                                'source': 'MoneyControl',
                                'published_date': datetime.now().isoformat()
                            })
                        except Exception as e:
                            logger.debug(f"[LAYER2_MC] Error parsing item: {e}")
                            continue
                    
                    logger.info(f"[LAYER2_MC] ✅ Scraped {len(articles)} articles from MoneyControl")
                    return articles
                    
        except asyncio.TimeoutError:
            logger.warning(f"[LAYER2_MC] ⏱️ Timeout scraping MoneyControl")
            return []
        except Exception as e:
            logger.error(f"[LAYER2_MC] ❌ Error: {e}")
            return []
    
    async def scrape_economic_times(self, ticker: str, company_name: str) -> List[Dict[str, Any]]:
        """
        Scrape Economic Times news for a stock.
        
        URL pattern: https://economictimes.indiatimes.com/{company-slug}/stocks/companyid-{id}.cms
        Fallback: Search page
        """
        try:
            # Use search instead of direct company page (easier to parse)
            search_query = company_name.replace(' ', '+')
            url = f"https://economictimes.indiatimes.com/topic/{search_query}"
            
            logger.info(f"[LAYER2_ET] Scraping Economic Times: {url}")
            
            async with aiohttp.ClientSession(headers=self.headers, timeout=self.timeout) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.warning(f"[LAYER2_ET] Failed: HTTP {response.status}")
                        return []
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')
                    
                    articles = []
                    
                    # Find news items (ET structure)
                    news_items = soup.find_all('div', class_='eachStory')[:10]  # Top 10
                    
                    for item in news_items:
                        try:
                            title_tag = item.find('h3') or item.find('h2')
                            link_tag = item.find('a')
                            
                            if not title_tag or not link_tag:
                                continue
                            
                            title = title_tag.get_text().strip()
                            link = link_tag.get('href', '')
                            
                            if not link.startswith('http'):
                                link = f"https://economictimes.indiatimes.com{link}"
                            
                            # Extract snippet
                            snippet_tag = item.find('p')
                            snippet = snippet_tag.get_text().strip() if snippet_tag else title
                            
                            articles.append({
                                'title': title,
                                'url': link,
                                'snippet': snippet,
                                'source': 'Economic Times',
                                'published_date': datetime.now().isoformat()
                            })
                        except Exception as e:
                            logger.debug(f"[LAYER2_ET] Error parsing item: {e}")
                            continue
                    
                    logger.info(f"[LAYER2_ET] ✅ Scraped {len(articles)} articles from Economic Times")
                    return articles
                    
        except asyncio.TimeoutError:
            logger.warning(f"[LAYER2_ET] ⏱️ Timeout scraping Economic Times")
            return []
        except Exception as e:
            logger.error(f"[LAYER2_ET] ❌ Error: {e}")
            return []
    
    async def scrape_livemint(self, ticker: str, company_name: str) -> List[Dict[str, Any]]:
        """
        Scrape Livemint news for a stock.
        
        URL pattern: https://www.livemint.com/Search/Link/Keyword/{company-name}
        """
        try:
            # Livemint search
            search_query = company_name.replace(' ', '%20')
            url = f"https://www.livemint.com/Search/Link/Keyword/{search_query}"
            
            logger.info(f"[LAYER2_LM] Scraping Livemint: {url}")
            
            async with aiohttp.ClientSession(headers=self.headers, timeout=self.timeout) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.warning(f"[LAYER2_LM] Failed: HTTP {response.status}")
                        return []
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')
                    
                    articles = []
                    
                    # Find news items (Livemint structure)
                    news_items = soup.find_all('div', class_='listingNew')[:10]  # Top 10
                    
                    for item in news_items:
                        try:
                            title_tag = item.find('h2') or item.find('a')
                            link_tag = item.find('a')
                            
                            if not title_tag or not link_tag:
                                continue
                            
                            title = title_tag.get_text().strip()
                            link = link_tag.get('href', '')
                            
                            if not link.startswith('http'):
                                link = f"https://www.livemint.com{link}"
                            
                            # Extract snippet
                            snippet_tag = item.find('p')
                            snippet = snippet_tag.get_text().strip() if snippet_tag else title
                            
                            articles.append({
                                'title': title,
                                'url': link,
                                'snippet': snippet,
                                'source': 'Livemint',
                                'published_date': datetime.now().isoformat()
                            })
                        except Exception as e:
                            logger.debug(f"[LAYER2_LM] Error parsing item: {e}")
                            continue
                    
                    logger.info(f"[LAYER2_LM] ✅ Scraped {len(articles)} articles from Livemint")
                    return articles
                    
        except asyncio.TimeoutError:
            logger.warning(f"[LAYER2_LM] ⏱️ Timeout scraping Livemint")
            return []
        except Exception as e:
            logger.error(f"[LAYER2_LM] ❌ Error: {e}")
            return []
    
    async def scrape_all(self, ticker: str, company_name: str) -> List[Dict[str, Any]]:
        """
        Scrape all Layer 2 sources in parallel.
        
        Returns:
            Combined list of articles from all sources
        """
        logger.info(f"[LAYER2] Starting parallel scraping for {ticker}")
        
        # Run all scrapers in parallel
        results = await asyncio.gather(
            self.scrape_moneycontrol(ticker, company_name),
            self.scrape_economic_times(ticker, company_name),
            self.scrape_livemint(ticker, company_name),
            return_exceptions=True
        )
        
        # Combine results
        all_articles = []
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
            elif isinstance(result, Exception):
                logger.warning(f"[LAYER2] One scraper failed: {result}")
        
        logger.info(f"[LAYER2] ✅ Total articles from Layer 2: {len(all_articles)}")
        return all_articles


# Global instance
layer2_scrapers = Layer2DirectScrapers()
