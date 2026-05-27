# SpendSense — Commit 3.1.1 Implementation Prompt
## Docker Image Size Optimisation (Multi-Stage Builds)

Reference: `design/MULTI_USER_ROADMAP.md` → Sprint 3, Commit 3.1 (improvement)

---

## Context

After Commit 3.1, Docker image sizes are:

| Image | Size | Compressed |
|---|---|---|
| `spendsense-backend:local` | 1.83GB | 422MB |
| `spendsense-frontend:local` | 1.40GB | 316MB |

The backend is large primarily because `build-essential` (~200MB of gcc, make, binutils)
is installed to compile `bcrypt`'s native C extensions — but remains in the final image
even though it's never needed at runtime.

This commit replaces both Dockerfiles with multi-stage builds to strip build tools
from the final runtime image, reducing image size by ~150–200MB on the backend.

**No changes to `docker-compose.yml`, `.dockerignore`, `migrate_schema.py`,
`backend/main.py`, or `frontend/app.py` — Dockerfiles only.**

---

## Why Multi-Stage Builds

A multi-stage Dockerfile uses two `FROM` blocks:

```
Stage 1 (builder)  — has gcc, make, build-essential
                   — runs uv sync, compiles bcrypt native extensions
                   — produces /app/.venv with compiled packages

Stage 2 (runtime)  — clean python:3.13-slim, no build tools
                   — copies only /app/.venv from builder
                   — copies only application code
                   — final image has no compiler, no build artifacts
```

The key line is `COPY --from=builder /app/.venv /app/.venv` — this copies the
fully compiled virtual environment without copying the tools used to build it.
Docker discards the builder stage entirely from the final image.

---

## Step 1 — Replace `Dockerfile.backend` with Multi-Stage Build

### What changes
- Split into two stages: `builder` and `runtime`
- `build-essential` only in `builder` stage — removed from `runtime`
- `uv sync` runs in `builder` — venv copied to `runtime` via `COPY --from`
- Final `CMD` uses `uvicorn` directly (from venv) instead of `uv run uvicorn`
  — `uv` is not needed at runtime since the venv is already built
- All other behaviour identical: non-root user, health check, port 8000

### Exact Dockerfile.backend

```dockerfile
# ── SpendSense Backend — Dockerfile (Multi-Stage) ────────────────────────────
# FastAPI + Uvicorn
# Stage 1: builder — compiles Python packages (includes build-essential for bcrypt)
# Stage 2: runtime — clean image without build tools (~150-200MB smaller)
#
# Build:  docker build -f Dockerfile.backend -t spendsense-backend:local .
# Run:    docker run --env-file .env -p 8000:8000 spendsense-backend:local

# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.13-slim AS builder

# build-essential required to compile bcrypt native C extensions
# Only present in this stage — not copied to runtime image
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Layer cache: only re-runs uv sync when pyproject.toml or uv.lock changes
COPY pyproject.toml uv.lock ./

# Install all production dependencies into /app/.venv
# --frozen: fails if uv.lock is out of sync
# --no-dev: exclude dev tools (pytest, black, etc.)
RUN uv sync --no-dev --frozen

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.13-slim

# Only curl needed at runtime — for HEALTHCHECK
# No build-essential, no compiler, no make
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy uv binary from builder (needed to run `uv run` if required)
COPY --from=builder /root/.local /root/.local
ENV PATH="/root/.local/bin:$PATH"

# Copy the fully compiled virtual environment from builder stage
# This includes bcrypt's compiled .so files — no recompilation needed
COPY --from=builder /app/.venv /app/.venv

# Add venv to PATH so uvicorn is callable directly (no uv run needed)
ENV PATH="/app/.venv/bin:$PATH"

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy application code (after venv copy for layer cache efficiency)
COPY backend/    ./backend/
COPY config.yaml ./config.yaml

# Create data directory mount point
RUN mkdir -p /app/data && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Health check — calls the public GET /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use uvicorn directly from venv — no uv run needed at runtime
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Expected size reduction
- Before: ~1.83GB
- After: ~1.4–1.6GB (saves ~150–200MB by removing build-essential)

---

## Step 2 — Replace `Dockerfile.frontend` with Multi-Stage Build

### What changes
- Same two-stage pattern as backend
- Frontend has no C extensions — no `build-essential` needed in either stage
- Multi-stage still beneficial: removes `uv` installer artifacts from final image
- Final `CMD` uses `streamlit` directly from venv
- All other behaviour identical: non-root user, health check, port 8501, ENV vars

### Exact Dockerfile.frontend

```dockerfile
# ── SpendSense Frontend — Dockerfile (Multi-Stage) ────────────────────────────
# Streamlit UI
# Stage 1: builder — installs Python packages via uv
# Stage 2: runtime — clean image, venv copied from builder
#
# Build:  docker build -f Dockerfile.frontend -t spendsense-frontend:local .
# Run:    docker run --env-file .env -e API_BASE=http://backend:8000 \
#                   -p 8501:8501 spendsense-frontend:local

# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.13-slim AS builder

# curl for uv installer only — not needed in runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Layer cache: only re-runs uv sync when pyproject.toml or uv.lock changes
COPY pyproject.toml uv.lock ./

# Install all production dependencies into /app/.venv
RUN uv sync --no-dev --frozen

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.13-slim

# curl for HEALTHCHECK only
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy compiled venv from builder — no uv needed at runtime
COPY --from=builder /app/.venv /app/.venv

# Add venv to PATH so streamlit is callable directly
ENV PATH="/app/.venv/bin:$PATH"

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy application code
COPY frontend/   ./frontend/
COPY config.yaml ./config.yaml

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8501

# Streamlit configuration
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# API_BASE default — overridden by docker-compose (http://backend:8000)
# and by Railway/Render (production API URL)
ENV API_BASE=http://localhost:8000

# Health check using Streamlit's built-in health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Use streamlit directly from venv — no uv run needed at runtime
CMD ["streamlit", "run", "frontend/app.py", \
     "--server.address", "0.0.0.0", \
     "--server.port", "8501"]
```

### Expected size reduction
- Before: ~1.40GB
- After: ~1.1–1.2GB (saves ~100–200MB by removing uv installer artifacts)

---

## Step 3 — Verify Size Improvement

After implementation, run these commands to confirm the reduction:

```bash
cd /Users/debashish/Desktop/ai-projects/expenditure-tracker

# Rebuild both images with multi-stage
docker build -f Dockerfile.backend  -t spendsense-backend:v2  .
docker build -f Dockerfile.frontend -t spendsense-frontend:v2 .

# Compare sizes
docker images | grep spendsense
# expect:
# spendsense-backend:v2     ~1.4-1.6GB   (was 1.83GB)
# spendsense-frontend:v2    ~1.1-1.2GB   (was 1.40GB)
# spendsense-backend:local  1.83GB       (old, for comparison)
# spendsense-frontend:local 1.40GB       (old, for comparison)

# Full stack test with new images
docker compose down
docker compose up -d --build

# Verify health endpoints still work
curl http://localhost:8000/health
curl http://localhost:8501/_stcore/health

# Verify login still works
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@spendsense.local","password":"changeme123"}'
# expect: {"access_token": "eyJ...", "token_type": "bearer"}

# Clean up old images after verification
docker rmi spendsense-backend:local spendsense-frontend:local
```

---

## Further Reduction Options (Future Consideration)

These are not part of this commit but documented for reference:

| Optimisation | Potential Saving | Complexity | When |
|---|---|---|---|
| Drop `pandas` from frontend, use pure Python for data grouping | ~170MB | Medium | If image size becomes a deployment concern |
| Use `python:3.13-alpine` for frontend (no C extensions needed) | ~80MB | Low | Frontend only — bcrypt not used there |
| Pin `anthropic` SDK to a minimal install | ~50MB | Low | Check if `anthropic[slim]` extra exists |
| Use `.dockerignore` to exclude test data | ~5MB | Trivial | Already done ✅ |
| Use `uv export --no-hashes > requirements.txt` + pip install | ~30MB | Low | Avoids uv in image entirely |

---

## Files Modified in This Commit

| File | Change |
|---|---|
| `Dockerfile.backend` | Replace single-stage with two-stage (builder + runtime) |
| `Dockerfile.frontend` | Replace single-stage with two-stage (builder + runtime) |

### Files NOT changed
- `docker-compose.yml` — no changes needed, build context unchanged
- `backend/main.py` — no changes
- `frontend/app.py` — no changes
- `migrate_schema.py` — no changes
- Any `.env` or config files

---

## Important: Do Not Break Before This Commit

The current `Dockerfile.backend` and `Dockerfile.frontend` work correctly.
Do not implement this commit until:
1. Commit 3.1 verification steps V1–V8 are fully passing
2. A working Docker Compose stack is confirmed with `docker compose ps`
3. The app is accessible at `http://localhost:8501`

This is a pure optimisation — correctness first, then size.

---

*Last updated: May 2026*
*Owner: Debashish*
*Status: Prompt ready — implement before Commit 3.2 (Railway deployment)*
