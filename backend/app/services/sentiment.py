"""
Async Sentiment Analysis Service with Parallel OpenAI Calls.

Key Improvements:
- AsyncAzureOpenAI for non-blocking API calls
- Parallel batch processing with asyncio.gather()
- Expected: 16s → 4s for 5 articles (4x improvement)
- Backward compatible sync wrapper for existing code
"""

from openai import AsyncAzureOpenAI, AzureOpenAI
from typing import Dict, Any, List
import logging
import json
import asyncio
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)


class SentimentService:
    """Service for analyzing market sentiment using OpenAI with async support."""
    
    def __init__(self):
        """Initialize both async and sync OpenAI clients."""
        # Async client for parallel batch processing
        self.async_client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        
        # Sync client for backward compatibility
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        
        self.model = settings.AZURE_OPENAI_DEPLOYMENT
    
    async def analyze_sentiment_async(self, text: str, ticker: str = None) -> Dict[str, Any]:
        """
        Async sentiment analysis of financial text.
        
        Args:
            text: Text to analyze
            ticker: Optional ticker symbol for context
            
        Returns:
            Dict with sentiment_score, confidence, classification, reasoning, key_factors
        """
        try:
            ticker_context = f" regarding {ticker}" if ticker else ""
            
            # Optimized prompt (reduced tokens)
            prompt = f"""Analyze this financial news{ticker_context}:

{text}

Return JSON with:
1. sentiment_score: -1 (bearish) to 1 (bullish)
2. confidence: 0.1-1.0
3. classification: "bullish", "bearish", or "neutral"
4. reasoning: 2-3 sentences
5. key_factors: 2-4 bullet points

JSON only."""

            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Financial sentiment analyst. JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Validate and clamp values
            validated_result = {
                "sentiment_score": max(-1, min(1, float(result.get("sentiment_score", 0)))),
                "confidence": max(0, min(1, float(result.get("confidence", 0)))),
                "classification": result.get("classification", "neutral"),
                "reasoning": result.get("reasoning", ""),
                "key_factors": result.get("key_factors", [])
            }
            
            logger.debug(f"Sentiment: {validated_result['classification']} ({validated_result['sentiment_score']:.2f})")
            return validated_result
            
        except Exception as e:
            logger.error(f"Async sentiment analysis error: {e}")
            return {
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "classification": "neutral",
                "reasoning": "Error during analysis",
                "key_factors": []
            }
    
    async def analyze_batch_sentiment_async(
        self,
        texts: List[str],
        ticker: str = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze sentiment for multiple texts IN PARALLEL.
        
        This is the KEY OPTIMIZATION: Uses asyncio.gather() for concurrent API calls.
        Expected: 4x faster than sequential (16s → 4s for 5 articles).
        
        Args:
            texts: List of texts to analyze
            ticker: Optional ticker symbol
            
        Returns:
            List of sentiment results
        """
        if not texts:
            logger.warning("⚠️  [SENTIMENT_NO_TEXTS] No texts provided for sentiment analysis")
            return []
        
        batch_start = datetime.now()
        logger.info(f"🔄 [SENTIMENT_BATCH_START] Starting parallel sentiment for {len(texts)} articles", extra={
            "operation": "sentiment_batch_start",
            "article_count": len(texts),
            "ticker": ticker,
            "parallel_mode": True,
            "timestamp": batch_start.isoformat()
        })
        
        # Create tasks for all texts
        tasks = [
            self.analyze_sentiment_async(text, ticker)
            for text in texts
        ]
        
        logger.debug(f"[SENTIMENT_GATHER] Launching {len(tasks)} parallel OpenAI calls")
        
        # Execute all in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        batch_duration = (datetime.now() - batch_start).total_seconds()
        
        # Handle any exceptions
        valid_results = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Sentiment analysis failed for article {idx}: {result}")
                # Add neutral sentiment for failed analysis
                valid_results.append({
                    "sentiment_score": 0.0,
                    "confidence": 0.0,
                    "classification": "neutral",
                    "reasoning": "Analysis failed",
                    "key_factors": []
                })
            else:
                valid_results.append(result)
        
        logger.info(f"✅ Parallel sentiment analysis completed: {len(valid_results)} results", extra={
            "operation": "sentiment_batch_async",
            "article_count": len(texts),
            "successful": len([r for r in valid_results if r['confidence'] > 0]),
            "ticker": ticker
        })
        
        return valid_results
    
    # ===== SYNC METHODS FOR BACKWARD COMPATIBILITY =====
    
    def analyze_sentiment(self, text: str, ticker: str = None) -> Dict[str, Any]:
        """
        Synchronous sentiment analysis (backward compatible).
        Use analyze_sentiment_async() for better performance.
        """
        try:
            ticker_context = f" regarding {ticker}" if ticker else ""
            
            prompt = f"""Analyze this financial news{ticker_context}:

{text}

Return JSON with:
1. sentiment_score: -1 (bearish) to 1 (bullish)
2. confidence: 0.1-1.0
3. classification: "bullish", "bearish", or "neutral"
4. reasoning: 2-3 sentences
5. key_factors: 2-4 bullet points

JSON only."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Financial sentiment analyst. JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            validated_result = {
                "sentiment_score": max(-1, min(1, float(result.get("sentiment_score", 0)))),
                "confidence": max(0, min(1, float(result.get("confidence", 0)))),
                "classification": result.get("classification", "neutral"),  
                "reasoning": result.get("reasoning", ""),
                "key_factors": result.get("key_factors", [])
            }
            
            logger.info(f"Sentiment: {validated_result['classification']}")
            return validated_result
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "classification": "neutral",
                "reasoning": "Error during analysis",
                "key_factors": []
            }
    
    def analyze_batch_sentiment(self, texts: List[str], ticker: str = None) -> List[Dict[str, Any]]:
        """
        Synchronous batch sentiment analysis (backward compatible).
        
        WARNING: Sequential - slow for multiple articles.
        Consider using analyze_batch_sentiment_async() in async context.
        """
        results = []
        for text in texts:
            result = self.analyze_sentiment(text, ticker)
            results.append(result)
        return results
    
    # ===== AGGREGATION (UNCHANGED) =====
    
    def aggregate_sentiment(self, sentiment_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate multiple sentiment analyses into single score.
        
        Args:
            sentiment_results: List of sentiment analysis results
            
        Returns:
            Aggregated sentiment with weighted average
        """
        if not sentiment_results:
            return {
                "aggregate_score": 0.0,
                "aggregate_classification": "neutral",
                "classification": "neutral",
                "total_articles": 0,
                "bullish_count": 0,
                "bearish_count": 0,
                "neutral_count": 0,
                "average_confidence": 0.0
            }
        
        # Weighted average by confidence
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
        if bullish > total / 2:
            classification = "bullish"
        elif bearish > total / 2:
            classification = "bearish"
        elif neutral > total / 2:
            if weighted_score > 0.4:
                classification = "bullish"
            elif weighted_score < -0.4:
                classification = "bearish"
            else:
                classification = "neutral"
        elif weighted_score > 0.25:
            classification = "bullish"
        elif weighted_score < -0.25:
            classification = "bearish"
        else:
            classification = "neutral"
            
        logger.info(f"Aggregated: {classification} ({weighted_score:.3f}), Bull:{bullish} Bear:{bearish} Neut:{neutral}")
        
        return {
            "aggregate_score": round(weighted_score, 3),
            "aggregate_classification": classification,
            "classification": classification,
            "total_articles": len(sentiment_results),
            "bullish_count": bullish,
            "bearish_count": bearish,
            "neutral_count": neutral,
            "average_confidence": round(sum(r["confidence"] for r in sentiment_results) / len(sentiment_results), 3)
        }


# Global instance
sentiment_service = SentimentService()
