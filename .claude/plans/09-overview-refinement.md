# Implementation Plan: Overview Tab Refinement — Sprint 09
**Spec**: `.claude/specs/09_overview-refinement.md`
**Date**: 2026-06-25
**Branch**: `feature/sprint06261-ui-enhancement`

---

## Overview

5 executable items (R4 dropped per spec; R6 is a one-line comment, so folded into Item 1).
**1 item requires a backend change** (Item 3 — `savings_total` in `get_balance_summary`).
Items are ordered smallest-blast-radius-first. R1 and R2 have no dependency on each other; R3 (section reorder) must come last.

**Start with: Item 1 (R6 comment) — trivial, zero risk, sets the marker for deferred work.**

---

## ⚠️ Flags & Gaps

### Flag 1 — Top Spends section not in spec R3 order
The spec's R3 section order (10 items) does not include "Top Spends This Month" (currently `Section 4`, lines 387–402 of `OverviewTab.tsx`). R3 says the new order "replaces spec 08's recommended order" — the top-5 transactions list is omitted.

**Plan assumes: retain Top Spends after Spend by Category (position between 4 and 5) unless the spec author explicitly says to drop it.** Flag before executing R3 (Item 5).

### Flag 2 — `spent_by_cat` in OverviewTab
`OverviewTab` fetches `summary.categories` (array of `{ category, spent }`) but does not derive a `spent_by_cat` map directly. For R2 Scenario 2 and R5 Category Winner, derive locally: `const spentByCat = Object.fromEntries(summary.categories.map(c => [c.category, c.spent]))`.

---

## Item 1 — R6: Add deferred Insight row TODO comment
**Scope**: Frontend-only
**Files**: `frontend/react/src/components/tabs/OverviewTab.tsx` — line 327

**Root cause**: Spec R6 defers a "Variable spending consumed X% of income this month. Average over last 6 months is Y%" insight row below the `BalanceBreakdown` bar. No backend query exists for 6-month historical aggregation. The spec only asks for a marker comment so the next sprint can locate the insertion point.

**What to do**:
After line 327 (`<BalanceBreakdown balance={balance} />`), add one comment line:
```tsx
{/* TODO: Insight row — see spec 09 R6, deferred (needs 6-month variable_total avg endpoint) */}
```

Full section after change:
```tsx
{/* ── Section 1: Monthly breakdown bar ───────────── */}
<section>
  <BalanceBreakdown balance={balance} />
  {/* TODO: Insight row — see spec 09 R6, deferred (needs 6-month variable_total avg endpoint) */}
</section>
```

**Acceptance criteria**:
- Comment present in source immediately after `<BalanceBreakdown>`.
- No visible change in the rendered UI.

---

## Item 2 — R2: Scenario-aware "What Changed?" rendering
**Scope**: Frontend-only
**Files**: `frontend/react/src/components/tabs/OverviewTab.tsx` — lines 600–678

**Root cause**: Current code at line 601 — `{mom && mom.months.length >= 2 && (() => {` — renders nothing for first-month users and always shows percentage changes even when `prevAmt === 0` (only guarded by `pct != null` which suppresses the % but still shows the arrow). Users with exactly one prior month see percentage changes that can be misleading ("+272%"). Three scenarios are needed.

**Current What Changed? guard (line 601):**
```tsx
{mom && mom.months.length >= 2 && (() => {
  const curr = mom.months[mom.months.length - 1];
  const prev = mom.months[mom.months.length - 2];
  ...
  const label = pct != null
    ? `${icon} ${pct}% (${fmtInr(Math.abs(delta))})`
    : `${icon} ${fmtInr(Math.abs(delta))}`;
  ...
```

**What to do**: Replace the entire What Changed? block (lines 600–678) with a single `{mom && (() => {...})()}` wrapper that branches on `mom.months.length` inside.

### Scenario 2 branch (`mom.months.length < 2`) — spending highlights, no arrows or %:
```tsx
if (mom.months.length < 2) {
  const highlights = [...summary.categories]
    .filter(c => c.spent > 0)
    .sort((a, b) => b.spent - a.spent)
    .slice(0, 3);
  if (highlights.length === 0) return null;
  return (
    <section>
      <h2 className="text-xs font-syne font-bold uppercase tracking-widest mb-1"
          style={{ color: "var(--text-sub)" }}>
        Spending Highlights
      </h2>
      <p className="text-xs mb-3" style={{ color: "var(--text-muted)" }}>
        Your first month — no prior comparison yet
      </p>
      <div className="space-y-0">
        {highlights.map(({ category, spent }) => (
          <div key={category} className="flex items-center gap-3 py-2.5 border-b"
               style={{ borderColor: "var(--border-lg)" }}>
            <span className="text-lg w-5 flex-shrink-0 text-center">
              {CATEGORY_ICONS[category] ?? "📦"}
            </span>
            <span className="flex-1 text-sm" style={{ color: "var(--text)" }}>
              {category}
            </span>
            <span className="text-sm font-syne font-semibold"
                  style={{ color: "var(--text)" }}>
              {fmtInr(spent)}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
```

### Scenario 3 branch (`mom.months.length === 2`) — ₹ delta, no %, new-category label:
Same structure as current but:
- `curr = mom.months[1]`, `prev = mom.months[0]`
- Label: `currAmt > 0 && prevAmt === 0 ? "New this month" : \`${icon} ${fmtInr(Math.abs(delta))}\``  (no `pct` at all)
- `"vs ${prevLabel}"` subtitle unchanged
- Colour/direction logic unchanged (SAVINGS_CATS inversion kept)

### Scenario 1 branch (`mom.months.length >= 3`) — full view, same as current:
- `curr = mom.months[mom.months.length - 1]`, `prev = mom.months[mom.months.length - 2]`
- Label: `pct != null ? \`${icon} ${pct}% (${fmtInr(Math.abs(delta))})\` : \`${icon} ${fmtInr(Math.abs(delta))}\`` — unchanged
- All existing colour, direction, SAVINGS_CATS logic unchanged
- Keep `"View all →"` toast button

**Acceptance criteria**:
- `mom.months.length < 2`: shows "Spending Highlights" heading, top 3 categories by spend, no arrows or percentages.
- `mom.months.length === 2`: shows "What Changed?" heading, ₹ delta only; categories new this month show "New this month" instead of a delta.
- `mom.months.length >= 3`: existing behaviour with % unchanged.
- SAVINGS_CATS (Savings/Investments) colour inversion untouched across all scenarios.

---

## Item 3 — R1 (Backend): Add `savings_total` to `get_balance_summary()`
**Scope**: Backend-only
**Files**:
- `backend/budget_rules.py` — lines 113–137 (`get_balance_summary` variable block and return dict)
- `frontend/react/src/types/index.ts` — lines 81–88 (`Summary.balance` shape)

**Root cause**: `get_balance_summary()` currently computes `variable_total = sum(e.amount for e in variable)` (line 120) but does not break out savings/investments separately. The Savings signal in R1's redesigned Financial Pulse needs `savings_total / total_income` to compute the protection ratio. The type `Summary.balance` (lines 81–88 of `types/index.ts`) does not include `savings_total`.

**What to do**:

### `backend/budget_rules.py` — after line 120:
```python
# current:
variable_total = sum(e.amount for e in variable)

# add:
savings_total  = sum(e.amount for e in variable
                     if e.category in ("Savings", "Investments"))
```

### `backend/budget_rules.py` — return dict, add one key after `variable_total`:
```python
# add:
"savings_total":   savings_total,
```

### `frontend/react/src/types/index.ts` — extend `Summary.balance`:
```typescript
// current:
balance: {
  remaining: number;
  total_income: number;
  fixed_paid_total: number;
  fixed_unpaid_total: number;
  variable_total: number;
};

// after:
balance: {
  remaining: number;
  total_income: number;
  fixed_paid_total: number;
  fixed_unpaid_total: number;
  variable_total: number;
  savings_total?: number;   // add
};
```

Use `?` because older cached responses may not include this field.

**Acceptance criteria**:
- `/summary/{month_key}` response `balance` object includes `savings_total` as a numeric value.
- Users with no Savings/Investments expenses return `savings_total: 0`.
- TypeScript build clean.

---

## Item 4 — R1 (Frontend): Redesign Financial Pulse as compact list
**Scope**: Frontend-only (depends on Item 3 for `balance.savings_total`)
**Files**: `frontend/react/src/components/tabs/OverviewTab.tsx` — lines 404–523 (Financial Pulse section)

**Root cause**: Current Financial Pulse renders a 2×2 grid of tile cards (4 tiles: Bills, Food, Spending, Tracking), with coloured dot + signal name + 1-word status + sub-label per tile. The spec replaces this with a single card containing a vertical list of 3–4 signal lines (icon + signal name | status copy). Data sources are similar but signals are renamed and thresholds revised.

**Existing data computations to reuse** (currently inside the Financial Pulse IIFE):
- `daysElapsed`, `isCurrentMonth`, `daysInMonth` — unchanged
- `foodCurr`, `foodPrev`, `foodPct` — unchanged logic
- `dailyRate`, `prevDailyRate`, `pacePct` — unchanged logic

**New signal definitions**:

| Signal | Icon | Status thresholds |
|--------|------|-------------------|
| Stability | 🛡️ | `unpaidFrac = fixed_unpaid / (fixed_paid + fixed_unpaid)` — `=== 0` → green "Fixed obligations complete"; `< 0.30` → amber "Bills nearly complete"; `>= 0.30` → red "Fixed obligations pending" |
| Lifestyle | 🔥 | Combine `foodPct` and `pacePct`: both ≤ 100% → green "Spending pace normal"; food 100–130% OR pace 100–130% → amber "Food/Spending above normal"; either > 130% → red "Spending accelerated this month". When no prior data (`foodPct == null && pacePct == null`) → neutral "#94a3b8" "No prior data to compare" |
| Savings | 🐷 | `savingsPct = (balance.savings_total ?? 0) / balance.total_income * 100` — ≥ 20% → green "X% of income protected" (substitute actual number); 10–20% → amber "Savings moderate this month"; < 10% → red "Savings below target". When `total_income === 0` → neutral "–" |
| Consistency | 🎯 | Always green — "Tracked expenses on X days this month" where `X = new Date().getDate()`. Comment: `// TODO: replace with real streak` |

**Layout change — replace 2×2 grid with single card + vertical list**:

```tsx
return (
  <section>
    <h2 className="text-xs font-syne font-bold uppercase tracking-widest mb-3"
        style={{ color: "var(--text-sub)" }}>
      Financial Pulse
    </h2>
    <div className="rounded-2xl border p-4 space-y-4"
         style={{ background: "var(--card)", borderColor: "var(--border-lg)" }}>
      {signals.map(s => (
        <div key={s.name} className="flex items-center gap-3">
          <span className="text-xl w-8 flex-shrink-0 text-center">{s.icon}</span>
          <span className="text-sm flex-1" style={{ color: "var(--text-sub)" }}>
            {s.name}
          </span>
          <span className="text-sm font-syne font-semibold text-right"
                style={{ color: s.colour }}>
            {s.label}
          </span>
        </div>
      ))}
    </div>
  </section>
);
```

The `signals` array replaces the old 4-tile array. Build it in the same IIFE before the return.

**Colour constants**:
- Green: `"#34d399"`, Amber: `"#f59e0b"`, Red: `"#f87171"`, Neutral: `"#94a3b8"`

**Acceptance criteria**:
- Financial Pulse is a single card with 4 rows (not a 2×2 grid).
- Stability uses `fixed_unpaid_total / (fixed_paid_total + fixed_unpaid_total)` thresholds.
- Lifestyle combines food and spending pace into one signal.
- Savings uses `balance.savings_total ?? 0`.
- Consistency shows `new Date().getDate()` with `// TODO: replace with real streak` comment.
- TypeScript build clean (`balance.savings_total` must be accessed as optional).

---

## Item 5 — R5: Category Winner tile
**Scope**: Frontend-only
**Files**: `frontend/react/src/components/tabs/OverviewTab.tsx` — insert after line 367 (end of `</SpendDonut>` block, inside the `summary.categories.length > 0` guard's section)

**Root cause**: No Category Winner tile exists. Data is available: `summary.categories` for top category by spend, `balance.variable_total` for % of variable, `mom` for MoM comparison.

**What to do**: After the `</SpendDonut>` closing tag (line 366), still inside the same `<section>`, add:

```tsx
{/* Category Winner */}
{(() => {
  const varCats = summary.categories.filter(c => !FIXED_CATEGORIES.includes(c.category));
  if (varCats.length === 0) return null;
  const top = [...varCats].sort((a, b) => b.spent - a.spent)[0];
  const pctOfVar = balance.variable_total > 0
    ? Math.round(top.spent / balance.variable_total * 100)
    : 0;
  const curr = mom?.months[mom.months.length - 1];
  const prev = mom && mom.months.length >= 2 ? mom.months[mom.months.length - 2] : null;
  const topCurr = curr ? (mom?.categories[top.category]?.[curr] ?? 0) : 0;
  const topPrev = prev ? (mom?.categories[top.category]?.[prev] ?? 0) : 0;
  const momPct = topPrev > 0 ? Math.round((topCurr - topPrev) / topPrev * 100) : null;
  const momLabel = momPct === null
    ? "First month"
    : momPct >= 0 ? `↑ +${momPct}% vs last month` : `↓ ${Math.abs(momPct)}% vs last month`;

  return (
    <div className="mt-4 rounded-2xl border p-4 flex items-center gap-4"
         style={{ background: "var(--card)", borderColor: "var(--border-lg)" }}>
      <span className="text-2xl flex-shrink-0" style={{ color: "#f59e0b" }}>🏆</span>
      <div className="flex-1 min-w-0">
        <p className="text-[10px] font-syne font-bold uppercase tracking-widest mb-0.5"
           style={{ color: "var(--text-sub)" }}>
          Top Category
        </p>
        <p className="text-base font-syne font-bold" style={{ color: "var(--text)" }}>
          {top.category}
        </p>
        <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
          {pctOfVar}% of variable spend · {momLabel}
        </p>
      </div>
      <p className="font-syne font-bold text-sm flex-shrink-0"
         style={{ color: "#f87171" }}>
        {fmtInr(top.spent)}
      </p>
    </div>
  );
})()}
```

**Note**: The Category Winner is inside the same `{summary.categories.length > 0 && (...)}` section as the donut, so it hides automatically when there are no categories.

**Acceptance criteria**:
- Shows top variable spending category, its amount, `% of variable spend`, and MoM % change.
- When `mom.months.length < 2` (or no prior month data), shows "First month" for MoM.
- Trophy icon (🏆) in amber (`#f59e0b`), category name in `font-syne font-bold`.
- Only considers non-fixed categories (uses `FIXED_CATEGORIES` filter).

---

## Item 6 — R3: Section reorder
**Scope**: Frontend-only
**Files**: `frontend/react/src/components/tabs/OverviewTab.tsx` — full JSX reorder (no logic changes)
**Depends on**: Items 2 (R2) and 4 (R1) complete

**Root cause**: Current section order diverges from the spec R3 mockup order. Specifically:
- Peace of Mind (Section 0c, lines 264–323) is currently in position 3 but should be in position 8.
- BalanceBreakdown (Section 1, lines 325–328) is currently in position 4 but should be position 3.
- Budget Health (Section 3, lines 370–385) is currently in position 6 but should be position 9.
- Top Spends (Section 4, lines 387–402) is not in the spec's new order — see ⚠️ Flag 1.

**Target section order** (per spec R3):
```
1.  Financial Snapshot (lines 192–247)            ← unchanged
2.  This Month's Story (lines 249–262)            ← unchanged
3.  BalanceBreakdown bar + R6 TODO (lines 325–328) ← move up from pos 4
4.  Spend by Category donut + Category Winner      ← move up from pos 5 + R5 added
5.  Financial Pulse compact list (R1 redesign)     ← move up from pos 8
6.  Upcoming Reality (lines 525–598)              ← unchanged
7.  What Changed? scenario-aware (R2)              ← unchanged
8.  Peace of Mind Score (lines 264–323)            ← move down from pos 3
9.  Budget Health (lines 370–385)                 ← move down from pos 6
10. Tiny Win (lines 680–701)                      ← unchanged
```

**Top Spends decision**: Confirm with spec author whether to keep or drop. If kept, insert between items 4 and 5 (after Category Winner, before Financial Pulse). If dropped, remove the section entirely.

**What to do**: Cut-and-paste the JSX blocks into target order. No JSX content changes — just resequencing. After reorder, update the `// ── Section N:` comments to match new positions.

Exact operations (assuming Top Spends is retained):
1. Cut Peace of Mind block (currently 0c) from between Story and BalanceBreakdown.
2. Paste Peace of Mind after What Changed? (new position 8).
3. BalanceBreakdown naturally moves to position 3 (was pushed down by Peace of Mind being above it).
4. Cut Budget Health block (currently Section 3).
5. Paste Budget Health after Peace of Mind (new position 9).
6. If Top Spends is retained: move it to between Category Winner and Financial Pulse.

**Acceptance criteria**:
- Rendered section order matches spec R3 list.
- No section accidentally removed (count sections before and after reorder).
- BalanceBreakdown is followed by R6 TODO comment (from Item 1).
- TypeScript build clean.

---

## Execution Summary

| Item | Spec issue | Scope | Effort | Depends on |
|------|-----------|-------|--------|------------|
| 1 | R6 — Deferred TODO comment | Frontend | XS | — |
| 2 | R2 — Scenario-aware What Changed? | Frontend | S | — |
| 3 | R1 backend — `savings_total` | Backend + Types | S | — |
| 4 | R1 frontend — Financial Pulse compact | Frontend | M | Item 3 |
| 5 | R5 — Category Winner tile | Frontend | S | — |
| 6 | R3 — Section reorder | Frontend | XS | Items 2, 4 |
