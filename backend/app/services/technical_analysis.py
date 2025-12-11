"""
Technical Analysis Service
Calculates RSI, MACD, Bollinger Bands and other technical indicators
"""
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator
from ta.volatility import BollingerBands
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class TechnicalAnalysisService:
    """Service for calculating technical indicators"""
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> Optional[float]:
        """
        Calculate RSI (Relative Strength Index)
        
        Args:
            df: DataFrame with 'close' column
            period: RSI period (default: 14)
            
        Returns:
            Current RSI value or None if insufficient data
        """
        try:
            if len(df) < period:
                return None
            
            rsi_indicator = RSIIndicator(close=df['close'], window=period)
            rsi = rsi_indicator.rsi()
            return round(rsi.iloc[-1], 2) if not pd.isna(rsi.iloc[-1]) else None
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return None
    
    @staticmethod
    def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, Any]:
        """
        Calculate MACD (Moving Average Convergence Divergence)
        
        Args:
            df: DataFrame with 'close' column
            fast: Fast EMA period (default: 12)
            slow: Slow EMA period (default: 26)
            signal: Signal line period (default: 9)
            
        Returns:
            Dict with MACD values and signal
        """
        try:
            if len(df) < slow:
                return {"error": "Insufficient data"}
            
            macd_indicator = MACD(close=df['close'], window_fast=fast, window_slow=slow, window_sign=signal)
            
            current_macd = round(macd_indicator.macd().iloc[-1], 2)
            current_signal = round(macd_indicator.macd_signal().iloc[-1], 2)
            current_hist = round(macd_indicator.macd_diff().iloc[-1], 2)
            
            # Determine signal
            prev_hist = macd_indicator.macd_diff().iloc[-2]
            if current_hist > 0 and prev_hist <= 0:
                trend_signal = "Bullish Crossover"
            elif current_hist < 0 and prev_hist >= 0:
                trend_signal = "Bearish Crossover"
            elif current_hist > 0:
                trend_signal = "Bullish"
            else:
                trend_signal = "Bearish"
            
            return {
                "macd": current_macd,
                "signal": current_signal,
                "histogram": current_hist,
                "trend": trend_signal
            }
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std: float = 2.0) -> Dict[str, Any]:
        """
        Calculate Bollinger Bands
        
        Args:
            df: DataFrame with 'close' column
            period: Moving average period (default: 20)
            std: Standard deviation multiplier (default: 2.0)
            
        Returns:
            Dict with Bollinger Band values
        """
        try:
            if len(df) < period:
                return {"error": "Insufficient data"}
            
            bb_indicator = BollingerBands(close=df['close'], window=period, window_dev=std)
            
            current_price = df['close'].iloc[-1]
            upper = round(bb_indicator.bollinger_hband().iloc[-1], 2)
            middle = round(bb_indicator.bollinger_mavg().iloc[-1], 2)
            lower = round(bb_indicator.bollinger_lband().iloc[-1], 2)
            bandwidth = round(bb_indicator.bollinger_wband().iloc[-1], 2)
            
            # Determine price position
            if current_price >= upper:
                position = "Above Upper Band (Overbought)"
            elif current_price <= lower:
                position = "Below Lower Band (Oversold)"
            elif current_price > middle:
                position = "Above Middle (Bullish Zone)"
            else:
                position = "Below Middle (Bearish Zone)"
            
            return {
                "upper": upper,
                "middle": middle,
                "lower": lower,
                "bandwidth": bandwidth,
                "current_price": round(current_price, 2),
                "position": position
            }
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def calculate_sma(df: pd.DataFrame, periods: list = [10, 50, 200]) -> Dict[int, float]:
        """
        Calculate Simple Moving Averages
        
        Args:
            df: DataFrame with 'close' column
            periods: List of periods to calculate
            
        Returns:
            Dict mapping period to SMA value
        """
        try:
            smas = {}
            for period in periods:
                if len(df) >= period:
                    sma_indicator = SMAIndicator(close=df['close'], window=period)
                    sma = sma_indicator.sma_indicator()
                    smas[period] = round(sma.iloc[-1], 2) if not pd.isna(sma.iloc[-1]) else None
            return smas
        except Exception as e:
            logger.error(f"Error calculating SMA: {e}")
            return {}
    
    @staticmethod
    def get_all_indicators(df: pd.DataFrame, ticker: str) -> Dict[str, Any]:
        """
        Calculate all technical indicators
        
        Args:
            df: DataFrame with OHLCV data
            ticker: Stock ticker symbol
            
        Returns:
            Dict with all technical indicators
        """
        if df is None or len(df) < 20:
            return {
                "ticker": ticker,
                "error": "Insufficient historical data for technical analysis",
                "data_points": len(df) if df is not None else 0
            }
        
        # Ensure close column exists
        if 'close' not in df.columns and 'Close' in df.columns:
            df = df.rename(columns={'Close': 'close'})
        
        current_price = df['close'].iloc[-1]
        
        indicators = {
            "ticker": ticker,
            "current_price": round(current_price, 2),
            "timestamp": datetime.now().isoformat(),
            "data_points": len(df),
            "indicators": {}
        }
        
        # RSI
        rsi = TechnicalAnalysisService.calculate_rsi(df)
        if rsi:
            rsi_signal = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
            indicators["indicators"]["rsi"] = {
                "value": rsi,
                "signal": rsi_signal
            }
        
        # MACD
        macd = TechnicalAnalysisService.calculate_macd(df)
        if "error" not in macd:
            indicators["indicators"]["macd"] = macd
        
        # Bollinger Bands
        bbands = TechnicalAnalysisService.calculate_bollinger_bands(df)
        if "error" not in bbands:
            indicators["indicators"]["bollinger_bands"] = bbands
        
        # SMAs
        smas = TechnicalAnalysisService.calculate_sma(df, [10, 50, 200])
        if smas:
            indicators["indicators"]["sma"] = smas
            
            # Trend analysis based on SMA
            if 10 in smas and 50 in smas and current_price > smas[50]:
                indicators["indicators"]["trend"] = "Uptrend"
            elif 10 in smas and 50 in smas and current_price < smas[50]:
                indicators["indicators"]["trend"] = "Downtrend"
            else:
                indicators["indicators"]["trend"] = "Sideways"
        
        return indicators
    
    @staticmethod
    def interpret_indicators(indicators: Dict[str, Any]) -> str:
        """
        Generate human-readable interpretation of technical indicators
        
        Args:
            indicators: Dict from get_all_indicators()
            
        Returns:
            Formatted interpretation string
        """
        if "error" in indicators:
            return f"⚠️ {indicators['error']}"
        
        lines = [f"📊 Technical Analysis for {indicators['ticker']}"]
        lines.append(f"Current Price: ₹{indicators['current_price']}")
        lines.append("")
        
        inds = indicators.get("indicators", {})
        
        # RSI
        if "rsi" in inds:
            rsi_data = inds["rsi"]
            emoji = "🔴" if rsi_data["signal"] == "Overbought" else "🟢" if rsi_data["signal"] == "Oversold" else "🟡"
            lines.append(f"{emoji} RSI (14): {rsi_data['value']} - {rsi_data['signal']}")
        
        # MACD
        if "macd" in inds:
            macd_data = inds["macd"]
            emoji = "📈" if "Bullish" in macd_data["trend"] else "📉"
            lines.append(f"{emoji} MACD: {macd_data['macd']} | Signal: {macd_data['signal']} | {macd_data['trend']}")
        
        # Bollinger Bands
        if "bollinger_bands" in inds:
            bb_data = inds["bollinger_bands"]
            lines.append(f"📊 Bollinger Bands: {bb_data['position']}")
            lines.append(f"   Upper: {bb_data['upper']} | Middle: {bb_data['middle']} | Lower: {bb_data['lower']}")
        
        # Trend
        if "trend" in inds:
            trend_emoji = "⬆️" if inds["trend"] == "Uptrend" else "⬇️" if inds["trend"] == "Downtrend" else "➡️"
            lines.append(f"{trend_emoji} Overall Trend: {inds['trend']}")
        
        return "\n".join(lines)
