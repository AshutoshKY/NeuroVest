# Logging Quick Reference Guide

## 🎯 Quick Start

### Configuration (.env file)

```bash
# Log Level (controls verbosity)
LOG_LEVEL=INFO          # Major milestones only
# LOG_LEVEL=DEBUG       # Detailed debug information

# Log Format
LOG_FORMAT=structured   # Detailed context fields
# LOG_FORMAT=simple     # Clean emoji-based format

# Other settings remain unchanged
DEBUG=True              # App debug mode (doesn't affect SQL logging anymore!)
```

---

## 📋 Log Format Reference

### Structured Format (Default)
```
TIMESTAMP | LEVEL | MODULE | [CONTEXT] MESSAGE

Example:
2025-12-05 20:48:35.751 | INFO | stocks | [req_id=a1b2c3d4, ticker=HAL, op=fetch_data, duration=250ms, status=success] ✅ Stock data fetched successfully
```

### Context Fields
- **req_id**: Request ID (first 8 chars) - use to trace entire request flow
- **ticker**: Stock ticker symbol
- **op**: Operation name (e.g., fetch_data, generate_analysis, ingest_for_ticker)
- **duration**: Time taken in milliseconds
- **status**: success/failure/cache_hit/cache_miss

---

## 🔍 Common Use Cases

### 1. Trace a Specific Request

Find the request ID from response headers or logs, then grep:
```bash
grep "req_id=abc12345" logs/app.log
```

You'll see the entire request flow from start to finish!

### 2. Debug Failed Analyses for a Ticker

```bash
grep "ticker=HAL" logs/app.log | grep "ERROR\|WARNING"
```

Shows all issues related to HAL stock.

### 3. Monitor API Performance

```bash
grep "duration=" logs/app.log | grep "op=fetch_data"
```

Shows how long each API call takes.

### 4. Check Cache Hit Rate

```bash
grep "cache_check" logs/app.log | grep "Cache HIT"
grep "cache_check" logs/app.log | grep "Cache MISS"
```

Compare counts to see cache effectiveness.

### 5. Track Ingestion Strategy Success

```bash
# Web Search success
grep "strategy=web_search" logs/app.log | grep "succeeded"

# RSS fallback triggers
grep "fallback=rss" logs/app.log
```

---

## 📊 Log Level Guidelines

### INFO Level (Recommended for Production)

Shows:
- ✅ Request received/sent
- ✅ Cache hits/misses
- ✅ API calls with timing
- ✅ Major operations (ingestion, analysis)
- ⚠️ Warnings (fallbacks, recoverable errors)
- ❌ Errors

**Doesn't show:**
- Document retrieval counts
- LLM parameters
- Internal service details

### DEBUG Level (For Development/Troubleshooting)

Shows **everything** INFO shows PLUS:
- 🔍 Document retrieval details
- 🔍 LLM call parameters and response structure
- 🔍 Technical analysis availability
- 🔍 Historical data presence
- 🔍 Cache operations with TTL
- 🔍 Detailed stack traces

---

## 🎨 Log Emojis Guide

- 📨 Incoming request
- 📤 Response sent
- 🔍 Search/lookup operation
- 📊 Data analysis/processing
- 📥 Data ingestion/download
- 📡 API call
- 🕵️ Web scraping
- ⚡ Cache hit (fast!)
- ❌ Cache miss / Error
- ⚠️ Warning / Fallback
- ✅ Success
- 🔄 Retry / Alternate strategy
- 🤖 LLM/AI operation
- 📄 Document processing

---

## 🛠️ Troubleshooting Examples

### Problem: "Analysis taking too long"

Check the logs for that ticker:
```bash
grep "ticker=SLOW_TICKER" logs/app.log
```

Look for:
1. `duration=` fields to see which step is slow
2. `Cache MISS` - maybe caching not working?
3. `strategy=web_search` - is web scraping timing out?

### Problem: "Getting errors for specific stock"

```bash
grep "ticker=PROBLEM_STOCK" logs/app.log | grep "ERROR"
```

The error log will show:
- Which operation failed (`op=...`)
- The error message (`error=...`)
- Request ID for full trace

### Problem: "Want to see what historical data was used"

```bash
grep "Generated analysis" logs/app.log
```

Output shows:
```
📊 Generated analysis for HAL with: technical indicators, 3 historical analyses, 30-day trends
```

---

## 📝 Example Log Flows

### Successful Analysis (Cache Hit)
```
INFO | request_middleware | [req_id=abc12345] 📨 Incoming request
INFO | redis_cache | [req_id=abc12345, ticker=HAL] ⚡ Cache HIT
INFO | request_middleware | [req_id=abc12345, status_code=200] 📤 Response sent
```
**Time: < 100ms**

### Successful Analysis (Cache Miss + Fresh Data)
```
INFO | request_middleware | [req_id=def67890] 📨 Incoming request
INFO | redis_cache | [req_id=def67890, ticker=BEL] ❌ Cache MISS
INFO | stocks | [req_id=def67890, ticker=BEL, op=ingest_for_ticker] 📥 Triggering on-demand ingestion
INFO | data_ingestion | [req_id=def67890, ticker=BEL, strategy=web_search, articles_count=8, status=success] ✅ Web Search scraper succeeded
INFO | stock_api_service | [req_id=def67890, ticker=BEL, provider=Finnhub, duration=180ms, status=success] ✅ Stock data fetched
INFO | rag | [req_id=def67890, ticker=BEL] 📊 Generated analysis with: technical indicators, 2 historical analyses
INFO | request_middleware | [req_id=def67890, status_code=200] 📤 Response sent
```
**Time: 2-5 seconds**

### Failed Analysis with Fallback
```
INFO | request_middleware | [req_id=ghi12345] 📨 Incoming request
INFO | data_ingestion | [req_id=ghi12345, ticker=NEW_STOCK, strategy=web_search] 🕵️ Trying Web Search scraper
ERROR | data_ingestion | [req_id=ghi12345, ticker=NEW_STOCK, strategy=web_search, fallback=rss, error=Timeout] ❌ Web Search failed
INFO | data_ingestion | [req_id=ghi12345, ticker=NEW_STOCK, strategy=rss] 📡 Trying RSS scraper
INFO | data_ingestion | [req_id=ghi12345, ticker=NEW_STOCK, strategy=rss, articles_count=5, status=success] ✅ RSS scraper succeeded
```

---

## 💡 Pro Tips

### 1. Request ID in API Responses

Every response includes `X-Request-ID` header:
```bash
curl -I http://localhost:8000/stocks/HAL/analysis
# Look for: X-Request-ID: abc12345-...
```

Use that ID to grep logs for the full request trace!

### 2. Monitor Logs in Real-Time

```bash
tail -f logs/app.log | grep "ticker=HAL"
```

Watch HAL-related logs live as requests come in.

### 3. Count Operations

```bash
# How many cache hits today?
grep "$(date +%Y-%m-%d)" logs/app.log | grep "Cache HIT" | wc -l

# How many analyses generated?
grep "Generated analysis" logs/app.log | wc -l
```

### 4. Find Slow Requests

```bash
# Find requests that took > 1 second (1000ms)
grep "duration=" logs/app.log | awk -F'duration=' '{print $2}' | awk -F'ms' '{if($1 > 1000) print}'
```

---

## 🚨 No More SQL Logs!

Previously, logs were filled with:
```
DEBUG SELECT * FROM stocks WHERE ticker = 'HAL'
DEBUG INSERT INTO analysis_cache ...
DEBUG SELECT operation_log ...
```

**Now:** SQL logging is completely disabled! Your logs only show application-level operations.

---

## 📚 Summary

| What You Want | How to Get It |
|---------------|---------------|
| Trace a request | `grep "req_id=abc12345" logs/app.log` |
| Debug a ticker | `grep "ticker=HAL" logs/app.log` |
| Check errors | `grep "ERROR" logs/app.log` |
| Monitor performance | `grep "duration=" logs/app.log` |
| See cache efficiency | `grep "cache_check" logs/app.log` |
| Watch live logs | `tail -f logs/app.log` |
| More detail | Set `LOG_LEVEL=DEBUG` |

**Your logs are now clean, searchable, and actionable!** 🎉
