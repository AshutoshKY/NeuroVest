# NeuroVest Deployment Guide: Oracle Cloud + Vercel

This guide covers deploying your backend (FastAPI + Redis + MySQL) to Oracle Cloud Free Tier and your frontend (Next.js) to Vercel, then connecting them.

---

## Architecture Overview

```
┌─────────────────────┐              ┌─────────────────────────────────────┐
│       Vercel        │              │       Oracle Cloud Free Tier       │
│    (Next.js FE)     │              │         ARM VM (24GB RAM)          │
│                     │    HTTPS     │                                     │
│  neurovest.vercel   │─────────────▶│  ┌─────────────────────────────┐   │
│       .app          │   API Calls  │  │    Docker Compose Stack      │   │
│                     │              │  │  ┌────────┬───────┬───────┐ │   │
│  Env Variable:      │              │  │  │Backend │ Redis │ MySQL │ │   │
│  NEXT_PUBLIC_API_URL│              │  │  │ :8000  │ :6379 │ :3306 │ │   │
│  = https://your-    │              │  │  └────────┴───────┴───────┘ │   │
│    oracle-ip:8000   │              │  └─────────────────────────────┘   │
└─────────────────────┘              │                                     │
                                     │  Public IP: xxx.xxx.xxx.xxx         │
                                     └─────────────────────────────────────┘
```

---

## Part 1: Oracle Cloud Setup (Backend)

### Step 1: Create Oracle Cloud Account

1. Go to [cloud.oracle.com](https://cloud.oracle.com)
2. Click "Start for free"
3. Fill in details (requires credit card for verification but won't charge)
4. Select a home region close to you

> [!IMPORTANT]
> Oracle verifies your card but doesn't charge. The Free Tier is **always free** with no time limit.

---

### Step 2: Create ARM VM Instance

1. Go to **Compute → Instances → Create Instance**
2. Configure:
   - **Name**: `neurovest-backend`
   - **Image**: Ubuntu 22.04 (or 24.04)
   - **Shape**: Click "Change Shape" → Ampere → **VM.Standard.A1.Flex**
   - **OCPUs**: 4 (free tier allows up to 4)
   - **Memory**: 24 GB (max free)
   - **Boot Volume**: 100 GB (free allows 200 GB total)

3. **Networking**: Keep "Create new VCN" checked
4. **SSH Keys**: Upload your public key or generate a new one
   ```bash
   # Generate SSH key if you don't have one
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/oracle_neurovest
   ```
5. Click **Create**

---

### Step 3: Configure Security Rules (Firewall)

1. Go to **Networking → Virtual Cloud Networks → Your VCN**
2. Click **Security Lists → Default Security List**
3. Add **Ingress Rules**:

| Source CIDR | Protocol | Port | Description |
|-------------|----------|------|-------------|
| 0.0.0.0/0 | TCP | 8000 | Backend API |
| 0.0.0.0/0 | TCP | 80 | HTTP (for Certbot) |
| 0.0.0.0/0 | TCP | 443 | HTTPS |

---

### Step 4: SSH into Your VM

```bash
ssh -i ~/.ssh/oracle_neurovest ubuntu@YOUR_PUBLIC_IP
```

### Step 5: Install Docker

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sudo sh

# Add user to docker group
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Log out and back in for group changes
exit
```

SSH back in:
```bash
ssh -i ~/.ssh/oracle_neurovest ubuntu@YOUR_PUBLIC_IP
```

---

### Step 6: Clone Your Repository

```bash
# Clone your repo
git clone https://github.com/YOUR_USERNAME/neurovest.git
cd neurovest
```

---

### Step 7: Create Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    container_name: neurovest_mysql
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: stockmarket_db
      MYSQL_USER: stockmarket_user
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
    networks:
      - neurovest_network
    restart: always
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      timeout: 20s
      retries: 10

  redis:
    image: redis:7-alpine
    container_name: neurovest_redis
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    networks:
      - neurovest_network
    restart: always
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: neurovest_backend
    environment:
      MYSQL_HOST: mysql
      MYSQL_PORT: 3306
      MYSQL_USER: stockmarket_user
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
      MYSQL_DATABASE: stockmarket_db
      REDIS_HOST: redis
      REDIS_PORT: 6379
      AZURE_OPENAI_API_KEY: ${AZURE_OPENAI_API_KEY}
      AZURE_OPENAI_ENDPOINT: ${AZURE_OPENAI_ENDPOINT}
      AZURE_OPENAI_DEPLOYMENT: ${AZURE_OPENAI_DEPLOYMENT}
      AZURE_OPENAI_API_VERSION: ${AZURE_OPENAI_API_VERSION}
      AZURE_OPENAI_EMBEDDING_DEPLOYMENT: ${AZURE_OPENAI_EMBEDDING_DEPLOYMENT}
      FINNHUB_API_KEY: ${FINNHUB_API_KEY}
      ALPHA_VANTAGE_API_KEY: ${ALPHA_VANTAGE_API_KEY}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      DEBUG: "False"
      # CORS - Allow your Vercel domain
      CORS_ORIGINS: "https://neurovest.vercel.app,https://your-custom-domain.com"
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
    ports:
      - "8000:8000"
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - neurovest_network
    restart: always

volumes:
  mysql_data:
  redis_data:

networks:
  neurovest_network:
    driver: bridge
```

---

### Step 8: Create Environment File

Create `.env` on the server:

```bash
nano .env
```

```env
# Database
MYSQL_ROOT_PASSWORD=your_secure_root_password
MYSQL_PASSWORD=your_secure_db_password

# JWT
JWT_SECRET_KEY=your_very_long_random_secret_key_here

# Azure OpenAI
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Stock APIs
FINNHUB_API_KEY=your_finnhub_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
```

---

### Step 9: Deploy Backend

```bash
# Build and start
docker compose -f docker-compose.prod.yml up -d --build

# Check status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f backend
```

### Step 10: Test Backend

```bash
# From your local machine
curl http://YOUR_ORACLE_IP:8000/health
```

---

## Part 2: HTTPS Setup (Recommended)

### Option A: Caddy (Easiest)

```bash
# Install Caddy
sudo apt install caddy -y

# Configure
sudo nano /etc/caddy/Caddyfile
```

```caddyfile
api.yourdomain.com {
    reverse_proxy localhost:8000
}
```

```bash
sudo systemctl restart caddy
```

### Option B: Use Oracle IP Directly (No domain needed)

If you don't have a domain, use the public IP directly. Vercel can still connect to `http://YOUR_IP:8000`.

---

## Part 3: Vercel Deployment (Frontend)

### Step 1: Connect Repository

1. Go to [vercel.com](https://vercel.com) and sign in with GitHub
2. Click **"Add New Project"**
3. Import your `neurovest` repository
4. Configure:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Next.js
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

### Step 2: Set Environment Variables

In Vercel project settings → **Environment Variables**, add:

| Name | Value |
|------|-------|
| `NEXT_PUBLIC_API_URL` | `http://YOUR_ORACLE_IP:8000` |

> If you set up HTTPS with a domain: `https://api.yourdomain.com`

### Step 3: Deploy

Click **Deploy**. Vercel will build and deploy your frontend.

Your app will be available at: `https://your-project.vercel.app`

---

## Part 4: Backend CORS Configuration

Update your backend `main.py` to allow Vercel:

```python
# In backend/app/main.py

from fastapi.middleware.cors import CORSMiddleware
import os

# Get allowed origins from environment
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

The `CORS_ORIGINS` env var in docker-compose.prod.yml should include your Vercel URL.

---

## Quick Reference Commands

```bash
# SSH into Oracle VM
ssh -i ~/.ssh/oracle_neurovest ubuntu@YOUR_IP

# Start all services
docker compose -f docker-compose.prod.yml up -d

# Stop all services
docker compose -f docker-compose.prod.yml down

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Rebuild after code changes
git pull
docker compose -f docker-compose.prod.yml up -d --build

# Check disk space
df -h

# Check memory
free -h
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Can't connect to port 8000 | Check Oracle Security List ingress rules |
| CORS errors | Verify `CORS_ORIGINS` includes your Vercel URL |
| MySQL connection refused | Wait for healthcheck, check logs |
| Out of memory | Reduce MySQL buffer pool size |

---

## Cost Summary

| Service | Cost |
|---------|------|
| Oracle Cloud VM | **$0** (Always Free Tier) |
| Oracle Block Storage | **$0** (200 GB free) |
| Vercel Frontend | **$0** (Hobby tier) |
| **Total** | **$0/month** |

---

## Part 5: Resource Sizing & Multiple Projects

You can run multiple projects on Oracle's Free Tier by splitting the resources.

### Oracle Free Tier Limits (Total)
*   **4 ARM OCPUs** (CPU Cores)
*   **24 GB RAM**
*   **200 GB Storage**

### Resource Usage Analysis (NeuroVest)
Based on production monitoring:
*   **Backend (Python + AI Models):** ~1 GB RAM
*   **MySQL Database:** ~500 MB RAM
*   **Redis Cache:** ~50 MB RAM
*   **Total Utilization:** ~1.5 - 2 GB RAM (out of 24 GB available)

### Scenario: Running 3 Large Projects (NeuroVest x3)

Yes, you can run 3 full-sized projects comfortably. Here is the exact optimal split to maximize your free 24GB RAM and 4 OCPUs:

| **Instance** | **Allocated CPU** | **Allocated RAM** | **Capacity Analysis** |
| :--- | :--- | :--- | :--- |
| **VM 1 (NeuroVest)** | **1 OCPU** | **8 GB** | ✅ **4x more than needed** (Uses ~2GB) |
| **VM 2 (Project B)** | **1 OCPU** | **8 GB** | ✅ **4x more than needed** |
| **VM 3 (Project C)** | **2 OCPU** | **8 GB** | ✅ **Extra CPU power** (Using remaining core) |
| **TOTAL** | **4 OCPUs** | **24 GB** | **100% Utilized (Max Free Tier)** |

**Why this works:**
1.  **Memory:** Each project realistically needs ~2GB. Giving them **8GB each** provides huge headroom for traffic spikes or adding more AI models.
2.  **CPU:** 1 ARM OCPU is quite powerful (equivalent to ~2 vCPUs on Intel). Since your app is mostly waiting for DB/API responses, 1 OCPU is plenty.
3.  **Storage:** You have **200 GB**. Split it: 50GB boot volume per VM (x3 = 150GB), leaving 50GB spare.

> **Recommendation:** This configuration gives you 3 distinct production environments that are completely isolated. If Project B crashes, NeuroVest stays up.


