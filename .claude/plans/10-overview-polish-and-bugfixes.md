# Implementation Plan: Overview Polish + Bug Fixes — Sprint 10
**Spec**: `.claude/specs/10_overview-polish-and-bugfixes.md`
**Date**: 2026-06-26
**Branch**: `feature/sprint06261-ui-enhancement`

---

## Overview

8 executable items: 3 bug fixes + 5 feature items.
**2 items require backend changes** (Item 3 — cache invalidation; Item 7 — Peace of Mind breakdown).
**1 new file** (Item 6 — `SpendingSignalsModal.tsx`).
**Item 8 (section reorder + responsive pairs) must run last** — depends on Items 4–7 being complete.

All decisions locked. No blocked items. Start with the two XS bug fixes (Items 1 and 2) — zero risk, immediate user-visible improvement.

---

## ⚠️ Flags & Gaps

### Flag 1 — Financial Pulse layout change in spec 09 R1
Spec 09 R1 specified a vertical list layout for Financial Pulse. This was superseded during spec 10 review — the confirmed layout is the **2×2 tile grid** matching the mockup. If spec 09 R1 has already been implemented as a vertical list, Item 8 (reorder) should also correct the Financial Pulse layout to 2×2 tiles. Check before executing Item 8.

### Flag 2 — `BudgetHealthCard` replacement strategy
Spec 10 R8 says "full redesign or replace with inline JSX". Before implementing Item 6, check whether `BudgetHealthCard` is used anywhere other than `OverviewTab.tsx`. If used elsewhere, redesign in place. If used only in OverviewTab, inline JSX is simpler and avoids prop interface churn.

### Flag 3 — Top Spends endpoint field verification
Before implementing Item 5 (R9 — Money Moments), read the existing top-spends endpoint response shape. The spec assumes `vendor`, `category`, `date`, `amount` are already returned. If `date` is missing, it must be added to the backend response — note this as a blocker and fix before frontend work.

### Flag 4 — Tailwind `md:` breakpoint
Tailwind's default `md:` breakpoint is 768px. The spec requires 580px. Before implementing Item 8, check `tailwind.config.js` for a custom `sm` or `md` breakpoint. If none exists at 580px, either add a custom screen (`'pair': '580px'`) or use an inline CSS media query wrapper (`style="display:grid"` with a `<style>` tag). Do not use 768px — it is too wide for the intended pairing on smaller laptops.

### Flag 5 — `_score_history` persistence
`_score_history` in `backend/main.py` is an in-memory dict. It resets on server restart, meaning delta will always be `null` after a deploy. This is acceptable for now — add a `# TODO: persist score_history to DB for reliable delta` comment. Do not block Item 7 on this.

---

## Item 1 — B2: Rename "Day-to-day" → "Variable" filter tab
**Scope**: Frontend-only
**Files**: `frontend/react/src/components/tabs/OverviewTab.tsx` (or child component rendering the Spend by Category filter tabs)

**Root cause**: The filter tab label is hardcoded as `"Day-to-day"`. The correct label per spec is `"Variable"`.

**What to do**:
1. Search for the string `"Day-to-day"` in `OverviewTab.tsx` and any imported child components (e.g. `SpendDonut.tsx` or similar).
2. Replace with `"Variable"`.
3. Filter logic (which categories are included/excluded) is unchanged — label only.

**Acceptance criteria**:
- Filter tab reads "Variable | Fixed Bills | All".
- Switching tabs still filters categories correctly.
- No TypeScript errors.

---

## Item 2 — B3: Fix due-reminders label for future bills
**Scope**: Frontend-only
**Files**: `frontend/react/src/components/tabs/OverviewTab.tsx` — Upcoming Reality section

**Root cause**: The label logic does not check the sign of `days_overdue`. When `days_overdue` is negative (bill is in the future), it incorrectly renders as overdue.

**What to do**:
Locate the label derivation for `days_overdue` in the Upcoming Reality section. Replace with:

```tsx
const dueLabel =
  days_overdue < 0
    ? `Due in ${Math.abs(days_overdue)} day(s)`
    : days_overdue === 0
    ? "Due today"
    : `${days_overdue} day(s) overdue`;
```

Also fix the sort order. Current sort: verify it is `ascending` by `days_overdue`. The first item shown should be the one with `days_overdue <= 0` closest to 0 (i.e. most imminent upcoming bill). If all bills are past due (`days_overdue > 0`), show the most overdue (highest positive value first).

Correct sort:
```tsx
const sorted = [...dueReminders].sort((a, b) => a.days_overdue - b.days_overdue);
const next = sorted.find(r => r.days_overdue <= 0) ?? sorted[sorted.length - 1];
```

**Acceptance criteria**:
- Bill due in 2 days → "Due in 2 day(s)".
- Bill due today → "Due today".
- Bill 2 days past due → "2 day(s) overdue".
- The most imminent upcoming bill is shown first; falls back to most overdue if all are past due.

---

## Item 3 — B1: Invalidate story and mantra caches on expense mutation
**Scope**: Backend-only
**Files**: `backend/main.py`

**Root cause**: `_story_cache` and `_mantra_cache` are keyed by `(user_id, month_key)` and never invalidated. After a user edits or deletes an expense, the cached story sentence reflects stale data until the cache key TTL expires (or server restart).

**What to do**:

### Add helper after the cache dict declarations:
```python
def _invalidate_month_caches(user_id: int, month_key: str) -> None:
    _story_cache.pop((user_id, month_key), None)
    _mantra_cache.pop((user_id, month_key), None)
```

### Call at the end of each expense mutation endpoint:
- `POST /expenses` — derive `month_key` from the expense date (`expense.date[:7]`), then call `_invalidate_month_caches(current_user.id, month_key)`.
- `PUT /expenses/{id}` — call for both the old expense's month_key (before update) and the new expense's month_key (after update), in case the date changed months.
- `DELETE /expenses/{id}` — derive `month_key` from the deleted expense's date, then call `_invalidate_month_caches(current_user.id, month_key)`.

**Acceptance criteria**:
- After adding an expense, the next fetch of `/insights/story/{month_key}` returns a freshly generated sentence.
- After editing an expense's category or amount, same.
- After deleting an expense, same.
- Cache invalidation for month A does not affect cached stories for month B.
- `_mantra_cache` is also invalidated via the same helper.

---

## Item 4 — R10: Monthly Breakdown Insight row (2-month average)
**Scope**: Frontend-only
**Files**: `frontend/react/src/components/tabs/OverviewTab.tsx`

**Root cause**: Spec 09 R6 added a `// TODO: Insight row` comment below `<BalanceBreakdown>`. The insight requires a 2-month average of `variable_total / total_income`. The prior month's summary is fetchable from the existing `/summary/{month_key}` endpoint — no new backend work needed.

**What to do**:

### Add `prevSummary` state:
```tsx
const [prevSummary, setPrevSummary] = useState<Summary | null>(null);
```

### Derive `prevMonthKey` inside `load()`:
```tsx
const [year, month] = selMonth.split("-").map(Number);
const prevDate = new Date(year, month - 2, 1); // month-2 because JS months are 0-indexed
const prevMonthKey = `${prevDate.getFullYear()}-${String(prevDate.getMonth() + 1).padStart(2, "0")}`;
```

### Add to `load()`'s Promise.all as an additional call:
```tsx
api.get<Summary>(`/summary/${prevMonthKey}`).then(r => r.data).catch(() => null)
```
Destructure and call `setPrevSummary(...)`.

### Replace the `// TODO: Insight row` comment with:
```tsx
{(() => {
  const currVarPct = balance.total_income > 0
    ? Math.round(balance.variable_total / balance.total_income * 100)
    : null;
  const prevVarPct = prevSummary?.balance.total_income
    ? Math.round(prevSummary.balance.variable_total / prevSummary.balance.total_income * 100)
    : null;
  if (currVarPct === null) return null;
  const avgPct = prevVarPct !== null
    ? Math.round((currVarPct + prevVarPct) / 2)
    : null;
  return (
    <div className="flex gap-2 items-start mt-3 rounded-xl border-l-2 pl-3 py-2"
         style={{ borderColor: "#f59e0b", background: "var(--card-muted)" }}>
      <span style={{ color: "#f59e0b", fontSize: 12 }}>⚡</span>
      <p className="text-[11px] leading-relaxed" style={{ color: "var(--text-muted)" }}>
        Variable spending consumed{" "}
        <span className="font-semibold" style={{ color: "var(--text)" }}>
          {currVarPct}% of income
        </span>{" "}
        this month.{" "}
        {avgPct !== null
          ? <>Your average over the last 2 months is <span className="font-semibold" style={{ color: "var(--text)" }}>{avgPct}%</span>.</>
          : "No prior month data to compare."}
      </p>
    </div>
  );
})()}
```

**Acceptance criteria**:
- Insight row renders below `<BalanceBreakdown>`.
- Shows `currVarPct`% and 2-month average when prior month data available.
- Shows fallback message when prior month returns null.
- No crash when `prevSummary` is null.
- `// TODO: Insight row` comment removed.
- TypeScript build clean.

---

## Item 5 — R9: Money Moments (rename + context badges)
**Scope**: Frontend-only (verify backend fields first — see Flag 3)
**Files**: `frontend/react/src/components/tabs/OverviewTab.tsx` — Top Spends section

**Root cause**: "Top Spends This Month" section lacks a summary line, context badges, and rank indicators. The rename and badge logic are frontend-only.

**What to do**:

### Pre-check (do before writing any code):
Read the current top-spends data shape in `OverviewTab.tsx`. Confirm `vendor`, `category`, `date`, `amount` are all present. If `date` is missing from the endpoint response, add it to the backend before proceeding.

### Summary line (add above the transaction list):
```tsx
{topSpends.length > 0 && balance.variable_total > 0 && (
  <p className="text-[11px] mb-3" style={{ color: "var(--text-muted)" }}>
    Largest {topSpends.length} purchases contributed{" "}
    <span style={{ color: "var(--text)", fontWeight: 600 }}>
      {Math.round(topSpends.reduce((s, t) => s + t.amount, 0) / balance.variable_total * 100)}%
    </span>{" "}
    of this month's spending.
  </p>
)}
```

### Context badge helper (add before the return):
```tsx
const getContextBadge = (tx: TopSpend, rank: number): { label: string; colour: string } | null => {
  if (rank === 1) return { label: "🏆 Biggest Purchase", colour: "#f59e0b" };
  if (["Savings", "Investments", "Mutual Fund"].includes(tx.category))
    return { label: "📈 Investment", colour: "#818cf8" };
  if (["Course", "Education"].includes(tx.category))
    return { label: "📚 Learning", colour: "#818cf8" };
  if (["Travel", "Medical", "Rent", "Cook", "Milk", "Electricity"].includes(tx.category))
    return { label: "🚗 Essential", colour: "#94a3b8" };
  if (tx.category === "Gifts")
    return { label: "❤️ Special Moment", colour: "#f472b6" };
  if (rank === 2) return { label: "👑 Top Spend", colour: "#f59e0b" };
  return null;
};
```

### Per-row changes:
- Add rank indicator (1–5, gold background for rank 1).
- Add `% of total spending` below the amount: `Math.round(tx.amount / balance.variable_total * 100)%`.
- Add context badge below the percentage when `getContextBadge` returns non-null.

### Section heading:
- Change "Top Spends This Month" → "💎 Money Moments".
- Add "View all →" button in header that fires `toast("See all transactions in the History tab →")`.

**Acceptance criteria**:
- Heading reads "💎 Money Moments" with "View all →".
- Summary line present when `variable_total > 0`.
- Rank 1 always gets 🏆 Biggest Purchase badge.
- Investment / Learning / Essential / Special Moment badges apply correctly to ranks 2+.
- Rank 2 gets 👑 Top Spend when no category badge applies.
- "View all →" toast fires: "See all transactions in the History tab →".

---

## Item 6 — R8: Spending Signals (rename + top-3 traffic light + View all modal)
**Scope**: Frontend-only (see Flag 2 before starting)
**Files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — Spending Signals section
- `frontend/react/src/components/shared/SpendingSignalsModal.tsx` — new file

**Root cause**: `BudgetHealthCard` renders all categories with progress bars that extend beyond 100%. The spec replaces this with a 3-card traffic-light design and a full bottom-sheet modal for "View all".

**What to do**:

### Pre-check:
Search for all usages of `BudgetHealthCard`. If used only in `OverviewTab.tsx`, inline the new design. If used elsewhere, create a new `SpendingSignalCard` component and keep `BudgetHealthCard` untouched.

### Signal selection logic (derive inline in OverviewTab):
```tsx
const budgetSignals = (() => {
  if (!budgets || budgets.length === 0) return [];
  const withRatio = budgets
    .filter(b => b.budget > 0)
    .map(b => ({ ...b, ratio: b.spent / b.budget }));
  const sorted = [...withRatio].sort((a, b) => b.ratio - a.ratio);
  const top = sorted[0];      // highest ratio — red
  const mid = sorted[1];      // second — amber
  const low = [...withRatio]  // lowest with spend > 0 — green
    .filter(b => b.spent > 0)
    .sort((a, b) => a.ratio - b.ratio)[0];
  return [top, mid, low].filter(Boolean);
})();
```

### Traffic light thresholds:
```tsx
const getSignalState = (ratio: number) => {
  if (ratio > 1)   return { badge: `Over by ${fmtInr(spent - budget)}`, colour: "#f87171", bg: "#2e1414" };
  if (ratio >= 0.8) return { badge: "Almost full", colour: "#f59e0b", bg: "#2e200a" };
  return           { badge: "On track",   colour: "#34d399", bg: "#0e2419" };
};
```

### Daily rate (right side):
```tsx
const daysLeft = isCurrentMonth ? daysInMonth - new Date().getDate() : 0;
const dailyRate = daysLeft > 0 && spent <= budget
  ? `₹${Math.round((budget - spent) / daysLeft)}/day left`
  : spent > budget
  ? `₹${fmtInr(spent - budget)} over`
  : null;
```

### Section heading change:
- `"Budget Health"` → `"Spending Signals"`
- Add `"View all →"` button that sets `showSignalsModal(true)`.

### `SpendingSignalsModal.tsx` — new file:
```tsx
// Props: { open: boolean; onClose: () => void; budgets: BudgetItem[]; daysLeft: number; fmtInr: fn }
// Renders a fixed bottom sheet: drag handle + "Spending Signals" heading + ALL budgeted
// categories as traffic-light cards (same card component, no limit).
// Close on backdrop click.
// Use `position: fixed; inset: 0` for backdrop, `position: fixed; bottom: 0; left: 0; right: 0;
// max-height: 85vh; overflow-y: auto` for the sheet itself.
// NOTE: Do not use position: fixed if rendering inside an iframe — check rendering context first.
// If in an iframe, use a full-height div overlay instead.
```

**Acceptance criteria**:
- Section heading reads "Spending Signals" with "View all →".
- Exactly 3 signal cards shown (fewer if fewer budgeted categories with spend > 0).
- No progress bars anywhere.
- Each card: category name, % of budget, badge (Over by / Almost full / On track), amount spent of budget, daily rate or overage.
- "View all →" opens bottom-sheet modal showing all budgeted categories.
- Modal closes on backdrop tap.
- TypeScript build clean.

---

## Item 7 — R7: Peace of Mind breakdown + delta movement
**Scope**: Backend + Frontend
**Files**:
- `backend/main.py` — extend `/insights/peace-of-mind/{month_key}`
- `frontend/react/src/types/index.ts` — extend `PeaceOfMind` interface
- `frontend/react/src/components/tabs/OverviewTab.tsx` — redesign Peace of Mind card

**Root cause**: Current endpoint returns only `{ score: int }`. The redesigned card needs factor breakdown, summary line, and delta vs yesterday.

### Backend — factor derivation:

```python
def _compute_pom_factors(balance: dict, budgets: list) -> list[dict]:
    factors = []

    # Positive factors
    fixed_total = balance["fixed_paid_total"] + balance["fixed_unpaid_total"]
    bills_pts = round(25 * balance["fixed_paid_total"] / fixed_total) if fixed_total > 0 else 0
    factors.append({"label": "Bills paid on time", "points": bills_pts})

    if balance["remaining"] > 0:
        factors.append({"label": "Positive remaining balance", "points": 20})

    factors.append({"label": "Consistent tracking", "points": 15})
    # TODO: replace with real streak

    # Negative factors — top 2 overspent categories
    overspent = sorted(
        [b for b in budgets if b["spent"] > b["budget"] and b["budget"] > 0],
        key=lambda b: b["spent"] - b["budget"], reverse=True
    )[:2]
    for b in overspent:
        pts = -round(min(15, (b["spent"] - b["budget"]) / b["budget"] * 10))
        factors.append({"label": f"{b['category']} overspend", "points": pts})

    # Pending bills deduction
    if balance["fixed_unpaid_total"] > 0 and balance["total_income"] > 0:
        pts = -round(min(16, balance["fixed_unpaid_total"] / balance["total_income"] * 100))
        factors.append({"label": "Pending bills", "points": pts})

    return factors
```

### Backend — score + summary + delta:
```python
base = 60
score = max(0, min(100, base + sum(f["points"] for f in factors)))

neg_count = sum(1 for f in factors if f["points"] < 0)
if neg_count == 0:
    summary = "Your finances are on track this month."
elif neg_count <= 2:
    summary = f"Your finances are stable but {neg_count} area(s) need attention."
else:
    summary = "A few areas need your attention this month."

today_key = (current_user.id, month_key, str(date.today()))
yesterday_key = (current_user.id, month_key, str(date.today() - timedelta(days=1)))
_score_history[today_key] = score
delta = score - _score_history[yesterday_key] if yesterday_key in _score_history else None
# TODO: persist score_history to DB for reliable delta across server restarts
```

### Backend — response shape:
```python
return {
    "score": score,
    "summary": summary,
    "delta": delta,
    "factors": factors,
}
```

Add `from datetime import date, timedelta` if not already imported.
Add `_score_history: dict[tuple, int] = {}` near `_mantra_cache`.

### Frontend — extend type:
```typescript
export interface PeaceOfMind {
  score: number;
  summary?: string;
  delta?: number | null;
  factors?: { label: string; points: number }[];
}
```

### Frontend — redesign card:

**SVG dial** (CSS-only, no library):
```tsx
const radius = 33;
const circ = 2 * Math.PI * radius; // ~207
const filled = (pom.score / 100) * circ;
const dialColour = pom.score >= 70 ? "#34d399" : pom.score >= 40 ? "#f59e0b" : "#f87171";

<svg width="88" height="88" viewBox="0 0 88 88">
  <circle cx="44" cy="44" r={radius} fill="none" stroke="var(--border-lg)" strokeWidth="9" />
  <circle cx="44" cy="44" r={radius} fill="none" stroke={dialColour} strokeWidth="9"
    strokeDasharray={`${filled} ${circ}`} strokeDashoffset={circ * 0.25}
    strokeLinecap="round" transform="rotate(-90 44 44)" />
</svg>
```

**Score centred in dial**, delta badge below it, factor list to the right.

**"Why this score?" expand** — when open, show a static methodology explanation:
> "Score = 60 base + bills completion (up to +25) + positive balance (+20) + tracking (+15), minus overspend and pending bill deductions."

**Acceptance criteria**:
- Dial colour reflects score range (green/amber/red).
- Score + "/100" centred in dial.
- Delta "↑ N pts vs yesterday" / "↓ N pts" shown when available; omitted when null.
- All factors shown inline (positives first, then negatives).
- "Why this score?" expand shows methodology only.
- Score clamped to [0, 100].
- TypeScript build clean.

---

## Item 8 — R11: Section reorder + responsive pairs
**Scope**: Frontend-only
**Files**: `frontend/react/src/components/tabs/OverviewTab.tsx`
**Depends on**: Items 4, 5, 6, 7 complete

**Root cause**: Section order and responsive pairing need to match spec 10 R11 canonical order. Two section pairs must render side-by-side at ≥580px.

**Pre-check (do before reordering)**:
1. Count total sections in `OverviewTab.tsx`. Record the count.
2. Check `tailwind.config.js` for a breakpoint at or near 580px (see Flag 4).
3. Check Financial Pulse layout — if it was implemented as a vertical list (spec 09 R1 original direction), update to 2×2 tile grid now (confirmed layout per spec 10 review).

**Canonical section order** (from spec 10 R11):
```
1.  Financial Snapshot
2.  June in One Sentence
3+4 [PAIR] Monthly Breakdown + Insight ∥ Spend by Category + Winner
5+6 [PAIR] Peace of Mind ∥ Spending Signals
7.  Upcoming Reality
8.  Money Moments
9.  What Changed?
10. Financial Pulse (2×2 tile grid)
11. Tiny Win
    Tara footer strip
```

**Responsive pair wrapper** (use for sections 3+4 and 5+6):
```tsx
<div className="grid grid-cols-1 gap-3 px-4 mt-4"
     style={{ gridTemplateColumns: "1fr" }}
     ref={el => {
       if (el) el.style.gridTemplateColumns =
         window.innerWidth >= 580 ? "1fr 1fr" : "1fr";
     }}>
  <div>{/* left */}</div>
  <div>{/* right */}</div>
</div>
```

Or add a custom Tailwind screen in `tailwind.config.js`:
```js
screens: { 'pair': '580px' }
```
Then use `pair:grid-cols-2`.

Or use a CSS class in the global stylesheet:
```css
@media (min-width: 580px) { .pair-grid { grid-template-columns: 1fr 1fr; } }
```

Choose whichever approach is least invasive to the existing Tailwind config.

**After reordering**:
- Update all `// ── Section N:` comments to new positions.
- Count sections again — must match pre-reorder count exactly.
- Check Financial Pulse renders as 2×2 tiles.

**Acceptance criteria**:
- Sections render in canonical order from spec 10 R11.
- At ≥580px: pairs 3+4 and 5+6 render side-by-side.
- At <580px: all sections stack single column.
- Section count before = section count after.
- Financial Pulse is a 2×2 tile grid.
- TypeScript build clean.

---

## Execution Summary

| Item | Spec ref | Scope | Effort | Depends on | Status |
|------|----------|-------|--------|------------|--------|
| 1 | B2 — "Variable" label | Frontend | XS | — | ✅ Done 2026-06-26 |
| 2 | B3 — Due-reminders sign fix | Frontend | XS | — | ✅ Done 2026-06-26 (also fixed FixedTab.tsx) |
| 3 | B1 — Cache invalidation | Backend | S | — | ✅ Done 2026-06-26 |
| 4 | R10 — Insight row (2-month avg) | Frontend | S | — | ✅ Done 2026-06-26 |
| 5 | R9 — Money Moments | Frontend | S | Flag 3 | ✅ Done 2026-06-26 |
| 6 | R8 — Spending Signals + modal | Frontend | M | Flag 2 | ✅ Done 2026-06-26 |
| 7 | R7 — Peace of Mind breakdown | Backend + Frontend | M | — | ✅ Done 2026-06-26 |
| 8 | R11 — Reorder + responsive pairs | Frontend | S | Items 4–7 | ✅ Done 2026-06-27 |
