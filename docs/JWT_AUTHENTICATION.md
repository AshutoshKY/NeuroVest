# JWT Authentication System - Technical Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Key Components](#key-components)
4. [Storage Infrastructure](#storage-infrastructure)
5. [Key Rotation System](#key-rotation-system)
6. [Token Lifecycle](#token-lifecycle)
7. [API Endpoints](#api-endpoints)
8. [Database Schema](#database-schema)
9. [Redis Keys](#redis-keys)
10. [Configuration](#configuration)
11. [Testing & Verification](#testing--verification)
12. [Troubleshooting](#troubleshooting)

---

## Overview

The JWT authentication system implements **seamless key rotation** with **dual Redis+MySQL storage**, ensuring users remain logged in even during backend restarts. Features include:

- ✅ **24-hour access tokens** with automatic refresh
- ✅ **7-day refresh tokens** for long-term sessions
- ✅ **Automatic key rotation** every 24 hours (activity-based)
- ✅ **3-key verification window** (current, previous_1, previous_2)
- ✅ **Dual storage**: Redis (fast) + MySQL (persistent)
- ✅ **Zero-downtime restarts** - users stay logged in
- ✅ **Activity-based token refresh** on frontend

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    JWT Authentication Flow                       │
└─────────────────────────────────────────────────────────────────┘

┌──────────┐          ┌──────────────┐          ┌──────────────┐
│  Client  │          │   Backend    │          │   Storage    │
│ (Browser)│          │  (FastAPI)   │          │  MySQL+Redis │
└─────┬────┘          └──────┬───────┘          └──────┬───────┘
      │                      │                         │
      │  1. POST /auth/login │                         │
      ├─────────────────────►│                         │
      │                      │   2. Verify credentials │
      │                      ├────────────────────────►│
      │                      │                         │
      │                      │   3. Get current key    │
      │                      │      from manager       │
      │                      │◄────────────────────────┤
      │                      │   (Redis → SQL)         │
      │                      │                         │
      │   4. JWT + cookies   │                         │
      │◄─────────────────────┤                         │
      │   (24hr access,      │                         │
      │    7day refresh)     │                         │
      │                      │                         │
      │  5. GET /api/* +JWT  │                         │
      ├─────────────────────►│                         │
      │                      │   6. Verify with keys   │
      │                      │      (current, prev_1,  │
      │                      │       prev_2)           │
      │                      ├────────────────────────►│
      │                      │◄────────────────────────┤
      │                      │                         │
      │   7. Response        │                         │
      │◄─────────────────────┤                         │
      │                      │                         │
      │                      │  Background: Hourly     │
      │                      │  rotation task          │
      │                      ├────────────────────────►│
      │                      │  - Check 24hrs passed   │
      │                      │  - Check user activity  │
      │                      │  - Rotate keys          │
      │                      │                         │
```

### Key Rotation Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   Dual Storage Architecture                      │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────┐         ┌──────────────────────┐
│     Redis Cache      │◄───────►│    MySQL Database    │
│  (Fast Access ~1ms)  │  Sync   │  (Persistent Store)  │
└──────────┬───────────┘         └──────────┬───────────┘
           │                                 │
           │    ┌────────────────────────┐   │
           └───►│  JWT Key Manager       │◄──┘
                │  - Load keys           │
                │  - Rotate keys         │
                │  - Sync storage        │
                └────────┬───────────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
    ┌─────▼─────┐  ┌────▼────┐  ┌─────▼─────┐
    │  CURRENT  │  │PREVIOUS_1│  │PREVIOUS_2 │
    │  (Sign)   │  │ (Verify) │  │ (Verify)  │
    └───────────┘  └──────────┘  └───────────┘
```

### Key Lifecycle State Machine

```
┌─────────────────────────────────────────────────────────────────┐
│                    Key Rotation Lifecycle                        │
└─────────────────────────────────────────────────────────────────┘

    NEW KEY GENERATED (T=0)
           │
           ├─► Status: CURRENT
           │   Used for: Signing new tokens
           │   TTL: 24 hours
           │   Verification: ✅
           │
           ▼ (After 24hrs rotation)
           │
           ├─► Status: PREVIOUS_1
           │   Used for: Verification only
           │   TTL: 48 hours total
           │   Verification: ✅
           │
           ▼ (After second 24hrs rotation)
           │
           ├─► Status: PREVIOUS_2
           │   Used for: Verification only
           │   TTL: 72 hours total
           │   Verification: ✅
           │
           ▼ (After third 24hrs rotation)
           │
           └─► Status: EXPIRED
               Deleted from Redis
               Marked inactive in MySQL
               Verification: ❌
```

---

## Key Components

### 1. JWT Key Manager
**Location**: `backend/app/core/jwt_key_manager.py`

**Responsibilities**:
- Generate cryptographically secure keys (256-bit)
- Store keys in both Redis and MySQL
- Load keys on startup from MySQL → Redis
- Rotate keys every 24 hours (activity-based)
- Provide current key for signing
- Provide all valid keys for verification

**Key Methods**:
```python
class JWTKeyManager:
    def sync_from_sql() -> None:
        """Load keys from MySQL to Redis on startup"""
        
    def get_current_key() -> str:
        """Get active signing key (CURRENT)"""
        
    def get_verification_keys() -> List[str]:
        """Get all 3 valid keys [current, previous_1, previous_2]"""
        
    def rotate_keys(force: bool = False) -> bool:
        """Rotate keys if conditions met"""
        
    def should_rotate() -> bool:
        """Check if 24 hours passed"""
```

### 2. Security Module
**Location**: `backend/app/core/security.py`

**Token Creation**:
```python
def create_access_token(data: dict) -> str:
    """
    Create JWT access token using CURRENT key.
    Expires in 24 hours.
    """
    key_manager = get_jwt_key_manager()
    secret_key = key_manager.get_current_key()
    
    payload = {
        "sub": str(user_id),
        "role": user_role,
        "exp": timestamp + 24hrs,
        "type": "access"
    }
    
    return jwt.encode(payload, secret_key, algorithm="HS256")
```

**Token Verification** (Multi-Key):
```python
def verify_token(token: str) -> Optional[dict]:
    """
    Verify JWT using any of the 3 valid keys.
    Tries current → previous_1 → previous_2.
    """
    keys = key_manager.get_verification_keys()
    
    for i, secret_key in enumerate(keys):
        try:
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            # Success!
            return payload
        except JWTError:
            continue  # Try next key
    
    return None  # All keys failed
```

### 3. Background Rotation Task
**Location**: `backend/app/tasks/key_rotation_task.py`

**How It Works**:
```python
async def key_rotation_scheduler():
    """Runs every hour, rotates if conditions met"""
    
    while True:
        if should_rotate():  # 24hrs passed?
            if users_active():  # Any active sessions?
                rotate_keys()
        
        await asyncio.sleep(3600)  # 1 hour
```

**Activity Check**:
```python
def _check_user_activity() -> bool:
    """Check Redis for recent user activity"""
    rate_limit_keys = redis.keys("rate_limit:*")
    return len(rate_limit_keys) > 0
```

### 4. Frontend Activity Tracker
**Location**: `frontend/src/lib/activity-tracker.ts`

**Auto-Refresh Logic**:
```typescript
class ActivityTracker {
  // Check every 5 minutes
  checkInterval = setInterval(() => {
    const timeSinceActivity = Date.now() - lastActivityTime;
    
    // If active in last 5 min AND page visible
    if (timeSinceActivity < 5 * 60 * 1000 && !document.hidden) {
      await apiClient.post('/auth/refresh');  // Get new tokens
    }
  }, 5 * 60 * 1000);
}
```

---

## Storage Infrastructure

### MySQL Database

**Table**: `jwt_keys`

```sql
CREATE TABLE jwt_keys (
    id INT AUTO_INCREMENT PRIMARY KEY,
    key_id VARCHAR(50) UNIQUE NOT NULL 
        COMMENT 'Unique identifier (e.g., 2025-12-11T12:44:12Z)',
    secret_key TEXT NOT NULL 
        COMMENT 'Base64-encoded JWT secret (urlsafe)',
    status ENUM('current', 'previous_1', 'previous_2', 'expired') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL 
        COMMENT 'created_at + 72 hours',
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMP NULL,
    
    INDEX idx_status (status),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Example Data**:
```
+----+---------------------+------------------+---------+---------------------+
| id | key_id              | status           | created | expires             |
+----+---------------------+------------------+---------+---------------------+
| 1  | 2025-12-11T12:44:12Z| current          | ...     | 2025-12-14T12:44:12Z|
| 2  | 2025-12-10T12:44:12Z| previous_1       | ...     | 2025-12-13T12:44:12Z|
| 3  | 2025-12-09T12:44:12Z| previous_2       | ...     | 2025-12-12T12:44:12Z|
+----+---------------------+------------------+---------+---------------------+
```

### Redis Cache

**Keys**:
```
jwt:keys:current           → JSON: {key_id, secret_key, expires_at}
jwt:keys:previous_1        → JSON: {key_id, secret_key, expires_at}
jwt:keys:previous_2        → JSON: {key_id, secret_key, expires_at}
jwt:keys:last_rotation     → UNIX timestamp
jwt:stats:verifications:current    → Counter
jwt:stats:verifications:previous_1 → Counter
jwt:stats:verifications:previous_2 → Counter
```

**TTL**: 7 days (longer than any key lifecycle)

---

## Key Rotation System

### Rotation Trigger Conditions

1. **Time-based**: 24 hours since last rotation
2. **Activity-based**: Users must be active (rate limit keys in Redis)
3. **Manual**: Can force rotate with `rotate_keys(force=True)`

### Rotation Process

```
Step 1: Check Conditions
├─► Time: 24hrs passed? ✓
├─► Activity: Users active? ✓
└─► Proceed with rotation

Step 2: Generate New Key
├─► Create 256-bit random key
├─► Generate unique key_id (timestamp)
└─► Set expiry (created_at + 72hrs)

Step 3: SQL Transaction (Atomic)
├─► BEGIN TRANSACTION
├─► UPDATE: current → previous_1
├─► UPDATE: previous_1 → previous_2
├─► UPDATE: previous_2 → expired (is_active=false)
├─► INSERT: new current key
└─► COMMIT

Step 4: Update Redis
├─► Store new current key
├─► Update previous_1 key
├─► Update previous_2 key
└─► Set last_rotation timestamp

Step 5: Logging
└─► Log rotation event with stats
```

### SQL Rotation Query

```sql
-- Start transaction
START TRANSACTION;

-- Demote current to previous_1
UPDATE jwt_keys 
SET status = 'previous_1' 
WHERE status = 'current' AND is_active = TRUE;

-- Demote previous_1 to previous_2  
UPDATE jwt_keys 
SET status = 'previous_2' 
WHERE status = 'previous_1' AND is_active = TRUE;

-- Mark previous_2 as expired
UPDATE jwt_keys 
SET status = 'expired', is_active = FALSE 
WHERE status = 'previous_2' AND is_active = TRUE;

-- Insert new current key
INSERT INTO jwt_keys (key_id, secret_key, status, created_at, expires_at, is_active)
VALUES ('2025-12-12T12:44:12Z', 'new_secret_key', 'current', NOW(), NOW() + INTERVAL 72 HOUR, TRUE);

COMMIT;
```

---

## Token Lifecycle

### Access Token

**Creation**:
```python
# User logs in at 2:00 PM
token = create_access_token({"sub": "123", "role": "user"})

# Token payload:
{
  "sub": "123",
  "role": "user",
  "exp": 1702568400,  # 2:00 PM next day
  "type": "access"
}

# Signed with CURRENT key
```

**Storage**:
```http
Set-Cookie: access_token=eyJhbGc...
  HttpOnly
  SameSite=Lax
  Max-Age=86400  (24 hours)
  Secure (in production)
```

**Verification Flow**:
```
Request arrives with token
  │
  ├─► Extract from cookie
  │
  ├─► Get verification keys (3 keys)
  │
  ├─► Try CURRENT key
  │     ├─► Success? Return payload ✅
  │     └─► Fail? Continue
  │
  ├─► Try PREVIOUS_1 key
  │     ├─► Success? Return payload ✅
  │     └─► Fail? Continue
  │
  ├─► Try PREVIOUS_2 key
  │     ├─► Success? Return payload ✅
  │     └─► Fail? Continue
  │
  └─► All failed → 401 Unauthorized ❌
```

### Refresh Token

**Creation**:
```python
refresh_token = create_refresh_token({"sub": "123", "role": "user"})

# Token payload:
{
  "sub": "123",
  "role": "user",
  "exp": 1703168400,  # 7 days later
  "type": "refresh"
}
```

**Storage**:
```http
Set-Cookie: refresh_token=eyJhbGc...
  HttpOnly
  SameSite=Lax
  Max-Age=604800  (7 days)
  Secure (in production)
```

**Database Tracking**:
```sql
-- Store in refresh_tokens table
INSERT INTO refresh_tokens (user_id, token, expires_at, revoked)
VALUES (123, 'token_hash', '2025-12-18 14:00:00', FALSE);
```

---

## API Endpoints

### Authentication Endpoints

#### 1. Login
```bash
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}

# Response (200 OK)
Set-Cookie: access_token=...; HttpOnly; Max-Age=86400
Set-Cookie: refresh_token=...; HttpOnly; Max-Age=604800

{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testdemo@neurovest.com",
    "password": "your_password"
  }' \
  -c cookies.txt  # Save cookies
```

#### 2. Refresh Token
```bash
POST /auth/refresh
Cookie: refresh_token=...

# Response (200 OK)
Set-Cookie: access_token=...; HttpOnly; Max-Age=86400
Set-Cookie: refresh_token=...; HttpOnly; Max-Age=604800

{
  "access_token": "new_token...",
  "refresh_token": "new_refresh...",
  "token_type": "bearer"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/auth/refresh \
  -b cookies.txt \  # Use saved cookies
  -c cookies.txt    # Update cookies
```

#### 3. Get Current User
```bash
GET /auth/me
Cookie: access_token=...

# Response (200 OK)
{
  "id": 123,
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "user",
  "is_verified": true,
  "created_at": "2025-12-10T10:00:00Z"
}
```

**cURL Example**:
```bash
curl -X GET http://localhost:8000/auth/me \
  -b cookies.txt
```

#### 4. Logout
```bash
POST /auth/logout
Cookie: access_token=..., refresh_token=...

# Response (200 OK)
Set-Cookie: access_token=; Max-Age=0  # Delete cookie
Set-Cookie: refresh_token=; Max-Age=0

{
  "message": "Successfully logged out"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/auth/logout \
  -b cookies.txt
```

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role ENUM('user', 'admin') DEFAULT 'user',
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    failed_login_attempts INT DEFAULT 0,
    locked_until TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_email (email),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### Refresh Tokens Table
```sql
CREATE TABLE refresh_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### JWT Keys Table
(See [Storage Infrastructure](#mysql-database) section)

---

## Redis Keys

### JWT Keys
```bash
# Current signing key
jwt:keys:current
# Value: {"key_id":"2025-12-11T12:44:12Z","secret_key":"H4hAh...","expires_at":"2025-12-14T12:44:12Z"}

# Previous key (rotation 1)
jwt:keys:previous_1

# Previous key (rotation 2)
jwt:keys:previous_2

# Last rotation timestamp
jwt:keys:last_rotation
# Value: 1765457052
```

### Verification Statistics
```bash
# Counter for tokens verified with current key
jwt:stats:verifications:current

# Counter for tokens verified with previous_1
jwt:stats:verifications:previous_1

# Counter for tokens verified with previous_2
jwt:stats:verifications:previous_2
```

---

## Configuration

### Environment Variables
```bash
# .env file
JWT_SECRET_KEY=fallback_key_only  # Used only if manager fails
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Hardcoded Constants
```python
# In jwt_key_manager.py
KEY_ROTATION_HOURS = 24  # Rotate every 24 hours
KEY_EXPIRY_HOURS = 72    # Keep 3 keys active (24 * 3)

# In activity-tracker.ts
CHECK_INTERVAL_MS = 5 * 60 * 1000  # Check every 5 minutes
ACTIVITY_WINDOW_MS = 5 * 60 * 1000 # Consider active if action in last 5 min
```

---

## Testing & Verification

### Verify Key Manager Status
```bash
docker-compose exec backend python -c "
from app.core.jwt_key_manager import get_jwt_key_manager

km = get_jwt_key_manager()
print('Current Key:', km.get_current_key()[:20], '...')
print('Verification Keys:', len(km.get_verification_keys()))
print('Stats:', km.get_stats())
"
```

### Check MySQL Keys
```bash
docker-compose exec mysql mysql -u stockmarket_user -p stockmarket_db -e "
SELECT key_id, status, 
       TIMESTAMPDIFF(HOUR, created_at, NOW()) as age_hours,
       is_active 
FROM jwt_keys 
WHERE is_active = TRUE 
ORDER BY created_at DESC;
"
```

### Check Redis Keys
```bash
# List all JWT keys
docker-compose exec redis redis-cli KEYS "jwt:*"

# Get current key details
docker-compose exec redis redis-cli GET jwt:keys:current

# Get stats
docker-compose exec redis redis-cli GET jwt:stats:verifications:current
```

### Test Login & Verify Token
```bash
# 1. Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' \
  -c cookies.txt -v

# 2. Make authenticated request
curl -X GET http://localhost:8000/auth/me \
  -b cookies.txt

# 3. Refresh token
curl -X POST http://localhost:8000/auth/refresh \
  -b cookies.txt \
  -c cookies.txt
```

### Monitor Logs
```bash
# Watch JWT logs
docker-compose logs -f backend | grep -i jwt

# Watch rotation logs
docker-compose logs -f backend | grep -i rotation

# Watch verification logs
docker-compose logs -f backend | grep "Token verified"
```

---

## Troubleshooting

### Issue: "Token verified with static key"

**Diagnosis**:
```bash
# Check if key manager is active
docker-compose exec backend python -c "
from app.core.jwt_key_manager import get_jwt_key_manager
from app.core.config import settings
km = get_jwt_key_manager()
print('Using manager:', km.get_current_key() != settings.JWT_SECRET_KEY)
"
```

**Solution**: This was a logging bug (fixed). The system IS using the manager even when it shows "static key" before the fix.

### Issue: Users logged out after restart

**Diagnosis**:
```bash
# Check if keys persisted
docker-compose exec backend python -c "
from app.core.database import SessionLocal
from app.models.jwt_key import JWTKey
db = SessionLocal()
print('Keys in DB:', db.query(JWTKey).filter(JWTKey.is_active==True).count())
"
```

**Solution**: 
1. Ensure `jwt_keys` table exists
2. Check startup logs for key manager initialization
3. Verify Redis connection

### Issue: Rotation not happening

**Diagnosis**:
```bash
# Check last rotation time
docker-compose exec redis redis-cli GET jwt:keys:last_rotation

# Check rotation task logs
docker-compose logs backend | grep "KEY_ROTATION"
```

**Solution**:
1. Verify background task is running
2. Check if users are active (rate limit keys exist)
3. Ensure 24 hours have passed

### Issue: 401 Unauthorized after rotation

**Diagnosis**:
```bash
# Check number of verification keys
docker-compose exec backend python -c "
from app.core.jwt_key_manager import get_jwt_key_manager
km = get_jwt_key_manager()
print('Verification keys:', len(km.get_verification_keys()))
"
```

**Solution**:
- Should have 3 keys after rotations
- Old tokens verified with previous_1 or previous_2
- If only 1 key, rotation hasn't happened yet

---

## Performance Metrics

### Key Operations Latency

| Operation | Redis | MySQL | Total |
|-----------|-------|-------|-------|
| Get current key | 1-2ms | - | 1-2ms |
| Verify token | 1-5ms | - | 1-5ms |
| Rotate keys | 50ms | 200ms | 250ms |
| Sync from SQL | - | 100ms | 100ms |

### Storage Overhead

| Component | Size | Count |
|-----------|------|-------|
| JWT key | ~200 bytes | 3 active |
| Redis cache | ~600 bytes | Per key set |
| MySQL row | ~500 bytes | 3-10 rows |

---

## Security Considerations

1. **Key Generation**: Uses `secrets.token_bytes(32)` for cryptographic randomness
2. **HttpOnly Cookies**: Prevents XSS attacks
3. **SameSite=Lax**: Protects against CSRF
4. **Secure Flag**: Set to True in production (HTTPS)
5. **Token Expiration**: 24-hour access, 7-day refresh
6. **Key Rotation**: Regular rotation minimizes exposure
7. **Multi-Key Verification**: Graceful degradation during rotation
8. **Redis Security**: Password-protected, internal network only
9. **MySQL Security**: Strong password, limited user permissions

---

## Monitoring Checklist

- [ ] Current key age < 25 hours
- [ ] Rotation happens every 24 hours
- [ ] 3 keys active after 2+ rotations
- [ ] Verification stats show token distribution
- [ ] No fallback to static key warnings
- [ ] Users stay logged in through restarts
- [ ] Activity tracker refreshing tokens

---

## Future Enhancements

- [ ] Admin dashboard for key management
- [ ] Metrics export (Prometheus)
- [ ] Distributed lock for multi-instance rotation
- [ ] Key rotation webhooks/notifications
- [ ] Automatic key cleanup (expired keys)
- [ ] JWT blacklist for immediate revocation
