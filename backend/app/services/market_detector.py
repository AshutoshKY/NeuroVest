"""
Market Detector Service
=======================

Detects whether a stock ticker belongs to US or Indian markets.
Uses suffix detection and common ticker lists for fast classification.

Author: NeuroVest
Date: 2025-12-13
"""

import logging
from typing import Literal, Optional, Set
from functools import lru_cache

logger = logging.getLogger(__name__)

MarketType = Literal["US", "INDIA", "UNKNOWN"]


class MarketDetector:
    """
    Detect stock market for intelligent API routing.
    
    Detection Logic:
    1. Check ticker suffix (.NS, .BO, .BSE → INDIA)
    2. Check exchange prefix (NSE:, BSE: → INDIA)
    3. Check against known ticker lists (cached)
    4. Default to INDIA (primary market)
    """
    
    # Common US tickers (top 100)
    US_TICKERS: Set[str] = {
        "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA",
        "BRK.A", "BRK.B", "UNH", "JNJ", "XOM", "V", "PG", "JPM", "MA",
        "HD", "CVX", "MRK", "ABBV", "LLY", "PEP", "COST", "AVGO", "KO",
        "TMO", "WMT", "MCD", "CSCO", "ACN", "ABT", "DHR", "NKE", "VZ",
        "ADBE", "CRM", "NFLX", "TXN", "NEE", "CMCSA", "PM", "UPS", "RTX",
        "ORCL", "QCOM", "HON", "AMGN", "SCHW", "INTC", "LOW", "AMD",
        "BA", "CAT", "SBUX", "GILD", "AXP", "GE", "DE", "IBM", "SPGI",
        "BKNG", "BLK", "T", "MMC", "MDLZ", "PLD", "ELV", "SYK", "ADI",
        "VRTX", "CI", "AMT", "ZTS", "ISRG", "TJX", "LRCX", "ADP", "REGN",
        "CVS", "MO", "SO", "PGR", "CB", "TMUS", "DUK", "ETN", "BSX",
        "AON", "SLB", "MMM", "BDX", "ITW", "GD", "APD", "CL", "EQIX"
    }
    
    # Common Indian tickers (top 100)
    INDIAN_TICKERS: Set[str] = {
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR",
        "ITC", "SBIN", "BHARTIARTL", "BAJFINANCE", "KOTAKBANK", "LT",
        "ASIANPAINT", "AXISBANK", "MARUTI", "TITAN", "SUNPHARMA", "ULTRACEMCO",
        "NESTLEIND", "DMART", "BAJAJFINSV", "TECHM", "POWERGRID", "NTPC",
        "HCLTECH", "ONGC", "TATAMOTORS", "TATASTEEL", "ADANIENT", "WIPRO",
        "JSWSTEEL", "COALINDIA", "INDUSINDBK", "M&M", "GRASIM", "APOLLOHOSP",
        "DIVISLAB", "ADANIPORTS", "DRREDDY", "BRITANNIA", "CIPLA", "EICHERMOT",
        "VEDL", "HEROMOTOCO", "BPCL", "TATACONSUM", "SHREECEM", "HINDPETRO",
        "IOC", "UPL", "SBILIFE", "BAJAJ-AUTO", "HDFCLIFE", "HINDALCO",
        "GODREJCP", "DABUR", "HAVELLS", "PIDILITIND", "BERGEPAINT", "BANDHANBNK",
        "ICICIGI", "AMBUJACEM", "SIEMENS", "DLF", "GAIL", "CHOLAFIN",
        "HAL", "BEL", "BDL", "BEML", "GRSE", "MDL", "COCHINSHIP",
        "ZOMATO", "PAYTM", "NYKAA", "POLICYBZR", "DELHIVERY"
    }
    
    def __init__(self):
        """Initialize market detector."""
        self.us_tickers = self.US_TICKERS
        self.indian_tickers = self.INDIAN_TICKERS
        logger.info(f"MarketDetector initialized: {len(self.us_tickers)} US, {len(self.indian_tickers)} Indian tickers")
    
    @lru_cache(maxsize=1000)
    def detect_market(self, ticker: str) -> MarketType:
        """
        Detect market for a given ticker.
        
        Args:
            ticker: Stock ticker symbol (e.g., "AAPL", "RELIANCE.NS", "TCS")
            
        Returns:
            "US", "INDIA", or "UNKNOWN"
            
        Examples:
            >>> detector.detect_market("AAPL")
            "US"
            >>> detector.detect_market("RELIANCE.NS")
            "INDIA"
            >>> detector.detect_market("TCS")
            "INDIA"
        """
        ticker_upper = ticker.upper().strip()
        
        # 1. Check suffix (most reliable)
        if ticker_upper.endswith(('.NS', '.BO', '.BSE')):
            logger.debug(f"Market: INDIA (suffix) - {ticker}")
            return "INDIA"
        
        # 2. Check exchange prefix
        if ticker_upper.startswith(('NSE:', 'BSE:')):
            logger.debug(f"Market: INDIA (prefix) - {ticker}")
            return "INDIA"
        
        # Remove any suffixes for list checking
        base_ticker = ticker_upper.replace('.NS', '').replace('.BO', '').replace('.BSE', '')
        base_ticker = base_ticker.replace('NSE:', '').replace('BSE:', '')
        
        # 3. Check against known US tickers
        if base_ticker in self.us_tickers:
            logger.debug(f"Market: US (known ticker) - {ticker}")
            return "US"
        
        # 4. Check against known Indian tickers
        if base_ticker in self.indian_tickers:
            logger.debug(f"Market: INDIA (known ticker) - {ticker}")
            return "INDIA"
        
        # 5. Default to INDIA (our primary market)
        logger.debug(f"Market: INDIA (default) - {ticker}")
        return "INDIA"
    
    def is_us_market(self, ticker: str) -> bool:
        """Check if ticker is from US market."""
        return self.detect_market(ticker) == "US"
    
    def is_indian_market(self, ticker: str) -> bool:
        """Check if ticker is from Indian market."""
        return self.detect_market(ticker) == "INDIA"
    
    def normalize_ticker(self, ticker: str, market: Optional[MarketType] = None) -> str:
        """
        Normalize ticker for API calls.
        
        Args:
            ticker: Raw ticker symbol
            market: Optional market override
            
        Returns:
            Normalized ticker for the detected/specified market
            
        Examples:
            >>> detector.normalize_ticker("RELIANCE", "INDIA")
            "RELIANCE.NS"
            >>> detector.normalize_ticker("AAPL", "US")
            "AAPL"
        """
        if market is None:
            market = self.detect_market(ticker)
        
        ticker_upper = ticker.upper().strip()
        
        # Remove existing suffixes
        base_ticker = ticker_upper.replace('.NS', '').replace('.BO', '').replace('.BSE', '')
        base_ticker = base_ticker.replace('NSE:', '').replace('BSE:', '')
        
        if market == "INDIA":
            # Add .NS suffix for Indian stocks (NSE is primary)
            if not ticker_upper.endswith(('.NS', '.BO')):
                return f"{base_ticker}.NS"
        
        return base_ticker
    
    def get_market_suffix(self, market: MarketType) -> str:
        """
        Get appropriate suffix for market.
        
        Args:
            market: Market type
            
        Returns:
            Suffix for Yahoo Finance API
        """
        return ".NS" if market == "INDIA" else ""


# Global instance
market_detector = MarketDetector()
