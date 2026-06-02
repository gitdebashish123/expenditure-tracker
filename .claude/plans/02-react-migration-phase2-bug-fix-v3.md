# Implementation Plan: React Migration Phase 2 — Bug Fixes & UX
**Spec**: `.claude/specs/react-migration-phase2-bug-fix.md`  
**Date**: 2026-06-02  
**Branch**: `feature/sprint7-react-migration-phase3`

---

## Overview

8 items total — 2 require backend + frontend, 6 are frontend-only.  
Items are ordered from smallest blast-radius to largest. Tackle in sequence to keep each PR reviewable on its own.

---

## Item 1 — Forgot Password stub on Login Page
**Scope**: Frontend-only  
**File**: `frontend/react/src/pages/LoginPage.tsx`

**What to do**:
After the `<button>` that toggles login/register mode (line 189), insert a second small text link labelled "Forgot password?" that is only visible when `mode === "login"`.

Clicking it sets a new local state flag `showForgotMsg = true`, which renders a dismissible info banner (same style as the existing `success` banner) with the message:
> "To reset your password, contact your administrator."

No new page, no API call, no routing. The banner dismisses when the user clicks the "×" or switches to register mode (`switchMode` already resets error/success — extend it to also reset `showForgotMsg`).

**Exact insertion point**: Between line 196 (`</button>`) and line 199 (Privacy notice `<p>`).

---

## Item 2 — Dividend / Bonus adds to main income
**Scope**: Backend + Frontend  
**Files**:
- `backend/main.py` — `POST /income` endpoint (line ~1000)
- `backend/models.py` — `IncomeEntry` model
- `frontend/react/src/components/settings/IncomeSection.tsx`
- `frontend/react/src/types/index.ts`

**Root cause**: `POST /income` upserts by `(month_key, user_id)` — a second income entry (dividend, bonus) for the same month overwrites the first instead of adding to it. `get_balance_summary()` already sums all `IncomeEntry` rows, so the backend aggregation is correct.

**What to do**:

### Backend
1. Change the upsert logic in `POST /income` to match on `(month_key, user_id, source)` instead of just `(month_key, user_id)`. This allows multiple sources (Salary, Dividend, Bonus) per month.
2. Add `GET /income/{month_key}/all` that returns all income entries for the month as a list (the existing `GET /income/{month_key}` returns only the first entry — keep it for backwards compatibility, add the new list endpoint alongside it).
3. No change needed to `get_balance_summary()` — it already sums all rows.

### Frontend (`IncomeSection.tsx`)
1. Fetch from `GET /income/{month_key}/all` to show all income sources.
2. Render a list of existing entries with their source name and amount.
3. An "Add income source" form (source label + amount) posts to the existing `POST /income` endpoint.
4. A delete button per entry calls `DELETE /income/{id}` (add this endpoint if it doesn't exist yet — simple user-scoped delete by id).

### Types (`types/index.ts`)
`IncomeEntry` already has `source`, `amount`, `month_key`, `note` fields — no change needed.

---

## Item 3 — Pie Chart Tooltip contrast fix
**Scope**: Frontend-only  
**File**: `frontend/react/src/components/shared/SpendDonut.tsx`

**Root cause**: Recharts `<Tooltip>` renders the item value line using the series fill colour by default (which may be dark against a dark background). The `contentStyle` sets the container background to `#1a1a28` and `color: "white"`, but the item value text inherits the slice's `fill` colour unless explicitly overridden with `itemStyle`.

**What to do** (lines 48–58):
Add `itemStyle={{ color: 'white' }}` to the `<Tooltip>` props alongside the existing `labelStyle`.

```tsx
<Tooltip
  formatter={(v: number) => [fmtInr(v), "Spent"]}
  contentStyle={{
    background: "#1a1a28",
    border: "1px solid rgba(255,255,255,0.1)",
    borderRadius: 12,
    color: "white",
    fontSize: 12,
  }}
  labelStyle={{ color: "white" }}
  itemStyle={{ color: "white" }}   // ← add this line
/>
```

---

## Item 4 — Monthly Breakdown — 4 labeled rows
**Scope**: Frontend-only (backend already returns all required fields)  
**File**: `frontend/react/src/components/shared/BalanceBreakdown.tsx`

**Current state**: Shows a stacked proportional bar with a legend. The bar is visually useful but the spec now calls for four explicit labeled rows showing exact amounts.

**What to do**: Replace the stacked-bar section with a 2×2 grid of stat rows. Keep the component's outer card wrapper and the "Monthly Breakdown" heading. Remove the `segments` array and the bar `<div>`.

New layout — four rows in order:
1. **Fixed Paid** — `balance.fixed_paid_total` — accent colour: `#34d399` (green)
2. **Fixed Remaining** — `balance.fixed_unpaid_total` — colour: `#f59e0b` (amber)
3. **Variable Already Paid** — `balance.variable_total` — colour: `#f87171` (red)
4. **Total Remaining** — `balance.remaining` — colour: green if ≥ 0, red if < 0

Each row: label on left (`text-xs`, `var(--text-sub)`), bold ₹ amount on right (`font-syne font-semibold`).

The `Balance` interface and props are unchanged — all four values exist on `balance` today.

---

## Item 5 — Top Spends capped at 5
**Scope**: Frontend-only  
**File**: `frontend/react/src/components/tabs/OverviewTab.tsx`

**Root cause**: Line 133 requests `?limit=10`.  
**Fix**: Change to `?limit=5`. The backend `/insights/top-spends/{month_key}` endpoint already accepts a `limit` query param and returns that many rows.

```ts
// line 133 — change:
api.get<TopSpend[]>(`/insights/top-spends/${selMonth}?limit=10`)
// to:
api.get<TopSpend[]>(`/insights/top-spends/${selMonth}?limit=5`)
```

No other changes needed.

---

## Item 6 — Fixed Tab: suppress "Auto-seeded fixed expense" note
**Scope**: Frontend-only  
**File**: `frontend/react/src/components/tabs/FixedExpenseRow.tsx`

**Root cause**: `seed_fixed_expenses()` in `backend/budget_rules.py` (line 184) sets `note="Auto-seeded fixed expense"` on every seeded row. `FixedExpenseRow.tsx` renders `item.note` unconditionally when truthy (lines 77–81).

**What to do**: Guard the note render with a check that filters out the auto-seed string:

```tsx
// lines 77–81 — change from:
{item.note && (
  <span className="ml-2 text-xs" style={{ color: "var(--text-muted)" }}>
    · {item.note}
  </span>
)}

// to:
{item.note && item.note !== "Auto-seeded fixed expense" && (
  <span className="ml-2 text-xs" style={{ color: "var(--text-muted)" }}>
    · {item.note}
  </span>
)}
```

This only suppresses the exact auto-seed string; any user-entered note still displays.

---

## Item 7 — Today/History: descending sort (latest first)
**Scope**: Backend (one line) + Frontend (one file)  
**Files**:
- `backend/main.py` — `GET /expenses/{month_key}` endpoint (line 618)
- `frontend/react/src/components/tabs/QuickAddTab.tsx` (line 64–68)

**Root cause**:
- `GET /expenses/{month_key}` already sorts by `Expense.date.desc()` (line 618), but `date` is a `DATE` column — within the same day, rows are returned in insertion order (ascending by id).
- `HistoryTab.tsx` client-side sorts by `b.date.localeCompare(a.date)` which also only uses the day string, so same-day items remain insertion-order.
- `QuickAddTab.tsx` slices `.slice(0, 10)` after filtering for today — relies entirely on API order.

**What to do**:

### Backend (`main.py` line 618)
Add `Expense.id.desc()` as a tiebreaker:
```python
# change:
).order_by(Expense.date.desc())
# to:
).order_by(Expense.date.desc(), Expense.id.desc())
```

### Frontend (`HistoryTab.tsx` line 270)
Update the client-side sort to also tiebreak by `id` descending:
```ts
// change:
return [...list].sort((a, b) => b.date.localeCompare(a.date));
// to:
return [...list].sort((a, b) => {
  const byDate = b.date.localeCompare(a.date);
  return byDate !== 0 ? byDate : b.id - a.id;
});
```

`QuickAddTab.tsx` gets the fix automatically once the API sorts correctly — no frontend change needed there.

---

## Item 8 — Cross-Tab Summary Cards (SummaryStrip + SummaryFlipCards)
**Scope**: Frontend-only (reuses `GET /summary/{month_key}`)  
**New files**:
- `frontend/react/src/components/shared/SummaryStrip.tsx`
- `frontend/react/src/components/shared/SummaryFlipCard.tsx`

**Modified files**:
- `frontend/react/src/pages/DashboardPage.tsx`
- `frontend/react/src/index.css` (flip card 3D CSS)

### Step 8a — `SummaryStrip.tsx` (mobile, < 768 px)

Props: `balance: Summary['balance']`

Renders a horizontal row of 4 chips, each with:
- Label (`text-[10px] uppercase tracking-widest`)
- Amount with count-up animation on mount (use `useEffect` + `requestAnimationFrame` to increment from 0 to final value over 600 ms, ease-out curve)

Chips (left → right): Income · Fixed Paid · Fixed Remaining · Balance Left  
Colour coding: Balance Left → green if ≥ 0, red if < 0; others use `var(--text-sub)`.  
Strip is `sticky top-0 z-20` so it stays below the tab bar when content scrolls.

### Step 8b — `SummaryFlipCard.tsx` (desktop, ≥ 768 px)

Props: `label: string`, `value: number`, `colour?: string`

Single card with CSS 3D flip on hover:
- Front face: label text centred, subtle icon or decorative element
- Back face: bold ₹ amount + same label in smaller text
- Transition: `transform-style: preserve-3d`, `transition: transform 300ms ease`, `rotateY(180deg)` on hover

Colour for the amount and a thin top-border accent matches the `colour` prop.

Add to `index.css`:
```css
.flip-card { perspective: 600px; }
.flip-card-inner { transition: transform 0.3s ease; transform-style: preserve-3d; }
.flip-card:hover .flip-card-inner { transform: rotateY(180deg); }
.flip-card-front, .flip-card-back { backface-visibility: hidden; }
.flip-card-back { transform: rotateY(180deg); }
```

### Step 8c — `DashboardPage.tsx` wiring

1. Fetch `GET /summary/{selMonth}` at the dashboard level (lifted out of `OverviewTab` — or fetched independently here to keep `OverviewTab` self-contained). Store as `summaryBalance` state.
2. Render the responsive summary block between `<BottomNav>` and `<main>` — but only when `tab === "today"` or `tab === "fixed"`:

```tsx
{(tab === "today" || tab === "fixed") && summaryBalance && (
  <>
    {/* Mobile strip */}
    <div className="md:hidden sticky top-[56px] z-20 px-4 py-2
                    border-b border-white/5"
         style={{ backgroundColor: "var(--bg)" }}>
      <SummaryStrip balance={summaryBalance} />
    </div>
    {/* Desktop flip cards */}
    <div className="hidden md:flex gap-3 max-w-2xl mx-auto px-4 py-3">
      <SummaryFlipCard label="Income"          value={summaryBalance.total_income}      colour="#6366f1" />
      <SummaryFlipCard label="Fixed Paid"      value={summaryBalance.fixed_paid_total}  colour="#34d399" />
      <SummaryFlipCard label="Fixed Remaining" value={summaryBalance.fixed_unpaid_total} colour="#f59e0b" />
      <SummaryFlipCard label="Balance Left"    value={summaryBalance.remaining}          colour={summaryBalance.remaining >= 0 ? "#34d399" : "#f87171"} />
    </div>
  </>
)}
```

3. Re-fetch `summaryBalance` when a new expense is added (listen for the same `fixedTemplateUpdated` event pattern, or pass a `onExpenseAdded` callback from `QuickAddTab`). The simplest approach: pass a `refreshKey` counter from `DashboardPage` that increments on each add; include it as a `useEffect` dep in the summary fetch.

---

## Execution Order

| # | Item | Effort | Risk |
|---|------|--------|------|
| 1 | Forgot password stub | XS | None |
| 5 | Top spends → limit 5 | XS | None |
| 6 | Suppress auto-seed note | XS | None |
| 3 | Pie chart tooltip colour | XS | None |
| 7 | Sort order fix | S | Low — one backend line + one frontend line |
| 4 | Monthly breakdown rows | S | Low — component rewrite, no API change |
| 2 | Dividend/bonus income | M | Medium — backend model + new endpoint + frontend UI |
| 8 | Cross-tab summary cards | L | Low — additive only, no existing code touched |

Start with items 1, 5, 6, 3 in one pass (all trivial). Then 7 and 4 together. Then 2. Then 8 last (largest but additive).

---

## Definition of Done
- `npm run build` passes (zero TypeScript errors, zero ESLint warnings)
- All 8 items manually verified in the running app (dev server + live backend)
- No regressions in OverviewTab, HistoryTab, or FixedTab existing functionality
