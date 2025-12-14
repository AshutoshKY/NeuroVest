# Feature Flag Implementation Guide

## Overview

A **feature flag** (also called feature toggle) is a configuration setting that allows you to **turn features on/off without deploying new code**. 

For the Smart Orchestrator, it means:
- ✅ Deploy the new code to production
- ✅ Keep it **OFF** by default (safe)
- ✅ Turn it **ON** when ready (instant)
- ✅ Turn it **OFF** if problems (instant rollback)

---

## How It Works

### Step 1: Environment Variable

Add to `backend/.env`:
```bash
# Smart Orchestrator Feature Flag
USE_SMART_ORCHESTRATOR=false  # Default: OFF (safe)
```

To enable:
```bash
USE_SMART_ORCHESTRATOR=true   # Turn ON
```

### Step 2: Configuration Loading

**File**: `backend/app/core/config.py`

```python
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    # ... existing settings ...
    
    # NEW: Smart Orchestrator Feature Flag
    USE_SMART_ORCHESTRATOR: bool = Field(
        default=False,  # Safe default = OFF
        env="USE_SMART_ORCHESTRATOR",
        description="Enable smart multi-API orchestration with intelligent routing"
    )
    
    # Optional: Per-endpoint granular control
    SMART_ORCHESTRATOR_ENDPOINTS: str = Field(
        default="all",  # "all", "quotes_only", "analysis_only", etc.
        env="SMART_ORCHESTRATOR_ENDPOINTS"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

**What this does**:
- Reads `USE_SMART_ORCHESTRATOR` from `.env` file
- Defaults to `False` if not set (safety first!)
- Can be changed without redeploying code

---

### Step 3: Smart Routing in StockAPIService

**File**: `backend/app/services/stock_api_service.py`

**BEFORE** (Current Code):
```python
async def get_stock_data(self, ticker: str) -> Dict[str, Any]:
    """Get stock data for a ticker"""
    # Check cache first
    cache_key = f"stock_{ticker}"
    if cache_key in self.cache:
        # ... cache logic ...
        
    # Try each API in priority order
    for api in self.apis:
        try:
            data = await self._fetch_from_api(api, ticker)
            if data:
                return data
        except Exception as e:
            continue
    
    raise Exception(f"Failed to fetch data for {ticker}")
```

**AFTER** (With Feature Flag):
```python
async def get_stock_data(self, ticker: str) -> Dict[str, Any]:
    """
    Get stock data for a ticker.
    
    NEW: Routes to Smart Orchestrator if feature flag enabled.
    Otherwise, uses original implementation (100% backward compatible).
    """
    from app.core.config import settings
    
    # FEATURE FLAG CHECK
    if settings.USE_SMART_ORCHESTRATOR:
        # 🆕 NEW PATH: Smart Orchestrator
        logger.info(f"🚀 Using Smart Orchestrator for {ticker}")
        from app.services.smart_orchestrator import smart_orchestrator
        return await smart_orchestrator.get_stock_data_enhanced(ticker)
    
    # 🔙 LEGACY PATH: Original Implementation (UNCHANGED)
    logger.info(f"📦 Using Legacy API Service for {ticker}")
    
    # ---- ORIGINAL CODE BELOW (unchanged) ----
    cache_key = f"stock_{ticker}"
    if cache_key in self.cache:
        cached_data, cached_time = self.cache[cache_key]
        if datetime.now() - cached_time < timedelta(seconds=self.cache_ttl):
            logger.info(f"✅ Cache hit for {ticker}")
            return cached_data
    
    # Try each API in priority order
    for api in self.apis:
        try:
            logger.info(f"🔄 Trying {api['name']} for {ticker}")
            data = await self._fetch_from_api(api, ticker)
            if data:
                logger.info(f"✅ {api['name']} succeeded for {ticker}")
                self.cache[cache_key] = (data, datetime.now())
                return data
        except Exception as e:
            logger.warning(f"❌ {api['name']} failed for {ticker}: {e}")
            continue
    
    logger.error(f"❌ All APIs failed for {ticker}")
    raise Exception(f"Failed to fetch data for {ticker} from all providers")
```

**Key Points**:
1. **First 10 lines = NEW** (feature flag check)
2. **Rest = UNCHANGED** (original code preserved)
3. If flag is OFF → Uses original code path
4. If flag is ON → Routes to smart orchestrator

---

## Rollout Strategy

### Phase 1: Deploy with Flag OFF (Week 1)

```bash
# .env
USE_SMART_ORCHESTRATOR=false
```

**What happens**:
- New code is deployed
- Smart orchestrator code exists but is **NOT USED**
- System behaves exactly as before
- Zero risk

**Deploy**:
```bash
cd /Volumes/AshDrive/prjts/stockmarket/backend
docker-compose down
docker-compose build
docker-compose up -d
```

**Verify**: Check logs, should see "Using Legacy API Service"

---

### Phase 2: Test with Single Stock (Week 2)

**Granular Feature Flag** (optional):

```python
# app/core/config.py
class Settings(BaseSettings):
    # ... existing ...
    
    SMART_ORCHESTRATOR_TEST_TICKERS: List[str] = Field(
        default=[],
        env="SMART_ORCHESTRATOR_TEST_TICKERS"
    )
```

```bash
# .env
USE_SMART_ORCHESTRATOR=false  # Still off globally
SMART_ORCHESTRATOR_TEST_TICKERS=["RELIANCE", "TCS"]  # Test only these
```

**Modified routing**:
```python
async def get_stock_data(self, ticker: str) -> Dict[str, Any]:
    from app.core.config import settings
    
    # Check if this ticker is in test list
    is_test_ticker = ticker in settings.SMART_ORCHESTRATOR_TEST_TICKERS
    
    if settings.USE_SMART_ORCHESTRATOR or is_test_ticker:
        # Use smart orchestrator
        from app.services.smart_orchestrator import smart_orchestrator
        return await smart_orchestrator.get_stock_data_enhanced(ticker)
    
    # Use legacy
    # ... original code ...
```

**Benefits**:
- Test on specific stocks only
- Compare old vs new side-by-side
- Low risk

---

### Phase 3: Enable for All Users (Week 3+)

After testing confirms everything works:

```bash
# .env
USE_SMART_ORCHESTRATOR=true  # 🚀 ENABLED!
```

**Restart backend**:
```bash
docker-compose restart backend
```

**That's it!** No code deployment needed.

---

## Monitoring & Rollback

### Monitor in Real-Time

```bash
# Watch logs
docker logs -f backend_app | grep "Smart Orchestrator\|Legacy API"
```

**Expected output** (flag ON):
```
🚀 Using Smart Orchestrator for RELIANCE
✅ Smart Orchestrator succeeded (0.8s)
🚀 Using Smart Orchestrator for TCS
✅ Smart Orchestrator succeeded (1.2s)
```

**Expected output** (flag OFF):
```
📦 Using Legacy API Service for RELIANCE
✅ Alpha Vantage succeeded for RELIANCE
📦 Using Legacy API Service for TCS
✅ yfinance succeeded for TCS
```

---

### Instant Rollback (If Issues)

**Problem detected?**
```bash
# Edit .env
nano /Volumes/AshDrive/prjts/stockmarket/backend/.env

# Change:
USE_SMART_ORCHESTRATOR=false

# Restart (takes ~10 seconds)
docker-compose restart backend
```

**System immediately reverts to old behavior**. No code changes, no redeployment.

---

## Advanced: Per-Endpoint Control

**More granular control**:

```python
# app/core/config.py
class Settings(BaseSettings):
    # ... existing ...
    
    # Which endpoints use smart orchestrator?
    SMART_ORCHESTRATOR_FOR_QUOTES: bool = Field(default=False)
    SMART_ORCHESTRATOR_FOR_HISTORICAL: bool = Field(default=False)
    SMART_ORCHESTRATOR_FOR_SEARCH: bool = Field(default=False)
```

```python
# In stock_api_service.py

async def get_stock_data(self, ticker: str) -> Dict[str, Any]:
    """Quotes endpoint"""
    if settings.SMART_ORCHESTRATOR_FOR_QUOTES:
        return await smart_orchestrator.get_stock_data_enhanced(ticker)
    # ... original ...

async def get_stock_history(self, ticker: str, days: int) -> Dict:
    """Historical endpoint"""
    if settings.SMART_ORCHESTRATOR_FOR_HISTORICAL:
        return await smart_orchestrator.get_stock_history_enhanced(ticker, days)
    # ... original ...

async def search_symbol(self, query: str, country: str) -> List[Dict]:
    """Search endpoint"""
    if settings.SMART_ORCHESTRATOR_FOR_SEARCH:
        return await smart_orchestrator.search_symbol_enhanced(query, country)
    # ... original ...
```

**Benefits**:
- Enable smart orchestrator for quotes only
- Keep historical data using old method
- Gradual migration per feature

---

## Configuration Examples

### Example 1: Fully Disabled (Safe Default)
```bash
# .env
USE_SMART_ORCHESTRATOR=false
```
✅ Uses old code
✅ Zero risk
✅ Good for initial deployment

---

### Example 2: Enabled for Testing
```bash
# .env
USE_SMART_ORCHESTRATOR=false
SMART_ORCHESTRATOR_TEST_TICKERS=["RELIANCE", "TCS", "INFY"]
```
✅ Only these 3 stocks use smart orchestrator
✅ All others use old code
✅ Good for comparing behavior

---

### Example 3: Fully Enabled
```bash
# .env
USE_SMART_ORCHESTRATOR=true
```
✅ All stocks use smart orchestrator
✅ Maximum performance
✅ After successful testing

---

### Example 4: Granular Control
```bash
# .env
USE_SMART_ORCHESTRATOR=false
SMART_ORCHESTRATOR_FOR_QUOTES=true     # Use for real-time quotes
SMART_ORCHESTRATOR_FOR_HISTORICAL=false # Old method for historical
SMART_ORCHESTRATOR_FOR_SEARCH=false    # Old method for search
```
✅ Feature-by-feature rollout
✅ Mix old and new
✅ Maximum safety

---

## How This Protects You

### Scenario 1: Bug in Smart Orchestrator
**Problem**: Smart orchestrator has a bug, returns wrong data

**Solution**:
```bash
# Instant fix (30 seconds)
USE_SMART_ORCHESTRATOR=false
docker-compose restart backend
```
✅ System reverts to old code
✅ No broken analysis
✅ No downtime

---

### Scenario 2: Performance Issue
**Problem**: Smart orchestrator is slower than expected

**Solution**:
```bash
# Disable while investigating
USE_SMART_ORCHESTRATOR=false
docker-compose restart backend

# Fix smart orchestrator code
# Test locally

# Re-enable when ready
USE_SMART_ORCHESTRATOR=true
docker-compose restart backend
```

---

### Scenario 3: Gradual Rollout
**Strategy**: Enable for 10% of stocks first

```python
import random

async def get_stock_data(self, ticker: str) -> Dict[str, Any]:
    # 10% rollout based on ticker hash
    ticker_hash = hash(ticker) % 100
    use_smart = ticker_hash < 10  # 10% of stocks
    
    if settings.USE_SMART_ORCHESTRATOR and use_smart:
        return await smart_orchestrator.get_stock_data_enhanced(ticker)
    
    # 90% use old code
    # ... original ...
```

---

## Logging & Metrics

**Track which path is used**:

```python
from prometheus_client import Counter

legacy_calls = Counter('stock_api_legacy_calls_total', 'Calls to legacy API')
smart_calls = Counter('stock_api_smart_calls_total', 'Calls to smart orchestrator')

async def get_stock_data(self, ticker: str) -> Dict[str, Any]:
    if settings.USE_SMART_ORCHESTRATOR:
        smart_calls.inc()
        logger.info(f"🚀 [SMART] {ticker}")
        return await smart_orchestrator.get_stock_data_enhanced(ticker)
    else:
        legacy_calls.inc()
        logger.info(f"📦 [LEGACY] {ticker}")
        # ... original ...
```

**Grafana dashboard**:
- Legacy calls/min
- Smart calls/min
- Success rates for each
- Response times for each

---

## Code Changes Required

### Only 3 Files Need Minor Edits

1. **`app/core/config.py`** - Add 1 line
```python
USE_SMART_ORCHESTRATOR: bool = Field(default=False, env="USE_SMART_ORCHESTRATOR")
```

2. **`backend/.env`** - Add 1 line
```bash
USE_SMART_ORCHESTRATOR=false
```

3. **`app/services/stock_api_service.py`** - Add 5 lines at top of `get_stock_data()`
```python
from app.core.config import settings
if settings.USE_SMART_ORCHESTRATOR:
    from app.services.smart_orchestrator import smart_orchestrator
    return await smart_orchestrator.get_stock_data_enhanced(ticker)
# ... rest unchanged ...
```

**That's it!** Everything else is NEW code that doesn't affect existing functionality.

---

## Testing the Flag

###Test 1: Verify Flag OFF
```bash
# In .env
USE_SMART_ORCHESTRATOR=false

# Restart
docker-compose restart backend

# Test endpoint
curl http://localhost:8000/api/v1/stocks/info/RELIANCE.NS

# Check logs
docker logs backend_app | tail -20

# Should see: "📦 Using Legacy API Service"
```

### Test 2: Verify Flag ON
```bash
# In .env
USE_SMART_ORCHESTRATOR=true

# Restart
docker-compose restart backend

# Test same endpoint
curl http://localhost:8000/api/v1/stocks/info/RELIANCE.NS

# Check logs
docker logs backend_app | tail -20

# Should see: "🚀 Using Smart Orchestrator"
```

### Test 3: Toggle During Runtime
```bash
# Start with flag OFF
docker-compose restart backend

# Make request → uses legacy
curl http://localhost:8000/api/v1/stocks/info/TCS.NS

# Change flag to ON
nano backend/.env  # Set USE_SMART_ORCHESTRATOR=true

# Restart
docker-compose restart backend

# Make same request → now uses smart orchestrator
curl http://localhost:8000/api/v1/stocks/info/TCS.NS

# Verify in logs that path changed!
```

---

## Summary

**Feature Flag = Safety Switch**

| Aspect | Value |
|--------|-------|
| Deployment Risk | 🟢 ZERO (flag is OFF by default) |
| Rollback Time | ⚡ 30 seconds (change flag + restart) |
| Testing Strategy | 🎯 Gradual (test tickers → full rollout) |
| Code Changes | ✅ Minimal (3 files, ~10 lines) |
| Production Safety | 🛡️ Maximum (instant on/off) |

**You control everything via `.env` file - no code deployment needed!**

Ready to implement? 🚀
