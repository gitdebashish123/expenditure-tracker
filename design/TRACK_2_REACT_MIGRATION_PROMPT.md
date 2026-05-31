# SanchaySaathi — Track 2: React Frontend Migration Prompt

**Owner:** Debashish
**Created:** May 2026
**Status:** Ready to implement — after Sprint 6 complete
**Prerequisite:** Sprints 1–6 complete ✅, Track 0 Quick Wins ✅

---

## Migration Philosophy — Streamlit Stays Until React Is Proven

SanchaySaathi currently runs a **Streamlit** frontend (`frontend/app.py`, ~1,700 lines)
talking to a **FastAPI** backend (`backend/main.py`). The backend is complete, battle-tested,
and stays **100% unchanged** throughout this entire migration.

**Streamlit is NOT decommissioned during this migration.**
It continues to run on `:8501` alongside the React app on `:5173` (dev) / `:80` (prod)
until all of the following conditions are met:

- All T2.1–T2.10 commits implemented and individually validated
- React app tested by real users in production for a minimum of 2 weeks
- No critical regressions found vs the Streamlit feature set
- Explicit sign-off decision made by Debashish to retire `frontend/app.py`

Until that decision is made, both frontends read the same `data/expenses.db`,
call the same backend endpoints, and can be run simultaneously.

**What this migration adds:** `frontend/react/` — a new Vite+React project
**What stays untouched:** `frontend/app.py`, all of `backend/`, `data/`, `config.yaml`, `.env`

## Why React (alongside Streamlit, not instead)

- Streamlit reruns the full Python script on every interaction — perceptible lag as app grows
- Mobile experience is CSS-workaround only — not truly responsive
- Features needed (live password strength bar, bottom nav, PWA, modals) are impossible or hacky in Streamlit
- User base growing past ~10–15 people who expect a native-feeling mobile app
- Streamlit remains as the fallback and reference implementation throughout

---

## Project Layout After Migration

```
expenditure-tracker/
├── backend/              # FastAPI — UNCHANGED
│   ├── main.py           #   all REST endpoints
│   ├── models.py         #   SQLModel schema
│   ├── auth.py           #   JWT + bcrypt
│   ├── budget_rules.py   #   balance, seeding, projections
│   └── ai_parser.py      #   Claude NL parsing
├── frontend/             # React lives in frontend/react/ — app.py UNTOUCHED
│   ├── app.py            #   Streamlit — still runs on :8501 during transition
│   └── react/            #   Vite+React project
│       ├── package.json
│       ├── vite.config.ts
│       ├── tailwind.config.ts
│       ├── index.html
│       ├── public/
│       │   ├── manifest.json     # PWA manifest
│       │   └── icons/            # PWA icons (192, 512)
│       └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api/
│       │   └── client.ts     # Axios instance + interceptors
│       ├── context/
│       │   ├── AuthContext.tsx
│       │   └── ThemeContext.tsx
│       ├── hooks/
│       │   ├── useAuth.ts
│       │   ├── useExpenses.ts
│       │   ├── useMonth.ts
│       │   └── useSummary.ts
│       ├── pages/
│       │   ├── LoginPage.tsx
│       │   ├── DashboardPage.tsx  # main shell with tabs
│       │   └── AccountPage.tsx    # password + delete account
│       ├── components/
│       │   ├── layout/
│       │   │   ├── BottomNav.tsx
│       │   │   ├── Header.tsx
│       │   │   └── ProfileDropdown.tsx
│       │   ├── tabs/
│       │   │   ├── QuickAddTab.tsx
│       │   │   ├── FixedTab.tsx
│       │   │   ├── OverviewTab.tsx
│       │   │   ├── HistoryTab.tsx
│       │   │   ├── SettingsTab.tsx
│       │   │   └── AdminTab.tsx
│       │   ├── shared/
│       │   │   ├── BalanceCards.tsx
│       │   │   ├── CategoryBar.tsx
│       │   │   ├── ExpenseRow.tsx
│       │   │   ├── MonthSelector.tsx
│       │   │   ├── PasswordStrengthBar.tsx
│       │   │   ├── Toast.tsx
│       │   │   └── EmptyState.tsx
│       │   └── onboarding/
│       │       └── OnboardingWizard.tsx
│       └── utils/
│           ├── formatInr.ts      # Indian number formatting
│           ├── formatDate.ts     # relative date helpers
│           └── categories.ts     # icons + category lists
├── data/                 # SQLite DB — UNCHANGED
├── design/               # docs — this file lives here
├── scripts/              # uat_test.py — UNCHANGED
└── docker-compose.yml    # updated to serve React build
```

---

## Tech Stack

| Layer | Technology | Version | Reason |
|---|---|---|---|
| Framework | React | 18 | Component model, hooks, concurrent rendering |
| Build tool | Vite | 5 | Fast HMR, instant cold start, ES modules |
| Language | TypeScript | 5 | Type safety, better IDE support |
| Styling | Tailwind CSS | 3 | Mobile-first, dark mode built-in, no CSS files |
| Charts | Recharts | 2 | Same API as before (already used in Streamlit artifacts) |
| HTTP | Axios | 1 | Interceptors for token injection + 401 redirect |
| Routing | React Router | 6 | URL-based navigation, account page routing |
| State | React Context + useState | — | Sufficient for this app's size |
| PWA | vite-plugin-pwa | latest | One config, installable on phone home screen |
| Icons | lucide-react | latest | Consistent icon set |

---

## Design System — Matching the Streamlit UI

Preserve the existing visual identity exactly. The Streamlit app defines this palette:

```typescript
// src/utils/theme.ts
export const DARK = {
  bg:        "#0a0a0f",
  card:      "#111118",
  card2:     "#1a1a28",
  border:    "rgba(255,255,255,0.07)",
  text:      "#ffffff",
  sub:       "rgba(255,255,255,0.4)",
  muted:     "rgba(255,255,255,0.25)",
  accent:    "#6366f1",          // indigo — primary CTA colour
  accent2:   "#8b5cf6",          // purple — gradient endpoint
  success:   "#34d399",          // green — positive balance
  danger:    "#ef4444",          // red — over budget / negative
  warning:   "#f59e0b",          // amber — approaching limit
  income:    "#f87171",          // expense amount colour
};

export const LIGHT = {
  bg:        "#f5f5f7",
  card:      "#ffffff",
  card2:     "#f0f0f5",
  border:    "rgba(0,0,0,0.08)",
  text:      "#1a1a2e",
  sub:       "rgba(0,0,0,0.5)",
  muted:     "rgba(0,0,0,0.3)",
  accent:    "#6366f1",
  accent2:   "#8b5cf6",
  success:   "#34d399",
  danger:    "#ef4444",
  warning:   "#f59e0b",
  income:    "#f87171",
};
```

Typography (match Google Fonts imports from Streamlit):
```css
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

/* Headings, amounts, tab labels, metric values */
font-family: 'Syne', sans-serif;

/* Body copy, labels, captions */
font-family: 'DM Sans', sans-serif;
```

Tailwind config additions:
```typescript
// tailwind.config.ts
fontFamily: {
  syne: ['Syne', 'sans-serif'],
  sans: ['DM Sans', 'sans-serif'],
},
```

---

## API Reference — All Endpoints (FastAPI Backend)

Base URL: `http://localhost:8000` (local) / Railway URL (production)
Authentication: `Authorization: Bearer <jwt_token>` header on all protected routes

### Auth
```
POST /auth/register          { email, password } → 201 UserResponse
POST /auth/login             { email, password } → TokenResponse { access_token }
GET  /auth/me                → UserResponse
POST /auth/complete-onboarding → { message }
PUT  /auth/password          { current_password, new_password } → { message }
DELETE /auth/account         { confirmation: "DELETE" } → { message }
```

### Expenses
```
POST /expenses/parse         { text, date_override? } → { saved[], warnings[], balance }
POST /expenses/manual        { vendor, amount, category, note?, date? } → Expense
GET  /expenses/{month_key}   → Expense[]
PATCH /expenses/{id}         { vendor?, amount?, category?, note? } → Expense
DELETE /expenses/{id}        → { deleted: id }
POST /expenses/bulk-delete   { ids: number[] } → { count }
```

### Fixed Expenses
```
GET  /fixed/{month_key}               → FixedExpense[]   (is_fixed=true expenses)
PATCH /fixed/{id}/toggle              → FixedExpense     (toggle paid status)
GET  /fixed/due-reminders/{month_key} → DueReminder[]
```

### Fixed Templates
```
GET  /fixed-templates         → FixedExpenseTemplate[]
POST /fixed-templates         { name, category, amount, template_type: "fixed"|"pool" }
PUT  /fixed-templates/{id}    { name?, amount?, due_day?, is_active? }
DELETE /fixed-templates/{id}  → { deleted: id }
```

### Essential Pools
```
GET  /pools/{month_key}                       → Pool[] (with entries, paid_total, unpaid_total)
POST /pools/{pool_id}/entries/{month_key}     { label, amount, note? } → PoolEntry
PATCH /pools/entries/{entry_id}               { label?, amount?, paid?, note? }
PATCH /pools/entries/{entry_id}/toggle        → PoolEntry
DELETE /pools/entries/{entry_id}              → { deleted: id }
```

### Summary & Insights
```
GET /summary/{month_key}                     → { balance, categories, warnings, fixed_progress }
GET /months                                  → string[]  (all months with data)
GET /income/{month_key}                      → IncomeEntry
GET /income/check/{month_key}                → { is_set: bool }
POST /income                                 { source, amount, note?, month_key }
GET /budgets                                 → BudgetLimit[]
PUT /budget                                  { category, limit_amount }
GET /insights/projection/{month_key}         → ProjectionItem[]
GET /insights/top-spends/{month_key}         → TopSpend[]
GET /insights/mom/{month_key}                → { months: string[], categories: { [cat]: { [month]: number } } }
```

### Expense Templates (Quick-add Favourites)
```
GET  /expense-templates                      → ExpenseTemplate[]
POST /expense-templates                      { name, vendor, category, amount }
PUT  /expense-templates/{id}                 { name?, vendor?, category?, amount? }
DELETE /expense-templates/{id}               → { deleted: id }
POST /expense-templates/{id}/log             → { saved: Expense, balance }
```

### Export
```
GET /export/csv/{month_key}   → text/csv
GET /export/csv/all           → text/csv
```

### Admin (is_admin=true only)
```
GET  /admin/stats                            → { total_users, active_users, total_expenses }
GET  /admin/users                            → AdminUser[]
PATCH /admin/users/{id}/toggle-active        → { id, email, is_active }
```

### Health
```
GET /health  → { status: "ok" }
```

---

## Data Models (TypeScript)

```typescript
// src/types/index.ts

export interface User {
  id: number;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  last_login: string | null;
  onboarding_complete: boolean;
}

export interface Expense {
  id: number;
  date: string;           // "YYYY-MM-DD"
  vendor: string;
  amount: number;
  category: string;
  note: string | null;
  is_fixed: boolean;
  paid: boolean;
  month_key: string;
  fixed_template_id: number | null;
}

export interface FixedExpense extends Expense {
  is_fixed: true;
}

export interface FixedExpenseTemplate {
  id: number;
  name: string;
  category: string;
  amount: number;
  is_active: boolean;
  sort_order: number;
  due_day: number | null;
  template_type: "fixed" | "pool";
  created_at: string;
}

export interface PoolEntry {
  id: number;
  pool_template_id: number;
  month_key: string;
  label: string;
  amount: number;
  paid: boolean;
  paid_date: string | null;
  note: string | null;
}

export interface Pool {
  id: number;
  name: string;
  category: string;
  entries: PoolEntry[];
  paid_total: number;
  unpaid_total: number;
  entry_count: number;
}

export interface Summary {
  balance: {
    remaining: number;
    total_income: number;
    fixed_paid_total: number;
    fixed_unpaid_total: number;
    variable_total: number;
  };
  categories: Array<{ category: string; spent: number }>;
  warnings: Array<{ level: "warning" | "danger"; message: string }>;
  fixed_progress: { paid: number; total: number };
}

export interface BudgetLimit {
  id: number;
  category: string;
  limit_amount: number;
}

export interface IncomeEntry {
  id: number;
  source: string;
  amount: number;
  month_key: string;
  note: string | null;
}

export interface ExpenseTemplate {
  id: number;
  name: string;
  vendor: string;
  category: string;
  amount: number;
  use_count: number;
}

export interface ProjectionItem {
  category: string;
  spent: number;
  limit: number;
  projected: number;
  pct_spent: number;
  pct_projected: number;
  status: "safe" | "warning" | "danger" | "over";
  days_left: number;
  daily_rate: number;
}
```

---

## Streamlit Reference — Feature by Feature

This section maps every Streamlit feature to its React equivalent so nothing is
missed during migration.

### Authentication Flow

**Streamlit (current):**
```python
# frontend/app.py — show_login_page()
# Two forms: login_form and register_form
# register_form: reg_email + reg_password (outside form for live strength bar)
#               + reg_confirm + submit (inside form)
# Login success: stores token, email, is_admin, onboarding_complete in st.session_state
# Token persists in session state (lost on browser refresh)
```

**React target:**
```typescript
// Token stored in localStorage — survives refresh
// AuthContext provides: user, token, login(), logout(), register()
// ProtectedRoute wrapper redirects to /login if no token
// On 401 response: Axios interceptor clears token + redirects to /login

// Password strength bar: live on every keystroke (works properly in React)
// 4 checks: length>=8, uppercase, digit, special char
// Colour: red → orange → yellow → green, label: Weak/Fair/Good/Strong
```

### Onboarding Wizard

**Streamlit (current):**
```python
# show_onboarding_wizard() — called when onboarding_complete=False
# 3 steps: Income → Bills → Spending Caps
# Progress bar (3 coloured segments), Skip per step, Skip All button
# Step 2 bills form: name, category, fixed/variable radio, amount
# "No, it varies" shows caption: "You'll add the actual amount once it's paid."
# POST /auth/complete-onboarding on finish or skip all
```

**React target:**
```typescript
// OnboardingWizard.tsx modal/overlay — shown when user.onboarding_complete=false
// Animated step transitions
// Step 2: same rich form — name, category, fixed/variable radio, amount
//         live caption when "No, it varies" selected
//         bills added show in a card list above the form (live, after each Add)
// Complete → set onboarding_complete=true in AuthContext, dismiss overlay
```

### Header

**Streamlit (current):**
```python
# col_title (3), col_theme (0.5), col_logout (0.7), col_month (1)
# app-title: "💸 SpendSense", subtitle: "Personal Expenditure Tracker"
# Theme toggle: 🌙/☀️ button
# Profile popover (st.popover): user initial, Change Password, Privacy Notice, Sign Out
# Month selector: selectbox showing "May 2026" format
```

**React target:**
```typescript
// Header.tsx — sticky top bar
// Left: SpendSense logo/wordmark
// Centre: MonthSelector (dropdown showing "May 2026")
// Right: ThemeToggle + ProfileDropdown
// ProfileDropdown: avatar circle (user initial), email, Change Password link,
//                 Privacy Notice link, Sign Out button
// On mobile: month selector moves below header (or in bottom sheet)
```

### Tab Structure

**Streamlit (current):**
```
⚡ Quick Add | 📌 Fixed | 📊 Dashboard | 📋 Expenses | ⚙️ Settings | [🛡️ Admin — admin only]
```

**React target (restructured for mobile — see Track 1 IA notes):**
```
Bottom nav (mobile) / Top tabs (desktop):
💸 Today    →  Quick Add + Today's entries
📊 Overview →  Dashboard (balance cards, charts, MoM)
📋 History  →  Full expense list (CRUD)
⚙️ Settings →  Bills, Budgets, Shortcuts, Fixed tab merged in
[🛡️ Admin — admin only, only visible when is_admin=true]
```

Account page: `/account` route — Change Password + Delete Account (separate page,
accessed from ProfileDropdown)

### Quick Add Tab

**Streamlit (current):**
```python
# NL text input + date picker (st.form "quick_add", clear_on_submit=True)
# POST /expenses/parse → shows saved expense cards + balance update
# Spinner during AI parsing
# Favourites chips (3 per row) — tap to log instantly via POST /expense-templates/{id}/log
# Today's Entries list (last 10, non-fixed, today only) with delete button
```

**React target:**
```typescript
// Large text input + date picker row
// "Add Expenses" button — shows loading spinner during POST /expenses/parse
// After save: animated cards for each saved expense + updated balance
// Favourites: horizontal scroll chips with icon + name + amount
// Today's entries: swipe-to-delete on mobile (touch events), delete button on desktop
// Real keyboard opens when input focused on mobile
```

### Fixed Tab

**Streamlit (current):**
```python
# Due reminders (current month only) — due-banner div
# Fixed expenses: grouped by category, tick/untick paid toggle
# Progress bar: paid/total count + amounts
# Essential Pools section: pool header, entry list, Add Payment form per pool
# Empty state: "No bills set up yet..."
```

**React target:**
```typescript
// Same structure — due reminders at top
// Checkbox rows with strikethrough when paid
// Category group headers with totals
# Pool section: expandable per pool, add-payment inline form
// Optimistic UI: tick toggles immediately, syncs in background
```

### Dashboard / Overview Tab

**Streamlit (current):**
```python
# Balance breakdown gauge bar (fixed paid | pending | variable | remaining)
# Budget Health: projection cards per category (status: safe/warning/danger/over)
# Top Spends: ranked list (#1–#5 with amounts)
# Month-over-Month: HTML table with trend arrows
```

**React target:**
```typescript
// Same sections with proper React chart components
// Balance breakdown: horizontal stacked bar using Recharts
// Budget health: progress bar cards (animated fill)
// Top Spends: ranked list with medal colours
// MoM table: responsive HTML table, sortable
// BONUS: add donut chart for category split (not in Streamlit)
```

### History / Expenses Tab

**Streamlit (current):**
```python
# Show/hide fixed checkbox, bulk select checkbox
# Grouped by date (descending), daily totals
# Normal row: icon | vendor+note | amount | edit | delete
# Edit mode inline: vendor, category, amount, note fields
# Bulk delete: checkboxes + "Delete N selected" button
```

**React target:**
```typescript
// Date-grouped list with sticky date headers
// Edit inline or slide-in panel
// Swipe-to-delete on mobile
// Bulk select: long-press or top checkbox
// Filter/search bar (bonus — not in Streamlit)
```

### Settings Tab

**Streamlit (current):**
```python
# Section 1: My Account (top) — last login, Change Password expander, Danger Zone
# Section 2: My Take-home — income form
# Section 3: Monthly Bills — fixed templates (grouped by cat), pool templates, Add Bill form
# Section 4: Spending Caps — budget limits form (2-col grid)
# Section 5: Saved Shortcuts — quick-add favourites CRUD
# Section 6: My Data — CSV download buttons (month + all)
```

**React target:**
```typescript
// Same sections, cleaner accordion/card layout
// My Account moved to separate /account route
// "Add a new bill" form: name, category, fixed/variable radio, amount
//   — "No, it varies" shows "You'll add the actual amount once it's paid." caption
// Budget caps: inline number inputs with colour-coded spent context
// CSV export: download buttons with loading state
```

### Admin Tab

**Streamlit (current):**
```python
# Shown only when user_is_admin=True (6th tab)
# 3 metric cards: Total Users, Active Users, Total Expenses
# User list: email (with crown/lock/person icon), status dot, last login,
#            expense count, Enable/Disable button (hidden for admin row)
# 🆕 onboarding badge shown for users who haven't completed wizard
```

**React target:**
```typescript
// Same layout — only rendered when user.is_admin=true
// User table with status badges
// Disable/Enable toggle with confirmation dialog
```

### Category Icons & Lists

**Streamlit (current):**
```python
CATEGORY_ICONS = {
    "Food": "🍔", "Travel": "🚗", "Groceries": "🛒", "Shopping": "🛍️",
    "Medical": "💊", "Entertainment": "🎬", "Gifts": "🎁", "Course": "📚",
    "Miscellaneous": "📦", "Housing": "🏠", "Savings": "💰", "EMI": "💳",
    "Investments": "📈", "Utilities": "⚡", "Insurance": "🛡️", "Household": "🏡"
}
FIXED_CATEGORIES = ["Housing", "EMI", "Savings", "Investments", "Insurance", "Utilities", "Household"]
VAR_CATEGORIES   = ["Food", "Travel", "Groceries", "Shopping", "Medical",
                    "Entertainment", "Gifts", "Course", "Miscellaneous"]
```

**React target:**
```typescript
// src/utils/categories.ts
export const CATEGORY_ICONS: Record<string, string> = {
  Food: "🍔", Travel: "🚗", Groceries: "🛒", Shopping: "🛍️",
  Medical: "💊", Entertainment: "🎬", Gifts: "🎁", Course: "📚",
  Miscellaneous: "📦", Housing: "🏠", Savings: "💰", EMI: "💳",
  Investments: "📈", Utilities: "⚡", Insurance: "🛡️", Household: "🏡",
};
export const FIXED_CATEGORIES = ["Housing","EMI","Savings","Investments","Insurance","Utilities","Household"];
export const VAR_CATEGORIES   = ["Food","Travel","Groceries","Shopping","Medical","Entertainment","Gifts","Course","Miscellaneous"];
```

### Indian Number Formatting

**Streamlit (current):**
```python
def fmt_inr(amount):
    # Indian lakh format: 15,00,000 not 1,500,000
    # last 3 digits, then every 2 digits
    ...
```

**React target:**
```typescript
// src/utils/formatInr.ts
export function fmtInr(amount: number): string {
  if (amount == null) return "₹0";
  const neg = amount < 0;
  const a = Math.abs(Math.round(amount));
  const s = String(a);
  let fmt: string;
  if (s.length <= 3) {
    fmt = s;
  } else {
    const last3 = s.slice(-3);
    let rest = s.slice(0, -3);
    const parts: string[] = [];
    while (rest.length > 2) {
      parts.unshift(rest.slice(-2));
      rest = rest.slice(0, -2);
    }
    if (rest) parts.unshift(rest);
    fmt = parts.join(",") + "," + last3;
  }
  return (neg ? "-₹" : "₹") + fmt;
}
```

### Relative Date Formatting

**Streamlit (current):**
```python
def fmt_date(date_str):
    # "Today", "Yesterday", "28 May" (current year), "28 May 2025" (other year)
```

**React target:**
```typescript
// src/utils/formatDate.ts
export function fmtDate(dateStr: string): string {
  const d = new Date(dateStr);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  if (d.toDateString() === today.toDateString()) return "Today";
  if (d.toDateString() === yesterday.toDateString()) return "Yesterday";
  const opts: Intl.DateTimeFormatOptions = d.getFullYear() === today.getFullYear()
    ? { day: "numeric", month: "short" }
    : { day: "numeric", month: "short", year: "numeric" };
  return d.toLocaleDateString("en-IN", opts);
}
```

---

## Axios Client Setup

```typescript
// src/api/client.ts
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export const api = axios.create({ baseURL: API_BASE });

// Inject token on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// On 401: clear token + redirect to login
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);
```

---

## Auth Context

```typescript
// src/context/AuthContext.tsx
interface AuthContextValue {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

// On mount: if token in localStorage, GET /auth/me to restore user
// login(): POST /auth/login → store token → GET /auth/me → set user
// logout(): clear localStorage, set user=null, redirect to /login
// register(): POST /auth/register → redirect to /login with success message
```

---

## PWA Configuration

```typescript
// vite.config.ts
import { VitePWA } from "vite-plugin-pwa";

VitePWA({
  registerType: "autoUpdate",
  manifest: {
    name: "SpendSense",
    short_name: "SpendSense",
    description: "Personal salary & expense tracker",
    theme_color: "#0a0a0f",
    background_color: "#0a0a0f",
    display: "standalone",
    orientation: "portrait",
    start_url: "/",
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
  },
  workbox: {
    globPatterns: ["**/*.{js,css,html,ico,png,svg}"],
    runtimeCaching: [
      {
        // Cache API responses for offline read
        urlPattern: /^https?:\/\/.*\/summary\/.*/,
        handler: "NetworkFirst",
        options: { cacheName: "api-summary" },
      },
    ],
  },
});
```

---

## Docker — Updated Frontend Service

```dockerfile
# Dockerfile.frontend (replace Streamlit container with React Nginx serve)
FROM node:20-alpine AS builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx/react.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

```nginx
# nginx/react.conf
server {
  listen 80;
  root /usr/share/nginx/html;
  index index.html;

  # React Router — serve index.html for all routes
  location / {
    try_files $uri $uri/ /index.html;
  }

  # Proxy API calls to FastAPI
  location /api/ {
    proxy_pass http://backend:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }
}
```

---

## Railway Deployment

The React build produces static files. On Railway:
- Frontend service: build command `cd frontend && npm run build`, serve with
  `npx serve dist` or switch to the Nginx Docker image
- Backend service: unchanged — same `uv run uvicorn backend.main:app` start command
- Set `VITE_API_BASE=https://your-backend.up.railway.app` as Railway env var for frontend

---

## Implementation Order (Commits)

### Commit T2.1 — Project Scaffold
- `cd frontend && npm create vite@latest . -- --template react-ts`
- Install: `tailwindcss`, `axios`, `react-router-dom`, `recharts`, `lucide-react`,
  `vite-plugin-pwa`
- Configure Tailwind with Syne + DM Sans font families and dark mode
- Set up `api/client.ts` with Axios interceptors
- Set up `AuthContext.tsx` — login, register, logout, token persistence
- `LoginPage.tsx` with live password strength bar (properly reactive — no Streamlit limitation)
- `ProtectedRoute.tsx` wrapper
- Verify: register, login, `/auth/me` call works, 401 redirects to login

### Commit T2.2 — Shell, Navigation & Onboarding
- `DashboardPage.tsx` shell with tab routing
- `Header.tsx` — logo, month selector, theme toggle, profile dropdown
- `BottomNav.tsx` — 4-tab bottom navigation (mobile), tab switching (desktop)
- `OnboardingWizard.tsx` — 3-step wizard, shown when `onboarding_complete=false`
  - Step 1: income form
  - Step 2: bill form (name, category, fixed/variable radio, amount, live bill list)
  - Step 3: spending caps
  - Skip All button
- `MonthSelector.tsx` — global month state via Context or URL param
- Verify: wizard shows for new user, completes, disappears on next login

### Commit T2.3 — Quick Add Tab
- `QuickAddTab.tsx`
- NL input form → POST /expenses/parse → animated expense cards
- Favourites chips (horizontal scroll on mobile)
- Today's entries list with swipe-to-delete (Hammer.js or native touch events)
- Verify: parse + save, favourite log, delete

### Commit T2.4 — Fixed Tab
- `FixedTab.tsx`
- Due reminders banner
- Fixed expense checklist (grouped by category, paid toggle with optimistic update)
- Progress bar
- Essential Pools section with per-pool Add Payment form
- Empty state
- Verify: toggle paid, add pool payment, delete pool entry

### Commit T2.5 — Overview / Dashboard Tab
- `OverviewTab.tsx`
- Balance breakdown stacked bar (Recharts)
- Budget health projection cards
- Top Spends ranked list
- Month-over-Month responsive table
- Donut chart for category split (bonus)
- Verify: all data renders correctly for month with data

### Commit T2.6 — History Tab
- `HistoryTab.tsx`
- Date-grouped list, daily totals
- Inline edit form
- Delete + bulk select
- Verify: edit, delete, bulk delete

### Commit T2.7 — Settings Tab
- `SettingsTab.tsx`
- Income form
- Monthly Bills: fixed template CRUD (grouped by category), pool template list, Add Bill form
- Spending Caps: inline budget edit with spent context
- Saved Shortcuts: favourite template CRUD
- CSV export with loading state
- Verify: save income, add bill, update cap, export CSV

### Commit T2.8 — Account Page & Admin Tab
- `AccountPage.tsx` at `/account` route
  - Change Password form (with live password strength bar)
  - Delete Account danger zone
- `AdminTab.tsx` (only rendered when `user.is_admin=true`)
  - Stats cards
  - User list with Enable/Disable
- Verify: password change, admin tab visibility, disable/enable user

### Commit T2.9 — PWA + Polish
- `vite-plugin-pwa` config — manifest, icons, service worker
- Add to iPhone home screen — verify standalone mode, theme colour
- Dark/light theme persistence (localStorage)
- Toast notifications (replace Streamlit's `st.toast`)
- Loading skeletons for initial data fetch
- Error boundaries
- Verify: installable, offline cached reads work

### Commit T2.10 — Docker + Railway + UAT
- Update `Dockerfile.frontend` to multi-stage Node → Nginx
- Update `docker-compose.yml` frontend service
- Update `nginx/` config for React Router + API proxy
- Update `scripts/uat_test.py` — all tests still pass against same backend
- Verify: `docker compose up` serves React, all UAT tests pass

---

## What Streamlit Had That React Does Better

| Feature | Streamlit Limitation | React Solution |
|---|---|---|
| Password strength bar | Only updates after form submit (form batches values) | Updates on every keystroke — fully live |
| Onboarding wizard | Page reruns on each step — flicker | Smooth animated step transitions, no full reload |
| Swipe to delete | JS injection workaround, fragile | Native touch events, Hammer.js, clean |
| Bottom navigation | Not natively possible | BottomNav component, 44px tap targets |
| PWA / installable | Not possible | One vite-plugin-pwa config line |
| Modal dialogs | Not natively possible | React Portal modals |
| Profile dropdown | `st.popover()` approximation | Native dropdown component |
| Optimistic UI (tick paid instantly) | Full page rerun — visible lag | Update local state immediately, sync in background |
| Charts | HTML table / custom CSS divs | Recharts — proper SVG charts, animations |
| URL-based routing | Not possible | React Router v6, shareable URLs |
| Dark/light persistence | Session state lost on refresh | localStorage |

---

## What NOT to Change (Ever, During This Migration)

- `frontend/app.py` — **Streamlit app stays running throughout.** Do not modify, move, or delete.
  Run it any time with `uv run streamlit run frontend/app.py` to verify parity with React.
- `backend/` — zero changes except adding React’s origin to CORS `allow_origins` (additive only)
- `data/expenses.db` — same SQLite database, shared between both frontends
- `config.yaml` — same categories and settings
- `scripts/uat_test.py` — all 10 test groups continue to pass unchanged
- `railway.toml` — backend deploy config unchanged
- `.env` / `.env.example` — backend secrets unchanged

---

## Verification Checklist (Per Commit)

```bash
# Before every commit — confirm Streamlit still runs
uv run streamlit run frontend/app.py --server.port 8501
# → http://localhost:8501 loads and all features work ✓

# T2.1 — Auth
curl http://localhost:5173  # React app loads
curl http://localhost:8000/health  # Backend still healthy
# → Both :8501 (Streamlit) and :5173 (React) serve their login pages simultaneously ✓

# T2.2 — Navigation
# New user login → wizard appears → completes → main app
# Existing user → no wizard
# Admin user → Admin tab visible
# Streamlit: same user logs in at :8501 → same data visible ✓

# T2.3–T2.8 — After each tab commit
# → Log an expense in React → it appears in Streamlit History tab ✓
# → Toggle a bill paid in Streamlit → it shows paid in React Fixed tab ✓
# (Both frontends share the same DB — any write in one is visible in the other)

# T2.9 — PWA
# Open on iPhone Safari → Add to Home Screen → opens standalone
# Turn off WiFi → last-loaded pages still readable (cached)
# Streamlit still runs locally – no impact ✓

# T2.10 — Full stack
uv run python3 scripts/uat_test.py  # ALL TESTS PASSED
docker compose up                    # both services start, React served on :80
uv run streamlit run frontend/app.py # Streamlit still runs alongside ✓
```

---

## Common Pitfalls

| Issue | Cause | Fix |
|---|---|---|
| CORS error from React to FastAPI | FastAPI CORS origins | Add `http://localhost:5173` to `allow_origins` in `backend/main.py` |
| 401 loop on refresh | Token not in localStorage | Store in `localStorage.setItem("token", ...)` on login |
| React Router 404 on refresh | Nginx not rewriting to `index.html` | Add `try_files $uri $uri/ /index.html` in nginx config |
| Indian number format wrong | Used `toLocaleString()` | Use custom `fmtInr()` — browser locale unreliable |
| Wizard shows for existing users | `onboarding_complete` defaults | On first load, check `user.onboarding_complete` from `/auth/me` |
| Admin tab visible to all | Rendering tab unconditionally | `{user?.is_admin && <AdminTab />}` |
| Token not sent to backend | Axios instance not used | Always use `import { api } from "@/api/client"`, not raw `fetch` |
| PWA not installing | Missing manifest fields | Ensure `display: "standalone"`, icons at 192 and 512 |

---

*Last updated: May 2026*
*Owner: Debashish*
*Status: Ready to implement — Sprint 6 complete, React migration next*
*Reference: `todo/01-frontend-mobile-whatsapp-enhancements.md`, `design/TECH_STACK_ANALYSIS.md`*
