"""
Signal History Service
Stores signals and their outcomes in ChromaDB for backtesting
Uses SEPARATE collection to avoid conflicts with existing RAG
"""

from .service import SignalHistoryService, get_signal_history_service
from .schemas import SignalRecord, SignalOutcome, BacktestStats
from .rag_integration import retrieve_signal_history_for_rag, format_signal_history_context

__all__ = [
    'SignalHistoryService',
    'get_signal_history_service',
    'SignalRecord',
    'SignalOutcome',
    'BacktestStats',
    'retrieve_signal_history_for_rag',
    'format_signal_history_context'
]

