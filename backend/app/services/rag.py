from openai import AzureOpenAI
from typing import Dict, Any, List, Generator, Tuple, AsyncGenerator
import logging
import asyncio  # BUG FIX: Import for await asyncio.sleep() in retry logic
import time  # For performance timing metrics
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
    
    async def generate_analysis(
        self,
        query: str,
        ticker: str = None,
        n_results: int = 10
    ) -> Dict[str, Any]:
        """
        Generate AI-powered analysis using RAG (async version).
        For backward compatibility. Use generate_analysis_with_steps for progressive updates.
        """
        # Collect all steps
        result = None
        async for step_type, data in self.generate_analysis_with_steps(query, ticker, n_results):
            if step_type == "final":
                result = data
        return result if result else {"error": "Analysis failed"}
    
    async def generate_analysis_with_steps(
        self,
        query: str,
        ticker: str = None,
        n_results: int = 10,
        stock_data: Dict[str, Any] = None
    ) -> AsyncGenerator[Tuple[str, Any], None]:
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
        analysis_start_time = time.time()
        timings = {}  # Track timing for each step
        
        try:
            # Step 1: Check Redis cache
            step_start = time.time()
            yield ("step", {"description": "🔍 Checking cache...", "timestamp": datetime.now().isoformat()})
            timings['cache_check'] = time.time() - step_start
            
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

            # Step 2: Retrieve relevant documents
            step_start = time.time()
            yield ("step", {"description": "📚 Fetching news & market data...", "timestamp": datetime.now().isoformat()})
            
            retrieval_start = time.time()
            filter_metadata = {"ticker": ticker} if ticker else None
            
            
            # Retrieve current news (indexing guaranteed complete by embeddings.py)
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
            # Step 3: Retrieve historical analyses (DYNAMIC temporal scoring)
            yield ("step", {"description": "🔍 Retrieving historical analyses with temporal decay...", "timestamp": datetime.now().isoformat()})
            historical_analyses = []
            if ticker:
                try:
                    from app.services.chromadb_temporal import retrieve_historical_analyses_dynamic
                    from app.core.config import settings
                    
                    logger.debug(f"[CHROMADB_TEMPORAL] Using dynamic retrieval for {ticker}")
                    historical_analyses_raw = retrieve_historical_analyses_dynamic(
                        embedding_service, ticker, days_back=settings.DAYS_BACK, max_analyses=settings.TARGET_ANALYSES,
                        temporal_decay_lambda=settings.TEMPORAL_DECAY_LAMBDA,
                        temporal_weight=settings.TEMPORAL_WEIGHT,
                        quality_weight=settings.QUALITY_WEIGHT,
                        max_per_week=settings.MAX_PER_WEEK
                    )
                    
                    if historical_analyses_raw:
                        # Extract metadata from the dynamic retrieval results
                        historical_analyses = [item['metadata'] for item in historical_analyses_raw]
                        logger.info(f"✅ [CHROMADB_TEMPORAL] Retrieved {len(historical_analyses)} analyses (dynamic)", extra={
                            "operation": "chromadb_temporal_retrieval",
                            "ticker": ticker,
                            "analyses_count": len(historical_analyses)
                        })
                    else:
                        logger.warning(f"⚠️  [CHROMADB_TEMPORAL_EMPTY] No historical analyses found for {ticker}")
                        
                except Exception as e:
                    logger.warning(f"⚠️  [CHROMADB_TEMPORAL_FAIL] Dynamic retrieval failed: {e}, using fallback", extra={
                        "operation": "chromadb_temporal_failure",
                        "ticker": ticker,
                        "error": str(e),
                        "error_type": type(e).__name__
                    })
                    # Fallback to old method
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
                            logger.debug(f" Historical analysis #{idx}", extra={
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
            
            
            # Step 3: Analyze sentiment (ASYNC PARALLEL - 4x faster!)
            yield ("step", {"description": "🎯 Analyzing market sentiment in parallel...", "timestamp": datetime.now().isoformat()})
            
            # Use async parallel sentiment analysis
            sentiment_results = await sentiment_service.analyze_batch_sentiment_async(
                texts=search_results.get("documents", []),
                ticker=ticker
            )
            aggregate_sentiment = sentiment_service.aggregate_sentiment(sentiment_results)
            
            # Step 4: Calculate technical indicators (if ticker provided)
            technical_analysis = None
            technical_trends = None
            prediction_accuracy = None
            
            if ticker:
                yield ("step", {"description": "📊 Fetching technical data in parallel...", "timestamp": datetime.now().isoformat()})
                try:
                    from app.services.stock_api_service import stock_api_service
                    from app.services.technical_trend_analyzer import TechnicalTrendAnalyzer
                    from app.services.prediction_accuracy_tracker import PredictionAccuracyTracker
                    # asyncio already imported at module level - no need to import again
                    
                    # NEW: PARALLEL EXECUTION - Run all 3 operations concurrently
                    logger.info(f"🚀 Starting parallel data fetching for {ticker}")
                    
                    async def get_technical_async():
                        """Get technical indicators (sync function wrapped in async)"""
                        historical_data = await asyncio.to_thread(
                            stock_api_service.get_historical_data, ticker, period="3mo"
                        )
                        if historical_data is not None and not historical_data.empty:
                            return TechnicalAnalysisService.get_all_indicators(historical_data, ticker)
                        return None
                    
                    async def get_trends_async():
                        """Get 30-day trends (sync function wrapped in async)"""
                        return await asyncio.to_thread(
                            TechnicalTrendAnalyzer.analyze_indicator_trends, ticker, days=30
                        )
                    
                    async def get_accuracy_async():
                        """Get prediction accuracy (sync function wrapped in async)"""
                        return await asyncio.to_thread(
                            PredictionAccuracyTracker.analyze_prediction_accuracy, ticker, days_back=30
                        )
                    
                    # Execute all three in parallel
                    parallel_start = datetime.now()
                    results = await asyncio.gather(
                        get_technical_async(),
                        get_trends_async(),
                        get_accuracy_async(),
                        return_exceptions=True  # Don't fail all if one fails
                    )
                    parallel_duration = (datetime.now() - parallel_start).total_seconds()
                    
                    # Unpack results
                    technical_analysis, technical_trends, prediction_accuracy = results
                    
                    # Handle exceptions
                    if isinstance(technical_analysis, Exception):
                        logger.error(f"❌ Technical analysis failed: {technical_analysis}")
                        technical_analysis = None
                    if isinstance(technical_trends, Exception):
                        logger.error(f"❌ Trends analysis failed: {technical_trends}")
                        technical_trends = None
                    if isinstance(prediction_accuracy, Exception):
                        logger.error(f"❌ Prediction accuracy failed: {prediction_accuracy}")
                        prediction_accuracy = None
                    
                    logger.info(f"✅ Parallel data fetching completed in {parallel_duration:.3f}s", extra={
                        "operation": "parallel_data_fetch",
                        "ticker": ticker,
                        "duration_seconds": parallel_duration,
                        "technical_success": technical_analysis is not None,
                        "trends_success": technical_trends is not None,
                        "accuracy_success": prediction_accuracy is not None
                    })
                    
                except Exception as e:
                    logger.error(f"Error in parallel data fetching: {e}")
            
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
            timings['data_retrieval'] = time.time() - retrieval_start
            
            llm_start = time.time()
            logger.debug("🤖 Calling LLM for analysis", extra={
                "operation": "generate_analysis",
                "ticker": ticker or "none",
                "has_technical": technical_analysis is not None,
                "has_historical": bool(historical_analyses),
                "has_trends": technical_trends is not None
            })
            
            analysis = await self._generate_llm_response(
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

            # ==================================================================
            # ENHANCED POST-PROCESSOR: Parse structured LLM response + Enrich
            # ==================================================================
            
            # Step 1: Parse nested LLM response (backward compatible)
            # Handle both old flat and new structured formats
            if isinstance(analysis, dict):
                # New structured format
                analysis_obj = analysis.get("analysis", {})
                if isinstance(analysis_obj, dict):
                    analysis_summary = analysis_obj.get("summary", "")
                    analysis_text = analysis_obj.get("full_text", "")
                    analysis_points = analysis_obj.get("key_points", [])
                else:
                    # Fallback: analysis is still a string
                    analysis_summary = ""
                    analysis_text = str(analysis_obj)
                    analysis_points = []
                
                prediction_obj = analysis.get("prediction", {})
                if isinstance(prediction_obj, dict):
                    prediction_summary = prediction_obj.get("summary", "")
                    prediction_text = prediction_obj.get("outlook", "")
                    scenarios = prediction_obj.get("scenarios", {})
                else:
                    # Fallback: prediction is still a string
                    prediction_summary = ""
                    prediction_text = str(prediction_obj)
                    scenarios = {}
            else:
                # Very old format or error
                analysis_summary = ""
                analysis_text = "Analysis not available."
                analysis_points = []
                prediction_summary = ""
                prediction_text = "No prediction available."
                scenarios = {}
            
            
            # Step 2: Build base result from LLM response
            # CRITICAL: Frontend expects 'analysis' and 'prediction' as STRINGS!
            # So we keep them flat and add NEW structured fields for future use
            
            result = {
                # OLD FORMAT (strings) - Frontend expects these!
                "analysis": analysis_text,  # ← Frontend uses this directly as string
                "prediction": prediction_text,  # ← Frontend uses this directly as string
                
                # NEW FORMAT (structured) - Includes summary, key_points, and full_text
                "analysis_structured": {
                    "summary": analysis_summary,
                    "key_points": analysis_points,
                    "full_text": analysis_text
                },
                "prediction_structured": {
                    "summary": prediction_summary,
                    "outlook": prediction_text,
                    "scenarios": scenarios
                },
                
                "reasoning": safe_extract(analysis, "reasoning", "No reasoning provided."),
                "risk_factors": safe_extract_list(analysis, "risk_factors", []),
                "key_insights": safe_extract_list(analysis, "key_insights", []),
                "confidence": analysis.get("confidence", 0.5) if isinstance(analysis, dict) else 0.5,
                "timeframe": analysis.get("timeframe", "medium-term") if isinstance(analysis, dict) else "medium-term",
                "price_target": analysis.get("price_target") if isinstance(analysis, dict) else None,
                
                # Sentiment and references (already available)
                "sentiment": aggregate_sentiment,
                "references": references,
                "disclaimer": DISCLAIMER,
                "cached": False
            }
            
            # Step 3: ENHANCED POST-PROCESSING - Enrich with all available data
            
            # 3A: Add comprehensive stock data
            if technical_analysis and ticker:
                # Extract price data from technical analysis
                current_price = technical_analysis.get('current_price', 0.0)
                
                result["stock_data"] = {
                    "ticker": ticker,
                    "current_price": current_price,
                    "day_high": technical_analysis.get('day_high', current_price),
                    "day_low": technical_analysis.get('day_low', current_price),
                    "previous_close": technical_analysis.get('previous_close', current_price),
                    "volume": technical_analysis.get('volume', 0),
                    "market_cap": technical_analysis.get('market_cap', 0),
                    "week_52_high": technical_analysis.get('week_52_high', current_price),
                    "week_52_low": technical_analysis.get('week_52_low', current_price),
                    "change": current_price - technical_analysis.get('previous_close', current_price),
                    "change_percent": ((current_price - technical_analysis.get('previous_close', current_price)) / technical_analysis.get('previous_close', current_price) * 100) if technical_analysis.get('previous_close', 0) > 0 else 0.0,
                    "currency": "INR",
                    "data_points": technical_analysis.get('data_points', 0)
                }
            
            # 3B: Add technical indicators summary
            if technical_analysis and 'indicators' in technical_analysis:
                indicators = technical_analysis['indicators']
                rsi_data = indicators.get('rsi', {})
                macd_data = indicators.get('macd', {})
                
                result["technical_summary"] = {
                    "rsi": {
                        "value": rsi_data.get('value', 0),
                        "signal": rsi_data.get('signal', 'unknown'),
                        "interpretation": "Oversold" if rsi_data.get('value', 50) < 30 else "Overbought" if rsi_data.get('value', 50) > 70 else "Neutral"
                    },
                    "macd": {
                        "value": macd_data.get('histogram', 0),
                        "signal": "bullish" if macd_data.get('histogram', 0) > 0 else "bearish",
                        "interpretation": "Positive momentum" if macd_data.get('histogram', 0) > 0 else "Negative momentum"
                    },
                    "trend": indicators.get('trend', 'unknown'),
                    "support_levels": indicators.get('bollinger_bands', {}).get('lower', 0),
                    "resistance_levels": indicators.get('bollinger_bands', {}).get('upper', 0)
                }
                
                # Also keep full technical_analysis for backward compatibility
                result["technical_analysis"] = technical_analysis
            
            # 3C: Add sentiment distribution
            if aggregate_sentiment:
                result["sentiment_detail"] = {
                    "overall_score": aggregate_sentiment.get('score', 0.0),
                    "classification": aggregate_sentiment.get('classification', 'neutral'),
                    "sentiment_count": aggregate_sentiment.get('sentiment_count', {}),
                    "trend": "improving" if aggregate_sentiment.get('score', 0) > 0.3 else "deteriorating" if aggregate_sentiment.get('score', 0) < -0.3 else "stable"
                }
            
            # 3D: Add analysis metadata
            result["metadata"] = {
                "analyzed_at": datetime.now().isoformat(),
                "ticker": ticker or "unknown",
                "data_freshness": "real-time",
                "sources_count": len(references) if references else 0,
                "historical_analyses_used": len(historical_analyses) if historical_analyses else 0,
                "has_technical_data": technical_analysis is not None,
                "has_trend_data": technical_trends is not None,
                "has_accuracy_data": prediction_accuracy is not None
            }
            
            # Step 4: Apply guardrails (validates all text fields including structured ones)
            result = guardrails_service.process_analysis(result)
            
            # Step 5: Cache the enriched result
            if ticker:
                # Use passed stock_data or fetch if missing (but fetch synchronously if needed, or just skip)
                # Since we are in a sync generator, we rely on passed stock_data for safety
                if stock_data:
                    self._cache_analysis(ticker, result, stock_data, technical_analysis)
                else:
                    logger.warning(f"⚠️ Stock data not provided for caching {ticker}, skipping price cache")
                    # Still cache the analysis itself, just without price data
                    self._cache_analysis(ticker, result, {}, technical_analysis)
            
            timings['llm_generation'] = time.time() - llm_start
            timings['total'] = time.time() - analysis_start_time
            
            # Add timing info to result
            result['_timings'] = {
                'total_seconds': round(timings['total'], 2),
                'cache_check_ms': round(timings.get('cache_check', 0) * 1000, 0),
                'data_retrieval_seconds': round(timings.get('data_retrieval', 0), 2),
                'llm_generation_seconds': round(timings.get('llm_generation', 0), 2)
            }
            
            logger.info(f"⏱️  Analysis completed in {timings['total']:.2f}s (LLM: {timings.get('llm_generation', 0):.2f}s, Data: {timings.get('data_retrieval', 0):.2f}s)")
            
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
            return  # async generators cannot return a value

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
            
            # Prediction analysis - Handle nested structure
            prediction_data = result.get('prediction', '')
            if isinstance(prediction_data, dict):
                # New nested format: extract outlook text
                prediction_text = prediction_data.get('outlook', '')
                # Also get scenarios for context
                scenarios = prediction_data.get('scenarios', {})
                # Combine into a single text for MySQL storage
                scenario_text = ""
                if scenarios:
                    scenario_parts = []
                    if scenarios.get('bull'):
                        scenario_parts.append(f"Bull: {scenarios['bull']}")
                    if scenarios.get('base'):
                        scenario_parts.append(f"Base: {scenarios['base']}")
                    if scenarios.get('bear'):
                        scenario_parts.append(f"Bear: {scenarios['bear']}")
                    scenario_text = " | ".join(scenario_parts)
                
                # Combine outlook + scenarios for full prediction text
                prediction_text = f"{prediction_text} {scenario_text}".strip() if scenario_text else prediction_text
            else:
                # Old flat format: prediction is already a string
                prediction_text = str(prediction_data) if prediction_data else ''
            
            prediction_direction = self._extract_prediction_direction(prediction_text, sentiment)
            
            # FIX: Extract confidence from LLM result, not sentiment
            # OpenAI returns confidence in result, but sentiment confidence is always 0
            confidence = result.get('confidence', 0.5) if isinstance(result, dict) else 0.5
            logger.debug(f"📊 Confidence extracted: {confidence} (from LLM result, not sentiment)")
            
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
    
    async def _generate_llm_response(
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
        
        # Format technical analysis with COMPLETE data if available
        technical_context = ""
        if technical_analysis and 'indicators' in technical_analysis:
            indicators = technical_analysis['indicators']
            rsi_data = indicators.get('rsi', {})
            macd_data = indicators.get('macd', {})
            bb_data = indicators.get('bollinger_bands', {})
            sma_data = indicators.get('sma', {})
            trend_data = indicators.get('trend', 'Unknown')
            
            # Get current price and market data
            current_price = technical_analysis.get('current_price', 'N/A')
            data_points = technical_analysis.get('data_points', 0)
            
            technical_context = f"""

TECHNICAL INDICATORS (Current State):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 PRICE ACTION:
   • Current Price: ₹{current_price}
   • Data Points Analyzed: {data_points} days
   • Overall Trend: {trend_data}

📈 RSI (Relative Strength Index):
   • Value: {rsi_data.get('value', 'N/A')} 
   • Signal: {rsi_data.get('signal', 'N/A')}
   • Interpretation: RSI below 30 = Oversold (potential buy), above 70 = Overbought (potential sell), 30-70 = Neutral

📉 MACD (Moving Average Convergence Divergence):
   • MACD Line: {macd_data.get('macd', 'N/A')}
   • Signal Line: {macd_data.get('signal', 'N/A')}
   • Histogram: {macd_data.get('histogram', 'N/A')}
   • Trend: {macd_data.get('trend', 'N/A')}
   • Interpretation: Positive histogram = Bullish momentum, Negative = Bearish momentum

📊 BOLLINGER BANDS:
   • Upper Band: ₹{bb_data.get('upper', 'N/A')}
   • Middle Band: ₹{bb_data.get('middle', 'N/A')}
   • Lower Band: ₹{bb_data.get('lower', 'N/A')}
   • Bandwidth: {bb_data.get('bandwidth', 'N/A')}%
   • Current Position: {bb_data.get('position', 'N/A')}
   • Interpretation: Price near upper band = potentially overbought, near lower band = potentially oversold

📈 MOVING AVERAGES:
   • SMA 10-day: ₹{sma_data.get('10', 'N/A')}
   • SMA 50-day: ₹{sma_data.get('50', 'N/A')}
   • Interpretation: Price above SMA = Bullish, below = Bearish

CRITICAL: Use these technical indicators to support your analysis with specific data points.
"""
        
        # Enhanced: Format technical indicator trends with COMPLETE 30-day data
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
            rsi_current = safe_fmt(rsi_trend.get('current'), 1)
            price_change = safe_fmt(price_trend.get('change_pct', 0), 2)
            sent_change = safe_fmt(sentiment_trend.get('change_from_oldest', 0), 2)
            
            trends_context = f"""

30-DAY TREND ANALYSIS (Historical Patterns):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 RSI MOMENTUM TREND:
   • Direction: {rsi_trend.get('direction', 'Unknown')}
   • Current RSI: {rsi_current}
   • 30-Day Average: {rsi_avg}
   • Interpretation: {rsi_trend.get('interpretation', 'No trend data')}
   • Insight: Shows whether stock is building bullish or bearish momentum

📈 MACD TREND:
   • Direction: {macd_trend.get('direction', 'Unknown')}
   • Interpretation: {macd_trend.get('interpretation', 'No trend data')}
   • Insight: Indicates if momentum is strengthening or weakening

💹 PRICE MOVEMENT:
   • Direction: {price_trend.get('direction', 'Unknown')}
   • 30-Day Change: {price_change}%
   • Insight: Overall price trajectory over past month

📰 SENTIMENT EVOLUTION:
   • Direction: {sentiment_trend.get('direction', 'Unknown')}
   • Sentiment Change: {sent_change}
   • Insight: How market sentiment has shifted

CRITICAL: These trends reveal momentum changes and pattern development over time.
Use this to identify if stock is improving, deteriorating, or stabilizing.
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
            
            historical_context = "\n".join(historical_summaries) if historical_summaries else "No historical data available."
        
        # OPTIMIZED PROMPTS (50% token reduction)
        # Build prompt based on whether we have historical context
        if historical_analyses and len(historical_analyses) > 0:
            # SYNTHESIS prompt (with historical data) - COMPREHENSIVE & DETAILED
            prompt = f"""You are a financial analyst for {ticker}. Synthesize past analyses with current market data.

CONTEXT (Current News & Data):
{context}

{technical_context}

{trends_context}

{accuracy_context}

HISTORICAL ANALYSES (Past Reports):
{historical_context}

⚠️ CRITICAL COMPLIANCE RULES:
- NEVER use words: buy, sell, purchase, acquire, divest, invest
- NEVER give direct advice ("you should", "we recommend")
- Use ONLY informational language: "indicators suggest", "data shows", "trends point to"
- Quote analyst views as "analyst recommends" NOT direct advice

INSTRUCTIONS:
1. Write COMPREHENSIVE, DETAILED ANALYSIS (3-4 full paragraphs covering ALL available data):
   
   Paragraph 1: Recent news, market events, and current sentiment
   - Include specific news items with data
   - Mention price movements and reactions
   - Discuss market sentiment trends
   
   Paragraph 2: Technical analysis with actual values
   - RSI with interpretation
   - MACD with trend direction  
   - Bollinger Bands position
   - 30-day and 62-day trends with percentages
   - All available technical indicators
   
   Paragraph 3: Company fundamentals and historical comparison
   - Financial position, debt, cash reserves
   - Compare current state vs historical analyses
   - Evolution of predictions and accuracy
   - Key changes since last analysis
   
   Paragraph 4: Market position and overall assessment
   - Competitive landscape
   - Sector role and importance
   - Long-term prospects
   - Current state summary

2. Write DETAILED PREDICTION/OUTLOOK (2-3 comprehensive paragraphs):
   
   Paragraph 1 - Near-Term (1-3 months):
   - Expected price movement with specific reasons
   - Key catalysts or risks
   - Technical signals and what they indicate
   - Sentiment factors
   
   Paragraph 2 - Medium-Term (3-6 months):
   - Trend expectations with data-backed reasoning
   - Fundamental drivers (earnings, deals, sector growth)
   - Growth or stability factors
   - Market conditions impact
   
   Paragraph 3 - Scenarios (detailed for each):
   Bull Case: Specific conditions, catalysts, supporting factors, price targets (₹X-₹Y)
   Base Case: Most likely scenario, supporting data, expected range (₹X-₹Y)
   Bear Case: Risk factors, negative catalysts, downside targets (₹X-₹Y)

3. List 5-7 RISK FACTORS with specific context and impact

4. List 5-7 KEY INSIGHTS with data points and analysis

JSON OUTPUT FORMAT:
{{
  "analysis": {{
    "summary": "Write a concise 2-3 sentence executive summary of the current situation and key takeaway",
    "key_points": [
      "Market Impact: [specific detail with data]",
      "Technical Analysis: [RSI, MACD, BB with values]",
      "Company Fundamentals: [financial position, cash, debt]",
      "Historical Comparison: [how current vs past]",
      "Market Position: [competitive landscape]"
    ],
    "full_text": "Write the complete 3-4 paragraph detailed analysis here as continuous text. Do NOT use markdown. Write natural flowing paragraphs with ALL data integrated. Each paragraph should be substantial (100-150 words). Include ALL technical values, news details, historical comparisons, and fundamental data. This is the MAIN comprehensive content covering everything in depth."
  }},
  "prediction": {{
    "summary": "1-2 sentence prediction overview with direction and confidence",
    "outlook": "Write the complete 2-3 paragraph prediction here as continuous text. Do NOT use markdown. Write natural flowing paragraphs covering near-term, medium-term, and all three scenarios with specific price ranges and detailed reasoning. Each paragraph should be substantial (100-150 words).",
    "scenarios": {{
      "bull": "Detailed bull case: specific catalysts, conditions, supporting factors, and price target (₹X-₹Y) with reasoning",
      "base": "Detailed base case: most likely scenario, supporting data, and expected range (₹X-₹Y) with reasoning",
      "bear": "Detailed bear case: key risks, negative catalysts, and downside targets (₹X-₹Y) with reasoning"
    }}
  }},
  "reasoning": "Detailed explanation of the logic, data analysis, and specific factors supporting the prediction",
  "confidence": 0.0-1.0,
  "risk_factors": ["Risk 1 with context", "Risk 2", "Risk 3", "Risk 4", "Risk 5", "Risk 6", "Risk 7"],
  "key_insights": ["Insight 1 with data", "Insight 2", "Insight 3", "Insight 4", "Insight 5", "Insight 6", "Insight 7"],
  "timeframe": "near-term/medium-term/long-term",
  "price_target": number or null
}}

CRITICAL: Write COMPREHENSIVE, DETAILED analysis. Use ALL available data. Write full natural paragraphs, NOT bullet points or markdown in full_text and outlook fields. Be thorough and data-rich. STRICTLY AVOID forbidden words."""
        else:
            # BASELINE prompt (no historical) - COMPREHENSIVE & DETAILED
            prompt = f"""You are a financial analyst establishing BASELINE analysis for {ticker}.

CONTEXT (News & Market Data):
{context}

{technical_context}

{trends_context}

{accuracy_context}

⚠️ CRITICAL COMPLIANCE RULES:
- NEVER use words: buy, sell, purchase, acquire, divest, invest
- NEVER give direct advice ("you should", "we recommend")
- Use ONLY informational language: "indicators suggest", "data shows", "trends point to"
- Quote analyst views as "analyst recommends" NOT direct advice

INSTRUCTIONS:
1. Write COMPREHENSIVE, DETAILED ANALYSIS (3-4 full paragraphs covering ALL available data):
   
   Paragraph 1: Recent news, market events, and current sentiment
   - Include specific news items with data
   - Mention price movements and reactions
   - Discuss market sentiment trends
   
   Paragraph 2: Technical analysis with actual values
   - RSI with interpretation
   - MACD with trend direction
   - Bollinger Bands position
   - 30-day and 62-day trends with percentages
   - All available technical indicators
   
   Paragraph 3: Company fundamentals
   - Financial position, debt, cash reserves
   - Sector role and competitive position
   - Recent deals, earnings, or events
   - Company strengths and weaknesses
   
   Paragraph 4: Market position and overall assessment
   - Competitive landscape
   - Long-term prospects
   - Current state summary

2. Write DETAILED PREDICTION/OUTLOOK (2-3 comprehensive paragraphs):
   
   Paragraph 1 - Near-Term (1-3 months):
   - Expected price movement with specific reasons
   - Key catalysts or risks
   - Technical signals and what they indicate
   - Sentiment factors
   
   Paragraph 2 - Medium-Term (3-6 months):
   - Trend expectations with data-backed reasoning
   - Fundamental drivers (earnings, deals, sector growth)
   - Growth or stability factors
   - Market conditions impact
   
   Paragraph 3 - Scenarios (detailed for each):
   Bull Case: Specific conditions, catalysts, supporting factors, price targets (₹X-₹Y)
   Base Case: Most likely scenario, supporting data, expected range (₹X-₹Y)
   Bear Case: Risk factors, negative catalysts, downside targets (₹X-₹Y)

3. List 5-7 RISK FACTORS with specific context and impact

4. List 5-7 KEY INSIGHTS with data points and analysis

JSON OUTPUT FORMAT:
{{
  "analysis": {{
    "summary": "Write a concise 2-3 sentence executive summary of the current situation and key takeaway",
    "key_points": [
      "Market Impact: [specific detail with data]",
      "Technical Analysis: [RSI, MACD, BB with values]",
      "Company Fundamentals: [financial position, cash, debt]",
      "Market Position: [competitive landscape]",
      "Current State: [key highlights]"
    ],
    "full_text": "Write the complete 3-4 paragraph detailed analysis here as continuous text. Do NOT use markdown. Write natural flowing paragraphs with ALL data integrated. Each paragraph should be substantial (100-150 words). Include ALL technical values, news details, and fundamental data. This is the MAIN comprehensive content."
  }},
  "prediction": {{
    "summary": "1-2 sentence prediction overview with direction and confidence",
    "outlook": "Write the complete 2-3 paragraph prediction here as continuous text. Do NOT use markdown. Write natural flowing paragraphs covering near-term, medium-term, and all three scenarios with specific price ranges and detailed reasoning. Each paragraph should be substantial (100-150 words).",
    "scenarios": {{
      "bull": "Detailed bull case: specific catalysts, conditions, supporting factors, and price target (₹X-₹Y) with reasoning",
      "base": "Detailed base case: most likely scenario, supporting data, and expected range (₹X-₹Y) with reasoning",
      "bear": "Detailed bear case: key risks, negative catalysts, and downside targets (₹X-₹Y) with reasoning"
    }}
  }},
  "reasoning": "Detailed explanation of the logic, data analysis, and specific factors supporting the prediction",
  "confidence": 0.0-1.0,
  "risk_factors": ["Risk 1 with context", "Risk 2", "Risk 3", "Risk 4", "Risk 5", "Risk 6", "Risk 7"],
  "key_insights": ["Insight 1 with data", "Insight 2", "Insight 3", "Insight 4", "Insight 5", "Insight 6", "Insight 7"],
  "timeframe": "near-term/medium-term/long-term",
  "price_target": number or null
}}

CRITICAL: Write COMPREHENSIVE, DETAILED analysis. Use ALL available data. Write full natural paragraphs, NOT bullet points or markdown in full_text and outlook fields. Be thorough and data-rich. STRICTLY AVOID forbidden words. This is baseline for future comparisons."""

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
        
        # NEW: Log FULL prompt at INFO level for debugging
        logger.info(f"📜 FULL OPENAI PROMPT for {ticker or 'none'}:")
        logger.info(f"\n{'='*80}\n{prompt}\n{'='*80}\n")
        
        # Also log metadata in structured format
        logger.info("Prompt metadata", extra={
            "operation": "openai_prompt_full",
            "ticker": ticker or "none",
            "prompt_length": len(prompt)
        })
        
        # Also log at debug for backward compatibility
        logger.debug("📝 Full LLM Prompt (Preview)", extra={
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
            # Call LLM with comprehensive parameters (synchronous client!)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert financial analyst for Indian stock markets with deep knowledge of technical analysis, fundamental analysis, and market sentiment."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=3000,  # Allow comprehensive, detailed responses
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            # Extract token usage
            usage = response.usage if hasattr(response, 'usage') else None
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0
            total_tokens = usage.total_tokens if usage else 0
            
            logger.info("✅ LLM response received", extra={
                "operation": "llm_call",
                "ticker": ticker or "none",
                "response_keys": list(result.keys()) if isinstance(result, dict) else [],
                "has_analysis": "analysis" in result,
                "has_prediction": "prediction" in result,
                "has_reasoning": "reasoning" in result,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "status": "success"
            })
            
            
            # NEW: Log FULL response at INFO level
            try:
                response_json_str = json.dumps(result, indent=2)
            except (TypeError, ValueError) as json_err:
                # If result contains non-serializable objects (like slice), use str()
                logger.warning(f"⚠️  Could not JSON serialize LLM response: {json_err}, using str() fallback")
                response_json_str = str(result)
            
            logger.info(f"📨 FULL OPENAI RESPONSE for {ticker or 'none'}:")
            logger.info(f"\n{'='*80}\n{response_json_str}\n{'='*80}\n")
            
            # Also log metadata in structured format
            logger.info("Response metadata", extra={
                "operation": "openai_response_full",
                "ticker": ticker or "none",
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            })
            
            # Log response preview at DEBUG level (backward compat)
            # Handle both dict and string formats for analysis/prediction
            analysis_preview = "none"
            if "analysis" in result:
                analysis_val = result["analysis"]
                if isinstance(analysis_val, dict):
                    analysis_preview = str(analysis_val.get("full_text", ""))[:200]
                else:
                    analysis_preview = str(analysis_val)[:200]
            
            prediction_preview = "none"
            if "prediction" in result:
                prediction_val = result["prediction"]
                if isinstance(prediction_val, dict):
                    prediction_preview = str(prediction_val.get("outlook", ""))[:200]
                else:
                    prediction_preview = str(prediction_val)[:200]
            
            logger.debug("📤 LLM Response Preview", extra={
                "operation": "llm_call",
                "ticker": ticker or "none",
                "analysis_preview": analysis_preview,
                "prediction_preview": prediction_preview
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}", exc_info=True)  # Add full traceback
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
