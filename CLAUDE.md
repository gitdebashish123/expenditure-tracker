# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

Wallet Mantra — a personal expenditure tracker with natural-language expense input, powered by the Anthropic Claude API. The user types prompts like `zomato 500, ola 200` and the app auto-categorises, saves, and tracks budgets.

## Tech Stack

- **Runtime**: Python 3.13 (uv-managed CPython 3.13.8)
- **Package manager**: `uv` — always use `uv run`, `uv add`, `uv sync`. Never use `pip` directly.
- **Backend**: FastAPI + Uvicorn, SQLite via SQLModel
- **Auth**: JWT (HS256, 8h default), bcrypt passwords via `backend/auth.py`
- **AI**: Anthropic Claude API (`claude-sonnet-4-20250514`) for expense parsing
- **Frontend (primary)**: React 18 + TypeScript + Vite + TailwindCSS, served by Nginx in Docker, port 80
- **Frontend (legacy)**: Streamlit `frontend/app.py` — kept during migration, not the active UI
- **Config**: `config.yaml` — salary, fixed expenses, budget limits, vendor→category mappings

## Commands

### Backend

```bash
# Start FastAPI (dev, with reload)
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Start everything (backend + Streamlit legacy)
./start.sh
```

### React Frontend

```bash
cd frontend/react
npm install          # first time only
npm run dev          # Vite dev server → http://localhost:5173
npm run build        # TypeScript check + Vite production build
npm run lint         # ESLint (zero-warning policy)
```

### Docker (full stack)

```bash
docker compose up -d            # start db-init, backend, React/Nginx frontend
docker compose up -d --build    # rebuild images after code changes
docker compose logs -f          # watch logs
docker compose down             # stop (keeps DB volume)
docker compose down -v          # stop + delete DB volume ⚠️
```

Access: React UI → `http://localhost:80`, API docs → `http://localhost:8000/docs`

### Tests

```bash
# Integration test — requires live backend on :8000
uv run python tests/test_isolation.py

# UAT smoke test
uv run python scripts/uat_test.py

# Schema migration (run after model changes)
uv run python migrate_schema.py
```

## Environment Variables

Copy `.env.example` to `.env`. Required vars:

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key |
| `JWT_SECRET_KEY` | HS256 signing key — backend refuses to start without it |

Generate JWT key: `python3 -c "import secrets; print(secrets.token_hex(32))"`

For Docker/Railway: `VITE_API_BASE` is the backend URL baked into the React bundle at build time (defaults to `http://localhost:8000`).

## Architecture

### Backend (`backend/`)

- `main.py` — FastAPI app. All endpoints (except `/health`, `/auth/register`, `/auth/login`) require `Depends(get_current_user)`. Rate-limited via slowapi. Input sanitised with bleach.
- `models.py` — SQLModel schema. Every table has a `user_id` FK for per-user data isolation. Two special model types:
  - `FixedExpenseTemplate` with `template_type="fixed"` — known monthly amount (rent, EMI)
  - `FixedExpenseTemplate` with `template_type="pool"` — ad-hoc entries per payee (electricity bill split across home/rented house); child rows are `PoolEntry`
- `auth.py` — `get_current_user` FastAPI dependency used on every protected endpoint. JWT decoded via python-jose. bcrypt used directly (not passlib — compatibility issue with bcrypt ≥4 on Python 3.13).
- `budget_rules.py` — `seed_fixed_expenses()` materialises `FixedExpenseTemplate` rows into the `expense` table each month; `get_balance_summary()` and `check_budget_warnings()` drive the dashboard numbers.
- `ai_parser.py` — single `parse_expense_input()` function that calls Claude with vendor→category hints from `config.yaml`.

On startup, the backend: auto-migrates `user.onboarding_complete` column if missing, seeds budget limits from `config.yaml` for the admin user, and creates a default admin account if no users exist.

### React Frontend (`frontend/react/src/`)

Provider tree (outermost → innermost): `ThemeProvider → AuthProvider → ToastProvider → BrowserRouter`

Pages:
- `/login` → `LoginPage` (public)
- `/` → `DashboardPage` (protected) — 6 tabs: **today** (QuickAdd), **fixed**, **overview**, **history**, **settings**, **admin** (admin users only)
- `/account` → `AccountPage` (change password, delete account)

New users see `OnboardingWizard` before the dashboard (gated by `user.onboarding_complete`). After the wizard, `POST /auth/complete-onboarding` is called and `AuthContext.refreshUser()` flips the flag.

API calls go through `src/api/client.ts` (axios instance). JWT token stored in `localStorage`. 401 responses auto-redirect to `/login`. Backend URL from `VITE_API_BASE` env var.

Path alias: `@` → `src/` (configured in `vite.config.ts` and `tsconfig.json`).

PWA: configured in `vite.config.ts` via `vite-plugin-pwa`. `/summary/*` uses NetworkFirst caching; `/expenses/*` uses StaleWhileRevalidate.

### Docker Compose

Three services: `db-init` (runs `migrate_schema.py` then exits) → `backend` (FastAPI) → `frontend` (React built by Vite, served by Nginx). DB persisted in a named Docker volume `spendsense_data`.

## Coding Conventions

- All new Python packages: `uv add <package>` — never pip
- All new JS packages: `npm install <package>` inside `frontend/react/`
- DB schema changes: `backend/models.py`, then run `migrate_schema.py`
- Business logic: `backend/budget_rules.py`
- AI prompt changes: `backend/ai_parser.py`
- `config.yaml` is the only place for salary, budget limits, or fixed expense amounts — not hardcoded in Python
- Month keys are always `"YYYY-MM"` strings (e.g. `"2026-05"`)
- Data isolation: every DB query in `main.py` must filter by `user_id == current_user.id`
- The `/export/csv/all` route must be defined before `/export/csv/{month_key}` in `main.py` — FastAPI route ordering prevents "all" being treated as a month key

## Key Domain Facts

- **Net monthly salary**: ₹1,46,709 (Infosys)
- **Fixed expenses total**: ~₹1,04,555/month (rent, EMIs, RDs, MFs, insurance, cook, milk, etc.)
- **Variable budget available**: ~₹42,154/month
- **Budget limits** (variable categories): Food ₹2,000 · Travel ₹4,000 · Groceries ₹5,000 · Shopping ₹3,000 · Medical ₹5,000 · Entertainment ₹2,000
- **Warning thresholds**: 80% → warning, 100% → danger alert

## Planned Features

- Telegram bot for faster logging
- Google Sheets write-back sync
- UPI/SMS auto-parsing
- OCR receipt scanning
- Monthly summary report (email/WhatsApp)
- `/api/v1` prefix via `APIRouter` (TODO noted in `main.py`)
