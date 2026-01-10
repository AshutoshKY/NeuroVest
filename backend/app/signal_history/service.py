"""
Signal History Service
Stores signals in ChromaDB using a SEPARATE collection
CRITICAL: Uses 'signal_history' collection, NOT 'stock_analysis' to avoid conflicts
"""

import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import json
import uuid

from app.core.config import settings
from app.signal_engine.schemas import SignalResponse
# ScenarioSet doesn't exist in scenario_engine - removed broken import
# The scenarios are returned as a list from generate_scenarios()
from .schemas import SignalRecord, SignalOutcome, BacktestStats

logger = logging.getLogger(__name__)


class SignalHistoryService:
    """
    Service for storing and retrieving signal history
    Uses SEPARATE ChromaDB collection to avoid conflicts with existing RAG
    """
    
    def __init__(self):
        """Initialize ChromaDB with SEPARATE collection for signals"""
        
        # Use same ChromaDB client path as existing service
        self.chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_DB_PATH,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Create SEPARATE collection for signal history
        # This does NOT interfere with existing 'stock_news' or 'stock_analysis' collections
        self.signal_collection = self.chroma_client.get_or_create_collection(
            name="signal_history",
            metadata={"description": "Signal generation history for backtesting"}
        )
        
        logger.info("✅ Signal History Service initialized with separate 'signal_history' collection")
    
    def store_signal(
        self,
        signal: SignalResponse,
        scenarios: List[Dict[str, Any]],  # List of scenario dicts, not ScenarioSet
        risk_score: int
    ) -> str:
        """
        Store a signal in ChromaDB
        
        Args:
            signal: Complete signal response
            scenarios: Generated scenarios
            risk_score: Risk assessment score
            
        Returns:
            signal_id for future reference
        """
        
        signal_id = f"{signal.symbol}_{signal.timeframe}_{int(signal.timestamp.timestamp())}"
        
        try:
            # Find scenarios by type (scenarios is a List[Dict], not an object)
            base_scenario = next((s for s in scenarios if s.get("type") == "base"), scenarios[0] if scenarios else {})
            bull_scenario = next((s for s in scenarios if s.get("type") == "bull"), scenarios[1] if len(scenarios) > 1 else {})
            bear_scenario = next((s for s in scenarios if s.get("type") == "bear"), scenarios[2] if len(scenarios) > 2 else {})
            
            # Helper to parse "1234.56 - 5678.90" target_zone string into [low, high]
            def parse_target_zone(zone_str: str) -> tuple:
                try:
                    parts = zone_str.replace(",", "").split(" - ")
                    return (float(parts[0]), float(parts[1]))
                except:
                    return (0.0, 0.0)
            
            # Extract price ranges from target_zone strings
            base_range = parse_target_zone(base_scenario.get("target_zone", "0 - 0"))
            bull_range = parse_target_zone(bull_scenario.get("target_zone", "0 - 0"))
            bear_range = parse_target_zone(bear_scenario.get("target_zone", "0 - 0"))
            
            # Create signal record
            record = SignalRecord(
                signal_id=signal_id,
                symbol=signal.symbol,
                timeframe=signal.timeframe,
                timestamp=signal.timestamp,
                directional_bias=signal.signal_summary.directional_bias,
                confidence_score=signal.signal_summary.confidence_score,
                risk_score=risk_score,
                entry_price=signal.price.last_close,
                base_case_low=base_range[0],
                base_case_high=base_range[1],
                base_case_probability=base_scenario.get("probability", 0.0),
                bull_case_low=bull_range[0],
                bull_case_high=bull_range[1],
                bull_case_probability=bull_scenario.get("probability", 0.0),
                bear_case_low=bear_range[0],
                bear_case_high=bear_range[1],
                bear_case_probability=bear_scenario.get("probability", 0.0),
                invalidation_level=base_range[0] * 0.97 if base_range[0] > 0 else 0.0
            )
            
            #  Store in ChromaDB
            # Document is JSON string of the signal summary
            document = f"{signal.symbol} signal: {signal.signal_summary.directional_bias} bias with {signal.signal_summary.confidence_score:.2f} confidence. {signal.signal_summary.primary_signal}"
            
            # Metadata for filtering
            metadata = {
                "signal_id": signal_id,
                "symbol": signal.symbol,
                "timeframe": signal.timeframe,
                "timestamp_unix": int(signal.timestamp.timestamp()),
                "directional_bias": signal.signal_summary.directional_bias,
                "confidence_score": float(signal.signal_summary.confidence_score),
                "risk_score": risk_score,
                "entry_price": float(signal.price.last_close),
                # Store full record as JSON string for retrieval
                "signal_record": record.json()
            }
            
            # No embedding needed for this collection (we query by metadata, not semantic search)
            # Use a dummy embedding since ChromaDB requires it
            dummy_embedding = [0.0] * 384  # Same dimension as sentence transformer
            
            self.signal_collection.add(
                embeddings=[dummy_embedding],
                documents=[document],
                metadatas=[metadata],
                ids=[signal_id]
            )
            
            logger.info(f"✅ Stored signal: {signal_id}")
            return signal_id
            
        except Exception as e:
            logger.error(f"❌ Error storing signal {signal_id}: {e}")
            raise
    
    def get_signals(
        self,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        days_back: int = 90,
        limit: int = 100
    ) -> List[SignalRecord]:
        """
        Retrieve signals from history
        
        Args:
            symbol: Filter by symbol (optional)
            timeframe: Filter by timeframe (optional)
            days_back: How far back to search
            limit: Max number of signals
            
        Returns:
            List of SignalRecord
        """
        
        try:
            # Build filter
            cutoff_timestamp = int((datetime.utcnow() - timedelta(days=days_back)).timestamp())
            
            where_clauses = []
            
            if symbol:
                where_clauses.append({"symbol": {"$eq": symbol}})
            
            if timeframe:
                where_clauses.append({"timeframe": {"$eq": timeframe}})
            
            # Always filter by timestamp
            where_clauses.append({"timestamp_unix": {"$gte": cutoff_timestamp}})
            
            where = {"$and": where_clauses} if len(where_clauses) > 1 else where_clauses[0]
            
            # Query ChromaDB
            results = self.signal_collection.get(
                where=where,
                limit=limit,
                include=["metadatas"]
            )
            
            if not results or 'metadatas' not in results:
                return []
            
            # Parse signal records from metadata
            signals = []
            for metadata in results['metadatas']:
                try:
                    record_json = metadata.get('signal_record')
                    if record_json:
                        record = SignalRecord.parse_raw(record_json)
                        signals.append(record)
                except Exception as e:
                    logger.warning(f"Failed to parse signal record: {e}")
                    continue
            
            logger.info(f"✅ Retrieved {len(signals)} signals")
            return signals
            
        except Exception as e:
            logger.error(f"❌ Error retrieving signals: {e}")
            return []
    
    def store_outcome(self, outcome: SignalOutcome):
        """
        Store the outcome of a signal
        
        This creates a new document linked to the original signal
        """
        
        try:
            outcome_id = f"{outcome.signal_id}_outcome"
            
            document = f"Outcome for {outcome.symbol}: {outcome.outcome_quality} ({outcome.price_change_percent:.2f}%)"
            
            metadata = {
                "type": "signal_outcome",
                "signal_id": outcome.signal_id,
                "symbol": outcome.symbol,
                "timestamp_unix": int(outcome.evaluation_timestamp.timestamp()),
                "outcome_quality": outcome.outcome_quality,
                "direction_correct": outcome.direction_correct,
                "price_change_percent": float(outcome.price_change_percent),
                # Store full outcome as JSON
                "outcome_record": outcome.json()
            }
            
            dummy_embedding = [0.0] * 384
            
            self.signal_collection.add(
                embeddings=[dummy_embedding],
                documents=[document],
                metadatas=[metadata],
                ids=[outcome_id]
            )
            
            logger.info(f"✅ Stored outcome for signal: {outcome.signal_id}")
            
        except Exception as e:
            logger.error(f"❌ Error storing outcome: {e}")
            raise
    
    def get_backtest_stats(
        self,
        symbol: str,
        timeframe: str,
        days_back: int = 90
    ) -> Optional[BacktestStats]:
        """
        Calculate backtest statistics for a symbol
        
        Args:
            symbol: Stock symbol
            timeframe: swing or positional
            days_back: Period to analyze
            
        Returns:
            BacktestStats or None if insufficient data
        """
        
        try:
            # Get all signals for this symbol/timeframe
            signals = self.get_signals(symbol=symbol, timeframe=timeframe, days_back=days_back)
            
            if len(signals) < 5:
                logger.warning(f"Insufficient signals for backtest: {len(signals)} (need at least 5)")
                return None
            
            # Get all outcomes
            cutoff_timestamp = int((datetime.utcnow() - timedelta(days=days_back)).timestamp())
            
            outcome_results = self.signal_collection.get(
                where={
                    "$and": [
                        {"type": {"$eq": "signal_outcome"}},
                        {"symbol": {"$eq": symbol}},
                        {"timestamp_unix": {"$gte": cutoff_timestamp}}
                    ]
                },
                limit=1000,
                include=["metadatas"]
            )
            
            if not outcome_results or not outcome_results.get('metadatas'):
                logger.warning(f"No outcomes found for backtest")
                return None
            
            # Parse outcomes
            outcomes = []
            for metadata in outcome_results['metadatas']:
                try:
                    outcome_json = metadata.get('outcome_record')
                    if outcome_json:
                        outcome = SignalOutcome.parse_raw(outcome_json)
                        outcomes.append(outcome)
                except:
                    continue
            
            if len(outcomes) < 5:
                logger.warning(f"Insufficient outcomes: {len(outcomes)}")
                return None
            
            # Calculate statistics
            bullish_signals = sum(1 for s in signals if s.directional_bias == "bullish")
            bearish_signals = sum(1 for s in signals if s.directional_bias == "bearish")
            neutral_signals = sum(1 for s in signals if s.directional_bias == "neutral")
            
            direction_correct = sum(1 for o in outcomes if o.direction_correct)
            direction_accuracy = direction_correct / len(outcomes) if outcomes else 0.0
            
            base_hits = sum(1 for o in outcomes if o.hit_base_case)
            bull_hits = sum(1 for o in outcomes if o.hit_bull_case)
            bear_hits = sum(1 for o in outcomes if o.hit_bear_case)
            invalidations = sum(1 for o in outcomes if o.hit_invalidation)
            
            wins = sum(1 for o in outcomes if o.outcome_quality == "win")
            losses = sum(1 for o in outcomes if o.outcome_quality == "loss")
            
            win_rate = wins / len(outcomes) if outcomes else 0.0
            
            gains = [o.price_change_percent for o in outcomes if o.price_change_percent > 0]
            losses_list = [abs(o.price_change_percent) for o in outcomes if o.price_change_percent < 0]
            
            avg_gain = sum(gains) / len(gains) if gains else 0.0
            avg_loss = sum(losses_list) / len(losses_list) if losses_list else 0.0
            
            profit_factor = (sum(gains) / sum(losses_list)) if losses_list and sum(losses_list) > 0 else 0.0
            
            # Create stats
            stats = BacktestStats(
                symbol=symbol,
                timeframe=timeframe,
                total_signals=len(signals),
                bullish_signals=bullish_signals,
                bearish_signals=bearish_signals,
                neutral_signals=neutral_signals,
                direction_accuracy=round(direction_accuracy, 3),
                base_case_hit_rate=round(base_hits / len(outcomes), 3),
                bull_case_hit_rate=round(bull_hits / len(outcomes), 3),
                bear_case_hit_rate=round(bear_hits / len(outcomes), 3),
                invalidation_rate=round(invalidations / len(outcomes), 3),
                avg_gain_percent=round(avg_gain, 2),
                avg_loss_percent=round(avg_loss, 2),
                win_rate=round(win_rate, 3),
                profit_factor=round(profit_factor, 2),
                period_start=min(s.timestamp for s in signals),
                period_end=max(s.timestamp for s in signals)
            )
            
            logger.info(f"✅ Calculated backtest stats for {symbol} ({timeframe})")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error calculating backtest stats: {e}")
            import traceback
            traceback.print_exc()
            return None


# Global instance
_signal_history_service = None

def get_signal_history_service() -> SignalHistoryService:
    """Get or create the global signal history service instance"""
    global _signal_history_service
    if _signal_history_service is None:
        _signal_history_service = SignalHistoryService()
    return _signal_history_service
