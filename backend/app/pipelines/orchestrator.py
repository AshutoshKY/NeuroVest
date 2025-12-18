"""
Pipeline Orchestrator
Routes requests to appropriate pipeline
NEVER mixes timeframes
"""

from typing import Literal
import logging

from app.signal_engine.schemas import SignalResponse
from .swing_pipeline import SwingPipeline
from .positional_pipeline import PositionalPipeline

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    Orchestrates pipeline selection and execution
    
    Critical Rule: NEVER mix timeframes
    """
    
    def __init__(self):
        self.pipelines = {
            "swing": SwingPipeline(),
            "positional": PositionalPipeline()
        }
    
    async def execute(
        self,
        symbol: str,
        timeframe: Literal["swing", "positional"] = "swing"
    ) -> SignalResponse:
        """
        Execute appropriate pipeline
        
        Args:
            symbol: Stock symbol
            timeframe: Desired timeframe
            
        Returns:
            SignalResponse from appropriate pipeline
        """
        
        if timeframe not in self.pipelines:
            raise ValueError(f"Invalid timeframe: {timeframe}. Must be 'swing' or 'positional'")
        
        pipeline = self.pipelines[timeframe]
        logger.info(f"Executing {pipeline.name} pipeline for {symbol}")
        
        signal = await pipeline.generate_signal(symbol)
        
        logger.info(f"{pipeline.name} complete: {signal.signal_summary.directional_bias} (confidence: {signal.signal_summary.confidence_score})")
        
        return signal
    
    def get_pipeline_info(self, timeframe: str) -> dict:
        """Get metadata about a pipeline"""
        
        if timeframe not in self.pipelines:
            raise ValueError(f"Invalid timeframe: {timeframe}")
        
        pipeline = self.pipelines[timeframe]
        
        return {
            "name": pipeline.name,
            "timeframe": pipeline.timeframe,
            "typical_holding_days": pipeline.typical_holding_days,
            "data_period": pipeline.data_period,
            "data_interval": pipeline.data_interval,
            "risk_multiplier": pipeline.get_risk_multiplier(),
            "confidence_weights": pipeline.get_confidence_weights()
        }


# Global instance
pipeline_orchestrator = PipelineOrchestrator()
