"""
Relative Strength Calculator
Calculate RS vs NIFTY and sector using existing stock_api_service
"""

import pandas as pd
from typing import Tuple
from app.services.stock_api_service import stock_api_service
from .sector_mapping import get_sector_for_symbol, get_sector_etf
import logging

logger = logging.getLogger(__name__)


def calculate_percentage_return(df: pd.DataFrame, periods: int = 20) -> float:
    """
    Calculate percentage return over N periods
    
    Args:
        df: DataFrame with Close prices
        periods: Lookback period
        
    Returns:
        Percentage return
    """
    if len(df) < periods:
        return 0.0
    
    close_col = 'Close' if 'Close' in df.columns else 'close'
    
    current_price = df[close_col].iloc[-1]
    past_price = df[close_col].iloc[-periods]
    
    if past_price == 0:
        return 0.0
    
    return ((current_price - past_price) / past_price) * 100


def calculate_relative_strength(
    symbol: str,
    period="1mo",
    lookback_days: int = 20
) -> Tuple[float, float, str, str]:
    """
    Calculate relative strength vs NIFTY and sector
    
    Args:
        symbol: Stock symbol
        period: Data period to fetch
        lookback_days: Days to calculate returns over
        
    Returns:
        (rs_vs_nifty, rs_vs_sector, sector_symbol, sector_trend)
        
    RS Formula:
        RS = (Stock Return / Benchmark Return)
        > 1.0 = Outperforming
        < 1.0 = Underperforming
        = 1.0 = Inline
    """
    
    try:
        # Fetch stock data (sync method, not async)
        stock_df = stock_api_service.get_historical_data(symbol, period=period, interval="1d")
        
        if stock_df is None or len(stock_df) < lookback_days:
            logger.warning(f"Insufficient data for {symbol}, returning default RS")
            return (1.0, 1.0, "UNKNOWN", "neutral")
        
        # Calculate stock return
        stock_return = calculate_percentage_return(stock_df, lookback_days)
        
        # Fetch NIFTY data
        nifty_df = stock_api_service.get_historical_data("^NSEI", period=period, interval="1d")
        
        if nifty_df is not None and len(nifty_df) >= lookback_days:
            nifty_return = calculate_percentage_return(nifty_df, lookback_days)
            
            # Calculate RS vs NIFTY
            if nifty_return != 0:
                rs_vs_nifty = (stock_return / nifty_return) if nifty_return != 0 else 1.0
            else:
                rs_vs_nifty = 1.0
        else:
            rs_vs_nifty = 1.0
        
        # Get sector and calculate RS vs sector
        sector_symbol = get_sector_etf(symbol)
        sector_name = get_sector_for_symbol(symbol)
        
        if sector_symbol != "^NSEI":  # If we have a specific sector ETF
            sector_df = stock_api_service.get_historical_data(sector_symbol, period=period, interval="1d")
            
            if sector_df is not None and len(sector_df) >= lookback_days:
                sector_return = calculate_percentage_return(sector_df, lookback_days)
                
                # Calculate RS vs sector
                rs_vs_sector = (stock_return / sector_return) if sector_return != 0 else 1.0
                
                # Determine sector trend
                if sector_return > 2:
                    sector_trend = "strong"
                elif sector_return < -2:
                    sector_trend = "weak"
                else:
                    sector_trend = "neutral"
            else:
                rs_vs_sector = 1.0
                sector_trend = "neutral"
        else:
            # No sector data, use NIFTY as proxy
            rs_vs_sector = rs_vs_nifty
            sector_trend = "neutral"
        
        # Clamp RS values to reasonable range (0.1 - 10.0)
        rs_vs_nifty = max(0.1, min(10.0, rs_vs_nifty))
        rs_vs_sector = max(0.1, min(10.0, rs_vs_sector))
        
        return (
            round(rs_vs_nifty, 2),
            round(rs_vs_sector, 2),
            sector_symbol,
            sector_trend
        )
        
    except Exception as e:
        logger.error(f"Error calculating RS for {symbol}: {e}")
        return (1.0, 1.0, "UNKNOWN", "neutral")


def determine_market_leadership(rs_vs_nifty: float, rs_vs_sector: float) -> str:
    """
    Determine if stock is a leader, inline, or laggard
    
    Leader: RS > 1.2 vs both NIFTY and sector
    Inline: RS between 0.8 and 1.2
    Laggard: RS < 0.8
    """
    
    avg_rs = (rs_vs_nifty + rs_vs_sector) / 2
    
    if avg_rs > 1.2:
        return "leader"
    elif avg_rs < 0.8:
        return "laggard"
    else:
        return "inline"
