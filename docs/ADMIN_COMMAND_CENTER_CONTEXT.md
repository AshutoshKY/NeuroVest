# NeuroVest Admin Command Center - System Context

> **⚠️ DEPRECATED**: This file is now superseded by **[ADMIN_GUIDE.md](./ADMIN_GUIDE.md)**.
> Please refer to the new guide for up-to-date information on the Admin Command Center.

> **Purpose**: Legacy codebase analysis (Archived).
> **Last Updated**: 2026-01-10 | **Status**: Archived


---

## 🚨 CRASH RECOVERY CHECKLIST

If starting a new session:
1. Read this file first
2. Check progress in `.agent/workflows/admin-command-center.md`
3. Ask user: "Which phase should I continue from?"

---

## Project Overview

**What**: AI-powered Indian stock market analysis platform with Admin Command Center
**Tech**: FastAPI + Next.js + MySQL + Redis + ChromaDB + Azure OpenAI (GPT-4)
**Key Principle**: LLM is a RENDERER, not a decision-maker. Signals are deterministic.

---

## Directory Structure (Critical Paths)

```
/Volumes/AshDrive/prjts/stockmarket/
├── backend/app/
│   ├── core/
│   │   ├── config.py        # Settings (pydantic), env vars, database URLs
│   │   ├── security.py      # JWT creation: create_access_token(), verify_token()
│   │   ├── jwt_key_manager.py  # Key rotation (24h, 3-key window)
│   │   ├── redis_client.py  # get_redis() - returns Redis connection
│   │   └── database.py      # get_db() - SQLAlchemy session
│   │
│   ├── middleware/
│   │   ├── auth_middleware.py    # get_current_user(), get_current_admin()
│   │   ├── security_middleware.py # IP blacklist, toggles, DDOS
│   │   └── rate_limit_middleware.py # 4-dimensional rate limiting
│   │
│   ├── api/
│   │   ├── auth.py          # /auth/login, /auth/register, /auth/refresh
│   │   ├── admin_management.py # /admin/users, /admin/system-toggles, /admin/audit-logs
│   │   ├── stocks.py        # /stocks/{ticker}/analysis
│   │   └── ...other routes
│   │
│   ├── models/
│   │   └── user.py          # User, RefreshToken, LoginHistory, UserRole enum
│   │
│   ├── services/
│   │   ├── rag.py           # RAGService - main AI analysis
│   │   ├── sentiment.py     # AsyncAzureOpenAI sentiment analysis
│   │   ├── embeddings.py    # EmbeddingService - ChromaDB + SentenceTransformers
│   │   └── encryption_service.py # RSA encryption
│   │
│   └── utils/
│       └── aes_decryption.py # AESDecryptor for FE→BE encryption
│
├── frontend/src/
│   ├── app/
│   │   ├── admin/           # Partial admin pages (need completion)
│   │   ├── auth/login/      # Login page
│   │   └── dashboard/       # User dashboard
│   │
│   ├── lib/
│   │   ├── api.ts           # APIClient with encryption, auto-refresh
│   │   ├── activity-tracker.ts # Token refresh on activity
│   │   └── tracking-headers.ts # Device/session tracking
│   │
│   └── components/          # React components
│
├── design_poc_1/neurovest-admin/  # UI DESIGN (SOURCE OF TRUTH)
│   ├── admin_overview.html
│   ├── admin_infrastructure.html
│   ├── admin_ai_rag.html
│   ├── admin_api_health.html
│   ├── admin_users.html
│   ├── admin_security.html
│   └── admin_controls.html
│
└── docs/
    ├── JWT_AUTHENTICATION.md
    ├── RATE_LIMITING.md
    ├── DATABASE_INFRASTRUCTURE.md
    └── RAG_SYSTEM.md
```

---

## Key Code Patterns (Copy-Paste Ready)

### 1. JWT Token Creation
```python
# backend/app/core/security.py
from app.core.jwt_key_manager import get_jwt_key_manager

def create_access_token(data: dict, expires_delta=None):
    key_manager = get_jwt_key_manager()
    secret_key = key_manager.get_current_key()  # Rotated every 24h
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=1440))
    to_encode.update({"exp": int(expire.timestamp()), "type": "access"})
    return jwt.encode(to_encode, secret_key, algorithm="HS256")
```

### 2. Admin Check Pattern
```python
# backend/app/api/admin_management.py
from app.middleware.auth_middleware import get_current_user
from app.models.user import User

def check_admin(current_user: User):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

@router.get("/admin/users")
async def list_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_admin(current_user)
    # ... admin logic
```

### 3. System Toggles (Redis)
```python
# backend/app/api/admin_management.py
from app.core.redis_client import get_redis

redis = get_redis()
toggles = {
    "login_enabled": redis.get("system:login_enabled") != b"0",
    "signup_enabled": redis.get("system:signup_enabled") != b"0",
    "maintenance_mode": redis.get("system:maintenance") == b"1",
}
```

### 4. Audit Logging
```python
async def log_admin_action(db, admin_user_id, action, target, changes_json, ip_address):
    db.execute(text("""
        INSERT INTO admin_audit_logs (admin_user_id, action, target, changes_json, ip_address, timestamp)
        VALUES (:admin_id, :action, :target, :changes, :ip, NOW())
    """), {"admin_id": admin_user_id, "action": action, "target": target, "changes": changes_json, "ip": ip_address})
    db.commit()
```

### 5. Frontend API Client Pattern
```typescript
// frontend/src/lib/api.ts
const apiClient = new APIClient();  // Singleton

// Auto-adds tracking headers, auto-refreshes tokens, auto-encrypts auth data
apiClient.post('/auth/login', { email, password });  // Encrypted automatically
apiClient.get('/admin/users');  // Token from httpOnly cookie
```

---

## Database Schema (Key Tables)

```sql
-- Users table with roles
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(10) DEFAULT 'user',  -- 'user' or 'admin'
    is_active BOOLEAN DEFAULT TRUE,
    failed_login_attempts INT DEFAULT 0,
    locked_until DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Admin audit logs
CREATE TABLE admin_audit_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    admin_user_id INT NOT NULL,
    action VARCHAR(100),
    target VARCHAR(255),
    changes_json TEXT,
    ip_address VARCHAR(45),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- IP blacklist
CREATE TABLE ip_blacklist (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ip_address VARCHAR(45) UNIQUE NOT NULL,
    reason VARCHAR(255),
    blocked_by_user_id INT,
    auto_flagged BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Redis Key Patterns

| Key Pattern | Type | Purpose |
|-------------|------|---------|
| `jwt:keys:current` | JSON | Current signing key |
| `jwt:keys:previous_1/2` | JSON | Previous keys for verification |
| `system:login_enabled` | String | "1" or "0" |
| `system:signup_enabled` | String | "1" or "0" |
| `system:maintenance` | String | "1" or "0" |
| `rate_limit:{role}:{dim}:{id}` | Counter | Rate limit tracking |
| `analysis_cache:{ticker}` | JSON | 1-hour analysis cache |

---

## What Exists vs What's Missing

### ✅ EXISTS (Do Not Rebuild)
- JWT auth with key rotation
- AES/RSA encryption for FE→BE
- Basic admin APIs (users, toggles, audit logs, IP blacklist)
- Security middleware (IP blacklist, DDOS, toggles)
- Rate limiting (4-dimensional)
- RAG system with ChromaDB
- Logging with loguru

### ❌ MISSING (To Build)
- SUPER_ADMIN role for dangerous operations
- JWT invalidation / Force logout mechanism
- Centralized kill switch with typed confirmation
- Request metrics infrastructure
- Infrastructure metrics (Redis/MySQL/ChromaDB)
- AI cost tracking
- Complete admin dashboard UI (7 pages)

---

## Environment Variables (config.py)

```python
# Critical settings from backend/.env
MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT
JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES (1440 = 24h)
RATE_LIMIT_ENABLED (True/False)
LOG_LEVEL (INFO/DEBUG), LOG_FORMAT (structured/simple)
```

---

## Design File Reference (All 7 Pages)

| Page | Key Widgets | Backend Data Needed |
|------|-------------|---------------------|
| overview | KPIs, Traffic chart, Health radar, Alerts | Live users, RPS, error rate |
| infrastructure | Redis/MySQL/ChromaDB charts | Infra metrics |
| ai-rag | Token usage, Cost, Guardrail rejections | AI metrics |
| api-health | External API status cards | API health checks |
| users | Distribution map, Session/Retention charts | User analytics |
| security | Attack vectors, WAF blocks, Audit log | Security events |
| controls | Kill switches, Toggles | Redis toggles, confirm actions |

---

## Docker Commands

```bash
# Start everything
cd /Volumes/AshDrive/prjts/stockmarket && docker-compose up -d

# Check services
docker ps --format "table {{.Names}}\t{{.Status}}"

# View backend logs
docker logs stockmarket-backend-1 --tail 100 -f

# Rebuild backend after changes
docker-compose build backend && docker-compose up -d backend
```

---

## Questions Pending User Decision

1. **SUPER_ADMIN**: Create new role OR use admin + confirmation modal?
2. **JWT Invalidation**: Global auth_epoch OR per-user token_version?
3. **Priority**: All 8 phases OR specific features first?

---

## Phase Completion Status

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | System Discovery | ✅ COMPLETE |
| 1 | RBAC & Trust Model | ⏳ Pending |
| 2 | JWT Invalidation | ⏳ Pending |
| 3 | Kill Switches | ⏳ Pending |
| 4 | Metrics Infrastructure | ⏳ Pending |
| 5 | AI & RAG Metrics | ⏳ Pending |
| 6 | Admin Backend APIs | ⏳ Pending |
| 7 | Frontend Dashboard | ⏳ Pending |
| 8 | Audit & Safety Net | ⏳ Pending |
