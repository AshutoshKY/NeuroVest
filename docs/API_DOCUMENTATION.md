# API Documentation - NeuroVest Stock Market Platform

**Document Version**: 1.0  
**Last Updated**: December 11, 2025  
**Total Endpoints**: 88 across 17 modules

## Table of Contents
1. [Executive Overview](#executive-overview)
2. [API Inventory](#api-inventory)
3. [Security Architecture](#security-architecture)
4. [Request/Response Headers](#requestresponse-headers)
5. [Authentication & Authorization](#authentication--authorization)
6. [Rate Limiting](#rate-limiting)
7. [Device & IP Tracking](#device--ip-tracking)
8. [Session Management](#session-management)
9. [AES Encryption](#aes-encryption)
10. [API Categories (Detailed)](#api-categories-detailed)
11. [Error Handling](#error-handling)
12. [Architecture Diagrams](#architecture-diagrams)

---

## Executive Overview

### Platform Statistics
- **Total API Endpoints**: 88
- **API Modules**: 17  
- **Security Layers**: 5 (JWT, Rate Limiting, Device/IP Tracking, Sessions, AES Encryption)
- **Supported Roles**: Guest, User, Admin
- **Authentication Method**: JWT with dual-token system (Access + Refresh)

### API Distribution by Category

| Category | Endpoints | Auth Required | Key Features |
|----------|-----------|---------------|--------------|
| **Authentication** | 8 | Mixed | JWT, AES encryption, session tracking |
| **User Management** | 9 | Yes | Profile, settings, password, account deletion |
| **Stock Analysis** | 7 | Yes | Real-time data, AI analysis, streaming (SSE) |
| **Watchlist/Favorites** | 8 | Yes | CRUD operations, bulk updates, reordering |
| **Analysis History** | 3 | Yes | CRUD for analysis records |
| **Saved Analyses** | 3 | Yes | Limited to 10 per user |
| **Security** | 6 | Yes | Session management, login history |
| **Stock Data** | 5 | Mixed | Search, info, trending stocks |
| **Admin** | 25+ | Admin only | User mgmt, traffic, health monitoring |
| **Device/Tracking** | 4 | Mixed | Device registration, rate limiting |
| **Sentiment/News** | 4 | No | Sentiment analysis, news aggregation |
| **Health/Monitoring** | 7 | Mixed | System health, data sources |

### Technology Stack
- **Backend**: FastAPI (Python 3.11+)
- **Database**: MySQL 8.0+ (primary), Redis 7.0+ (cache, rate limiting)
- **Authentication**: JWT (HS256) with rotating keys (24-hour rotation)
- **Encryption**: AES-256-CBC (sensitive data), RSA-2048 (key exchange)
- **Real-time**: Server-Sent Events (SSE) for analysis streaming

---

## Security Architecture

### 5-Layer Security Model

```
┌──────────────────────────────────────────────────────────┐
│                   Security Layers Stack                   │
└──────────────────────────────────────────────────────────┘

Layer 5: AES Encryption          ┌──────────────────────┐
         (Sensitive Data)        │ email_encrypted: true│
                                 │ password_encrypted   │
         ─────────────────────── └──────────────────────┘
                 │
                 v
Layer 4: Session Management      ┌──────────────────────┐
         (Max 2 per user)        │ Active Sessions: 2/2│
                                 │ Oldest auto-revoked  │
         ─────────────────────── └──────────────────────┘
                 │
                 v
Layer 3: Device/IP Tracking      ┌──────────────────────┐
         (Fingerprinting)        │ Device FP + GeoIP    │
                                 │ Multi-dimensional ID │
         ─────────────────────── └──────────────────────┘
                 │
                 v
Layer 2: Rate Limiting           ┌──────────────────────┐
         (4D: User/IP/           │ User: 5/day          │
          Session/Device)        │ Guest: 2/day         │
         ─────────────────────── └──────────────────────┘
                 │
                 v
Layer 1: JWT Authentication      ┌──────────────────────┐
         (Dual-token, Rotating)  │ Access: 24h          │
                                 │ Refresh: 7d          │
                                 │ 3-key verification   │
         ─────────────────────── └──────────────────────┘
```

### Complete Request Flow

```
Client Request
     │
     v
┌────────────────────────┐
│ 1. Extract Headers     │
│ • Cookie: tokens      │
│ • X-Device-Token      │
│ • X-Session-ID        │
│ • X-IP-Address        │
└──────┬─────────────────┘
       │
       v
┌────────────────────────┐     ┌──────────────┐
│ 2. JWT Verification    │────►│ 401: Invalid │
│ (3 key attempts)       │     │     Token    │
└──────┬─────────────────┘     └──────────────┘
       │ Valid
       v
┌────────────────────────┐     ┌──────────────┐
│ 3. Rate Limit Check    │────►│ 429: Too Many│
│ (4 dimensions)         │     │   Requests   │
└──────┬─────────────────┘     └──────────────┘
       │ Allowed
       v
┌────────────────────────┐     ┌──────────────┐
│ 4. Device Validation   │────►│ 400: Missing │
│ (Fingerprint + IP)     │     │   Headers    │
└──────┬─────────────────┘     └──────────────┘
       │ Valid
       v
┌────────────────────────┐     ┌──────────────┐
│ 5. Session Check       │────►│ 401: Session │
│ (Active, not revoked)  │     │   Revoked    │
└──────┬─────────────────┘     └──────────────┘
       │ Active
       v
┌────────────────────────┐     ┌──────────────┐
│ 6. AES Decryption      │────►│ 400: Decrypt │
│ (If encrypted data)    │     │    Failed    │
└──────┬─────────────────┘     └──────────────┘
       │ Success
       v
┌────────────────────────┐
│ 7. Execute Endpoint    │
│    and Return 200      │
└────────────────────────┘
```

---

## Request/Response Headers

### Standard Request Headers

#### Required for All Authenticated Endpoints
```http
Cookie: access_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Cookie: refresh_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # Only for /auth/refresh
Content-Type: application/json
```

#### Tracking Headers (Required for Rate-Limited Endpoints)
```http
X-Device-Token: {"device_fp":"abc123...","session_id":"uuid",...}
X-Session-ID: 550e8400-e29b-41d4-a716-446655440000
X-IP-Address: 203.0.113.42  # Optional, backend auto-detects if missing
```

**X-Device-Token JSON Structure**:
```json
{
  "device_fp": "unique_browser_fingerprint",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "browser": "Chrome 120.0.0.0",
  "os": "Mac OS X 10.15.7",
  "device_type": "desktop",
  "screen": "1920x1080",
  "timezone": "America/New_York"
}
```

### Standard Response Headers

#### Success Responses
```http
HTTP/1.1 200 OK
Content-Type: application/json
X-Request-ID: 6d757e86-7971-4849-9b6c-b0d59c682a09
X-Trace-ID: 81b18c4e
Access-Control-Allow-Credentials: true
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Expose-Headers: X-Request-ID
Vary: Origin
Date: Thu, 11 Dec 2025 17:09:15 GMT
Server: uvicorn
```

#### Rate Limiting Headers
```http
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 3
X-RateLimit-Reset: 1702648800
X-RateLimit-Window: 86400
```

#### Authentication Response Headers
```http
Set-Cookie: access_token=eyJhbG...; HttpOnly; SameSite=Lax; Max-Age=86400; Path=/
Set-Cookie: refresh_token=eyJhbG...; HttpOnly; SameSite=Lax; Max-Age=604800; Path=/
```

---

## Authentication & Authorization

### JWT Token System

See [JWT_AUTHENTICATION.md](./JWT_AUTHENTICATION.md) for complete details.

**Quick Reference**:

| Token Type | Lifetime | Purpose | Storage | Renewable |
|------------|----------|---------|---------|-----------|
| Access Token | 24 hours | API authorization | HttpOnly cookie | Yes (via refresh) |
| Refresh Token | 7 days | Token renewal | HttpOnly cookie + DB | Yes (auto-renewed) |

**Access Token Payload**:
```json
{
  "sub": "123",          // User ID
  "role": "user",        // user/admin
  "exp": 1702648800,    // Expires at (Unix timestamp)
  "type": "access",     // Token type
  "iat": 1702562400     // Issued at (Unix timestamp)
}
```

### Authorization Levels

| Role | Analyses/24h | Access Scope | Special Features |
|------|--------------|--------------|------------------|
| **Guest** | 2 | Public endpoints, trending stocks | Limited search |
| **User** | 5 | All user endpoints | Full analysis, watchlist, history |
| **Admin** | Unlimited | All endpoints | User mgmt, traffic stats, cache control |

---

## Rate Limiting

### Multi-Dimensional Approach

**4 Tracking Dimensions**:
1. **User ID** - Primary for authenticated users
2. **IP Address** - Primary for guests, fallback for users
3. **Session ID** - Secondary tracking across refreshes
4. **Device Fingerprint** - Prevents multi-browser abuse

### Redis Key Strategy

**Format**: `rate_limit:{role}:{dimension}:{identifier}:{type}`

**Examples**:
```bash
# User accessing analysis endpoint
rate_limit:user:user:123:analysis                    # Primary (user ID)
rate_limit:user:session:550e8400-...:analysis       # Secondary (session)
rate_limit:user:ip:a1b2c3d4:analysis                # Fallback (IP hash)
rate_limit:user:device:abc123fp:analysis            # Fallback (device FP)

# Guest accessing analysis endpoint
rate_limit:guest:ip:a1b2c3d4:analysis              # Primary (IP hash)
rate_limit:guest:device:abc123fp:analysis          # Secondary (device FP)
rate_limit:guest:session:550e8400-...:analysis     # Fallback (session)
```

**Properties**:
- **TTL**: 86400 seconds (24 hours from first request)
- **Value**: Integer counter (incremented on each request)
- **Window**: Rolling 24-hour window (resets 24h after first use)

### Rate Limit Check

**Endpoint**: `GET /tracking/user/check-limit`

**Request**:
```bash
curl -X GET http://localhost:8000/tracking/user/check-limit \
  -H "Cookie: access_token=eyJhbG..." \
  -H "X-Device-Token: {\"device_fp\":\"abc123\",\"session_id\":\"550e8400-...\"}" \
  -H "X-Session-ID: 550e8400-e29b-41d4-a716-446655440000"
```

**Response** (200 OK):
```json
{
  "remaining": 3,
  "limit": 5,
  "role": "user",
  "reset_at": 1702648800
}
```

---

## Device & IP Tracking

### Device Fingerprinting

**Collected Data**:
- Browser fingerprint (canvas, WebGL, fonts)
- User agent (browser name/version)
- Operating system
- Device type (desktop/mobile/tablet)
- Screen resolution
- Timezone

**Frontend** (`/lib/tracking-headers.ts`):
```typescript
const deviceToken = {
  device_fp: await generateFingerprint(),  // FingerprintJS
  browser: "Chrome 120.0.0.0",
  os: "Mac OS X 10.15.7",
  device_type: "desktop",
  screen: "1920x1080",
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  session_id: localStorage.getItem('session_id') || generateUUID()
};
```

### IP Geolocation

**Backend** (`/services/login_tracker.py`):
```python
import geoip2.database

reader = geoip2.database.Reader('GeoLite2-City.mmdb')
response = reader.city(ip_address)

location = {
    "country": response.country.name,
    "city": response.city.name,
    "latitude": response.location.latitude,
    "longitude": response.location.longitude
}
```

**Used For**:
- Login history (location display)
- Active sessions (IP geolocation)
- Suspicious login detection

---

## Session Management

### Session Lifecycle

```
┌────────────────────────────────────────────────────────────┐
│                 Session Lifecycle Flow                      │
└────────────────────────────────────────────────────────────┘

User Login
    │
    v
┌─────────────────────────┐
│ 1. Create Refresh Token │
│ - Generate JWT          │
│ - Hash and store in DB  │
│ - Attach device info    │
└──────────┬──────────────┘
           │
           v
┌─────────────────────────┐
│ 2. Count Active Sessions│
│ Query: user_id, revoked=false, not expired
│ Current Count: N        │
└──────────┬──────────────┘
           │
           ├─────────── N < 2 ────────┐
           │                          │
           │ N >= 2                   v
           v                     ┌────────────┐
┌──────────────────────┐         │  Allow     │
│ 3. Revoke Oldest     │         │  Login     │
│ - Sort by created_at │         └────────────┘
│ - Keep 2 newest      │
│ - Revoke others      │
│   (SET revoked=true) │
└──────────┬───────────┘
           │
           v
┌──────────────────────┐
│ 4. Session Active    │
│ - User has 2 sessions│
│ - Oldest auto-revoked│
└──────────────────────┘

On Logout
    │
    v
┌──────────────────────┐
│ Revoke This Session  │
│ SET revoked=true     │
│ WHERE token=current  │
└──────────────────────┘
```

### Session Database Schema

```sql
CREATE TABLE refresh_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token TEXT NOT NULL,                   -- Hashed refresh token
    expires_at TIMESTAMP NOT NULL,
    revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP NULL,
    
    -- Session tracking
    ip_address VARCHAR(45),
    device_type VARCHAR(50),               -- desktop/mobile/tablet
    os VARCHAR(100),                        -- Mac OS X 10.15.7
    browser VARCHAR(100),                   -- Chrome 120.0
    device_name VARCHAR(255),              -- "Mac - Chrome"
    session_id VARCHAR(255),               -- UUID from frontend
    
    -- Location (from GeoIP)
    country VARCHAR(100),
    city VARCHAR(100),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_revoked (user_id, revoked),
    INDEX idx_expires_at (expires_at)
);
```

### Session Management APIs

#### Get Active Sessions
```bash
GET /api/security/active-sessions
```

**Response**:
```json
[
  {
    "id": 42,
    "device_type": "desktop",
    "os": "Mac OS X 10.15.7",
    "browser": "Chrome 120.0",
    "device_name": "Mac - Chrome",
    "ip_address": "192.168.1.100",
    "country": "United States",
    "city": "New York",
    "last_used_at": "2025-12-11T16:55:10Z",
    "created_at": "2025-12-11T10:00:00Z",
    "is_current": true
  },
  {
    "id": 41,
    "device_type": "mobile",
    "os": "iOS 17.1",
    "browser": "Safari 17.0",
    "device_name": "iPhone - Safari",
    "ip_address": "203.0.113.42",
    "country": "United States",
    "city": "San Francisco",
    "last_used_at": "2025-12-11T14:30:00Z",
    "created_at": "2025-12-10T08:00:00Z",
    "is_current": false
  }
]
```

#### Revoke Session
```bash
POST /api/security/revoke-session/41
```

**Response**: 204 No Content

#### Revoke All Other Sessions
```bash
POST /api/security/revoke-all-sessions
```

**Response**:
```json
{
  "message": "All other sessions have been logged out. Only this session remains active."
}
```

---

## AES Encryption

### Encryption Architecture

```
┌──────────────────────────────────────────────────────────┐
│              AES-256-CBC Encryption Flow                  │
└──────────────────────────────────────────────────────────┘

Frontend                          Backend
┌─────────────┐                  ┌──────────────┐
│   User      │                  │   FastAPI    │
│ Enters      │                  │   Server     │
│ Password    │                  └──────┬───────┘
└──────┬──────┘                         │
       │                                │
       v                                │
┌──────────────────┐                    │
│ 1. Get Public    │                    │
│    Key from      │───────────────────►│
│    Backend       │   GET /tracking/   │
│                  │   encryption/      │
└──────┬───────────┘   public-key       │
       │         ◄──────────────────────┤
       │         {                      │
       │           "public_key":        │
       │           "-----BEGIN..."      │
       │         }                      │
       v                                │
┌──────────────────┐                    │
│ 2. Encrypt with  │                    │
│    AES (CryptoJS)│                    │
│                  │                    │
│ Input:           │                    │
│  - Plaintext     │                    │
│  - Public key    │                    │
│                  │                    │
│ Output:          │                    │
│  "U2FsdGVkX1..."│                    │
│  (base64)        │                    │
└──────┬───────────┘                    │
       │                                │
       v                                │
┌──────────────────┐                    │
│ 3. Send Request  │                    │
│ {                │                    │
│   password:      │                    │
│    "U2FsdGVk...│                    │
│   password_      │                    │
│    encrypted:    │                    │
│    true          │──────────────────►│
│ }                │   POST /auth/      │
└──────────────────┘   login            │
                                        v
                               ┌────────────────┐
                               │ 4. Decrypt     │
                               │   (PyCrypto)   │
                               │                │
                               │ Input:         │
                               │  - Encrypted   │
                               │  - Public key  │
                               │                │
                               │ Steps:         │
                               │  a) Decode     │
                               │     base64     │
                               │  b) Extract    │
                               │     salt       │
                               │  c) Derive     │
                               │     key+IV     │
                               │  d) Decrypt    │
                               │                │
                               │ Output:        │
                               │  "SecurePass123"│
                               │  (plaintext)   │
                               └────────┬───────┘
                                        │
                                        v
                               ┌────────────────┐
                               │ 5. Hash & Store│
                               │   (bcrypt)     │
                               │                │
                               │ Password never │
                               │ stored plain   │
                               └────────────────┘
```

### Implementation Details

**Algorithm**: AES-256-CBC
**Key Derivation**: OpenSSL EVP_BytesToKey (MD5-based, CryptoJS compatible)
**Format**: `Base64(Salted__ + salt[8 bytes] + ciphertext)`

**Frontend** (CryptoJS):
```typescript
import CryptoJS from 'crypto-js';

// Fetch public key
const { public_key } = await fetch('/tracking/encryption/public-key').then(r => r.json());

// Encrypt field
const encrypted = CryptoJS.AES.encrypt(plaintext, public_key).toString();
// Output: "U2FsdGVkX18abc123...def456"
```

**Backend** (`/utils/aes_decryption.py`):
```python
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64

def decrypt_field(encrypted_value: str, secret_key: str) -> str:
    # 1. Decode base64
    encrypted_bytes = base64.b64decode(encrypted_value)
    
    # 2. Verify "Salted__" prefix
    assert encrypted_bytes[:8] == b'Salted__'
    
    # 3. Extract salt and ciphertext
    salt = encrypted_bytes[8:16]
    ciphertext = encrypted_bytes[16:]
    
    # 4. Derive 256-bit key + 128-bit IV (EVP_BytesToKey)
    key_iv = derive_key_and_iv(secret_key.encode(), salt)
    key = key_iv[:32]
    iv = key_iv[32:48]
    
    # 5. Decrypt
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)
    
    return decrypted.decode('utf-8')
```

### Encrypted Endpoints

| Endpoint | Encrypted Fields | Mandatory |
|----------|------------------|-----------|
| `POST /auth/register` | `email`, `password`, `full_name` | Yes |
| `POST /auth/login` | `email`, `password` | Yes |
| `PATCH /auth/change-password` | `current_password`, `new_password` | Yes |
| `DELETE /auth/delete-account` | `password` | Yes |

**Payload Example**:
```json
{
  "email": "U2FsdGVkX1+abc123...",
  "email_encrypted": true,
  "password": "U2FsdGVkX1+def456...",
  "password_encrypted": true
}
```

---


---

## 13. Admin Management
**Base URL**: `/admin`

### 13.1 User Management
| Endpoint | Method | Role | Description |
|----------|--------|------|-------------|
| `/users` | GET | Admin | List all users (paginated) |
| `/users/disable` | POST | Super Admin | Disable user account |
| `/users/enable` | POST | Super Admin | Enable user account |

**Disable User Payload**:
```json
{
  "user_id": 123,
  "reason": "Suspicious activity detected"
}
```

### 13.2 IP Blacklist
| Endpoint | Method | Role | Description |
|----------|--------|------|-------------|
| `/ip-blacklist` | GET | Admin | List blacklisted IPs |
| `/ip-blacklist/add` | POST | Super Admin | Add IP to blacklist |
| `/ip-blacklist/{ip}` | DELETE | Super Admin | Remove IP from blacklist |

### 13.3 System Toggles
| Endpoint | Method | Role | Description |
|----------|--------|------|-------------|
| `/system-toggles` | GET | Admin | Get all system toggle states |
| `/system-toggles` | POST | Super Admin | Set system toggle state |

**Valid Toggles**: `login_enabled`, `signup_enabled`, `guest_enabled`, `maintenance`

### 13.4 Audit Logs
| Endpoint | Method | Role | Description |
|----------|--------|------|-------------|
| `/audit-logs` | GET | Admin | View system audit logs |

---

## 14. Admin Traffic Analytics
**Base URL**: `/admin/traffic`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/realtime` | GET | Active users (5m), requests (1h) |
| `/hourly` | GET | Hourly breakdown (default 24h) |
| `/daily` | GET | Daily aggregated traffic (30d) |
| `/geo-distribution` | GET | Request distribution by country |
| `/top-ips` | GET | Most active IP addresses |
| `/popular-stocks` | GET | Most analyzed tickers |

---

## 15. Admin Kill Switches
**Base URL**: `/admin/killswitch`

**Warning**: Activation requires typing a confirmation code specific to the switch.

| Endpoint | Method | Role | Description |
|----------|--------|------|-------------|
| `/status` | GET | Admin | View all kill switch statuses |
| `/activate` | POST | Super Admin | Activate a kill switch |
| `/deactivate` | POST | Super Admin | Deactivate a kill switch |

**Kill Switch Types**:
- `emergency_shutdown`: Stops all non-admin access
- `pause_ai_service`: Disables all AI features
- `pause_trading_api`: Disables external data calls
- `block_new_registrations`: Stops signups

---

## 16. Admin AI Metrics
**Base URL**: `/admin/ai`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/summary` | GET | Today's total tokens, requests, cost |
| `/hourly` | GET | Hourly usage breakdown |
| `/requests` | GET | Recent AI request log |
| `/guardrails` | GET | Safety guardrail rejection stats |
| `/cost-breakdown` | GET | Daily cost trends |
| `/overview` | GET | Comprehensive AI metrics dashboard |

---

## 17. Admin Dashboard
**Base URL**: `/admin/dashboard`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/overview` | GET | Full dashboard state (Infra + Traffic + AI + Risk) |
| `/quick-stats` | GET | Minimal KPI stats for header cards |
| `/alerts` | GET | Active system alerts and critical warnings |

---

## 18. Smart Orchestrator Admin
**Base URL**: `/admin/smartorchestrator`

**Purpose**: Manage the multi-tier API aggregation system, circuit breakers, and caches.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health status of all connected stock APIs |
| `/health/{api}/{market}` | GET | Detailed stats for specific provider |
| `/circuit-breaker/reset` | POST | Reset circuit breaker for an API |
| `/cache/stats` | GET | View hit/miss rates for Memory/Redis/Stale tiers |
| `/cache/clear` | POST | ⚠️ Clear all cache tiers (Force fresh data) |
| `/stats` | GET | Comprehensive orchestrator performance metrics |
| `/config` | GET | View current timeout and specific strategy settings |

**Circuit Breaker Reset Payload**:
```json
{
  "api_name": "finnhub",
  "market": "US"
}
```

---

*Continued in Part 2: API Categories (Detailed), Error Handling, and Architecture Diagrams*

