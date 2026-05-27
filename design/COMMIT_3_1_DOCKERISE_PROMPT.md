# SpendSense — Commit 3.1 Implementation Prompt
## Sprint 3 — Production Infrastructure: Dockerise the App

Reference: `design/MULTI_USER_ROADMAP.md` → Sprint 3, Commit 3.1

---

## Context

SpendSense currently runs on your Mac via `./start.sh` using `uv`. This is fine for
local development but cannot be shared — if your Mac sleeps, the app goes down for
everyone. Docker packages the app into self-contained images that run identically
on any machine or cloud platform.

This commit creates the Docker setup required for Railway/Render deployment (Commit 3.2).

**Project root:** `/Users/debashish/Desktop/ai-projects/expenditure-tracker`  
**Python version:** 3.13 (from `.python-version`)  
**Package manager:** `uv` — Docker images must also use uv, not pip

---

## Current Stack Summary

| Component | Technology | Port | Entry point |
|---|---|---|---|
| Backend API | FastAPI + Uvicorn | 8000 | `backend.main:app` |
| Frontend UI | Streamlit | 8501 | `frontend/app.py` |
| Database | SQLite | — | `data/expenses.db` |
| Config | `config.yaml` + `.env` | — | loaded at startup |

---

## Files to Create

```
expenditure-tracker/
├── Dockerfile.backend          ← FastAPI container
├── Dockerfile.frontend         ← Streamlit container
├── docker-compose.yml          ← Local multi-container orchestration
├── .dockerignore               ← Exclude unnecessary files from images
└── backend/main.py             ← Add GET /health endpoint (small addition)
```

---

## Step 1 — Add `GET /health` Endpoint to `backend/main.py`

Add a single health check endpoint **before** the auth endpoints. It must be:
- **Public** — no `Depends(get_current_user)` — Railway/Render call this
  without a token to verify the container is running
- **Lightweight** — no DB query, just return status and version
- **Informative** — return app name, version, and current timestamp

```python
@app.get("/health")
def health_check():
    """Public health check — used by Railway/Render and docker-compose."""
    return {
        "status": "ok",
        "app": "SpendSense",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }
```

Place it immediately after the `CORSMiddleware` block and `on_startup`,
before the Request Models section. It must be the first route defined.

---

## Step 2 — Create `Dockerfile.backend`

### Requirements

- Base image: `python:3.13-slim` — matches `.python-version`, minimal footprint
- Install `uv` inside the image (curl method from astral.sh)
- Copy only what the backend needs — not nginx/, tests/, frontend/, data/
- Use `uv sync --no-dev` — production dependencies only, no dev tools
- Run as a **non-root user** (`appuser`) — security best practice
- Expose port 8000
- Use `uv run` to start uvicorn — consistent with local dev
- `--host 0.0.0.0` is required — containers must bind to all interfaces,
  not just localhost
- No `--reload` flag in production — it watches the filesystem and wastes CPU

### Exact Dockerfile.backend

```dockerfile
# ── SpendSense Backend — Dockerfile ──────────────────────────────────────────
# FastAPI + Uvicorn
# Python 3.13-slim, uv package manager, non-root user
# Exposes port 8000

FROM python:3.13-slim

# System dependencies for bcrypt and cryptography packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv — fast Python package manager
# Pin to a specific version for reproducible builds
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:/root/.local/bin:$PATH"

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy dependency files first (layer caching — only re-runs uv sync
# when pyproject.toml or uv.lock changes, not on every code change)
COPY pyproject.toml uv.lock ./

# Install dependencies as root (into /app/.venv), then fix ownership
RUN uv sync --no-dev --frozen

# Copy application code
COPY backend/     ./backend/
COPY config.yaml  ./config.yaml

# Create data directory with correct ownership
# The volume mount will overlay this, but the directory must exist
RUN mkdir -p /app/data && chown -R appuser:appuser /app

# Switch to non-root user for runtime
USER appuser

# Expose backend port
EXPOSE 8000

# Health check — Docker will mark container unhealthy if this fails
# Start after 30s, check every 30s, timeout 10s, 3 retries before unhealthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command — no --reload in production
CMD ["uv", "run", "uvicorn", "backend.main:app", \
     "--host", "0.0.0.0", "--port", "8000"]
```

---

## Step 3 — Create `Dockerfile.frontend`

### Requirements

- Base image: `python:3.13-slim`
- Same uv installation pattern as backend
- Copy only frontend-related files
- `STREAMLIT_SERVER_HEADLESS=true` — required for Docker, disables browser-open attempt
- `STREAMLIT_SERVER_ADDRESS=0.0.0.0` — must bind to all interfaces
- The frontend calls the backend via `API_BASE` — this must be configurable
  via environment variable so it works both locally and in production
- Expose port 8501

### API_BASE configuration

Currently `frontend/app.py` has `API_BASE = "http://localhost:8000"` hardcoded.
This must be changed to read from an environment variable:

```python
API_BASE = os.getenv("API_BASE", "http://localhost:8000")
```

Add `import os` if not already present at the top of `frontend/app.py`.

This one-line change is required in this commit — without it, the frontend
container cannot reach the backend container (they have different hostnames
in Docker's network).

### Exact Dockerfile.frontend

```dockerfile
# ── SpendSense Frontend — Dockerfile ─────────────────────────────────────────
# Streamlit UI
# Python 3.13-slim, uv package manager, non-root user
# Exposes port 8501

FROM python:3.13-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:/root/.local/bin:$PATH"

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Dependencies (layer cache)
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

# Application code
COPY frontend/    ./frontend/
COPY config.yaml  ./config.yaml

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8501

# Streamlit-specific environment variables
# headless=true: don't try to open a browser (required in containers)
# address=0.0.0.0: bind to all interfaces (required in containers)
# CORS: allow all origins (nginx handles restriction in production)
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_PORT=8501

# Health check using Streamlit's built-in health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["uv", "run", "streamlit", "run", "frontend/app.py", \
     "--server.address", "0.0.0.0", \
     "--server.port", "8501"]
```

---

## Step 4 — Create `docker-compose.yml`

### Requirements

- Three services: `backend`, `frontend`, `db-init`
- `db-init` — a one-shot service that runs the migration script on startup,
  then exits. Ensures the DB schema is always up to date before services start
- Named volume `spendsense_data` — persists `data/expenses.db` across container
  restarts and image rebuilds
- `backend` depends on `db-init` completing successfully
- `frontend` depends on `backend` being healthy
- Environment variables loaded from `.env` file (never hardcoded in compose)
- `API_BASE` for frontend set to `http://backend:8000` — Docker's internal DNS
  resolves service names automatically
- Health checks reference the `GET /health` endpoint added in Step 1
- Restart policy: `unless-stopped` — containers restart automatically after
  system reboot or crash, but not if manually stopped

### Exact docker-compose.yml

```yaml
# ── SpendSense — Docker Compose ───────────────────────────────────────────────
# Local development and production-equivalent stack
#
# Usage:
#   Start:   docker compose up -d
#   Logs:    docker compose logs -f
#   Stop:    docker compose down
#   Rebuild: docker compose up -d --build
#   Reset:   docker compose down -v   (WARNING: deletes database volume)

version: "3.9"

services:

  # ── Schema Migration (runs once, then exits) ──────────────────────────────
  db-init:
    build:
      context: .
      dockerfile: Dockerfile.backend
    command: ["uv", "run", "python", "migrate_add_user_id.py"]
    env_file: .env
    volumes:
      - spendsense_data:/app/data
      # Mount migration script so it can access the DB
      - ./migrate_add_user_id.py:/app/migrate_add_user_id.py:ro
    restart: "no"   # one-shot — run once and exit

  # ── FastAPI Backend ────────────────────────────────────────────────────────
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    env_file: .env
    volumes:
      - spendsense_data:/app/data
    depends_on:
      db-init:
        condition: service_completed_successfully
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      start_period: 30s
      retries: 3

  # ── Streamlit Frontend ─────────────────────────────────────────────────────
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "8501:8501"
    env_file: .env
    environment:
      # Override API_BASE so frontend reaches backend via Docker's internal DNS
      # 'backend' resolves to the backend service's container IP automatically
      API_BASE: "http://backend:8000"
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      start_period: 40s
      retries: 3

volumes:
  # Named volume — persists database across container restarts
  # Data survives: image rebuilds, container recreation, system reboots
  # Data lost only on: docker compose down -v (explicit volume delete)
  spendsense_data:
    driver: local
```

---

## Step 5 — Create `.dockerignore`

Prevents unnecessary files from being copied into Docker build context.
A large build context slows down builds and can accidentally include secrets.

```dockerignore
# Python artifacts
__pycache__/
*.py[cod]
*.egg-info/
.venv/
dist/
build/

# Environment files — NEVER copy into images
# Secrets are injected via --env-file or platform dashboard
.env
.env.local
.env.*.local

# Database — injected via volume mount, not baked into image
data/
*.db

# Development and local tools
nginx/
tests/
design/
.claude/

# Version control
.git/
.gitignore

# macOS
.DS_Store

# IDE
.vscode/
.idea/

# Uploaded data files
*.xlsx
monthly_expenditure.xlsx

# uv local cache
.uv/

# Logs
*.log
```

---

## Step 6 — Update `frontend/app.py`

One line change only. Near the top of the file, find:

```python
API_BASE = "http://localhost:8000"
```

Replace with:

```python
API_BASE = os.getenv("API_BASE", "http://localhost:8000")
```

Ensure `import os` is present in the imports (it already is from Sprint 1).
No other changes to `frontend/app.py` in this commit.

---

## Critical Implementation Notes

**Why `uv sync --frozen`:**
`--frozen` fails the build if `uv.lock` is out of sync with `pyproject.toml`.
This is intentional — it prevents silent dependency drift in production images.
If you add a new package locally, run `uv sync` on your Mac first to update
`uv.lock`, then commit both files before rebuilding the Docker image.

**Why separate Dockerfiles instead of one:**
- Backend and frontend have different startup commands and different file dependencies
- In Railway/Render, each service deploys from its own Dockerfile
- Separate files make it clear what each container needs

**Why `db-init` as a separate service:**
Running migrations as a separate one-shot container is safer than running them
inside the backend's startup code:
- If migration fails, the backend never starts (fail-fast)
- Migration output is in separate logs, easy to inspect
- In production (Railway), this pattern maps to a "pre-deploy command"

**Why `python:3.13-slim` not `python:3.13-alpine`:**
`bcrypt` and `cryptography` packages require C compilation. Alpine uses musl
libc which causes compilation failures for these packages. `slim` (Debian-based)
has the full standard library and works reliably.

**Why `build-essential` in backend image:**
`bcrypt>=5.0.0` compiles native extensions during `uv sync`. Without
`build-essential` (gcc, make, etc.), the build fails. The frontend image
does not need it since Streamlit has no C extensions.

---

## Verification Steps

### V1 — Syntax checks before building
```bash
cd /Users/debashish/Desktop/ai-projects/expenditure-tracker

# Verify health endpoint added
grep -n "def health_check" backend/main.py
# expect: line number with the function

# Verify API_BASE is now env-driven
grep -n "API_BASE" frontend/app.py
# expect: API_BASE = os.getenv("API_BASE", "http://localhost:8000")
```

### V2 — Build both images
```bash
# Build backend image
docker build -f Dockerfile.backend -t spendsense-backend:local .
# expect: Successfully built <image_id>
# expect: no errors during uv sync

# Build frontend image
docker build -f Dockerfile.frontend -t spendsense-frontend:local .
# expect: Successfully built <image_id>
```

### V3 — Test full stack with Docker Compose
```bash
# Start all services
docker compose up -d

# Watch logs until healthy
docker compose logs -f

# Check all containers are running
docker compose ps
# expect: backend running, frontend running, db-init exited (0)
```

### V4 — Verify health endpoints
```bash
# Backend health
curl http://localhost:8000/health
# expect: {"status":"ok","app":"SpendSense","version":"2.0.0","timestamp":"..."}

# Frontend health
curl http://localhost:8501/_stcore/health
# expect: "ok"
```

### V5 — Verify app works end to end
```bash
# Login via Docker-hosted backend
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@spendsense.local","password":"changeme123"}'
# expect: {"access_token": "eyJ...", "token_type": "bearer"}

# Open frontend in browser
open http://localhost:8501
# expect: SpendSense login page loads
# expect: Can log in and see dashboard
```

### V6 — Verify data persists across restart
```bash
# Log an expense via API
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@spendsense.local","password":"changeme123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -X POST http://localhost:8000/expenses/manual \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"vendor":"DockerTest","amount":100,"category":"Food"}'

# Restart containers
docker compose restart backend

# Verify expense still exists
MONTH=$(date +%Y-%m)
curl "http://localhost:8000/expenses/$MONTH" \
  -H "Authorization: Bearer $TOKEN"
# expect: DockerTest expense is still present
```

### V7 — Verify local dev still works (non-Docker)
```bash
# Stop Docker stack
docker compose down

# Start the original way
./start.sh
# expect: App starts normally on ports 8000 and 8501
# Docker setup must not break local development
```

### V8 — Check image sizes
```bash
docker images | grep spendsense
# expect: backend ~500-800MB, frontend ~600-900MB
# (large due to Python + ML libs, acceptable for production)
```

---

## Files Created / Modified in This Commit

| File | Change |
|---|---|
| `Dockerfile.backend` | New — FastAPI container definition |
| `Dockerfile.frontend` | New — Streamlit container definition |
| `docker-compose.yml` | New — local multi-container orchestration |
| `.dockerignore` | New — build context exclusions |
| `backend/main.py` | Add `GET /health` endpoint (public, ~8 lines) |
| `frontend/app.py` | `API_BASE` now reads from `os.getenv()` (1 line) |

### Files NOT changed
- `backend/models.py` — no schema changes
- `backend/auth.py` — no changes
- `backend/budget_rules.py` — no changes
- `pyproject.toml` — no new dependencies for Docker
- `start.sh` — local dev workflow unchanged
- Any `.env` or config files

---

## After This Commit

The app can be started two ways:

| Method | Command | Use case |
|---|---|---|
| Local dev (uv) | `./start.sh` | Development, hot reload |
| Docker Compose | `docker compose up -d` | Production-equivalent, persistent |

Both methods use the same `.env` file and the same `data/` volume path.

---

*Last updated: May 2026*
*Owner: Debashish*
*Status: Prompt ready — awaiting execution approval*
