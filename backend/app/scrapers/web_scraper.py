import logging
import requests
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from datetime import datetime

logger = logging.getLogger(__name__)

class WebScraper:
    """
    Scraper V2: Searches the web for stock news and scrapes content.
    Uses DuckDuckGo Search (DDGS) to find relevant articles.
    """
    
    def __init__(self):
        self.ddgs = DDGS()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def search_and_scrape(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for news and scrape the content.
        
        Args:
            query: Search query (e.g., "Tata Steel stock news")
            max_results: Maximum number of articles to process
            
        Returns:
            List of scraped articles
        """
        logger.info("🔍 Initiating web search", extra={
            "operation": "web_search",
            "query": query,
            "max_results": max_results,
            "search_engine": "DuckDuckGo"
        })
        articles = []
        
        try:
            # Search for news using text search with backend='html' to avoid rate limits
            # We append "stock news" to the query to ensure relevance
            results = self.ddgs.text(f"{query}", region="in-en", backend="html", max_results=max_results)
            
            if not results:
                logger.warning("⚠️  Web search returned no results", extra={
                    "operation": "web_search",
                    "query": query,
                    "status": "no_results"
                })
                return []
                
            logger.info("✅ Web search completed", extra={
                "operation": "web_search",
                "query": query,
                "results_count": len(results),
                "status": "success"
            })
            
            from urllib.parse import urlparse
            domain_counts = {}
            
            for result in results:
                url = result.get('href')
                title = result.get('title')
                snippet = result.get('body')
                
                if not url:
                    continue
                
                # Domain diversity check
                try:
                    domain = urlparse(url).netloc
                    # Normalize domain (remove www.)
                    if domain.startswith('www.'):
                        domain = domain[4:]
                        
                    # Limit to 2 articles per domain to ensure diversity
                    if domain_counts.get(domain, 0) >= 2:
                        logger.info(f"Skipping {url} (max articles for {domain} reached)")
                        continue
                        
                    domain_counts[domain] = domain_counts.get(domain, 0) + 1
                except:
                    pass
                    
                # Scrape full content
                logger.debug(f"🌐 Attempting to scrape URL", extra={
                    "operation": "scrape_url",
                    "url": url,
                    "domain": domain,
                    "title": title
                })
                
                content = self._scrape_url(url)
                
                # Fallback to snippet if scraping fails or returns little content
                if not content and snippet:
                    logger.warning("⚠️  URL scraping failed, using snippet", extra={
                        "operation": "scrape_url",
                        "url": url,
                        "status": "fallback_to_snippet"
                    })
                    content = snippet
                elif content:
                    logger.debug("✅ URL scraped successfully", extra={
                        "operation": "scrape_url",
                        "url": url,
                        "content_length": len(content),
                        "status": "success"
                    })
                
                if content:
                    articles.append({
                        'title': title,
                        'content': content,
                        'url': url,
                        'timestamp': datetime.now().isoformat(), # Text search doesn't return date, use current time
                        'source': f"Web - {domain}", # Use domain as source name
                        'raw_html': content
                    })
            
            logger.info("✅ Web scraping completed", extra={
                "operation": "web_scrape",
                "query": query,
                "articles_scraped": len(articles),
                "unique_domains": len(domain_counts),
                "status": "success"
            })
            
            # --- Dynamic Expansion Logic ---
            # If we have too few articles, try expanding the search with different keywords
            if len(articles) < 3:
                logger.info(f"⚠️ Low article count ({len(articles)}). Triggering dynamic search expansion...")
                expansion_queries = [f"{query} analysis", f"{query} financial results"]
                
                for exp_query in expansion_queries:
                    if len(articles) >= 5:
                        break
                        
                    logger.info(f"🔍 Expanding search with: '{exp_query}'")
                    try:
                        more_results = self.ddgs.text(exp_query, region="in-en", backend="html", max_results=5)
                        
                        for result in more_results:
                            url = result.get('href')
                            if not url or any(a['url'] == url for a in articles): # Avoid duplicates
                                continue
                                
                            # Basic domain check for expansion
                            try:
                                domain = urlparse(url).netloc
                                if domain.startswith('www.'): domain = domain[4:]
                                if domain_counts.get(domain, 0) >= 2: continue
                                domain_counts[domain] = domain_counts.get(domain, 0) + 1
                            except: pass
                            
                            content = self._scrape_url(url)
                            if not content and result.get('body'):
                                content = result.get('body')
                                
                            if content:
                                articles.append({
                                    'title': result.get('title'),
                                    'content': content,
                                    'url': url,
                                    'timestamp': datetime.now().isoformat(),
                                    'source': f"Web (Expanded) - {domain}",
                                    'raw_html': content
                                })
                    except Exception as e:
                        logger.warning(f"Expansion search failed for '{exp_query}': {e}")

            return articles
            
        except Exception as e:
            logger.error(f"❌ Scraper V2 Search Failed: {e}")
            return []

    def _scrape_url(self, url: str) -> str:
        """
        Fetch and extract text content from a URL.
        """
        try:
            # Enhanced headers to mimic real browser
            headers = self.headers.copy()
            headers.update({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            logger.debug("📥 HTTP request successful", extra={
                "operation": "scrape_url_http",
                "url": url,
                "status_code": response.status_code,
                "response_size": len(response.text)
            })
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'ads', 'noscript', 'form', 'button']):
                tag.decompose()
            
            # Extract text from paragraphs and divs with substantial text
            text_blocks = []
            
            # Strategy 1: Paragraphs
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 50:
                    text_blocks.append(text)
            
            # Strategy 2: If paragraphs are scarce, look for divs
            if len(text_blocks) < 3:
                divs = soup.find_all('div')
                for div in divs:
                    text = div.get_text(strip=True)
                    # Heuristic: long text with spaces likely contains sentences
                    if len(text) > 100 and text.count(' ') > 10: 
                        # Avoid duplicating if it contains already found paragraphs
                        if not any(t in text for t in text_blocks):
                            text_blocks.append(text)

            text_content = ' '.join(text_blocks)
            
            if len(text_content) < 100: # Lowered threshold
                logger.debug("⚠️  Extracted content too short", extra={
                    "operation": "scrape_url_extract",
                    "url": url,
                    "content_length": len(text_content),
                    "status": "insufficient_content"
                })
                return None
            
            logger.debug("✅ Content extracted successfully", extra={
                "operation": "scrape_url_extract",
                "url": url,
                "paragraphs_found": len(text_blocks),
                "content_length": len(text_content),
                "status": "success"
            })
                
            return text_content
            
        except Exception as e:
            logger.warning("❌ URL scraping failed", extra={
                "operation": "scrape_url",
                "url": url,
                "status": "failure",
                "error": str(e)
            })
            return None

# Global instance
web_scraper = WebScraper()
