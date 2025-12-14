# Internal API Architecture Guide

## Overview
This document provides a comprehensive mapping of all internal FastAPI endpoints, their implementation details, service dependencies, and data flows.

---

## API Endpoint Directory

### Authentication (`/auth`)
- `POST /auth/signup` - User registration
- `POST /auth/login` - User authentication (JWT + Device tracking)
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Revoke session
- `GET /auth/me` - Get current user & session info

### Stocks (`/stocks`)
- `GET /stocks/search` - Search for stocks
- `GET /stocks/{ticker}/data` - Get real-time stock data
- `GET /stocks/{ticker}/analysis` - Get AI-powered analysis (RAG)
- `GET /stocks/{ticker}/analysis-stream` - SSE Stream for analysis
- `GET /stocks/{ticker}/logs` - Get operation logs for ticker

### User Features (`/api`)
- `GET /api/watchlist` - Get user watchlist
- `POST /api/watchlist` - Add to watchlist
- `GET /api/favourites` - Get favourite stocks
- `POST /api/favourites` - Add to favourites
- `GET /api/history` - Get analysis history
- `POST /api/saved-analyses` - Save an analysis
- `GET /api/saved-analyses` - Get saved analyses

### Security (`/security`)
- `GET /security/login-history` - content: View login history
- `GET /security/active-sessions` - content: View active sessions
- `POST /security/revoke-session/{token_id}` - Revoke session
- `POST /security/revoke-all-sessions` - Revoke all sessions

### Admin (`/admin`)
- `POST /admin/ingest` - Trigger ingestion
- `GET /admin/users` - Manage users
- `GET /admin/stats` - System statistics
- `GET /admin/audit-logs` - View audit trails
- `GET /admin/system-toggles` - Manage feature flags
- `GET /admin/ip-blacklist` - Manage blocked IPs

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

**Purpose**: Authenticate user and issue JWTs with device tracking

**Request Schema**:
```python
{
    "email": "user@example.com",
    "password": "password123"
}
```

**Implementation Flow**:
```python
@router.post("/login")
def login(credentials: UserLogin, request: Request, db: Session):
    # 1. Verify credentials
    user = authenticate_user(db, credentials.email, credentials.password)
    if not user:
        # Log failed attempt
        record_login_history(user_id=None, status="failed", ...)
        raise HTTPException(401)
    
    # 2. Key Rotation Check
    current_key_id = get_current_key_id(db)
    
    # 3. Create Access Token (Short-lived: 15m)
    access_token = create_access_token(
        data={"sub": str(user.id), "kid": current_key_id}
    )
    
    # 4. Create Refresh Token (Long-lived: 7d)
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "kid": current_key_id}
    )
    
    # 5. Track Session
    store_refresh_token(db, user.id, refresh_token, device_info=...)
    record_login_history(user.id, status="success", ...)
    
    return {"access_token": access_token, "refresh_token": refresh_token}
```

**Features**:
- **Device Tracking**: Logs IP, User-Agent, Device Type
- **JWT Rotation**: Uses `kid` header for key rotation support
- **Session Management**: Stores refresh token hash in DB

---

### `POST /auth/refresh`

**Purpose**: Get new access token using refresh token

**Implementation**:
1. Validates refresh token signature
2. Checks if token exists in `refresh_tokens` table and is not revoked
3. Issues new access token
4. (Optional) Rotates refresh token

---

### `GET /auth/me`

**Purpose**: Get current user profile and session security info

**Response**:
```json
{
    "id": 1,
    "email": "user@example.com",
    "full_name": "Ashutosh",
    "security": {
        "mfa_enabled": false,
        "last_login": "2025-12-12T10:00:00",
        "active_sessions": 2
    }
}
```

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

**Purpose**: Get comprehensive AI-powered stock analysis (RAG Synthesis)

**Parameters**:
- `ticker`: Stock symbol
- `mode`: (Internal) Auto-selects "Synthesis" or "Baseline"

**RAG Logic Flow (Enhanced)**:
1. **Data Collection**:
   - Fetch real-time price & technicals (RSI, MACD, BB)
   - Fetch news (DuckDuckGo + RSS)
   - **Retrieve History**: Query ChromaDB `stock_analysis` for past analyses

2. **Prompt Engineering (2-Mode)**:
   - **Mode A: Synthesis** (If history > 0)
     - Compares Current vs Past metrics
     - Identifies Trajectory (Improving/Declining)
     - Validates past predictions
   - **Mode B: Baseline** (If no history)
     - Establishes initial benchmarks
     - Focuses on current setup

3. **Generation**:
   - Azure GPT-4 generates JSON analysis
   - Output includes: Summary, Reasoning, Prediction, Risk Factors, Key Insights

4. **Post-Processing**:
   - **Guardrails**: Sanitize forbidden phrases ("Buy", "Sell")
   - **Trend Analysis**: Analyze 30-day indicator trends
   - **Storage**: Save to `analysis_history` and ChromaDB `stock_analysis`

**Response**:
```json
{
    "ticker": "HAL",
    "analysis": "HAL shows strong momentum compared to last week...",
    "mode": "synthesis",
    "technical_analysis": {
        "rsi": 65.5,
        "trend_30d": "uptrend",
        "macd_signal": "bullish"
    },
    "prediction": {
        "outcome": "Bullish",
        "confidence": 0.85,
        "timeframe": "1-3 months"
    },
    "synthesis": {
        "price_change": "+5.2%",
        "sentiment_shift": "improved"
    }
}
```

---

### `GET /stocks/{ticker}/analysis-stream`

**File**: `backend/app/api/stocks.py`

**Purpose**: Real-time progress streaming (Server-Sent Events)

**Format**: `text/event-stream`

**Events**:
- `thinking`: Progress update (e.g., "Scanning news...", "Analyzing trends...")
- `result`: Final JSON payload

**Frontend Usage**:
```typescript
const eventSource = new EventSource(`/stocks/${ticker}/analysis-stream`);
eventSource.addEventListener("thinking", (e) => console.log(e.data));
eventSource.addEventListener("result", (e) => setData(JSON.parse(e.data)));
```
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

### `GET /admin/users`
**File**: `backend/app/api/admin_management.py`
**Purpose**: List all users (paginated)
**Response**: `[{id, email, is_active, last_login...}]`

### `POST /admin/users/{action}`
**Purpose**: Enable/Disable users
**Actions**: `enable`, `disable`

### `GET /admin/ip-blacklist`
**Purpose**: View blocked IPs
**Response**: `[{ip, reason, blocked_at, expires_at}]`

### `POST /admin/ip-blacklist/add`
**Purpose**: Block an IP address manually
**Body**: `{"ip": "1.2.3.4", "reason": "spam"}`

### `GET /admin/system-toggles`
**Purpose**: View/Manage feature flags (e.g., maintenance mode)
**Response**: `{"maintenance_mode": false, "registration_enabled": true}`

### `GET /admin/audit-logs`
**Purpose**: key admin actions (ban user, config change)
**Response**: `[{admin_email, action, target, timestamp}]`

---

## 6. User Feature Endpoints

### `GET /api/watchlist`
**File**: `backend/app/api/user_stocks.py`
**Purpose**: Get user's watchlist
**Response**: `[{ticker, current_price, added_at}]`

### `POST /api/watchlist`
**Purpose**: Add stock to watchlist
**Body**: `{"ticker": "HAL"}`

### `GET /api/history`
**Purpose**: Get user's analysis history
**Response**: `[{ticker, sentiment, created_at, analysis_summary}]`

### `POST /api/saved-analyses`
**Purpose**: Save a specific analysis for later reference
**Body**: `{"ticker": "HAL", "analysis_id": "..."}`

---

## 7. Security Endpoints

### `GET /security/login-history`
**File**: `backend/app/api/security.py`
**Purpose**: View recent login attempts for current user
**Response**: `[{timestamp, ip_address, device, status}]`

### `GET /security/active-sessions`
**Purpose**: View all active JWT sessions
**Response**: `[{token_id, device, created_at, expires_at, is_current}]`

### `POST /security/revoke-session/{token_id}`
**Purpose**: Remote logout a specific device
**Method**: Revokes the refresh token

---

## 8. Tracking Endpoints

### `GET /tracking/guest/check-limit`
**File**: `backend/app/api/tracking.py`
**Purpose**: Check remaining free analyses for guest IP
**Response**: `{"limit": 5, "used": 3, "remaining": 2}`

### `GET /tracking/user/check-limit`
**Purpose**: Check daily limit for logged-in user
**Response**: `{"tier": "free", "limit": 20, "used": 5}`


## 9. Service Layer Architecture

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

## 10. Database Interaction Summary

### Read Operations
| Endpoint | Tables Read | Purpose |
|----------|-------------|---------|
| `GET /stocks/{ticker}/analysis` | `analysis_cache`, `stock_analysis` (Chroma) | Check cache & retrieval |
| `GET /auth/login` | `users` | Verify credentials |
| `GET /api/watchlist` | `watchlist` | Fetch user stocks |
| `GET /security/login-history` | `login_history` | Audit logins |
| `GET /admin/users` | `users` | Admin listing |

### Write Operations
| Endpoint | Tables Written | Purpose |
|----------|----------------|---------|
| `POST /auth/signup` | `users` | Create user account |
| `POST /auth/login` | `login_history`, `refresh_tokens` | Log attempt, store session |
| `GET /stocks/{ticker}/analysis` | `analysis_cache`, `analysis_history` | Cache result, track history |
| `POST /api/watchlist` | `watchlist` | Add stock |
| `POST /security/revoke-session` | `refresh_tokens` | Mark revoked |

---

## 11. Performance Characteristics

| Endpoint | Avg Response Time | Cacheable | Heavy Operations |
|----------|-------------------|-----------|------------------|
| `GET /stocks/search` | 200-500ms | No | Finnhub API call |
| `GET /stocks/{ticker}/data` | 300-800ms | No | 1-4 API calls (fallback) |
| `GET /stocks/{ticker}/analysis` (no cache) | 15-30s | Yes (1h) | Scraping, embeddings, LLM |
| `GET /stocks/{ticker}/analysis` (cached) | <100ms | Yes (1h) | DB read only |
| `POST /admin/ingest` | 30-60s | No | Scraping, embeddings |
| `GET /admin/status` | 100-200ms | No | DB queries |

---

## 12. Error Handling Patterns

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

## 13. Testing Internal APIs

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

## 14. Dependency Injection

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
