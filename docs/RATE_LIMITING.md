# Rate Limiting System - Technical Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Tracking Mechanisms](#tracking-mechanisms)
4. [Rate Limit Tiers](#rate-limit-tiers)
5. [Device Token Signing](#device-token-signing)
6. [Storage Infrastructure](#storage-infrastructure)
7. [Enforcement Flow](#enforcement-flow)
8. [API Endpoints](#api-endpoints)
9. [Database Schema](#database-schema)
10. [Redis Keys](#redis-keys)
11. [Configuration](#configuration)
12. [Testing & Verification](#testing--verification)
13. [Troubleshooting](#troubleshooting)

---

## Overview

The rate limiting system implements **multi-dimensional tracking** with **device token signing** to prevent abuse while maintaining user experience. Features include:

- ✅ **4-dimensional tracking**: Device, Session, IP, User ID
- ✅ **Signed device tokens**: HMAC-SHA256 signature verification
- ✅ **Rolling 24-hour windows** for analysis limits
- ✅ **Per-minute & per-hour** API limits
- ✅ **Role-based limits**: Guest, User, Admin
- ✅ **Redis-backed** for high performance
- ✅ **Graceful error handling** with detailed messages

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   Rate Limiting Architecture                     │
└─────────────────────────────────────────────────────────────────┘

┌──────────┐          ┌──────────────┐          ┌──────────────┐
│  Client  │          │   Backend    │          │    Redis     │
│ (Browser)│          │  (FastAPI)   │          │   (Store)    │
└─────┬────┘          └──────┬───────┘          └──────┬───────┘
      │                      │                         │
      │  1. Initial Request  │                         │
      ├─────────────────────►│                         │
      │                      │   2. Generate signed    │
      │                      │      device token       │
      │                      │   (HMAC-SHA256)         │
      │                      │                         │
      │  3. Device token     │                         │
      │◄─────────────────────┤                         │
      │  (stored in cookie)  │                         │
      │                      │                         │
      │  4. API Request +    │                         │
      │     Tracking Headers │                         │
      │  - Device Token      │                         │
      │  - Session ID        │                         │
      │  - IP Address        │                         │
      │  - User ID (cookie)  │                         │
      ├─────────────────────►│                         │
      │                      │   5. Validate device    │
      │                      │      token signature    │
      │                      │                         │
      │                      │   6. Build tracking     │
      │                      │      keys (4 dims)      │
      │                      │                         │
      │                      │   7. Check limits       │
      │                      ├────────────────────────►│
      │                      │   INCR rate_limit:*     │
      │                      │◄────────────────────────┤
      │                      │   count, TTL            │
      │                      │                         │
      │   8a. Success (200)  │                         │
      │◄─────────────────────┤   OR                    │
      │                      │                         │
      │   8b. Rate Limited   │                         │
      │       (429)          │                         │
      │◄─────────────────────┤                         │
      │                      │                         │
```

### Multi-Dimensional Tracking

```
┌─────────────────────────────────────────────────────────────────┐
│            4-Dimensional Rate Limit Tracking                     │
└─────────────────────────────────────────────────────────────────┘

          ┌────────────────────────────┐
          │   Incoming Request         │
          └────────────┬───────────────┘
                       │
          ┌────────────▼───────────────┐
          │   Extract Identifiers      │
          └────────────┬───────────────┘
                       │
       ┌───────────────┼───────────────┬───────────────┐
       │               │               │               │
┌──────▼──────┐ ┌─────▼──────┐ ┌──────▼──────┐ ┌─────▼──────┐
│   DEVICE    │ │  SESSION   │ │     IP      │ │   USER     │
│ Fingerprint │ │     ID     │ │  Address    │ │     ID     │
│  (signed)   │ │  (UUID)    │ │ (hashed)    │ │ (from JWT) │
└──────┬──────┘ └─────┬──────┘ └──────┬──────┘ └─────┬──────┘
       │              │               │               │
       │    Build Redis Keys (per dimension)          │
       │              │               │               │
  rate_limit:    rate_limit:    rate_limit:     rate_limit:
  guest:device:  guest:session: guest:ip:       user:user:
  abc123:        def456:        hash789:        12:
  analysis       analysis       analysis        analysis
       │              │               │               │
       └──────────────┴───────────────┴───────────────┘
                       │
          ┌────────────▼───────────────┐
          │   Check ALL dimensions     │
          │   (strictest wins)         │
          └────────────────────────────┘
```

### Device Token Signing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│              Device Token Generation & Validation                │
└─────────────────────────────────────────────────────────────────┘

GENERATION (Backend):
┌─────────────────────────┐
│ Device Fingerprint      │  Canvas hash, WebGL, fonts, etc.
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Create Payload          │
│ {                       │
│   fingerprint: "abc",   │
│   created_at: 1234567,  │
│   nonce: "random"       │
│ }                       │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Sign with HMAC-SHA256   │
│ key = SECRET_KEY        │
│ signature = hmac(...)   │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Encode Token            │
│ base64(payload.signature)│
└────────────┬────────────┘
             │
             ▼
   Send to client (cookie)


VALIDATION (Backend):
┌─────────────────────────┐
│ Receive Token           │
│ X-Device-Token header   │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Decode Token            │
│ base64_decode(token)    │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Extract Parts           │
│ payload, signature      │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Verify Signature        │
│ expected = hmac(payload)│
│ compare(expected, sig)  │
└────────────┬────────────┘
             │
      ┌──────┴──────┐
      │             │
  ✅ Valid      ❌ Invalid
      │             │
    Allow        Reject (401)
```

---

## Tracking Mechanisms

### 1. Device Fingerprinting

**Frontend Generation** (`device-token-manager.ts`):
```typescript
async generateFingerprint(): Promise<string> {
  const components = {
    canvas: await this.getCanvasFingerprint(),
    webgl: await this.getWebGLFingerprint(),
    fonts: await this.getFontFingerprint(),
    audio: await this.getAudioFingerprint(),
    screen: `${screen.width}x${screen.height}x${screen.colorDepth}`,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    language: navigator.language,
    platform: navigator.platform,
    hardwareConcurrency: navigator.hardwareConcurrency,
    deviceMemory: (navigator as any).deviceMemory,
    userAgent: navigator.userAgent
  };
  
  // Hash components
  const fingerprintString = JSON.stringify(components);
  return await this.hashSHA256(fingerprintString);
}
```

**Backend Validation** (`device_token_config.py`):
```python
def verify_device_token(token: str) -> Tuple[bool, Optional[dict]]:
    """Verify HMAC signature of device token"""
    try:
        decoded = base64.b64decode(token)
        payload_json, signature = decoded.rsplit(b'.', 1)
        payload = json.loads(payload_json)
        
        # Compute expected signature
        expected_sig = hmac.new(
            SECRET_KEY.encode(),
            payload_json,
            hashlib.sha256
        ).digest()
        
        # Constant-time comparison
        if hmac.compare_digest(expected_sig, signature):
            return True, payload
        
        return False, None
    except Exception:
        return False, None
```

### 2. Session Tracking

**Frontend** (`session-manager.ts`):
```typescript
class SessionManager {
  private sessionId: string;
  
  initializeSession(): void {
    // Check if session exists
    this.sessionId = localStorage.getItem('session_id');
    
    if (!this.sessionId) {
      // Generate new session (UUID v4)
      this.sessionId = crypto.randomUUID();
      localStorage.setItem('session_id', this.sessionId);
    }
  }
  
  getSessionId(): string {
    return this.sessionId;
  }
}
```

**Backend** (`tracking.py`):
```python
def get_session_id(request: Request) -> Optional[str]:
    """Extract session ID from request headers"""
    return request.headers.get("X-Session-ID")
```

### 3. IP Tracking

**Backend** (`tracking.py`):
```python
def get_client_ip(request: Request) -> str:
    """Extract client IP with proxy support"""
    # Check X-Forwarded-For (proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Check X-Real-IP (nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Direct connection
    return request.client.host if request.client else "unknown"

def hash_ip(ip: str) -> str:
    """Hash IP for privacy (SHA-256, first 16 chars)"""
    return hashlib.sha256(ip.encode()).hexdigest()[:16]
```

### 4. User ID Tracking

**Backend** (`auth_middleware.py`):
```python
async def get_current_user(request: Request) -> Optional[User]:
    """Extract user from JWT token"""
    access_token = request.cookies.get("access_token")
    
    if not access_token:
        return None
    
    payload = verify_token(access_token, token_type="access")
    if not payload:
        return None
    
    user_id = payload.get("sub")
    return db.query(User).filter(User.id == int(user_id)).first()
```

---

## Rate Limit Tiers

### Guest Limits

| Limit Type | Count | Window | Reset |
|------------|-------|--------|-------|
| **Analysis** | 2 | 24 hours | Rolling |
| **API (minute)** | 30 | 60 seconds | Rolling |
| **API (hour)** | 500 | 3600 seconds | Rolling |

**Redis Keys**:
```
rate_limit:guest:device:{fingerprint}:analysis       TTL: 86400s
rate_limit:guest:session:{session_id}:analysis       TTL: 86400s
rate_limit:guest:ip:{ip_hash}:analysis              TTL: 86400s

rate_limit:guest:device:{fingerprint}:api_minute    TTL: 60s
rate_limit:guest:session:{session_id}:api_minute    TTL: 60s
rate_limit:guest:ip:{ip_hash}:api_minute           TTL: 60s
```

### User Limits

| Limit Type | Count | Window | Reset |
|------------|-------|--------|-------|
| **Analysis** | 5 | 24 hours | Rolling |
| **API (minute)** | 60 | 60 seconds | Rolling |
| **API (hour)** | 1000 | 3600 seconds | Rolling |

**Redis Keys**:
```
rate_limit:user:device:{fingerprint}:analysis       TTL: 86400s
rate_limit:user:session:{session_id}:analysis       TTL: 86400s
rate_limit:user:ip:{ip_hash}:analysis              TTL: 86400s
rate_limit:user:user:{user_id}:analysis            TTL: 86400s  (4th dimension!)

rate_limit:user:device:{fingerprint}:api_minute    TTL: 60s
rate_limit:user:session:{session_id}:api_minute    TTL: 60s
rate_limit:user:ip:{ip_hash}:api_minute           TTL: 60s
rate_limit:user:user:{user_id}:api_minute         TTL: 60s
```

### Admin Limits

| Limit Type | Count | Window | Reset |
|------------|-------|--------|-------|
| **Analysis** | Unlimited | - | - |
| **API (minute)** | 120 | 60 seconds | Rolling |
| **API (hour)** | 5000 | 3600 seconds | Rolling |

**Configuration** (`rate_limiting/config.py`):
```python
@dataclass
class RateLimitConfig:
    # Guest limits
    GUEST_ANALYSIS_LIMIT: int = 2
    GUEST_ANALYSIS_WINDOW: int = 86400  # 24 hours
    GUEST_API_MINUTE_LIMIT: int = 30
    GUEST_API_HOUR_LIMIT: int = 500
    
    # User limits
    USER_ANALYSIS_LIMIT: int = 5
    USER_ANALYSIS_WINDOW: int = 86400  # 24 hours
    USER_API_MINUTE_=LIMIT: int = 60
    USER_API_HOUR_LIMIT: int = 1000
    
    # Admin limits
    ADMIN_ANALYSIS_LIMIT: int = 999999  # Effectively unlimited
    ADMIN_ANALYSIS_WINDOW: int = 86400
    ADMIN_API_MINUTE_LIMIT: int = 120
    ADMIN_API_HOUR_LIMIT: int = 5000
```

---

## Device Token Signing

### Token Structure

```json
{
  "payload": {
    "fingerprint": "a1b2c3d4e5f6...",
    "created_at": 1702480000,
    "nonce": "random_string_for_uniqueness"
  },
  "signature": "hmac_sha256_signature_bytes"
}

// Encoded as: base64(JSON.stringify(payload) + '.' + signature)
```

### Generation Process

**Backend** (`device_token_config.py`):
```python
def create_device_token(fingerprint: str) -> str:
    """Create signed device token"""
    payload = {
        "fingerprint": fingerprint,
        "created_at": int(datetime.now().timestamp()),
        "nonce": secrets.token_hex(8)
    }
    
    payload_json = json.dumps(payload).encode()
    
    # Sign with HMAC-SHA256
    signature = hmac.new(
        SECRET_KEY.encode(),
        payload_json,
        hashlib.sha256
    ).digest()
    
    # Combine and encode
    token_bytes = payload_json + b'.' + signature
    return base64.b64encode(token_bytes).decode()
```

### Validation Process

```python
def verify_device_token(token: str) -> Tuple[bool, Optional[dict]]:
    """Verify device token signature"""
    try:
        # Decode
        decoded = base64.b64decode(token)
        payload_json, signature = decoded.rsplit(b'.', 1)
        
        # Compute expected signature
        expected_sig = hmac.new(
            SECRET_KEY.encode(),
            payload_json,
            hashlib.sha256
        ).digest()
        
        # Constant-time comparison (prevents timing attacks)
        if not hmac.compare_digest(expected_sig, signature):
            return False, None
        
        # Parse payload
        payload = json.loads(payload_json)
        
        # Optional: Check age (prevent replay attacks)
        created_at = payload.get("created_at", 0)
        age_seconds = datetime.now().timestamp() - created_at
        if age_seconds > 86400 * 30:  # 30 days max
            return False, None
        
        return True, payload
        
    except Exception as e:
        logger.error(f"Device token verification failed: {e}")
        return False, None
```

### Frontend Integration

**Tracking Headers** (`tracking-headers.ts`):
```typescript
static async getHeaders(): Promise<Record<string, string>> {
  const deviceToken = await DeviceTokenManager.getDeviceToken();
  const sessionId = SessionManager.getSessionId();
  
  return {
    'X-Device-Token': deviceToken,      // Signed device fingerprint
    'X-Session-ID': sessionId,          // Session UUID
    'X-Client-Timestamp': Date.now().toString()
  };
}
```

---

## Storage Infrastructure

### Redis Key Patterns

```
rate_limit:{role}:{dimension}:{identifier}:{limit_type}

Components:
- role:       guest | user | admin
- dimension:  device | session | ip | user
- identifier: fingerprint | session_id | ip_hash | user_id
- limit_type: analysis | api_minute | api_hour
```

**Examples**:
```
rate_limit:guest:device:abc123def456:analysis
rate_limit:user:session:uuid-1234-5678:api_minute
rate_limit:admin:ip:a1b2c3d4:api_hour
rate_limit:user:user:42:analysis
```

### Redis Data Structure

**Key Type**: String (counter)

**Value**: Integer (current count)

**TTL**: Varies by limit type
- `analysis`: 86400 seconds (24 hours)
- `api_minute`: 60 seconds
- `api_hour`: 3600 seconds

**Operations**:
```bash
# Increment counter
INCR rate_limit:guest:device:abc123:analysis

# Set TTL on first increment
EXPIRE rate_limit:guest:device:abc123:analysis 86400

# Get current count
GET rate_limit:guest:device:abc123:analysis

# Get TTL (time remaining)
TTL rate_limit:guest:device:abc123:analysis
```

---

## Enforcement Flow

### Request Processing Pipeline

```
1. Request Arrives
   │
   ▼
2. Extract Tracking Headers
   ├─► X-Device-Token
   ├─► X-Session-ID
   ├─► X-Forwarded-For / X-Real-IP
   └─► Cookie: access_token (for user ID)
   │
   ▼
3. Validate Device Token
   ├─► Verify HMAC signature
   ├─► Extract fingerprint
   └─► Check age
   │
   ▼
4. Determine Role
   ├─► JWT present & valid? → user/admin
   └─► No JWT? → guest
   │
   ▼
5. Build Tracking Keys (all dimensions)
   ├─► rate_limit:{role}:device:{fingerprint}:{type}
   ├─► rate_limit:{role}:session:{session_id}:{type}
   ├─► rate_limit:{role}:ip:{ip_hash}:{type}
   └─► rate_limit:{role}:user:{user_id}:{type} (if authenticated)
   │
   ▼
6. Check All Dimensions
   ├─► For each key:
   │   ├─► GET count from Redis
   │   ├─► Compare with limit
   │   └─► If ANY dimension exceeds → BLOCK
   │
   ▼
7a. All Checks Pass
    ├─► INCR all dimension keys
    ├─► Set TTL if first increment
    └─► Allow request (200 OK)

7b. Any Check Fails
    ├─► Log violation
    ├─► Return 429 Too Many Requests
    └─► Include reset_at timestamp
```

### Code Implementation

**Guest Limiter** (`guest_limiter.py`):
```python
class GuestRateLimiter:
    def check_limit(self, request: Request, limit_type: str) -> Tuple[bool, int]:
        """
        Check if guest request is within limits.
        Returns: (allowed, remaining_count)
        """
        # Build tracking keys (3 dimensions for guest)
        keys = TrackingUtils.build_tracking_keys(
            request=request,
            user_id=None,
            role="guest",
            limit_type=limit_type
        )
        
        # Get limit for this type
        limit = self._get_limit(limit_type)
        
        # Check all dimensions
        max_count = 0
        for key in keys:
            count = int(redis.get(key) or 0)
            max_count = max(max_count, count)
        
        # Return strictest dimension
        allowed = max_count < limit
        remaining = max(0, limit - max_count)
        
        return allowed, remaining
    
    def increment(self, request: Request, limit_type: str) -> None:
        """Increment counters for all dimensions"""
        keys = TrackingUtils.build_tracking_keys(
            request=request,
            user_id=None,
            role="guest",
            limit_type=limit_type
        )
        
        ttl = self._get_ttl(limit_type)
        
        for key in keys:
            # Increment counter
            new_count = redis.incr(key)
            
            # Set TTL on first increment
            if new_count == 1:
                redis.expire(key, ttl)
```

**User Limiter** (`user_limiter.py`):
```python
class UserRateLimiter:
    def check_limit(self, request: Request, user_id: int, limit_type: str) -> Tuple[bool, int]:
        """
        Check if user request is within limits.
        Returns: (allowed, remaining_count)
        """
        # Build tracking keys (4 dimensions for user)
        keys = TrackingUtils.build_tracking_keys(
            request=request,
            user_id=user_id,
            role="user",
            limit_type=limit_type
        )
        
        # ... same logic as guest, but with 4 dimensions
```

---

## API Endpoints

### 1. Check Limit
```bash
GET /tracking/user/check-limit

Headers:
  X-Device-Token: {signed_token}
  X-Session-ID: {uuid}
  Cookie: access_token={jwt}

Response (200 OK):
{
  "limit": 5,
  "remaining": 3,
  "reset_at": 1702570000,  // Unix timestamp
  "role": "user"
}

Response (429 Too Many Requests):
{
  "detail": "Rate limit exceeded. Try again in 5 hours.",
  "limit": 5,
  "remaining": 0,
  "reset_at": 1702570000
}
```

**cURL Example**:
```bash
curl -X GET http://localhost:8000/tracking/user/check-limit \
  -H "X-Device-Token: eyJmaW5nZXJwcmludCI..." \
  -H "X-Session-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -b "access_token=eyJhbGciOiJIUzI1NiIs..."
```

### 2. Device Token Generation
```bash
POST /tracking/device-token/generate

Body:
{
  "fingerprint": "a1b2c3d4e5f6g7h8i9j0"
}

Response (200 OK):
{
  "device_token": "eyJmaW5nZXJwcmludCI6ImEx...",
  "expires_at": 1705152000
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/tracking/device-token/generate \
  -H "Content-Type: application/json" \
  -d '{"fingerprint":"a1b2c3d4e5f6g7h8i9j0"}'
```

### 3. Admin: List Rate Limited Users
```bash
GET /admin/traffic/rate-limited-users?minutes=5

Headers:
  Cookie: access_token={admin_jwt}

Response (200 OK):
{
  "count": 3,
  "users": [
    {
      "device_fingerprint": "abc123",
      "session_id": "uuid-1234",
      "ip_address": "192.168.1.1",
      "last_attempt": "2025-12-11T12:00:00Z",
      "blocked_reason": "Analysis limit exceeded"
    },
    ...
  ]
}
```

**cURL Example**:
```bash
curl -X GET 'http://localhost:8000/admin/traffic/rate-limited-users?minutes=5' \
  -H "Cookie: access_token=admin_jwt_token"
```

### 4. Admin: Remove Rate Limit
```bash
POST /admin/traffic/remove-rate-limit

Headers:
  Cookie: access_token={admin_jwt}

Body:
{
  "dimension": "device",  // device | session | ip | user
  "identifier": "abc123def456"
}

Response (200 OK):
{
  "removed": 3,  // Number of keys deleted
  "keys": [
    "rate_limit:guest:device:abc123:analysis",
    "rate_limit:guest:device:abc123:api_minute",
    "rate_limit:guest:device:abc123:api_hour"
  ]
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/admin/traffic/remove-rate-limit \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=admin_jwt" \
  -d '{
    "dimension": "device",
    "identifier": "abc123def456"
  }'
```

---

## Database Schema

### Rate Limit Violations (Optional Logging)
```sql
CREATE TABLE rate_limit_violations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    device_fingerprint VARCHAR(255),
    session_id VARCHAR(255),
    ip_address VARCHAR(45),
    limit_type VARCHAR(50),
    exceeded_count INT,
    limit_value INT,
    violation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user_id (user_id),
    INDEX idx_device (device_fingerprint),
    INDEX idx_time (violation_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## Redis Keys

### Analysis Limits (24-hour rolling)
```bash
# Guest
rate_limit:guest:device:{fingerprint}:analysis     # TTL: 86400s
rate_limit:guest:session:{session_id}:analysis     # TTL: 86400s
rate_limit:guest:ip:{ip_hash}:analysis            # TTL: 86400s

# User (+ user dimension)
rate_limit:user:device:{fingerprint}:analysis      # TTL: 86400s
rate_limit:user:session:{session_id}:analysis      # TTL: 86400s
rate_limit:user:ip:{ip_hash}:analysis             # TTL: 86400s
rate_limit:user:user:{user_id}:analysis           # TTL: 86400s

# Admin
rate_limit:admin:device:{fingerprint}:analysis     # TTL: 86400s
rate_limit:admin:session:{session_id}:analysis     # TTL: 86400s
rate_limit:admin:ip:{ip_hash}:analysis            # TTL: 86400s
rate_limit:admin:user:{user_id}:analysis          # TTL: 86400s
```

### API Minute Limits (60-second rolling)
```bash
rate_limit:{role}:{dimension}:{identifier}:api_minute
# TTL: 60s
```

### API Hour Limits (3600-second rolling)
```bash
rate_limit:{role}:{dimension}:{identifier}:api_hour
# TTL: 3600s
```

---

## Configuration

### Environment Variables
```bash
# .env
RATE_LIMIT_ENABLED=true  # Master switch
DEVICE_TOKEN_SECRET=your_secret_key_here
```

### Rate Limit Config
**File**: `backend/app/rate_limiting/config.py`

```python
@dataclass
class RateLimitConfig:
    # Guest
    GUEST_ANALYSIS_LIMIT: int = 2
    GUEST_ANALYSIS_WINDOW: int = 86400
    GUEST_API_MINUTE_LIMIT: int = 30
    GUEST_API_HOUR_LIMIT: int = 500
    
    # User
    USER_ANALYSIS_LIMIT: int = 5
    USER_ANALYSIS_WINDOW: int = 86400
    USER_API_MINUTE_LIMIT: int = 60
    USER_API_HOUR_LIMIT: int = 1000
    
    # Admin
    ADMIN_ANALYSIS_LIMIT: int = 999999
    ADMIN_ANALYSIS_WINDOW: int = 86400
    ADMIN_API_MINUTE_LIMIT: int = 120
    ADMIN_API_HOUR_LIMIT: int = 5000
```

---

## Testing & Verification

### Check User's Current Limits
```bash
# Via API
curl -X GET http://localhost:8000/tracking/user/check-limit \
  -H "X-Device-Token: $(cat device_token.txt)" \
  -H "X-Session-ID: test-session-123" \
  -b cookies.txt

# Direct Redis query
docker-compose exec redis redis-cli --scan --pattern "rate_limit:user:*"
docker-compose exec redis redis-cli GET "rate_limit:user:device:abc123:analysis"
```

### Manually Set Limit
```bash
# Set analysis count to 4 (1 remaining for limit of 5)
docker-compose exec redis redis-cli SET "rate_limit:user:device:abc123:analysis" 4
docker-compose exec redis redis-cli EXPIRE "rate_limit:user:device:abc123:analysis" 86400
```

### View All Rate Limit Keys
```bash
docker-compose exec redis redis-cli --scan --pattern "rate_limit:*"
```

### Get TTL for Key
```bash
docker-compose exec redis redis-cli TTL "rate_limit:user:device:abc123:analysis"
# Returns seconds remaining until reset
```

### Clear All Rate Limits (Admin)
```bash
docker-compose exec redis redis-cli --scan --pattern "rate_limit:*" | \
  xargs docker-compose exec -T redis redis-cli DEL
```

### Test Device Token Signature
```bash
# Python script
docker-compose exec backend python -c "
from app.rate_limiting.device_token_config import create_device_token, verify_device_token

# Generate
token = create_device_token('test_fingerprint_123')
print('Token:', token)

# Verify
valid, payload = verify_device_token(token)
print('Valid:', valid)
print('Payload:', payload)

# Test with wrong token
valid, _ = verify_device_token('invalid_token_here')
print('Invalid token check:', valid)
"
```

### Monitor Rate Limit Hits
```bash
# Watch logs for rate limit checks
docker-compose logs -f backend | grep "LIMITER"

# Watch for violations
docker-compose logs -f backend | grep "Rate limit exceeded"
```

---

## Troubleshooting

### Issue: Rate limit not enforcing

**Diagnosis**:
```bash
# Check if rate limiting is enabled
docker-compose exec backend python -c "
from app.core.config import settings
print('Rate limit enabled:', settings.RATE_LIMIT_ENABLED)
"

# Check if tracking headers are present
docker-compose logs backend | grep "X-Device-Token"
```

**Solution**:
1. Enable in `.env`: `RATE_LIMIT_ENABLED=true`
2. Restart backend
3. Ensure frontend sends tracking headers

### Issue: Device token validation failing

**Diagnosis**:
```bash
# Check logs for validation errors
docker-compose logs backend | grep "Device token"
```

**Solution**:
1. Verify `DEVICE_TOKEN_SECRET` is set in `.env`
2. Check token format (base64 encoded)
3. Ensure frontend and backend use same secret

### Issue: Guest limit too strict

**Diagnosis**:
```bash
# Check current limits
docker-compose exec backend python -c "
from app.rate_limiting.config import rate_limit_config
print('Guest analysis limit:', rate_limit_config.GUEST_ANALYSIS_LIMIT)
"
```

**Solution**:
1. Adjust limits in `rate_limiting/config.py`
2. Restart backend
3. Or use admin endpoint to remove specific limits

### Issue: Reset time not showing correctly

**Diagnosis**:
```bash
# Check TTL calculation
curl -X GET http://localhost:8000/tracking/user/check-limit \
  -H "X-Device-Token: ..." | jq '.reset_at'
```

**Solution**:
- Ensure backend returns `reset_at` in response
- Frontend should display: `new Date(reset_at * 1000)`

---

## Security Considerations

1. **HMAC Signing**: Prevents device token forgery
2. **Constant-Time Comparison**: Prevents timing attacks
3. **Multi-Dimensional Tracking**: Harder to bypass (need to spoof all 4)
4. **Rolling Windows**: More fair than fixed-window limits
5. **IP Hashing**: Privacy-preserving (SHA-256)
6. **HttpOnly Cookies**: Device tokens in httpOnly cookies
7. **Signed Tokens**: Can't be modified client-side
8. **Rate Limit Middleware**: Runs before business logic
9. **Redis Password**: Protect Redis in production
10. **Admin-Only Endpoints**: Reset limits requires admin role

---

## Performance Metrics

### Redis Operations per Request

| Role | Dimensions | Redis Ops | Latency |
|------|-----------|-----------|---------|
| Guest | 3 | 6-9 | 2-5ms |
| User | 4 | 8-12 | 3-6ms |
| Admin | 4 | 8-12 | 3-6ms |

**Breakdown**:
- GET (check): 1 op per dimension
- INCR: 1 op per dimension (if allowed)
- EXPIRE: 1 op per dimension (on first increment)

### Storage Overhead

| Item | Size | Count (typical) |
|------|------|-----------------|
| Rate limit key | ~80 bytes | 3-4 per user |
| Counter value | 8 bytes | Same as keys |
| Total per user | ~350 bytes | - |

**Example**: 1000 active users = ~350 KB in Redis

---

## Monitoring Checklist

- [ ] Rate limit keys have correct TTL
- [ ] Device tokens validate successfully
- [ ] Multi-dimensional tracking working
- [ ] Violations logged appropriately
- [ ] Reset times calculated correctly
- [ ] Admin endpoints accessible
- [ ] Frontend sends all tracking headers
- [ ] Redis memory usage within limits

---

## Future Enhancements

- [ ] Whitelist/blacklist management
- [ ] Dynamic limits based on user behavior
- [ ] Distributed rate limiting (multi-instance)
- [ ] Rate limit analytics dashboard
- [ ] Automatic DDoS detection
- [ ] Geographic-based limits
- [ ] Time-of-day based limits
- [ ] Custom limit tiers per user
