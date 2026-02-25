<p align="center">
  <img src="frontend/public/neurovest-logo.jpg" alt="NeuroVest Logo" width="120" />
</p>

<h1 align="center">NeuroVest</h1>
<p align="center"><b>AI-Powered Stock Analysis Platform for the Indian Market</b></p>

<p align="center">
  <img src="https://img.shields.io/badge/version-2.0-blue.svg" />
  <img src="https://img.shields.io/badge/architecture-Hybrid--RAG-purple.svg" />
  <img src="https://img.shields.io/badge/security-Defense--in--Depth-green.svg" />
  <img src="https://img.shields.io/badge/engines-7--Core-orange.svg" />
  <img src="https://img.shields.io/badge/databases-3--Tier-red.svg" />
  <img src="https://img.shields.io/badge/license-MIT-brightgreen.svg" />
</p>

<p align="center">
  <i>NeuroVest is a <b>"Glass Box AI"</b> — it doesn't ask the AI what to think.<br/>
  It <b>tells</b> the AI what to think, using mathematically computed scenarios, risk scores, and price zones.<br/>
  The LLM is a <b>renderer</b>, not a decision-maker.</i>
</p>

---

## 📸 Screenshots

> *Click any thumbnail to view full size*

<details>
<summary><b>🏠 Landing Page & Auth</b> · <b>📊 Dashboard</b> · <b>🧠 Analysis</b> · <b>⚙️ Settings</b> · <b>🛡️ Admin</b></summary>

#### Landing & Authentication
<p>
  <a href="docs/screenshots/4-46-59_AM.png"><img src="docs/screenshots/4-46-59_AM.png" width="150" alt="Landing Page" /></a>
  <a href="docs/screenshots/4-48-21_AM.png"><img src="docs/screenshots/4-48-21_AM.png" width="150" alt="Login" /></a>
  <a href="docs/screenshots/4-48-32_AM.png"><img src="docs/screenshots/4-48-32_AM.png" width="150" alt="Sign Up" /></a>
</p>

#### Dashboard & Watchlist
<p>
  <a href="docs/screenshots/4-49-47_AM.png"><img src="docs/screenshots/4-49-47_AM.png" width="150" alt="Dashboard" /></a>
  <a href="docs/screenshots/4-49-57_AM.png"><img src="docs/screenshots/4-49-57_AM.png" width="150" alt="Search" /></a>
  <a href="docs/screenshots/4-53-28_AM.png"><img src="docs/screenshots/4-53-28_AM.png" width="150" alt="Watchlist" /></a>
</p>

#### AI Analysis Pipeline
<p>
  <a href="docs/screenshots/4-50-44_AM.png"><img src="docs/screenshots/4-50-44_AM.png" width="150" alt="Analysis Input" /></a>
  <a href="docs/screenshots/4-50-54_AM.png"><img src="docs/screenshots/4-50-54_AM.png" width="150" alt="Processing" /></a>
  <a href="docs/screenshots/4-51-45_AM.png"><img src="docs/screenshots/4-51-45_AM.png" width="150" alt="Live Logs" /></a>
  <a href="docs/screenshots/4-52-09_AM.png"><img src="docs/screenshots/4-52-09_AM.png" width="150" alt="Results 1" /></a>
  <a href="docs/screenshots/4-52-19_AM.png"><img src="docs/screenshots/4-52-19_AM.png" width="150" alt="Results 2" /></a>
  <a href="docs/screenshots/4-52-27_AM.png"><img src="docs/screenshots/4-52-27_AM.png" width="150" alt="Results 3" /></a>
</p>

#### Settings & Docs
<p>
  <a href="docs/screenshots/4-50-08_AM.png"><img src="docs/screenshots/4-50-08_AM.png" width="150" alt="Settings" /></a>
  <a href="docs/screenshots/4-50-26_AM.png"><img src="docs/screenshots/4-50-26_AM.png" width="150" alt="Documentation" /></a>
</p>

#### Admin Command Center
<p>
  <a href="docs/screenshots/5-06-34_AM.png"><img src="docs/screenshots/5-06-34_AM.png" width="150" alt="Admin Overview" /></a>
  <a href="docs/screenshots/5-06-55_AM.png"><img src="docs/screenshots/5-06-55_AM.png" width="150" alt="Traffic" /></a>
  <a href="docs/screenshots/5-07-11_AM.png"><img src="docs/screenshots/5-07-11_AM.png" width="150" alt="Security" /></a>
  <a href="docs/screenshots/5-07-22_AM.png"><img src="docs/screenshots/5-07-22_AM.png" width="150" alt="Users" /></a>
  <a href="docs/screenshots/5-07-31_AM.png"><img src="docs/screenshots/5-07-31_AM.png" width="150" alt="Kill Switches" /></a>
  <a href="docs/screenshots/5-07-42_AM.png"><img src="docs/screenshots/5-07-42_AM.png" width="150" alt="User Intel" /></a>
</p>

</details>

---

## 🛠️ Tech Stack

### Backend

| Technology | Purpose |
|-----------|--------|
| **FastAPI** (Python 3.11) | High-performance async API framework |
| **Azure OpenAI GPT-4** | AI-powered stock analysis & narrative generation |
| **ChromaDB** | Vector database for semantic search & RAG |
| **MySQL 8.0** | Relational database (18 tables) |
| **Redis 7** | Caching, rate limiting, JWT key storage |
| **Sentence Transformers** | Local embedding model (all-MiniLM-L6-v2) |
| **SQLAlchemy** | ORM for database interactions |
| **Pydantic** | Data validation & serialization |

### Frontend

| Technology | Purpose |
|-----------|--------|
| **Next.js 14** | React framework with SSR |
| **React** | Component-based UI |
| **TailwindCSS** | Utility-first CSS styling |
| **Chart.js** | Interactive technical indicator charts |
| **TypeScript** | Type-safe frontend code |

### Infrastructure

| Technology | Purpose |
|-----------|--------|
| **Docker & Docker Compose** | Containerized deployment |
| **Nginx** | Reverse proxy |
| **GitHub Actions** | CI/CD pipeline |

---

## 🎨 Features

### For Users

| Feature | Description |
|---------|-------------|
| ✅ **Smart Stock Analysis** | AI-powered insights based on news, sentiment, and technicals |
| ✅ **Real-Time News** | Latest updates from trusted Indian financial sources |
| ✅ **Sentiment Tracking** | Market mood analysis with confidence scores |
| ✅ **Technical Charts** | Interactive visualizations of RSI, MACD, Bollinger Bands |
| ✅ **Portfolio Management** | Watchlist & favorites to track investments |
| ✅ **Historical Context** | Learn from past analyses and prediction accuracy |
| ✅ **Scenario Forecasting** | Probabilistic bull/base/bear scenarios |
| ✅ **Risk Assessment** | 0-100 multi-factor risk scoring |
| ✅ **Saved Analyses** | Save up to 10 analyses for future reference |
| ✅ **Session Management** | View & revoke active sessions remotely |

### For Developers

| Feature | Description |
|---------|-------------|
| ✅ **Async Processing** | High-performance parallel sentiment analysis |
| ✅ **Modular Architecture** | Clean separation of concerns across 7 engines |
| ✅ **Vector Search** | Semantic similarity for relevant RAG context |
| ✅ **Comprehensive Logging** | Detailed observability at every layer |
| ✅ **Docker Ready** | One-command deployment with `docker compose up` |
| ✅ **Well Documented** | 32 technical docs, 800+ line README |
| ✅ **Feature Flags** | Toggle Smart Orchestrator, rate limits, kill switches |
| ✅ **Circuit Breakers** | Auto-disable failing APIs, self-healing |
| ✅ **4D Rate Limiting** | Device + Session + IP + User tracking |
| ✅ **JWT Key Rotation** | Zero-downtime 24h key rotation with 3-key window |

---

## 🏗️ System Architecture

NeuroVest uses a **Hybrid-RAG** architecture called _"The Sandwich"_ — the AI is sandwiched between layers of hard mathematical verification. Every insight is grounded in deterministic math.

```mermaid
graph TB
    subgraph CLIENT["🖥️ Client Layer"]
        FE["Next.js Frontend"]
        DT["Device Token Manager"]
        AT["Activity Tracker"]
        SM["Session Manager"]
    end

    subgraph GATEWAY["🌐 FastAPI Gateway"]
        MW["Middleware Stack"]
        SEC["Security Middleware"]
        RL["Rate Limit Middleware"]
        REQ["Request Middleware"]
    end

    subgraph LAYER1["⚡ Layer 1 — Deterministic Core"]
        SO["Smart API Orchestrator"]
        SE["Signal Engine"]
        PE["Price Engine"]
        RE["Risk Engine"]
        SCE["Scenario Engine"]
        RS["Relative Strength"]
        BT["Backtesting Engine"]
    end

    subgraph LAYER2["🔍 Layer 2 — Context Layer"]
        RAG["RAG Service"]
        EMB["Embedding Service"]
        SENT["Sentiment Engine"]
        SCRP["Web Scrapers"]
    end

    subgraph LAYER3["🤖 Layer 3 — Generative Synthesis"]
        LLM["Azure OpenAI GPT-4"]
        VAL["Narrative Validator"]
        GUARD["Guardrails Service"]
    end

    subgraph DATA["💾 Data Layer"]
        MYSQL[("MySQL 8.0<br/>18 Tables")]
        CHROMA[("ChromaDB<br/>2 Collections")]
        REDIS[("Redis 7<br/>12+ Key Patterns")]
    end

    FE -->|"HTTPS + JWT"| MW
    DT -->|"X-Device-Token"| MW
    SM -->|"X-Session-ID"| MW
    MW --> SEC --> RL --> REQ

    REQ --> SO
    SO -->|"Parallel APIs"| SE
    SE --> PE
    SE --> RE
    SE --> SCE
    SE --> RS
    SCE --> BT

    REQ --> RAG
    RAG --> EMB
    RAG --> SENT
    SENT --> SCRP

    RAG -->|"Structured Prompt"| LLM
    LLM -->|"Draft Narrative"| VAL
    VAL --> GUARD
    GUARD -->|"Validated Response"| FE

    SO <-->|"Stock Data"| REDIS
    SE <-->|"Cache"| REDIS
    RAG <-->|"Vector Search"| CHROMA
    EMB <-->|"Embeddings"| CHROMA
    RE <-->|"User Data"| MYSQL
    BT <-->|"Snapshots"| MYSQL
    GUARD <-->|"Analysis History"| MYSQL

    style CLIENT fill:#1a1a2e,stroke:#16213e,color:#e94560
    style GATEWAY fill:#16213e,stroke:#0f3460,color:#e94560
    style LAYER1 fill:#0f3460,stroke:#533483,color:#e94560
    style LAYER2 fill:#533483,stroke:#e94560,color:#fff
    style LAYER3 fill:#e94560,stroke:#f39189,color:#1a1a2e
    style DATA fill:#1a1a2e,stroke:#e94560,color:#fff
```

---

## 🧠 The 7-Engine Deterministic Core

Unlike most AI apps that ask the LLM _"What do you think?"_, NeuroVest **tells** the LLM what to think based on math. Every engine is deterministic — same input always produces same output.

```mermaid
graph LR
    subgraph INPUT["📥 Input"]
        OHLCV["OHLCV Data<br/>(3 months)"]
        MKT["Market Context<br/>(Nifty, VIX)"]
        NEWS["News Articles<br/>(7 days)"]
    end

    subgraph SIGNAL["⚡ Signal Engine"]
        TREND["Trend<br/>Classifier"]
        MOM["Momentum<br/>Classifier"]
        VOL["Volatility<br/>Classifier"]
        STRUCT["Structure<br/>Classifier"]
        VOLM["Volume<br/>Classifier"]
    end

    subgraph ENGINES["🔧 Processing Engines"]
        PE2["Price Engine<br/>Supply/Demand Zones"]
        RS2["Relative Strength<br/>vs Nifty & Sector"]
        RISK["Risk Engine<br/>0-100 Danger Score"]
        SCEN["Scenario Engine<br/>Bull/Base/Bear"]
        BACK["Backtesting<br/>Snapshot Storage"]
        SENTI["Sentiment Engine<br/>News Classification"]
        VALID["Narrative Validator<br/>Anti-Hallucination"]
    end

    OHLCV --> TREND & MOM & VOL & STRUCT & VOLM
    MKT --> RISK
    NEWS --> SENTI

    TREND & MOM & VOL & STRUCT & VOLM -->|"Signal Summary"| PE2
    PE2 -->|"Price Zones"| SCEN
    SENTI -->|"Sentiment Score"| RISK
    TREND & MOM -->|"Trend + Momentum"| RISK
    RISK -->|"Risk Score"| SCEN
    SCEN -->|"Scenarios"| BACK
    SCEN -->|"Scenarios + Zones"| VALID

    style SIGNAL fill:#0d1117,stroke:#58a6ff,color:#c9d1d9
    style ENGINES fill:#161b22,stroke:#58a6ff,color:#c9d1d9
```

### Engine Specifications

| # | Engine | Purpose | Key Output | Latency |
|---|--------|---------|------------|---------|
| 1 | **Signal Engine** | Classify market signals from OHLCV | `directional_bias`, `confidence_score`, `signal_conflicts` | 150ms |
| 2 | **Price Engine** | Identify supply/demand zones | `support`, `resistance`, `value_area` zones | 20ms |
| 3 | **Risk Engine** | Aggregate risk into 0-100 score | 6-component risk breakdown (trend, volatility, market, sector, conflict, news) | 80ms |
| 4 | **Scenario Engine** | Probabilistic forecasting | Bull/Base/Bear scenarios with probabilities summing to 1.0 | 10ms |
| 5 | **Sentiment Engine** | News mood classification | Score (-1 to +1), classification, trend | Part of ingestion |
| 6 | **Backtesting Engine** | Track prediction accuracy | Snapshot IDs for future outcome tracking | 5ms |
| 7 | **Narrative Validator** | Anti-hallucination guardrails | Forbidden term detection, price zone validation, probability matching | 20ms |

### Risk Score Breakdown (0-100)

```
╔═══════════════════╦════════╦══════════════════════════════════════╗
║ Component         ║ Weight ║ Logic                                ║
╠═══════════════════╬════════╬══════════════════════════════════════╣
║ Trend Risk        ║ 0-25   ║ Weak trend = 25, Strong = 0          ║
║ Volatility Risk   ║ 0-20   ║ ATR%: Low=0, Normal=5, High=15      ║
║ Market Risk       ║ 0-15   ║ VIX regime + Nifty trend             ║
║ Sector Risk       ║ 0-15   ║ RS vs sector < 0.8 = 15              ║
║ Signal Conflicts  ║ 0-15   ║ 5 points per conflicting signal      ║
║ News/Sentiment    ║ 0-10   ║ Sentiment < -0.3 = 10                ║
╠═══════════════════╬════════╬══════════════════════════════════════╣
║ TOTAL             ║ 0-100  ║ ≤30 Low, ≤60 Moderate, >60 High      ║
╚═══════════════════╩════════╩══════════════════════════════════════╝
```

---

## 🔗 RAG Pipeline — Retrieval-Augmented Generation

NeuroVest's RAG system ensures every AI response is **grounded in real data** — not hallucinated.

```mermaid
sequenceDiagram
    participant U as 👤 User
    participant API as ⚡ FastAPI
    participant Cache as 🔴 Redis Cache
    participant Scraper as 🌐 Web Scraper
    participant Embed as 🧮 Embedding Service
    participant Chroma as 📦 ChromaDB
    participant LLM as 🤖 Azure GPT-4
    participant Guard as 🛡️ Guardrails

    U->>API: Analyze RELIANCE
    API->>Cache: Check cache (1h TTL)
    
    alt Cache HIT
        Cache-->>U: Return instantly (<1ms)
    else Cache MISS
        API->>Scraper: Scrape news (DuckDuckGo + RSS)
        Scraper-->>API: 10-15 articles

        API->>Embed: Generate embeddings
        Note over Embed: all-MiniLM-L6-v2<br/>384 dimensions<br/>FREE (local)
        Embed->>Chroma: Store in stock_news

        API->>Chroma: Vector search (top 10)
        Chroma-->>API: Relevant articles

        API->>Chroma: Get historical analyses
        Chroma-->>API: Past 5 analyses

        Note over API: Assemble context:<br/>News + Technical + History

        alt Has History
            Note over API: SYNTHESIS mode<br/>"Compare old vs new"
        else First Analysis
            Note over API: BASELINE mode<br/>"Establish benchmarks"
        end

        API->>LLM: Structured prompt + context
        Note over LLM: Temperature: 0.5<br/>Response: JSON<br/>Cost: ~$0.15/analysis

        LLM-->>API: Narrative draft
        API->>Guard: Validate output
        Note over Guard: ✗ Forbidden terms<br/>✗ Price out of zones<br/>✗ Probability mismatch<br/>✓ Add disclaimer
        Guard-->>API: Clean response

        API->>Cache: Store (Redis 1h + MySQL + ChromaDB)
        API-->>U: Complete analysis
    end
```

### RAG Technology Stack

| Component | Technology | Purpose | Cost |
|-----------|-----------|---------|------|
| Embeddings | `all-MiniLM-L6-v2` (Sentence Transformers) | Text → 384-dim vectors | **FREE** (local) |
| Vector DB | ChromaDB (Persistent) | Semantic search over news & analyses | **FREE** |
| LLM | Azure OpenAI GPT-4 | Narrative generation from structured data | ~$0.15/analysis |
| News Scraping | DuckDuckGo + Google RSS | Real-time news ingestion | **FREE** |
| Cache | Redis (1h TTL) | Avoid redundant LLM calls | — |

### Prompt Engineering — Two Modes

```
┌─────────────────────────────────────────────────────────┐
│                 SYNTHESIS MODE                           │
│  (When historical analyses exist for this ticker)        │
│                                                          │
│  "You have historical memory. COMPARE current state      │
│   against baseline. Previously RSI was 62, now 65...     │
│   Track TRAJECTORY, not just snapshot."                  │
├─────────────────────────────────────────────────────────┤
│                 BASELINE MODE                            │
│  (First-time analysis for this ticker)                   │
│                                                          │
│  "Establish a BASELINE. Set benchmarks for future        │
│   comparisons. Identify PRIMARY risks to track."         │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 Smart API Orchestrator

The orchestrator intelligently routes stock data requests across multiple APIs with **circuit breaker** protection and **parallel execution**.

```mermaid
graph TD
    REQ["📨 Stock Data Request"]

    REQ -->|"Feature Flag"| CHECK{USE_SMART_<br/>ORCHESTRATOR?}

    CHECK -->|"true"| SMART["⚡ Smart Orchestrator"]
    CHECK -->|"false"| LEGACY["🐌 Legacy (Sequential)"]

    SMART --> CACHE{"3-Tier Cache<br/>Check"}
    CACHE -->|"Memory Hit (60s)"| RET["Return <100ms"]
    CACHE -->|"Redis Fresh (5m)"| RET
    CACHE -->|"Redis Stale (1h)"| RET
    CACHE -->|"MISS"| DETECT["📍 Market Detection"]

    DETECT -->|"INDIA"| INDIA["Yahoo Finance<br/>Alpha Vantage"]
    DETECT -->|"US"| US["Finnhub<br/>Yahoo Finance"]

    INDIA --> HEALTH{"Health Check<br/>Circuit Breaker"}
    US --> HEALTH

    HEALTH -->|"Healthy"| PARALLEL["⚡ Parallel Execution"]
    HEALTH -->|"Circuit Open ⛔"| FALLBACK["Fallback APIs"]

    PARALLEL --> MERGE["🔀 Data Merge<br/>Quality Scoring"]
    FALLBACK --> MERGE

    MERGE --> STORE["📦 Store in Cache"]
    STORE --> RET

    LEGACY -->|"Sequential<br/>1-2s"| RET

    style SMART fill:#0d1117,stroke:#58a6ff,color:#c9d1d9
    style PARALLEL fill:#238636,stroke:#2ea043,color:#fff
    style HEALTH fill:#da3633,stroke:#f85149,color:#fff
```

### Circuit Breaker Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Failure Threshold** | 5 failures | Opens circuit after 5 consecutive failures |
| **Time Window** | 300s | Failure window for threshold counting |
| **Recovery Time** | 300s | Time before retrying a broken circuit |
| **Success Threshold** | 30% | Minimum success rate to keep circuit closed |

---

## 📊 Data Pipeline — 11 Steps, ~2.8s

Each analysis request triggers a highly optimized pipeline. The **LLM call dominates** at 64% of total latency.

```mermaid
graph LR
    subgraph "Stage 1: Ingestion (800ms)"
        S1["1️⃣ Market Data<br/>OHLCV via<br/>Smart Orchestrator"]
    end

    subgraph "Stage 2: Math (310ms)"
        S2["2️⃣ Technical<br/>Indicators<br/>(50ms)"]
        S3["3️⃣ Signal<br/>Classification<br/>(150ms)"]
        S4["4️⃣ Price<br/>Zones<br/>(20ms)"]
        S5["5️⃣ Risk<br/>Scoring<br/>(80ms)"]
        S6["6️⃣ Scenario<br/>Generation<br/>(10ms)"]
    end

    subgraph "Stage 3: Context (155ms)"
        S7["7️⃣ Backtesting<br/>Snapshot<br/>(5ms)"]
        S8["8️⃣ RAG<br/>Retrieval<br/>(150ms)"]
    end

    subgraph "Stage 4: AI (1820ms)"
        S9["9️⃣ LLM<br/>Narrative<br/>(1800ms)"]
        S10["🔟 Validation<br/>(20ms)"]
    end

    subgraph "Stage 5: Store (50ms)"
        S11["1️⃣1️⃣ Multi-tier<br/>Storage"]
    end

    S1 --> S2 --> S3 --> S4 --> S5 --> S6 --> S7 --> S8 --> S9 --> S10 --> S11
```

### Latency Breakdown

| Step | Component | Latency | % Total |
|------|-----------|---------|---------|
| 1 | Market Data Ingestion | 800ms | 28% |
| 2 | Indicator Calculation | 50ms | 2% |
| 3 | Signal Classification | 150ms | 5% |
| 4 | Price Zone Calculation | 20ms | 1% |
| 5 | Risk Scoring | 80ms | 3% |
| 6 | Scenario Generation | 10ms | <1% |
| 7 | Backtesting Snapshot | 5ms | <1% |
| 8 | RAG Retrieval | 150ms | 5% |
| 9 | **LLM Narrative** | **1800ms** | **64%** |
| 10 | Validation | 20ms | 1% |
| 11 | Storage | 50ms | 2% |
| | **TOTAL** | **~2830ms** | |

### Failure Recovery

The system follows **Graceful Degradation** — core engines always work, even if supporting services fail:

| Failure | Recovery | User Impact |
|---------|----------|-------------|
| All APIs down | Return 503 | Cannot analyze |
| ChromaDB down | Continue without history | Less context |
| LLM timeout | Return structured data only | No narrative, but scenarios visible |
| Validation fails | Log and continue | Accepted with warning |
| Storage error | Log and continue | Analysis works, not persisted |

---

## 💾 3-Tier Database Architecture

```mermaid
graph TB
    subgraph APP["FastAPI Backend"]
        ORM["SQLAlchemy ORM"]
        CHROMALIB["ChromaDB Client"]
        REDISPY["Redis Client"]
    end

    subgraph MYSQL["🐬 MySQL 8.0 — Relational Data"]
        direction LR
        AUTH["🔐 Auth (4 tables)<br/>users, refresh_tokens,<br/>jwt_keys, failed_login_attempts"]
        USER["👤 User Data (4 tables)<br/>watchlist, favourites,<br/>saved_analyses, user_watchlist"]
        ANALYTICS["📈 Analytics (3 tables)<br/>login_history, traffic_stats,<br/>analysis_history"]
        ADMIN["🛡️ Admin (4 tables)<br/>active_sessions, audit_logs,<br/>email_queue, ip_blacklist"]
        CACHESQL["💾 Cache (1 table)<br/>analysis_cache"]
    end

    subgraph CHROMA["🔮 ChromaDB — Vector Store"]
        NEWS_C["📰 stock_news<br/>News article embeddings<br/>384-dim vectors"]
        ANALYSIS_C["📊 stock_analysis<br/>Historical analysis embeddings<br/>Semantic search"]
    end

    subgraph REDIS_DB["🔴 Redis 7 — In-Memory"]
        JWT_R["🔑 JWT Keys (3 keys)<br/>current, previous_1, previous_2"]
        RATE_R["⏱️ Rate Limits<br/>4D tracking across<br/>device/session/IP/user"]
        CACHE_R["💨 Stock & Analysis Cache<br/>60s memory, 5m fresh, 1h stale"]
        DEVICE_R["📱 Device Tracking<br/>Token registration + activity"]
    end

    ORM <--> MYSQL
    CHROMALIB <--> CHROMA
    REDISPY <--> REDIS_DB

    style MYSQL fill:#00758f,stroke:#00758f,color:#fff
    style CHROMA fill:#6c3483,stroke:#8e44ad,color:#fff
    style REDIS_DB fill:#d63031,stroke:#e17055,color:#fff
```

### Database Summary

| Database | Tables/Collections | Purpose | Storage |
|----------|-------------------|---------|---------|
| **MySQL 8.0** | 18 tables | Users, sessions, analytics, admin | Persistent (Docker volume) |
| **ChromaDB** | 2 collections | Vector embeddings for RAG | Local filesystem |
| **Redis 7** | 12+ key patterns | Cache, rate limits, JWT keys | In-memory + AOF (256MB max) |

---

## 🛡️ Security — Defense in Depth

### 1. 4-Dimensional Rate Limiting

Attackers cannot evade bans by simply changing one identifier. Every request is tracked across **4 independent dimensions**, and the **strictest** one wins.

```mermaid
graph TD
    REQ["📨 Incoming Request"] --> EXTRACT["Extract 4 Identifiers"]

    EXTRACT --> D1["🖥️ Device<br/>HMAC-SHA256<br/>Fingerprint"]
    EXTRACT --> D2["🔑 Session<br/>UUID v4"]
    EXTRACT --> D3["🌐 IP<br/>SHA-256 Hash"]
    EXTRACT --> D4["👤 User ID<br/>JWT Claim"]

    D1 --> CHECK["Redis: INCR all 4 keys"]
    D2 --> CHECK
    D3 --> CHECK
    D4 --> CHECK

    CHECK --> DECIDE{Any dimension<br/>exceeds limit?}
    DECIDE -->|"Yes"| BLOCK["⛔ 429 Too Many Requests"]
    DECIDE -->|"No"| ALLOW["✅ Allow Request"]

    style BLOCK fill:#da3633,stroke:#f85149,color:#fff
    style ALLOW fill:#238636,stroke:#2ea043,color:#fff
```

#### Rate Limit Tiers

| Role | Analysis/24h | API/min | API/hour |
|------|-------------|---------|----------|
| **Guest** | 2 | 30 | 500 |
| **User** | 5 | 60 | 1,000 |
| **Admin** | Unlimited | 120 | 5,000 |

#### Device Token Signing Flow

```
Frontend → Generate fingerprint (canvas, WebGL, fonts, audio, screen)
         → Hash with SHA-256
         → Send to backend

Backend  → Create payload {fingerprint, timestamp, nonce}
         → Sign with HMAC-SHA256 (server secret)
         → Return signed token (base64)

Validation → Decode token
           → Recompute HMAC signature
           → Constant-time comparison (prevents timing attacks)
           → If mismatch → REJECT (stolen token on different device)
```

### 2. JWT Key Rotation — Zero Downtime

Keys rotate every 24 hours. Users are **never** forcibly logged out.

```mermaid
graph LR
    subgraph "Sliding Window (3 Keys Active)"
        K1["🟢 CURRENT<br/>(0-24h)<br/>Sign + Verify"]
        K2["🟡 PREVIOUS_1<br/>(24-48h)<br/>Verify Only"]
        K3["🟠 PREVIOUS_2<br/>(48-72h)<br/>Verify Only"]
        K4["🔴 EXPIRED<br/>(>72h)<br/>Deleted"]
    end

    K1 -->|"After 24h"| K2
    K2 -->|"After 24h"| K3
    K3 -->|"After 24h"| K4

    style K1 fill:#238636,stroke:#2ea043,color:#fff
    style K2 fill:#9e6a03,stroke:#d29922,color:#fff
    style K3 fill:#bd561d,stroke:#db6d28,color:#fff
    style K4 fill:#da3633,stroke:#f85149,color:#fff
```

**Dual Storage**: Redis (fast, ~1ms) + MySQL (persistent, survives restarts). On startup, keys are loaded from MySQL → Redis.

### 3. Narrative Guardrails

The Narrative Validator ensures the LLM never:

| Rule | What It Catches | Action |
|------|----------------|--------|
| **Forbidden Terms** | `buy`, `sell`, `hold`, `RSI`, `EMA`, `P/E` | Replace with safe alternatives |
| **Price Validation** | Prices outside support/resistance zones | Flag as error |
| **Probability Match** | Narrative % ≠ scenario probabilities | Flag as warning |
| **Tone Check** | High-conviction language with low confidence | Flag as warning |
| **Disclaimer** | Missing risk disclaimer | Auto-inject |

### 4. Encryption & Transport

- **At Rest**: Passwords (bcrypt), Device Tokens (HMAC-SHA256)
- **In Transit**: HTTPS (TLS 1.3), `httpOnly` cookies for JWTs (prevents XSS theft)
- **Login Protection**: Account locked after 5 failed attempts (15 min cooldown)

---

## ⚙️ Admin Command Center

A full-featured admin dashboard with **RBAC** (Role-Based Access Control):

| Feature | ADMIN | SUPER_ADMIN |
|---------|:-----:|:-----------:|
| View system health & golden signals | ✅ | ✅ |
| View user list & login history | ✅ | ✅ |
| View traffic analytics | ✅ | ✅ |
| View kill switch status | ✅ | ✅ |
| **Disable/Enable users** | ❌ | ✅ |
| **Blacklist/Unblock IPs** | ❌ | ✅ |
| **Toggle kill switches** | ❌ | ✅ |
| **Force logout users** | ❌ | ✅ |
| **System toggles** | ❌ | ✅ |

### Available Kill Switches

| Switch | Effect |
|--------|--------|
| `BLOCK_SIGNUPS` | Prevent new user registrations |
| `BLOCK_ANALYSIS` | Disable AI analysis endpoint |
| `EMERGENCY_SHUTDOWN` | Block all non-admin API access |
| `DISABLE_RATE_LIMITS` | Temporarily disable rate limiting |
| `MAINTENANCE_MODE` | Show maintenance page to users |

---

## 👤 User Management & Tracking

### User Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Registered: POST /auth/register
    Registered --> Active: Email Verified
    Registered --> Locked: 5 Failed Logins
    Active --> Active: Login / Analysis / Settings
    Active --> Locked: 5 Failed Logins
    Locked --> Active: 15min Cooldown
    Active --> Disabled: Admin Action
    Disabled --> Active: Admin Re-enable
```

### Session & Device Tracking

Every login records:
- **Device info**: Type (Desktop/Mobile/Tablet), OS, Browser, Device Name
- **Network**: IP address (hashed for privacy), GeoIP (city, country, lat/lon)
- **Session**: UUID, device fingerprint, timestamps
- **Security**: Login success/failure, failure reason

Users can view all active sessions in **Settings** and revoke any session remotely. Maximum **2 concurrent sessions** per user (oldest auto-revoked).

---

## 🔧 Trading Utilities & Data Sources

### External Data Sources

| Source | Type | Data Provided | Priority |
|--------|------|--------------|----------|
| **Yahoo Finance** | Stock API | OHLCV, fundamentals | Primary (INDIA) |
| **Alpha Vantage** | Stock API | Historical data | Primary (INDIA) |
| **Finnhub** | Stock API | Real-time quotes | Primary (US) |
| **Marketstack** | Stock API | Global coverage | Fallback |
| **DuckDuckGo** | News Scraper | Web search results | Primary |
| **Google News RSS** | News Feed | Structured news | Fallback |

### Technical Indicators Calculated

| Indicator | Parameters | Classification |
|-----------|-----------|----------------|
| **SMA** | 50-day, 200-day | Trend direction |
| **RSI** | 14-period | Overbought (>70) / Oversold (<30) |
| **MACD** | 12, 26, 9 | Bullish/Bearish crossover |
| **ATR** | 14-period | Volatility regime (Low/Normal/High/Extreme) |
| **Bollinger Bands** | 20-period, 2σ | Price position vs bands |
| **Volume Profile** | Variable | Volume trend (increasing/decreasing/stable) |
| **Swing Highs/Lows** | 5-period window | Support/Resistance identification |

---

## 🗂️ Project Structure

```
neurovest/
├── backend/
│   ├── app/
│   │   ├── api/                    # 28 API route files
│   │   │   ├── auth.py             # Login, register, refresh, logout
│   │   │   ├── stocks.py           # Stock analysis endpoints
│   │   │   ├── admin_management.py # User/IP/toggle management
│   │   │   ├── admin_killswitch.py # Kill switch controls
│   │   │   └── admin_session.py    # Session management
│   │   ├── core/                   # Configuration & security
│   │   │   ├── config.py           # Environment-based settings
│   │   │   ├── security.py         # JWT + password hashing
│   │   │   ├── jwt_key_manager.py  # Key rotation system
│   │   │   ├── rbac.py             # Role-based access control
│   │   │   └── database.py         # SQLAlchemy connection
│   │   ├── middleware/             # Request processing pipeline
│   │   │   ├── security_middleware.py
│   │   │   ├── rate_limit_middleware.py
│   │   │   ├── metrics_middleware.py
│   │   │   └── request_middleware.py
│   │   ├── signal_engine/          # Technical signal classification
│   │   ├── scenario_engine/        # Probabilistic forecasting
│   │   ├── price_engine/           # Support/resistance zones
│   │   ├── risk_scoring/           # Multi-factor risk assessment
│   │   ├── sentiment_impact/       # News sentiment analysis
│   │   ├── relative_strength/      # Stock vs sector comparison
│   │   ├── backtesting/            # Prediction accuracy tracking
│   │   ├── signal_history/         # Signal persistence
│   │   ├── llm_integration/        # Azure OpenAI wrapper
│   │   ├── output_validator/       # LLM output validation
│   │   ├── validators/             # Narrative guardrails
│   │   ├── pipelines/              # Analysis orchestration
│   │   ├── rate_limiting/          # 4D rate limiting system
│   │   ├── scrapers/               # News scraping (11 files)
│   │   ├── services/               # Business logic (35 files)
│   │   ├── trading_utils/          # Market utilities
│   │   ├── models/                 # SQLAlchemy models
│   │   ├── utils/                  # AES decryption, GeoIP, etc.
│   │   └── main.py                 # Application entry point
│   ├── migrations/                 # Database migration SQL
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/                    # Next.js pages
│   │   ├── components/             # React components
│   │   └── lib/                    # Utilities
│   │       ├── activity-tracker.ts
│   │       ├── device-token-manager.ts
│   │       ├── session-manager.ts
│   │       └── tracking-headers.ts
│   └── Dockerfile
├── docs/                           # 32 documentation files
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Azure OpenAI API Key
- (Optional) Finnhub / Alpha Vantage API Keys

### Setup

```bash
# 1. Clone
git clone https://github.com/AshutoshKY/NeuroVest.git
cd NeuroVest

# 2. Configure
cp .env.example .env
# Edit .env with your API keys

# 3. Launch
docker compose up -d --build

# 4. Access
# Frontend:  http://localhost:3000
# Backend:   http://localhost:8000
# API Docs:  http://localhost:8000/docs
```

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `AZURE_OPENAI_API_KEY` | ✅ | Azure OpenAI API key | — |
| `AZURE_OPENAI_ENDPOINT` | ✅ | Azure endpoint URL | — |
| `JWT_SECRET_KEY` | ✅ | Fallback JWT signing key | — |
| `MYSQL_PASSWORD` | ✅ | Database password | — |
| `FINNHUB_API_KEY` | Optional | Finnhub stock data | — |
| `ALPHA_VANTAGE_API_KEY` | Optional | Alpha Vantage data | — |
| `USE_SMART_ORCHESTRATOR` | Optional | Enable parallel API routing | `true` |
| `RATE_LIMIT_ENABLED` | Optional | Enable 4D rate limiting | `true` |
| `CHROMA_DB_PATH` | Optional | Vector store location | `./data/chroma` |

### Docker Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `mysql` | `mysql:8.0` | 3306 | Relational database |
| `redis` | `redis:7-alpine` | 6379 | Cache & rate limiting |
| `backend` | Custom (FastAPI) | 8000 | API server |
| `frontend` | Custom (Next.js) | 3000 | Web application |

---

## 📜 Documentation Index

| Document | Description |
|----------|-------------|
| [ENGINES.md](./docs/ENGINES.md) | Deep dive into all 7 core engines |
| [RAG_SYSTEM.md](./docs/RAG_SYSTEM.md) | Complete RAG pipeline documentation |
| [RATE_LIMITING.md](./docs/RATE_LIMITING.md) | 4D rate limiting system |
| [DATABASE_INFRASTRUCTURE.md](./docs/DATABASE_INFRASTRUCTURE.md) | 3-tier database architecture |
| [JWT_AUTHENTICATION.md](./docs/JWT_AUTHENTICATION.md) | JWT key rotation system |
| [SMART_ORCHESTRATOR_ARCHITECTURE.md](./docs/SMART_ORCHESTRATOR_ARCHITECTURE.md) | Smart API orchestrator |
| [DATA_FLOW.md](./docs/DATA_FLOW.md) | End-to-end data pipeline |
| [API_DOCUMENTATION.md](./docs/API_DOCUMENTATION.md) | API endpoint reference |
| [ADMIN_GUIDE.md](./docs/ADMIN_GUIDE.md) | Admin dashboard guide |
| [BACKTESTING.md](./docs/BACKTESTING.md) | Prediction tracking system |
| [deployment_guide.md](./docs/deployment_guide.md) | Production deployment guide |
| [TESTING_PIPELINE.md](./docs/TESTING_PIPELINE.md) | Testing strategy & results |

---

## 📊 Performance

### Benchmark Results

**Analysis Pipeline** (tested with 10 stocks):

| Stage | Avg Latency | Notes |
|-------|------------|-------|
| News Aggregation | 0.15s | RSS primary source |
| Sentiment Analysis | 3.8s | 5 articles in parallel (GPT-4) |
| Technical Indicators | 1.2s | RSI, MACD, Bollinger, ATR |
| RAG Generation | 5s | Context assembly + LLM call |
| **Total Pipeline** | **10-12s** | ✅ End-to-end |

**Success Rates**:

| Component | Rate |
|-----------|------|
| News Retrieval | 75%+ (RSS primary) |
| Sentiment Accuracy | 90%+ (GPT-4) |
| Technical Calculation | 100% (deterministic) |
| Cache Hit Rate | 70%+ (Redis) |

---

## 🔧 Configuration

### ChromaDB Temporal Retrieval

Fine-tune historical analysis retrieval in `backend/app/core/config.py`:

```python
TEMPORAL_DECAY_LAMBDA = 0.05   # Decay rate (higher = faster decay)
TEMPORAL_WEIGHT = 0.6          # Weight for recency
QUALITY_WEIGHT = 0.4           # Weight for quality
MAX_PER_WEEK = 2               # Diversity constraint
DAYS_BACK = 45                 # Search window days
```

### RSS News Sources

Configure feeds in `backend/app/scrapers/rss_news_aggregator.py`:

```python
RSS_FEEDS = {
    'moneycontrol': 'https://www.moneycontrol.com/rss/latestnews.xml',
    'economic_times': 'https://economictimes.indiatimes.com/rssfeedstopstories.cms',
    'livemint': 'https://www.livemint.com/rss/markets'
}
```

---

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Restart specific service
docker-compose restart backend

# Stop all services
docker-compose down

# Rebuild after code changes
docker-compose build backend
docker-compose up -d

# Check service health
docker-compose ps

# Access backend shell
docker exec -it stockmarket_backend bash

# Access MySQL
docker exec -it stockmarket_mysql mysql -u stockmarket_user -p stockmarket_db

# Access Redis CLI
docker exec -it stockmarket_redis redis-cli
```

---

## 🧪 Testing

### Run Tests Locally

```bash
cd /Volumes/Storage-Ash/prjts/stockmarket
python3 test_optimizations.py
```

### Run Tests in Docker

```bash
# Test RSS aggregator
docker exec stockmarket_backend python3 -c "
from app.scrapers.rss_news_aggregator import rss_aggregator
print('✅ RSS aggregator loaded')
"

# Test embedding service
docker exec stockmarket_backend python3 -c "
from app.services.embeddings import EmbeddingService
print('✅ Embedding service loaded')
"

# Test signal engine
docker exec stockmarket_backend python3 -c "
from app.signal_engine.service import SignalService
print('✅ Signal engine loaded')
"

# Run full test suite
docker exec stockmarket_backend pytest app/tests/ -v
```

---

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Code Style

- **Backend**: Follow PEP 8, use type hints
- **Frontend**: ESLint + Prettier config included
- **Commits**: Use conventional commits (`feat:`, `fix:`, `docs:`, etc.)

---

## 📝 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 📧 Contact

| | |
|---|---|
| **Author** | Ashutosh Kumar Yadav |
| **Email** | [akyadav3996@gmail.com](mailto:akyadav3996@gmail.com) |
| **Portfolio** | [ashutoshky.vercel.app](https://ashutoshky.vercel.app) |
| **GitHub** | [github.com/AshutoshKY](https://github.com/AshutoshKY) |

For questions or support, please [open an issue](https://github.com/AshutoshKY/NeuroVest/issues) on GitHub.

---

## 🙏 Acknowledgments

- **Azure OpenAI** — GPT-4 for AI-powered analysis
- **ChromaDB** — Vector database for semantic search
- **Sentence Transformers** — Free local embeddings
- **Moneycontrol, ET, Livemint** — RSS feed providers
- **yfinance** — Stock data API
- **FastAPI** — High-performance async framework

---

<p align="center">
  <b>Built with ❤️ for the Indian Stock Market Community</b><br/>
  <b>by <a href="https://ashutoshky.vercel.app">Ashutosh Kumar Yadav</a></b><br/>
  <sub>7 Engines · 3 Databases · 4D Security · Zero Hallucinations</sub>
</p>
