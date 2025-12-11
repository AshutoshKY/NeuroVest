# Internal API Architecture Guide

## Overview
This document provides a comprehensive mapping of all internal FastAPI endpoints, their implementation details, service dependencies, and data flows.

---

## API Endpoint Directory

### Authentication (`/auth`)
- `POST /auth/signup` - User registration
- `POST /auth/login` - User authentication
- `GET /auth/me` - Get current user info

### Stocks (`/stocks`)
- `GET /stocks/search` - Search for stocks
- `GET /stocks/{ticker}/data` - Get real-time stock data
- `GET /stocks/{ticker}/analysis` - Get AI-powered analysis
- `GET /stocks/{ticker}/logs` - Get operation logs for ticker

### News (`/news`)
- `GET /news/feed` - Get general news feed
- `GET /news/{ticker}` - Get news for specific ticker

### Sentiment (`/sentiment`)
- `GET /sentiment/{ticker}` - Get sentiment for ticker
- `GET /sentiment/sector/{sector}` - Get sector sentiment

### Admin (`/admin`)
- `POST /admin/ingest` - Trigger manual data ingestion
- `GET /admin/status` - Get system status
- `GET /admin/errors` - Get recent errors
- `GET /admin/logs` - Get operation logs
- `GET /admin/stats` - Get system statistics
- `GET /admin/sources/{source_name}` - Get source details
- `DELETE /admin/logs` - Clear old logs

---

## 1. Authentication Endpoints

### `POST /auth/signup`

**File**: `backend/app/api/auth.py`

**Purpose**: Register new user account

**Request Schema**:
```python
{
    "email": "user@example.com",      # EmailStr, required
    "password": "password123",         # str, required
    "full_name": "John Doe"           # Optional[str]
}
```

**Implementation Flow**:
```python
@router.post("/signup")
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    # 1. Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    
    # 2. Hash password
    hashed_password = get_password_hash(user_data.password)  # Uses passlib bcrypt
    
    # 3. Create user record
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name
    )
    db.add(new_user)
    db.commit()
    
    # 4. Generate JWT token
    access_token = create_access_token(
        data={"sub": str(new_user.id), "email": new_user.email}
    )
    
    return {"access_token": access_token, "user_id": new_user.id}
```

**Services Called**:
- `app.core.security.get_password_hash()` - Password hashing
- `app.core.security.create_access_token()` - JWT generation

**Database Tables**:
- **INSERT**: `users` table

**Response**:
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "user_id": 1,
    "email": "user@example.com"
}
```

---

### `POST /auth/login`

**File**: `backend/app/api/auth.py`

**Purpose**: Authenticate existing user

**Implementation Flow**:
```python
@router.post("/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    # 1. Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()
    
    # 2. Verify password
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(401, "Incorrect email or password")
    
    # 3. Generate JWT
    access_token = create_access_token(...)
    
    return {"access_token": access_token}
```

**Services Called**:
- `app.core.security.verify_password()` - Password verification
- `app.core.security.create_access_token()` - JWT generation

**Database Tables**:
- **SELECT**: `users` table

---

## 2. Stock Endpoints

### `GET /stocks/search`

**File**: `backend/app/api/stocks.py`

**Purpose**: Search for stocks by name or ticker

**Query Parameters**:
- `query` (required): Search term (e.g., "HAL", "Reliance")

**Implementation**:
```python
@router.get("/search")
async def search_stocks(query: str):
    # Uses stock_api_service to search across multiple APIs
    results = await stock_api_service.search_stocks(query)
    return {"results": results}
```

**Services Called**:
- `app.services.stock_api_service.search_stocks()`
  - Calls Finnhub `/search` endpoint
  - Normalizes ticker symbols (removes `.NS`, `.BO`)
  - Filters results

**External APIs**:
- Finnhub Symbol Search API

**Response**:
```json
{
    "results": [
        {
            "ticker": "HAL",
            "name": "Hindustan Aeronautics Limited",
            "exchange": "NSE",
            "type": "Common Stock"
        }
    ]
}
```

---

### `GET /stocks/{ticker}/data`

**File**: `backend/app/api/stocks.py`

**Purpose**: Get real-time stock price and metrics

**Path Parameters**:
- `ticker`: Stock symbol (e.g., "HAL")

**Query Parameters**:
- `provider` (optional): Specific API to use ("Finnhub", "Alpha Vantage", etc.)

**Implementation Flow**:
```python
@router.get("/{ticker}/data")
async def get_stock_data(ticker: str, provider: Optional[str] = None):
    if provider:
        # Test specific provider
        data = await stock_api_service.get_stock_data_from_provider(ticker, provider)
    else:
        # Use priority-based fallback
        data = await data_ingestion_service.fetch_stock_data(ticker)
    
    return data
```

**Services Called**:
- `app.services.data_ingestion.fetch_stock_data()` - Main entry point
  - Calls `stock_api_service.get_stock_data()` with priority fallback:
    1. Try Finnhub
    2. Try Alpha Vantage
    3. Try Yahoo Finance
    4. Try Marketstack

**External APIs** (Priority order):
1. Finnhub API
2. Alpha Vantage API
3. Yahoo Finance (yahooquery)
4. Marketstack API

**Database Tables**:
- **INSERT**: `operation_logs` (tracks API call)
- **UPDATE**: `data_source_status` (updates success/failure)

**Response**:
```json
{
    "ticker": "HAL",
    "exchange": "NSE",
    "current_price": 4250.50,
    "previous_close": 4200.00,
    "day_high": 4300.00,
    "day_low": 4180.00,
    "volume": 1500000,
    "currency": "INR",
    "timestamp": "2025-12-04T10:15:00",
    "provider": "Finnhub",
    "historical_data": {
        "timestamps": [1701648000, 1701734400, ...],
        "closes": [4200, 4220, 4250],
        "volumes": [1400000, 1450000, 1500000]
    }
}
```

**Error Handling**:
- Returns 404 with descriptive message if provider fails
- Example: "Marketstack failed for RELICAB: Marketstack returned no data"

---

### `GET /stocks/{ticker}/analysis`

**File**: `backend/app/api/stocks.py`

**Purpose**: Get comprehensive AI-powered stock analysis (Most complex endpoint)

**Path Parameters**:
- `ticker`: Stock symbol

**Implementation Flow**:
```python
@router.get("/{ticker}/analysis")
async def get_stock_analysis(ticker: str):
    # 1. Fetch stock data (async)
    stock_data = await data_ingestion_service.fetch_stock_data(ticker)
    
    # 2. Fetch and process news (async)
    report = await data_ingestion_service.fetch_news_for_ticker(ticker)
    
    # 3. Generate RAG analysis
    analysis = rag_service.generate_analysis(
        query=f"Analyze {ticker} stock",
        ticker=ticker,
        n_results=10
    )
    
    # 4. Combine results
    return {**analysis, **stock_data}
```

**Services Called** (Sequential):

1. **Stock Data**:
   - `data_ingestion_service.fetch_stock_data()`
   - → `stock_api_service.get_stock_data()` (tries 4 APIs)

2. **News Scraping**:
   - `data_ingestion_service.fetch_news_for_ticker()`
   - → DuckDuckGo News search (100 results)
   - → Google RSS scraper (fallback)
   - → `preprocessing_service.clean_text()` (text cleaning)
   - → `preprocessing_service.chunk_text()` (500-char chunks)
   - → `embedding_service.embed_batch()` (Azure OpenAI or local)
   - → ChromaDB storage

3. **RAG Analysis**:
   - `rag_service.generate_analysis()`
   - → **Cache check** (1-hour TTL in `analysis_cache` table)
   - → `embedding_service.query_similar()` (semantic search in ChromaDB)
   - → `rag_service._format_context()` (prepare prompt)
   - → Azure OpenAI GPT-4 (generate analysis JSON)
   - → `sentiment_service.analyze_batch_sentiment()` (sentiment analysis)
   - → `sentiment_service.aggregate_sentiment()` (aggregate scores)
   - → `guardrails_service.process_analysis()` (add disclaimers)
   - → **Cache store** (save for 1 hour)

**External APIs Triggered**:
1. Stock API (Finnhub/Alpha Vantage/Yahoo/Marketstack)
2. DuckDuckGo News API
3. Google RSS Feed
4. Azure OpenAI Embeddings API
5. Azure OpenAI GPT-4 API

**Database Tables**:
- **SELECT**: `analysis_cache` (check for cached result)
- **INSERT**: `operation_logs` (log scraping, API calls)
- **UPDATE**: `data_source_status` (track scraper health)
- **INSERT**: ChromaDB `stock_market_news` collection
- **INSERT**: `analysis_cache` (store result)

**Response**:
```json
{
    "ticker": "HAL",
    "analysis": "Hindustan Aeronautics Limited shows strong fundamentals...",
    "reasoning": "Key drivers include recent defense contracts...",
    "prediction": "The outlook suggests potential upside if execution remains strong...",
    "risk_factors": [
        "Dependency on government contracts",
        "Project execution delays"
    ],
    "sentiment": {
        "classification": "bullish",
        "aggregate_score": 0.65,
        "confidence": 0.78,
        "individual_sentiments": [
            {"title": "HAL wins contract", "sentiment": "bullish", "score": 0.8}
        ]
    },
    "references": [
        {
            "source": "Economic Times",
            "url": "https://...",
            "timestamp": "2025-12-04",
            "ticker": "HAL"
        }
    ],
    "key_insights": [
        "Recent contract wins boost revenue visibility",
        "Strong order book provides stability"
    ],
    "current_price": 4250.50,
    "previous_close": 4200.00,
    "day_high": 4300.00,
    "day_low": 4180.00,
    "volume": 1500000,
    "currency": "INR",
    "disclaimer": "This is informational content only...",
    "cached": false,  // or true with cache_timestamp
    "cache_timestamp": "2025-12-04T10:00:00"
}
```

**Performance**:
- First request (no cache): ~15-30 seconds
- Cached request: <1 second
- Cache TTL: 1 hour

---

### `GET /stocks/{ticker}/logs`

**File**: `backend/app/api/stocks.py`

**Purpose**: Get operation logs for specific ticker

**Implementation**:
```python
@router.get("/{ticker}/logs")
def get_stock_logs(ticker: str, db: Session = Depends(get_db)):
    logs = db.query(OperationLog).filter(
        OperationLog.source.contains(ticker)
    ).order_by(OperationLog.timestamp.desc()).limit(50).all()
    
    return {"logs": [log.to_dict() for log in logs]}
```

**Database Tables**:
- **SELECT**: `operation_logs`

---

## 3. News Endpoints

### `GET /news/feed`

**File**: `backend/app/api/news.py`

**Purpose**: Get general news feed (recent articles)

**Implementation**:
```python
@router.get("/feed")
def get_news_feed(db: Session = Depends(get_db)):
    # Query ChromaDB for recent articles
    from app.services.embeddings import embedding_service
    
    # Get all recent documents (no filter)
    results = embedding_service.collection.get(limit=50)
    
    # Format as news feed
    articles = []
    for i, metadata in enumerate(results['metadatas']):
        articles.append({
            'title': results['documents'][i][:100],
            'source': metadata.get('source'),
            'ticker': metadata.get('ticker'),
            'url': metadata.get('url'),
            'timestamp': metadata.get('timestamp')
        })
    
    return {"articles": articles}
```

**Services Called**:
- `embedding_service.collection.get()` - ChromaDB query

**Database Tables**:
- **SELECT**: ChromaDB `stock_market_news` collection

---

### `GET /news/{ticker}`

**File**: `backend/app/api/news.py`

**Purpose**: Get news articles for specific ticker

**Implementation**:
```python
@router.get("/{ticker}")
def get_ticker_news(ticker: str):
    from app.services.embeddings import embedding_service
    
    # Query ChromaDB with ticker filter
    results = embedding_service.collection.get(
        where={"ticker": ticker},
        limit=50
    )
    
    return {"ticker": ticker, "articles": format_articles(results)}
```

**Services Called**:
- `embedding_service.collection.get()` - Filtered ChromaDB query

---

## 4. Sentiment Endpoints

### `GET /sentiment/{ticker}`

**File**: `backend/app/api/sentiment.py`

**Purpose**: Get sentiment analysis for ticker

**Implementation**:
```python
@router.get("/{ticker}")
def get_sentiment(ticker: str):
    from app.services.embeddings import embedding_service
    from app.services.sentiment import sentiment_service
    
    # 1. Get articles from ChromaDB
    results = embedding_service.query_similar(
        query_text=ticker,
        n_results=10,
        filter_metadata={"ticker": ticker}
    )
    
    # 2. Analyze sentiment
    sentiments = sentiment_service.analyze_batch_sentiment(
        results['documents'],
        ticker=ticker
    )
    
    # 3. Aggregate
    aggregate = sentiment_service.aggregate_sentiment(sentiments)
    
    return {
        "ticker": ticker,
        "sentiment": aggregate,
        "article_sentiments": sentiments
    }
```

**Services Called**:
- `embedding_service.query_similar()` - ChromaDB semantic search
- `sentiment_service.analyze_batch_sentiment()` - Azure OpenAI sentiment analysis
- `sentiment_service.aggregate_sentiment()` - Aggregate with guardrails

**External APIs**:
- Azure OpenAI GPT-4 (sentiment classification)

**Response**:
```json
{
    "ticker": "HAL",
    "sentiment": {
        "classification": "bullish",
        "aggregate_score": 0.65,
        "confidence": 0.78,
        "neutral_majority": false
    },
    "article_sentiments": [
        {
            "title": "HAL wins defense contract",
            "sentiment": "bullish",
            "score": 0.8,
            "confidence": 0.9
        }
    ]
}
```

---

## 5. Admin Endpoints

### `POST /admin/ingest`

**File**: `backend/app/api/admin.py`

**Purpose**: Manually trigger news scraping and ingestion

**Implementation**:
```python
@router.post("/ingest")
async def trigger_ingestion():
    report = await data_ingestion_service.run_ingestion_pipeline()
    
    return {
        "status": "success",
        "report": report.to_dict()
    }
```

**Services Called**:
- `data_ingestion_service.run_ingestion_pipeline()`
  - Loads all scrapers from `sources.yaml`
  - Runs DuckDuckGo scraper
  - Runs RSS scrapers in parallel
  - Processes and stores articles
  - Updates `data_source_status`

**External APIs**:
- DuckDuckGo News API
- Google RSS Feed
- Azure OpenAI Embeddings

**Database Tables**:
- **INSERT**: ChromaDB `stock_market_news`
- **INSERT**: `operation_logs`
- **UPDATE**: `data_source_status`

**Response**:
```json
{
    "status": "success",
    "message": "Data ingestion completed",
    "report": {
        "duration_seconds": 45.2,
        "total_articles": 150,
        "total_chunks": 450,
        "sources": [
            {
                "source": "DuckDuckGo News",
                "success": true,
                "articles_count": 100
            },
            {
                "source": "Google News RSS",
                "success": true,
                "articles_count": 50
            }
        ]
    }
}
```

---

### `GET /admin/status`

**File**: `backend/app/api/admin.py`

**Purpose**: Get comprehensive system health status

**Implementation**:
```python
@router.get("/status")
def get_system_status(db: Session = Depends(get_db)):
    # 1. Load configured scrapers
    scrapers = load_scrapers()
    scraper_status = []
    
    # 2. Get DB status for each scraper
    for scraper in scrapers:
        db_status = db.query(DataSourceStatus).filter(
            DataSourceStatus.source_name == scraper.name
        ).first()
        
        if db_status:
            scraper_status.append(db_status.to_dict())
        else:
            scraper_status.append({
                'source_name': scraper.name,
                'health_status': 'unknown'
            })
    
    # 3. Add DuckDuckGo (hardcoded)
    ddg_status = db.query(DataSourceStatus).filter(
        DataSourceStatus.source_name == "DuckDuckGo News"
    ).first()
    if ddg_status:
        scraper_status.append(ddg_status.to_dict())
    
    # 4. Get API status
    apis = load_api_configs()
    api_status = []
    for api in apis:
        db_status = db.query(DataSourceStatus).filter(
            DataSourceStatus.source_name == api['name']
        ).first()
        if db_status:
            api_status.append(db_status.to_dict())
    
    return {
        "scrapers": scraper_status,
        "apis": api_status,
        "vector_db": {
            "document_count": embedding_service.get_collection_count()
        }
    }
```

**Services Called**:
- `scraper_factory.load_scrapers()` - Load scraper configs
- `scraper_factory.load_api_configs()` - Load API configs
- `embedding_service.get_collection_count()` - ChromaDB count

**Database Tables**:
- **SELECT**: `data_source_status`

**Response**:
```json
{
    "scrapers": [
        {
            "source_name": "Google News RSS",
            "source_type": "scraper",
            "enabled": true,
            "health_status": "healthy",
            "success_rate": 100.0,
            "last_success": "2025-12-04T10:00:00",
            "avg_response_time_ms": 1200
        },
        {
            "source_name": "DuckDuckGo News",
            "health_status": "healthy",
            "success_rate": 100.0
        }
    ],
    "apis": [
        {
            "source_name": "Finnhub",
            "health_status": "healthy",
            "success_rate": 98.5,
            "avg_response_time_ms": 450
        }
    ],
    "vector_db": {
        "document_count": 4500
    }
}
```

---

### `GET /admin/errors`

**File**: `backend/app/api/admin.py`

**Purpose**: Get recent error logs

**Query Parameters**:
- `limit` (optional, default=10): Number of errors to return

**Implementation**:
```python
@router.get("/errors")
def get_errors(limit: int = 10, db: Session = Depends(get_db)):
    errors = db.query(OperationLog).filter(
        OperationLog.status == 'failure',
        OperationLog.timestamp >= datetime.now() - timedelta(days=7)
    ).order_by(OperationLog.timestamp.desc()).limit(limit).all()
    
    return {"errors": [e.to_dict() for e in errors]}
```

**Database Tables**:
- **SELECT**: `operation_logs` WHERE status='failure'

---

### `GET /admin/logs`

**File**: `backend/app/api/admin.py`

**Purpose**: Get recent operation logs

**Query Parameters**:
- `limit` (optional, default=50): Number of logs
- `operation_type` (optional): Filter by type (scrape, api_call, analysis)
- `source` (optional): Filter by source name

**Database Tables**:
- **SELECT**: `operation_logs`

---

### `GET /admin/stats`

**File**: `backend/app/api/admin.py`

**Purpose**: Get system-wide statistics

**Implementation**:
```python
@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    # Last 24 hours
    last_24h_start = datetime.now() - timedelta(days=1)
    
    total_ops = db.query(OperationLog).filter(
        OperationLog.timestamp >= last_24h_start
    ).count()
    
    successful = db.query(OperationLog).filter(
        OperationLog.timestamp >= last_24h_start,
        OperationLog.status == 'success'
    ).count()
    
    total_articles = db.query(func.sum(OperationLog.articles_count)).filter(
        OperationLog.timestamp >= last_24h_start,
        OperationLog.operation_type == 'scrape'
    ).scalar() or 0
    
    return {
        "last_24h": {
            "total_operations": total_ops,
            "successful_operations": successful,
            "total_articles": total_articles
        }
    }
```

**Database Tables**:
- **SELECT**: `operation_logs` (aggregations)

---

### `DELETE /admin/logs`

**File**: `backend/app/api/admin.py`

**Purpose**: Clear old operation logs

**Query Parameters**:
- `days` (optional, default=30): Delete logs older than N days

**Implementation**:
```python
@router.delete("/logs")
def clear_logs(days: int = 30, db: Session = Depends(get_db)):
    cutoff = datetime.now() - timedelta(days=days)
    
    deleted = db.query(OperationLog).filter(
        OperationLog.timestamp < cutoff
    ).delete()
    
    db.commit()
    
    return {"deleted": deleted}
```

**Database Tables**:
- **DELETE**: `operation_logs`

---

## 6. Service Layer Architecture

### Data Flow for Analysis Request

```
User Request → FastAPI → Service Layer → External APIs → Database
     ↓
[GET /stocks/HAL/analysis]
     ↓
[stocks.py:get_stock_analysis()]
     ↓
     ├→ [data_ingestion_service.fetch_stock_data()]
     │   └→ [stock_api_service.get_stock_data()]
     │       ├→ Try Finnhub API ✓
     │       └→ Log to operation_logs
     │
     ├→ [data_ingestion_service.fetch_news_for_ticker()]
     │   ├→ DuckDuckGo News API (100 articles)
     │   ├→ Google RSS Feed (fallback)
     │   ├→ [preprocessing_service.clean_text()]
     │   ├→ [preprocessing_service.chunk_text()]
     │   ├→ [embedding_service.embed_batch()]
     │   │   └→ Azure OpenAI Embeddings API
     │   └→ Store in ChromaDB
     │
     └→ [rag_service.generate_analysis()]
         ├→ Check analysis_cache (1h TTL)
         ├→ [embedding_service.query_similar()] → ChromaDB
         ├→ [_format_context()]
         ├→ Azure OpenAI GPT-4 API
         ├→ [sentiment_service.analyze_batch_sentiment()]
         │   └→ Azure OpenAI GPT-4 (sentiment)
         ├→ [sentiment_service.aggregate_sentiment()]
         ├→ [guardrails_service.process_analysis()]
         └→ Store in analysis_cache
```

---

## 7. Database Interaction Summary

### Read Operations
| Endpoint | Tables Read | Purpose |
|----------|-------------|---------|
| `GET /stocks/{ticker}/analysis` | `analysis_cache` | Check for cached analysis |
| `GET /admin/status` | `data_source_status` | Get scraper/API health |
| `GET /admin/logs` | `operation_logs` | Get operation history |
| `GET /admin/errors` | `operation_logs` | Get failed operations |
| `GET /auth/login` | `users` | Verify credentials |

### Write Operations
| Endpoint | Tables Written | Purpose |
|----------|----------------|---------|
| `POST /auth/signup` | `users` | Create user account |
| `GET /stocks/{ticker}/analysis` | `analysis_cache`<br>`operation_logs`<br>`data_source_status`<br>ChromaDB | Cache result<br>Log operations<br>Update health<br>Store embeddings |
| `POST /admin/ingest` | `operation_logs`<br>`data_source_status`<br>ChromaDB | Log scraping<br>Update health<br>Store articles |
| `DELETE /admin/logs` | `operation_logs` | Delete old logs |

---

## 8. Performance Characteristics

| Endpoint | Avg Response Time | Cacheable | Heavy Operations |
|----------|-------------------|-----------|------------------|
| `GET /stocks/search` | 200-500ms | No | Finnhub API call |
| `GET /stocks/{ticker}/data` | 300-800ms | No | 1-4 API calls (fallback) |
| `GET /stocks/{ticker}/analysis` (no cache) | 15-30s | Yes (1h) | Scraping, embeddings, LLM |
| `GET /stocks/{ticker}/analysis` (cached) | <100ms | Yes (1h) | DB read only |
| `POST /admin/ingest` | 30-60s | No | Scraping, embeddings |
| `GET /admin/status` | 100-200ms | No | DB queries |

---

## 9. Error Handling Patterns

### Stock Data Errors
```python
# Priority-based fallback
try:
    return await finnhub_api()
except Exception as e:
    try:
        return await alpha_vantage_api()
    except Exception as e:
        try:
            return await yahoo_api()
        except Exception as e:
            return await marketstack_api()
```

### Provider-Specific Testing Errors
```python
# Returns 404 with detailed message
try:
    data = await stock_api_service.get_stock_data_from_provider(ticker, provider)
except Exception as provider_error:
    raise HTTPException(
        status_code=404,
        detail=f"{provider} failed for {ticker}: {str(provider_error)}"
    )
```

### Analysis Errors
```python
# Graceful degradation - returns basic data even if AI fails
try:
    analysis = rag_service.generate_analysis(...)
except Exception as e:
    logger.error(f"Analysis failed: {e}")
    return {
        "analysis": "Analysis unavailable",
        "sentiment": {"classification": "neutral"},
        **stock_data  # Still return price data
    }
```

---

## 10. Testing Internal APIs

### Test Complete Flow
```bash
# 1. Search
curl "http://localhost:8000/stocks/search?query=HAL"

# 2. Get Price
curl "http://localhost:8000/stocks/HAL/data"

# 3. Get Analysis (triggers everything)
time curl "http://localhost:8000/stocks/HAL/analysis"

# 4. Get Analysis (cached - instant)
time curl "http://localhost:8000/stocks/HAL/analysis"
```

### Test Admin Endpoints
```bash
# Trigger ingestion
curl -X POST "http://localhost:8000/admin/ingest"

# Monitor status
curl "http://localhost:8000/admin/status"

# Check logs
curl "http://localhost:8000/admin/logs?limit=10"

# View errors
curl "http://localhost:8000/admin/errors"
```

---

## 11. Dependency Injection

All endpoints use FastAPI's dependency injection:

```python
# Database session
db: Session = Depends(get_db)

# JWT authentication (when implemented)
current_user: User = Depends(get_current_user)
```

**Service Instances** (Global singletons):
- `data_ingestion_service` - Data ingestion orchestration
- `stock_api_service` - Stock API integration
- `rag_service` - RAG analysis
- `embedding_service` - Vector embeddings
- `sentiment_service` - Sentiment analysis
- `guardrails_service` - Output validation
- `preprocessing_service` - Text processing

All services are instantiated in their respective files and imported as singletons.
