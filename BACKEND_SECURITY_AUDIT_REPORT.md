# Backend Security Audit & Risk Report

> **Auditor**: Antigravity Agent
> **Date**: January 2026
> **Scope**: Middleware, Authentication, Signal Engine, Infrastructure

## 1. Executive Summary

The NeuroVest backend demonstrates a **high level of security maturity** for an MVP, particularly in its session management and rate-limiting modules. However, **critical stability risks** in the deterministic engines and **authorization gaps** in middleware require immediate remediation to ensure production readiness.

| Component | Rating | Key Finding |
| :--- | :--- | :--- |
| **Authentication** | 🟢 **Excellent** | Zero-downtime key rotation & signed device tokens. |
| **Rate Limiting** | 🟢 **Strong** | 4-Dimensional tracking makes abuse extremely difficult. |
| **Authorization** | 🔴 **Critical** | Middleware RBAC check is present but unimplemented (TODO). |
| **Stability** | 🔴 **Critical** | CPU-bound Signal Engine blocks the Async Event Loop. |

---

## 2. Critical Findings (Red Flags)

### 🔴 Risk 1: "Sync-in-Async" Blocking Calls
**Severity**: CRITICAL (Availability Risk)

-   **Location**: `app/signal_engine/` called from `app/api/stocks.py`.
-   **The Issue**: The `SignalEngine` makes heavy use of **Pandas and NumPy** for technical analysis. These interactions are synchronous and CPU-intensive. When called directly from an `async def` endpoint:
    ```python
    # BLOCKS the entire server loop!
    signal = signal_engine.analyze(df) 
    ```
-   **Impact**: During a heavy analysis (e.g., 200ms), the Python Event Loop is frozen. **Heartbeats fail, other requests timeout, and DB connections may drop.** A single user can effectively DoS the system by spamming analysis requests.
-   **Remediation**: Offload these calls to a thread pool.
    ```python
    # Fix: Run in separate thread
    signal = await asyncio.to_thread(signal_engine.analyze, df)
    ```

### 🔴 Risk 2: Middleware RBAC Gaps
**Severity**: HIGH (Authorization Risk)

-   **Location**: `app/middleware/security_middleware.py`.
-   **The Issue**: The `_is_user_admin` method—intended to protect admin routes globally—contains a placeholder:
    ```python
    # TODO: Decode JWT and check role
    return False 
    ```
-   **Impact**: While individual endpoints use dependency injection (`Depends(require_admin)`) to stay safe, the *Defense-in-Depth* layer is porous. If a developer forgets the dependency on a new admin route, it will be effectively public.
-   **Remediation**: Implement proper JWT decoding in the middleware to enforce the `role: admin` claim globally for `/admin/*` paths.

---

## 3. Security Feature Deep Dive

NeuroVest employs several advanced security patterns.

### 3.1 4-Dimensional Rate Limiting
Most rate limiters track only IP. We track 4 dimensions to prevent evasion.

| Dimension | Method | Evasion Difficulty |
| :--- | :--- | :--- |
| **1. IP Address** | `hash(X-Forwarded-For)` | Low (VPNs) |
| **2. Session ID** | `UUID` in Header | Low (Clear storage) |
| **3. User ID** | JWT Subject | High (Requires new account) |
| **4. Device Token** | **Signed HMAC-SHA256 Token** | **Very High** |

**Device Token Mechanism**:
1. Server generates a signature of the client's fingerprint (Canvas, User-Agent, etc.).
2. This `X-Device-Token` must be sent with headers.
3. If an attacker tampers with the fingerprint, the signature fails.
4. If an attacker replays a token from another machine, the fingerprint mismatch flags it.

### 3.2 Zero-Downtime Key Rotation
-   **Problem**: Rotating JWT keys usually logs everyone out.
-   **Solution**: Triple-Key Window.
    -   New tokens signed with **Key A** (Current).
    -   Server validates against **Key A** OR **Key B** (Yesterday) OR **Key C** (2 days ago).
    -   Key A becomes Key B automatically after 24h.
-   **Result**: Full rotation security with 0 user friction.

---

## 4. Recommendations Roadmap

### Phase 1: Stabilization (Immediate)
-   [ ] **Fix**: Wrap all `SignalEngine`, `PriceEngine`, `ScenarioEngine` calls in `asyncio.to_thread`.
-   [ ] **Fix**: Implement the JWT decoder in `SecurityMiddleware`.

### Phase 2: Hardening
-   [ ] **Refactor**: Remove hardcoded whitelist paths in `rate_limit_middleware.py` in favor of config-based lists.
-   [ ] **Resilience**: Wrap Redis calls in `try/except` to allow the system to "Fail Open" (or "Fail Safe") if Redis goes down, rather than crashing 500.

### Phase 3: Monitoring
-   [ ] **Alerting**: Add alerts for "Circuit Breaker Tripped" events in the Smart Orchestrator.
-   [ ] **Logging**: Standardize audit logs for Admin actions to include "Previous Value" vs "New Value" for diff tracking.
