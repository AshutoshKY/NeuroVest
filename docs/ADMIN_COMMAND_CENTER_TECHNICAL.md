# Admin Command Center: Technical Deep Dive & Architecture

**Version**: 2.0  
**Last Updated**: January 2026  
**Status**: Live / Production-Ready

---

## 1. Architectural Overview

The **Admin Command Center** is not just a UI; it's a completely separate observability stack running alongside the main application. It uses a **Smart Orchestrator** pattern to aggregate real-time data from multiple sources (Redis, Docker, MySQL, ChromaDB) without impacting the performance of the core stock analysis engine.

### Core Components
1.  **Frontend (`/frontend/src/app/admin`)**: Next.js 14 + React Server Components + Client Hooks. Uses "Glassmorphism" UI for premium feel.
2.  **Backend Aggregator (`AdminOrchestrator`)**: specialized service in `backend/app/api/admin_orchestrator.py` that fan-outs requests to subsystems.
3.  **Metrics Pipeline**:
    *   **System Metrics**: Direct interface with Docker Socket (`/var/run/docker.sock`) for container stats.
    *   **AI Metrics**: Event-based recording of RAG latency and token usage.
    *   **Business Metrics**: Real-time aggregation from Redis counters.

---

## 2. Frontend Implementation (`/frontend`)

### 2.1 Unified Data Fetching Hook
We implemented a custom hook `useSREUnifiedOverview` (`frontend/src/hooks/useMetrics.ts`) that solves the "N+1" request problem. Instead of 10 separate API calls, it hits a single aggregator endpoint.

```typescript
// frontend/src/hooks/useMetrics.ts
export function useSREUnifiedOverview(refreshInterval = 30000) {
  // Polls /admin/sre-unified-overview every 30s
  // Returns: { system_health, ai_metrics, active_users, alerts, ... }
  // Handles errors gracefully to prevent dashboard crash
}
```

### 2.2 Reusable Chart Components
We use `react-chartjs-2` with a custom "Neon" theme wrapper to ensure consistency.
*   **Location**: `frontend/src/components/admin/charts/`
*   **Key File**: `GradientLineChart.tsx` - Automatically handles gradient fills (Green/Red/Blue) based on trend direction.

### 2.3 Page Structure
*   **Overview (`/admin`)**: High-level KPIs. Uses `StatsCard` components.
*   **Infrastructure (`/admin/infrastructure`)**:
    *   **Real-time Container Stats**: CPU/Mem usage from Docker.
    *   **Redis/MySQL**: Interactive connection logic.
*   **AI/RAG (`/admin/ai-rag`)**:
    *   **Scatter Plot**: Token usage vs Latency.
    *   **Cost Estimator**: Live calculation based on Azure pricing ($0.03/1k input, $0.06/1k output).

---

## 3. Backend Implementation (`/backend`)

### 3.1 Async RAG & Concurrency (`rag.py`)
**Problem**: Previous synchronous OpenAI calls blocked the implementation (10s+ latency).
**Solution**: Converted to fully Async implementation.
*   **File**: `app/services/rag.py`
*   **Change**:
    ```python
    # OLD (Blocking)
    self.client = AzureOpenAI(...)
    response = self.client.chat.completions.create(...)

    # NEW (Non-Blocking)
    self.async_client = AsyncAzureOpenAI(...)
    response = await self.async_client.chat.completions.create(...)
    ```
*   **Result**: The server can now handle **concurrent stock analyses**. One user analyzing "TCS" does not block another user analyzing "RELIANCE".

### 3.2 Non-Blocking Model Loading (`embeddings.py`)
**Problem**: `sentence-transformers` model (~100MB) took 5+ mins to download/load, blocking server startup.
**Solution**: Background Thread Loading + Persistence.
*   **File**: `app/services/embeddings.py` & `app/main.py`
*   **Logic**:
    1.  `docker-compose.yml` mounts volume `/app/data/models`.
    2.  `main.py` triggers `embedding_service.preload_model()` as an asyncio background task.
    3.  Server becomes "Healthy" immediately; model loads in background.

### 3.3 System Metrics Service (`system_metrics.py`)
**Purpose**: Monitor physical resource usage of containers.
*   **Mechanism**: Connects to `unix:///var/run/docker.sock`.
*   **Metrics Collected**:
    *   **CPU %**: Calculated from delta between CPU usage and System CPU usage.
    *   **Memory**: Usage vs Limit.
    *   **Network I/O**: RX/TX bytes.
*   **Security**: The backend container has read-only access to the Docker socket.

---

## 4. Metrics & Signals (What we measure)

### 4.1 SRE Golden Signals
We adhere to Google's SRE Golden Signals:
1.  **Latency**: Time to serve a request.
    *   *RAG Latency*: measured in `rag.py` (Embedding + Retrieval + LLM Generation).
    *   *API Latency*: measured in `metrics_middleware.py`.
2.  **Traffic**: Requests per Second (RPS).
    *   Stored in Redis `rate_limit:{window}` keys.
3.  **Errors**: HTTP 500s.
    *    tracked in `error_middleware.py`.
4.  **Saturation**: Resource fullness.
    *   Redis Memory Usage.
    *   MySQL Connection Pool usage.

### 4.2 AI/RAG Specific Metrics
Located in `app/services/ai_metrics.py`.
*   **Embedding Latency**: Time to vectorise query.
*   **Retrieval Latency**: Time to fetch docs from ChromaDB.
*   **LLM Latency**: Time for Azure OpenAI to generate response.
*   **Context Quality**: Number of documents retrieved vs used.
*   **Token Usage**: Precise input/output token counts from OpenAI response.

---

## 5. Security Deep Dive

### 5.1 RBAC & Middleware
*   **File**: `app/middleware.py`
*   **Admin Access**:
    *   Checks `users` table for `role='admin'`.
    *   Additional check for `is_super_admin` for dangerous actions (Kill switch).
*   **IP Protection**:
    *   Redis-backed IP blacklist.
    *   DDOS protection (rate limit > 100 req/min from single IP).

### 5.2 Encryption
*   **AES-256**: All sensitive frontend-backend communication (login passwords) is encrypted before transmission.
*   **RSA**: Used for key exchange.

---

## 6. Deployment & Docker Strategy

### 6.1 Docker Compose
We use a multi-container architecture defined in `docker-compose.yml`:
*   **backend**: FastAPI (Python 3.11). Persists models to `./backend/data/models`.
*   **frontend**: Next.js 14.
*   **redis**: Caching & Rate Limiting (Persistent volume).
*   **mysql**: User data & History (Persistent volume).

### 6.2 Persistence
To prevent data loss and slow startups:
*   `mysql_data`: Persists User DB.
*   `redis_data`: Persists Rate limits and cache.
*   `SENTENCE_TRANSFORMERS_HOME`: Persists AI models on host disk.

---

## 7. Future Roadmap (Documented)
1.  **Alerting**: Slack/Email webhooks for "Kill Switch" activation.
2.  **Log Aggregation**: Move from `docker logs` to ELK or Loki stack.
3.  **Horizontal Scaling**: K8s deployment manifests (current stacks are Docker Compose).
