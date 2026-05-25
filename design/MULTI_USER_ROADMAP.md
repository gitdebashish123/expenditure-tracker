# SpendSense — Multi-User Implementation Roadmap

This document captures the phased plan to evolve SpendSense from a personal tool into a
secure, multi-user financial tracker suitable for 4–5 trusted users initially, with a
path to medium/large scale.

---

## Context & Motivation

SpendSense was built to solve a personal problem: managing monthly salary wisely, tracking
fixed and variable expenses, and maintaining awareness of remaining balance. As it matures,
the goal is to make it available to a small group of trusted users while ensuring:

- Each user's financial data is completely private and isolated
- The system is trustworthy, transparent, and secure
- The experience is smooth for non-technical users

**Minimum viable multi-user state:** Sprints 1 + 2 + 3  
**Production-ready state:** All 6 sprints complete

---

## Sprint 1 — Secure the Foundation

**Goal:** No one can access the app or API without credentials  
**Effort:** ~1 week  
**Prerequisite:** None

### Commit 1.1 — Environment & Secrets Hygiene
- Move `ANTHROPIC_API_KEY` to `.env` file
- Add `python-dotenv` to `pyproject.toml`
- Add `.env` to `.gitignore`
- Add `.env.example` with placeholder values for new contributors
- Audit `config.yaml` — move any sensitive values to `.env`

### Commit 1.2 — HTTPS Local Setup
- Add `nginx` reverse proxy config for local HTTPS
- Generate self-signed cert for local development
- Document production HTTPS setup via Let's Encrypt in README

### Commit 1.3 — FastAPI Backend Authentication
- Add `python-jose` and `passlib` to dependencies
- Create `backend/auth.py` — JWT token generation and verification
- Add `POST /auth/login` endpoint — returns signed JWT
- Add `POST /auth/register` endpoint — hashed password storage
- Add `get_current_user` dependency — validates JWT on every protected endpoint
- Protect all existing endpoints with `Depends(get_current_user)`
- Add `User` table to `models.py` — id, email, hashed_password, created_at, last_login

### Commit 1.4 — Streamlit Login Screen
- Add `streamlit-authenticator` or custom login form as the app entry point
- Session state carries JWT token — passed in all API calls as Bearer header
- Logout button in header
- Redirect to login if token expired or missing

---

## Sprint 2 — Data Isolation

**Goal:** Every user sees only their own data  
**Effort:** ~3 days  
**Prerequisite:** Sprint 1

### Commit 2.1 — Schema Migration
- Add `user_id` (FK to User) to all tables:
  `Expense`, `IncomeEntry`, `FixedExpenseTemplate`, `PoolEntry`, `BudgetLimit`, `ExpenseTemplate`
- Write `migrate_add_user_id.py` — ALTER TABLE script, assigns existing rows to a default `owner` user
- Update `SQLModel` class definitions in `models.py`

### Commit 2.2 — API Query Isolation
- Update every `select()` query in `main.py` and `budget_rules.py` to filter by `user_id`
- Update every `INSERT` to include `user_id` from the authenticated session
- Update `seed_fixed_expenses()` in `budget_rules.py` to scope to `user_id`
- Update all insight endpoints (`/insights/mom`, `/insights/projection`, `/insights/top-spends`)

### Commit 2.3 — Test Data Isolation
- Write a test script that creates two users, adds data for each, and verifies neither can see the other's data
- Verify all 20+ endpoints respect `user_id` boundary

---

## Sprint 3 — Production Infrastructure

**Goal:** App runs reliably 24/7, not dependent on your Mac being on  
**Effort:** ~2 days  
**Prerequisite:** Sprint 1 + 2

### Commit 3.1 — Dockerise the App
- Write `Dockerfile` for FastAPI backend
- Write `Dockerfile` for Streamlit frontend
- Write `docker-compose.yml` — backend + frontend + volume for SQLite
- Add health check endpoint to FastAPI (`GET /health`)
- Test full stack locally with Docker

### Commit 3.2 — Railway/Render Deployment
- Create `railway.toml` deployment config
- `render.yaml` deployment config will be consider (if required) , for now skip it
- Set all environment variables in platform dashboard (never in code)
- Configure persistent volume for SQLite database
- Set up automatic deploys from `main` branch on GitHub
- Verify HTTPS is automatic on chosen platform

### Commit 3.3 — Backup Strategy
- Write `scripts/backup_db.py` — copies SQLite to a timestamped file
- Schedule daily backup via cron or platform scheduler
- Add backup download endpoint `GET /admin/backup` — admin only
- Document restore procedure in README

---

## Sprint 4 — User Trust & Transparency

**Goal:** Users feel safe sharing their financial data  
**Effort:** ~2 days  
**Prerequisite:** Sprint 2

### Commit 4.1 — Data Export
- Add `GET /export/csv/{month_key}` endpoint — returns all user's expenses as CSV
- Add `GET /export/csv/all` — full history export
- Add "Download my data" button in Settings — visible to all users
- Test that export only returns the authenticated user's data

### Commit 4.2 — Account Management
- Add `DELETE /auth/account` endpoint — deletes user and all their data (cascade)
- Add "Delete my account" button in Settings — requires typing "DELETE" to confirm
- Add `GET /auth/me` endpoint — returns email, created_at, last_login
- Show "Last login" in Settings so users can spot unauthorised access

### Commit 4.3 — Privacy Notice
- Write `PRIVACY.md` — plain English: what is stored, what is sent to Anthropic API,
  how long data is kept, how to delete
- Add a brief privacy note in the onboarding/first-login flow
- Add link to privacy notice in Settings footer

---

## Sprint 5 — Rate Limiting & API Hardening

**Goal:** Prevent abuse, control costs, harden the API  
**Effort:** ~3 days  
**Prerequisite:** Sprint 3

### Commit 5.1 — Rate Limiting
- Add `slowapi` library to dependencies
- Apply rate limits to expensive endpoints:
  - `POST /expenses/parse` — 30 calls/hour per user (AI cost control)
  - `POST /auth/login` — 10 attempts/hour per IP (brute force protection)
  - All other endpoints — 300 calls/hour per user
- Return `429 Too Many Requests` with a clear message when exceeded

### Commit 5.2 — Input Validation & Sanitisation
- Add Pydantic field validators — max lengths on all string fields, positive-only amounts
- Sanitise vendor/label/note fields — strip HTML tags to prevent injection
- Add request size limit to FastAPI — reject payloads over 10KB
- Add CORS restriction — only allow requests from the known frontend URL

### Commit 5.3 — Security Headers
- Add `SecurityMiddleware` to FastAPI — sets `X-Content-Type-Options`,
  `X-Frame-Options`, `Strict-Transport-Security`
- Remove FastAPI default headers that expose server version
- Add API versioning prefix — all routes move to `/api/v1/...`

---

## Sprint 6 — Onboarding & Multi-user Polish

**Goal:** A new user can sign up and be productive in under 5 minutes  
**Effort:** ~1 week  
**Prerequisite:** All above sprints

### Commit 6.1 — Registration Flow
- Self-registration page with email + password (or invite-only with admin-generated tokens)
- Email validation on registration
- Password strength requirements enforced on frontend and backend
- Welcome screen after first login — "Let's set up your account"

### Commit 6.2 — First-time Setup Wizard
- Step 1: "What's your monthly take-home?" → sets IncomeEntry for current month
- Step 2: "Confirm your monthly bills" → pre-fills from default config, user edits amounts
- Step 3: "Set your spending caps" → simple sliders for Food, Groceries, Travel etc.
- Skip option on each step — can be done later in Settings
- `onboarding_complete` flag on User table — wizard only shows once

### Commit 6.3 — Admin Panel (Basic)
- Simple admin route `/admin` — accessible only to a designated admin user
- View: list of all users, registration date, last login, expense count
- Actions: disable a user account, trigger manual backup
- Internal tooling — does not need to be polished

### Commit 6.4 — User Acceptance Testing
- Test complete flow: register → onboard → log expenses → view dashboard → export → delete account
- Test with two concurrent users — verify data isolation holds end to end
- Load test the AI parsing endpoint with 10 concurrent requests
- Fix any issues found before sharing with the first external user

---

## Sprint Summary

| Sprint | Focus | Effort | Prerequisite | Blocks sharing? |
|--------|-------|--------|--------------|-----------------|
| 1 | Auth & security | ~1 week | None | ✅ Yes |
| 2 | Data isolation | ~3 days | Sprint 1 | ✅ Yes |
| 3 | Deployment | ~2 days | Sprint 1 + 2 | ✅ Yes |
| 4 | Trust & transparency | ~2 days | Sprint 2 | No |
| 5 | Hardening | ~3 days | Sprint 3 | No |
| 6 | Onboarding | ~1 week | All above | No |

---

## Architecture Decisions

### Authentication
**Chosen approach:** JWT tokens via `python-jose` + `passlib`  
**Reason:** Self-contained, no external service dependency, works well with FastAPI's
dependency injection. Upgrade path to Auth0 or Supabase Auth is straightforward later.

### Data Isolation Strategy
**Chosen approach:** Single SQLite database with `user_id` on every table  
**Reason:** Right-sized for 5–20 users. Simple to audit, easy to migrate to PostgreSQL
later. Row-level security can be added at the SQLAlchemy layer without changing the schema.

### Hosting
**Recommended:** Railway (primary) or Render (alternative)  
**Reason:** Free/low-cost tier, automatic HTTPS, persistent volumes, environment variable
management, GitHub auto-deploy. No DevOps expertise required.

### Database for Scale
**Current:** SQLite (single file, zero config)  
**At 20+ users:** Migrate to PostgreSQL on Railway — same SQLModel code, change connection string  
**At 100+ users:** Add connection pooling via `asyncpg`

---

## Security Principles

1. **Secrets never in code** — all keys, passwords, and tokens in environment variables
2. **Every request authenticated** — no unauthenticated endpoints except `/health` and `/auth/login`
3. **Data always scoped** — every query filters by `user_id`; no global queries in production
4. **HTTPS everywhere** — HTTP only acceptable on localhost during development
5. **Least privilege** — users can only read/write their own data; admin actions require admin role
6. **Transparency** — users know what data is stored and what is sent to third parties (Anthropic API)

---

## What Users Are Told (Privacy Commitment)

> SpendSense stores your expense entries, income amounts, and budget settings.
> When you use natural language input (e.g. "zomato 500"), that text is sent to
> Anthropic's Claude API for parsing — Anthropic's privacy policy applies to that data.
> We do not store your full name, phone number, or any payment credentials.
> You can export all your data or delete your account at any time.

---

*Last updated: May 2026*  
*Owner: Debashish*
