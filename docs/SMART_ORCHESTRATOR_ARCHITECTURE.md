# Smart API Orchestrator - Architecture & Integration Guide

**Version**: 2.0.0  
**Status**: Production Ready  
**Last Updated**: December 2025

---

## 📐 System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
│  Next.js Frontend → API Client → JWT Auth → Rate Limiter        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI GATEWAY                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Stock API Service (Entry Point)                         │  │
│  │  ┌─────────────────────────────────────────────────┐    │  │
│  │  │  Feature Flag Check: USE_SMART_ORCHESTRATOR     │    │  │
│  │  └─────────────────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
             ↙                                        ↘
┌─────────────────────────┐              ┌─────────────────────────┐
│   SMART ORCHESTRATOR    │              │    LEGACY PATH          │
│   (NEW - v2.0)          │              │    (Fallback)           │
├─────────────────────────┤              ├─────────────────────────┤
│ 1. Check Cache          │              │ Sequential API calls:   │
│    ├─ Memory (60s)     │              │ 1. Finnhub              │
│    ├─ Redis Fresh (5m) │              │ 2. Alpha Vantage        │
│    └─ Redis Stale (1h) │              │ 3. Marketstack          │
│                         │              │ 4. Yahoo Finance        │
│ 2. Market Detection     │              └─────────────────────────┘
│    ├─ US Market         │
│    └─ INDIA Market      │
│                         │
│ 3. Health Check         │
│    └─ Circuit Breaker   │
│                         │
│ 4. Parallel Execution   │
│    ├─ Task 1: Yahoo    │
│    └─ Task 2: Alpha    │
│                         │
│ 5. Data Merging         │
│    └─ Quality Scoring   │
│                         │
│ 6. Cache Storage        │
└─────────────────────────┘
```

### Component Interaction Flow

```mermaid
sequenceDiagram
    participant User
    participant API as FastAPI
    participant Flag as Feature Flag
    participant Smart as Smart Orchestrator
    participant Cache as Multi-Tier Cache
    participant Detector as Market Detector
    participant Health as Health Tracker
    participant APIs as External APIs
    participant Legacy as Legacy Service
    
    User->>API: GET /stocks/analyze?ticker=RELIANCE
    API->>Flag: Check USE_SMART_ORCHESTRATOR
    
    alt Smart Orchestrator Enabled
        Flag->>Smart: Route to Smart
        Smart->>Cache: Check cache (Memory/Redis)
        
        alt Cache Hit
            Cache-->>Smart: Return cached data
            Smart-->>User: Return (< 100ms)
        else Cache Miss
            Smart->>Detector: Detect market
            Detector-->>Smart: INDIA
            
            Smart->>Health: Check API health
            Health-->>Smart: Yahoo✓, Alpha✓
            
            par Parallel API Calls
                Smart->>APIs: Call Yahoo Finance
                Smart->>APIs: Call Alpha Vantage
            end
            
            APIs-->>Smart: Alpha: 0.3s, Yahoo: 0.5s
            Smart->>Smart: Merge data (quality scoring)
            Smart->>Cache: Store in cache
            Smart->>Health: Record success
            Smart-->>User: Return merged data (0.5s)
        end
    else Smart Orchestrator Disabled
        Flag->>Legacy: Route to Legacy
        Legacy->>APIs: Sequential calls
        APIs-->>Legacy: Data (1-2s)
        Legacy-->>User: Return data
    end
```

---

## 🔌 Integration Points

### 1. Stock API Service Integration

**File**: `backend/app/services/stock_api_service.py`

```python
async def get_stock_data(self, ticker: str) -> Dict[str, Any]:
    """
    Main entry point - routes to smart orchestrator if enabled.
    
    Integration: Feature flag check → Smart or Legacy
    """
    from app.core.config import settings
    
    if settings.USE_SMART_ORCHESTRATOR:
        # NEW PATH: Smart orchestrator
        from app.services.smart_orchestrator import smart_orchestrator
        return await smart_orchestrator.get_stock_data_enhanced(ticker)
    
    # LEGACY PATH: Original implementation
    return await self._get_stock_data_legacy(ticker)
```

**Key Points**:
- ✅ 100% backward compatible
- ✅ Single feature flag controls routing
- ✅ Legacy path completely unchanged
- ✅ Instant rollback capability

### 2. RAG System Integration

**Files**: `backend/app/services/rag.py`

```python
# Fetch stock data for analysis
stock_data = await stock_api_service.get_stock_data(ticker)
# ↑ Automatically uses smart orchestrator if enabled
# Returns same format, so RAG processing unchanged
```

**Integration Status**: ✅ **NO CHANGES NEEDED**
- RAG expects same data format
- Technical indicators still work
- Analysis pipeline unaffected

### 3. Analysis Pipeline Integration

**Files**: `backend/app/api/stocks.py`

```python
# Analysis endpoint
@router.post("/analyze")
async def analyze_stock(request: AnalysisRequest):
    # Fetches stock data internally
    data = await data_ingestion.fetch_stock_data(ticker)
    # ↑ Uses smart orchestrator if enabled
    # No code changes needed
```

**Integration Status**: ✅ **NO CHANGES NEEDED**
- Same API contracts
- Same return formats
- Existing tests still pass

### 4. Admin API Integration

**File**: `backend/app/main.py`

```python
from app.api import admin_orchestrator

# Register admin routes
app.include_router(
    admin_orchestrator.router,
    prefix="/admin/orchestrator",
    tags=["admin_orchestrator"]
)
```

**New Endpoints**:
- `GET /admin/orchestrator/health` - API health status
- `GET /admin/orchestrator/cache-stats` - Cache metrics
- `POST /admin/orchestrator/reset-breakers` - Circuit breaker reset

---

## 🗄️ Database & Cache Structure

### Redis Cache Structure

```
# Memory Cache (60s TTL)
cache:memory:{ticker} → {
    data: {stock_data},
    timestamp: 1234567890
}

# Redis Fresh Cache (300s TTL)
cache:fresh:{ticker} → {
    data: {stock_data},
    timestamp: 1234567890
}

# Redis Stale Cache (3600s TTL)  
cache:stale:{ticker} → {
    data: {stock_data},
    timestamp: 1234567890
}

# Health Tracking
health:{api_name}_{market} → {
    total: 100,
    successes: 85,
    failures: 15,
    circuit_open: false,
    last_check: 1234567890
}

# Circuit Breaker State
circuit:{api_name}_{market}:failures → [timestamp1, timestamp2, ...]
circuit:{api_name}_{market}:state → "open" | "closed"
```

### MySQL Tables (Unchanged)

```sql
-- No schema changes required
-- Existing tables work as-is:
-- - users
-- - analysis_cache
-- - sentiment_data
-- - news_articles
```

---

## 🔧 Configuration Management

### Environment Variables

```bash
# Feature Flag (Required)
USE_SMART_ORCHESTRATOR=true          # Enable smart orchestrator

# Timeouts
SMART_ORCHESTRATOR_TIMEOUT=5.0       # Parallel execution timeout (seconds)
PER_API_TIMEOUT=3.0                  # Individual API timeout

# Cache TTLs
CACHE_MEMORY_TTL=60                  # Memory cache (seconds)
CACHE_FRESH_TTL=300                  # Redis fresh cache (seconds)
CACHE_STALE_TTL=3600                 # Redis stale cache (seconds)

# Circuit Breaker
CIRCUIT_BREAKER_THRESHOLD=5          # Min failures to open circuit
CIRCUIT_BREAKER_WINDOW=300           # Time window (seconds)
CIRCUIT_BREAKER_RECOVERY=300         # Recovery time (seconds)
CIRCUIT_SUCCESS_THRESHOLD=0.3        # 30% success rate minimum

# API Keys (Existing)
FINNHUB_API_KEY=...
ALPHA_VANTAGE_API_KEY=...
MARKETSTACK_API_KEY=...
```

### API Strategy Configuration

**File**: `backend/app/services/smart_orchestrator.py`

```python
API_STRATEGY = {
    "US": {
        "primary": ["Finnhub", "Yahoo Finance"],
        "fallback": ["Marketstack"]
    },
    "INDIA": {
        "primary": ["Yahoo Finance", "Alpha Vantage"],
        "fallback": ["Marketstack"]
    }
}
```

**Customization**: Edit API_STRATEGY to change API selection per market.

---

## 📊 Monitoring & Observability

### Key Metrics to Monitor

1. **Performance Metrics**:
   - Stock data fetch time (target: <1s)
   - Total analysis time
   - Cache hit rate (target: >70%)
   
2. **Reliability Metrics**:
   - API success rate per provider
   - Circuit breaker state
   - Fallback usage rate

3. **Resource Metrics**:
   - Redis memory usage
   - API call count
   - Error rate

### Monitoring Endpoints

```bash
# Health check
curl http://localhost:8000/admin/orchestrator/health

# Response:
{
  "status": "success",
  "apis": [
    {
      "api": "Yahoo Finance",
      "market": "INDIA",
      "total_calls": 1250,
      "successes": 1125,
      "success_rate": 0.90,
      "circuit_open": false
    }
  ]
}

# Cache statistics
curl http://localhost:8000/admin/orchestrator/cache-stats

# Response:
{
  "memory_hits": 450,
  "redis_hits": 320,
  "hit_rate_percent": 78.5
}
```

### Log Patterns

**Success Pattern**:
```
🚀 [SMART] Using Smart Orchestrator for RELIANCE
📍 [SMART] Market: RELIANCE → INDIA
🎯 [SMART] Selected APIs: ['Yahoo Finance', 'Alpha Vantage']
✅ [SMART] Success: RELIANCE from Smart (Alpha Vantage) (0.49s)
```

**Failure Pattern**:
```
⚠️  [SMART] API config not found: yfinance
⚠️  [SMART] Falling back to legacy service
```

**Circuit Breaker Pattern**:
```
⛔ [CIRCUIT BREAKER] OPENED for finnhub_india
⛔ [SMART] Skipping Finnhub for INDIA (circuit open)
```

---

## 🧪 Testing Strategy

### Unit Tests

```bash
# Run smart orchestrator tests
docker exec stockmarket_backend pytest app/tests/test_smart_orchestrator.py -v

# Test coverage:
# - Market detection (US vs INDIA)
# - Cache functionality (3 tiers)
# - Health tracking
# - Circuit breaker
# - Data merging
# - Parallel execution
```

### Integration Tests

```bash
# Test with smart orchestrator ON
curl -X POST http://localhost:8000/stocks/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "RELIANCE"}'

# Check logs
docker logs stockmarket_backend | grep SMART

# Expected: "🚀 [SMART]" messages
```

### Performance Tests

```bash
# Measure response time
time curl -X POST http://localhost:8000/stocks/analyze \
  -d '{"ticker": "TCS"}'

# Expected: <1s for stock data
```

---

## 🚀 Deployment Guide

### Phase 1: Deploy with Flag OFF

```bash
# 1. Deploy code
git pull origin main
docker-compose build backend

# 2. Set flag OFF in .env
USE_SMART_ORCHESTRATOR=false

# 3. Start services
docker-compose up -d backend

# 4. Verify legacy mode
docker logs stockmarket_backend | grep "LEGACY\|SMART"
# Should see: [LEGACY] messages
```

### Phase 2: Enable for Testing

```bash
# 1. Enable flag
USE_SMART_ORCHESTRATOR=true

# 2. Restart
docker-compose restart backend

# 3. Test specific stock
curl -X POST http://localhost:8000/stocks/analyze \
  -d '{"ticker": "RELIANCE"}'

# 4. Monitor logs
docker logs -f stockmarket_backend | grep SMART
```

### Phase 3: Production Rollout

```bash
# 1. Monitor for 24 hours
# 2. Check metrics dashboard
# 3. Verify no errors
# 4. If stable → keep enabled
# 5. If issues → instant rollback
```

### Emergency Rollback (<30 seconds)

```bash
# 1. Edit .env
nano backend/.env
# Change: USE_SMART_ORCHESTRATOR=false

# 2. Restart
docker-compose restart backend

# System immediately reverts to legacy mode
```

---

## 🔍 Troubleshooting

### Issue: Smart Orchestrator Not Working

**Symptoms**:
- Logs show `[LEGACY]` instead of `[SMART]`
- Stock data slow

**Solution**:
```bash
# Check flag
grep USE_SMART_ORCHESTRATOR backend/.env

# Restart backend
docker-compose restart backend

# Verify
curl http://localhost:8000/admin/orchestrator/config
```

### Issue: All APIs Circuit-Broken

**Symptoms**:
- Getting stale cache warnings
- High error rate

**Solution**:
```bash
# Check health
curl http://localhost:8000/admin/orchestrator/health

# Reset circuits
curl -X POST http://localhost:8000/admin/orchestrator/reset-breakers
```

### Issue: Cache Not Working

**Symptoms**:
- Every request hits APIs
- Low cache hit rate

**Solution**:
```bash
# Check Redis
docker exec stock market_redis redis-cli PING

# Check cache stats
curl http://localhost:8000/admin/orchestrator/cache-stats

# Clear cache if needed
docker exec stockmarket_redis redis-cli FLUSHALL
```

---

## 📈 Performance Optimization

### Current Performance (v2.0)

- Stock data: **0.5s** ✅
- Total analysis: **47s** (sentiment + LLM dominant)

### Optimization Opportunities

1. **Parallelize Sentiment** (~20s savings):
   ```python
   # Current: Sequential scraping
   # Proposed: Parallel scraping with asyncio
   ```

2. **Cache Historical Data** (~2s savings):
   ```python
   # Cache historical OHLCV data
   # TTL: 1 hour for daily data
   ```

3. **Faster LLM** (~5s savings):
   ```python
   # Current: GPT-4 (11.2s)
   # Proposed: GPT-4o-mini (6-7s)
   ```

---

## 🎯 Production Checklist

- [x] Smart orchestrator implemented
- [x] Unit tests passing
- [x] Integration tests passing
- [x] Bug fixes applied (recursion, API mapping, division by zero)
- [x] Documentation complete
- [x] Feature flag working
- [x] Monitoring endpoints active
- [ ] Load testing completed
- [ ] Production deployment approved
- [ ] Rollback procedure tested

---

**Architecture & Integration Guide - Smart API Orchestrator v2.0**  
**Status**: Production Ready ✅  
**Contact**: NeuroVest Team
