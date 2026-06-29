# Implementation Plan: Adaptive Insights — Sprint 12
**Spec**: `.claude/specs/12_adaptive-insights.md`
**Date**: 2026-06-27
**Branch**: new branch from `main` after spec 11 merges
**Prerequisite**: spec 11 W1 (gap detection) must be deployed before this sprint begins.
**Blocker** (2026-06-27): Spec 11 W1 is ⬜ pending — `isConsecutiveMonth` does not yet exist in `OverviewTab.tsx`. Do NOT start this sprint until W1 ships.

---

## Overview

8 items: 2 backend extensions, 1 type update, 4 scenario sub-components, 1 scenario selector + rename.
**2 items require backend work** (Items 1 and 2) — both are additive, no existing endpoints modified destructively.
**Items 4–7 can be built in parallel** once Items 1–3 are done.
**Item 8 (scenario selector + rename) must run last** — it wires everything together.

Open decisions resolved for this plan:

| Decision | Resolution |
|----------|-----------|
| `expense_count` location | Add to `/summary/{month_key}` response (simpler, no new endpoint) |
| Sparse tracking threshold | `< 10` distinct tracked days in prior month |
| Scenario D when current month also sparse | Neutral framing: "Keep logging expenses to build your financial picture." |
| Extract to own file? | Defer decision to implementation time — check `OverviewTab.tsx` line count first |
| "View all →" in Scenario B | Keep existing toast: "See all transactions in the History tab →" |

---

## ⚠️ Flags & Gaps

### Flag 1 — `isConsecutiveMonth` does NOT yet exist (W1 pending)
Spec 11 W1 was supposed to add `isConsecutiveMonth` to `OverviewTab.tsx` but W1 is still ⬜ pending as of 2026-06-27. At the start of this sprint, check whether W1 has shipped:
- If W1 is done: reuse `isConsecutiveMonth` from `OverviewTab.tsx` — do not redefine it.
- If W1 is not done: define `isConsecutiveMonth` in Item 8 (the scenario selector) before the IIFE, and skip the W1 gap-notice fallback (Scenario C already handles it better).

### Flag 2 — Existing "What Changed?" IIFE has three branches
The current code has three internal branches: first-month (< 2 months), single-prior-month (= 2 months), and multi-month (> 2 months). In spec 12 these map as: first-month → Scenario A, single-prior-month → Scenario B, multi-month → Scenario B.

**Intentional simplification**: The current single-prior-month branch shows ₹ delta only (no percentage). `InsightsScenarioB` uses `fmtMoM` for all cases, which will show percentages even on the first comparison month. This is an acceptable UX improvement — more informative, not a regression. Do not add a special branch for `mom.months.length === 2` inside `InsightsScenarioB`.

### Flag 3 — `func.distinct` in SQLAlchemy
The `days_tracked` query uses `func.count(func.distinct(Expense.date))`. Verify the exact SQLAlchemy import path in `main.py` — it may need `from sqlalchemy import func, distinct` and the syntax `func.count(distinct(Expense.date))` instead. Check before writing the query.

### Flag 4 — `summary.categories` shape for Scenario A and C
Both scenarios need the top spending category. Confirm `summary.categories` is an array sorted by `spent` descending, or sort it before slicing. Read the `/summary/{month_key}` endpoint response shape before building the sub-components.

### Flag 5 — `expense_count` field name collision
Before adding `expense_count` to the summary response, search `main.py` for any existing field by that name in the summary dict. If it already exists under a different name (e.g. `total_expenses`), use that instead of adding a duplicate.

### Flag 6 — `OverviewTab.tsx` line count — decision already made
`OverviewTab.tsx` is currently ~1,100 lines (verified 2026-06-27), well above the 700-line threshold. **Scenario sub-components (Items 4–7) must be placed in a new file: `frontend/react/src/components/shared/InsightsSection.tsx`.** Do not keep them inline. Item 8 imports them from there.

---

## Item 1 — Add `expense_count` to `/summary/{month_key}`
**Spec ref**: Backend change 1
**Scope**: Backend-only
**Files**: `backend/main.py`

**Pre-check**: Search for any existing `expense_count` or `total_expenses` field in the summary response (Flag 5). If it already exists, skip this item and note the actual field name for Item 4.

**What to do**:

Locate the summary computation function (the one that builds the dict returned by `GET /summary/{month_key}`). Add the expense count query:

```python
expense_count = db.query(func.count(Expense.id)).filter(
    Expense.user_id == user_id,
    Expense.date.startswith(month_key)
).scalar() or 0
```

Add `"expense_count": expense_count` to the returned dict.

Do NOT change any existing fields — this is purely additive.

**Acceptance criteria**:
- `GET /summary/2026-06` response includes `"expense_count": <int>`.
- Value is 0 for a month with no expenses (not null, not omitted).
- All existing summary fields unchanged.
- No Python errors.

---

## Item 2 — Add `days_tracked` to `/insights/mom/{month_key}`
**Spec ref**: Backend change 2
**Scope**: Backend-only
**Files**: `backend/main.py`

**Pre-check**: Read the MoM endpoint to understand how `months_in_window` is computed. Confirm the exact SQLAlchemy import style used in the file (Flag 3).

**What to do**:

Inside the MoM endpoint, after `months_in_window` is established, compute distinct tracked days per month:

```python
from sqlalchemy import distinct  # add if not already imported

days_tracked = {}
for m in months_in_window:
    count = db.query(func.count(distinct(Expense.date))).filter(
        Expense.user_id == user_id,
        Expense.date.startswith(m)
    ).scalar() or 0
    days_tracked[m] = count
```

Add `"days_tracked": days_tracked` to the returned dict.

**Acceptance criteria**:
- `GET /insights/mom/2026-06` response includes `"days_tracked": { "2026-05": 22, "2026-06": 18, ... }`.
- Keys match the `months` array exactly.
- Value is 0 for months with no expenses.
- All existing MoM fields unchanged.
- No Python errors.

---

## Item 3 — Update `Summary` and `MoMData` TypeScript types
**Spec ref**: Backend change 3
**Scope**: Frontend-only
**Files**: `frontend/react/src/types/index.ts`

**Pre-check**: Read the full `types/index.ts` to see current `Summary` and `MoMData` interfaces before editing.

**What to do**:

```typescript
// In Summary interface — add:
expense_count?: number;

// In MoMData interface — add:
days_tracked: Record<string, number>;
```

Both fields are optional (`?`) on `Summary` to avoid breaking existing months where the backend hasn't redeployed yet. `days_tracked` on `MoMData` is required since the backend always returns it after Item 2 deploys.

**Acceptance criteria**:
- `tsc --noEmit` passes with no new errors.
- Existing type usages unchanged.

---

## Item 4 — Scenario A: Onboarding Insights sub-component
**Spec ref**: Scenario A
**Scope**: Frontend-only
**Files**: `OverviewTab.tsx` (or `InsightsSection.tsx` — see Flag 6)

**Pre-check**: Confirm `summary.categories` is sorted by `spent` descending (Flag 4). Confirm `expense_count` field name from Item 1.

**What to do**:

Create `InsightsScenarioA` as either an inline function component or an exported component:

```tsx
function InsightsScenarioA({ summary }: { summary: Summary }) {
  const totalSpent = summary.categories.reduce((s, c) => s + c.spent, 0);
  const top = [...summary.categories].sort((a, b) => b.spent - a.spent)[0];
  const topPct = totalSpent > 0 && top
    ? Math.round(top.spent / totalSpent * 100)
    : null;
  const expenseCount = summary.expense_count ?? null;

  return (
    <div
      className="rounded-2xl border p-4 space-y-3"
      style={{ background: "var(--card)", borderColor: "var(--border-lg)" }}
    >
      <p
        className="text-[10px] font-syne font-bold uppercase tracking-widest"
        style={{ color: "var(--accent)" }}
      >
        Your first month 🎉
      </p>
      <div className="space-y-2">
        {expenseCount !== null && (
          <p className="text-sm" style={{ color: "var(--text)" }}>
            📝 You've logged{" "}
            <span className="font-semibold">{expenseCount} expenses</span> so far.
          </p>
        )}
        {top && topPct !== null && (
          <p className="text-sm" style={{ color: "var(--text)" }}>
            🏷️ <span className="font-semibold">{top.category}</span> accounts for{" "}
            <span className="font-semibold">{topPct}%</span> of your spending.
          </p>
        )}
        <p className="text-sm" style={{ color: "var(--text-sub)" }}>
          📅 Continue tracking to unlock monthly comparisons next month.
        </p>
      </div>
    </div>
  );
}
```

**Acceptance criteria**:
- Renders when `mom.months.length < 2`.
- Shows expense count when available; omits the line when null.
- Shows top category + percentage when categories exist; omits when empty.
- Encouragement line always present.
- No comparison language anywhere in the output.

---

## Item 5 — Scenario B: MoM Comparison sub-component (refactor existing)
**Spec ref**: Scenario B
**Scope**: Frontend-only
**Files**: `OverviewTab.tsx` (or `InsightsSection.tsx`)

**Pre-check**: Read the current What Changed? IIFE carefully. Identify all three internal branches (first-month, single-prior, multi-month) — Flag 2. Only the multi-month branch becomes Scenario B. The other two become Scenarios A and C/D and are handled by the selector in Item 8.

**What to do**:

Extract the **multi-month branch only** of the current What Changed? IIFE into `InsightsScenarioB`:

```tsx
function InsightsScenarioB({
  mom, summary, curr, prev, onViewAll
}: {
  mom: MoMData;
  summary: Summary;
  curr: string;
  prev: string;
  onViewAll: () => void;
}) {
  const SAVINGS_CATS = new Set(["Savings", "Investments"]);
  const prevLabel = new Date(prev + "-01").toLocaleString("en-IN", { month: "short" });

  const fmtMoM = (rawPct: number | null, prevAmt: number): string => {
    if (prevAmt === 0) return "New this month";
    if (rawPct === null) return "—";
    if (Math.abs(rawPct) > 300) return rawPct > 0 ? "↑ New high" : "↓ Major drop";
    return `${rawPct > 0 ? "↑" : "↓"} ${Math.abs(Math.round(rawPct))}%`;
  };

  const changes = Object.entries(mom.categories)
    .map(([cat, byMonth]) => ({
      cat,
      currAmt: byMonth[curr] ?? 0,
      prevAmt: byMonth[prev] ?? 0,
      delta:   (byMonth[curr] ?? 0) - (byMonth[prev] ?? 0),
    }))
    .filter(c => c.prevAmt > 0 || c.currAmt > 0)
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
    .slice(0, 4);

  if (changes.length === 0) return null;

  return (
    <div className="space-y-0">
      {changes.map(({ cat, delta, prevAmt, currAmt }) => {
        const isUp = delta > 0;
        const isSavingsCat = SAVINGS_CATS.has(cat);
        const isPositive = isSavingsCat ? isUp : !isUp;
        const dotColour = isPositive ? "#34d399" : "#f87171";
        const rawPct = prevAmt > 0 ? Math.round((delta / prevAmt) * 100) : null;
        const momStr = fmtMoM(rawPct, prevAmt);
        const label = prevAmt === 0 ? momStr : `${momStr} (${fmtInr(Math.abs(delta))})`;

        return (
          <div key={cat} className="flex items-center gap-3 py-2.5 border-b"
               style={{ borderColor: "var(--border-lg)" }}>
            <span className="text-lg w-5 flex-shrink-0 text-center" style={{ color: dotColour }}>
              {isUp ? "↑" : "↓"}
            </span>
            <span className="flex-1 text-sm" style={{ color: "var(--text)" }}>{cat}</span>
            <div className="text-right">
              <span className="text-sm font-syne font-semibold" style={{ color: dotColour }}>
                {label}
              </span>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                {fmtInr(currAmt)} this month
              </p>
            </div>
          </div>
        );
      })}
      <button
        onClick={onViewAll}
        className="text-xs mt-2 w-full text-right transition-opacity hover:opacity-70"
        style={{ color: "var(--accent)" }}
      >
        View all →
      </button>
    </div>
  );
}
```

The `fmtMoM` formatter already exists in the current code from spec 11 P2 — reuse it, don't duplicate.

**Acceptance criteria**:
- All existing MoM row behaviour preserved exactly (↑/↓ deltas, "New this month", "New high", "Major drop").
- "View all →" fires the existing toast.
- No regressions from the refactor — output is pixel-identical to the current multi-month branch.

---

## Item 6 — Scenario C: Gap Notice + Spending Highlights sub-component
**Spec ref**: Scenario C
**Scope**: Frontend-only
**Files**: `OverviewTab.tsx` (or `InsightsSection.tsx`)

**What to do**:

```tsx
function InsightsScenarioC({
  summary, prev
}: {
  summary: Summary;
  prev: string;
}) {
  const prevLabel = new Date(prev + "-01")
    .toLocaleString("en-IN", { month: "long", year: "numeric" });
  const top3 = [...summary.categories]
    .sort((a, b) => b.spent - a.spent)
    .slice(0, 3);

  return (
    <div className="space-y-3">
      {/* Gap notice */}
      <div
        className="rounded-2xl border p-4"
        style={{ background: "var(--card)", borderColor: "var(--border-lg)" }}
      >
        <p className="text-sm font-medium" style={{ color: "var(--text-sub)" }}>
          📅 Last tracked: <span style={{ color: "var(--text)" }}>{prevLabel}</span>
        </p>
        <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
          Monthly comparisons work best with consecutive months.
        </p>
      </div>

      {/* Current month top spending */}
      {top3.length > 0 && (
        <div>
          <p
            className="text-[10px] font-syne font-bold uppercase tracking-widest mb-2"
            style={{ color: "var(--text-sub)" }}
          >
            This month's top spending
          </p>
          <div className="space-y-0">
            {top3.map(c => (
              <div key={c.category} className="flex items-center gap-3 py-2.5 border-b"
                   style={{ borderColor: "var(--border-lg)" }}>
                <span className="text-lg w-5 flex-shrink-0 text-center">
                  {CATEGORY_ICONS[c.category] ?? "📦"}
                </span>
                <span className="flex-1 text-sm" style={{ color: "var(--text)" }}>
                  {c.category}
                </span>
                <span className="text-sm font-syne font-semibold" style={{ color: "var(--text)" }}>
                  {fmtInr(c.spent)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
```

This replaces the spec 11 W1 gap notice (which was text-only) with a richer version that adds top-3 category rows.

**Acceptance criteria**:
- Gap notice shows the last tracked month name + year.
- Top 3 categories shown below when `summary.categories` is non-empty.
- No MoM comparison rows rendered.
- No crash when `summary.categories` is empty.

---

## Item 7 — Scenario D: Tracking Quality sub-component
**Spec ref**: Scenario D
**Scope**: Frontend-only
**Files**: `OverviewTab.tsx` (or `InsightsSection.tsx`)

**What to do**:

```tsx
function InsightsScenarioD({
  currDays, prevDays
}: {
  currDays: number;
  prevDays: number;
}) {
  const bothSparse = currDays < 10 && prevDays < 10;

  return (
    <div
      className="rounded-2xl border p-4 space-y-2"
      style={{ background: "var(--card)", borderColor: "var(--border-lg)" }}
    >
      {bothSparse ? (
        <p className="text-sm" style={{ color: "var(--text-sub)" }}>
          Keep logging expenses to build your financial picture.
        </p>
      ) : (
        <>
          <div className="flex items-center justify-between">
            <p className="text-sm" style={{ color: "var(--text-sub)" }}>
              📊 Tracked this month
            </p>
            <p className="text-sm font-syne font-semibold" style={{ color: "var(--text)" }}>
              {currDays} days
            </p>
          </div>
          <div className="flex items-center justify-between">
            <p className="text-sm" style={{ color: "var(--text-sub)" }}>
              Last month
            </p>
            <p className="text-sm font-syne font-semibold" style={{ color: "#f59e0b" }}>
              {prevDays} days
            </p>
          </div>
          <p className="text-xs pt-1" style={{ color: "var(--text-muted)" }}>
            Monthly comparisons become more accurate with consistent daily tracking.
          </p>
        </>
      )}
    </div>
  );
}
```

**Acceptance criteria**:
- Shows when prior month is consecutive but `prevDays < 10`.
- When both current and prior are sparse: shows neutral encouragement only.
- When only prior is sparse: shows day counts for both months + explanation.
- No MoM category rows rendered.

---

## Item 8 — Scenario selector + heading rename (wire-up, must run last)
**Spec ref**: Frontend — Scenario Selector
**Scope**: Frontend-only
**Files**: `OverviewTab.tsx`
**Depends on**: Items 1–7 all complete

**Pre-check**:
1. Check whether spec 11 W1 shipped (Flag 1): if `isConsecutiveMonth` exists in `OverviewTab.tsx`, reuse it; if not, define it here before the IIFE.
2. Confirm Items 4–7 sub-components are in `InsightsSection.tsx` and TypeScript-clean (Flag 6 — extraction is mandatory, not optional).
3. Verify Items 4–7 render correctly in isolation before wiring up the selector.

**What to do**:

**Step 1**: Remove the entire existing What Changed? IIFE (`mom && (() => { ... })()`). All three branches inside it are now handled by sub-components.

**Step 2**: Replace with the scenario selector:

```tsx
{/* ── Section 9: 💡 Insights ─────────────────────── */}
{mom && (() => {
  const curr = mom.months[mom.months.length - 1];
  const prev = mom.months.length >= 2 ? mom.months[mom.months.length - 2] : null;
  const isFirstMonth    = !prev;
  const isConsecutive   = prev ? isConsecutiveMonth(curr, prev) : false;
  const currDaysTracked = mom.days_tracked?.[curr] ?? 0;
  const prevDaysTracked = prev ? (mom.days_tracked?.[prev] ?? 0) : 0;
  const isQualityData   = prevDaysTracked >= 10;

  const scenario =
    isFirstMonth                   ? "A" :
    isConsecutive && isQualityData ? "B" :
    isConsecutive                  ? "D" :
    "C";

  return (
    <section>
      <div className="flex items-center justify-between mb-3">
        <h2
          className="text-xs font-syne font-bold tracking-widest"
          style={{ color: "var(--text-sub)" }}
        >
          💡 Insights
        </h2>
        {scenario === "B" && prev && (
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>
            vs {new Date(prev + "-01").toLocaleString("en-IN", { month: "short" })}
          </span>
        )}
      </div>

      {scenario === "A" && <InsightsScenarioA summary={summary} />}
      {scenario === "B" && prev && (
        <InsightsScenarioB
          mom={mom}
          summary={summary}
          curr={curr}
          prev={prev}
          onViewAll={() => toast("See all transactions in the History tab →")}
        />
      )}
      {scenario === "C" && prev && <InsightsScenarioC summary={summary} prev={prev} />}
      {scenario === "D" && (
        <InsightsScenarioD currDays={currDaysTracked} prevDays={prevDaysTracked} />
      )}
    </section>
  );
})()}
```

**Step 3**: Search the codebase for any remaining `"What changed?"` / `"WHAT CHANGED?"` / `"📊 What changed?"` strings and remove them. The section comment (`// ── Section 9`) should be updated to read `// ── Section 9: 💡 Insights`.

**Step 4**: If `"📊"` was added to the heading in spec 11 P3, it is now superseded by `"💡"` — the old string will be gone since the entire IIFE was replaced. Confirm no orphaned `"📊 What changed?"` string remains.

**Acceptance criteria**:
- Exactly one of A/B/C/D renders depending on data state.
- Scenario B: all existing MoM rows render identically to before.
- Scenario A: onboarding card renders for first-month users.
- Scenario C: gap notice + top-3 categories renders for gap users.
- Scenario D: tracking quality card renders for sparse-prior-month users.
- "What changed?" heading string absent from the codebase.
- Section comment updated.
- TypeScript build clean (`tsc --noEmit`).
- No crash on any null/empty data combination.

---

## Execution Summary

| Item | Spec ref | Scope | Effort | Depends on | Status |
|------|----------|-------|--------|------------|--------|
| 1 | Backend: `expense_count` on summary | Backend | XS | Flag 5 | ⬜ |
| 2 | Backend: `days_tracked` on MoM | Backend | S | Flag 3 | ⬜ |
| 3 | Types: `Summary` + `MoMData` | Frontend | XS | Items 1, 2 | ⬜ |
| 4 | Scenario A — Onboarding | Frontend | S | Item 3, Flag 4, Flag 6 | ⬜ |
| 5 | Scenario B — MoM refactor | Frontend | S | Item 3, Flag 2 | ⬜ |
| 6 | Scenario C — Gap + Highlights | Frontend | S | Item 3, Flag 4 | ⬜ |
| 7 | Scenario D — Tracking Quality | Frontend | S | Item 3 | ⬜ |
| 8 | Scenario selector + rename | Frontend | S | Items 4–7, Flag 1, Flag 6 | ⬜ |
