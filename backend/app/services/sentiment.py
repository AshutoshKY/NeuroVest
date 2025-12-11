from openai import AzureOpenAI
from typing import Dict, Any
import logging
import json
from app.core.config import settings

logger = logging.getLogger(__name__)


class SentimentService:
    """Service for analyzing market sentiment using OpenAI."""
    
    def __init__(self):
        """Initialize OpenAI client."""
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        self.model = settings.AZURE_OPENAI_DEPLOYMENT
    
    def analyze_sentiment(self, text: str, ticker: str = None) -> Dict[str, Any]:
        """
        Analyze sentiment of financial text.
        
        Args:
            text: Text to analyze
            ticker: Optional ticker symbol for context
            
        Returns:
            Dict with sentiment_score (-1 to 1), confidence (0 to 1),
            and classification (bullish/bearish/neutral)
        """
        try:
            ticker_context = f" regarding {ticker}" if ticker else ""
            
            prompt = f"""You are a financial sentiment analysis expert. Analyze the following market news text{ticker_context}.

Text: {text}

Provide a JSON response with:
1. sentiment_score: A number from -1 (very bearish) to 1 (very bullish), with 0 being neutral.
2. confidence: A number from 0.1 to 1.0 indicating how confident you are in this assessment based on the text's clarity and relevance. Avoid 0 unless the text is completely irrelevant.
3. classification: One of "bullish", "bearish", or "neutral"
4. reasoning: A brief explanation of your analysis (2-3 sentences)
5. key_factors: A list of 2-4 key factors that influenced your sentiment assessment

Respond ONLY with valid JSON, no other text."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a financial sentiment analysis expert. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Validate and ensure all required fields
            validated_result = {
                "sentiment_score": float(result.get("sentiment_score", 0)),
                "confidence": float(result.get("confidence", 0)),
                "classification": result.get("classification", "neutral"),
                "reasoning": result.get("reasoning", ""),
                "key_factors": result.get("key_factors", [])
            }
            
            # Clamp values to valid ranges
            validated_result["sentiment_score"] = max(-1, min(1, validated_result["sentiment_score"]))
            validated_result["confidence"] = max(0, min(1, validated_result["confidence"]))
            
            logger.info(f"Sentiment analysis completed: {validated_result['classification']}")
            return validated_result
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            # Return neutral sentiment on error
            return {
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "classification": "neutral",
                "reasoning": "Error occurred during sentiment analysis",
                "key_factors": []
            }
    
    def analyze_batch_sentiment(self, texts: list[str], ticker: str = None) -> list[Dict[str, Any]]:
        """Analyze sentiment for multiple texts."""
        results = []
        for text in texts:
            result = self.analyze_sentiment(text, ticker)
            results.append(result)
        return results
    
    def aggregate_sentiment(self, sentiment_results: list[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate multiple sentiment analyses into a single score.
        
        Args:
            sentiment_results: List of sentiment analysis results
            
        Returns:
            Aggregated sentiment with weighted average
        """
        if not sentiment_results:
            return {
                "aggregate_score": 0.0,
                "aggregate_classification": "neutral",
                "total_articles": 0,
                "bullish_count": 0,
                "bearish_count": 0,
                "neutral_count": 0
            }
        
        # Calculate weighted average based on confidence
        total_weight = sum(r["confidence"] for r in sentiment_results)
        if total_weight > 0:
            weighted_score = sum(
                r["sentiment_score"] * r["confidence"] 
                for r in sentiment_results
            ) / total_weight
        else:
            weighted_score = sum(r["sentiment_score"] for r in sentiment_results) / len(sentiment_results)
        
        # Count classifications
        bullish = sum(1 for r in sentiment_results if r["classification"] == "bullish")
        bearish = sum(1 for r in sentiment_results if r["classification"] == "bearish")
        neutral = sum(1 for r in sentiment_results if r["classification"] == "neutral")
        total = len(sentiment_results)
        
        # Determine aggregate classification
        # Priority 1: Majority Vote (if > 50% agree)
        if bullish > total / 2:
            classification = "bullish"
        elif bearish > total / 2:
            classification = "bearish"
        elif neutral > total / 2:
            # If majority is neutral, only override if score is strongly directional
            if weighted_score > 0.4:
                classification = "bullish"
            elif weighted_score < -0.4:
                classification = "bearish"
            else:
                classification = "neutral"
        # Priority 2: Weighted Score with reasonable thresholds
        elif weighted_score > 0.25:
            classification = "bullish"
        elif weighted_score < -0.25:
            classification = "bearish"
        else:
            classification = "neutral"
            
        logger.info(f"Aggregated Sentiment: {classification} (Score: {weighted_score:.3f}, Bull: {bullish}, Bear: {bearish}, Neut: {neutral})")
        
        return {
            "aggregate_score": round(weighted_score, 3),
            "aggregate_classification": classification,
            "classification": classification,  # Alias for frontend compatibility
            "total_articles": len(sentiment_results),
            "bullish_count": bullish,
            "bearish_count": bearish,
            "neutral_count": neutral,
            "average_confidence": round(sum(r["confidence"] for r in sentiment_results) / len(sentiment_results), 3)
        }


# Global instance
sentiment_service = SentimentService()
