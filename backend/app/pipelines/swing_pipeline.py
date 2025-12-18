"""
Swing Trading Pipeline
3-10 day holding period
Focus: Momentum + Volume confirmation
"""

import pandas as pd
from typing import Dict

from app.services.stock_api_service import stock_api_service
from app.signal_engine.service import build_full_signal
from app.signal_engine.schemas import SignalResponse
from .base_pipeline import BasePipeline


class SwingPipeline(BasePipeline):
    """
    Swing trading pipeline (3-10 days)
    
    Characteristics:
    - Daily data
    - Tighter stops (1.5 * ATR)
    - Emphasis on momentum and volume
    - Less weight on long-term trend
    """
    
    @property
    def name(self) -> str:
        return "Swing Trading"
    
    @property
    def timeframe(self) -> str:
        return "swing"
    
    @property
    def typical_holding_days(self) -> int:
        return 7  # Middle of 3-10 day range
    
    @property
    def data_period(self) -> str:
        return "3mo"  # Need 200 days for EMA 200
    
    @property
    def data_interval(self) -> str:
        return "1d"  # Daily candles
    
    async def fetch_data(self, symbol: str) -> pd.DataFrame:
        """Fetch daily data for swing trading"""
        # get_historical_data is SYNC, not async
        return stock_api_service.get_historical_data(
            symbol,
            period=self.data_period,
            interval=self.data_interval
        )
    
    async def generate_signal(self, symbol: str, df: pd.DataFrame = None) -> SignalResponse:
        """Generate swing trading signal"""
        
        if df is None:
            df = await self.fetch_data(symbol)
        
        # Use signal engine with swing timeframe
        signal = await build_full_signal(symbol, df=df, timeframe="swing")
        
        return signal
    
    def get_risk_multiplier(self) -> float:
        """
        Risk multiplier for stops
        Swing: 1.5 * ATR (tighter stops for shorter timeframe)
        """
        return 1.5
    
    def get_confidence_weights(self) -> Dict[str, float]:
        """
        Confidence weights for swing trading
        
        Swing trading emphasizes:
        - Momentum (35%): RSI regimes, MACD crosses
        - Volume (30%): Confirmation critical for short-term moves
        - Trend (20%): Less emphasis on long-term trend
        - Volatility (15%): Moderate importance
        """
        return {
            "momentum": 0.35,
            "volume": 0.30,
            "trend": 0.20,
            "volatility": 0.15
        }
