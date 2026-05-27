# SpendSense — Commit 3.2 Implementation Prompt
## Railway Deployment

Reference: `design/MULTI_USER_ROADMAP.md` → Sprint 3, Commit 3.2

---

## Context

SpendSense runs correctly in Docker Compose locally (Commit 3.1). This commit
deploys it to Railway so it runs 24/7 without depending on your Mac.

**Why Railway (not Render):**
- Free Hobby tier includes persistent volumes (Render free tier does not)
- Two services (backend + frontend) can share a private internal network
- Automatic HTTPS on every deploy with no configuration
- GitHub auto-deploy on push to `main`
- Environment variables managed in dashboard — never in code
- Railway CLI enables deploy from terminal without browser

**Project root:** `/Users/debashish/Desktop/ai-projects/expenditure-tracker`
**GitHub repo:** Must be pushed before deployment (Railway deploys from GitHub)

---

## Architecture on Railway

```
Internet
    │
    ├── https://spendsense-frontend.up.railway.app  (Streamlit, port 8501)
    │         │
    │         │ internal network (railway.internal)
    │         ▼
    └── https://spendsense-backend.up.railway.app   (FastAPI, port 8000)
                    │
                    ▼
             Persistent Volume
             /app/data/expenses.db
```

Two Railway services share one project:
- **backend** — FastAPI, built from `Dockerfile.backend`
- **frontend** — Streamlit, built from `Dockerfile.frontend`

The frontend reaches the backend via Railway's **private internal network**
(`http://backend.railway.internal:8000`) — not the public URL. This is faster,
free of egress charges, and more secure than routing through the internet.

---

## Prerequisites — Complete Before Starting

### Git Branching Strategy

Railway auto-deploys on every push to `main`. This means `main` must only
receive merges when a sprint is fully verified — never during development.

```
main          ← production only — Railway deploys from here
  └── develop ← integration branch — all day-to-day development
        ├── feature/sprint2-data-isolation
        ├── feature/sprint2-api-queries
        ├── feature/sprint3-railway-deploy   ← this commit
        └── feature/sprint4-data-export
```

**Rules:**
- All development work goes to `develop` or `feature/*` branches
- `main` only receives a merge when a sprint is complete and fully verified
- Every merge to `main` triggers a Railway production deploy — treat it as a release

**Set up branching now (if not already done):**

```bash
cd /Users/debashish/Desktop/ai-projects/expenditure-tracker

# Create develop branch from current main
git checkout -b develop
git push origin develop

# All Sprint 2 and Sprint 3 work happens on develop (or feature branches)
# Only merge to main when sprint is verified end-to-end
```

### Pre-flight Checks

```bash
# 1. Verify you are on develop branch
git branch --show-current
# expect: develop

# 2. Verify Docker stack works locally
docker compose up -d
curl http://localhost:8000/health
# expect: {"status":"ok","app":"SpendSense",...}

# 3. Verify git is clean (all changes committed)
git status
# expect: nothing to commit

# 4. Push develop to GitHub
git push origin develop

# 5. Verify Railway CLI is v4+
railway --version
# expect: v4.x.x or higher
# If on older version: brew upgrade railway

# 6. Confirm GitHub remote exists
git remote -v
# expect: origin pointing to your GitHub repo
```

---

## Step 1 — Create `railway.toml`

`railway.toml` tells Railway how to build and run the project. It lives at
the project root and is committed to git.

### Key decisions encoded in railway.toml

**Two services, one config file:**
Railway reads `railway.toml` and creates one service per `[services.X]` block.
Each service specifies its own Dockerfile and start command.

**Health check path:**
Railway uses the health check to know when a deploy is ready before routing
traffic. Backend uses `GET /health` (added in Commit 3.1). Frontend uses
Streamlit's built-in `GET /_stcore/health`.

**Pre-deploy command:**
`migrate_schema.py` runs once before the backend starts on each deploy. This
is the Railway equivalent of the `db-init` Docker Compose service.

**No `render.yaml`** — the roadmap notes Render is skipped for now. Railway only.

### Exact railway.toml

```toml
# ── SpendSense — Railway Deployment Config ────────────────────────────────────
# Defines two services: backend (FastAPI) and frontend (Streamlit)
# Railway reads this file automatically when connected to the GitHub repo
#
# Docs: https://docs.railway.app/reference/railway-toml

[project]
name = "spendsense"

# ── Backend Service ───────────────────────────────────────────────────────────
[services.backend]
# Build from the backend-specific Dockerfile
dockerfile = "Dockerfile.backend"

# Run schema migration before each deploy
# Equivalent to the db-init service in docker-compose.yml
# Runs once, must exit 0 before the backend starts
pre_deploy_command = "uv run python migrate_schema.py"

# Health check — Railway waits for this to return 200 before marking deploy live
healthcheck_path = "/health"
healthcheck_timeout = 60

# Port the backend listens on (must match CMD in Dockerfile.backend)
port = 8000

# Restart policy — restart container if it crashes
restart_policy_type = "on_failure"
restart_policy_max_retries = 3

# ── Frontend Service ──────────────────────────────────────────────────────────
[services.frontend]
dockerfile = "Dockerfile.frontend"

# Health check — Streamlit's built-in health endpoint
healthcheck_path = "/_stcore/health"
healthcheck_timeout = 60

# Port the frontend listens on (must match CMD in Dockerfile.frontend)
port = 8501

restart_policy_type = "on_failure"
restart_policy_max_retries = 3
```

---

## Step 2 — Persistent Volume for SQLite

Railway volumes persist data across deploys and container restarts.
Without a volume, the SQLite database is wiped on every deploy.

### What to do in Railway dashboard

After creating the Railway project (Step 4), for the **backend service** only:

1. Go to: Railway dashboard → spendsense project → backend service → **Volumes**
2. Click **Add Volume**
3. Set mount path: `/app/data`
4. Volume name: `spendsense-db`

This mounts a persistent filesystem at `/app/data` inside the container —
the same path where `expenses.db` lives.

**Frontend does not need a volume** — it has no state.

### Why SQLite on a volume works for 4–5 users

SQLite handles concurrent reads well and serialises writes. For 4–5 users
making occasional API calls, write contention is essentially zero. A volume-mounted
SQLite is production-appropriate at this scale.

**Migration path when needed:** Change `DATABASE_URL` to a PostgreSQL connection
string — SQLModel code is unchanged, only the env var changes.

---

## Step 3 — Environment Variables

### Backend environment variables (set in Railway dashboard)

| Variable | Value | Notes |
|---|---|---|
| `ANTHROPIC_API_KEY` | `sk-ant-...` | From Anthropic console |
| `JWT_SECRET_KEY` | 64-char hex string | Generate: `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `JWT_EXPIRE_MINUTES` | `480` | 8 hours |
| `ADMIN_EMAIL` | `your@email.com` | Your login email |
| `ADMIN_PASSWORD` | strong password | Change from `changeme123` |
| `DATABASE_URL` | `sqlite:////app/data/expenses.db` | 4 slashes — absolute path inside container |
| `DEFAULT_MONTHLY_INCOME` | `0` | Optional fallback |

**Important: `DATABASE_URL` format in Railway**
- Local Docker uses `sqlite:///./data/expenses.db` (relative path)
- Railway needs `sqlite:////app/data/expenses.db` (absolute path, 4 slashes)
- The volume is mounted at `/app/data` — must use absolute path

### Frontend environment variables (set in Railway dashboard)

| Variable | Value | Notes |
|---|---|---|
| `API_BASE` | `http://backend.railway.internal:8000` | Railway's private internal network |

**Why `railway.internal` not the public URL:**
- Internal network is free — no egress bandwidth charges
- Faster — stays within Railway's datacenter
- More secure — backend not directly exposed to internet traffic from frontend

---

## Step 4 — Deploy to Railway

> **Railway CLI v4 note:** The `service create --name` command was removed in
> v4. Services are now created via the dashboard and then linked to the CLI.
> The recommended approach for a two-service project like SpendSense is
> GitHub-connected auto-deploy, which is more reliable and requires no CLI
> uploads at all.

### 4a. Create Railway account and login

```bash
# Login — opens browser for OAuth
railway login

# If browser login fails, use browserless mode:
railway login --browserless
# Opens a URL in terminal — visit it in any browser to complete login

# Verify login
railway whoami
# expect: your Railway account email
```

### 4b. Create project and services in the dashboard

Railway CLI v4 removed `service create --name`. Use the dashboard instead:

1. Go to `https://railway.app` → **New Project** → **Empty Project**
2. Name it `spendsense`
3. Inside the project: click **+ New** → **Empty Service** → name it `backend`
4. Click **+ New** again → **Empty Service** → name it `frontend`

### 4c. Connect GitHub repo to each service

**Preferred method — GitHub auto-deploy via dashboard:**

**For the backend service:**
1. Click the `backend` service tile
2. Go to **Settings** tab
3. Under **Source** section → click **Connect Repo**
4. Select `gitdebashish123/expenditure-tracker`
5. Set **Branch** to `main`
6. Under **Build** section (scroll down below Source):
   - Change **Builder** from `Railpack` to `Dockerfile`
   - A new field appears: **Dockerfile Path** → type `Dockerfile.backend`
7. Under **Deploy** section (scroll down below Build):
   - Set **Start Command** to:
     `uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000`
8. Click **Save** → Railway auto-deploys

**For the frontend service:**
1. Click the `frontend` service tile
2. Go to **Settings** tab
3. Under **Source** section → click **Connect Repo**
4. Select `gitdebashish123/expenditure-tracker`
5. Set **Branch** to `main`
6. Under **Build** section:
   - Change **Builder** from `Railpack` to `Dockerfile`
   - Set **Dockerfile Path** to `Dockerfile.frontend`
7. Under **Deploy** section:
   - Set **Start Command** to:
     `uv run streamlit run frontend/app.py --server.address 0.0.0.0 --server.port 8501`
8. Click **Save** → Railway auto-deploys

> **Why Builder must be set to Dockerfile:**
> Railway's default builder (Railpack) auto-detects Python projects and overrides
> the Dockerfile CMD with its own start command using system Python. This causes
> `ModuleNotFoundError` because the venv built by `uv sync` is bypassed.
> Setting Builder to Dockerfile forces Railway to use your Dockerfile exclusively.
>
> **Why `uv run` prefix in Start Command:**
> Even with Dockerfile builder, the explicit Start Command field in Railway
> overrides the Dockerfile CMD. Always prefix with `uv run` so the virtual
> environment (where all dependencies are installed) is activated before
> starting the app.

> Railway reads `railway.toml` from the repo root automatically — health
> checks, pre-deploy commands, and restart policy are all picked up from
> the file committed in Step 1.

---

**Alternative method — CLI upload (use if GitHub Connect shows "No repositories found")**

Railway's GitHub App sync can lag on trial accounts or newly public repos.
The CLI upload bypasses the GitHub connection entirely and deploys directly
from your Mac. GitHub auto-deploy can be reconnected later once the sync
issue resolves.

```bash
cd /Users/debashish/Desktop/ai-projects/expenditure-tracker

# Verify you are logged in
railway whoami
# expect: your Railway account email

# Link this directory to the spendsense Railway project
railway link
# When prompted:
# Select project: spendsense
# Select environment: production

# Deploy backend service
railway service backend
railway up --detach
# expect: upload starts, build triggered in Railway dashboard

# Deploy frontend service
railway service frontend
railway up --detach
# expect: upload starts, build triggered in Railway dashboard

# Check deployment status and get URLs
railway status
# expect: both services listed with deployed URLs
```

> **Note on CLI upload + Builder settings:**
> Even when deploying via CLI, you must still set the Builder to `Dockerfile`
> and configure the Start Command with `uv run` prefix in the Railway dashboard.
> The CLI uploads the code but Railway still controls how it builds and starts.

### 4d. Add volume to backend service (dashboard only)

Volumes cannot be created via CLI — dashboard only:

1. Click the `backend` service tile
2. Go to **Volumes** tab → **Add Volume**
3. Mount path: `/app/data`
4. Volume name: `spendsense-db`
5. Click **Create Volume**

The volume mounts at `/app/data` inside the container — this is where
`expenses.db` lives. Data persists across all deploys.

### 4e. Set environment variables (dashboard)

**Backend service → Variables tab:**

Add each variable from the backend table in Step 3. Railway redeploys
automatically after saving variables.

Quickest method — use Railway's **Raw Editor** (paste all at once):
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
JWT_SECRET_KEY=your-64-char-hex-here
JWT_EXPIRE_MINUTES=480
ADMIN_EMAIL=your@email.com
ADMIN_PASSWORD=your-strong-password
DATABASE_URL=sqlite:////app/data/expenses.db
DEFAULT_MONTHLY_INCOME=0
```

**Frontend service → Variables tab:**
```
API_BASE=http://backend.railway.internal:8000
```

### 4f. Link CLI to project (optional — for logs and status)

```bash
cd /Users/debashish/Desktop/ai-projects/expenditure-tracker

# Link this directory to the Railway project
railway link
# When prompted:
# Select project: spendsense
# Select environment: production

# Check status
railway status
# expect: both services listed with deployed URLs

# View logs
railway logs --service backend
railway logs --service frontend
```

### 4g. Get deployed URLs

```bash
railway status
# Shows URLs for both services, e.g.:
# backend:  https://spendsense-backend-production.up.railway.app
# frontend: https://spendsense-frontend-production.up.railway.app
```

Or find them in the dashboard: click each service tile → **Settings** →
**Networking** → **Generate Domain**.

---

## Step 5 — Merge to `main` and Verify Auto-Deploy

Railway is configured to deploy from `main`. All work so far has been on
`develop`. This step merges `develop` → `main` for the first production deploy.

**Only do this step when all local verification passes.**

```bash
cd /Users/debashish/Desktop/ai-projects/expenditure-tracker

# Ensure develop is clean and up to date
git checkout develop
git status
# expect: nothing to commit

# Merge develop into main — this triggers Railway deploy
git checkout main
git merge develop --no-ff -m "release: Sprint 3.2 Railway deployment"
git push origin main
# expect: Railway dashboard shows new deploy triggered within 30 seconds
```

**`--no-ff` flag** — creates a merge commit instead of fast-forwarding.
This keeps the git history clean — you can clearly see when each sprint
was released to production.

**After this merge, all future sprint work:**
```bash
# Always develop on develop or feature branches — never directly on main
git checkout develop

# When a sprint is complete and verified:
git checkout main
git merge develop --no-ff -m "release: Sprint X.X description"
git push origin main   # triggers Railway deploy
git checkout develop   # immediately switch back
```

**Verify Railway auto-deploy triggered:**
1. Open Railway dashboard after `git push origin main`
2. expect: new deployment triggered within 30 seconds
3. expect: deploy goes live within 3–5 minutes
4. expect: zero downtime (Railway uses rolling deploys)

---

## Step 6 — Update CORS for Production URL

Once deployed, the backend needs to allow requests from the production frontend URL.

In `backend/main.py`, update `allow_origins` to include the Railway frontend URL:

```python
allow_origins=[
    "http://localhost:8501",           # local HTTP
    "https://localhost:8443",          # local HTTPS via nginx
    "https://YOUR-FRONTEND.up.railway.app",  # production — replace with actual URL
]
```

**Important:** Get the actual frontend URL from `railway status` first, then update.
Commit and push — Railway auto-deploys.

---

## Step 7 — Update README.md

Add a **Deployment** section to README.md covering:

1. **Live URLs** — link to the deployed frontend and API docs
2. **Re-deploying** — `git push origin main` triggers auto-deploy
3. **Checking logs** — `railway logs --service backend` and `--service frontend`
4. **Environment variables** — where to update them (Railway dashboard, never in code)
5. **Database backup** — manual backup command (Commit 3.3 will automate this)
6. **Rollback** — Railway dashboard → Deployments → click previous deploy → Rollback

---

## Verification Steps

### V1 — Health endpoints respond on production URLs
```bash
# Get your URLs first
railway status

BACKEND_URL="https://YOUR-BACKEND.up.railway.app"
FRONTEND_URL="https://YOUR-FRONTEND.up.railway.app"

# Backend health
curl $BACKEND_URL/health
# expect: {"status":"ok","app":"SpendSense","version":"2.0.0","timestamp":"..."}

# Frontend health
curl $FRONTEND_URL/_stcore/health
# expect: "ok"
```

### V2 — HTTPS is automatic
```bash
# Confirm HTTPS — no -k flag needed (certificate is trusted)
curl https://YOUR-BACKEND.up.railway.app/health
# expect: valid response, no certificate warning
```

### V3 — Login works on production
```bash
curl -X POST $BACKEND_URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","password":"your-admin-password"}'
# expect: {"access_token":"eyJ...","token_type":"bearer"}
```

### V4 — Frontend loads and dashboard works
```
Open https://YOUR-FRONTEND.up.railway.app in browser
expect: SpendSense login page loads over HTTPS
Log in with admin credentials
expect: Dashboard renders with all tabs working
```

### V5 — Data persists across redeploy
```bash
TOKEN=$(curl -s -X POST $BACKEND_URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","password":"your-password"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Log a test expense
curl -X POST $BACKEND_URL/expenses/manual \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"vendor":"RailwayTest","amount":100,"category":"Food"}'

# Trigger a redeploy via develop → main merge
git checkout develop
git commit --allow-empty -m "test: verify data persistence across deploy"
git push origin develop
git checkout main
git merge develop --no-ff -m "test: data persistence verification"
git push origin main
git checkout develop

# Wait for redeploy to complete (~3-5 minutes), then check expense still exists
MONTH=$(date +%Y-%m)
curl $BACKEND_URL/expenses/$MONTH \
  -H "Authorization: Bearer $TOKEN"
# expect: RailwayTest expense is still present
```

### V6 — Auto-deploy triggers on main merge
```bash
# Make a change on develop and merge to main
git checkout develop
git commit --allow-empty -m "test: verify Railway auto-deploy"
git push origin develop
git checkout main
git merge develop --no-ff -m "test: auto-deploy verification"
git push origin main
git checkout develop
# Open Railway dashboard
# expect: new deployment triggered within 30 seconds
# expect: new deployment goes live within 3-5 minutes
# expect: zero downtime (Railway uses rolling deploys)
```

### V7 — Internal network used (not public URL)
```bash
# Check frontend logs — API calls should go to railway.internal, not public URL
railway logs --service frontend | grep "API_BASE\|backend"
# expect: references to backend.railway.internal, not the public HTTPS URL
```

---

## Files Created / Modified in This Commit

| File | Change |
|---|---|
| `railway.toml` | New — Railway deployment config |
| `backend/main.py` | Add production frontend URL to `allow_origins` |
| `README.md` | Add Deployment section with live URLs and ops commands |

### Files NOT changed
- `Dockerfile.backend` — unchanged
- `Dockerfile.frontend` — unchanged
- `docker-compose.yml` — local dev unchanged
- `migrate_schema.py` — unchanged (Railway runs it as pre-deploy command)
- `.env` — secrets never in code, set in Railway dashboard

---

## Cost Estimate

Railway Hobby plan ($5/month) covers:
- 2 services (backend + frontend)
- 1 persistent volume (SQLite database)
- Automatic HTTPS on both services
- 100GB outbound bandwidth/month
- GitHub auto-deploy

For 4–5 users with occasional usage, total Railway cost will be **$5/month or less**.

Railway's free tier ($0) also works but sleeps inactive services after inactivity —
not suitable for a shared app where other users need it available at any time.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| "No repositories found" in Connect Repo | Railway GitHub App sync lag — common on trial accounts and newly public repos | Use CLI upload alternative in Step 4c: `railway link` then `railway up --detach` |
| `ModuleNotFoundError: No module named 'jose'` or any missing module | Railway using system Python instead of uv venv | Settings → Build → change Builder from Railpack to Dockerfile; set Dockerfile Path to `Dockerfile.backend` |
| `Error loading ASGI app. Attribute "app" not found in module "main"` | Railway start command using `main` instead of `backend.main` | Settings → Deploy → Start Command: `uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000` |
| `migrate_schema.py` fails on first deploy | `DATABASE_URL` not set or wrong path | Verify `sqlite:////app/data/expenses.db` (4 slashes) in backend variables |
| Frontend shows "Backend not running" | `API_BASE` wrong or backend not healthy | Check `API_BASE=http://backend.railway.internal:8000` in frontend variables |
| Login returns 500 | `JWT_SECRET_KEY` not set | Add it to backend variables in dashboard |
| CORS error in browser | Production frontend URL not in `allow_origins` | Update `main.py` CORS list with actual Railway frontend URL |
| Data lost after redeploy | Volume not mounted or wrong mount path | Verify volume is attached to backend at `/app/data` |
| Streamlit shows blank page | Streamlit not fully booted during health check | Increase `healthcheck_timeout` in `railway.toml` to 120 |

---

## Important: Do Before This Commit

1. ✅ Commit 3.1 Docker stack working locally (`docker compose ps` all healthy)
2. ✅ All code committed and pushed to GitHub (`git status` clean)
3. ✅ Railway CLI v4+ installed (`railway --version` shows v4.x.x)
4. ✅ Railway account created at `https://railway.app` and logged in (`railway whoami`)
5. ✅ GitHub repo is public or Railway GitHub App has access to the private repo
6. ✅ `railway.toml` committed to repo (Step 1 complete)

---

## After This Commit — Share with First User

Once V1–V6 verification steps pass, SpendSense is ready to share with the
first external user. Send them:

1. The frontend URL: `https://YOUR-FRONTEND.up.railway.app`
2. A temporary password (they can change it via Settings once logged in)
3. A note that the Anthropic AI parses their expense text — link to PRIVACY.md

**Before sharing:** Change `ADMIN_PASSWORD` in Railway dashboard from `changeme123`
to a strong password. This is the single most important security step before
going multi-user.

**Return to develop after sharing:**
```bash
# All future work continues on develop
git checkout develop
# Never commit directly to main again
```

---

*Last updated: May 2026*
*Owner: Debashish*
*Status: Prompt ready — requires Commit 3.1 verified before execution*
