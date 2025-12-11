"""
Upstox API integration for historical stock data (NSE/BSE).
FREE API - No authentication required!
"""
import logging
import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict
import json

logger = logging.getLogger(__name__)

# Cache for instrument keys to avoid repeated API calls
_instrument_cache: Dict[str, str] = {}


def get_instrument_key(ticker: str) -> Optional[str]:
    """
    Dynamically resolve ticker symbol to Upstox instrument key.
    
    Uses NSE India API to get ISIN, then constructs Upstox instrument key.
    Results are cached to minimize API calls.
    
    Args:
        ticker: Stock ticker symbol (e.g., "SBIN", "HAL", "TATAMOTORS")
        
    Returns:
        Instrument key (e.g., "NSE_EQ|INE062A01020") or None
    """
    ticker_upper = ticker.upper()
    
    # Check cache first
    if ticker_upper in _instrument_cache:
        logger.debug(f"Cache hit for {ticker_upper}: {_instrument_cache[ticker_upper]}")
        return _instrument_cache[ticker_upper]
    
    try:
        # Use NSE India API to get ISIN code (FREE, no auth required)
        # This API provides stock metadata including ISIN
        nse_url = f"https://www.nseindia.com/api/quote-equity?symbol={ticker_upper}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
           'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.nseindia.com/'
        }
        
        logger.info(f"🔍 Looking up ISIN for {ticker_upper} from NSE...")
        
        # Create session to maintain cookies
        session = requests.Session()
        
        # First visit NSE homepage to get cookies
        session.get('https://www.nseindia.com', headers=headers, timeout=10)
        
        # Now fetch stock data
        response = session.get(nse_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract ISIN from response
            isin = data.get('info', {}).get('isin')
            
            if isin:
                # Construct Upstox instrument key: NSE_EQ|ISIN
                instrument_key = f"NSE_EQ|{isin}"
                
                # Cache and return
                _instrument_cache[ticker_upper] = instrument_key
                logger.info(f"✅ Found instrument key for {ticker_upper}: {instrument_key}")
                return instrument_key
            else:
                logger.warning(f"❌ No ISIN found in NSE response for {ticker_upper}")
                return None
        else:
            logger.warning(f"❌ NSE API returned status {response.status_code} for {ticker_upper}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error resolving instrument key for {ticker}: {e}")
        return None


def fetch_upstox_historical(ticker: str, interval: str, days: int) -> Optional[pd.DataFrame]:
    """
    Fetch historical candle data from Upstox API (FREE, no authentication).
    
    Dynamically resolves ticker to instrument key, works for ANY Indian stock!
    
    Args:
        ticker: Stock ticker symbol (e.g., "SBIN", "HAL", "TATAMOTORS")
        interval: "1minute", "5minute", "30minute", "1hour", "day"
        days: Number of days of historical data to fetch
        
    Returns:
        pandas DataFrame with OHLCV data or None if failed
    """
    # Dynamically get instrument key
    instrument_key = get_instrument_key(ticker)
    if not instrument_key:
        logger.warning(f"❌ Cannot fetch data for {ticker} - instrument key not found")
        return None
    
    # Calculate date range
    to_date = datetime.now()
    from_date = to_date - timedelta(days=days)
    
    # Format dates as YYYY-MM-DD
    to_date_str = to_date.strftime("%Y-%m-%d")
    from_date_str = from_date.strftime("%Y-%m-%d")
    
    # Upstox FREE API endpoint (NO AUTH REQUIRED!)
    url = f"https://api.upstox.com/v2/historical-candle/{instrument_key}/{interval}/{to_date_str}/{from_date_str}"
    
    logger.info(f"📊 Fetching {ticker} from Upstox: {interval}, {days} days")
    logger.info(f"🔗 Upstox URL: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('status') == 'success' and data.get('data', {}).get('candles'):
                candles = data['data']['candles']
                
                # Parse candle data: [timestamp, open, high, low, close, volume, oi]
                timestamps = []
                opens = []
                highs = []
                lows = []
                closes = []
                volumes = []
                
                for candle in candles:
                    if len(candle) >= 6:
                        # Upstox returns ISO datetime string
                        timestamps.append(pd.to_datetime(candle[0]))
                        opens.append(float(candle[1]))
                        highs.append(float(candle[2]))
                        lows.append(float(candle[3]))
                        closes.append(float(candle[4]))
                        volumes.append(int(candle[5]))
                
                if timestamps:
                    df = pd.DataFrame({
                        'Open': opens,
                        'High': highs,
                        'Low': lows,
                        'Close': closes,
                        'Volume': volumes
                    }, index=timestamps)
                    
                    # Sort by timestamp (oldest first)
                    df = df.sort_index()
                    
                    logger.info(f"✅ Upstox: Fetched {len(df)} candles for {ticker} ({interval})")
                    return df
                else:
                    logger.warning(f"⚠️ Upstox: Empty candle data for {ticker}")
                    return None
            else:
                logger.warning(f"⚠️ Upstox: API returned no candles for {ticker}")
                logger.debug(f"Response: {data}")
                return None
        else:
            logger.error(f"❌ Upstox API error: HTTP {response.status_code} for {ticker}")
            logger.debug(f"Response: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Exception fetching from Upstox for {ticker}: {e}")
        return None
