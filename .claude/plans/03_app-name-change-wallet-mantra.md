# Plan: App Rename — SanchaySaathi → Wallet Mantra

## Context

"SanchaySaathi" is phonetically close to **Sanchar Saathi**, a high-profile Indian
government telecom-safety app (DoT / TRAI). To eliminate brand confusion and potential
trademark exposure, the app is being renamed to:

> **Wallet Mantra — Beyond expense tracking**

This is a purely cosmetic change — no DB schema, API contracts, routes, or JWT claims
change. The Docker volume `spendsense_data` is deliberately **not** renamed (data-loss
risk; noted in spec 03).

---

## New Name Tokens

| Purpose | Value |
|---|---|
| Display heading | `Wallet Mantra` |
| Tagline | `Beyond expense tracking` |
| PWA `name` | `Wallet Mantra` |
| PWA `short_name` | `WalletMantra` |
| npm / pyproject slug | `wallet-mantra` |
| CSV filename prefix | `walletMantra_` |
| FastAPI title | `Wallet Mantra API` |
| Logo emoji (keep) | 💸 |

---

## Changes

### 1. React Frontend — primary active UI

**`frontend/react/index.html`**
- `<title>SanchaySaathi</title>` → `<title>Wallet Mantra</title>`
- `content="SanchaySaathi"` (apple meta tag) → `content="Wallet Mantra"`

**`frontend/react/vite.config.ts`**
- Comment: `// PWA — makes SanchaySaathi installable` → `// PWA — makes Wallet Mantra installable`
- `name: "SanchaySaathi"` → `name: "Wallet Mantra"`
- `short_name: "SanchaySaathi"` → `short_name: "WalletMantra"`
- `description: "Your companion for smart daily budgeting"` → `description: "Beyond expense tracking"`

**`frontend/react/package.json`**
- `"name": "sanchaySaathi"` → `"name": "wallet-mantra"`

**`frontend/react/src/components/layout/Header.tsx`**
- Heading: `💸 SanchaySaathi` → `💸 Wallet Mantra`
- Tagline p-tag: `"Your companion for smart daily budgeting"` → `"Beyond expense tracking"`
- Comment line 12: `SanchaySaathi logo + tagline` → `Wallet Mantra logo + tagline`

**`frontend/react/src/pages/LoginPage.tsx`**
- `<h1>SanchaySaathi</h1>` → `<h1>Wallet Mantra</h1>`
- Tagline p-tag (line 101–103): `"Your companion for smart daily budgeting"` → `"Beyond expense tracking"`

**`frontend/react/src/components/onboarding/OnboardingWizard.tsx`**
- `Welcome to SanchaySaathi!` → `Welcome to Wallet Mantra!`

**`frontend/react/src/components/settings/ExportSection.tsx`**
- CSV filename (line 67): `` `sanchaySaathi_${selMonth}.csv` `` → `` `walletMantra_${selMonth}.csv` ``
- CSV filename (line 87): `` `sanchaySaathi_all_${today}.csv` `` → `` `walletMantra_all_${today}.csv` ``
- Comment (line 17): update `SanchaySaathi (not SpendSense)` → `Wallet Mantra`

### 2. Backend

**`backend/main.py`**
- Line 54: `title="SpendSense API"` → `title="Wallet Mantra API"`
- Line 189: `"app": "SpendSense"` → `"app": "Wallet Mantra"`
- Line 1248: `filename = f"spendsense_all_{today}.csv"` → `filename = f"walletMantra_all_{today}.csv"`
- Line 1296: `filename = f"spendsense_{month_key}.csv"` → `filename = f"walletMantra_{month_key}.csv"`

### 3. Config & Root Files

**`CLAUDE.md`** (root)
- Heading / first paragraph: `SanchaySaathi (previously SpendSense)` → `Wallet Mantra`
- Line 113 Docker volume mention: leave `spendsense_data` as-is (not renamed — data loss risk)

**`.claude/CLAUDE.md`**
- `# SpendSense — Project Context for Claude` → `# Wallet Mantra — Project Context for Claude`

**`pyproject.toml`**
- `name = "spendsense"` → `name = "wallet-mantra"`
- `spendsense-api = "backend.main:app"` → `wallet-mantra-api = "backend.main:app"`

**`railway.toml`**
- Top comment: `# ── SanchaySaathi — Railway…` → `# ── Wallet Mantra — Railway…`
- `name = "sanchaySaathi"` → `name = "walletMantra"`

**`docker-compose.yml`**
- Top comment only: `# ── SanchaySaathi — Docker Compose` → `# ── Wallet Mantra — Docker Compose`
- **Do NOT rename** `spendsense_data` volume — data loss risk (spec 03 exclusion)

### 4. Legacy Frontend (low priority — not active UI)

**`frontend/app.py`** (Streamlit, kept but dormant)
- `page_title="SpendSense"` → `"Wallet Mantra"`
- All `SpendSense` display strings → `Wallet Mantra`
- CSV `file_name` prefixes: `spendsense_` → `walletMantra_`

---

## Out of Scope

- `/design/` folder docs — internal only, no user-facing impact
- Test / script files (`tests/`, `scripts/`) — functional code, not display
- Docker volume name `spendsense_data` — not renamed (data loss)
- App icon / logo redesign — separate task
- Domain / DNS changes — already handled externally

---

## Verification

After implementation, run:

```bash
# 1. Zero old-name hits in active source files
grep -r -i "sanchay\|spendsense" \
  frontend/react/src/ backend/main.py \
  frontend/react/index.html frontend/react/vite.config.ts \
  CLAUDE.md .claude/CLAUDE.md pyproject.toml railway.toml

# 2. TypeScript build passes
cd frontend/react && npm run build

# 3. Start dev server and verify in browser
npm run dev  # → http://localhost:5173
# Check: browser tab shows "Wallet Mantra"
# Check: login page shows "💸 Wallet Mantra" + "Beyond expense tracking"
# Check: dashboard header shows "💸 Wallet Mantra"
# Check: onboarding first screen shows "Welcome to Wallet Mantra!"
# Check: CSV export download is named walletMantra_YYYY-MM.csv

# 4. Backend /docs title
# → http://localhost:8000/docs should show "Wallet Mantra API"
# → http://localhost:8000/health should return "app": "Wallet Mantra"
```
