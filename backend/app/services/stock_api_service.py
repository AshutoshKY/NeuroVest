"""
Multi-API stock data service with automatic fallback and async support.
"""
import aiohttp
import asyncio
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from app.scrapers.scraper_factory import load_api_configs

logger = logging.getLogger(__name__)


class StockAPIService:
    """
    Service for fetching stock data from multiple APIs with:
    - Automatic fallback between providers
    - Rate limiting
    - Caching
    - Async requests for better performance
    """
    
    def __init__(self):
        """Initialize with API configurations."""
        self.apis = load_api_configs()
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = 300  # 5 minutes
        
        logger.info(f"Initialized StockAPIService with {len(self.apis)} APIs")
    
    async def get_stock_data(self, ticker: str) -> Dict[str, Any]:
        """
        Get stock data for a ticker, trying APIs in priority order.
        
        NEW: Routes to Smart Orchestrator if feature flag enabled.
        Otherwise uses original implementation (100% backward compatible).
        
        Args:
            ticker: Stock ticker symbol (e.g., 'HAL', 'BEL')
            
        Returns:
            Stock data dictionary
        """
        from app.core.config import settings
        
        # FEATURE FLAG: Route to Smart Orchestrator if enabled
        if settings.USE_SMART_ORCHESTRATOR:
            try:
                logger.info(f"🚀 [SMART] Using Smart Orchestrator for {ticker}")
                from app.services.smart_orchestrator import smart_orchestrator
                return await smart_orchestrator.get_stock_data_enhanced(ticker)
            except Exception as e:
                logger.error(f"❌ [SMART] Smart Orchestrator failed for {ticker}, falling back to legacy: {e}")
                # Fall through to legacy implementation below
        
        # Call legacy implementation
        return await self._get_stock_data_legacy(ticker)
    
    async def _get_stock_data_legacy(self, ticker: str) -> Dict[str, Any]:
        """
        LEGACY IMPLEMENTATION - Direct API fallback chain.
        
        This method BYPASSES the feature flag check to prevent recursion.
        Used by:
        1. get_stock_data() when feature flag is OFF
        2. Smart orchestrator for fallback scenarios
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Stock data dictionary
        """
        logger.debug(f"📦 [LEGACY] Using original API service for {ticker}")
        
        # Check cache first
        cache_key = f"stock_{ticker}"
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if datetime.now() - cached_time < timedelta(seconds=self.cache_ttl):
                logger.info(f"✅ Cache hit for {ticker}")
                return cached_data
        
        # Try each API in priority order
        for api in self.apis:
            try:
                logger.info(f"🔄 Trying {api['name']} for {ticker}")
                
                data = await self._fetch_from_api(api, ticker)
                
                if data:
                    logger.info(f"✅ {api['name']} succeeded for {ticker}")
                    
                    # Cache the result
                    self.cache[cache_key] = (data, datetime.now())
                    
                    return data
                    
            except Exception as e:
                logger.warning(f"❌ {api['name']} failed for {ticker}: {e}")
                continue
        
        # All APIs failed
        logger.error(f"❌ All APIs failed for {ticker}")
        raise Exception(f"Failed to fetch data for {ticker} from all providers")
    
    async def get_stock_data_from_provider(self, ticker: str, provider_name: str) -> Dict[str, Any]:
        """
        Get stock data from a specific provider (for testing purposes).
        
        Args:
            ticker: Stock ticker symbol
            provider_name: Name of the provider to use
            
        Returns:
            Stock data dictionary
        """
        # Find the requested API
        api = next((a for a in self.apis if a['name'].lower() == provider_name.lower()), None)
        
        if not api:
            raise Exception(f"Provider '{provider_name}' not found. Available: {[a['name'] for a in self.apis]}")
        
        logger.info(f"🔄 Testing {api['name']} for {ticker}")
        
        try:
            data = await self._fetch_from_api(api, ticker)
            if data:
                logger.info(f"✅ {api['name']} succeeded for {ticker}")
                return data
            else:
                raise Exception(f"{api['name']} returned no data")
        except Exception as e:
            logger.error(f"❌ {api['name']} failed for {ticker}: {e}")
            raise Exception(f"Failed to fetch data from {api['name']}: {str(e)}")
    
    async def _fetch_from_api(self, api: Dict[str, Any], ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch data from a specific API.
        
        Args:
            api: API configuration dictionary
            ticker: Stock ticker symbol
            
        Returns:
            Stock data or None if failed
        """
        api_name = api['name']
        
        if api_name == "Finnhub":
            return await self._fetch_finnhub(api, ticker)
        elif api_name == "Alpha Vantage":
            return await self._fetch_alpha_vantage(api, ticker)
        elif api_name == "Marketstack":
            return await self._fetch_marketstack(api, ticker)
        elif api_name == "Yahoo Finance":
            return await self._fetch_yahoo(api, ticker)
        else:
            logger.warning(f"Unknown API: {api_name}")
            return None
    
    async def _fetch_finnhub(self, api: Dict, ticker: str) -> Optional[Dict]:
        """Fetch from Finnhub API."""
        api_key = os.getenv(api['api_key_env'])
        if not api_key:
            logger.error(f"API key not found: {api['api_key_env']}")
            return None
        
        base_url = api['base_url']
        quote_endpoint = api['endpoints']['quote']
        
        # Append .NS for Indian stocks if not present (but NOT for indices like ^NSEI)
        if not ticker.endswith(('.NS', '.BO')) and not ticker.startswith('^'):
            search_ticker = f"{ticker}.NS"
        else:
            search_ticker = ticker
            
        url = f"{base_url}{quote_endpoint}"
        params = {
            'symbol': search_ticker,
            'token': api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=api['timeout_seconds']) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check if data is valid (c=0 usually means invalid ticker)
                    if data.get('c', 0) == 0:
                        logger.warning(f"Finnhub returned 0 price for {search_ticker}")
                        return None
                    
                    return {
                        'ticker': ticker,
                        'exchange': 'NSE',
                        'current_price': data.get('c', 0),
                        'previous_close': data.get('pc', 0),
                        'day_high': data.get('h', 0),
                        'day_low': data.get('l', 0),
                        'volume': data.get('v', 0),
                        'currency': 'INR',
                        'timestamp': datetime.now().isoformat(),
                        'provider': 'Finnhub'
                    }
                else:
                    logger.error(f"Finnhub error: {response.status}")
                    return None
    
    async def _fetch_alpha_vantage(self, api: Dict, ticker: str) -> Optional[Dict]:
        """Fetch from Alpha Vantage API."""
        api_key = os.getenv(api['api_key_env'])
        if not api_key:
            return None
        
        url = api['base_url']
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': f'{ticker}.BSE',  # Bombay Stock Exchange
            'apikey': api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=api['timeout_seconds']) as response:
                if response.status == 200:
                    data = await response.json()
                    quote = data.get('Global Quote', {})
                    
                    if not quote:
                        return None
                    
                    return {
                        'ticker': ticker,
                        'exchange': 'BSE',
                        'current_price': float(quote.get('05. price', 0)),
                        'previous_close': float(quote.get('08. previous close', 0)),
                        'day_high': float(quote.get('03. high', 0)),
                        'day_low': float(quote.get('04. low', 0)),
                        'volume': int(quote.get('06. volume', 0)),
                        'timestamp': datetime.now().isoformat(),
                        'provider': 'Alpha Vantage'
                    }
                else:
                    return None
    
    async def _fetch_marketstack(self, api: Dict, ticker: str) -> Optional[Dict]:
        """Fetch from Marketstack API."""
        api_key = os.getenv(api['api_key_env'])
        if not api_key:
            return None
        
        base_url = api['base_url']
        endpoint = api['endpoints']['eod']
        
        url = f"{base_url}{endpoint}"
        params = {
            'access_key': api_key,
            'symbols': f'{ticker}.XNSE'  # NSE Exchange
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=api['timeout_seconds']) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if not data.get('data'):
                        return None
                    
                    latest = data['data'][0]
                    
                    return {
                        'ticker': ticker,
                        'exchange': 'NSE',
                        'current_price': latest.get('close', 0),
                        'previous_close': latest.get('open', 0),
                        'day_high': latest.get('high', 0),
                        'day_low': latest.get('low', 0),
                        'volume': latest.get('volume', 0),
                        'timestamp': datetime.now().isoformat(),
                        'provider': 'Marketstack'
                    }
                else:
                    return None
    
    async def _fetch_yahoo(self, api: Dict, ticker: str) -> Optional[Dict]:
        """Fetch from Yahoo Finance API (fallback)."""
        yahoo_ticker = f"{ticker}.NS"
        url = f"{api['base_url']}/{yahoo_ticker}"
        params = {
            'interval': '1d',
            'range': '1d'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=api['timeout_seconds']) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'chart' not in data or 'result' not in data['chart']:
                        return None
                    
                    result = data['chart']['result'][0]
                    meta = result.get('meta', {})
                    
                    return {
                        'ticker': ticker,
                        'exchange': 'NSE',
                        'current_price': meta.get('regularMarketPrice', 0),
                        'previous_close': meta.get('previousClose', 0),
                        'day_high': meta.get('regularMarketDayHigh', 0),
                        'day_low': meta.get('regularMarketDayLow', 0),
                        'volume': meta.get('regularMarketVolume', 0),
                        'timestamp': datetime.now().isoformat(),
                        'provider': 'Yahoo Finance'
                    }
                else:
                    return None
    
    async def get_company_news(self, ticker: str, days_back: int = 7) -> List[Dict]:
        """
        Get news for a company from Finnhub.
        
        Args:
            ticker: Stock ticker
            days_back: Number of days of news to fetch
            
        Returns:
            List of news articles
        """
        finnhub_api = next((api for api in self.apis if api['name'] == 'Finnhub'), None)
        
        if not finnhub_api:
            return []
        
        api_key = os.getenv(finnhub_api['api_key_env'])
        if not api_key:
            return []
        
        from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')
        
        url = f"{finnhub_api['base_url']}{finnhub_api['endpoints']['news']}"
        params = {
            'symbol': ticker,
            'from': from_date,
            'to': to_date,
            'token': api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            logger.error(f"Error fetching news from Finnhub: {e}")
        
        return []

    async def get_stock_history(self, ticker: str, days: int = 5) -> Dict[str, Any]:
        """
        Get historical stock data (candles) for a ticker.
        Tries Finnhub -> yfinance -> Upstox.
        
        Args:
            ticker: Stock ticker
            days: Number of days of history
            
        Returns:
            Dictionary with historical data
        """
        # 1. Try Finnhub (Primary)
        finnhub_api = next((api for api in self.apis if api['name'] == 'Finnhub'), None)
        if finnhub_api:
            api_key = os.getenv(finnhub_api['api_key_env'])
            if api_key:
                try:
                    # Calculate timestamps
                    to_date = int(datetime.now().timestamp())
                    from_date = int((datetime.now() - timedelta(days=days)).timestamp())
                    
                    # Append .NS for Indian stocks if not present (but NOT for indices)
                    if not ticker.endswith(('.NS', '.BO')) and not ticker.startswith('^'):
                        search_ticker = f"{ticker}.NS"
                    else:
                        search_ticker = ticker
                        
                    url = f"{finnhub_api['base_url']}/stock/candle"
                    params = {
                        'symbol': search_ticker,
                        'resolution': '60',  # 60 minute candles
                        'from': from_date,
                        'to': to_date,
                        'token': api_key
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, params=params, timeout=10) as response:
                            if response.status == 200:
                                data = await response.json()
                                if data.get('s') == 'ok':
                                    logger.info(f"✅ Finnhub history success for {ticker}")
                                    return {
                                        'timestamps': data.get('t', []),
                                        'opens': data.get('o', []),
                                        'highs': data.get('h', []),
                                        'lows': data.get('l', []),
                                        'closes': data.get('c', []),
                                        'volumes': data.get('v', [])
                                    }
                except Exception as e:
                    logger.warning(f"Finnhub history failed for {ticker}: {e}")

        # 2. Try yfinance (Fallback 1)
        logger.info(f"🔄 Trying yfinance fallback for {ticker} history...")
        try:
            import yfinance as yf
            
            suffixes_to_try = []
            if not ticker.endswith(('.NS', '.BO')):
                suffixes_to_try = [f"{ticker}.NS", f"{ticker}.BO"]
            else:
                suffixes_to_try = [ticker]
            
            for ticker_with_suffix in suffixes_to_try:
                try:
                    stock = yf.Ticker(ticker_with_suffix)
                    # Get 60m data for requested days
                    hist = stock.history(period=f"{days}d", interval="60m")
                    
                    if not hist.empty:
                        logger.info(f"✅ yfinance history success for {ticker_with_suffix}")
                        return {
                            'timestamps': (hist.index.astype(int) // 10**9).tolist(),
                            'opens': hist['Open'].tolist(),
                            'highs': hist['High'].tolist(),
                            'lows': hist['Low'].tolist(),
                            'closes': hist['Close'].tolist(),
                            'volumes': hist['Volume'].tolist()
                        }
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"yfinance fallback failed: {e}")

        # 3. Try Upstox (Fallback 2)
        logger.info(f"🔄 Trying Upstox fallback for {ticker} history...")
        try:
            from app.services.upstox_api import fetch_upstox_historical
            hist = fetch_upstox_historical(ticker, "1hour", days)
            
            if hist is not None and not hist.empty:
                logger.info(f"✅ Upstox history success for {ticker}")
                return {
                    'timestamps': (hist.index.astype(int) // 10**9).tolist(),
                    'opens': hist['Open'].tolist(),
                    'highs': hist['High'].tolist(),
                    'lows': hist['Low'].tolist(),
                    'closes': hist['Close'].tolist(),
                    'volumes': hist['Volume'].tolist()
                }
        except Exception as e:
            logger.error(f"Upstox fallback failed: {e}")
        
        return {}


    async def search_symbol(self, query: str, country: str = "All") -> List[Dict[str, str]]:
        """
        Search for a stock symbol using Alpha Vantage -> Yahoo Finance -> yfinance.
        
        Args:
            query: Search query
            country: Country filter (e.g., "India", "United States", "All")
            
        Returns:
            List of matching stocks
        """
        # Check cache
        cache_key = f"search_{query}_{country}"
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if datetime.now() - cached_time < timedelta(minutes=60): # Cache for 1 hour
                return cached_data

        results = []
        
        # 1. Try Alpha Vantage
        try:
            av_results = await self._search_alpha_vantage(query, country)
            if av_results:
                results.extend(av_results)
        except Exception as e:
            logger.warning(f"Alpha Vantage search failed: {e}")
            
        # 2. Try Yahoo Finance (yahooquery) if results are low
        if len(results) < 3:
            try:
                yf_results = await self._search_yahoo_query(query, country)
                # Deduplicate
                existing_tickers = {r['ticker'] for r in results}
                for res in yf_results:
                    if res['ticker'] not in existing_tickers:
                        results.append(res)
            except Exception as e:
                logger.warning(f"Yahoo search failed: {e}")

        # 3. Try Web Search (DuckDuckGo) Fallback
        # This is very effective for partial queries like "zomat" -> "ZOMATO.NS"
        if not results:
            logger.info(f"🔄 Trying Web Search fallback for '{query}'...")
            try:
                web_results = await self._search_web_fallback(query, country)
                if web_results:
                    results.extend(web_results)
                    logger.info(f"✅ Web Search found {len(web_results)} results")
            except Exception as e:
                logger.warning(f"Web Search fallback failed: {e}")
                
        # 4. Try yfinance Ticker check (Last resort for exact matches)
        if not results and len(query) > 2:
            try:
                import yfinance as yf
                # Try adding suffixes for India
                suffixes = [".NS", ".BO"] if country in ["India", "All"] else [""]
                
                for suffix in suffixes:
                    ticker_to_check = f"{query.upper()}{suffix}"
                    try:
                        ticker_obj = yf.Ticker(ticker_to_check)
                        info = ticker_obj.info
                        if info and 'shortName' in info:
                            results.append({
                                "ticker": query.upper(),
                                "name": info.get('shortName', info.get('longName', query)),
                                "exchange": "NSE" if suffix == ".NS" else "BSE" if suffix == ".BO" else "Unknown",
                                "sector": info.get('sector', 'Unknown')
                            })
                            break
                    except:
                        continue
            except Exception as e:
                logger.warning(f"yfinance search check failed: {e}")
        
        # Cache results if found
        if results:
            self.cache[cache_key] = (results, datetime.now())
            
        return results

    async def _search_alpha_vantage(self, query: str, country: str) -> List[Dict]:
        """Helper to search Alpha Vantage."""
        alpha_vantage_api = next((api for api in self.apis if api['name'] == 'Alpha Vantage'), None)
        if not alpha_vantage_api: return []
        
        api_key = os.getenv(alpha_vantage_api['api_key_env'])
        if not api_key: return []
        
        url = alpha_vantage_api['base_url']
        params = {'function': 'SYMBOL_SEARCH', 'keywords': query, 'apikey': api_key}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    matches = data.get('bestMatches', [])
                    return self._filter_results(matches, country, source="AV")
        return []

    async def _search_yahoo_query(self, query: str, country: str) -> List[Dict]:
        """Helper to search Yahoo Finance via yahooquery."""
        from yahooquery import search
        import asyncio
        
        # Run synchronous yahooquery in thread pool
        loop = asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: search(query))
            quotes = data.get('quotes', [])
            return self._filter_results(quotes, country, source="YF")
        except Exception as e:
            logger.error(f"YahooQuery error: {e}")
            return []

    async def _search_web_fallback(self, query: str, country: str) -> List[Dict]:
        """
        Fallback: Search the web for the ticker using DuckDuckGo.
        Useful when APIs fail or return no results for partial queries.
        """
        from duckduckgo_search import DDGS
        import re
        import asyncio
        
        results = []
        
        # Construct search query
        search_query = f"{query} share price"
        if country == "India":
            search_query += " India"
        elif country == "United States":
            search_query += " US"
            
        logger.info(f"🕵️ Web Search Query: {search_query}")
        
        try:
            # Run synchronous DDGS in thread pool
            loop = asyncio.get_event_loop()
            
            def run_search():
                with DDGS() as ddgs:
                    return list(ddgs.text(search_query, region="in-en" if country == "India" else "wt-wt", backend="html", max_results=5))
            
            ddg_results = await loop.run_in_executor(None, run_search)
            
            if not ddg_results:
                return []
                
            # Regex to find tickers in titles/snippets
            # Strategy 1: Look for explicit patterns like (TICKER) or NSE: TICKER
            explicit_pattern = re.compile(r'\(([A-Z0-9]+(?:\.[A-Z]+)?)\)|NSE:\s*([A-Z0-9]+)|BSE:\s*([A-Z0-9]+)')
            
            # Strategy 2: Look for all caps words (potential tickers)
            caps_pattern = re.compile(r'\b([A-Z]{3,10})\b')
            
            # Common words to ignore
            stop_words = {
                'SHARE', 'PRICE', 'STOCK', 'LIVE', 'NSE', 'BSE', 'INDIA', 'LTD', 'NEWS', 
                'TODAY', 'MARKET', 'MONEYCONTROL', 'FINANCE', 'LIMITED', 'CHART', 'VALUE',
                'ANALYSIS', 'TARGET', 'BUY', 'SELL', 'GURU', 'SCREENER', 'TREND', 'INVEST'
            }
            
            found_tickers = set()
            
            for res in ddg_results:
                title = res.get('title', '')
                body = res.get('body', '')
                text = f"{title} {body}"
                
                # 1. Try explicit patterns first
                matches = explicit_pattern.findall(text)
                for match in matches:
                    # match is a tuple of groups, pick the non-empty one
                    ticker = next((m for m in match if m), None)
                    if ticker:
                        ticker = ticker.upper()
                        # Add suffix if missing and country is India
                        if country == "India" and not ticker.endswith(('.NS', '.BO')):
                            # Default to NSE
                            ticker = f"{ticker}.NS"
                            
                        if ticker not in found_tickers:
                            results.append({
                                "ticker": ticker.replace('.NS', ''), # Clean for display
                                "name": title.split('Share Price')[0].strip(),
                                "exchange": "NSE" if ".NS" in ticker else "BSE" if ".BO" in ticker else "Unknown",
                                "sector": "Unknown"
                            })
                            found_tickers.add(ticker)

                # 2. If no explicit matches, try heuristic (all caps words)
                # Only if we have few results
                if len(results) < 2:
                    caps_matches = caps_pattern.findall(title) # Only check title for heuristics to reduce noise
                    for word in caps_matches:
                        if word not in stop_words and word not in found_tickers:
                            # Heuristic: If query is "zomat" and word is "ZOMATO", it's likely a match
                            # Or if word starts with query (case insensitive)
                            if query.upper() in word or word in query.upper() or len(word) >= 3:
                                ticker = word
                                if country == "India":
                                    ticker = f"{word}.NS"
                                
                                if ticker not in found_tickers:
                                    results.append({
                                        "ticker": word,
                                        "name": title.split('Share Price')[0].strip(),
                                        "exchange": "NSE" if country == "India" else "Unknown",
                                        "sector": "Unknown"
                                    })
                                    found_tickers.add(ticker)
                            
            return results[:3] # Return top 3 unique matches
            
        except Exception as e:
            logger.error(f"Web Search error: {e}")
            return []

    def _filter_results(self, matches: List[Dict], country: str, source: str) -> List[Dict]:
        """Filter and normalize search results from different providers."""
        results = []
        
        # Country to Region/Exchange keywords mapping
        country_map = {
            "India": ["India", "Bombay", "NSE", "BSE", "NSI"],
            "United States": ["United States", "NASDAQ", "NYSE", "AMEX", "BATS", "USA"],
            "United Kingdom": ["United Kingdom", "London", "LSE"],
            "Canada": ["Canada", "Toronto", "Vancouver", "TSX", "CN"],
            "Germany": ["Germany", "Frankfurt", "XETRA", "Berlin", "Munich", "Stuttgart", "DE"],
            "France": ["France", "Paris", "FR"],
            "China": ["China", "Shanghai", "Shenzhen", "HK"],
            "Japan": ["Japan", "Tokyo", "JP"],
            "Australia": ["Australia", "Sydney", "AU"],
            "Brazil": ["Brazil", "Sao Paolo", "BR"],
        }
        
        target_keywords = country_map.get(country, []) if country != "All" else []

        for match in matches:
            # Normalize fields based on source
            if source == "AV":
                symbol = match.get('1. symbol')
                name = match.get('2. name')
                region = match.get('4. region', '')
                exch = region
            else: # YF
                symbol = match.get('symbol')
                name = match.get('longname') or match.get('shortname')
                exch = match.get('exchange', '')
                # Yahoo doesn't give 'region' directly in quotes, infer from exchange or symbol
                region = exch
            
            if not symbol or not name:
                continue

            # Filter logic
            if country != "All":
                match_found = False
                
                # Check keywords
                for keyword in target_keywords:
                    if keyword.lower() in region.lower() or keyword.lower() in exch.lower():
                        match_found = True
                        break
                
                # Suffix checks
                if country == "India" and symbol.endswith(('.NS', '.BO', '.BSE')): match_found = True
                if country == "Canada" and symbol.endswith('.TO'): match_found = True
                if country == "United Kingdom" and symbol.endswith('.L'): match_found = True
                
                if not match_found:
                    continue

            # Normalize ticker: Remove exchange suffixes for cleaner symbols
            clean_symbol = symbol
            # Remove common Indian exchange suffixes
            if symbol.endswith('.NS'):
                clean_symbol = symbol[:-3]  # Remove .NS
            elif symbol.endswith('.BO'):
                clean_symbol = symbol[:-3]  # Remove .BO
            elif symbol.endswith('.BSE'):
                clean_symbol = symbol[:-4]  # Remove .BSE
            # Remove other common suffixes
            elif symbol.endswith('.TO'):
                clean_symbol = symbol[:-3]
            elif symbol.endswith('.L'):
                clean_symbol = symbol[:-2]

            results.append({
                "ticker": clean_symbol,  # Use cleaned symbol
                "name": name,
                "exchange": exch,
                "sector": "Unknown"
            })
            
        return results
    
    def get_historical_data(self, ticker: str, period: str = "3mo", interval: str = "1d") -> Optional[Any]:
        """
        Get historical OHLCV data using Upstox API (primary) with yfinance fallback.
        
        Args:
            ticker: Stock ticker (e.g., 'SBIN', 'BEL')
            period: Data period - 1d, 5d, 1mo, 3mo, 6mo, 1y
            interval: Data interval - 1m, 5m, 15m, 30m, 60m, 1h, 1d
            
        Returns:
            pandas DataFrame with OHLCV data or None
        """
        from app.services.upstox_api import fetch_upstox_historical
        
        # Map intervals to Upstox format and days
        interval_upstox_map = {
            "1m": ("1minute", 1),
            "5m": ("5minute", 5),
            "15m": ("15minute", 15),
            "30m": ("30minute", 30),
            "60m": ("1hour", 60),
            "1h": ("1hour", 60),
            "1d": ("day", 365),
        }
        
        period_days_map = {
            "1d": 1,
            "5d": 5,
            "1mo": 30,
            "3mo": 90,
            "6mo": 180,
            "1y": 365,
        }
        
        upstox_interval, _ = interval_upstox_map.get(interval, ("day", 1))
        days = period_days_map.get(period, 90)
        
        # PRIMARY: Try Upstox API (FREE, no auth required!)
        hist = fetch_upstox_historical(ticker, upstox_interval, days)
        if hist is not None and not hist.empty:
            return hist
        
        # FALLBACK 1: Try yfinance
        logger.info(f"Upstox unavailable for {ticker}, trying yfinance...")
        try:
            import yfinance as yf
            
            suffixes_to_try = []
            if not ticker.endswith(('.NS', '.BO')):
                suffixes_to_try = [f"{ticker}.NS", f"{ticker}.BO"]
            else:
                suffixes_to_try = [ticker]
            
            for ticker_with_suffix in suffixes_to_try:
                try:
                    stock = yf.Ticker(ticker_with_suffix)
                    hist = stock.history(period=period, interval=interval)
                    
                    if not hist.empty:
                        logger.info(f"✅ yfinance: Got {len(hist)} data points for {ticker_with_suffix}")
                        return hist
                except Exception as e:
                    logger.debug(f"yfinance failed {ticker_with_suffix}: {e}")
                    continue
        except Exception as e:
            logger.error(f"yfinance fallback failed: {e}")

        # FALLBACK 2: Try yahooquery
        logger.info(f"yfinance unavailable for {ticker}, trying yahooquery...")
        try:
            from yahooquery import Ticker
            
            suffixes_to_try = []
            if not ticker.endswith(('.NS', '.BO')):
                suffixes_to_try = [f"{ticker}.NS", f"{ticker}.BO"]
            else:
                suffixes_to_try = [ticker]
                
            for ticker_with_suffix in suffixes_to_try:
                try:
                    t = Ticker(ticker_with_suffix)
                    hist = t.history(period=period, interval=interval)
                    
                    if not hist.empty:
                        # Reset index to match yfinance format if needed, or just return as is
                        # yahooquery returns multi-index (symbol, date)
                        if isinstance(hist.index, pd.MultiIndex):
                            hist = hist.reset_index(level=0, drop=True)
                        
                        logger.info(f"✅ yahooquery: Got {len(hist)} data points for {ticker_with_suffix}")
                        return hist
                except Exception:
                    continue
                    
        except Exception as e:
            logger.error(f"yahooquery fallback failed: {e}")
            
        logger.warning(f"⚠️ No historical data for {ticker} from any source")
        return None
    
    def get_historical_data_multi_period(self, ticker: str) -> Dict[str, Any]:
        """
        Get historical data for multiple timeframes for candlestick charts.
        
        Args:
            ticker: Stock ticker (e.g., 'SBIN', 'BEL')
            
        Returns:
            Dict with DataFrames for each period:
            {
                "1d": DataFrame (1-minute intervals),
                "5d": DataFrame (5-minute intervals),
                "1mo": DataFrame (1-hour intervals),
                "3mo": DataFrame (1-day intervals),
                "1y": DataFrame (1-day intervals)
            }
        """
        periods_config = {
            "1d": {"period": "1d", "interval": "1m"},    # 1 day, 1-min intervals
            "5d": {"period": "5d", "interval": "5m"},    # 5 days, 5-min intervals
            "1mo": {"period": "1mo", "interval": "1h"},  # 1 month, 1-hour intervals
            "3mo": {"period": "3mo", "interval": "1d"},  # 3 months, 1-day intervals
            "1y": {"period": "1y", "interval": "1d"}     # 1 year, 1-day intervals
        }
        
        result = {}
        
        for period_key, config in periods_config.items():
            hist = self.get_historical_data(
                ticker,
                period=config["period"],
                interval=config["interval"]
            )
            
            if hist is not None:
                result[period_key] = hist
            else:
                result[period_key] = None
                
        return result


# Global instance
stock_api_service = StockAPIService()
