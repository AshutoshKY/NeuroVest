"""
Sector Mapping for Indian Stocks
Maps NSE stocks to their sectors and corresponding ETF symbols
"""

# Major Indian sector ETFs (example mapping)
SECTOR_ETF_MAPPING = {
    "BANK": "BANKBEES.NS",  # Banking sector
    "IT": "ITBEES.NS",  # IT sector
    "PHARMA": "PHARMBEES.NS",  # Pharma sector
    "AUTO": "AUTOBEES.NS",  # Auto sector
    "FMCG": "FMCGBEES.NS",  # FMCG sector
    "METAL": "METALBEES.NS",  # Metals sector
    "ENERGY": "ENERGYBEES.NS",  # Energy sector
}

# Stock to sector mapping (simplified - should be expanded)
STOCK_SECTOR_MAP = {
    # Banking
    "HDFC": "BANK",
    "HDFCBANK": "BANK",
    "ICICIBANK": "BANK",
    "SBIN": "BANK",
    "AXISBANK": "BANK",
    "KOTAKBANK": "BANK",
    
    # IT
    "TCS": "IT",
    "INFY": "IT",
    "WIPRO": "IT",
    "HCLTECH": "IT",
    "TECHM": "IT",
    
    # Energy/Oil & Gas
    "RELIANCE": "ENERGY",
    "ONGC": "ENERGY",
    "IOC": "ENERGY",
    "BPCL": "ENERGY",
    
    # Pharma
    "SUNPHARMA": "PHARMA",
    "DRREDDY": "PHARMA",
    "CIPLA": "PHARMA",
    "DIVISLAB": "PHARMA",
    
    # Auto
    "TATAMOTORS": "AUTO",
    "MARUTI": "AUTO",
    "M&M": "AUTO",
    "BAJAJ-AUTO": "AUTO",
    
    # FMCG
    "HINDUNILVR": "FMCG",
    "ITC": "FMCG",
    "NESTLEIND": "FMCG",
    "BRITANNIA": "FMCG",
    
    # Metals
    "TATASTEEL": "METAL",
    "HINDALCO": "METAL",
    "JSWSTEEL": "METAL",
    "VEDL": "METAL",
}


def get_sector_for_symbol(symbol: str) -> str:
    """
    Get sector for a stock symbol
    
    Args:
        symbol: Stock symbol (e.g., "RELIANCE.NS", "INFY")
        
    Returns:
        Sector name or "UNKNOWN"
    """
    # Remove .NS or .BO suffix
    clean_symbol = symbol.split('.')[0].upper()
    
    return STOCK_SECTOR_MAP.get(clean_symbol, "UNKNOWN")


def get_sector_etf(symbol: str) -> str:
    """
    Get the ETF symbol for a stock's sector
    
    Args:
        symbol: Stock symbol
        
    Returns:
        ETF symbol or "^NSEI" (NIFTY as fallback)
    """
    sector = get_sector_for_symbol(symbol)
    
    if sector == "UNKNOWN":
        return "^NSEI"  # Fallback to NIFTY
    
    return SECTOR_ETF_MAPPING.get(sector, "^NSEI")
