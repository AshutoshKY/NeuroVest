# NeuroVest - Market-Grade Stock Analysis Platform

**A deterministic, auditable, and backtestable AI-driven decision-support system for serious traders and investors.**

---

## What This Is

NeuroVest is **not** another LLM stock tipster. It is a **market-grade probabilistic state machine** that:

- Computes signals deterministically from market data
- Generates bounded scenarios with validated probabilities
- Locks LLM to narrative rendering only (cannot generate predictions)
- Enforces strict validation to prevent drift
- Enables backtesting for continuous calibration

**This system earns trust through structure, not storytelling.**

---

## Why This Architecture Exists

### The Problem with LLM-First Approaches

Traditional LLM-driven stock analysis tools suffer from:

❌ **Non-Deterministic Output** - Same input produces different results  
❌ **Narrative Drift** - LLM introduces indicators/fundamentals not in signals  
❌ **No Accountability** - Cannot backtest AI-generated predictions  
❌ **Illusory Confidence** - LLM sounds authoritative without being accurate  
❌ **Compliance Risk** - Uncontrolled language may imply investment advice

### Our Solution

✅ **Deterministic Computation** - Signal engines produce repeatable results  
✅ **Strict Separation** - LLM renders narratives from structured data only  
✅ **Validator-Enforced Constraints** - Forbidden terms blocked, drift detected  
✅ **Backtestable Architecture** - Every scenario tracked against outcomes  
✅ **Explainable Reasoning** - Metadata shows derivation of every number

---

## System Architecture (High-Level)

```
┌─────────────────────────────────────────────────────────────────┐
│                        MARKET DATA APIs                          │
│              (OHLCV, Volume, News, Sentiment)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
         ┌──────▼──────┐          ┌──────▼──────┐
         │ SIGNAL      │          │ SENTIMENT   │
         │ ENGINE      │          │ ENGINE      │
         └──────┬──────┘          └──────┬──────┘
                │                        │
                ├────────────────────────┤
                │                        │
         ┌──────▼──────┐          ┌──────▼──────┐
         │ PRICE       │          │ RISK        │
         │ ENGINE      │          │ SCORING     │
         └──────┬──────┘          └──────┬──────┘
                │                        │
                └────────────┬───────────┘
                             │
                      ┌──────▼──────┐
                      │ SCENARIO    │
                      │ ENGINE      │
                      │ (DETERMINISTIC)
                      └──────┬──────┘
                             │
                ┌────────────┴────────────┐
                │                         │
         ┌──────▼──────┐          ┌──────▼──────┐
         │ BACKTESTING │          │ LLM         │
         │ SNAPSHOT    │          │ RENDERER    │
         └──────┬──────┘          └──────┬──────┘
                │                        │
                │                 ┌──────▼──────┐
                │                 │ NARRATIVE   │
                │                 │ VALIDATOR   │
                │                 └──────┬──────┘
                │                        │
                └────────────┬───────────┘
                             │
                      ┌──────▼──────┐
                      │   STORAGE   │
                      │  (ChromaDB) │
                      └─────────────┘
```

---

## Key Design Principles

### 1. **Computation Before Narrative**

Signals → Scenarios → Risk Scores → Structured JSON → LLM Rendering

The LLM **never** makes decisions. It **only** explains them.

### 2. **Deterministic at Core**

Same market data + Same configuration = **Same scenarios, Same probabilities**

This enables:
- Repeatability
- Backtesting
- Debugging
- Trust

### 3. **Validator-Enforced Constraints**

LLM output is checked for:
- Forbidden terms (indicators, fundamentals, advice)
- Price references outside valid zones
- Scenario probability mismatches
- Contradictions to signal bias

**Invalid output is rejected** (Phase 2 enforcement)

### 4. **Backtestable by Design**

Every scenario prediction is:
- Stored with timestamp and market context
- Tracked against realized outcomes
- Measured for accuracy
- Used to calibrate future predictions

---

## What Makes This Market-Grade

| Criterion | NeuroVest | Typical LLM Tool |
|-----------|-----------|------------------|
| **Deterministic** | ✅ Yes | ❌ No |
| **Explainable** | ✅ Metadata shows derivation | ❌ Black box |
| **Backtestable** | ✅ Scenarios vs outcomes tracked | ❌ Cannot validate |
| **Validator-Enforced** | ✅ Drift/terms blocked | ❌ Uncontrolled |
| **Probability Sum** | ✅ Always = 1.0 | ❌ Often inconsistent |
| **LLM Role** | ✅ Renderer only | ❌ Decision-maker |
| **Trust Mechanism** | ✅ Structure + validation | ❌ Confidence in tone |

---

## Quick Start

### Prerequisites

```bash
# Environment
Python 3.9+
Docker + Docker Compose

# Services
PostgreSQL (user data)
Redis (caching)
ChromaDB (vector storage)
```

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/neurovest.git
cd neurovest

# Start services
docker-compose up -d

# Install dependencies
cd backend
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start API server
uvicorn app.main:app --reload --port 8000
```

### First Analysis

```bash
# Example: Analyze RELIANCE stock
curl -X POST "http://localhost:8000/api/v1/analysis/RELIANCE" \
  -H "Content-Type: application/json"
```

---

## Data Flow (Simplified)

1. **Market Data Ingestion** (OHLCV + Volume)
2. **Technical Indicator Calculation** (RSI, MACD, SMA, ATR)
3. **Signal Classification** (Trend, Momentum, Volatility, Structure)
4. **Risk Aggregation** (6 risk components → normalized score)
5. **Scenario Generation** (Deterministic probabilities, triggers, invalidation)
6. **Backtesting Snapshot** (Store for outcome tracking)
7. **RAG Retrieval** (Historical analyses, news)
8. **LLM Rendering** (Narrativegeneration from structured JSON)
9. **Narrative Validation** (Forbidden terms, drift detection)
10. **Response Return** (Structured + Narrative)

---

## Core Engines (Overview)

### 1. Signal Engine
- **Input**: OHLCV data
- **Output**: Directional bias, confidence, momentum state
- **Deterministic**: Yes

### 2. Scenario Engine
- **Input**: Signal summary, price zones, conflicts, risk score
- **Output**: 2-4 scenarios with probabilities (sum = 1.0)
- **Deterministic**: Yes

### 3. Risk Engine
- **Input**: Signals, market context, sentiment, sector RS
- **Output**: 0-100 risk score with breakdown
- **Components**: 6 (trend, volatility, market, sector, conflicts, news)

### 4. Price Engine
- **Input**: OHLCV data
- **Output**: Support/resistance/value zones
- **Used By**: Scenario triggers, LLM context

### 5. Sentiment Engine
- **Input**: News articles (RSS + scraping)
- **Output**: Aggregate sentiment score (-1 to +1)
- **Used By**: Risk engine (news_risk component)

### 6. Narrative Validator
- **Input**: LLM output + Structured state
- **Output**: Pass/Fail + Error list
- **Checks**: Forbidden terms, drift, price zones, probabilities

### 7. Backtesting Engine
- **Input**: Scenarios + outcomes
- **Output**: Performance metrics, calibration recommendations
- **Purpose**: Continuous improvement

---

## What This System Does NOT Do

❌ **Give Investment Advice** - Provides analysis, not recommendations  
❌ **Guarantee Outcomes** - Markets are probabilistic, not predictable  
❌ **Replace Due Diligence** - Tool for informed decisions, not autopilot  
❌ **Override User Judgment** - Augments analysis, doesn't replace trader  
❌ **Predict Exact Prices** - Generates bounded scenarios, not point forecasts

---

## Documentation Index

For detailed information, see:

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - System architecture, module design
- **[DATA_FLOW.md](./DATA_FLOW.md)** - End-to-end data pipeline
- **[ENGINES.md](./ENGINES.md)** - Engine-by-engine deep dive
- **[BEFORE_AFTER.md](./BEFORE_AFTER.md)** - Redesign impact analysis
- **[BACKTESTING.md](./BACKTESTING.md)** - Backtesting guide
- **[API_DOCUMENTATION.md](./API_DOCUMENTATION.md)** - API reference
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Production deployment guide

---

## Known Limitations

1. **Relative Strength** - Currently uses placeholder (1.0) values. Actual vs-index/vs-sector calculation planned.
2. **Narrative Validation** - Phase 1 (logging only). Phase 2 will enforce regeneration on failure.
3. **Backtesting Storage** - In-memory (MVP). Database persistence planned for production.
4. **Test Coverage** - Core engines 80%+, integration tests partial. Expanding coverage ongoing.

---

## Technical Stack

**Backend**: FastAPI, Python 3.9+  
**Vector DB**: ChromaDB  
**Database**: PostgreSQL  
**Cache**: Redis  
**LLM**: OpenAI GPT-4  
**Containerization**: Docker + Docker Compose

---

## License

[Your License Here]

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

---

## Contact

**Maintainer**: [Your Name]  
**Email**: [Your Email]  
**Issues**: [GitHub Issues Link]

---

**This system converts "AI magic" into "engineering discipline."**
