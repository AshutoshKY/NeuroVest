# Finnhub Investigation Report

## Root Cause Identified ✅

**The Issue**: Finnhub's **free tier does NOT support Indian market data**

### Key Findings

#### ✅ What Works
1. **API Key is Valid**
   - Successfully returns data for US stocks (AAPL: $278.89)
   - Rate limit: 60 calls/minute ✅
   - 59 calls remaining after test
   
2. **Working Endpoints** (for US stocks):
   - `/quote` - Real-time quotes ✅
   - `/stock/profile2` - Company profiles ✅
   - `/search` - Symbol search ✅
   - Got 29,810 US symbols successfully ✅

#### ❌ What Doesn't Work

1. **Indian Stocks = HTTP 403 Forbidden**
   ```
   RELIANCE.NS → 403 Forbidden ❌
   RELIANCE.BO → 403 Forbidden ❌
   TCS.NS      → 403 Forbidden ❌
   ```

2. **Historical Candles = HTTP 403**
   - `/stock/candle` endpoint restricted
   - Error: "You don't have access to this resource"
   - Requires premium plan

3. **All Indian Ticker Formats Fail**:
   - ❌ `RELIANCE.NS` (NSE suffix) → 403
   - ❌ `RELIANCE.BO` (BSE suffix) → 403  
   - ⚠️ `RELIANCE` (no suffix) → 200 OK but price=0 (no data)
   - ⚠️ `NSE:RELIANCE` → 200 OK but price=0 (no data)

## Why This Happens

**Finnhub Free Tier Restrictions**:
- ✅ US markets: FREE
- ❌ International markets (including India): **PREMIUM ONLY**

From Finnhub documentation:
> "International stock data requires a premium subscription. Free tier supports US markets only."

## Impact on NeuroVest

**Current Configuration**:
```yaml
stock_apis:
  - name: "Finnhub"
    enabled: true
    priority: 1  # ← Highest priority API
    endpoints:
      quote: "/quote"
      company: "/stock/profile2"
```

**Current Behavior**:
1. User requests Indian stock (e.g., RELIANCE.NS)
2. System tries Finnhub first (priority 1)
3. Gets HTTP 403 Forbidden
4. Waits for 10-second timeout
5. Moves to next API (Alpha Vantage)
6. **Total waste: ~1 second per request**

**POC Results Confirm**:
- Finnhub: 0/20 success rate on Indian stocks
- Every request: HTTP 403
- 0.8 seconds wasted per stock

## Solutions

### Option 1: Disable Finnhub for Indian Stocks ✅ (Recommended)

**Configuration Change**:
```yaml
stock_apis:
  - name: "Finnhub"
    enabled: false  # ← Disable completely
    priority: 99
    description: "Free tier doesn't support Indian markets"
```

**Pros**:
- ✅ No wasted API calls
- ✅ Faster response time (save 0.8s per request)
- ✅ No cost
- ✅ Immediate implementation

**Cons**:
- Won't have Finnhub as backup (but it doesn't work anyway!)

### Option 2: Upgrade to Finnhub Premium

**Cost**: Unknown (need to check Finnhub pricing)

**What You Get**:
- ✅ Indian market data (.NS/.BO)
- ✅ Historical candles
- ✅ More rate limits
- ✅ Premium support

**Check Pricing**:
- Visit: https://finnhub.io/pricing
- Look for "International Markets" or "India" coverage

**Pros**:
- Professional data source
- Official SLA
- More comprehensive data

**Cons**:
- 💰 Monthly cost
- Might be expensive for MVP stage

### Option 3: Use Finnhub Selectively (IF you upgrade)

**If you upgrade to premium**, configure:
```python
# smart_api_orchestrator.py
def select_apis_for_stock(ticker, market_cap):
    apis = []
    
    # Only use Finnhub if PREMIUM plan enabled
    if FINNHUB_PREMIUM_ENABLED:
        apis.append("finnhub")
    
    # Always use yfinance for Indian stocks
    apis.append("yfinance")
    
    # Alpha Vantage for large cap
    if market_cap > 10000_crore:
        apis.append("alpha_vantage")
    
    return apis
```

## Recommendation

### Immediate Action: Disable Finnhub ✅

**Update `/Volumes/AshDrive/prjts/stockmarket/backend/config/sources.yaml`**:

```yaml
stock_apis:
  # Finnhub - DISABLED (free tier doesn't support India)
  - name: "Finnhub"
    enabled: false
    priority: 99
    base_url: "https://finnhub.io/api/v1"
    api_key_env: "FINNHUB_API_KEY"
    endpoints:
      quote: "/quote"
      company: "/stock/profile2"
      news: "/company-news"
    rate_limit_per_minute: 60
    timeout_seconds: 10
    description: "Real-time stock data (US only on free tier) - DISABLED"
    reason: "Free tier does not support Indian markets (.NS/.BO)"
    
  # yfinance - Now PRIMARY
  - name: "Yahoo Finance"
    enabled: true
    priority: 1  # ← Promoted to #1
    base_url: "https://query1.finance.yahoo.com/v8/finance/chart"
    ticker_suffix: ".NS"
    rate_limit_per_minute: 60
    timeout_seconds: 10
    description: "Free stock data API - BEST for Indian markets"
    
  # Alpha Vantage - SECONDARY (for large cap only)
  - name: "Alpha Vantage"
    enabled: true
    priority: 2
    base_url: "https://www.alphavantage.co/query"
    api_key_env: "ALPHA_VANTAGE_API_KEY"
    endpoints:
      quote: "function=GLOBAL_QUOTE"
      intraday: "function=TIME_SERIES_INTRADAY"
    rate_limit_per_minute: 5
    timeout_seconds: 15
    description: "Supplement for large-cap stocks (rate limited)"
    use_for: ["large_cap"]
    
  # Marketstack - DISABLED (100 calls/month unusable)
  - name: "Marketstack"
    enabled: false
    priority: 99
    base_url: "http://api.marketstack.com/v1"
    api_key_env: "MARKETSTACK_API_KEY"
    endpoints:
      eod: "/eod"
      intraday: "/intraday"
    rate_limit_per_minute: 10
    timeout_seconds: 10
    description: "DISABLED - 100 calls/month too restrictive"
```

**Impact**:
- ✅ Faster responses (save 0.8s per stock)
- ✅ No wasted API calls
- ✅ yfinance becomes primary (90% success rate!)
- ✅ Alpha Vantage as supplement (45% success for large cap)

---

## Testing After Configuration Change

Run POC again to confirm improvement:
```bash
cd /Volumes/AshDrive/prjts/stockmarket
export $(cat backend/.env | grep -E "ALPHA_VANTAGE_API_KEY" | xargs)
python3 poc_all_apis_comprehensive.py
```

**Expected Results**:
- Finnhub: Skipped (not called)
- yfinance: 90% success (same as before)
- Average response time: ~0.5s (vs 1.3s before)
- Speedup: 2.6x faster!

---

## Future: If You Upgrade to Premium

1. **Check Finnhub premium plans**:
   - Visit: https://finnhub.io/pricing
   - Look for plan that includes Indian markets
   
2. **Estimated Cost** (you'd need to verify):
   - Starter: $XX/month (may not include India)
   - Professional: $XX/month (likely includes India)
   - Enterprise: Custom pricing

3. **When to consider premium**:
   - ✅ If you need official data source with SLA
   - ✅ If you're generating revenue and can afford it
   - ✅ If you need historical candles (403 on free tier)
   - ✅ If you need corporate actions data
   
4. **Not worth it if**:
   - ❌ MVP stage (yfinance works great)
   - ❌ Limited budget
   - ❌ yfinance + Alpha Vantage cover your needs

---

## Summary

**Problem**: Finnhub free tier doesn't support Indian stocks

**Root Cause**: `.NS` and `.BO` suffixes return HTTP 403 Forbidden

**Proof**: 
- ✅ US stocks (AAPL) work perfectly
- ❌ All Indian stocks return 403
- ✅ API key is valid (not expired/blocked)
- ❌ Not a rate limit issue (60/min available)

**Solution**: Disable Finnhub in configuration

**Alternative**: Upgrade to Finnhub premium (if budget allows)

**Impact**: 
- Faster responses (0.8s saved per stock)
- yfinance becomes primary API (90% success!)
- Zero functional impact (Finnhub wasn't working anyway)

**Next**: Proceed to designing smart orchestrator with:
- yfinance as primary
- Alpha Vantage as supplement (large cap only)
- Finnhub excluded
- Marketstack excluded
