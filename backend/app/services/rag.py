from openai import AzureOpenAI
from typing import Dict, Any, List, Generator, Tuple
import logging
from datetime import datetime
from app.core.config import settings
from app.services.embeddings import embedding_service
from app.services.sentiment import sentiment_service
from app.services.guardrails import guardrails_service, DISCLAIMER
from app.services.technical_analysis import TechnicalAnalysisService
from app.services.redis_cache import redis_cache

logger = logging.getLogger(__name__)


class RAGService:
    """Retrieval-Augmented Generation service for stock analysis."""
    
    def __init__(self):
        """Initialize RAG service with OpenAI client."""
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        self.model = settings.AZURE_OPENAI_DEPLOYMENT
    
    def generate_analysis(
        self,
        query: str,
        ticker: str = None,
        n_results: int = 10
    ) -> Dict[str, Any]:
        """
        Generate AI-powered analysis using RAG (synchronous version).
        For backward compatibility. Use generate_analysis_with_steps for progressive updates.
        """
        # Collect all steps
        result = None
        for step_type, data in self.generate_analysis_with_steps(query, ticker, n_results):
            if step_type == "final":
                result = data
        return result if result else {"error": "Analysis failed"}
    
    def generate_analysis_with_steps(
        self,
        query: str,
        ticker: str = None,
        n_results: int = 10,
        stock_data: Dict[str, Any] = None
    ) -> Generator[Tuple[str, Any], None, None]:
        """
        Generate AI-powered analysis with progress steps.
        
        Args:
            query: User's analysis query
            ticker: Optional ticker symbol to filter results
            n_results: Number of relevant documents to retrieve
            stock_data: Optional pre-fetched stock data
            
        Yields:
            Tuple of (step_type, data) where step_type is:
            - "step": thinking step with description
            - "final": complete analysis result
        """
        try:
            # Step 1: Check Redis cache
            yield ("step", {"description": "🔍 Checking cache...", "timestamp": datetime.now().isoformat()})
            
            cached = redis_cache.get_analysis(ticker) if ticker else None
            
            if cached:
                # Cache HIT - return immediately (instant response!)
                cached["_from_cache"] = True
                logger.info(f"⚡ Redis cache HIT for {ticker} - instant response")
                
                # Track trending even on cache hits
                if ticker:
                    redis_cache.track_trending(ticker)
                
                yield ("final", cached)
                return

            # Step 2: Retrieve documents (NEWS + HISTORICAL ANALYSIS)
            yield ("step", {"description": "📰 Fetching latest news and market data...", "timestamp": datetime.now().isoformat()})
            filter_metadata = {"ticker": ticker} if ticker else None
            
            # Retrieve current news
            search_results = embedding_service.query_similar(
                query_text=query,
                n_results=n_results,
                filter_metadata=filter_metadata
            )
            
            logger.debug("📄 Document retrieval complete", extra={
                "operation": "generate_analysis",
                "ticker": ticker or "none",
                "documents_count": len(search_results.get("documents", [])),
                "query_length": len(query)
            })
            
            # NEW: Also retrieve historical analyses for this ticker
            historical_analyses = []
            if ticker:
                try:
                    # Use the robust retrieval method
                    logger.info("�️  Retrieving historical analyses from ChromaDB", extra={
                        "operation": "retrieve_historical",
                        "ticker": ticker,
                        "requested_count": 5
                    })
                    
                    historical_data = self.retrieve_historical_analyses(ticker, top_k=5)
                    
                    if historical_data:
                        logger.info("✅ Retrieved OLD DATA from vector DB", extra={
                            "operation": "retrieve_historical",
                            "ticker": ticker,
                            "data_type": "historical_analysis",
                            "count": len(historical_data),
                            "source": "ChromaDB",
                            "status": "using_old_data"
                        })
                        
                        # Log details of historical data
                        for idx, item in enumerate(historical_data[:3], 1):
                            meta = item.get("metadata", {})
                            logger.debug(f"� Historical analysis #{idx}", extra={
                                "operation": "retrieve_historical",
                                "ticker": ticker,
                                "analysis_date": meta.get("timestamp", "unknown")[:10],
                                "prediction": meta.get("prediction_direction", "unknown"),
                                "sentiment": meta.get("sentiment_classification", "unknown"),
                                "price": meta.get("price", "N/A")
                            })
                        
                        historical_analyses = [item["text"] for item in historical_data]
                    else:
                        logger.warning("⚠️  NO OLD DATA found in vector DB", extra={
                            "operation": "retrieve_historical",
                            "ticker": ticker,
                            "data_type": "historical_analysis",
                            "source": "ChromaDB",
                            "status": "no_historical_data"
                        })
                        
                except Exception as e:
                    logger.error("❌ Error retrieving OLD DATA from vector DB", extra={
                        "operation": "retrieve_historical",
                        "ticker": ticker,
                        "source": "ChromaDB",
                        "status": "failure",
                        "error": str(e)
                    }, exc_info=True)
                    # Continue without historical_analyses
            
            if not search_results["documents"]:
                yield ("final", {
                    "analysis": f"No recent market data found{' for ' + ticker if ticker else ''}.",
                    "sentiment": {"classification": "Insufficient Data", "score": 0.0},
                    "references": [],
                    "reasoning": "Insufficient data to provide detailed reasoning.",
                    "risk_factors": [],
                    "key_insights": [],
                    "disclaimer": DISCLAIMER
                })
                return
            
            # Step 3: Analyze sentiment
            yield ("step", {"description": "🎯 Analyzing market sentiment...", "timestamp": datetime.now().isoformat()})
            sentiment_results = sentiment_service.analyze_batch_sentiment(
                search_results["documents"][:5],
                ticker=ticker
            )
            aggregate_sentiment = sentiment_service.aggregate_sentiment(sentiment_results)
            
            # Step 4: Calculate technical indicators (if ticker provided)
            technical_analysis = None
            technical_trends = None
            prediction_accuracy = None
            
            if ticker:
                yield ("step", {"description": "📊 Calculating technical indicators...", "timestamp": datetime.now().isoformat()})
                try:
                    from app.services.stock_api_service import stock_api_service
                    from app.services.technical_trend_analyzer import TechnicalTrendAnalyzer
                    from app.services.prediction_accuracy_tracker import PredictionAccuracyTracker
                    
                    # Get current technical indicators
                    historical_data = stock_api_service.get_historical_data(ticker, period="3mo")
                    if historical_data is not None and not historical_data.empty:
                        technical_analysis = TechnicalAnalysisService.get_all_indicators(
                            historical_data, ticker
                        )
                    
                    # NEW: Analyze 30-day indicator trends
                    yield ("step", {"description": "📈 Analyzing technical indicator trends...", "timestamp": datetime.now().isoformat()})
                    technical_trends = TechnicalTrendAnalyzer.analyze_indicator_trends(ticker, days=30)
                    
                    # NEW: Check prediction accuracy
                    yield ("step", {"description": "🎯 Evaluating past prediction accuracy...", "timestamp": datetime.now().isoformat()})
                    prediction_accuracy = PredictionAccuracyTracker.analyze_prediction_accuracy(ticker, days_back=30)
                    
                except Exception as e:
                    logger.error(f"Error fetching technical data: {e}")
            
            # Step 5: Generate AI analysis with historical context
            yield ("step", {"description": "🤖 Generating AI-powered analysis...", "timestamp": datetime.now().isoformat()})
            context = self._format_context(search_results)
            
            # Log what data sources are available
            data_sources = {"current_news": True}
            if technical_analysis: data_sources["technical_indicators"] = True
            if historical_analyses: data_sources["old_historical_data"] = len(historical_analyses)
            if technical_trends: data_sources["30day_trends"] = True
            if prediction_accuracy: data_sources["past_accuracy"] = True
            
            logger.info("📊 Preparing to call LLM with available data", extra={
                "operation": "generate_llm_response",
                "ticker": ticker or "none",
                "data_sources": data_sources,
                "has_old_data": bool(historical_analyses),
                "has_new_data": bool(search_results.get("documents")),
                "old_data_count": len(historical_analyses) if historical_analyses else 0,
                "new_data_count": len(search_results.get("documents", []))
            })
            
            # Only pass non-None values to avoid cluttering prompt with empty sections
            logger.debug("🤖 Calling LLM for analysis", extra={
                "operation": "generate_analysis",
                "ticker": ticker or "none",
                "has_technical": technical_analysis is not None,
                "has_historical": bool(historical_analyses),
                "has_trends": technical_trends is not None
            })
            
            analysis = self._generate_llm_response(
                query, 
                context, 
                ticker, 
                technical_analysis,
                historical_analyses if historical_analyses else None,
                technical_trends if technical_trends else None,
                prediction_accuracy if prediction_accuracy else None
            )
            
            # Log what context was available
            context_info = []
            if technical_analysis: context_info.append("technical indicators")
            if historical_analyses: context_info.append(f"{len(historical_analyses)} historical analyses")
            if technical_trends: context_info.append("30-day trends")
            if prediction_accuracy: context_info.append("prediction accuracy")
            
            if context_info:
                logger.info(f"📊 Generated analysis for {ticker} with: {', '.join(context_info)}")
            else:
                logger.info(f"📊 Generated analysis for {ticker} (initial analysis - no historical data yet)")
            
            # Extract references once
            references = self._extract_references(search_results)
            
            # Type-safe extraction helper
            def safe_extract(data, key, default=""):
                """Safely extract and convert LLM response fields to expected types."""
                value = data.get(key, default)
                # If it's a dict, try to extract 'text' or 'content' field
                if isinstance(value, dict):
                    value = value.get('text', value.get('content', value.get('summary', str(value))))
                # If it's still not a string, convert it
                if not isinstance(value, str):
                    value = str(value) if value else default
                return value
            
            def safe_extract_list(data, key, default=None):
                """Safely extract list fields from LLM response."""
                if default is None:
                    default = []
                value = data.get(key, default)
                # If it's a string, try to parse as JSON
                if isinstance(value, str):
                    try:
                        import json
                        value = json.loads(value)
                    except:
                        # If it fails, wrap in list
                        value = [value] if value else default
                # Ensure it's a list
                if not isinstance(value, list):
                    value = [str(value)] if value else default
                return value

            # Combine results with type safety
            result = {
                "analysis": safe_extract(analysis, "summary", "Analysis not available."),
                "reasoning": safe_extract(analysis, "reasoning", "No reasoning provided."),
                "prediction": safe_extract(analysis, "prediction", "No prediction available."),
                "sentiment": aggregate_sentiment,
                "references": references,
                "risk_factors": safe_extract_list(analysis, "risk_factors", []),
                "key_insights": safe_extract_list(analysis, "key_insights", []),
                "disclaimer": DISCLAIMER,
                "technical_analysis": technical_analysis,  # Include for frontend
                "cached": False
            }
            
            # Apply guardrails
            result = guardrails_service.process_analysis(result)
            
            # Cache the result if ticker is provided (pass stock_data and technical_analysis)
            if ticker:
                # Use passed stock_data or fetch if missing (but fetch synchronously if needed, or just skip)
                # Since we are in a sync generator, we rely on passed stock_data for safety
                if stock_data:
                    self._cache_analysis(ticker, result, stock_data, technical_analysis)
                else:
                    logger.warning(f"⚠️ Stock data not provided for caching {ticker}, skipping price cache")
                    # Still cache the analysis itself, just without price data
                    self._cache_analysis(ticker, result, {}, technical_analysis)
            
            yield ("final", result)
            
        except Exception as e:
            logger.error(f"Error generating analysis: {e}")
            yield ("final", {
                "analysis": "An error occurred while generating analysis. Please try again.",
                "sentiment": {"classification": "neutral", "score": 0.0},
                "references": [],
                "reasoning": "Error occurred during analysis generation.",
                "risk_factors": [],
                "key_insights": [],
                "disclaimer": DISCLAIMER
            })
            return None

    def _cache_analysis(self, ticker: str, result: Dict[str, Any], stock_data: Dict = None, technical_analysis: Dict = None):
        """Store analysis result in cache with comprehensive tracking."""
        try:
            from app.core.database import get_db
            from app.models.analysis_cache import AnalysisCache
            
            db = next(get_db())
            
            # Extract data for new fields
            sentiment = result.get('sentiment', {})
            
            # Price data
            price = stock_data.get('current_price', 0) if stock_data else result.get('current_price', 0)
            previous_close = stock_data.get('previous_close', 0) if stock_data else 0
            day_high = stock_data.get('day_high', 0) if stock_data else 0
            day_low = stock_data.get('day_low', 0) if stock_data else 0
            volume = stock_data.get('volume', 0) if stock_data else 0
            
            # Technical indicators
            tech_indicators = technical_analysis.get('indicators', {}) if technical_analysis else {}
            rsi_data = tech_indicators.get('rsi', {})
            macd_data = tech_indicators.get('macd', {})
            bb_data = tech_indicators.get('bollinger_bands', {})
            
            # Prediction analysis
            prediction_text = result.get('prediction', '')
            prediction_direction = self._extract_prediction_direction(prediction_text, sentiment)
            confidence = sentiment.get('average_confidence', sentiment.get('confidence', 0.0))
            
            # Create new cache entry with FULL tracking
            new_cache = AnalysisCache(
                ticker=ticker,
                analysis_json=result,
                sentiment_score=sentiment.get('aggregate_score', 0),
                article_count=len(result.get('references', [])),
                
                # Price tracking
                price=price,
                previous_close=previous_close,
                day_high=day_high,
                day_low=day_low,
                volume=volume,
                
                # Technical indicators
                rsi=rsi_data.get('value'),
                rsi_signal=rsi_data.get('signal'),
                macd=macd_data.get('macd'),
                macd_signal=macd_data.get('signal'),
                macd_histogram=macd_data.get('histogram'),
                macd_trend=macd_data.get('trend'),
                bb_upper=bb_data.get('upper'),
                bb_middle=bb_data.get('middle'),
                bb_lower=bb_data.get('lower'),
                bb_position=bb_data.get('position'),
                
                # Predictions
                prediction_text=prediction_text,
                prediction_direction=prediction_direction,
                confidence=confidence,
                
                # Historical context
                risk_factors_json=result.get('risk_factors', []),
                key_insights_json=result.get('key_insights', [])
            )
            
            db.add(new_cache)
            db.commit()
            logger.info(f"✅ Cached enhanced analysis for {ticker}")
            
            # Also embed the analysis for semantic search
            self._embed_analysis_result(ticker, result, stock_data, technical_analysis)
            
        except Exception as e:
            logger.error(f"Failed to cache analysis: {e}")
    
    def _extract_prediction_direction(self, prediction_text: str, sentiment: Dict) -> str:
        """Extract prediction direction from text and sentiment."""
        # Safety check: if prediction_text is a dict, convert to string or extract text
        if isinstance(prediction_text, dict):
            prediction_text = prediction_text.get('text', prediction_text.get('prediction', ''))
        
        # Ensure it's a string
        if not isinstance(prediction_text, str):
            prediction_text = str(prediction_text)
            
        prediction_lower = prediction_text.lower()
        
        # Check for explicit directional keywords
        if any(word in prediction_lower for word in ['upside', 'rally', 'gain', 'bullish', 'rise']):
            return "Bullish"
        elif any(word in prediction_lower for word in ['downside', 'decline', 'fall', 'bearish', 'drop']):
            return "Bearish"
        elif any(word in prediction_lower for word in ['consolidate', 'sideways', 'range', 'neutral']):
            return "Neutral"
        
        # Fallback to sentiment
        sentiment_class = sentiment.get('classification', 'Neutral').lower()
        if 'bullish' in sentiment_class:
            return "Bullish"
        elif 'bearish' in sentiment_class:
            return "Bearish"
        else:
            return "Neutral"
    
    def _embed_analysis_result(self, ticker: str, result: Dict[str, Any], stock_data: Dict = None, technical_analysis: Dict = None):
        """
        Create embeddings for analysis results to enable semantic search over historical analyses.
        """
        try:
            from datetime import datetime
            from app.services.embeddings import embedding_service
            
            # Extract key components
            sentiment = result.get('sentiment', {})
            prediction = result.get('prediction', '')
            insights = result.get('key_insights', [])
            risks = result.get('risk_factors', [])
            
            # Format technical indicators as text
            tech_text = ""
            if technical_analysis and 'indicators' in technical_analysis:
                indicators = technical_analysis['indicators']
                rsi_data = indicators.get('rsi', {})
                macd_data = indicators.get('macd', {})
                bb_data = indicators.get('bollinger_bands', {})
                
                tech_text = f"""
Technical Indicators:
- RSI: {rsi_data.get('value', 'N/A')} ({rsi_data.get('signal', 'N/A')})
- MACD: {macd_data.get('trend', 'N/A')} (Histogram: {macd_data.get('histogram', 'N/A')})
- Bollinger Bands: {bb_data.get('position', 'N/A')}
"""
            
            # Create comprehensive analysis document for embedding
            analysis_document = f"""
Stock Analysis: {ticker}
Date: {datetime.now().strftime('%Y-%m-%d')}

Sentiment Analysis:
- Classification: {sentiment.get('classification', 'N/A')}
- Confidence: {sentiment.get('average_confidence', sentiment.get('confidence', 0.0)):.2f}
- Score: {sentiment.get('aggregate_score', 0.0):.2f}

{tech_text}

Key Insights:
{chr(10).join(f'- {insight}' for insight in insights)}

Risk Factors:
{chr(10).join(f'- {risk}' for risk in risks)}

Future Outlook & Prediction:
{prediction}
""".strip()
            
            # Extract data for metadata
            current_price = 0.0
            day_high = 0.0
            day_low = 0.0
            volume = 0
            prev_close = 0.0
            
            if stock_data:
                current_price = stock_data.get('current_price', 0.0)
                day_high = stock_data.get('day_high', 0.0)
                day_low = stock_data.get('day_low', 0.0)
                volume = stock_data.get('volume', 0)
                prev_close = stock_data.get('previous_close', 0.0)
            
            rsi_val = 'N/A'
            macd_trend = 'N/A'
            bb_position = 'N/A'
            
            if technical_analysis and 'indicators' in technical_analysis:
                indicators = technical_analysis['indicators']
                rsi_val = indicators.get('rsi', {}).get('value', 'N/A')
                macd_trend = indicators.get('macd', {}).get('trend', 'N/A')
                bb_position = indicators.get('bollinger_bands', {}).get('position', 'N/A')

            # Serialize lists to JSON for storage
            import json
            risk_factors_json = json.dumps(risks) if risks else "[]"
            key_insights_json = json.dumps(insights) if insights else "[]"

            # Store in vector database with metadata
            metadata = {
                'type': 'historical_analysis',
                'ticker': ticker,
                'timestamp': datetime.now().isoformat(),
                'sentiment_classification': sentiment.get('classification', 'Neutral'),
                'sentiment_score': sentiment.get('aggregate_score', 0.0),
                'prediction_direction': self._extract_prediction_direction(prediction, sentiment),
                'confidence': sentiment.get('average_confidence', 0.0),
                'price': float(current_price) if current_price else 0.0,
                'day_high': float(day_high) if day_high else 0.0,
                'day_low': float(day_low) if day_low else 0.0,
                'volume': int(volume) if volume else 0,
                'previous_close': float(prev_close) if prev_close else 0.0,
                'rsi': float(rsi_val) if isinstance(rsi_val, (int, float)) else 0.0,
                'macd_trend': str(macd_trend),
                'bb_position': str(bb_position),
                'risk_factors': risk_factors_json,
                'key_insights': key_insights_json,
                'prediction_summary': prediction[:1000]  # Store first 1000 chars of prediction
            }
            
            # Add to embeddings
            embedding_service.add_documents(
                documents=[analysis_document],
                metadatas=[metadata],
                ids=[f"analysis_{ticker}_{int(datetime.now().timestamp())}"],
                collection_type="analysis"
            )
            
            logger.info(f"✅ SUCCESSFULLY EMBEDDED historical analysis for {ticker}")
            
        except Exception as e:
            logger.error(f"Failed to embed analysis result: {e}")

    
    def _format_context(self, search_results: Dict[str, Any]) -> str:
        """Format retrieved documents into context string."""
        context_parts = []
        
        for i, (doc, metadata) in enumerate(zip(
            search_results["documents"],
            search_results["metadatas"]
        ), 1):
            source = metadata.get("source", "Unknown")
            timestamp = metadata.get("timestamp", "Unknown")
            ticker = metadata.get("ticker", "")
            
            context_parts.append(
                f"[Article {i}] ({source} - {timestamp})\n"
                f"Ticker: {ticker}\n"
                f"Content: {doc}\n"
            )
        
        return "\n\n".join(context_parts)
    
    def _generate_llm_response(
        self, 
        query: str, 
        context: str, 
        ticker: str = None, 
        technical_analysis: Dict = None, 
        historical_analyses: list = None,
        technical_trends: Dict = None,
        prediction_accuracy: Dict = None
    ) -> Dict[str, Any]:
        """Generate LLM response with FULL context: news, technical, trends, and learning from past accuracy."""
        
        # Format technical analysis if available
        technical_context = ""
        if technical_analysis and 'indicators' in technical_analysis:
            indicators = technical_analysis['indicators']
            rsi_data = indicators.get('rsi', {})
            macd_data = indicators.get('macd', {})
            bb_data = indicators.get('bollinger_bands', {})
            
            technical_context = f"""

Technical Indicators Analysis (Current):
- RSI (14): {rsi_data.get('value', 'N/A')} - {rsi_data.get('signal', 'N/A')}
- MACD: {macd_data.get('trend', 'N/A')} (Histogram: {macd_data.get('histogram', 'N/A')})
- Bollinger Bands: {bb_data.get('position', 'N/A')}
"""
        
        # NEW: Format technical indicator trends
        trends_context = ""
        if technical_trends:
            rsi_trend = technical_trends.get('rsi_trend', {})
            macd_trend = technical_trends.get('macd_trend', {})
            price_trend = technical_trends.get('price_trend', {})
            sentiment_trend = technical_trends.get('sentiment_trend', {})
            
            # Helper to safely format floats
            def safe_fmt(val, decimals=1):
                if isinstance(val, (int, float)):
                    return f"{val:.{decimals}f}"
                return "N/A"

            rsi_avg = safe_fmt(rsi_trend.get('avg_30d'), 1)
            price_change = safe_fmt(price_trend.get('change_pct', 0), 1)
            sent_change = safe_fmt(sentiment_trend.get('change_from_oldest', 0), 2)
            
            trends_context = f"""
Technical Indicator Trends (30-Day Analysis):
- RSI Trend: {rsi_trend.get('direction', 'Unknown')} ({rsi_trend.get('interpretation', '')})
  Current: {rsi_trend.get('current', 'N/A')}, 30D Avg: {rsi_avg}
- MACD Trend: {macd_trend.get('direction', 'Unknown')} ({macd_trend.get('interpretation', '')})
- Price Trend: {price_trend.get('direction', 'Unknown')}, Change: {price_change}%
- Sentiment Trend: {sentiment_trend.get('direction', 'Unknown')}, Change: {sent_change}

INTERPRETATION: These trends show momentum and pattern changes over the past month.
"""
        
        # NEW: Format prediction accuracy
        accuracy_context = ""
        if prediction_accuracy:
            accuracy_rate = prediction_accuracy.get('accuracy_rate', 0)
            total_preds = prediction_accuracy.get('total_predictions', 0)
            correct_preds = prediction_accuracy.get('correct_predictions', 0)
            insight = prediction_accuracy.get('insight', '')
            
            accuracy_context = f"""

Past Prediction Accuracy (Learning from History):
- Overall Accuracy: {accuracy_rate:.1f}% ({correct_preds}/{total_preds} correct predictions)
- High-Confidence Accuracy: {prediction_accuracy.get('high_confidence_accuracy', 0):.1f}%
- Recent Performance: {prediction_accuracy.get('recent_accuracy', 0):.1f}%
- Insight: {insight}

IMPORTANT: Use this accuracy data to calibrate confidence levels and improve predictions.
If past predictions were often wrong in similar situations, adjust your outlook accordingly.
"""
        
        # Format historical analysis context
        historical_context = ""
        if historical_analyses and len(historical_analyses) > 0:
            historical_summaries = []
            for idx, item in enumerate(historical_analyses[:3], 1):  # Top 3
                # Handle both string (old format) and dict (new format)
                if isinstance(item, str):
                    snippet = item[:200]
                    historical_summaries.append(f"{idx}. {snippet}...")
                else:
                    # New format with metadata
                    meta = item.get("metadata", {})
                    date = meta.get("timestamp", "Unknown")[:10]
                    direction = meta.get("prediction_direction", "Unknown")
                    price = meta.get("price", "N/A")
                    
                    # Format risks and insights if available
                    risks = meta.get("risk_factors", [])
                    insights = meta.get("key_insights", [])
                    
                    risk_str = f"Risks: {', '.join(risks[:2])}" if risks else ""
                    insight_str = f"Insights: {', '.join(insights[:2])}" if insights else ""
                    
                    summary = f"{idx}. [{date}] {direction} at ₹{price}. {insight_str}. {risk_str}"
                    historical_summaries.append(summary)
            
            historical_context = f"""

Historical Analysis Context (Past Analyses for {ticker}):
{chr(10).join(historical_summaries)}

IMPORTANT: Compare current state with these past analyses. Identify evolving patterns.
"""

        # SELECT PROMPT BASED ON HISTORY AVAILABILITY
        if historical_analyses and len(historical_analyses) > 0:
            # SCENARIO 1: HISTORY EXISTS -> SYNTHESIS MODE
            prompt = f"""You are a financial analyst with access to comprehensive historical data. Your task is to SYNTHESIZE past and present data to determine the stock's trajectory.

DATA SOURCES:
1. HISTORICAL BASELINE (Past Analyses): Use this to understand the stock's previous state, risks, and technical setup.
2. FRESH MARKET DATA (News & Current Metrics): Use this to see what has changed right now.

CONTEXT:
{context}{technical_context}{trends_context}{accuracy_context}{historical_context}

CRITICAL INSTRUCTIONS:
1. COMPARE & CONTRAST: You MUST explicitly compare current metrics (Price, RSI, Sentiment) against the Historical Baseline.
   - "Previously, RSI was X, now it is Y, indicating..."
   - "The risk of Z mentioned in the past has now [increased/decreased] because..."
2. IDENTIFY TRAJECTORY: Do not just analyze the snapshot. Analyze the *change*. Is the stock improving or deteriorating compared to the last analysis?
3. SYNTHESIZE: Your prediction MUST be based on the combination of old and new data.
   - If the old prediction was "Bullish" and new data is good -> Reinforce confidence.
   - If the old prediction was "Bullish" but new data is bad -> Explain the pivot.

OUTPUT FORMAT (JSON):
1. summary: Detailed synthesis of how the stock has evolved from the past analysis to now.
2. reasoning: Explain the drivers of change. Reference specific past vs. current numbers.
3. risk_factors: List 3-5 risks. Highlight if old risks are still relevant or if new ones emerged.
4. key_insights: List 3-5 takeaways focusing on the *shift* in momentum or sentiment.
5. prediction: Forward-looking outlook. explicitly reference the trajectory from past to present.

Respond ONLY with valid JSON."""
        else:
            # SCENARIO 2: NO HISTORY -> BASELINE CREATION MODE
            prompt = f"""You are a financial analyst establishing a BASELINE analysis for this stock. This is the first analysis in our system.

DATA SOURCES:
1. FRESH MARKET DATA (News & Current Metrics): Use this to form your initial view.

CONTEXT:
{context}{technical_context}{trends_context}{accuracy_context}

CRITICAL INSTRUCTIONS:
1. ESTABLISH BASELINE: Since there is no past data, focus on creating a solid foundation.
   - Clearly state the current technical and fundamental setup.
   - Identify the *primary* risks that should be tracked in future.
2. ANALYZE CURRENT MOMENTUM: Use the 30-day trends (if available in context) to judge immediate direction.
3. SET EXPECTATIONS: Your prediction should set a benchmark for future comparisons.

OUTPUT FORMAT (JSON):
1. summary: Comprehensive analysis of the current market state.
2. reasoning: Explain the key drivers based on current news and metrics.
3. risk_factors: List 3-5 critical risks to watch going forward.
4. key_insights: List 3-5 major takeaways from the current data.
5. prediction: Forward-looking outlook based on current evidence.

Respond ONLY with valid JSON."""

        # Log the prompt being sent to LLM
        logger.info("📝 Prepared prompt for LLM", extra={
            "operation": "_generate_llm_response",
            "ticker": ticker or "none",
            "prompt_type": "synthesis" if historical_analyses and len(historical_analyses) > 0 else "baseline",
            "has_historical_context": bool(historical_analyses and len(historical_analyses) > 0),
            "historical_analyses_count": len(historical_analyses) if historical_analyses else 0,
            "has_technical": bool(technical_analysis),
            "has_trends": bool(technical_trends),
            "has_accuracy": bool(prediction_accuracy)
        })
        
        # Log actual prompt at DEBUG level
        logger.debug("📝 Full LLM Prompt", extra={
            "operation": "_generate_llm_response",
            "ticker": ticker or "none",
            "prompt_length": len(prompt),
            "prompt_preview": prompt[:500] + "..." if len(prompt) > 500 else prompt
        })

        try:
            logger.info("🤖 Calling LLM (Azure OpenAI)", extra={
                "operation": "llm_call",
                "ticker": ticker or "none",
                "model": self.model,
                "temperature": 0.5
            })
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial analyst with historical memory. Learn from past predictions to improve accuracy."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            logger.info("✅ LLM response received", extra={
                "operation": "llm_call",
                "ticker": ticker or "none",
                "response_keys": list(result.keys()) if isinstance(result, dict) else [],
                "has_summary": "summary" in result,
                "has_prediction": "prediction" in result,
                "status": "success"
            })
            
            # Log response preview at DEBUG level
            logger.debug("📤 LLM Response Preview", extra={
                "operation": "llm_call",
                "ticker": ticker or "none",
                "summary_preview": result.get("summary", "")[:200] if "summary" in result else "none",
                "prediction_preview": result.get("prediction", "")[:200] if "prediction" in result else "none"
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return {
                "summary": "Unable to generate analysis at this time.",
                "reasoning": "",
                "risk_factors": [],
                "key_insights": []
            }
    
    def _extract_references(self, search_results: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract references from search results."""
        references = []
        
        for metadata in search_results["metadatas"]:
            references.append({
                "source": metadata.get("source", "Unknown"),
                "timestamp": metadata.get("timestamp", "Unknown"),
                "ticker": metadata.get("ticker", ""),
                "url": metadata.get("url", "")
            })
        
        return references
    
    def retrieve_historical_analyses(self, ticker: str, top_k: int = 30):
        """
        Retrieve historical analyses for a ticker from ChromaDB.
        Returns embedded historical analysis documents.
        """
        try:
            from app.services.embeddings import embedding_service
            
            # Query ChromaDB for historical_analysis documents for this ticker
            # USE collection.get() for exact metadata matching
            # MUST use $and operator for multiple conditions in ChromaDB
            filter_metadata = {
                "$and": [
                    {"type": {"$eq": "historical_analysis"}},
                    {"ticker": {"$eq": ticker}}
                ]
            }
            
            logger.info("🔍 Retrieving history with filter", extra={
                "operation": "retrieve_historical_analyses",
                "ticker": ticker,
                "filter": str(filter_metadata),
                "limit": top_k,
                "source": "ChromaDB"
            })
            
            # Retrieve historical analyses from analysis collection
            results = embedding_service.get_documents(
                where={"$and": [{"type": "historical_analysis"}, {"ticker": ticker}]},
                limit=top_k,
                collection_type="analysis"
            )
            
            result_count = len(results['ids']) if results and results.get('ids') else 0
            
            logger.info(f"🔍 ChromaDB returned {result_count} historical documents", extra={
                "operation": "retrieve_historical_analyses",
                "ticker": ticker,
                "count": result_count,
                "source": "ChromaDB"
            })
            
            if not results or not results.get("ids"):
                logger.info(f"No historical analyses found for {ticker}")
                return []
            
            # Format results with metadata
            historical_data = []
            documents = results.get("documents", [])
            metadatas = results.get("metadatas", [])
            
            # Sort by timestamp descending (newest first)
            combined = []
            for doc, metadata in zip(documents, metadatas):
                combined.append({"text": doc, "metadata": metadata})
            
            # Sort by timestamp in metadata
            combined.sort(key=lambda x: x["metadata"].get("timestamp", ""), reverse=True)
            
            # Parse JSON fields in metadata
            import json
            for item in combined:
                meta = item["metadata"]
                
                # Parse risk factors
                if "risk_factors" in meta and isinstance(meta["risk_factors"], str):
                    try:
                        meta["risk_factors"] = json.loads(meta["risk_factors"])
                    except:
                        meta["risk_factors"] = []
                
                # Parse key insights
                if "key_insights" in meta and isinstance(meta["key_insights"], str):
                    try:
                        meta["key_insights"] = json.loads(meta["key_insights"])
                    except:
                        meta["key_insights"] = []
            
            return combined
            
        except Exception as e:
            logger.error(f"Error retrieving historical analyses: {e}")
            return []


# Global instance
rag_service = RAGService()
