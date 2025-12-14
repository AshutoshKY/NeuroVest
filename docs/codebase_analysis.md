# NeuroVest Codebase Analysis - Stock API Integration Points

**Date**: 2025-12-12
**Purpose**: Deep analysis before implementing Smart API Orchestrator

---

## Executive Summary

**Critical Finding**: `StockAPIService` is HEAVILY integrated across the entire application:
- ✅ **9+ import locations** across services and API routes
- ✅ RAG system depends on it for technical indicators
- ✅ Data ingestion service uses it for initial stock data
- ✅ Multiple API endpoints call it directly
- ✅ Analysis pipeline requires historical data from it

**Risk Level**: 🔴 **HIGH** - Any breaking changes will cascade across entire system

**Recommended Approach**: **NON-BREAKING** enhancement with feature flag

---

## Integration Points Mapped

### 1. Core Service Files

#### `app/services/stock_api_service.py` (877 lines)
**Current Implementation**:
- Simple in-memory cache (5-minute TTL)
- Sequential waterfall fallback (API1 → API2 → API3 → API4)
- Methods used by OTHER services:
  - `get_stock_data(ticker)` - **MOST CRITICAL**
  - `get_stock_data_from_provider(ticker, provider_name)`
  - `get_stock_history(ticker, days)`
  - `get_historical_data(ticker, period)`
  - `search_symbol(query, country)`
  - `get_company_news(ticker)`

**Global Instance**:
```python
# Line 876
stock_api_service = StockAPIService()
```

---

### 2. Direct Consumers

#### A. `app/services/data_ingestion.py`
**Line 13**: `from app.services.stock_api_service import stock_api_service`

**Usage**:
- **Line 101**: `data = await stock_api_service.get_stock_data(ticker)`
  - Called in `fetch_stock_data()` method
  - Used during data ingestion pipeline
  - **CRITICAL**: Returns stock data for analysis

**Impact**: If `get_stock_data()` signature changes, data ingestion BREAKS

---

#### B. `app/services/rag.py` (913 lines)
**Line 184**: `from app.services.stock_api_service import stock_api_service`

**Usage**:
- **Line 189**: `historical_data = stock_api_service.get_historical_data(ticker, period="3mo")`
  - Used in `generate_analysis_with_steps()` - **CORE RAG FUNCTION**
  - Fetches 3-month historical data for technical analysis
  - **CRITICAL**: Technical indicators depend on this

**Impact**: RAG analysis pipeline BREAKS if historical data format changes

---

#### C. `app/api/stocks.py` (1212 lines)
**Multiple imports** at lines 100, 193, 357, 502, 593, 784, 955

**Usage Points**:
1. **Line 101**: `results = await stock_api_service.search_symbol(q, country)`
   - Search stocks endpoint
   
2. **Line 203**: `api_data = await stock_api_service.get_stock_data(clean_ticker)`
   - Get stock info endpoint (most used!)
   - Also at lines 388, 516
   
3. **Line 594**: `historical_data = await api_service.get_stock_history(ticker, days=5)`
   - Analysis endpoint
   - Also at line 785
   
4. **Line 637**: `multi_period_data = api_service.get_historical_data_multi_period(ticker)`
   - Multi-period historical for charts

**Impact**: Multiple user-facing API endpoints REL Y on StockAPIService

---

#### D. `app/services/health_monitor.py`
**Line 224**: `from app.services.stock_api_service import StockAPIService`
**Line 227**: `stock_service = StockAPIService()`
**Line 246**: `data = await stock_service.get_stock_data_from_provider(test_ticker, provider_name)`

**Usage**: Health check for API providers

**Impact**: Low (only for monitoring)

---

## Critical Dependencies

### Data Flow Diagram

```
User Request
    ↓
API Route (/api/stocks.py)
    ↓
StockAPIService.get_stock_data(ticker)
    ↓
    ├─→ Cache Check (5-min TTL)
    ├─→ API Waterfall (Finnhub → AV → MS → YF)
    └─→ Return Data
        ↓
    ├─→ RAG Service (for analysis)
    │   └─→ get_historical_data() for technical indicators
    │
    ├─→ Data Ingestion (for pipeline)
    │   └─→ fetch_stock_data() for initial data
    │
    └─→ Direct API Response
```

---

## Current StockAPIService Methods - Complete API

### Public Methods (MUST NOT BREAK)

1. **`async get_stock_data(ticker: str) -> Dict[str, Any]`**
   - Returns: `{ticker, exchange, current_price, previous_close, day_high, day_low, volume, currency, timestamp, provider}`
   - **Used by**: data_ingestion, stocks API, watchlist
   - **Critical**: YES

2. **`async get_stock_data_from_provider(ticker: str, provider_name: str) -> Dict[str, Any]`**
   - Returns: Same as above
   - **Used by**: health_monitor, specific provider testing
   - **Critical**: NO

3. **`async get_stock_history(ticker: str, days: int = 5) -> Dict`**
   - Returns: `{dates: [...], prices: [...], volumes: [...]}`
   - **Used by**: RAG analysis, API routes
   - **Critical**: YES

4. **`def get_historical_data(ticker: str, period: str = "3mo", interval: str = "1d") -> DataFrame`**
   - Returns: pandas DataFrame with OHLCV
   - **Used by**: RAG for technical indicators
   - **Critical**: YES

5. **`def get_historical_data_multi_period(ticker: str) -> Dict[str, DataFrame]`**
   - Returns: `{"1mo": df, "3mo": df, "6mo": df, "1y": df}`
   - **Used by**: Analysis charts
   - **Critical**: MEDIUM

6. **`async search_symbol(query: str, country: str = "All") -> List[Dict]`**
   - Returns: `[{ticker, name, exchange, sector}, ...]`
   - **Used by**: Search endpoint
   - **Critical**: MEDIUM

7. **`async get_company_news(ticker: str) -> List[Dict]`**
   - Returns: List of news items
   - **Used by**: Data ingestion for news
   - **Critical**: LOW

---

## Redis Already Running

**Confirmed**: User states "Redis, backend and SQL is running in docker"

**Current Redis Usage**:
- `app/core/redis_client.py` - Redis connection
- `app/services/redis_cache.py` - Analysis caching
- `app/api/stocks.py` - Stock info caching (1-hour TTL)

**Existing Cache Keys**:
- `stock_info:{ticker}` - 1-hour TTL (line 163, stocks.py)
- `analysis:{ticker}` - Redis cache for analysis

---

## Breaking Change Risk Assessment

### 🔴 HIGH RISK if we modify:
1. `get_stock_data()` return structure
2. `get_historical_data()` DataFrame columns
3. `get_stock_history()` return structure
4. Any method signature (parameters)

### 🟡 MEDIUM RISK if we modify:
1. Internal caching mechanism
2. API priority order
3. Timeout values

### 🟢 LOW RISK if we:
1. Add NEW methods
2. Add feature flags
3. Enhance existing methods WITHOUT changing signatures
4. Add parallel execution INTERNALLY

---

## Implementation Strategy - NON-BREAKING

### Phase 1: Add Smart Orchestrator as NEW SERVICE

**File**: `app/services/smart_orchestrator.py` (NEW)

**Approach**: Create WRAPPER around existing StockAPIService

```python
class SmartOrchestrator:
    def __init__(self):
        self.legacy_service = stock_api_service  # Use existing
        self.cache = MultiTierCache()
        self.health = APIHealthTracker()
        self.detector = MarketDetector()
        
    async def get_stock_data_smart(self, ticker: str) -> Dict:
        """
        New method - doesn't replace existing
        """
        # Smart logic here
        pass
```

### Phase 2: Feature Flag

**File**: `app/core/config.py`

```python
class Settings:
    # ... existing ...
    USE_SMART_ORCHESTRATOR: bool = Field(
        default=False,
        env="USE_SMART_ORCHESTRATOR"
    )
```

### Phase 3: Gradual Migration

**Modify**: `app/services/stock_api_service.py`

```python
async def get_stock_data(self, ticker: str) -> Dict[str, Any]:
    """Existing method - add smart routing"""
    
    # Feature flag check
    from app.core.config import settings
    if settings.USE_SMART_ORCHESTRATOR:
        from app.services.smart_orchestrator import smart_orchestrator
        return await smart_orchestrator.get_stock_data_smart(ticker)
    
    # FALLBACK: Original implementation (unchanged)
    cache_key = f"stock_{ticker}"
    # ... rest of original code ...
```

**Benefits**:
✅ Zero breaking changes
✅ Can toggle feature on/off
✅ Easy rollback if issues
✅ Test in production safely

---

## Testing Strategy

### 1. Unit Tests
- Test smart orchestrator independently
- Mock all API calls
- Verify return format matches original

### 2. Integration Tests
- Test with feature flag ON
- Ensure RAG still works
- Ensure data ingestion still works
- Ensure API endpoints return same format

### 3. Comparison Testing
```python
# Run both old and new, compare
old_result = await stock_api_service.get_stock_data_legacy(ticker)
new_result = await smart_orchestrator.get_stock_data_smart(ticker)

assert old_result.keys() == new_result.keys()
assert abs(old_result['current_price'] - new_result['current_price']) < 0.01
```

---

## Admin Dashboard Integration Points

### Health Tracking API Endpoints (NEW)

**File**: `app/api/admin.py` (NEW or extend existing)

```python
@router.get("/api/health")
async def get_api_health_status():
    """Get health status of all stock APIs"""
    return await health_tracker.get_all_health_stats()

@router.get("/api/health/{api_name}/{market}")
async def get_specific_api_health(api_name: str, market: str):
    """Get health of specific API for specific market"""
    return await health_tracker.get_health(f"{api_name}_{market}")

@router.post("/api/health/circuit-breaker/reset")
async def reset_circuit_breaker(api_name: str, market: str):
    """Manually reset circuit breaker"""
    await health_tracker.close_circuit(f"{api_name}_{market}")
    return {"status": "reset"}

@router.get("/api/stats/cache")
async def get_cache_stats():
    """Get cache hit/miss rates"""
    return await cache.get_stats()
```

---

## Documentation Requirements

### Files to Create/Update

1. **`README_SMART_ORCHESTRATOR.md`** (NEW)
   - Architecture overview
   - How it works
   - Configuration guide
   - Troubleshooting

2. **`docs/API_INTEGRATION.md`** (UPDATE)
   - Document new smart orchestrator
   - API health endpoints
   - Feature flag usage

3. **`docs/INTERNAL_API.md`** (UPDATE)
   - Smart orchestrator methods
   - Health tracker API
   - Cache layer API

4. **`docs/MIGRATION_GUIDE.md`** (NEW)
   - How to enable smart orchestrator
   - What changes
   - Rollback procedure

---

## Redis Data Structures

### Keys to Use

```python
# API Health Tracking
"api_health:{api_name}_{market}" → Hash
    {
        "total_calls": int,
        "successes": int,
        "failures": int,
        "success_rate": float,
        "circuit_open": bool,
        "last_failure": timestamp
    }

# Recent Failures (Sorted Set)
"failures:{api_name}_{market}" → ZSet
    {timestamp: failure_data_json}

# Cache (3-tier)
"stock:cache:{ticker}" → String (JSON)
    TTL: 300s (5 min fresh)
    
"stock:stale:{ticker}" → String (JSON)
    TTL: 3600s (1 hour stale)

# Trending Stocks
"trending:stocks" → ZSet
    {ticker: request_count}
```

---

## Next Steps - Implementation Order

1. ✅ **Complete analysis** (THIS DOCUMENT)
2. ⏭️ Create `smart_orchestrator.py` with NEW methods
3. ⏭️ Create `multi_tier_cache.py`
4. ⏭️ Create `api_health_tracker.py`
5. ⏭️ Create `market_detector.py`
6. ⏭️ Add feature flag to `config.py`
7. ⏭️ Modify `stock_api_service.py` with feature flag check
8. ⏭️ Create admin API endpoints
9. ⏭️ Write comprehensive tests
10. ⏭️ Update documentation
11. ⏭️ Deploy with flag OFF
12. ⏭️ Enable for test ticker
13. ⏭️ Monitor for 24 hours
14. ⏭️ Gradual rollout

---

## Conclusion

**Safe to Proceed**: YES, with feature flag approach

**Estimated Implementation**: 7-10 days

**Risk Mitigation**: Feature flag + wrapper pattern = zero breaking changes

**Review Status**: Ready for implementation

---

## Questions for User (Already Answered)

1. ✅ Redis running? → YES
2. ✅ API keys configured? → YES
3. ✅ Market preference? → INDIA primary, US secondary
4. ✅ Start implementation? → YES (with caution)

**Ready to implement!** 🚀
