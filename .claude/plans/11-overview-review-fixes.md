# Implementation Plan: Overview Review Fixes — Sprint 11
**Spec**: `.claude/specs/11_overview-review-fixes.md`
**Date**: 2026-06-27
**Branch**: `feature/sprint06261-ui-enhancement`

---

## Overview

9 items: 3 spec violations (F1–F3), 3 layout fixes (L1–L3), 3 polish items (P1–P3).
**1 item requires backend work** (F2/F2a — standalone Insight card + first-month prompt branching).
**8 items are pure frontend** — 5 are XS one-liners, 3 are S-effort.
**No item is blocked by another** — all can be done in order.

Start with Items 1–5 (all XS, zero-risk visual fixes) before tackling Items 6–9.

---

## ⚠️ Flags & Gaps

### Flag 1 — Spending Signals component location
Before implementing Item 6 (F1), confirm where the primary stat ("168%") is rendered. It may be in `OverviewTab.tsx` inline JSX or inside a `SpendingSignalCard` sub-component created in sprint 10. Search for the percentage render before editing.

### Flag 2 — BalanceBreakdown component
Item 1 (F3) and Item 7 (L1) both touch the stacked bar. Before Item 1, check whether the bar is rendered inline in `OverviewTab.tsx` or extracted into a `BalanceBreakdown` component. If extracted, make changes in that component file.

### Flag 3 — Financial Pulse DOM nesting (for L2)
Before Item 8, inspect the JSX structure around Financial Pulse in `OverviewTab.tsx`. Look for any wrapping grid or flex parent that might be constraining it to a column. If Financial Pulse shares a parent with Money Moments or What Changed?, it needs to be moved outside that parent.

### Flag 4 — Insight endpoint naming conflict
Sprint 10 already added a story endpoint (`/insights/story/{month_key}`) and a peace-of-mind endpoint (`/insights/peace-of-mind/{month_key}`). For F2, use `/insights/monthly-insight/{month_key}` to avoid naming collision. Confirm this route does not already exist before adding.

### Flag 5 — `_invalidate_month_caches` must include `_insight_cache`
When implementing F2 backend, add `_insight_cache.pop((user_id, month_key), None)` to the existing `_invalidate_month_caches` helper. Do not create a second invalidation function.

---

## Item 1 — F3: Add segment labels inside stacked breakdown bar
**Spec ref**: F3
**Scope**: Frontend-only
**Files**: `OverviewTab.tsx` (or `BalanceBreakdown` component — see Flag 2)

**What to do**:
1. Locate the stacked bar segments (three `<div>` elements with flex widths representing bills, variable, balance).
2. Each segment `<div>` already has `width: X%`. Compute `widthPct` as the numeric percentage for each segment.
3. Apply the label rule: if `widthPct >= 12`, render `"{label} {pct}%"` inside the segment; otherwise render `"{pct}%"` only.
4. Labels:
   - Fixed Paid / Bills segment → `"Bills"`
   - Variable Spent segment → `"Variable"`
   - Balance Left segment → `"Balance"`
5. Style: `font-size: 10px`, `color: #fff`, `white-space: nowrap`, `overflow: hidden`, `text-overflow: ellipsis`, centered vertically in the segment.

**Acceptance criteria**:
- Segments ≥12% wide show e.g. "Bills 62%".
- Segments <12% show percentage only.
- No overflow outside bar container at any viewport width.

---

## Item 2 — P1: Bills Paid KPI smarter subtext
**Spec ref**: P1
**Scope**: Frontend-only
**Files**: `OverviewTab.tsx` — Bills Paid KPI card

**What to do**:
Locate the Bills Paid KPI subtitle string. Replace with:
```tsx
const billsSubtitle = balance.fixed_unpaid_total === 0
  ? "All bills cleared ✓"
  : `Out of ₹${fmtInr(balance.fixed_paid_total + balance.fixed_unpaid_total)}`;
```
Use `billsSubtitle` in the KPI render.

**Acceptance criteria**:
- 100% paid → subtitle reads "All bills cleared ✓".
- Unpaid bills remain → subtitle reads "Out of ₹{total}".

---

## Item 3 — P2: Cap extreme MoM percentages in What Changed?
**Spec ref**: P2
**Scope**: Frontend-only
**Files**: `OverviewTab.tsx` — What Changed? section

**What to do**:
Locate where MoM percentage change is derived and displayed. Add a display formatter:
```tsx
const fmtMoM = (pct: number | null, prevAmount: number | null): string => {
  const isNew = prevAmount === null || prevAmount === 0;
  if (isNew) return "New this month";
  if (pct === null) return "—";
  if (Math.abs(pct) > 300) return pct > 0 ? "↑ New high" : "↓ Major drop";
  return `${pct > 0 ? "↑" : "↓"} ${Math.abs(Math.round(pct))}%`;
};
```
Replace inline percentage display with `fmtMoM(row.pct_change, row.prev_amount)`.

Confirm the data shape from the What Changed? API response includes `prev_amount` (or equivalent). If not, derive `isNew` from `pct_change > 300 && currentAmount > 0`.

**Acceptance criteria**:
- Zero prior-month base → "New this month".
- >300% absolute change → "↑ New high" or "↓ Major drop".
- ≤300% change → "↑ X%" or "↓ X%" as before.

---

## Item 4 — P3: Add icons to full-width section headings
**Spec ref**: P3
**Scope**: Frontend-only
**Files**: `OverviewTab.tsx` — 6 section heading strings

**What to do**:
Find each of the 6 section headings and prepend the assigned emoji:

| Find | Replace with |
|------|-------------|
| `"PEACE OF MIND"` (or `"Peace of Mind"`) | `"🧘 Peace of mind"` |
| `"SPENDING SIGNALS"` (or `"Spending Signals"`) | `"📡 Spending signals"` |
| `"UPCOMING REALITY"` (or `"Upcoming Reality"`) | `"📅 Upcoming reality"` |
| `"WHAT CHANGED?"` (or `"What Changed?"`) | `"📊 What changed?"` |
| `"FINANCIAL PULSE"` (or `"Financial Pulse"`) | `"💓 Financial pulse"` |
| `"TINY WIN"` (or `"Tiny Win"`) | `"🎉 Tiny win"` |

If headings use `text-transform: uppercase` CSS, remove that property (or Tailwind `uppercase` class) so sentence case is rendered correctly.

**Acceptance criteria**:
- All 6 headings have their icon prefix.
- All headings are sentence case.
- Icon and text are on the same baseline.

---

## Item 5 — L3: Top Spending Category separator
**Spec ref**: L3
**Scope**: Frontend-only
**Files**: `OverviewTab.tsx` — Spend by Category card, Top Spending Category sub-section

**What to do**:
Locate the Top Spending Category block inside the Spend by Category card. Add a divider above it:
```tsx
<div className="border-t mt-3 pt-3" style={{ borderColor: "var(--border)" }}>
  {/* existing Top Spending Category content */}
</div>
```

**Acceptance criteria**:
- Hairline border separates the category list from the Top Spending Category block.
- Vertical spacing is consistent with other intra-card dividers.

---

## Item 6 — F1: Reformat Spending Signals primary stat
**Spec ref**: F1
**Scope**: Frontend-only
**Files**: `OverviewTab.tsx` (or `SpendingSignalCard` — see Flag 1)

**What to do**:
Locate where the primary percentage stat is computed/rendered for each signal tile. Replace raw ratio display with:

```tsx
const getSignalStat = (spent: number, budget: number): string => {
  const ratio = spent / budget;
  if (ratio > 1) {
    const overPct = Math.round((ratio - 1) * 100);
    return `${overPct}% over budget`;
  }
  const pct = Math.round(ratio * 100);
  return `${pct}% of budget`;
};
```

Use `getSignalStat(signal.spent, signal.budget)` as the primary large-text stat in each tile.

Keep the secondary badge ("Over by ₹X" / "On track" / "Almost full") unchanged.

**Acceptance criteria**:
- Over-budget tile: e.g. "68% over budget" (not "168%").
- On-track tile: e.g. "21% of budget".
- Near-budget tile: e.g. "92% of budget".
- Secondary badge unchanged.

---

## Item 7 — L1: Card height parity in responsive pairs
**Spec ref**: L1
**Scope**: Frontend-only
**Files**: `OverviewTab.tsx` — responsive pair grid wrappers and card root divs

**What to do**:
1. Locate the two responsive pair wrappers (the `div` with `grid grid-cols-1 pair:grid-cols-2` or equivalent).
2. Confirm the grid wrapper uses `align-items: stretch` — this is CSS Grid default but may have been overridden. Remove any `items-start` or `align-items: flex-start` on the wrapper.
3. Ensure each direct child `<div>` of the pair wrapper has `h-full` (Tailwind) or `height: 100%`.
4. Ensure each card root element inside those children also has `h-full`.

```tsx
<div className="grid grid-cols-1 gap-3 px-4 mt-4 pair:grid-cols-2">
  <div className="h-full">
    <MonthlyBreakdownCard className="h-full" />
  </div>
  <div className="h-full">
    <SpendByCategoryCard className="h-full" />
  </div>
</div>
```

**Acceptance criteria**:
- Both cards in each pair always match the taller sibling's height at ≥580px.
- At <580px, cards revert to natural height.
- No white-space gap below the shorter card's content.

---

## Item 8 — L2: Financial Pulse — ensure full-width placement
**Spec ref**: L2
**Scope**: Frontend-only
**Files**: `OverviewTab.tsx` — Financial Pulse section

**What to do**:
1. Read the JSX structure around Financial Pulse (see Flag 3). Trace parent elements up to the section level.
2. If Financial Pulse is inside a grid column div (e.g. the right column of a Money Moments ∥ What Changed? pair), move it outside — it should be a sibling of that pair grid, not a child.
3. Wrap in a standard full-width section container matching Upcoming Reality or Tiny Win:
```tsx
<div className="px-4 mt-4">
  {/* Financial Pulse content */}
</div>
```

**Acceptance criteria**:
- Financial Pulse renders full width at all viewport sizes.
- Not shifted right or constrained to a column.
- Appears between What Changed? and Tiny Win in the visual flow.

---

## Item 9 — F2: Standalone Insight card at position 5 + first-month prompt fix
**Spec ref**: F2, F2a
**Scope**: Backend + Frontend
**Files**:
- `backend/main.py` — new endpoint + cache + invalidation + prompt branching
- `frontend/react/src/components/tabs/OverviewTab.tsx` — new card at position 5 + `isSafeInsight` guard

### Backend steps

**Step 1**: Add cache dict near `_story_cache`:
```python
_insight_cache: dict[tuple, str] = {}
```

**Step 2**: Add `_insight_cache` eviction to the existing `_invalidate_month_caches` helper:
```python
def _invalidate_month_caches(user_id: int, month_key: str) -> None:
    _story_cache.pop((user_id, month_key), None)
    _mantra_cache.pop((user_id, month_key), None)
    _insight_cache.pop((user_id, month_key), None)  # add this line
```

**Step 3**: Add new endpoint (see Flag 4 — confirm route not already present).

The endpoint must detect first month and branch the AI prompt accordingly.

```python
@router.get("/insights/monthly-insight/{month_key}")
async def get_monthly_insight(month_key: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cache_key = (current_user.id, month_key)
    if cache_key in _insight_cache:
        return {"insight": _insight_cache[cache_key]}

    # Gather context
    balance = _compute_balance(current_user.id, month_key, db)
    categories = _get_category_totals(current_user.id, month_key, db)

    # Previous month
    year, month_num = map(int, month_key.split("-"))
    prev_date = date(year, month_num, 1) - timedelta(days=1)
    prev_key = prev_date.strftime("%Y-%m")
    prev_balance = _compute_balance(current_user.id, prev_key, db)

    # Detect first month
    is_first_month = (prev_balance is None or prev_balance.get("variable_total", 0) == 0)

    top_category = categories[0]["category"] if categories else "N/A"
    top_amount   = categories[0]["total"]    if categories else 0
    savings_total = balance.get("savings_total", 0)
    savings_pct   = round(savings_total / balance["total_income"] * 100) if balance["total_income"] else 0
    unpaid_count  = balance.get("fixed_unpaid_count", 0)  # adapt field name as needed

    if is_first_month:
        prompt = f"""This is the user's first tracked month in Wallet Mantra. Generate exactly ONE short, encouraging, forward-looking observation (maximum 20 words). Do not reference any comparison to prior months, percentages, or changes. Focus only on what is notable or positive about this month's actual data.

Month: {month_key}
Top spending category: {top_category} at ₹{top_amount}
Savings this month: ₹{savings_total} ({savings_pct}% of income)
Bills paid: {'all' if unpaid_count == 0 else f'{unpaid_count} remaining'}

Respond with a single sentence only. No preamble."""
    else:
        prompt = f"""You are a financial assistant. Generate exactly ONE concise observation sentence (maximum 20 words) about this user's financial behaviour this month. Do not restate totals already visible on the dashboard. Do not mention percentage changes unless both the current month and prior month values are non-zero and meaningful. Focus on a pattern, trend, or notable behaviour.

Month: {month_key}
Variable spending: ₹{balance['variable_total']} ({round(balance['variable_total']/balance['total_income']*100) if balance['total_income'] else 0}% of income)
Top category: {top_category} at ₹{top_amount}
Prior month variable: ₹{prev_balance['variable_total']}
Bills paid: {'all' if unpaid_count == 0 else f'{unpaid_count} remaining'}

Respond with a single sentence only. No preamble."""

    try:
        insight = _call_ai(prompt).strip()
        _insight_cache[cache_key] = insight
        return {"insight": insight}
    except Exception:
        return {"insight": None}
```

Note: adapt `_call_ai`, `_compute_balance`, `_get_category_totals`, field names to match what actually exists in `main.py`.

### Frontend steps

**Step 1**: Add state (if not already added by the existing `monthlyInsight` state from the current plan):
```tsx
const [monthlyInsight, setMonthlyInsight] = useState<string | null>(null);
```

**Step 2**: Add to `load()` Promise.all:
```tsx
api.get<{ insight: string | null }>(`/insights/monthly-insight/${selMonth}`)
  .then(r => setMonthlyInsight(r.data.insight))
  .catch(() => setMonthlyInsight(null)),
```

**Step 3**: Add `isSafeInsight` helper above the return statement:
```tsx
const isSafeInsight = (text: string, isFirstMonth: boolean): boolean => {
  if (!isFirstMonth) return true;
  const comparativeTerms = ["% from", "last month", "compared to", "jumped", "increased by", "decreased by"];
  return !comparativeTerms.some(term => text.toLowerCase().includes(term));
};

const isFirstMonth = prevSummary === null;
```

**Step 4**: The Insight card already exists in the correct position from sprint 11 Item 9 — inside the Monthly Breakdown column (`flex flex-col gap-3`), below `<BalanceBreakdown />`, with `flex-1` to fill remaining height. Confirm the existing card render uses the updated guard:
```tsx
{monthlyInsight && isSafeInsight(monthlyInsight, isFirstMonth) && (
  <div
    className="flex-1 rounded-2xl border p-4"
    style={{ borderColor: "var(--border)", background: "var(--card)" }}
  >
    <p className="text-[11px] font-semibold tracking-wide mb-2" style={{ color: "var(--accent)" }}>
      ✨ Insight
    </p>
    <p className="text-[13px] leading-relaxed" style={{ color: "var(--text)" }}>
      {monthlyInsight}
    </p>
  </div>
)}
```
Do NOT move the card — its position inside the Monthly Breakdown column is correct and final.

**Acceptance criteria**:
- "✨ Insight" card sits inside the Monthly Breakdown column, below `<BalanceBreakdown />`, using `flex-1` to fill remaining height.
- First-month users receive an encouraging, forward-looking sentence with no comparative language.
- Returning users receive a comparative observation only when prior data is non-zero.
- If `isSafeInsight` returns false (backend guard failed), card is suppressed silently.
- Card is hidden when API returns null or errors.
- Cache invalidated on expense mutation.
- TypeScript build clean.

---

## Execution Summary

| Item | Spec ref | Scope | Effort | Depends on | Status |
|------|----------|-------|--------|------------|--------|
| 1 | F3 — Segment labels in bar | Frontend | XS | Flag 2 | ✅ pre-session |
| 2 | P1 — Bills Paid smarter subtext | Frontend | XS | — | ✅ pre-session |
| 3 | P2 — Cap extreme MoM % | Frontend | XS | — | ✅ pre-session |
| 4 | P3 — Section heading icons | Frontend | XS | — | ✅ pre-session |
| 5 | L3 — Top Spending Category separator | Frontend | XS | — | ✅ pre-session |
| 6 | F1 — Spending Signals % reformatting | Frontend | S | Flag 1 | ✅ 2026-06-27 |
| 7 | L1 — Card height parity in pairs | Frontend | S | Flag 2 | ✅ 2026-06-27 |
| 8 | L2 — Financial Pulse full width | Frontend | S | Flag 3 | ✅ 2026-06-27 (no change — already correct) |
| 9 | F2 — Insight card (core) | Backend + Frontend | M | Flags 4, 5 | ✅ 2026-06-27 (see deviations) |
| 9b | F2a — First-month prompt guard | Backend + Frontend | S | — | ⬜ pending |
| 10 | F4 — KPI cards: drop 4th tile + remove heading | Frontend | XS | — | ⬜ pending |
| 11 | W1 — What Changed? gap detection | Frontend | S | — | ⬜ pending |

---

## Deviations from Plan (2026-06-27)

**Item 9 — Insight card placement changed**: Plan specified a standalone full-width card between the two pair grids. After implementation, user feedback repositioned it inside Section 1 (Monthly Breakdown left column). The `<section>` is now `flex flex-col gap-3`; the Insight card is the last child with `flex-1` so it fills the remaining height to match Spend by Category on the right.

**⚡ variable spending strip removed**: The computed "Variable spending consumed X% of income" strip below BalanceBreakdown was removed as redundant with the ✨ Insight card. Both communicated the same variable spend story.

**Donut filter → `<select>` dropdown** (user-requested, not in plan): The three inline filter buttons (Variable / Fixed Bills / All) were replaced with a `<select>` + `ChevronDown` icon (`appearance-none`). Default stays `"variable"`.

**F2a not yet implemented**: The first-month prompt branching (backend) and `isSafeInsight` frontend guard (spec F2a) were not done in this session — tracked as item 9b above.

---

## Item 10 — F4: Remove Financial Snapshot heading; reduce KPI tiles from 4 to 3
**Spec ref**: F4
**Scope**: Frontend-only
**Files**: `OverviewTab.tsx` — Section 0

**What to do**:
1. Remove the `<h2>Financial Snapshot</h2>` heading element and its wrapping `<section>` label entirely.
2. In the tiles array, remove the 4th entry (the "Pending Bills" / "All Bills Clear ✓" tile).
3. Change `grid-cols-2` → `grid-cols-3` on the KPI grid wrapper.

The Bills Paid tile subtitle already handles the paid/unpaid state via P1 (Item 2).

**Acceptance criteria**:
- No "Financial Snapshot" heading on the page.
- Exactly 3 tiles: Remaining, Income, Bills Paid in a single `grid-cols-3` row.
- Bills Paid subtitle shows "All bills cleared ✓" or "Out of ₹{total}" correctly.
- No other content removed.

---

## Item 11 — W1: What Changed? gap detection
**Spec ref**: W1
**Scope**: Frontend-only
**Files**: `OverviewTab.tsx` — What Changed? section

**What to do**:

**Step 1**: Add `isConsecutiveMonth` helper near the top of the What Changed? IIFE (before `changes` is built):
```tsx
const isConsecutiveMonth = (current: string, prior: string): boolean => {
  const [cy, cm] = current.split("-").map(Number);
  const [py, pm] = prior.split("-").map(Number);
  const expectedPriorMonth = cm === 1 ? 12 : cm - 1;
  const expectedPriorYear  = cm === 1 ? cy - 1 : cy;
  return py === expectedPriorYear && pm === expectedPriorMonth;
};
```

**Step 2**: After the existing `curr` / `prev` derivation, add:
```tsx
const hasValidComparison = prev !== null && isConsecutiveMonth(curr, prev);
```

**Step 3**: Wrap the existing comparison JSX (the `changes.map(...)` list) in a `hasValidComparison` guard. When `false`, render the gap notice instead:
```tsx
{hasValidComparison ? (
  <div className="space-y-0">
    {changes.map(({ cat, delta, prevAmt, currAmt }) => (
      // ... existing row JSX unchanged ...
    ))}
    <button ...>View all →</button>
  </div>
) : (
  <div className="py-4 text-center space-y-1">
    <p className="text-sm" style={{ color: "var(--text-sub)" }}>
      📅 Last tracked month was{" "}
      {new Date(prev + "-01").toLocaleString("en-IN", { month: "long", year: "numeric" })}.
    </p>
    <p className="text-xs" style={{ color: "var(--text-muted)" }}>
      Monthly comparisons work best with consecutive months.
    </p>
  </div>
)}
```

Note: this guard only applies to the 2+ prior months scenario (Scenario 1 in the code). The first-month fallback ("Spending Highlights") and single-prior-month path already have their own branches and are unchanged.

**Acceptance criteria**:
- Gap ≥ 2 calendar months between current and prior: comparison rows hidden, gap notice shown.
- Gap = 0 (consecutive months): existing behaviour completely unchanged.
- January → December year rollover handled correctly.
- No crash when `mom.months.length < 2` (existing first-month branch handles this).
