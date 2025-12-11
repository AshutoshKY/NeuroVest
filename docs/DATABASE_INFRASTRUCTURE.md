# Database Infrastructure Documentation - NeuroVest Stock Market Platform

**Document Version**: 1.0  
**Last Updated**: December 11, 2025  
**Database Stack**: MySQL 8.0 + ChromaDB + Redis 7-alpine

## Table of Contents
1. [Executive Overview](#executive-overview)
2. [Architecture Overview](#architecture-overview)
3. [MySQL (Relational Database)](#mysql-relational-database)
4. [ChromaDB (Vector Database)](#chromadb-vector-database)
5. [Redis (Cache & Rate Limiting)](#redis-cache--rate-limiting)
6. [Data Flow & Integration](#data-flow--integration)
7. [Feature Dependencies](#feature-dependencies)
8. [Performance & Cost Analysis](#performance--cost-analysis)

---

## Executive Overview

### Database Stack Summary

| Database | Version | Purpose | Storage | Key Features |
|----------|---------|---------|---------|--------------|
| **MySQL** | 8.0 | Relational data, user management, sessions | Persistent (Docker volume) | ACID transactions, Foreign keys, Indexes |
| **ChromaDB** | Latest (PersistentClient) | Vector embeddings, RAG system | Local filesystem | Semantic search, 384-dim vectors |
| **Redis** | 7-alpine | Cache, rate limiting, JWT keys | In-memory + AOF | LRU eviction, 256MB max memory |

### Database Distribution

```
Total Tables: 18 (MySQL)
Total Collections: 2 (ChromaDB)
Total Redis Key Patterns: 12+

MySQL Tables:
├── Authentication (4): users, refresh_tokens, jwt_keys, failed_login_attempts
├── User Data (4): watchlist, favourites, saved_analyses, user_watchlist
├── Analytics (3): login_history, traffic_stats, analysis_history
├── Admin (4): active_sessions, admin_audit_logs, email_queue, ip_blacklist
└── Cache (1): analysis_cache

ChromaDB Collections:
├── stock_news (news articles, embeddings)
└── stock_analysis (historical analyses, embeddings)

Redis Keys:
├── JWT (3): jwt:keys:current, jwt:keys:previous_*, jwt:keys:last_rotation
├── Rate Limiting (4): rate_limit:{role}:{dimension}:{id}:{type}
├── Device Tracking (2): device_activity:{fp}:registration, device_token:*
└── Caching (2): stock_info:{ticker}, analysis_cache:*
```

---

## Architecture Overview

### Database Connectivity Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                   3-Tier Database Architecture                   │
└──────────────────────────────────────────────────────────────────┘

                        ┌─────────────┐
                        │   FastAPI   │
                        │   Backend   │
                        └──────┬──────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         v                     v                     v
    ┌─────────┐          ┌──────────┐         ┌──────────┐
    │  MySQL  │          │ ChromaDB │         │  Redis   │
    │  8.0    │          │ (Vectors)│         │ 7-alpine │
    └────┬────┘          └─────┬────┘         └─────┬────┘
         │                     │                     │
         │                     │                     │
┌────────┴─────────┐  ┌────────┴─────────┐  ┌────────┴─────────┐
│ Persistent Data  │  │ Vector Embeddings│  │ In-Memory Cache  │
│ • Users          │  │ • News Articles  │  │ • JWT Keys       │
│ • Sessions       │  │ • Analyses       │  │ • Rate Limits    │
│ • Watchlists     │  │ • Semantic Search│  │ • Stock Info     │
│ • Analyses       │  │   (384-dim)      │  │ • Device Tokens  │
│ • Login History  │  │ • RAG Context    │  │ TTL: Variable    │
└──────────────────┘  └──────────────────┘  └──────────────────┘

Docker Volumes:        Local Filesystem      In-Memory + AOF
```

### Connection Configuration

**Docker Compose** (`docker-compose.yml`):
```yaml
mysql:
  image: mysql:8.0
  environment:
    MYSQL_DATABASE: stockmarket_db
    MYSQL_USER: stockmarket_user
    MYSQL_PASSWORD: secure_password_123
  volumes:
    - mysql_data:/var/lib/mysql
  ports:
    - "3306:3306"

redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
  volumes:
    - redis_data:/data
  ports:
    - "6379:6379"

backend:
  environment:
    MYSQL_HOST: mysql
    MYSQL_PORT: 3306
    REDIS_HOST: redis
    REDIS_PORT: 6379
```

---

## MySQL (Relational Database)

### Database Specifications

- **Version**: MySQL 8.0
- **Engine**: InnoDB (ACID compliant)
- **Charset**: utf8mb4 with utf8mb4_unicode_ci collation
- **Container**: stockmarket_mysql
- **Persistent Storage**: Docker volume `mysql_data`
- **Total Tables**: 18

### Table Schema Documentation

#### 1. **users** (Core User Table)

**Purpose**: Store user accounts with authentication and authorization

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role ENUM('user', 'admin') DEFAULT 'user' NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    failed_login_attempts INT DEFAULT 0 NOT NULL,
    locked_until TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_email (email),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Columns** (11):
- `id` - Primary key
- `email` - Unique identifier, indexed
- `hashed_password` - bcrypt hash (never stored plain)
- `full_name` - Display name
- `role` - user/admin (indexed for authorization)
- `is_verified` - Email verification status
- `is_active` - Account active/suspended
- `failed_login_attempts` - Brute force protection (0-5)
- `locked_until` - Temporary account lock timestamp
- `created_at` - Registration timestamp
- `updated_at` - Last modification timestamp

**Relationships**:
- Referenced by: `refresh_tokens`, `watchlist`, `favourites`, `saved_analyses`, `login_history`

---

#### 2. **refresh_tokens** (JWT Session Management)

**Purpose**: Store refresh tokens for session persistence

```sql
CREATE TABLE refresh_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(500) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    revoked BOOLEAN DEFAULT FALSE NOT NULL,
    last_used_at TIMESTAMP NULL,
    
    -- Session metadata
    ip_address VARCHAR(45),
    device_type VARCHAR(50),
    os VARCHAR(100),
    browser VARCHAR(100),
    device_name VARCHAR(255),
    session_id VARCHAR(255),
    country VARCHAR(100),
    city VARCHAR(100),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_token (token),
    INDEX idx_user_id (user_id),
    INDEX idx_user_revoked (user_id, revoked),
    INDEX idx_expires_at (expires_at),
    UNIQUE KEY unique_token (token)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Columns** (16):
- **Core**: `id`, `user_id`, `token` (hashed), `expires_at`, `revoked`
- **Session Tracking**: `ip_address`, `device_type`, `os`, `browser`, `session_id`
- **Location**: `country`, `city` (from GeoIP)
- **Timestamps**: `created_at`, `last_used_at`

**Key Features**:
- Max 2 active sessions per user (oldest auto-revoked)
- 7-day expiration
- Cascade delete on user deletion
- Tracks device and location for security display

---

#### 3. **jwt_keys** (JWT Signing Key Rotation)

**Purpose**: Store rotating JWT signing keys (24-hour rotation)

```sql
CREATE TABLE jwt_keys (
    id INT AUTO_INCREMENT PRIMARY KEY,
    key_id VARCHAR(50) UNIQUE NOT NULL,  -- e.g., '2025-12-11T12:44:12Z'
    secret_key TEXT NOT NULL,            -- Base64-encoded 256-bit key
    status ENUM('current', 'previous_1', 'previous_2', 'expired') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,       -- created_at + 72 hours
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMP NULL,
    
    INDEX idx_status (status),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Columns** (8):
- `key_id` - Unique timestamp-based ID
- `secret_key` - Cryptographically secure 256-bit key
- `status` - current (signing), previous_1/2 (verification), expired
- `expires_at` - 72 hours from creation (3 rotation cycles)

**Lifecycle**:
1. **Current** (0-24h): Used for signing new tokens
2. **Previous_1** (24-48h): Used for verification only
3. **Previous_2** (48-72h): Used for verification only
4. **Expired** (>72h): Marked inactive, no verification

**Purpose**: Zero-downtime token rotation. Users remain logged in even after key rotation.

---

#### 4. **watchlist** (User Stock Watchlist)

```sql
CREATE TABLE watchlist (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    exchange VARCHAR(50),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_ticker (user_id, ticker),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB;
```

**Columns** (6):
- `ticker` - Stock symbol (e.g., "TCS", "RELIANCE")
- `name` - Company name
- `exchange` - NSE/BSE
- Unique constraint: one ticker per user

---

#### 5. **favourites** (User Favorite Stocks)

```sql
CREATE TABLE favourites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    exchange VARCHAR(50),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_ticker (user_id, ticker),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB;
```

**Same structure as watchlist** - separate collection for UX purposes

---

#### 6. **saved_analyses** (User Saved Analysis Results)

```sql
CREATE TABLE saved_analyses (
    id CHAR(36) PRIMARY KEY,  -- UUID
    user_email VARCHAR(255) NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    title VARCHAR(255),
    analysis_data JSON NOT NULL,  -- Complete analysis result
    price DECIMAL(10,2),
    currency VARCHAR(10) DEFAULT 'INR',
    sentiment VARCHAR(50),
    confidence DECIMAL(3,2),      -- 0.00-1.00
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user_email (user_email),
    INDEX idx_ticker (ticker),
    INDEX idx_saved_at (saved_at)
) ENGINE=InnoDB;
```

**Columns** (10):
- `analysis_data` - Full JSON analysis response
- **Limit**: 10 saved analyses per user
- Extracted fields (`price`, `sentiment`, `confidence`) for quick filtering

---

#### 7. **analysis_history** (Analysis Request Tracking)

```sql
CREATE TABLE analysis_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    user_id INT,
    ip_address VARCHAR(50),
    sentiment VARCHAR(50),
    success BOOLEAN DEFAULT TRUE,
    cached BOOLEAN DEFAULT FALSE,
    latency_ms INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_ticker (ticker),
    INDEX idx_user_id (user_id),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB;
```

**Purpose**: Track all analysis requests for analytics and trending stocks

---

#### 8. **login_history** (Login Attempt Tracking)

```sql
CREATE TABLE login_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    ip_address VARCHAR(50),
    user_agent TEXT,
    country VARCHAR(100),
    city VARCHAR(100),
    login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT TRUE,
    failure_reason VARCHAR(255),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_login_at (login_at),
    INDEX idx_success (success)
) ENGINE=InnoDB;
```

**Features**:
- Tracks both successful and failed logins
- GeoIP location tracking
- Used for security dashboard ("Recent Logins")

---

#### 9. **active_sessions** (Real-Time Session Tracking)

```sql
CREATE TABLE active_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_session_token (session_token),
    INDEX idx_user_id (user_id),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB;
```

**Purpose**: Track active browser sessions (separate from refresh tokens)

---

#### 10. **failed_login_attempts** (Brute Force Protection)

```sql
CREATE TABLE failed_login_attempts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL,
    ip_address VARCHAR(50),
    attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_email (email),
    INDEX idx_ip_address (ip_address),
    INDEX idx_attempt_time (attempt_time)
) ENGINE=InnoDB;
```

**Logic**:
- 5 failed attempts → temporary account lock (15 minutes)
- Reset on successful login

---

#### 11. **ip_blacklist** (IP Ban List)

```sql
CREATE TABLE ip_blacklist (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ip_address VARCHAR(50) UNIQUE NOT NULL,
    reason VARCHAR(255),
    blacklisted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    blacklisted_until TIMESTAMP,
    
    INDEX idx_ip_address (ip_address)
) ENGINE=InnoDB;
```

**Purpose**: Admin-managed IP ban list for abuse prevention

---

#### 12. **traffic_stats** (Hourly Traffic Aggregation)

```sql
CREATE TABLE traffic_stats (
    id INT PRIMARY KEY AUTO_INCREMENT,
    hour_timestamp TIMESTAMP NOT NULL,
    total_requests INT DEFAULT 0,
    unique_ips INT DEFAULT 0,
    total_analyses INT DEFAULT 0,
    unique_users INT DEFAULT 0,
    avg_latency_ms INT DEFAULT 0,
    error_count INT DEFAULT 0,
    
    UNIQUE KEY unique_hour (hour_timestamp),
    INDEX idx_hour_timestamp (hour_timestamp)
) ENGINE=InnoDB;
```

**Purpose**: Admin traffic analytics dashboard

---

#### 13-18. Additional Tables

- **analysis_cache**: Cached AI analysis results (1-hour TTL)
- **user_watchlist**: Legacy watchlist table
- **user_favorites**: Legacy favorites table  
- **user_analysis_history**: Per-user analysis tracking
- **admin_audit_logs**: Admin action audit trail
- **email_queue**: Async email sending queue

---

### MySQL Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| **Avg Query Latency** | <50ms | Most queries use indexed fields |
| **Connection Pool** | 5-20 connections | FastAPI connection pooling |
| **Storage (Current)** | ~50-100MB | Depends on user activity |
| **Storage (1 year projection)** | ~500MB-1GB | Assuming 1000 active users |
| **Backup Strategy** | Docker volume snapshots | Daily recommended |

**Cost Estimation** (Managed MySQL):
- **AWS RDS (db.t3.micro)**: ~$15/month
- **DigitalOcean Managed DB**: ~$15/month
- **Self-hosted (VPS)**: $5-10/month
- **Current (Docker)**: Free (uses VPS storage)

---

## ChromaDB (Vector Database)

### ChromaDB Specifications

- **Type**: Persistent vector database
- **Storage**: Local filesystem (`/app/chroma_data`)
- **Embedding Model**: `all-MiniLM-L6-v2` (Sentence Transformers)
- **Vector Dimensions**: 384
- **Collections**: 2 (stock_news, stock_analysis)

### Implementation

**Initialization** (`backend/app/services/embeddings.py`):
```python
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self):
        # Local embedding model (FREE - no API costs)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Persistent ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_DB_PATH,  # /app/chroma_data
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Create collections
        self.news_collection = self.chroma_client.get_or_create_collection(
            name=\"stock_news\",
            metadata={\"description\": \"Stock market news articles\"}
        )
        
        self.analysis_collection = self.chroma_client.get_or_create_collection(
            name=\"stock_analysis\",
            metadata={\"description\": \"Historical stock analyses\"}
        )
```

### Collections

#### 1. **stock_news** Collection

**Purpose**: Store news articles with vector embeddings for RAG

**Document Structure**:
```python
{
    \"id\": \"article_TCS_2025-12-11_001\",
    \"document\": \"TCS announces Q3 earnings showing 15% YoY growth...\",
    \"embedding\": [0.123, -0.456, ...],  # 384 dimensions
    \"metadata\": {
        \"ticker\": \"TCS\",
        \"source\": \"Business Standard\",
        \"published_date\": \"2025-12-11\",
        \"url\": \"https://...\",
        \"category\": \"earnings\"
    }
}
```

**Typical Size**:
- **Documents per ticker**: 10-50 recent articles
- **Total documents**: 500-5,000 (varies with ingestion)
- **Storage per document**: ~2-5KB (text + embedding)
- **Total storage**: 1-25MB

---

#### 2. **stock_analysis** Collection

**Purpose**: Store historical AI analyses for retrieval

**Document Structure**:
```python
{
    \"id\": \"analysis_TCS_2025-12-11_user123\",
    \"document\": \"Analysis: TCS shows strong fundamentals with...\",
    \"embedding\": [0.234, -0.567, ...],  # 384 dimensions
    \"metadata\": {
        \"ticker\": \"TCS\",
        \"user_id\": 123,
        \"sentiment\": \"bullish\",
        \"confidence\": 0.85,
        \"timestamp\": \"2025-12-11T10:00:00Z\",
        \"historical_analysis\": true
    }
}
```

---

### Embedding Process

**1. Text → Vector** (Sentence Transformers):
```python
def generate_embedding(text: str) -> List[float]:
    # all-MiniLM-L6-v2 model (384 dimensions)
    embedding = self.model.encode(text, convert_to_numpy=True)
    return embedding.tolist()  # [384 floats]
```

**Latency**:
- Single embedding: ~10-50ms (CPU)
- Batch (10 docs): ~100-200ms (CPU)
- GPU acceleration: ~5-20ms per doc (if available)

**2. Storage**:
```python
def add_documents(documents: List[str], metadatas: List[Dict], ids: List[str]):
    embeddings = self.generate_embeddings_batch(documents)
    self.news_collection.add(
        embeddings=embeddings,
       documents=documents,
        metadatas=metadatas,
        ids=ids
    )
```

**3. Semantic Search**:
```python
def query_similar(query_text: str, n_results: int = 10):
    query_embedding = self.generate_embedding(query_text)
    results = self.news_collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where={\"ticker\": \"TCS\"}  # Filter by metadata
    )
    return results
```

**Query Latency**:
- Small collection (<1000 docs): ~10-50ms
- Medium collection (1000-10000 docs): ~50-200ms
- Large collection (>10000 docs): ~200-500ms

---

### RAG (Retrieval-Augmented Generation) Integration

**How ChromaDB Powers RAG**:

```
User Request: \"Analyze TCS stock\"
     │
     v
┌────────────────────────┐
│ 1. Query Embedding     │
│ Generate 384-dim vector│
│ for \"Analyze TCS\"      │
└──────────┬─────────────┘
           │
           v
┌────────────────────────┐
│ 2. ChromaDB Query      │
│ Semantic search in     │
│ stock_news collection  │
│ Filter: ticker=\"TCS\"   │
│ n_results=10           │
└──────────┬─────────────┘
           │
           v
┌────────────────────────┐
│ 3. Retrieve Context    │
│ Top 10 relevant articles│
│ - Earnings reports     │
│ - Market sentiment     │
│ - Recent announcements │
└──────────┬─────────────┘
           │
           v
┌────────────────────────┐
│ 4. RAG Prompt Assembly │
│ Context: [10 articles] │
│ Question: Analyze TCS  │
│ Instructions: ...      │
└──────────┬─────────────┘
           │
           v
┌────────────────────────┐
│ 5. Azure OpenAI GPT-4 │
│ Generate analysis with │
│ grounded context       │
└────────────────────────┘
```

**Code Example** (`backend/app/services/rag.py`):
```python
def generate_analysis(query: str, ticker: str):
    # 1. Retrieve relevant context
    results = embedding_service.query_similar(
        query_text=query,
        n_results=10,
        filter_metadata={\"ticker\": ticker},
        collection_type=\"news\"
    )
    
    # 2. Construct RAG prompt
    context = \"\\n\".join(results[\"documents\"])
    prompt = f\"\"\"
    Context from recent news:
    {context}
    
    Question: {query}
    
    Provide detailed analysis with:
    - Sentiment (bullish/bearish/neutral)
    - Key insights
    - Risk factors
    - Prediction
    \"\"\"
    
    # 3. Call Azure OpenAI
    response = openai.ChatCompletion.create(
        model=\"gpt-4\",
        messages=[{\"role\": \"user\", \"content\": prompt}]
    )
    
    return response
```

---

### ChromaDB Performance & Cost

| Metric | Value | Notes |
|--------|-------|-------|
| **Embedding Model** | all-MiniLM-L6-v2 | FREE (local, no API) |
| **Vector Dimensions** | 384 | Optimal for semantic search |
| **Storage per doc** | 2-5KB | Text + embedding + metadata |
| **Query Latency** | 10-200ms | Depends on collection size |
| **Ingestion Latency** | 100-500ms | Parallel embedding generation |
| **Disk Space (current)** | 5-50MB | Depends on doc count |
| **Disk Space (1 year)** | 50-500MB | With regular cleanup |

**Cost**:
- **Embedding Generation**: FREE (local SentenceTransformers)
- **Storage**: Included in VPS disk
- **Alternative (Azure OpenAI Embeddings)**: $0.0001 per 1K tokens (~$5-20/month for 1000 users)

**Why Local Embeddings?**:
- ✅ Zero cost
- ✅ No API rate limits
- ✅ Low latency (no network calls)
- ✅ Privacy (no data sent to third parties)
- ❌ Slightly lower quality than text-embedding-ada-002 (but good enough for most use cases)

---

## Redis (Cache & Rate Limiting)

### Redis Specifications

- **Version**: Redis 7-alpine
- **Memory Limit**: 256MB
- **Eviction Policy**: allkeys-lru (Least Recently Used)
- **Persistence**: AOF (Append-Only File) enabled
- **Container**: stockmarket_redis

**Configuration**:
```bash
redis-server \
  --appendonly yes \           # Persistence
  --maxmemory 256mb \          # Memory limit
  --maxmemory-policy allkeys-lru  # Evict oldest keys when full
```

### Redis Key Patterns

#### 1. **JWT Keys** (3 keys)

**Purpose**: Store current and previous JWT signing keys

```bash
# Current signing key
jwt:keys:current
Value: {\"key_id\":\"2025-12-11T12:44:12Z\",\"secret_key\":\"H4hA...\",\"expires_at\":\"2025-12-14T12:44:12Z\"}
TTL: 604800 (7 days)

# Previous rotation 1
jwt:keys:previous_1
Value: {\"key_id\":\"2025-12-10T12:44:12Z\",\"secret_key\":\"G3gB...\",\"expires_at\":\"2025-12-13T12:44:12Z\"}
TTL: 604800

# Previous rotation 2
jwt:keys:previous_2
Value: {\"key_id\":\"2025-12-09T12:44:12Z\",\"secret_key\":\"F2fC...\",\"expires_at\":\"2025-12-12T12:44:12Z\"}
TTL: 604800

# Last rotation timestamp
jwt:keys:last_rotation
Value: 1765457052 (Unix timestamp)
TTL: -1 (no expiration)
```

**Verification Statistics**:
```bash
jwt:stats:verifications:current
jwt:stats:verifications:previous_1
jwt:stats:verifications:previous_2
```

---

#### 2. **Rate Limiting Keys** (Multiple dimensions)

**Format**: `rate_limit:{role}:{dimension}:{identifier}:{type}`

**Examples**:
```bash
# User-based (primary for authenticated users)
rate_limit:user:user:123:analysis
Value: 3 (number of requests)
TTL: 86400 (24 hours from first request)

# Session-based
rate_limit:user:session:7c410e19-c23c-4689-aa2d-fa9334dd730d:analysis
Value: 2
TTL: 86400

# IP-based (primary for guests)
rate_limit:user:ip:2925189ad34fcc10:analysis
Value: 4
TTL: 86400

# Device-based
rate_limit:user:device:6ee72b9429a81cd035fe7213c780de12:analysis
Value: 2
TTL: 86400

# Guest (IP-based)
rate_limit:guest:ip:a1b2c3d4e5f6789:analysis
Value: 1
TTL: 86400
```

**Logic**:
1. User requests analysis
2. Backend checks ALL related keys:
   - `rate_limit:user:user:{user_id}:analysis`
   - `rate_limit:user:session:{session_id}:analysis`
   - `rate_limit:user:ip:{ip_hash}:analysis`
   - `rate_limit:user:device:{device_fp}:analysis`
3. If ANY key >= limit → **429 Too Many Requests**
4. Otherwise: INCR all keys, set TTL 86400s on first INCR

**Why 4 dimensions?**:
- **User ID**: Primary (prevents user from exceeding quota)
- **Session**: Prevents multi-tab abuse
- **IP**: Prevents proxy/VPN switching
- **Device**: Prevents multi-browser abuse

---

#### 3. **Device Tracking Keys**

```bash
# Device activity tracking
device_activity:6ee72b9429a81cd035fe7213c780de12:registration
Value: {\"registered_at\":1702562400,\"last_seen\":1702648800}
TTL: 604800 (7 days)

# Device token secret (for encryption)
device_token:secret_key
Value: <RSA_PUBLIC_KEY_PEM>
TTL: -1 (persistent)
```

---

#### 4. **Stock Info Cache**

```bash
# Cached stock data (1-hour TTL)
stock_info:TCS.NS
Value: {\"ticker\":\"TCS.NS\",\"current_price\":3188.15,\"day_change\":+12.50,...}
TTL: 3600 (1 hour)

stock_info:RELIANCE.NS
Value: {\"ticker\":\"RELIANCE.NS\",\"current_price\":2455.75,...}
TTL: 3600
```

**Purpose**: Reduce API calls to Yahoo Finance/Alpha Vantage

---

### Redis Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| **Avg Read Latency** | <1ms | In-memory, local network |
| **Avg Write Latency** | <1ms | Async AOF write |
| **Memory Usage** | 10-50MB | Depends on active keys |
| **Max Memory** | 256MB | LRU eviction when full |
| **Connections** | 5-20 | FastAPI connection pool |
| **Persistence** | AOF (every second) | Fsync every 1 sec |

**Cost**:
- **Current (Docker)**: Free
- **Managed Redis (AWS ElastiCache)**: ~$15/month (cache.t3.micro)
- **Self-hosted**: $5-10/month

---

## Data Flow & Integration

### Analysis Request Flow (All 3 Databases)

```
User Request: GET /stocks/TCS/analysis
     │
     v
┌────────────────────┐
│ 1. REDIS CHECK     │
│ GET analysis_cache:│
│     TCS            │
└──────┬─────────────┘
       │ Cache MISS
       v
┌────────────────────┐
│ 2. RATE LIMIT      │
│ (REDIS)            │
│ Check:             │
│ - rate_limit:user:*│
│ - Incr if allowed  │
└──────┬─────────────┘
       │ Allowed
       v
┌────────────────────┐
│ 3. VECTOR SEARCH   │
│ (ChromaDB)         │
│ Query stock_news   │
│ for ticker=TCS     │
│ → Top 10 articles  │
└──────┬─────────────┘
       │
       v
┌────────────────────┐
│ 4. RAG GENERATION  │
│ (Azure OpenAI)     │
│ Context from       │
│ ChromaDB + GPT-4   │
└──────┬─────────────┘
       │
       v
┌────────────────────┐
│ 5. STORE RESULTS   │
│ (ALL 3 DBs)        │
│                    │
│ MySQL:             │
│ - analysis_history │
│   (ticker, user,   │
│    sentiment)      │
│                    │
│ Redis:             │
│ - analysis_cache:  │
│   TCS (1h TTL)     │
│                    │
│ ChromaDB:          │
│ - stock_analysis   │
│   (for future RAG) │
└────────────────────┘
```

### Authentication Flow (MySQL + Redis)

```
POST /auth/login
     │
     v
┌────────────────────┐
│ 1. VERIFY PASSWORD │
│ (MySQL)            │
│ SELECT * FROM users│
│ WHERE email=...    │
│ → bcrypt verify    │
└──────┬─────────────┘
       │ Valid
       v
┌────────────────────┐
│ 2. GET JWT KEY     │
│ (Redis)            │
│ GET jwt:keys:      │
│     current        │
└──────┬─────────────┘
       │
       v
┌────────────────────┐
│ 3. CREATE TOKENS   │
│ - Access (24h)     │
│ - Refresh (7d)     │
│ Sign with CURRENT  │
│ JWT key            │
└──────┬─────────────┘
       │
       v
┌────────────────────┐
│ 4. STORE SESSION   │
│ (MySQL)            │
│ INSERT INTO        │
│ refresh_tokens     │
│ - Hash token       │
│ - Device metadata  │
│ - GeoIP location   │
└──────┬─────────────┘
       │
       v
┌────────────────────┐
│ 5. TRACK LOGIN     │
│ (MySQL)            │
│ INSERT INTO        │
│ login_history      │
└────────────────────┘
```

---

## Feature Dependencies

### Feature → Database Mapping

| Feature | MySQL | ChromaDB | Redis | Cost/Latency |
|---------|-------|----------|-------|--------------|
| **User Registration** | ✅ users | ❌ | ❌ | Free / <50ms |
| **Login** | ✅ users, login_history | ❌ | ✅ JWT keys | Free / <50ms |
| **JWT Refresh** | ✅ refresh_tokens | ❌ | ✅ JWT keys | Free / <50ms |
| **Session Management** | ✅ refresh_tokens | ❌ | ✅ Device tracking | Free / <50ms |
| **Rate Limiting** | ❌ | ❌ | ✅ rate_limit:* | Free / <1ms |
| **Stock Analysis (RAG)** | ✅ analysis_history | ✅ stock_news, stock_analysis | ✅ Cache | GPT-4: $0.03-0.10 per analysis / 2-5s |
| **Watchlist** | ✅ watchlist | ❌ | ❌ | Free / <10ms |
| **Saved Analyses** | ✅ saved_analyses | ❌ | ❌ | Free / <20ms |
| **Admin Traffic Stats** | ✅ traffic_stats | ❌ | ❌ | Free / <100ms |
| **Stock Info (cached)** | ❌ | ❌ | ✅ stock_info:* | Free if cached / <1ms |

### RAG System Dependencies

```
RAG Analysis Pipeline:
├── Data Ingestion (ChromaDB + MySQL)
│   ├── News scraper → MySQL (raw articles)
│   ├── Embedding generation → ChromaDB (vectors)
│   └── Metadata indexing → ChromaDB (ticker, date)
│
├── Query Processing (All 3)
│   ├── Rate limiting → Redis (check quota)
│   ├── Cache check → Redis (analysis_cache:*)
│   └── User tracking → MySQL (analysis_history)
│
├── Vector Search (ChromaDB)
│   ├── Query embedding (all-MiniLM-L6-v2)
│   ├── Semantic search (stock_news collection)
│   └── Context retrieval (top 10 articles)
│
├── Analysis Generation (Azure OpenAI)
│   ├── RAG prompt assembly
│   ├── GPT-4 generation
│   └── Response parsing
│
└── Storage (All 3)
    ├── Cache result → Redis (1h TTL)
    ├── Track request → MySQL (analysis_history)
    └── Store analysis → ChromaDB (for future reference)
```

---

## Performance & Cost Analysis

### Latency Profile

| Operation | MySQL | ChromaDB | Redis | Total |
|-----------|-------|----------|-------|-------|
| **User Login** | 30ms | - | 1ms | 31ms |
| **JWT Verify** | - | - | 1ms | 1ms |
| **Rate Limit Check** | - | - | 1ms | 1ms |
| **Stock Info (cached)** | - | - | 1ms | 1ms |
| **Stock Info (uncached)** | - | - | 100ms (API) | 100ms |
| **Vector Search** | - | 50ms | - | 50ms |
| **RAG Analysis (cold)** | 20ms | 100ms | 1ms | 2-5s (OpenAI dominant) |
| **RAG Analysis (cached)** | - | - | 1ms | 1ms |
| **Save Watchlist** | 15ms | - | - | 15ms |

### Storage Estimates (1 Year, 1000 Active Users)

| Database | Current | 1 Year Projection | Growth Rate |
|----------|---------|-------------------|-------------|
| **MySQL** | 50-100MB | 500MB-1GB | Linear with users |
| **ChromaDB** | 5-50MB | 50-500MB | Linear with ingestion |
| **Redis** | 10-50MB | 50-100MB | Stable (LRU eviction) |
| **Total** | 65-200MB | 600MB-1.6GB | Manageable on VPS |

### Cost Analysis (Monthly, Production)

#### Self-Hosted (Current Setup)
```
VPS (4GB RAM, 80GB SSD): $20/month
├── MySQL: Included
├── Redis: Included
└── ChromaDB: Included

Azure OpenAI GPT-4: ~$50-200/month
├── Depends on usage
└── 1000 analyses ≈ $30-100

Total: $70-220/month
```

#### Managed Services (Alternative)
```
AWS RDS MySQL (db.t3.micro): $15/month
AWS ElastiCache Redis (cache.t3.micro): $15/month
VPS for ChromaDB (2GB): $10/month
Azure OpenAI GPT-4: $50-200/month

Total: $90-240/month
```

**Recommendation**: Self-hosted is cost-effective for <5000 users

---

## Summary

### Database Strengths

| Database | Best For | Avoid For |
|----------|----------|-----------|
| **MySQL** | Structured data, ACID transactions, relationships | Unstructured data, high-frequency writes |
| **ChromaDB** | Semantic search, RAG, embeddings | Structured queries, transactions |
| **Redis** | Caching, rate limiting, ephemeral data | Long-term storage, complex queries |

### Optimization Tips

1. **MySQL**:
   - Regular index analysis (`EXPLAIN` queries)
   - Cleanup old `login_history` (>90 days)
   - Archive `traffic_stats` (>1 year)

2. **ChromaDB**:
   - Periodic cleanup of old news (>30 days)
   - Batch embedding generation
   - Consider GPU for faster embeddings at scale

3. **Redis**:
   - Monitor memory usage (`INFO memory`)
   - Tune eviction policy if needed
   - Consider Redis Sentinel for HA

### Monitoring Queries

**MySQL Health**:
```sql
-- Check table sizes
SELECT 
    table_name,
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
FROM information_schema.TABLES
WHERE table_schema = 'stockmarket_db'
ORDER BY size_mb DESC;

-- Check slow queries
SHOW FULL PROCESSLIST;
```

**Redis Health**:
```bash
# Memory usage
redis-cli INFO memory

# Key count by pattern
redis-cli --scan --pattern "rate_limit:*" | wc -l

# Eviction stats
redis-cli INFO stats | grep evicted
```

**ChromaDB Health**:
```python
# Collection sizes
print(f\"News: {embedding_service.news_collection.count()} documents\")
print(f\"Analysis: {embedding_service.analysis_collection.count()} documents\")
```

---

*End of Database Infrastructure Documentation*
