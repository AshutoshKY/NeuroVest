"""
Base Pipeline
Abstract base class for all time horizon pipelines
"""

from abc import ABC, abstractmethod
from typing import Dict
import pandas as pd

from app.signal_engine.schemas import SignalResponse


class BasePipeline(ABC):
    """
    Abstract base class for analysis pipelines
    
    Each pipeline represents a different time horizon:
    - Swing: 3-10 days
    - Positional: 2-8 weeks
    - Intraday: Minutes to hours (future)
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Pipeline name"""
        pass
    
    @property
    @abstractmethod
    def timeframe(self) -> str:
        """Timeframe: 'swing' | 'positional' | 'intraday'"""
        pass
    
    @property
    @abstractmethod
    def typical_holding_days(self) -> int:
        """Expected holding period in days"""
        pass
    
    @property
    @abstractmethod
    def data_period(self) -> str:
        """Data period to fetch (e.g., '3mo', '1y')"""
        pass
    
    @property
    @abstractmethod
    def data_interval(self) -> str:
        """Data interval (e.g., '1d', '1wk')"""
        pass
    
    @abstractmethod
    async def fetch_data(self, symbol: str) -> pd.DataFrame:
        """Fetch appropriate data for this pipeline"""
        pass
    
    @abstractmethod
    async def generate_signal(self, symbol: str, df: pd.DataFrame = None) -> SignalResponse:
        """Generate signal using this pipeline's parameters"""
        pass
    
    @abstractmethod
    def get_risk_multiplier(self) -> float:
        """Get risk multiplier for this timeframe (for ATR stops)"""
        pass
    
    @abstractmethod
    def get_confidence_weights(self) -> Dict[str, float]:
        """
        Get confidence scoring weights for this timeframe
        
        Different timeframes emphasize different factors:
        - Swing: Momentum + Volume
        - Positional: Trend + Structure
        """
        pass
