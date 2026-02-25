# NeuroVest Admin Command Center Guide

**Status**: Active  
**Version**: 1.1  
**Last Updated**: January 2026

**For Developers**: See **[Technical Deep Dive & Architecture](./ADMIN_COMMAND_CENTER_TECHNICAL.md)** for code-level details.

---

## 🛡️ Administrative Overview

The **NeuroVest Admin Command Center** is a unified interface for monitoring system health, managing users, controlling costs, and responding to security threats. It is designed with a **"Trust No One"** architecture where sensitive actions require higher privileges and explicit confirmations.

### core principles
1. **RBAC Enforcement**: Strict separation between `ADMIN` (Viewer) and `SUPER_ADMIN` (Mutator).
2. **Audit Trails**: Every administrative action is logged with actor, IP, timestamp, and changes.
3. **Safety First**: Kill switches and dangerous actions require typed confirmation codes.
4. **Real-Time Visibility**: Infrastructure and AI metrics are streamed in near real-time.

---

## 🔑 Access & Authentication

### Roles & Privileges

| Feature | Admin (Viewer) | Super Admin (Mutator) |
|---------|----------------|-----------------------|
| **Dashboard** | ✅ View Metrics | ✅ View Metrics |
| **Users** | ✅ List Users | ✅ Disable/Enable/Delete |
| **System** | ✅ View Toggles | ✅ Toggle Login/Signup |
| **Kill Switch** | ✅ View Status | ✅ Activate/Deactivate |
| **Audit Logs** | ✅ View Logs | ✅ View Logs |
| **IP Blacklist** | ✅ View IPs | ✅ Add/Remove IPs |

### Accessing the Dashboard
- **URL**: `/admin/dashboard`
- **Requirement**: User account with `role='admin'` or `role='super_admin'`.
- **Session**: Admin sessions have a stricter 1-hour expiry (vs 24h for users).

---

## 📊 Dashboard Modules

### 1. Overview & KPIs
The landing page provides a high-level pulse of the system:
- **System Health**: Composite score based on Redis, MySQL, and ChromaDB connectivity.
- **Real-Time Traffic**: Active users (5 min window) and Requests Per Second (RPS).
- **AI Usage**: Total tokens consumed and estimated cost for the day.
- **Active Alerts**: Critical warnings (e.g., "Kill Switch Active", "Database Down").

### 2. Infrastructure Health
Detailed metrics for the underlying stack:
- **Redis**: Memory usage, connection count, hit rate.
- **MySQL**: Connection pool status, row counts.
- **ChromaDB**: Collection count, embedding latency.

### 3. AI & RAG Analytics
Monitor the brain of NeuroVest:
- **Token consumption**: Track input vs output tokens.
- **Cost Analysis**: Hourly and daily cost breakdown.
- **Guardrails**: View rejected queries (safety violations).

### 4. Traffic & Security
- **Geo-Map**: Heatmap of user requests.
- **Top IPs**: Identify potential abusers or heavy users.
- **Rate Limits**: View users currently being throttled.

---

## 🚨 Security Controls

### Kill Switches
**Location**: `/admin/controls`

These are extreme measures for emergency situations. Activation requires a **typed confirmation code**.

| Switch Name | Code | Effect |
|-------------|------|--------|
| **Emergency Shutdown** | `SHUTDOWN-NOW` | ⛔️ Stops ALL non-admin access immediately. |
| **Pause AI Service** | `PAUSE-AI` | 🧠 Returns static data only; disables GPT-4 calls. |
| **Pause Trading API** | `STOP-MARKET` | 📉 Stops fetching new stock data (serves cache). |
| **Block New Registrations** | `LOCK-DOOR` | 🔒 Prevents new user signups. |

### IP Blacklist
**Location**: `/admin/security`

- **Manual Block**: Add IP + Reason.
- **Auto-Block**: System auto-blocks IPs after multiple failed login attempts or DDOS behavior.
- **Unblock**: Remove IPs to restore access.


---

## 5. Smart Orchestrator Management
**Location**: `/admin/controls`

The **Smart Orchestrator** manages stock data acquisition from multiple providers (Yahoo, Alpha Vantage, Finnhub).

### Key Controls
- **Circuit Breaker Reset**: If an API provider (e.g., Finnhub) fails repeatedly, it gets "Circuit Broken" (stopped). Use this to manually reset it if you know the service is back up.
- **Clear Cache**: Forces the system to fetch fresh data for all stocks. Useful if bad data was cached.
- **Health Check**: View success rates and latency for each provider per market (US/India).

---

## 🧾 User Management Strategy

### Handling Suspicious Users
1. **Investigate**: Check "Audit Logs" for their activity.
2. **Disable**: Use "Disable Account" button (Super Admin only).
3. **Analyze**: Check their IP in "Traffic > Top IPs".
4. **Blacklist**: If abuse is confirmed, add their IP to the blacklist.

---

## 🛠 Troubleshooting

### Common Admin Issues

**1. "Access Denied" on Admin Route**
- **Cause**: Your user role is likely `user`.
- **Fix**: Update database: `UPDATE users SET role='admin' WHERE email='...'`.

**2. Dashboard Shows "System Down"**
- **Cause**: One of the core services (Redis/MySQL) is unreachable.
- **Fix**: Check docker containers: `docker ps`.

**3. Kill Switch Won't Activate**
- **Cause**: Incorrect confirmation code or lack of `SUPER_ADMIN` role.
- **Fix**: Ensure you type the code exactly (case-sensitive) and have correct privileges.
