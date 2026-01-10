from openai import AzureOpenAI
from typing import Dict, Any, List, Generator, Tuple, AsyncGenerator
import logging
import asyncio  # BUG FIX: Import for await asyncio.sleep() in retry logic
import time  # For performance timing metrics
import json  # For structured request formatting in V3 prompt
from datetime import datetime
from app.core.config import settings
from app.services.embeddings import embedding_service
from app.services.sentiment import sentiment_service
from app.services.guardrails import guardrails_service, DISCLAIMER
from app.services.technical_analysis import TechnicalAnalysisService
from app.services.redis_cache import redis_cache
from app.services.smart_orchestrator import smart_orchestrator  # Smart API orchestration

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
            
            # NEW: Fetch FRESH news by searching and scraping (BEFORE querying ChromaDB)
            # TEMPORARILY DISABLED - embeddings service startup issue
            # TODO: Fix sentence-transformers offline mode, then re-enable
            if ticker:
                try:
                    from app.services.data_ingestion import data_ingestion_service
                    
                    logger.info("🔍 Searching for fresh news articles", extra={
                        "operation": "fresh_news_search",
                        "ticker": ticker
                    })
                    
                    # This will:
                    # 1. Search for news via intelligent_news_service (RSS → Scraper → DuckDuckGo)
                    # 2. Scrape article content
                    # 3. Store in ChromaDB with proper metadata
                    articles_ingested = await data_ingestion_service.ingest_for_ticker(
                        ticker=ticker,
                        company_name=None  # Could map ticker to company name if needed
                    )
                    
                    logger.info(f"✅ Fresh news ingestion complete: {articles_ingested} articles", extra={
                        "operation": "fresh_news_ingested",
                        "ticker": ticker,
                        "articles_count": articles_ingested
                    })
                    
                except Exception as news_err:
                    logger.warning(f"⚠️ Fresh news ingestion failed, will use existing data: {news_err}", extra={
                        "operation": "fresh_news_ingestion_error",
                        "ticker": ticker,
                        "error": str(news_err)
                    })
            
            # Now retrieve from ChromaDB (includes both fresh and stored news)
            search_results = embedding_service.query_similar(
                query_text=query,
                n_results=n_results,
                filter_metadata=filter_metadata
            )
            
            logger.info(f"🔍 IMMEDIATE search_results check", extra={
                "operation": "news_query_result",
                "ticker": ticker,
                "search_results_type": type(search_results).__name__,
                "has_documents_key": "documents" in search_results if isinstance(search_results, dict) else False,
                "documents_count": len(search_results.get("documents", [])) if isinstance(search_results, dict) else 0,
                "documents_type": type(search_results.get("documents")).__name__ if isinstance(search_results, dict) and "documents" in search_results else "N/A"
            })
            
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
            
            # Step 3b: Retrieve signal history (NEW - HYBRID INTEGRATION)
            signal_history = []
            
            if ticker:
                logger.info(f"🔗 HYBRID: Retrieving signal history for RAG context", extra={
                    "operation": "signal_history_start",
                    "ticker": ticker or "none"
                })
                
                try:
                    from app.signal_history.rag_integration import retrieve_signal_history_for_rag
                    
                    signal_history = retrieve_signal_history_for_rag(
                        ticker=ticker,
                        days_back=90,
                        max_signals=5
                    )
                    
                    if signal_history:
                        logger.info(f"✅ SIGNAL HISTORY: Retrieved {len(signal_history)} past signals", extra={
                            "operation": "signal_history_success",
                            "ticker": ticker,
                            "count": len(signal_history),
                            "oldest_signal": signal_history[-1].get('timestamp') if signal_history else None,
                            "newest_signal": signal_history[0].get('timestamp') if signal_history else None,
                            "signal_symbols": [s.get('symbol') for s in signal_history],
                            "signal_biases": [s.get('signal_summary', {}).get('directional_bias') for s in signal_history]
                        })
                        
                        # Log each signal for debugging
                        for i, sig in enumerate(signal_history, 1):
                            logger.debug(f"   Signal {i}: {sig.get('symbol')} @ {sig.get('timestamp')} - {sig.get('signal_summary', {}).get('directional_bias')}")
                    else:
                        logger.info(f"ℹ️ SIGNAL HISTORY: Empty for {ticker} (new stock or fresh DB)", extra={
                            "operation": "signal_history_empty",
                            "ticker": ticker,
                            "reason": "No past signals found - this is normal for new analysis"
                        })
                        
                except Exception as sig_err:
                    logger.error(f"❌ SIGNAL HISTORY ERROR: {sig_err}", extra={
                        "operation": "signal_history_exception",
                        "ticker": ticker,
                        "error_type": type(sig_err).__name__
                    })
                    import traceback
                    logger.debug(f"Signal history traceback: {traceback.format_exc()}")
            else:
                logger.warning(f"⚠️ SIGNAL HISTORY: Skipped (no ticker provided)", extra={
                    "operation": "signal_history_skipped",
                    "reason": "ticker is None"
                })
            
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
                    
                    async def get_stock_data_async():
                        """Get current stock data using Smart Orchestrator with parallel API calls"""
                        logger.info(f"[SMART] Using Smart Orchestrator for current stock data: {ticker}")
                        stock_data_result = await smart_orchestrator.get_stock_data_enhanced(ticker)
                        logger.info(f"[SMART] ✅ Got stock data from {stock_data_result.get('provider', 'unknown')}: ${stock_data_result.get('current_price', 'N/A')}")
                        return stock_data_result
                    
                    async def get_technical_async():
                        """Get technical indicators using historical data"""
                        # Note: Historical data still uses stock_api_service directly
                        # because smart orchestrator doesn't support historical data fetching yet
                        historical_data = await asyncio.to_thread(
                            smart_orchestrator.stock_api_service.get_historical_data, ticker, period="3mo"
                        )
                        logger.info(f"[HISTORICAL] Fetched {len(historical_data) if historical_data is not None and not historical_data.empty else 0} data points for {ticker}")
                        
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
                    
                    # Execute all FOUR in parallel (added stock_data)
                    parallel_start = datetime.now()
                    results = await asyncio.gather(
                        get_stock_data_async(),  # NEW: Smart orchestrator for current data
                        get_technical_async(),
                        get_trends_async(),
                        get_accuracy_async(),
                        return_exceptions=True  # Don't fail all if one fails
                    )
                    parallel_duration = (datetime.now() - parallel_start).total_seconds()
                    
                    # Unpack results
                    stock_data, technical_analysis, technical_trends, prediction_accuracy = results
                    
                    # Handle exceptions
                    if isinstance(stock_data, Exception):
                        logger.error(f"❌ Stock data fetching failed: {stock_data}")
                        stock_data = None
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
            
            # NEW: Integrate trading_utils patterns (AFTER technical data available)
            if ticker and technical_analysis and stock_data and 'dataframe' in stock_data:
                try:
                    from app.trading_utils import (
                        detect_strat_pattern,
                        detect_power_of_3,
                        calculate_smoothed_roc
                    )
                    
                    logger.info("📊 Detecting trading patterns", extra={
                        "operation": "trading_utils_patterns",
                        "ticker": ticker
                    })
                    
                    df = stock_data['dataframe']
                    
                    # Detect patterns
                    strat = detect_strat_pattern(df)
                    power_of_3 = detect_power_of_3(df)
                    smoothed_roc = calculate_smoothed_roc(df)
                    
                    # Add to technical_analysis
                    technical_analysis['strat_pattern'] = strat.dict() if strat else None
                    technical_analysis['power_of_3'] = power_of_3.dict() if power_of_3 else None
                    technical_analysis['smoothed_roc'] = smoothed_roc
                    
                    logger.info(f"✅ Trading patterns detected", extra={
                        "operation": "trading_utils_detected",
                        "ticker": ticker,
                        "strat": strat.pattern if strat else "none",
                        "power_of_3": power_of_3.phase if power_of_3 else "none"
                    })
                    
                except Exception as pattern_err:
                    logger.warning(f"⚠️ Pattern detection failed: {pattern_err}", extra={
                        "operation": "trading_utils_error",
                        "ticker": ticker
                    })
            
            # NEW: Generate Deterministic Signal (AFTER technical analysis is available)
            signal_data = None
            risk_assessment = None
            scenarios = None
            
            if ticker and technical_analysis:
                logger.info("🎯 HYBRID: Generating deterministic signal", extra={
                    "operation": "signal_generation_start",
                    "ticker": ticker
                })
                
                try:
                    from app.signal_engine.service import build_full_signal
                    
                    # Build signal from technical data
                    signal_data = await build_full_signal(ticker, timeframe="swing")
                    
                    logger.info("✅ Signal generated", extra={
                        "operation": "signal_generated",
                        "ticker": ticker,
                        "directional_bias": signal_data.signal_summary.directional_bias if signal_data else None,
                        "confidence": signal_data.signal_summary.confidence_score if signal_data else None
                    })
                    
                    # NEW: Calculate Risk Score
                    if signal_data:
                        logger.info("📊 HYBRID: Calculating risk score", extra={
                            "operation": "risk_scoring_start",
                            "ticker": ticker
                        })
                        
                        try:
                            from app.risk_scoring.scoring import calculate_risk_score
                            
                            # signal_data.market_context is ALREADY a MarketContext object!
                            # Pass it directly (don't create dict)
                            risk_assessment_result = calculate_risk_score(
                                signal=signal_data,
                                market_context=signal_data.market_context  # ✅ Correct type
                            )
                            
                            # RiskAssessment has risk_score (int) and risk_level (str)
                            risk_assessment = {
                                "score": risk_assessment_result.risk_score,  # Note: risk_score not score
                                "level": risk_assessment_result.risk_level,
                                "trend_risk": risk_assessment_result.trend_risk,
                                "volatility_risk": risk_assessment_result.volatility_risk,
                                "market_risk": risk_assessment_result.market_risk,
                                "sector_risk": risk_assessment_result.sector_risk,
                                "conflict_risk": risk_assessment_result.conflict_risk,
                                "news_risk": risk_assessment_result.news_risk,
                                "conflicts": risk_assessment_result.conflicts,
                                "notes": risk_assessment_result.notes
                            }
                            
                            logger.info(f"✅ Risk score calculated: {risk_assessment['score']}/100 ({risk_assessment['level']})", extra={
                                "operation": "risk_score_calculated",
                                "ticker": ticker,
                                "risk_score": risk_assessment['score'],
                                "risk_level": risk_assessment['level'],
                                "breakdown": {
                                    "trend": risk_assessment['trend_risk'],
                                    "volatility": risk_assessment['volatility_risk'],
                                    "market": risk_assessment['market_risk'],
                                    "sector": risk_assessment['sector_risk'],
                                    "conflicts": risk_assessment['conflict_risk'],
                                    "news": risk_assessment['news_risk']
                                }
                            })
                            
                        except Exception as risk_err:
                            logger.error(f"Risk scoring failed: {risk_err}", extra={
                                "operation": "risk_scoring_error",
                                "ticker": ticker,
                                "error": str(risk_err)
                            })
                            import traceback
                            logger.error(f"Risk scoring traceback: {traceback.format_exc()}")
                            risk_assessment = None
                    
                    
                    # MARKET-GRADE: Generate Scenarios DETERMINISTICALLY (before LLM)
                    # This is SOURCE OF TRUTH. LLM MUST NOT generate scenarios.
                    scenarios = None
                    if signal_data and risk_assessment_result:
                        logger.info("🎯 MARKET-GRADE: Generating deterministic scenarios", extra={
                            "operation": "scenario_generation_start",
                            "ticker": ticker,
                            "trend_bias": signal_data.get("signal_summary", {}).get("directional_bias"),
                            "confidence": signal_data.get("signal_summary", {}).get("confidence_score")
                        })
                        try:
                            from app.scenario_engine import generate_scenarios
                            
                            # Prepare inputs for scenario generation
                            market_state = {
                                "trend_bias": signal_data.get("signal_summary", {}).get("directional_bias", "neutral"),
                                "confidence": signal_data.get("signal_summary", {}).get("confidence_score", 0.5),
                                "momentum": signal_data.get("signal_summary", {}).get("momentum", "neutral"),
                                "volatility": "compression"  # Can extract from technical if available
                            }
                            
                            price_zones = {
                                "support": signal_data.get("price_levels", {}).get("support", {"lower": 0, "upper": 0}),
                                "value_area": signal_data.get("price_levels", {}).get("value", {"lower": 0, "upper": 0}),
                                "resistance": signal_data.get("price_levels", {}).get("resistance", {"lower": 0, "upper": 0}),
                                "current_price": signal_data.get("signal_summary", {}).get("current_price", 0)
                            }
                            
                            signal_conflicts = signal_data.get("signal_conflicts", [])
                            risk_score = risk_assessment_result.get("score", 0.5)
                            
                            # GENERATE SCENARIOS
                            scenarios = generate_scenarios(
                                market_state=market_state,
                                price_zones=price_zones,
                                signal_conflicts=signal_conflicts,
                                risk_score=risk_score
                            )
                            
                            # Validate probabilities sum to 1.0
                            total_prob = sum(s.get("probability", 0) for s in scenarios)
                            logger.info(f"✅ Generated {len(scenarios)} scenarios, prob_sum={total_prob:.3f}", extra={
                                "operation": "scenario_generation_complete",
                                "ticker": ticker,
                                "scenario_count": len(scenarios),
                                "probabilities": [s.get("probability") for s in scenarios],
                                "prob_sum_valid": abs(total_prob - 1.0) < 0.001,
                                "scenario_ids": [s.get("id") for s in scenarios]
                            })
                            
                            # BACKTESTING: Store scenario snapshot for outcome tracking
                            try:
                                from app.backtesting import store_snapshot
                                
                                snapshot_id = store_snapshot(
                                    ticker=ticker,
                                    market_state=market_state,
                                    price_zones=price_zones,
                                    scenarios=scenarios,
                                    signal_conflicts=signal_conflicts,
                                    risk_score=risk_score,
                                    current_price=market_state.get("current_price", 0)
                                )
                                
                                logger.info(f"📸 Stored backtesting snapshot: {snapshot_id}", extra={
                                    "operation": "snapshot_stored",
                                    "snapshot_id": snapshot_id,
                                    "ticker": ticker
                                })
                            except Exception as snapshot_err:
                                # Don't block on snapshot errors
                                logger.warning(f"Failed to store snapshot: {snapshot_err}", extra={
                                    "operation": "snapshot_storage_failed",
                                    "ticker": ticker,
                                    "error": str(snapshot_err)
                                })

                        except Exception as scenario_err:
                            logger.error(f"Scenario generation failed: {str(scenario_err)}", extra={
                                "operation": "scenario_generation_error",
                                "ticker": ticker,
                                "error": str(scenario_err),
                                "traceback": traceback.format_exc()
                            })
                            scenarios = None
                    else:
                        logger.warning("Skipping scenario generation: missing signal_data or risk_assessment", extra={
                            "operation": "scenario_generation_skipped",
                            "ticker": ticker,
                            "has_signal_data": bool(signal_data),
                            "has_risk_assessment": bool(risk_assessment_result)
                        })

                    #         logger.error(f"Scenario generation failed: {scenario_err}")
                    
                except Exception as signal_err:
                    logger.error(f"Signal generation failed: {signal_err}", extra={
                        "operation": "signal_generation_error",
                        "ticker": ticker,
                        "error": str(signal_err)
                    })
                    signal_data = None
            
            # Step 5: Generate AI analysis with historical context
            yield ("step", {"description": "🤖 Generating AI-powered analysis...", "timestamp": datetime.now().isoformat()})
            context = self._format_context(search_results)
            
            # NEW: Verify news context is populated
            logger.info(f"📰 News context verification", extra={
                "operation": "news_context_verification",
                "ticker": ticker,
                "context_length": len(context),
                "has_content": len(context) > 100,
                "documents_in_results": len(search_results.get("documents", []))
            })
            
            if len(context) < 100:
                logger.warning(f"⚠️ News context appears empty or very short!", extra={
                    "operation": "news_context_warning",
                    "ticker": ticker,
                    "context_length": len(context)
                })
            
            # Log what data sources are available
            data_sources = {"current_news": True}
            if technical_analysis: data_sources["technical_indicators"] = True
            if historical_analyses: data_sources["old_historical_data"] = len(historical_analyses)
            if signal_history: data_sources["signal_history"] = len(signal_history)
            if technical_trends: data_sources["30day_trends"] = True
            if prediction_accuracy: data_sources["past_accuracy"] = True
            
            logger.info("📊 Preparing to call LLM with available data", extra={
                "operation": "generate_llm_response",
                "ticker": ticker or "none",
                "data_sources": data_sources,
                "has_old_data": bool(historical_analyses),
                "has_signal_history": bool(signal_history),
                "has_new_data": bool(search_results.get("documents")),
                "old_data_count": len(historical_analyses) if historical_analyses else 0,
                "signal_history_count": len(signal_history) if signal_history else 0,
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
                "has_trends": technical_trends is not None,
                "has_signal_data": signal_data is not None,
                "has_risk_assessment": risk_assessment is not None,
                "has_scenarios": scenarios is not None
            })
            
            analysis = await self._generate_llm_response(
                query,  # FIXED: Use query notquery_text
                context,
                ticker=ticker,
                technical_analysis=technical_analysis,
                historical_analyses=historical_analyses,
                signal_history=signal_history if signal_history else None,
                technical_trends=technical_trends,
                prediction_accuracy=prediction_accuracy,
                signal_data=signal_data,  # NEW: Pass signal data
                risk_assessment=risk_assessment,  # NEW
                scenarios=scenarios,  # NEW
                stock_data=stock_data  # NEW: Pass fresh stock data from smart orchestrator
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
            
            # Step 1: Parse LLM response - PRESERVE existing analysis_structured if present
            # _generate_llm_response already builds analysis_structured for V3 format!
            
            # Check if analysis_structured already exists (built by _generate_llm_response)
            existing_analysis_structured = None
            existing_prediction_structured = None
            
            if isinstance(analysis, dict):
                existing_analysis_structured = analysis.get("analysis_structured")
                existing_prediction_structured = analysis.get("prediction_structured")
            
            if existing_analysis_structured and isinstance(existing_analysis_structured, dict):
                # V3 FORMAT: Use pre-built structured data from _generate_llm_response
                # Use safe_extract helpers to ensures types (especially for key_points which can come as dict)
                analysis_summary = safe_extract(existing_analysis_structured, "summary", "")
                analysis_text = safe_extract(existing_analysis_structured, "full_text", analysis.get("analysis", ""))
                analysis_points = safe_extract_list(existing_analysis_structured, "key_points", [])
                
                if existing_prediction_structured and isinstance(existing_prediction_structured, dict):
                    prediction_summary = safe_extract(existing_prediction_structured, "summary", "")
                    prediction_text = safe_extract(existing_prediction_structured, "outlook", analysis.get("prediction", ""))
                    scenarios = existing_prediction_structured.get("scenarios", [])
                    # Note: No separate key_points for prediction in this path yet, but logic is consistent
                else:
                    prediction_summary = ""
                    prediction_text = str(analysis.get("prediction", ""))
                    scenarios = {}
                    
                logger.info(f"✅ Using pre-built analysis_structured from LLM response", extra={
                    "operation": "use_existing_structured",
                    "ticker": ticker,
                    "summary_length": len(analysis_summary),
                    "key_points_is_list": isinstance(analysis_points, list),
                    "key_points_count": len(analysis_points),
                    "has_prediction_structured": bool(existing_prediction_structured)
                })
            elif isinstance(analysis, dict):
                # LEGACY FORMAT: Try to parse nested structure (backward compatible)
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
                "cached": False,
                
                # V3 MARKET-GRADE FIELDS (NEW) - Preserve structured signals
                "market_state": analysis.get("market_state", {}) if isinstance(analysis, dict) else {},
                "price_zones": analysis.get("price_zones", {}) if isinstance(analysis, dict) else {},
                "scenarios": analysis.get("scenarios", []) if isinstance(analysis, dict) else [],
                "signal_conflicts": analysis.get("signal_conflicts", []) if isinstance(analysis, dict) else []
            }
            
            logger.info(f"📦 Built result dict with V3 fields for {ticker}", extra={
                "operation": "result_build_complete",
                "ticker": ticker,
                "has_market_state": bool(result.get("market_state")),
                "has_price_zones": bool(result.get("price_zones")),
                "scenario_count": len(result.get("scenarios", [])),
                "has_signal_conflicts": bool(result.get("signal_conflicts"))
            })
            
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
        signal_history: list = None,
        technical_trends: Dict = None,
        prediction_accuracy: Dict = None,
        signal_data = None,  # NEW
        risk_assessment: Dict = None,  # NEW
        scenarios = None,  # NEW
        stock_data: Dict = None  # NEW: Fresh stock data from smart orchestrator
    ) -> Dict[str, Any]:
        """Generate LLM response with FULL context: news, technical, trends, signal history, deterministic signals, risk scores, and scenarios."""
        
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
        
        # Format signal history (NEW - Our deterministic predictions)
        signal_context = ""
        if signal_history and len(signal_history) > 0:
            from app.signal_history.rag_integration import format_signal_history_context
            signal_context = format_signal_history_context(signal_history)
        
        # Format CURRENT deterministic signal (NEW - Real-time signal)
        current_signal_context = ""
        if signal_data:
            try:
                signal_summary = signal_data.signal_summary
                trend_data = signal_data.trend
                
                current_signal_context = f"""

DETERMINISTIC SIGNAL (Current):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 SIGNAL SUMMARY:
   • Directional Bias: {signal_summary.directional_bias}
   • Confidence: {signal_summary.confidence_score:.2f}
   • Conviction: {signal_summary.conviction}
   • Primary Signal: {signal_summary.primary_signal}
   • Timeframe: {signal_data.timeframe}

📈 TREND ANALYSIS:
   • Trend State: {trend_data.trend_state}
   • Trend Strength: {trend_data.strength}
   • EMA Alignment: {trend_data.ema_alignment_score:.2f}
   • EMA 20: ₹{trend_data.ema_20:.2f}
   • EMA 50: ₹{trend_data.ema_50:.2f}
   • EMA 200: ₹{trend_data.ema_200:.2f}

📊 MOMENTUM & VOLUME:
   • RSI: {signal_data.momentum.rsi_14:.1f} ({signal_data.momentum.rsi_regime})
   • MACD: {signal_data.momentum.macd.state}
   • Volume Confirmation: {"✅ Yes" if signal_data.volume.volume_confirmation else "❌ No"}
   • Volume vs Avg: {signal_data.volume.today_vs_20d_avg:.2f}x

CRITICAL: This signal is deterministic and CANNOT be overridden by narrative.
"""
            except Exception as e:
                logger.error(f"Failed to format signal context: {e}")
                import traceback
                logger.error(f"Signal context traceback: {traceback.format_exc()}")
                current_signal_context = ""
        
        # Format risk assessment (NEW)
        risk_context = ""
        if risk_assessment:
            risk_context = f"""

RISK ASSESSMENT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 OVERALL RISK:
   • Total Risk Score: {risk_assessment['score']}/100
   • Risk Level: {risk_assessment['level'].upper()}
   • Assessment: {risk_assessment['notes']}

📋 RISK BREAKDOWN:
   • Trend Risk: {risk_assessment['trend_risk']}/25 points
   • Volatility Risk: {risk_assessment['volatility_risk']}/20 points
   • Market Risk: {risk_assessment['market_risk']}/15 points
   • Sector Risk: {risk_assessment['sector_risk']}/15 points
   • Signal Conflicts: {risk_assessment['conflict_risk']}/15 points
   • News Risk: {risk_assessment['news_risk']}/10 points
"""
            
            # Add conflicts separately to avoid f-string backslash issue
            if risk_assessment['conflicts']:
                conflicts_text = "\n".join(f"   • {c}" for c in risk_assessment['conflicts'])
                risk_context += f"\n⚠️ CONFLICTS DETECTED:\n{conflicts_text}\n"
            else:
                risk_context += "\n✅ No signal conflicts detected\n"
            
            risk_context += """
INTERPRETATION:
   • 0-30: Low Risk - Favorable trading environment
   • 31-60: Moderate Risk - Exercise caution, manage position size
   • 61-100: High Risk - Consider avoiding or reducing exposure
"""
        
        
        # Format scenarios (MARKET-GRADE: Pre-generated deterministic scenarios)
        scenarios_context = ""
        if scenarios and isinstance(scenarios, list):
            # NEW: Handle LIST format from scenario_engine.generate_scenarios()
            scenarios_context = """

🎯 PRE-GENERATED SCENARIOS (DETERMINISTIC - DO NOT MODIFY):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 CRITICAL: These scenarios were generated BEFORE you receive them using deterministic math.
YOU MUST NOT generate new scenarios, modify probabilities, or change triggers/invalidation.
YOUR JOB: COPY these scenarios exactly into your output and EXPLAIN why they have these probabilities.

"""
            total_prob_check = sum(s.get('probability', 0) for s in scenarios)
            scenarios_context += f"Total Probability: {total_prob_check:.3f} (Validated: {abs(total_prob_check - 1.0) < 0.001})\n\n"
            
            for i, scenario in enumerate(scenarios, 1):
                scenarios_context += f"""Scenario {i} - {scenario.get('type', 'unknown').upper()}:
   • ID: {scenario.get('id', 'N/A')} (Versioned for tracking)
   • Description: {scenario.get('description', 'N/A')}
   • Probability: {scenario.get('probability', 0):.3f} ({scenario.get('probability', 0)*100:.1f}%)
   • Trigger Conditions: {scenario.get('trigger_conditions', 'N/A')}
   • Invalidation Level: {scenario.get('invalidation_level', 'N/A')}
   • Target Zone: {scenario.get('target_zone', 'Calculated from price_zones')}
   • Derived From: {scenario.get('derived_from', {}).get('trend_bias', 'N/A')} (confidence: {scenario.get('derived_from', {}).get('confidence', 0):.2f})

"""
            scenarios_context += """
🚨 MANDATORY: You MUST include all these scenarios in your output exactly as provided.
✅ COPY the scenario data
✅ EXPLAIN why these probabilities make sense given market_state
✅ REFERENCE these scenarios in your narrative
❌ DO NOT generate new scenarios
❌ DO NOT modify probabilities
❌ DO NOT change triggers or invalidation levels

"""
        elif scenarios and hasattr(scenarios, 'scenarios'):
            # OLD: Handle object format for backward compatibility
            scenarios_context = """

PRICE SCENARIOS (Probability-Weighted):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            for scenario in scenarios.scenarios:
                scenarios_context += f"""{scenario.name}:
   • Probability: {scenario.probability*100:.0f}%
   • Price Range: ₹{scenario.price_range[0]:.2f} - ₹{scenario.price_range[1]:.2f}
   • Drivers: {', '.join(scenario.drivers)}
   • Invalidation: {scenario.invalidation}
"""
            scenarios_context += "\nCRITICAL: These scenarios are based on ATR and technical data. Use them as framework."
        
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

{signal_context}

{current_signal_context}

{risk_context}

{scenarios_context}

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

{current_signal_context}

{risk_context}

{scenarios_context}

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
            # NEW: Build structured request for probabilistic prompt V3
            structured_request = {
                "asset": {
                    "symbol": ticker,
                    "exchange": "NSE",
                    "currency": "INR",
                    # FIXED: Use fresh stock_data from smart orchestrator, not old technical_analysis
                    "current_price": stock_data.get('current_price') if stock_data else (technical_analysis.get('current_price') if technical_analysis else None)
                },
                "current_market_data": {
                    # NEW: Add fresh market data from smart orchestrator
                    "price": stock_data.get('current_price') if stock_data else None,
                    "previous_close": stock_data.get('previous_close') if stock_data else None,
                    "day_high": stock_data.get('day_high') if stock_data else None,
                    "day_low": stock_data.get('day_low') if stock_data else None,
                    "volume": stock_data.get('volume') if stock_data else None,
                    "provider": stock_data.get('provider') if stock_data else None,
                    "timestamp": stock_data.get('timestamp') if stock_data else None
                },
                "technical_indicators": {
                    "rsi": {
                        "value": technical_analysis.get('rsi') if technical_analysis else None,
                        "trend": "neutral"
                    },
                    "macd": technical_analysis.get('macd', {}) if technical_analysis else {},
                    "bollinger_bands": technical_analysis.get('bollinger_bands', {}) if technical_analysis else {},
                    "trend": signal_data.trend.dict() if signal_data else {}
                },
                "historical_context": {
                    "vector_lookback_days": 45,
                    "retrieved_patterns": []
                },
                "sentiment": {
                    "current": "neutral",
                    "trend": "flat", 
                    "score": 0.0
                },
                "deterministic_signal": {
                    "directional_bias": signal_data.signal_summary.directional_bias if signal_data else "neutral",
                    "confidence_score": signal_data.signal_summary.confidence_score if signal_data else 0.5,
                    "conviction": signal_data.signal_summary.conviction if signal_data else "low"
                } if signal_data else {},
                "risk_assessment": risk_assessment if risk_assessment else {}
            }
            
            # Format structured request as context
            scenario_section = f"SCENARIOS:\n{scenario_context}" if scenarios else ""
            structured_context = f"""
STRUCTURED MARKET DATA:
{json.dumps(structured_request, indent=2)}

DETERMINISTIC ANALYSIS:
{signal_context}

RISK ASSESSMENT:
{risk_context}

{scenario_section}
"""
            
            # Use V3 probabilistic prompt
            from app.llm_integration.prompts import SYSTEM_PROMPT_V3_PROBABILISTIC
            system_prompt = SYSTEM_PROMPT_V3_PROBABILISTIC
            
            prompt_parts = [
                structured_context,
                f"\nNEWS CONTEXT:\n{context}",
                f"\nUSER QUERY: {query}"
            ]
            
            # Combine prompt parts into a single user message
            user_message_content = "\n".join(prompt_parts)

            logger.info("🔐 HYBRID INTEGRATION: Using SYSTEM_PROMPT_V3_PROBABILISTIC (probabilistic prompt)", extra={
                "operation": "hybrid_llm_call",
                "ticker": ticker or "none",
                "model": self.model,
                "temperature": 0.0,
                "system_prompt_type": "SYSTEM_PROMPT_V3_PROBABILISTIC",
                "system_prompt_length": len(system_prompt),
                "user_prompt_length": len(user_message_content),
                "has_technical": bool(technical_analysis),
                "has_historical": bool(historical_analyses),
                "has_signal_history": bool(signal_history),
                "has_trends": bool(technical_trends)
            })
            
            # Call LLM with V3 probabilistic prompt
            import time
            import uuid
            llm_call_start = time.time()
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},  # V3 probabilistic prompt
                    {"role": "user", "content": user_message_content}  # Structured data + news + query
                ],
                temperature=0.0,  # Deterministic for V3
                max_tokens=3000,
                response_format={"type": "json_object"}
            )
            
            llm_call_end = time.time()
            llm_latency_ms = (llm_call_end - llm_call_start) * 1000
            
            # Track AI metrics (Phase 5)
            try:
                from app.services.ai_metrics import AIMetricsService, AIUsageType, AIProvider
                
                usage = response.usage
                if usage:
                    AIMetricsService.record_request(
                        request_id=str(uuid.uuid4())[:8],
                        usage_type=AIUsageType.RAG_ANALYSIS,
                        provider=AIProvider.AZURE_OPENAI,
                        model=self.model,
                        prompt_tokens=usage.prompt_tokens,
                        completion_tokens=usage.completion_tokens,
                        latency_ms=llm_latency_ms,
                        ticker=ticker,
                        success=True
                    )
            except Exception as metrics_err:
                logger.warning(f"[AI_METRICS] Failed to record: {metrics_err}")
            
            # Module-level json import at line 6 is used
            result = json.loads(response.choices[0].message.content)
            
            # VALIDATE SIGNAL (Market-Grade Quality Control)
            try:
                from app.validators import validate_signal
                
                logger.info(f"🔍 Starting signal validation for {ticker}", extra={
                    "operation": "signal_validation_start",
                    "ticker": ticker,
                    "has_market_state": "market_state" in result,
                    "has_price_zones": "price_zones" in result,
                    "has_scenarios": "scenarios" in result,
                    "has_narrative": "narrative" in result,
                    "scenario_count": len(result.get("scenarios", []))
                })
                
                validation_result = validate_signal(result)
                
                if not validation_result.valid:
                    # Log errors with full details (non-blocking for now, per rollout plan Phase 1)
                    logger.error(f"🚨 Signal validation FAILED for {ticker}", extra={
                        "operation": "signal_validation_failed",
                        "ticker": ticker,
                        "error_count": len(validation_result.errors),
                        "errors": validation_result.errors,
                        "warning_count": len(validation_result.warnings),
                        "warnings": validation_result.warnings,
                        "market_state_confidence": result.get("market_state", {}).get("confidence", "N/A"),
                        "scenario_probs": [s.get("probability") for s in result.get("scenarios", [])],
                        "narrative_type": type(result.get("narrative")).__name__
                    })
                    
                    # Log each error individually for clarity
                    for i, error in enumerate(validation_result.errors, 1):
                        logger.error(f"  ❌ Validation Error {i}/{len(validation_result.errors)}: {error}", extra={
                            "operation": "validation_error_detail",
                            "ticker": ticker,
                            "error_index": i,
                            "error_message": error
                        })
                    
                    # TODO Phase 4: Enable enforcement - raise ValidationError
                    # raise ValidationError(f"Signal validation failed: {validation_result.errors}")
                    
                    logger.warning("⚠️ Accepting invalid signal for now (Phase 1: logging only)", extra={
                        "operation": "validation_bypassed",
                        "ticker": ticker,
                        "phase": "Phase 1 - Logging Only"
                    })
                
                # Log warnings even if valid
                if validation_result.warnings:
                    logger.warning(f"⚠️ Signal validation warnings for {ticker}", extra={
                        "operation": "signal_validation_warnings", 
                        "ticker": ticker,
                        "warning_count": len(validation_result.warnings),
                        "warnings": validation_result.warnings
                    })
                    
                    # Log each warning individually
                    for i, warning in enumerate(validation_result.warnings, 1):
                        logger.warning(f"  ⚠️ Validation Warning {i}/{len(validation_result.warnings)}: {warning}", extra={
                            "operation": "validation_warning_detail",
                            "ticker": ticker,
                            "warning_index": i,
                            "warning_message": warning
                        })
                
                if validation_result.valid:
                    logger.info(f"✅ Signal validation PASSED for {ticker}", extra={
                        "operation": "signal_validation_passed",
                        "ticker": ticker,
                        "warning_count": len(validation_result.warnings),
                        "validation_summary": {
                            "confidence": result.get("market_state", {}).get("confidence"),
                            "scenario_count": len(result.get("scenarios", [])),
                            "prob_sum": sum(s.get("probability", 0) for s in result.get("scenarios", [])),
                            "narrative_format": "dict" if isinstance(result.get("narrative"), dict) else "string"
                        }
                    })
            
            except Exception as validation_err:
                logger.error(f"❌ Validator exception for {ticker}: {validation_err}", extra={
                    "operation": "validator_exception",
                    "ticker": ticker,
                    "error": str(validation_err),
                    "error_type": type(validation_err).__name__
                }, exc_info=True)
                # Don't block on validator errors during Phase 1
                logger.warning("⚠️ Continuing despite validator exception (Phase 1)", extra={
                    "operation": "validation_exception_bypassed",
                    "ticker": ticker
                })
            
            # MARKET-GRADE: NARRATIVE VALIDATION (Enforce LLM as renderer only)
            try:
                from app.validators.narrative_validator import validate_narrative
                
                logger.info(f"📝 MARKET-GRADE: Validating narrative for {ticker}", extra={
                    "operation": "narrative_validation_start",
                    "ticker": ticker,
                    "has_narrative": "narrative" in result
                })
                
                # Build structured state for validation
                structured_state = {
                    "market_state": result.get("market_state", {}),
                    "price_zones": result.get("price_zones", {}),
                    "scenarios": result.get("scenarios", []),
                    "risk_factors": result.get("risk_factors", [])
                }
                
                narrative_validation = validate_narrative(
                    narrative=result.get("narrative", {}),
                    structured_state=structured_state
                )
                
                if not narrative_validation.is_valid:
                    logger.error(f"🚨 NARRATIVE validation FAILED for {ticker}", extra={
                        "operation": "narrative_validation_failed",
                        "ticker": ticker,
                        "error_count": len(narrative_validation.errors),
                        "errors": narrative_validation.errors,
                        "warning_count": len(narrative_validation.warnings),
                        "warnings": narrative_validation.warnings
                    })
                    
                    # Log each error individually
                    for i, error in enumerate(narrative_validation.errors, 1):
                        logger.error(f"  ❌ Narrative Error {i}/{len(narrative_validation.errors)}: {error}", extra={
                            "operation": "narrative_error_detail",
                            "ticker": ticker,
                            "error_index": i,
                            "error_message": error
                        })
                    
                    # TODO Phase 2: Enable regeneration with stricter constraints
                    # stricter_prompt = enforce_narrative_regeneration(result["narrative"], structured_state, narrative_validation)
                    # regenerate_narrative_with_strict_prompt(...)
                    
                    logger.warning("⚠️ Accepting invalid narrative for now (Phase 1: logging only)", extra={
                        "operation": "narrative_validation_bypassed",
                        "ticker": ticker,
                        "phase": "Phase 1 - Logging Only"
                    })
                else:
                    logger.info(f"✅ NARRATIVE validation PASSED for {ticker}", extra={
                        "operation": "narrative_validation_passed",
                        "ticker": ticker,
                        "warning_count": len(narrative_validation.warnings)
                    })
                
                # Log warnings even if valid
                if narrative_validation.warnings:
                    for i, warning in enumerate(narrative_validation.warnings, 1):
                        logger.warning(f"  ⚠️ Narrative Warning {i}/{len(narrative_validation.warnings)}: {warning}", extra={
                            "operation": "narrative_warning_detail",
                            "ticker": ticker,
                            "warning_index": i,
                            "warning_message": warning
                        })
                        
            except Exception as narrative_validation_err:
                logger.error(f"❌ Narrative validator exception for {ticker}: {narrative_validation_err}", extra={
                    "operation": "narrative_validator_exception",
                    "ticker": ticker,
                    "error": str(narrative_validation_err),
                    "error_type": type(narrative_validation_err).__name__
                }, exc_info=True)
                logger.warning("⚠️ Continuing despite narrative validator exception (Phase 1)", extra={
                    "operation": "narrative_validation_exception_bypassed",
                    "ticker": ticker
                })

            
            # Log full OpenAI response for debugging
            logger.info(f"📨 FULL OPENAI RESPONSE CONTENT for {ticker}:")
            logger.info(f"{response.choices[0].message.content[:1000]}")  # First 1000 chars
            
            # NOTE: We do NOT validate RAG output here
            # RAG has its own schema (analysis, prediction, reasoning, etc.)
            # Output validation is ONLY for Signal API (SignalResponse schema)
            # The validator expects: analysis_summary, signal_explanation, scenario_narratives, market_context_summary
            # But RAG produces: analysis.summary, analysis.full_text, prediction.outlook, etc.
            # These are DIFFERENT schemas, so validation would fail incorrectly
            
            logger.info(f"✅ RAG: LLM response received successfully", extra={
                "operation": "rag_llm_success",
                "ticker": ticker or "none",
                "response_keys": list(result.keys()) if isinstance(result, dict) else []
            })
            
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
            
            # NEW: Map V3 probabilistic response to legacy format
            # V3 has: market_state, price_zones, scenarios, narrative (new: dict or old: string)
            # Legacy expects: analysis, prediction, reasoning
            if "market_state" in result and "narrative" not in result.get("analysis", {}):
                logger.info(f"🔄 Mapping V3 response to legacy format for {ticker}")
                
                market_state = result.get("market_state", {})
                price_zones = result.get("price_zones", {})
                scenarios_v3 = result.get("scenarios", [])
                narrative = result.get("narrative", "")
                
                # Check if narrative is new structured format (dict) or old format (string)
                if isinstance(narrative, dict):
                    logger.info("✅ Detected NEW structured narrative format", extra={
                        "operation": "narrative_format_detection",
                        "ticker": ticker,
                        "narrative_type": "dict",
                        "has_analysis_summary": bool(narrative.get("analysis_summary")),
                        "has_analysis_text": bool(narrative.get("analysis_text")),
                        "has_prediction_text": bool(narrative.get("prediction_text")),
                        "analysis_text_length": len(narrative.get("analysis_text", "")),
                        "prediction_text_length": len(narrative.get("prediction_text", ""))
                    })
                    
                    # NEW FORMAT: Use structured narrative fields
                    analysis_text = narrative.get("analysis_text", "")
                    prediction_text = narrative.get("prediction_text", "")
                    
                    # CRITICAL: Preserve all V3 structured fields
                    # Keep market_state, price_zones, scenarios, etc.
                    # (result already has these from OpenAI response)
                    
                    # Add legacy text fields for backward compatibility
                    result["analysis"] = analysis_text
                    result["prediction"] = prediction_text
                    result["reasoning"] = narrative.get("analysis_summary", "")
                    
                    result["analysis_structured"] = {
                        "summary": narrative.get("analysis_summary", ""),
                        "key_points": narrative.get("analysis_key_points", []),
                        "full_text": analysis_text
                    }
                    
                    result["prediction_structured"] = {
                        "summary": narrative.get("prediction_summary", ""),
                        "key_points": narrative.get("prediction_key_points", []),
                        "outlook": prediction_text,
                        "scenarios": scenarios_v3
                    }
                    
                    logger.info(f"✅ Mapped new narrative: analysis={len(analysis_text)} chars, prediction={len(prediction_text)} chars", extra={
                        "operation": "narrative_mapping_complete",
                        "ticker": ticker,
                        "analysis_length": len(analysis_text),
                        "prediction_length": len(prediction_text),
                        "preserved_v3_fields": {
                            "market_state": bool(result.get("market_state")),
                            "price_zones": bool(result.get("price_zones")),
                            "scenarios": len(result.get("scenarios", [])),
                            "signal_conflicts": len(result.get("signal_conflicts", [])),
                            "risk_factors": len(result.get("risk_factors", []))
                        }
                    })
                    
                else:
                    logger.warning("⚠️ Detected OLD narrative format (string), using fallback mapping")
                    
                    # OLD FORMAT: Build analysis from market_state + price_zones + narrative string
                    analysis_text = f"""Market Analysis:
Trend: {market_state.get('trend_bias', 'neutral').title()}
Momentum: {market_state.get('momentum_state', 'neutral').title()}
Volatility: {market_state.get('volatility_state', 'normal').title()}
Confidence: {market_state.get('confidence', 0.5):.0%}

Price Zones:
Support: ₹{price_zones.get('support', [0])[0] if isinstance(price_zones.get('support'), list) else price_zones.get('support', 0)}
Value Area: ₹{price_zones.get('value_area', [0])[0] if isinstance(price_zones.get('value_area'), list) else price_zones.get('value_area', 0)}
Resistance: ₹{price_zones.get('resistance', [0])[0] if isinstance(price_zones.get('resistance'), list) else price_zones.get('resistance', 0)}

{narrative}"""
                    
                    # Map prediction from scenarios
                    prediction_text = "Market Scenarios:\\n\\n"
                    for scenario in scenarios_v3:
                        prediction_text += f"{scenario.get('description', 'Unknown').title()}: "
                        prediction_text += f"(Probability: {scenario.get('probability', 0):.0%})\\n\\n"
                    
                    result["analysis"] = analysis_text
                    result["prediction"] = prediction_text
                    result["reasoning"] = narrative if isinstance(narrative, str) else ""
                    
                    result["analysis_structured"] = {
                        "summary": f"{market_state.get('trend_bias', 'Neutral').title()} trend with {market_state.get('confidence', 0.5):.0%} confidence",
                        "key_points": [
                            f"Trend: {market_state.get('trend_bias', 'neutral')}",
                            f"Momentum: {market_state.get('momentum_state', 'neutral')}",
                            f"Volatility: {market_state.get('volatility_state', 'normal')}"
                        ],
                        "full_text": analysis_text
                    }
                    
                    result["prediction_structured"] = {
                        "summary": f"{len(scenarios_v3)} scenarios identified",
                        "outlook": prediction_text,
                        "scenarios": scenarios_v3
                    }
                    
                    logger.info(f"✅ Mapped old narrative: analysis={len(analysis_text)} chars, prediction={len(prediction_text)} chars")
            
            # FINAL: Log result structure before returning
            logger.info(f"📤 Final RAG result for {ticker}", extra={
                "operation": "rag_result_final",
                "ticker": ticker,
                "result_keys": list(result.keys()) if isinstance(result, dict) else [],
                "has_market_state": "market_state" in result if isinstance(result, dict) else False,
                "has_price_zones": "price_zones" in result if isinstance(result, dict) else False,
                "has_scenarios": "scenarios" in result if isinstance(result, dict) else False,
                "scenario_count": len(result.get("scenarios", [])) if isinstance(result, dict) else 0,
                "has_analysis": "analysis" in result if isinstance(result, dict) else False,
                "has_prediction": "prediction" in result if isinstance(result, dict) else False
            })
            
            return result
            
        except Exception as llm_err:
            logger.error(f"Error generating LLM response: {llm_err}", exc_info=True)  # Add full traceback
            return {
                "summary": "Unable to generate analysis at this time.",
                "reasoning": "",
                "risk_factors": [],
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
