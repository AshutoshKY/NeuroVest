"""
Service for analyzing technical indicator trends over time.
Provides insights into how indicators are changing (improving, declining, patterns).
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class TechnicalTrendAnalyzer:
    """Analyzes trends in technical indicators over time."""
    
    @staticmethod
    def analyze_indicator_trends(ticker: str, days: int = 30) -> Dict[str, Any]:
        """
        Analyze technical indicator trends over the past N days.
        
        Args:
            ticker: Stock ticker
            days: Number of days to analyze (default 30)
            
        Returns:
            Dict with trend analysis for RSI, MACD, BB, etc.
        """
        try:
            from app.core.database import get_db
            from app.models.analysis_cache import AnalysisCache
            
            db = next(get_db())
            
            # Get past analyses for this ticker
            cutoff_date = datetime.now() - timedelta(days=days)
            past_analyses = db.query(AnalysisCache).filter(
                AnalysisCache.ticker == ticker,
                AnalysisCache.timestamp >= cutoff_date
            ).order_by(AnalysisCache.timestamp.desc()).all()
            
            if len(past_analyses) < 2:
                logger.warning(f"Not enough historical data for {ticker} ({len(past_analyses)} records)")
                return None
            
            # Extract time-series data
            timestamps = [a.timestamp for a in past_analyses]
            rsi_values = [a.rsi for a in past_analyses if a.rsi is not None]
            macd_histograms = [a.macd_histogram for a in past_analyses if a.macd_histogram is not None]
            prices = [a.price for a in past_analyses if a.price is not None]
            sentiment_scores = [a.sentiment_score for a in past_analyses if a.sentiment_score is not None]
            
            trends = {
                "period_days": days,
                "data_points": len(past_analyses)
            }
            
            # RSI Trend Analysis
            if len(rsi_values) >= 2:
                rsi_trend = TechnicalTrendAnalyzer._calculate_trend(rsi_values)
                trends["rsi_trend"] = {
                    "direction": rsi_trend["direction"],
                    "strength": rsi_trend["strength"],
                    "current": rsi_values[0],
                    "avg_30d": np.mean(rsi_values),
                    "change_from_oldest": rsi_values[0] - rsi_values[-1],
                    "interpretation": TechnicalTrendAnalyzer._interpret_rsi_trend(rsi_values)
                }
            
            # MACD Trend Analysis
            if len(macd_histograms) >= 2:
                macd_trend = TechnicalTrendAnalyzer._calculate_trend(macd_histograms)
                trends["macd_trend"] = {
                    "direction": macd_trend["direction"],
                    "strength": macd_trend["strength"],
                    "current": macd_histograms[0],
                    "avg_30d": np.mean(macd_histograms),
                    "interpretation": TechnicalTrendAnalyzer._interpret_macd_trend(macd_histograms)
                }
            
            # Price Trend Analysis
            if len(prices) >= 2:
                price_trend = TechnicalTrendAnalyzer._calculate_trend(prices)
                # Protect against division by zero
                if prices[-1] != 0:
                    price_change_pct = ((prices[0] - prices[-1]) / prices[-1]) * 100
                else:
                    logger.warning(f"Oldest price is zero for {ticker}, cannot calculate percentage change")
                    price_change_pct = 0.0
                
                trends["price_trend"] = {
                    "direction": price_trend["direction"],
                    "strength": price_trend["strength"],
                    "current": prices[0],
                    "oldest": prices[-1],
                    "change_pct": price_change_pct,
                    "volatility": np.std(prices)
                }
            
            # Sentiment Trend Analysis
            if len(sentiment_scores) >= 2:
                sentiment_trend = TechnicalTrendAnalyzer._calculate_trend(sentiment_scores)
                trends["sentiment_trend"] = {
                    "direction": sentiment_trend["direction"],
                    "current": sentiment_scores[0],
                    "avg_30d": np.mean(sentiment_scores),
                    "change_from_oldest": sentiment_scores[0] - sentiment_scores[-1]
                }
            
            logger.info(f"📊 Analyzed {days}-day trends for {ticker}: {len(past_analyses)} data points")
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing trends for {ticker}: {e}")
            return None
    
    @staticmethod
    def _calculate_trend(values: List[float]) -> Dict[str, Any]:
        """Calculate trend direction and strength using linear regression."""
        if len(values) < 2:
            return {"direction": "Unknown", "strength": 0.0}
        
        # Simple linear regression
        x = np.arange(len(values))
        y = np.array(values)
        
        # Calculate slope
        slope = np.polyfit(x, y, 1)[0]
        
        # Normalize slope to strength (-1 to 1)
        max_val = max(abs(min(values)), abs(max(values)))
        strength = slope / max_val if max_val != 0 else 0
        
        # Determine direction
        if abs(slope) < 0.01:
            direction = "Flat"
        elif slope > 0:
            direction = "Rising"
        else:
            direction = "Declining"
        
        return {
            "direction": direction,
            "strength": abs(strength),
            "slope": slope
        }
    
    @staticmethod
    def _interpret_rsi_trend(rsi_values: List[float]) -> str:
        """Interpret RSI trend pattern."""
        current = rsi_values[0]
        avg = np.mean(rsi_values)
        
        if current > 70 and avg > 65:
            return "Sustained overbought - potential correction risk"
        elif current < 30 and avg < 35:
            return "Sustained oversold - potential bounce opportunity"
        elif current > avg + 10:
            return "Strengthening momentum"
        elif current < avg - 10:
            return "Weakening momentum"
        else:
            return "Stable momentum"
    
    @staticmethod
    def _interpret_macd_trend(macd_histograms: List[float]) -> str:
        """Interpret MACD histogram trend."""
        current = macd_histograms[0]
        
        # Check if histogram is growing or shrinking
        if len(macd_histograms) >= 3:
            recent = macd_histograms[:3]
            if all(recent[i] > recent[i+1] for i in range(len(recent)-1)):
                return "Strengthening bullish momentum"
            elif all(recent[i] < recent[i+1] for i in range(len(recent)-1)):
                return "Weakening momentum (potential reversal)"
        
        if current > 0:
            return "Bullish momentum"
        elif current < 0:
            return "Bearish momentum"
        else:
            return "Neutral momentum"
