---
description: Resume Admin Command Center development after crash or new session
---

# Admin Command Center Workflow

This workflow helps resume work on the NeuroVest Admin Command Center project.

## Pre-requisites
- Docker running with backend, MySQL, Redis
- Frontend dev server running
- Admin user account exists

## Recovery Steps

### Step 1: Read Context
Read the system context file that contains all codebase analysis:
```
View file: /Volumes/AshDrive/prjts/stockmarket/docs/ADMIN_COMMAND_CENTER_CONTEXT.md
```

### Step 2: Check Progress
Check the current task progress:
```
View file: /Users/ashmav/.gemini/antigravity/brain/06cfaaf6-f361-47a4-a74c-86f0e30a1cf6/task.md
```

### Step 3: Review Implementation Plan
```
View file: /Users/ashmav/.gemini/antigravity/brain/06cfaaf6-f361-47a4-a74c-86f0e30a1cf6/implementation_plan.md
```

### Step 4: Verify Environment
// turbo
```bash
cd /Volumes/AshDrive/prjts/stockmarket && docker ps --format "table {{.Names}}\t{{.Status}}"
```

### Step 5: Ask User for Resume Point
Ask the user: "Which phase should I continue from? Current status: [check task.md]"

## Phase Checkpoints

### Phase 0 - System Discovery
- [ ] Project structure explored
- [ ] Docs (JWT, Rate Limiting, Database) read
- [ ] Backend core code analyzed
- [ ] Frontend structure understood
- [ ] Design files (7 HTML) reviewed
- [ ] Implementation plan created

### Phase 1 - RBAC & Trust Model
- [ ] UserRole enum updated with SUPER_ADMIN
- [ ] rbac.py dependency created
- [ ] Database migration for role column
- [ ] audit_logs table created
- [ ] Tests for role enforcement

### Phase 2 - JWT Invalidation
- [ ] auth_epoch in Redis
- [ ] verify_token() updated to check epoch
- [ ] session_control.py service created
- [ ] Force logout API endpoint
- [ ] Tests for token invalidation

### Phase 3 - Kill Switches
- [ ] kill_switch.py module created
- [ ] security_middleware.py updated
- [ ] admin_kill_switch.py API created
- [ ] SUPER_ADMIN enforcement
- [ ] Typed confirmation required
- [ ] Tests for kill switch

### Phase 4 - Metrics Infrastructure
- [ ] metrics_middleware.py created
- [ ] Request metrics collected
- [ ] request_metrics table created
- [ ] infra_metrics.py for Redis/MySQL/ChromaDB
- [ ] Hourly aggregation working

### Phase 5 - AI & RAG Metrics
- [ ] ai_metrics.py wrapper created
- [ ] rag.py updated to track tokens/cost
- [ ] Guardrail rejection tracking
- [ ] Redis keys for AI metrics

### Phase 6 - Admin Backend APIs
- [ ] admin_overview.py
- [ ] admin_infrastructure.py
- [ ] admin_ai.py
- [ ] admin_external_api.py
- [ ] admin_users_intel.py
- [ ] admin_security_events.py

### Phase 7 - Frontend Dashboard
- [ ] AdminSidebar component
- [ ] KPICard component
- [ ] Chart components (ApexCharts)
- [ ] Overview page
- [ ] Infrastructure page
- [ ] AI & RAG page
- [ ] API Health page
- [ ] Users page
- [ ] Security page
- [ ] Kill Switches page
- [ ] ConfirmModal component

### Phase 8 - Audit & Safety Net
- [ ] Enhanced audit logging
- [ ] SSE for live audit stream
- [ ] Historical audit search

## Quick Commands

### Start Environment
// turbo
```bash
cd /Volumes/AshDrive/prjts/stockmarket && docker-compose up -d
```

### Check Backend Logs
// turbo
```bash
docker logs stockmarket-backend-1 --tail 50
```

### Run Backend Tests
```bash
cd /Volumes/AshDrive/prjts/stockmarket/backend && python -m pytest tests/ -v
```

### Start Frontend
// turbo
```bash
cd /Volumes/AshDrive/prjts/stockmarket/frontend && npm run dev
```

## Key Design Files
- `/Volumes/AshDrive/prjts/stockmarket/design_poc_1/neurovest-admin/admin_overview.html`
- `/Volumes/AshDrive/prjts/stockmarket/design_poc_1/neurovest-admin/admin_infrastructure.html`
- `/Volumes/AshDrive/prjts/stockmarket/design_poc_1/neurovest-admin/admin_ai_rag.html`
- `/Volumes/AshDrive/prjts/stockmarket/design_poc_1/neurovest-admin/admin_api_health.html`
- `/Volumes/AshDrive/prjts/stockmarket/design_poc_1/neurovest-admin/admin_users.html`
- `/Volumes/AshDrive/prjts/stockmarket/design_poc_1/neurovest-admin/admin_security.html`
- `/Volumes/AshDrive/prjts/stockmarket/design_poc_1/neurovest-admin/admin_controls.html`
