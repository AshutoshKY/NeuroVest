# RAG System Documentation - NeuroVest Stock Market Platform

**Document Version**: 1.0  
**Last Updated**: December 11, 2025  
**RAG Model**: Azure OpenAI GPT-4 with Retrieval-Augmented Generation

## Table of Contents
1. [Executive Overview](#executive-overview)
2. [RAG Architecture](#rag-architecture)
3. [Complete Data Flow](#complete-data-flow)
4. [Data Ingestion Pipeline](#data-ingestion-pipeline)
5. [Vector Database & Embeddings](#vector-database--embeddings)
6. [Context Retrieval Process](#context-retrieval-process)
7. [Prompt Engineering](#prompt-engineering)
8. [OpenAI Integration](#openai-integration)
9. [Security & Guardrails](#security--guardrails)
10. [Caching Strategy](#caching-strategy)
11. [Frontend-Backend Integration](#frontend-backend-integration)
12. [Performance & Cost Analysis](#performance--cost-analysis)
13. [Real-Time Observability](#real-time-observability)

---

## Executive Overview

### What is RAG?

**RAG (Retrieval-Augmented Generation)** is an AI architecture that combines:
1. **Information Retrieval**: Fetching relevant context from a knowledge base
2. **Generative AI**: Using that context to generate informed, grounded responses

**Why RAG?**
- ✅ **Grounded Responses**: AI answers are based on real, up-to-date data
- ✅ **Reduced Hallucinations**: Context prevents AI from making things up
- ✅ **Dynamic Knowledge**: No need to retrain models for new information
- ✅ **Cost-Effective**: Cheaper than fine-tuning custom models

### NeuroVest RAG Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Data Ingestion** | Web Scraping (DuckDuckGo) + RSS Feeds | Fetch latest stock news |
| **Embeddings** | Sentence-Transformers (all-MiniLM-L6-v2) | Convert text → 384-dim vectors |
| **Vector DB** | ChromaDB (Persistent) | Store & search embeddings |
| **LLM** | Azure OpenAI GPT-4 | Generate analysis from context |
| **Caching** | Redis (1h) + MySQL + ChromaDB | Multi-tier performance optimization |
| **Performance** | AsyncIO + Background Loading | Non-blocking start & concurrent reqs |
| **Security** | Guardrails Service | Input validation, output sanitization |

---

## RAG Architecture

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                    RAG System Architecture                            │
└──────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                   │
└──────────────┬──────────────────────────────────────┬───────────────┘
               │                                      │
               v                                      v
    ┌──────────────────┐                  ┌──────────────────┐
    │  News Sources    │                  │  Stock APIs      │
    │  ──────────────  │                  │  ──────────────  │
    │  • Web Scraping  │                  │  • Yahoo Finance │
    │  • RSS Feeds     │                  │  • Alpha Vantage │
    │  • Google News   │                  │  • Finnhub       │
    └────────┬─────────┘                  └──────────┬───────┘
             │                                       │
             v                                       v
    ┌──────────────────────────────────────────────────────┐
    │         Data Ingestion Service                       │
    │  • Parallel scraping                                 │
    │  • Deduplication                                     │
    │  • Preprocessing                                     │
    └────────────────────┬─────────────────────────────────┘
                         │
                         v
┌────────────────────────────────────────────────────────────────────┐
│                      EMBEDDING LAYER                                │
└────────────────────────────────────────────────────────────────────┘
                         │
             ┌───────────┴───────────┐
             v                       v
    ┌─────────────────┐     ┌─────────────────┐
    │ Text Chunking   │     │ Embedding Model │
    │ (512 tokens)    │────▶│ all-MiniLM-L6-v2│
    └─────────────────┘     │ (384 dimensions)│
                            └────────┬────────┘
                                     │
                                     v
┌────────────────────────────────────────────────────────────────────┐
│                     STORAGE LAYER                                   │
└────────────────────────────────────────────────────────────────────┘
                                     │
          ┌──────────────────────────┼──────────────────────────┐
          v                          v                          v
    ┌──────────┐              ┌────────────┐            ┌──────────┐
    │ ChromaDB │              │   MySQL    │            │  Redis   │
    │          │              │            │            │          │
    │ • News   │              │ • Users    │            │ • Cache  │
    │   (vector│              │ • History  │            │ • JWT    │
    │   search)│              │ • Sessions │            │ • Limits │
    └────┬─────┘              └──────┬─────┘            └────┬─────┘
         │                           │                       │
         └───────────────┬───────────┴───────────────────────┘
                         │
                         v
┌────────────────────────────────────────────────────────────────────┐
│                      RAG LAYER                                      │
└────────────────────────────────────────────────────────────────────┘
         │
         │ User Query: "Analyze TCS stock"
         v
    ┌─────────────────────────────────────┐
    │  1. Rate Limiting (Redis)           │
    │     Check: 5 analyses/day           │
    └──────────────┬──────────────────────┘
                   │ Allowed
                   v
    ┌─────────────────────────────────────┐
    │  2. Cache Check (Redis)             │
    │     Key: analysis_cache:TCS         │
    └──────────────┬──────────────────────┘
                   │ Cache MISS
                   v
    ┌─────────────────────────────────────┐
    │  3. Vector Search (ChromaDB)        │
    │     • Query embedding               │
    │     • Semantic search (news)        │
    │     • Filter: ticker=TCS            │
    │     • Retrieve: Top 10 articles     │
    └──────────────┬──────────────────────┘
                   │
                   v
    ┌─────────────────────────────────────┐
    │  4. Historical Context (ChromaDB)   │
    │     • Retrieve past analyses        │
    │     • Extract: predictions, risks   │
    │     • Compare: old vs new state     │
    └──────────────┬──────────────────────┘
                   │
                   v
    ┌─────────────────────────────────────┐
    │  5. Technical Analysis (MySQL)      │
    │     • Calculate: RSI, MACD, BB      │
    │     • 30-day trend analysis         │
    │     • Prediction accuracy tracking  │
    └──────────────┬──────────────────────┘
                   │
                   v
    ┌─────────────────────────────────────┐
    │  6. Context Assembly                │
    │     • News articles (current)       │
    │     • Historical analyses (old)     │
    │     • Technical indicators          │
    │     • Trend data                    │
    └──────────────┬──────────────────────┘
                   │
                   v
    ┌─────────────────────────────────────┐
    │  7. Prompt Engineering              │
    │     • Synthesis mode (if history)   │
    │     • Baseline mode (no history)    │
    │     • Inject: comparison keywords   │
    └──────────────┬──────────────────────┘
                   │
                   v
┌────────────────────────────────────────────────────────────────────┐
│              LLM LAYER (Async Azure OpenAI GPT-4)                   │
└────────────────────────────────────────────────────────────────────┘
         │
         │ Temperature: 0.5
         │ Response Format: JSON
         v
    ┌─────────────────────────────────────┐
    │  GPT-4 Generation                   │
    │  • Summary                          │
    │  • Reasoning                        │
    │  • Risk Factors                     │
    │  • Key Insights                     │
    │  • Prediction                       │
    └──────────────┬──────────────────────┘
                   │
                   v
    ┌─────────────────────────────────────┐
    │  8. Security Guardrails             │
    │     • Output sanitization           │
    │     • Disclaimer injection          │
    │     • Financial advice removal      │
    └──────────────┬──────────────────────┘
                   │
                   v
    ┌─────────────────────────────────────┐
    │  9. Multi-Tier Storage              │
    │     • Redis: 1h cache               │
    │     • MySQL: analysis_history       │
    │     • ChromaDB: embed for future    │
    └──────────────┬──────────────────────┘
                   │
                   v
               ┌────────┐
               │ Client │
               │Response│
               └────────┘
```

---

## Complete Data Flow

### End-to-End Request Flow

```
USER REQUEST
    │
    ├─► Frontend: GET /stocks/TCS/analysis
    │
    v
┌───────────────────────────────────────────────────────────────────┐
│ STEP 1: API ENDPOINT (/api/stocks.py)                             │
│ • Extract ticker from URL                                         │
│ • Get current user from JWT                                       │
│ • Call RAG service                                                │
└──────────────────────────┬────────────────────────────────────────┘
                           │
                           v
┌───────────────────────────────────────────────────────────────────┐
│ STEP 2: RATE LIMITING (Redis)                                     │
│ • Check: rate_limit:user:123:analysis                             │
│ • Current: 3/5 requests                                           │
│ • Decision: ALLOW                                                 │
│ • Action: INCR counter, set TTL 86400s                            │
└──────────────────────────┬────────────────────────────────────────┘
                           │
                           v
┌───────────────────────────────────────────────────────────────────┐
│ STEP 3: CACHE CHECK (Redis)                                       │
│ Key: analysis_cache:TCS                                           │
│ TTL: 3600s (1 hour)                                               │
│                                                                   │
│ IF CACHE HIT:                                                     │
│   → Return instantly (<1ms)                                       │
│   → Skip steps 4-9 (MASSIVE performance boost)                    │
│                                                                   │
│ IF CACHE MISS:                                                    │
│   → Continue to step 4                                            │
└──────────────────────────┬────────────────────────────────────────┘
                           │ CACHE MISS
                           v
┌─────────────────────────────────────────────────────────────────── │
│ STEP 4: DATA INGESTION (On-Demand)                                │
│ • Trigger: ingest_for_ticker("TCS", "Tata Consultancy Services")  │
│ • Strategy 1: Web Scraper (DuckDuckGo)                            │
│   - Query: "Tata Consultancy Services TCS stock news"             │
│   - Fetch: 15 search results                                      │
│   - Extract: Full article content                                 │
│   - Deduplicate: Remove duplicates by URL                         │
│ • Strategy 2 (Fallback): RSS Scraper (Google News)                │
│   - Query: Google News RSS feed                                   │
│   - Fetch: 5 articles                                             │
│ • Result: 10-15 fresh articles                                    │
└──────────────────────────┬────────────────────────────────────────┘
                           │
                           v
┌───────────────────────────────────────────────────────────────────┐
│ STEP 5: TEXT PREPROCESSING                                        │
│ • Clean HTML (remove tags, scripts)                               │
│ • Chunk text (512 tokens per chunk)                               │
│ • Extract keywords (TF-IDF)                                       │
│ • Detect tickers (regex + hardcoded list)                         │
│ • Metadata: {ticker, source, url, timestamp}                      │
└──────────────────────────┬────────────────────────────────────────┘
                           │
                           v
┌───────────────────────────────────────────────────────────────────┐
│ STEP 6: EMBEDDING GENERATION (Local Model)                        │
│ Model: all-MiniLM-L6-v2 (Sentence Transformers)                   │
│ Input:  "Tata Consultancy Services reports strong Q3 earnings..." │
│ Output: [0.123, -0.456, 0.789, ..., 0.234] (384 dimensions)      │
│ Latency: 10-50ms per chunk (CPU)                                  │
│ Cost: FREE (local inference)                                      │
└──────────────────────────┬────────────────────────────────────────┘
                           │
                           v
┌───────────────────────────────────────────────────────────────────┐
│ STEP 7: VECTOR DB STORAGE (ChromaDB)                              │
│ Collection: stock_news                                            │
│ Documents: 15 articles × ~3 chunks = 45 vectors                   │
│ Metadata: {ticker: "TCS", source: "...", url: "...", ...}         │
│ Storage: ~/chroma_data/stock_news/                                │
└──────────────────────────┬────────────────────────────────────────┘
                           │
                           v
┌───────────────────────────────────────────────────────────────────┐
│ STEP 8: VECTOR SEARCH (Semantic Similarity)                       │
│ Query: "Analyze TCS stock performance and outlook"                │
│ Query Embedding: generate_embedding(query) → 384-dim vector       │
│ Search: ChromaDB.query(                                           │
│   query_embedding=[query_vector],                                 │
│   n_results=10,                                                   │
│   where={\"ticker\": \"TCS\"}  # Metadata filter                      │
│ )                                                                 │
│ Result: Top 10 most relevant articles (by cosine similarity)      │
│ Latency: 10-50ms                                                  │
└──────────────────────────┬────────────────────────────────────────┘
                           │
                           v
┌───────────────────────────────────────────────────────────────────┐
│ STEP 9: HISTORICAL ANALYSIS RETRIEVAL (ChromaDB)                  │
│ Collection: stock_analysis                                        │
│ Query: retrieve_historical_analyses("TCS", top_k=5)               │
│ WHERE: {type: "historical_analysis", ticker: "TCS"}               │
│ Result: [                                                         │
│   {                                                               │
│     text: "Past analysis summary...",                             │
│     metadata: {                                                   │
│       timestamp: "2025-12-10",                                    │
│       prediction_direction: "Bullish",                            │
│       sentiment: "Positive",                                      │
│       price: 3175.50,                                             │
│       rsi: 62.5,                                                  │
│       risk_factors: [...],                                        │
│       key_insights: [...]                                         │
│     }                                                             │
│   },                                                              │
│   ...  // 4 more historical analyses                             │
│ ]                                                                 │
│ Latency: 50-100ms                                                 │
└──────────────────────────┬────────────────────────────────────────┘
                           │
                           v
┌───────────────────────────────────────────────────────────────────┐
│ STEP 10: TECHNICAL INDICATORS (Stock API + MySQL)                 │
│ • Fetch: 3-month historical OHLCV data                            │
│ • Calculate:                                                      │
│   - RSI (14): 65.2 (Neutral)                                      │
│   - MACD: Bullish crossover                                       │
│   - Bollinger Bands: Price near upper band                        │
│ • 30-Day Trends:                                                  │
│   - RSI Trend: Rising (from 58 → 65)                              │
│   - Price Trend: +5.2% (bullish momentum)                         │
│   - Sentiment Trend: Improving                                    │
│ • Prediction Accuracy (past 30 days):                             │
│   - Overall: 75% (9/12 correct)                                   │
│   - High-Confidence: 85%                                         │
│ • Latency: 100-300ms (API calls)                                  │
└──────────────────────────┬────────────────────────────────────────┘
                           │
                           v
┌───────────────────────────────────────────────────────────────────┐
│ STEP 11: CONTEXT ASSEMBLY                                         │
│ Combine all data sources:                                         │
│                                                                   │
│ [News Context] (10 articles):                                     │
│ • Article 1: "TCS Q3 earnings beat estimates..."                  │
│ • Article 2: "TCS wins $500M deal with Fortune 500..."            │
│ • ...                                                             │
│                                                                   │
│ [Technical Context]:                                              │
│ • RSI: 65.2 (Neutral)                                             │
│ • MACD: Bullish (Histogram +2.3)                                  │
│ • BB: Price at upper band (potential resistance)                  │
│                                                                   │
│ [Trend Context] (30-day analysis):                                │
│ • RSI Trend: Rising (momentum building)                           │
│ • Price Trend: +5.2% (bullish)                                    │
│ • Sentiment Trend: Improving (+0.15)                              │
│                                                                   │
│ [Historical Context] (5 past analyses):                           │
│ • [2025-12-10] Bullish at ₹3175. Insights: Strong fundamentals... │
│ • [2025-12-05] Neutral at ₹3100. Risks: Market volatility...      │
│ • ...                                                             │
│                                                                   │
│ [Prediction Accuracy Context]:                                    │
│ • Overall: 75% accuracy                                           │
│ • Insight: Model tends to be bullish; calibrate confidence        │
└──────────────────────────┬────────────────────────────────────────┘
                           │
                           v
┌───────────────────────────────────────────────────────────────────┐
│ STEP 12: PROMPT ENGINEERING (Intelligent Mode Selection)          │
│                                                                   │
│ IF historical_analyses.length > 0:                                │
│   MODE: SYNTHESIS (Compare old vs new)                            │
│   Prompt: "You are a financial analyst with historical memory.    │
│            CRITICAL: Compare current state (Price: ₹3188, RSI: 65)│
│            against Historical Baseline (Price: ₹3175, RSI: 62).   │
│            Analyze the TRAJECTORY and CHANGE..."                  │
│                                                                   │
│ ELSE:                                                             │
│   MODE: BASELINE (First analysis)                                 │
│   Prompt: "You are establishing a BASELINE analysis. Focus on     │
│            current setup and create benchmarks for future..."     │
│                                                                   │
│ Output Format: JSON with {summary, reasoning, prediction, ...}    │
└──────────────────────────┬────────────────────────────────────────┘
                           │
                           v
┌───────────────────────────────────────────────────────────────────┐
│ STEP 13: OPENAI API CALL (Azure GPT-4)                            │
│ Model: gpt-4 (Azure deployment)                                   │
│ Temperature: 0.5 (balanced creativity/consistency)                │
│ Messages: [                                                       │
│   {role: "system", content: "You are a financial analyst..."},    │
│   {role: "user", content: <FULL_PROMPT_WITH_CONTEXT>}             │
│ ]                                                                 │
│ Response Format: {type: "json_object"}                            │
│                                                                   │
│ Cost: ~$0.03-0.10 per request (depends on context length)         │
│ Latency: 2-5 seconds (Non-blocking / Concurrent)                  │
│                                                                   │
│ Response: {                                                       │
│   summary: "TCS shows strong momentum with Q3 earnings beat...",  │
│   reasoning: "Revenue growth +12% YoY, RSI rising from 62→65...", │
│   risk_factors: ["Market volatility", "Sector headwinds", ...],   │
│   key_insights: ["Strong fundamentals", "Technical breakout",...],│
│   prediction: "Bullish outlook with ₹3250 target..."              │
│ }                                                                 │
└──────────────────────────┬────────────────────────────────────────┘
                           │
                           v
┌───────────────────────────────────────────────────────────────────┐
│ STEP 14: SECURITY GUARDRAILS                                      │
│ Input Validation:                                                 │
│ • Check for prompt injection attempts                             │
│ • Sanitize user input                                             │
│                                                                   │
│ Output Processing:                                                │
│ • Remove financial advice ("Buy", "Sell" → "May consider")        │
│ • Inject disclaimer: "This is not financial advice..."            │
│ • Sanitize HTML/script tags                                       │
│ • Validate JSON structure                                         │
└──────────────────────────┬────────────────────────────────────────┘
                           │
                           v
┌───────────────────────────────────────────────────────────────────┐
│ STEP 15: MULTI-TIER STORAGE                                       │
│                                                                   │
│ ┌─── REDIS CACHE ───┐                                             │
│ │ Key: analysis_cache:TCS                                         │
│ │ Value: {analysis result JSON}                                   │
│ │ TTL: 3600s (1 hour)                                             │
│ │ Purpose: Fast subsequent requests                               │
│ └───────────────────┘                                             │
│                                                                   │
│ ┌─── MYSQL ────────┐                                              │
│ │ Table: analysis_history                                         │
│ │ INSERT: (ticker, user_id, sentiment, timestamp)                 │
│ │ Purpose: Track usage, trending stocks                           │
│ │                                                                 │
│ │ Table: analysis_cache                                           │
│ │ INSERT: (ticker, analysis_json, price, rsi, predictions...)     │
│ │ Purpose: Historical tracking with full metadata                 │
│ └───────────────────┘                                             │
│                                                                   │
│ ┌─── CHROMADB ─────┐                                              │
│ │ Collection: stock_analysis                                      │
│ │ Add Document: Full analysis summary with embeddings             │
│ │ Metadata: {ticker, timestamp, sentiment, prediction, rsi, ...}  │
│ │ Purpose: Enable semantic search over past analyses              │
│ │          Used in future analyses for comparison                 │
│ └───────────────────┘                                             │
└──────────────────────────┬────────────────────────────────────────┘
                           │
                           v
┌───────────────────────────────────────────────────────────────────┐
│ STEP 16: RESPONSE TO CLIENT                                       │
│ HTTP 200 OK                                                       │
│ {                                                                 │
│   "ticker": "TCS",                                                │
│   "analysis": "TCS shows strong momentum...",                     │
│   "reasoning": "Revenue growth +12% YoY...",                      │
│   "prediction": "Bullish outlook with ₹3250 target...",           │
│   "sentiment": {                                                  │
│     "classification": "Bullish",                                  │
│     "score": 0.75,                                                │
│     "confidence": 0.85                                            │
│   },                                                              │
│   "risk_factors": ["Market volatility", ...],                     │
│   "key_insights": ["Strong fundamentals", ...],                   │
│   "technical_analysis": {                                         │
│     "indicators": {rsi, macd, bollinger_bands},                   │
│     "trends": {...}                                               │
│   },                                                              │
│   "references": [                                                 │
│     {source: "ET", url: "...", title: "..."},                     │
│     ...                                                           │
│   ],                                                              │
│   "disclaimer": "This is not financial advice...",                │
│   "cached": false                                                 │
│ }                                                                 │
│                                                                   │
│ Total Latency:                                                    │
│ • Cache HIT: <1ms                                                 │
│ • Cache MISS (full pipeline): 3-8 seconds                         │
│   - Ingestion: 1-2s                                               │
│   - Embedding: 0.5-1s                                             │
│   - Vector search: 0.05s                                          │
│   - LLM: 2-5s (dominant)                                          │
│   - Storage: 0.1s                                                 │
└───────────────────────────────────────────────────────────────────┘
```

---

## Data Ingestion Pipeline

### Two-Strategy Ingestion System

The system uses a **primary + fallback** strategy for maximum reliability:

**Strategy 1: Web Scraper (Primary)** - DuckDuckGo Search
```python
# Triggered on-demand during analysis request
articles = web_scraper.search_and_scrape(
    query=f"{company_name} {ticker} stock news",
    max_results=15
)
# Returns: Full article content from diverse sources
```

**Strategy 2: RSS Scraper (Fallback)** - Google News RSS
```python
# If web scraper fails
rss_url = f"https://news.google.com/rss/search?q={query}"
articles = rss_scraper.fetch(rss_url, max_articles=5)
# Returns: Reliable but less detailed articles
```

### Preprocessing Pipeline

1. **Deduplication**: Remove duplicate URLs
2. **HTML Cleaning**: Strip tags, scripts, ads
3. **Text Chunking**: Split into 512-token segments
4. **Keyword Extraction**: TF-IDF algorithm
5. **Ticker Detection**: Regex + hardcoded list
6. **Embedding Generation**: 384-dim vectors
7. **Storage**: ChromaDB with metadata

---

## Vector Database & Embeddings

### Embedding Model: all-MiniLM-L6-v2

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embedding = model.encode("TCS reports strong earnings")
# Output: [0.123, -0.456, ..., 0.234]  # 384 dimensions
```

**Model Specifications**:
- Dimensions: 384
- Max sequence length: 256 tokens
- Speed: 10-50ms per text (CPU)
- Cost: **FREE** (local inference)

### Vector Search (Semantic Similarity)

```python
# 1. Generate query embedding
query_embedding = model.encode("Analyze TCS stock")

# 2. Search ChromaDB using cosine similarity
results = chroma_collection.query(
    query_embeddings=[query_embedding],
    n_results=10,
    where={"ticker": "TCS"}  # Metadata filter
)

# 3. Returns top 10 most similar articles
# Sorted by distance (0.0 = identical, 2.0 = opposite)
```

### Historical Analysis Retrieval

**The KEY to intelligent synthesis:**

```python
def retrieve_historical_analyses(ticker: str, top_k: int = 5):
    """Get past analyses for comparison"""
    
    results = chroma_analysis_collection.get(
        where={
            "$and": [
                {"type": "historical_analysis"},
                {"ticker": ticker}
            ]
        },
        limit=top_k
    )
    
    # Returns: Past analyses with metadata
    # - timestamp, prediction, sentiment
    # - price, RSI, risk factors, insights
```

---

## Prompt Engineering

### Intelligent Mode Selection

**TWO PROMPTING MODES**:

#### Mode 1: SYNTHESIS (if history exists)

```python
prompt = f"""You are a financial analyst with comprehensive historical data.

CRITICAL TASK: SYNTHESIZE past and present to identify TRAJECTORY.

DATA SOURCES:
1. HISTORICAL BASELINE (Past Analyses):
   {historical_context}  # Past 5 analyses with predictions, risks

2. FRESH MARKET DATA (Current):
   {news_context}         # Top 10 news articles
   {technical_context}    # RSI, MACD, Bollinger Bands
   {trends_context}       # 30-day indicator trends

MANDATORY COMPARISON:
- "Previously RSI was 62, now it is 65, indicating..."
- "The risk of X mentioned in past has INCREASED because..."
- Compare: Price then vs now, Sentiment then vs now

OUTPUT (JSON):
{{
  "summary": "How the stock evolved from past to present",
  "reasoning": "Drivers of change with specific numbers",
  "risk_factors": ["Old risks still relevant? New risks?"],
  "key_insights": ["Focus on SHIFTS in momentum"],
  "prediction": "Trajectory-based forward outlook"
}}
"""
```

#### Mode 2: BASELINE (first analysis)

```python
prompt = f"""You are establishing a BASELINE analysis (first-time).

CONTEXT:
{news_context}         # Current news articles
{technical_context}    # Current technical indicators
{trends_context}       # 30-day trends

FOCUS:
1. Establish current technical/fundamental setup
2. Identify PRIMARY risks to track
3. Set benchmark for future comparisons

OUTPUT (JSON):
{{
  "summary": "Comprehensive current state analysis",
  "reasoning": "Key drivers from current data",
  "risk_factors": ["3-5 critical risks for future tracking"],
  "key_insights": ["Major takeaways"],
  "prediction": "Forward outlook as baseline"
}}
"""
```

### Key Techniques

1. **Explicit Comparison Keywords**: "Previously X, now Y"
2. **JSON Response Format**: Structured, parseable output
3. **Temperature 0.5**: Balanced creativity/consistency
4. **System Message**: "You have historical memory. Learn from past predictions."

---

## OpenAI Integration

### Azure OpenAI Setup

```python
from openai import AsyncAzureOpenAI
import asyncio

client = AsyncAzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-15-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

response = await client.chat.completions.create(
    model="gpt-4",
    messages=[
        {
            "role": "system",
            "content": "You are a financial analyst with historical memory."
        },
        {
            "role": "user",
            "content": prompt  # Full context assembled above
        }
    ],
    temperature=0.5,
    response_format={"type": "json_object"}
)

analysis = json.loads(response.choices[0].message.content)
```

### Cost Optimization

**Per-Analysis Cost**:
- Input tokens: ~3500 × $0.03/1K = **$0.105**
- Output tokens: ~800 × $0.06/1K = **$0.048**
- **Total**: ~**$0.15 per analysis**

**With Caching** (70% hit rate):
- Actual cost: $0.15 × 0.30 = **$0.045 per analysis**
- Monthly (5000 analyses): **$225**

---

## Security & Guardrails

### Forbidden Phrases

```python
FORBIDDEN_PHRASES = [
    "buy", "sell", "you should", "we recommend",
    "strong buy", "strong sell", "time to buy"
]

REPLACEMENTS = {
    "buy": "acquire",
    "sell": "divest",
    "you should": "one might consider",
    "strong buy": "strong positive indicators"
}
```

### Output Sanitization

```python
def process_analysis(analysis: Dict) -> Dict:
    """Apply security guardrails"""
    
    # 1. Sanitize text fields
    for field in ["analysis", "reasoning", "summary"]:
        if field in analysis:
            # Replace forbidden phrases
            text = analysis[field]
            for forbidden, alternative in REPLACEMENTS.items():
                text = re.sub(
                    r'\b' + re.escape(forbidden) + r'\b',
                    alternative,
                    text,
                    flags=re.IGNORECASE
                )
            analysis[field] = text
    
    # 2. Add disclaimer
    analysis["disclaimer"] = """
⚠️ IMPORTANT: This is AI-generated analysis for 
informational purposes only. Not financial advice.
Always consult a qualified financial advisor.
    """
    
    return analysis
```

---

## Caching Strategy

### Multi-Tier Caching (Fast → Slow)

**Tier 1: Redis (1-hour TTL)**
```python
# Check cache FIRST
cached = redis.get(f"analysis_cache:{ticker}")
if cached:
    return json.loads(cached)  # <1ms return! ⚡

# ... generate analysis ...

# Cache for 1 hour
redis.setex(
    f"analysis_cache:{ticker}",
    3600,  # 1 hour
    json.dumps(analysis)
)
```

**Tier 2: MySQL (analysis_cache table)**
```python
# Persistent cache with metadata
db.execute("""
    INSERT INTO analysis_cache 
    (ticker, analysis_json, price, rsi, sentiment, ...)
    VALUES (?, ?, ?, ?, ?, ...)
""")
```

**Tier 3: ChromaDB (for future synthesis)**
```python
# Embed analysis for historical retrieval
chroma_analysis_collection.add(
    documents=[full_analysis_text],
    metadatas=[{
        "type": "historical_analysis",
        "ticker": ticker,
        "timestamp": now(),
        "prediction": "Bullish",
        "price": 3188.50,
        "rsi": 65.2,
        "risk_factors": json.dumps([...]),
        "key_insights": json.dumps([...])
    }],
    ids=[f"analysis_{ticker}_{timestamp}"]
)
```

### Cache Performance

| Metric | Value |
|--------|-------|
| Hit Rate | 65-75% (popular stocks) |
| Latency (hit) | <1ms |
| Latency (miss) | 3-8 seconds |
| Cost Savings | ~$525/month |
| Speed Improvement | 3000x faster |

---

## Frontend-Backend Integration

### REST API Endpoint

**GET** `/stocks/{ticker}/analysis`

```typescript
// Frontend
const response = await apiClient.get(`/stocks/TCS/analysis`);
```

```python
# Backend handler
@router.get("/{ticker}/analysis")
async def get_stock_analysis(
    ticker: str,
    request: Request,
    current_user = Depends(get_optional_user)
):
    # 1. Rate limiting
    await check_rate_limit(current_user.id, "analysis")
    
    # 2. Cache check
    cached = redis_cache.get_analysis(ticker)
    if cached:
        return cached
    
    # 3. Generate analysis
    analysis = rag_service.generate_analysis(
        query=f"Analyze {ticker} stock",
        ticker=ticker
    )
    
    # 4. Store & return
    redis_cache.set_analysis(ticker, analysis)
    return analysis
```

### Streaming Endpoint (Server-Sent Events)

**GET** `/stocks/{ticker}/analysis-stream`

```typescript
// Frontend - Progressive updates
const eventSource = new EventSource(
    `http://localhost:8000/stocks/${ticker}/analysis-stream`
);

eventSource.addEventListener('thinking', (e) => {
    const step = JSON.parse(e.data);
    console.log(step.description);  
    // "🔍 Checking cache..."
    // "📰 Fetching news..."
    // "🤖 Generating analysis..."
});

eventSource.addEventListener('result', (e) => {
    const analysis = JSON.parse(e.data);
    setAnalysisData(analysis);
    eventSource.close();
});
```

```python
# Backend - Yield progress steps
@router.get("/{ticker}/analysis-stream")
async def stream_analysis(ticker: str):
    async def event_generator():
        for step_type, data in rag_service.generate_analysis_with_steps(
            query, ticker
        ):
            if step_type == "step":
                yield {
                    "event": "thinking",
                    "data": json.dumps(data)
                }
            elif step_type == "final":
                yield {
                    "event": "result",
                    "data": json.dumps(data)
                }
    
    return EventSourceResponse(event_generator())
```

---

## Performance & Cost Analysis

### Latency Breakdown

| Component | Cache HIT | Cache MISS |
|-----------|-----------|------------|
| Rate Limiting | 1ms | 1ms |
| Cache Check | 1ms | 1ms |
| Data Ingestion | - | 1-2s |
| Embedding | - | 0.5-1s |
| Vector Search | - | 50ms |
| Technical Calc | - | 200ms |
| **OpenAI GPT-4** | - | **2-5s** |
| Storage | - | 100ms |
| **TOTAL** | **<5ms** | **4-9s** |

### Monthly Cost (1000 Users, 5 Analyses Each)

| Component | Cost | Optimization |
|-----------|------|--------------|
| OpenAI GPT-4 | $225 | 70% cache hit rate |
| Embeddings | $0 | Local model (FREE) |
| Redis | $0 | Self-hosted |
| MySQL | $0 | Self-hosted |
| ChromaDB | $0 | Self-hosted |
| VPS (4GB) | $20 | Hosts all services |
| Stock APIs | $0-50 | Free tiers |
| **TOTAL** | **$245-295** | - |

### Scaling Projections

| Users | Analyses/Day | OpenAI Cost | Infrastructure | Total |
|-------|--------------|-------------|----------------|-------|
| 1K | 5K | $225 | $70 | $295 |
| 5K | 25K | $1,125 | $150 | $1,275 |
| 10K | 50K | $2,250 | $300 | $2,550 |
| 50K | 250K | $11,250 | $1,000 | $12,250 |

---

## Complete RAG Flow (Pseudocode)

```python
def analyze_stock(ticker: str, user_id: int) -> Dict:
    """End-to-end RAG analysis"""
    
    # === STEP 1: GATE CHECKS ===
    check_rate_limit(user_id, ticker)  # 5/day
    
    cached = redis.get(f"analysis_cache:{ticker}")
    if cached:
        return json.loads(cached)  # ⚡ <1ms
    
    # === STEP 2: DATA COLLECTION ===
    # On-demand news ingestion
    ingest_for_ticker(ticker)
    # → Web scraping (15 articles)
    # → Preprocessing & chunking
    # → Embedding (384-dim)
    # → Store in ChromaDB
    
    # Fetch stock data
    stock_data = get_stock_data(ticker)
    # → Multi-API fallback
    
    # === STEP 3: CONTEXT ASSEMBLY ===
    news = query_similar_news(ticker, n=10)
    historical = retrieve_historical_analyses(ticker, n=5)
    technical = calculate_indicators(ticker)
    trends = analyze_30day_trends(ticker)
    
    # === STEP 4: PROMPT ENGINEERING ===
    if len(historical) > 0:
        prompt = synthesis_prompt(
            news, technical, trends, historical
        )  # Compare old vs new
    else:
        prompt = baseline_prompt(
            news, technical, trends
        )  # First analysis
    
    # === STEP 5: LLM GENERATION ===
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Financial analyst..."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        response_format={"type": "json_object"}
    )
    
    analysis = json.loads(response.choices[0].message.content)
    
    # === STEP 6: SECURITY ===
    analysis = apply_guardrails(analysis)
    # → Sanitize forbidden phrases
    # → Add disclaimer
    
    # === STEP 7: STORAGE ===
    redis.setex(f"analysis_cache:{ticker}", 3600, json.dumps(analysis))
    db.insert_analysis_history(ticker, user_id, analysis)
    embed_for_future_retrieval(ticker, analysis)
    
    # === STEP 8: RETURN ===
    return analysis
```

---

## Key Takeaways

### What Makes This RAG System Unique?

1. **Historical Memory** 🧠
   - Compares current vs past state
   - Learns from prediction accuracy
   - Synthesizes trajectory, not snapshots

2. **Multi-Source Intelligence** 📊
   - Real-time news (web + RSS)
   - Technical indicators (RSI, MACD, BB)
   - Historical analyses (ChromaDB)
   - 30-day trend analysis
   - Prediction accuracy tracking

3. **Cost-Optimized** 💰
   - FREE local embeddings
   - 70% cache hit rate
   - $0.045 per analysis (after caching)

4. **Security-First** 🛡️
   - Forbidden phrase detection
   - Automatic sanitization
   - Compliance disclaimers

5. **Performance-Optimized** ⚡
   - Cache hits: <5ms
   - Parallel data fetching
   - Efficient vector search

### Technology Stack

**Backend**:
- `openai` - Azure OpenAI GPT-4
- `sentence-transformers` - Local embeddings
- `chromadb` - Vector database
- `fastapi` - API framework
- `redis` - Caching
- `sqlalchemy` - ORM
- `beautifulsoup4` - Web scraping

**Frontend**:
- `react` - UI framework
- `next.js` - Framework
- `axios` - HTTP client
- `eventsource` - SSE support

### Limitations & Future Improvements

**Current Limitations**:
- 1-hour cache (may miss breaking news)
- Limited to 10 news articles
- Historical context capped at 5 analyses
- No real-time price updates during generation

**Future Enhancements**:
- Real-time mode for breaking news
- Multi-model ensemble (GPT-4 + Claude)
- User feedback loop integration
- Sector-wide comparative analysis
- Earnings calendar integration

---

## Summary

The RAG system combines:
- **Retrieval**: Semantic search over news + historical analyses
- **Augmentation**: Technical indicators, trends, accuracy tracking
- **Generation**: GPT-4 with intelligent synthesis prompts

**Result**: Grounded, context-aware stock analysis that learns from history and adapts to market changes.

---

**End of RAG System Documentation**

*Version: 1.0*  
*Last Updated: December 11, 2025*  
*Total: 1,050+ lines*


---

## Real-Time Observability

### AIMetricsService Pattern

The system uses an event-based metrics collection pattern to provide real-time visibility into RAG performance without adding latency.

**Metrics Captured per Query**:
1.  **Embedding Latency**: Time to vectorise user query.
2.  **Retrieval Latency**: Time to fetch documents from ChromaDB.
3.  **LLM Latency**: Time for Azure OpenAI to generate response.
4.  **Documents Retrieved**: Count of relevant chunks found.
5.  **Token Usage**: Input/Output tokens (used for cost calculation).
6.  **Cost**: Estimated cost in USD based on Azure pricing.

### Dashboard Integration

The gathered metrics are streamed to the Admin Dashboard (`/admin/ai-rag`) via the `AdminOrchestrator`.

-   **Scatter Plot**: Visualizes the relationship between Token Usage and Latency.
-   **Cost Estimator**: Tracks daily accumulation of AI spend.
-   **Latency Breakdown**: Helps identify bottlenecks (e.g., if Retrieval > LLM, optimize ChromaDB).

