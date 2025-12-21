"""
Signal History Integration for RAG
Integrates signal history with existing news and temporal analysis
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from app.signal_history import get_signal_history_service, SignalRecord

logger = logging.getLogger(__name__)


def retrieve_signal_history_for_rag(
    ticker: str,
    days_back: int = 90,
    max_signals: int = 5
) -> List[Dict[str, Any]]:
    """
    Retrieve signal history in format compatible with RAG system
    
    This integrates with existing chromadb_temporal and news retrieval
    Returns signals formatted similarly to historical analyses
    
    Args:
        ticker: Stock symbol
        days_back: How far back to retrieve
        max_signals: Maximum number of signals
        
    Returns:
        List of signal summaries for RAG context
    """
    
    try:
        service = get_signal_history_service()
        
        # Get recent signals
        signals = service.get_signals(
            symbol=ticker,
            timeframe=None,  # Get both swing and positional
            days_back=days_back,
            limit=max_signals * 2  # Get extra, then filter
        )
        
        if not signals:
            logger.info(f"No signal history found for {ticker}")
            return []
        
        # Convert to RAG-compatible format (similar to historical_analyses)
        signal_summaries = []
        
        for signal in signals[:max_signals]:
            # Format as analysis-like text
            summary = f"""
Signal Generated: {signal.timestamp.strftime('%Y-%m-%d')}
Timeframe: {signal.timeframe}
Directional Bias: {signal.directional_bias} (Confidence: {signal.confidence_score:.0%})
Entry Price: ₹{signal.entry_price:.2f}
Risk Score: {signal.risk_score}/100

Price Scenarios:
- Base Case ({signal.base_case_probability:.0%}): ₹{signal.base_case_low:.0f} - ₹{signal.base_case_high:.0f}
- Bull Case ({signal.bull_case_probability:.0%}): ₹{signal.bull_case_low:.0f} - ₹{signal.bull_case_high:.0f}
- Bear Case ({signal.bear_case_probability:.0%}): ₹{signal.bear_case_low:.0f} - ₹{signal.bear_case_high:.0f}

Invalidation Level: ₹{signal.invalidation_level:.2f}
"""
            
            # Create metadata (compatible with chromadb_temporal format)
            metadata = {
                'type': 'signal_history',
                'ticker': ticker,
                'timestamp': signal.timestamp.isoformat(),
                'timestamp_unix': int(signal.timestamp.timestamp()),
                'prediction_direction': signal.directional_bias.capitalize(),
                'confidence': signal.confidence_score,
                'risk_score': signal.risk_score,
                'timeframe': signal.timeframe,
                'entry_price': signal.entry_price
            }
            
            signal_summaries.append({
                'text': summary.strip(),
                'metadata': metadata
            })
        
        logger.info(f"✅ Retrieved {len(signal_summaries)} signals for RAG context")
        return signal_summaries
        
    except Exception as e:
        logger.error(f"Error retrieving signal history for RAG: {e}")
        return []


def format_signal_history_context(signal_summaries: List[Dict[str, Any]]) -> str:
    """
    Format signal history for LLM context
    
    Args:
        signal_summaries: List from retrieve_signal_history_for_rag()
        
    Returns:
        Formatted string for LLM prompt
    """
    
    if not signal_summaries:
        return ""
    
    context_parts = ["=== SIGNAL HISTORY (Our Previous Predictions) ===\n"]
    
    for i, signal in enumerate(signal_summaries, 1):
        text = signal.get('text', '')
        metadata = signal.get('metadata', {})
        
        context_parts.append(f"\nSignal #{i} ({metadata.get('timestamp', 'unknown')[:10]}):")
        context_parts.append(text)
        context_parts.append("")
    
    return "\n".join(context_parts)
