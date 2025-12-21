"""
Positional Trading Pipeline
2-8 week holding period
Focus: Trend + Structure
"""

import pandas as pd
from typing import Dict

from app.services.stock_api_service import stock_api_service
from app.signal_engine.service import build_full_signal
from app.signal_engine.schemas import SignalResponse
from .base_pipeline import BasePipeline


class PositionalPipeline(BasePipeline):
    """
    Positional trading pipeline (2-8 weeks)
    
    Characteristics:
    - Weekly data
    - Wider stops (3.0 * ATR)
    - Emphasis on trend and structure
    - Less weight on short-term momentum
    """
    
    @property
    def name(self) -> str:
        return "Positional Trading"
    
    @property
    def timeframe(self) -> str:
        return "positional"
    
    @property
    def typical_holding_days(self) -> int:
        return 35  # Middle of 2-8 week range (5 weeks)
    
    @property
    def data_period(self) -> str:
        return "2y"  # Need more data for weekly candles
    
    @property
    def data_interval(self) -> str:
        return "1wk"  # Weekly candles
    
    async def fetch_data(self, symbol: str) -> pd.DataFrame:
        """Fetch weekly data for positional trading"""
        # get_historical_data is SYNC, not async
        return stock_api_service.get_historical_data(
            symbol,
            period=self.data_period,
            interval=self.data_interval
        )
    
    async def generate_signal(self, symbol: str, df: pd.DataFrame = None) -> SignalResponse:
        """Generate positional trading signal"""
        
        if df is None:
            df = await self.fetch_data(symbol)
        
        # Use signal engine with positional timeframe
        signal = await build_full_signal(symbol, df=df, timeframe="positional")
        
        return signal
    
    def get_risk_multiplier(self) -> float:
        """
        Risk multiplier for stops
        Positional: 3.0 * ATR (wider stops for longer timeframe)
        """
        return 3.0
    
    def get_confidence_weights(self) -> Dict[str, float]:
        """
        Confidence weights for positional trading
        
        Positional trading emphasizes:
        - Trend (40%): Long-term trend is critical
        - Structure (25%): Market structure patterns
        - Volatility (20%): Inverse importance
        - Momentum (15%): Less weight on short-term momentum
        - Volume (0%): Less critical for long-term
        """
        return {
            "trend": 0.40,
            "structure": 0.25,
            "volatility": 0.20,
            "momentum": 0.15,
            "volume": 0.00
        }
