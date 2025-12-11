"""
Service for tracking and analyzing prediction accuracy.
Enables the system to learn from past predictions and improve over time.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PredictionAccuracyTracker:
    """Tracks and analyzes prediction accuracy for continuous learning."""
    
    @staticmethod
    def analyze_prediction_accuracy(ticker: str, days_back: int = 30) -> Dict[str, Any]:
        """
        Analyze how accurate past predictions were.
        
        Compares:
        - Predicted direction vs actual price movement
        - Predicted sentiment vs actual outcomes
        - Confidence levels vs accuracy
        
        Args:
            ticker: Stock ticker
            days_back: How far back to analyze
            
        Returns:
            Dict with accuracy metrics and insights
        """
        try:
            from app.core.database import get_db
            from app.models.analysis_cache import AnalysisCache
            
            db = next(get_db())
            
            # Get predictions from the past
            cutoff_date = datetime.now() - timedelta(days=days_back)
            past_predictions = db.query(AnalysisCache).filter(
                AnalysisCache.ticker == ticker,
                AnalysisCache.timestamp >= cutoff_date,
                AnalysisCache.prediction_direction.isnot(None)
            ).order_by(AnalysisCache.timestamp.desc()).all()
            
            if len(past_predictions) < 2:
                logger.warning(f"Not enough predictions for {ticker} to analyze accuracy")
                return None
            
            # Analyze each prediction against subsequent price movement
            accuracy_results = []
            
            for i, prediction in enumerate(past_predictions[:-1]):  # Exclude last one (no future data)
                # Get the analysis made at this time
                predicted_direction = prediction.prediction_direction
                predicted_price = prediction.price
                confidence = prediction.confidence or 0.5
                
                # Find next analysis (7 days later ideally)
                future_date = prediction.timestamp + timedelta(days=7)
                
                # Get closest analysis after 7 days
                future_analysis = db.query(AnalysisCache).filter(
                    AnalysisCache.ticker == ticker,
                    AnalysisCache.timestamp >= future_date,
                    AnalysisCache.timestamp <= future_date + timedelta(days=3)  # Within 3 days
                ).order_by(AnalysisCache.timestamp).first()
                
                if future_analysis and future_analysis.price:
                    actual_price = future_analysis.price
                    price_change_pct = ((actual_price - predicted_price) / predicted_price) * 100
                    
                    # Determine actual direction
                    if price_change_pct > 2:
                        actual_direction = "Bullish"
                    elif price_change_pct < -2:
                        actual_direction = "Bearish"
                    else:
                        actual_direction = "Neutral"
                    
                    # Check if prediction was correct
                    was_correct = (predicted_direction == actual_direction)
                    
                    accuracy_results.append({
                        "date": prediction.timestamp,
                        "predicted_direction": predicted_direction,
                        "actual_direction": actual_direction,
                        "confidence": confidence,
                        "correct": was_correct,
                        "price_change_pct": price_change_pct
                    })
            
            if not accuracy_results:
                return None
            
            # Calculate overall metrics
            total_predictions = len(accuracy_results)
            correct_predictions = sum(1 for r in accuracy_results if r["correct"])
            accuracy_rate = (correct_predictions / total_predictions) * 100
            
            # Analyze by confidence level
            high_conf_predictions = [r for r in accuracy_results if r["confidence"] >= 0.7]
            high_conf_accuracy = (sum(1 for r in high_conf_predictions if r["correct"]) / len(high_conf_predictions) * 100) if high_conf_predictions else 0
            
            # Recent vs older accuracy
            recent_predictions = accuracy_results[:5]
            recent_accuracy = (sum(1 for r in recent_predictions if r["correct"]) / len(recent_predictions) * 100) if recent_predictions else 0
            
            summary = {
                "total_predictions": total_predictions,
                "correct_predictions": correct_predictions,
                "accuracy_rate": accuracy_rate,
                "high_confidence_accuracy": high_conf_accuracy,
                "recent_accuracy": recent_accuracy,
                "predictions": accuracy_results,
                "insight": PredictionAccuracyTracker._generate_accuracy_insight(
                    accuracy_rate, high_conf_accuracy, recent_accuracy
                )
            }
            
            logger.info(f"📊 Prediction accuracy for {ticker}: {accuracy_rate:.1f}% ({correct_predictions}/{total_predictions})")
            return summary
            
        except Exception as e:
            logger.error(f"Error analyzing prediction accuracy for {ticker}: {e}")
            return None
    
    @staticmethod
    def _generate_accuracy_insight(overall: float, high_conf: float, recent: float) -> str:
        """Generate human-readable insight about prediction accuracy."""
        insights = []
        
        if overall >= 70:
            insights.append(f"High overall accuracy ({overall:.0f}%)")
        elif overall >= 50:
            insights.append(f"Moderate accuracy ({overall:.0f}%)")
        else:
            insights.append(f"Low accuracy ({overall:.0f}%) - predictions need improvement")
        
        if high_conf > overall + 15:
            insights.append("High-confidence predictions significantly more accurate")
        
        if recent > overall + 10:
            insights.append("Recent predictions improving")
        elif recent < overall - 10:
            insights.append("Recent predictions declining")
        
        return ". ".join(insights) + "."
