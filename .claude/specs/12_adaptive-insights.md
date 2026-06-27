# Spec: Adaptive Insights — Replace "What Changed?" with "💡 Insights"
**Date**: 2026-06-27
**Status**: 🔴 Blocked — spec 11 W1 (gap detection) is a prerequisite and is not yet shipped
**Branch**: new branch from `main` after spec 11 merges
**Follows**: `11_overview-review-fixes.md` — spec 11 W1 (gap detection) is a prerequisite.
**Blocker** (2026-06-27): Spec 11 W1 is still ⬜ pending. `isConsecutiveMonth` does not yet exist in `OverviewTab.tsx`. Spec 12 cannot begin until W1 is complete and merged.
**Source**: `Wallet_Mantra_Adaptive_Insights_Recommendation.md` (2026-06-27)

---

## Context

The current "What Changed?" section is a comparison-only component — it has exactly one mode. It only delivers value to users with consecutive monthly data, which excludes:
- First-time users (no prior month)
- Users returning after a gap (non-consecutive months)
- Users with sparse tracking (low days-tracked in prior month)

Spec 11 W1 added a gap-detection guard to prevent misleading comparisons. This spec replaces the entire section with a **scenario-aware "💡 Insights" engine** that always has something meaningful to show, regardless of data maturity.

---

## Product Decision

**Rename**: "What Changed?" → "💡 Insights"

This rename signals a different contract to the user: the section is no longer purely comparative — it is personalised and adaptive. The rename should land together with the full scenario engine, not before.

**Section heading icon**: 💡 (replaces 📊 assigned in spec 11 P3 — update the heading in `OverviewTab.tsx` when this spec is implemented)

---

## Scenario Engine

The section renders exactly one of four scenarios, evaluated in priority order:

```
IF first month (no prior data)         → Scenario A: Onboarding Insights
ELSE IF prior month is consecutive     → Scenario B: Month-over-Month Comparison  (existing logic)
ELSE IF prior month exists but gap ≥ 2 → Scenario C: Gap + Spending Highlights
ELSE IF tracking quality is low        → Scenario D: Tracking Quality Insight
```

Scenario B is the existing "What Changed?" behaviour, preserved intact. Scenarios A, C, D are new.

---

## Scenario A — Onboarding Insights (first month)

**Trigger**: `mom.months.length < 2` (no prior recorded month at all)

**Current behaviour**: Shows "Spending Highlights" — top 3 categories by spend with no context. Functional but not engaging.

**New behaviour**: Replace with a richer onboarding card:

```
💡 Insights
Your first month →                          [encourage label]

• You've logged {expenseCount} expenses so far.
• {topCategory} accounts for {topCatPct}% of your spending.
• Continue tracking to unlock monthly comparisons next month.
```

**Data needed (all frontend-derivable)**:
- `expenseCount`: not currently in scope — requires either a count from the summary API or a separate fetch. **Option**: add `expense_count: int` to the existing `/summary/{month_key}` response (small backend change).
- `topCategory` + `topCatPct`: already available from `summary.categories`.

**Design**: single card, no list rows, friendly tone. No section subheading ("vs May" etc.).

---

## Scenario B — Month-over-Month Comparison (consecutive prior month)

**Trigger**: prior month exists AND `isConsecutiveMonth(curr, prev)` is true AND tracking quality is sufficient (see Scenario D).

**Behaviour**: Existing "What Changed?" logic — unchanged from spec 11. Category rows with ↑/↓ deltas, "New this month", "New high" labels.

**Heading change only**: section heading updates from "📊 What changed?" to "💡 Insights" with subheading "vs {prevMonthLabel}".

---

## Scenario C — Gap Notice + Spending Highlights

**Trigger**: prior month exists but `isConsecutiveMonth(curr, prev)` is false (gap ≥ 2 months).

**Current behaviour (post spec 11 W1)**: Shows gap notice only — no data.

**New behaviour**: Show gap notice + current month's top 3 spending categories as context:

```
💡 Insights

📅 Last tracked: {prevMonthLabel}
Monthly comparisons work best with consecutive months.

This month's top spending:
• {cat1}  ₹{amount1}
• {cat2}  ₹{amount2}
• {cat3}  ₹{amount3}
```

---

## Scenario D — Tracking Quality Insight

**Trigger**: prior month is consecutive BUT `daysTracked` in the prior month is below a threshold (< 10 days tracked).

**Why**: Comparing June (25 tracked days) against May (4 tracked days) produces structurally misleading deltas. The numbers are real but the comparison is not meaningful.

**Threshold**: `daysTracked < 10` in the prior month. This is a conservative threshold that catches clearly sparse months without over-triggering.

**Data needed (requires backend)**:
- Add `days_tracked: int` to the `/insights/mom/{month_key}` response, representing the number of distinct expense dates in each month.
- Frontend reads `mom.days_tracked[prev]` to detect sparse prior month.

**Behaviour**: Skip MoM comparison, show tracking encouragement instead:

```
💡 Insights

📊 Expenses tracked on {currDaysTracked} days this month.
Last month: {prevDaysTracked} days.

Monthly comparisons become more accurate with consistent daily tracking.
```

**Note**: If `currDaysTracked` is also low (< 10), don't shame the user — use a neutral framing: "Keep logging expenses to build your financial picture."

---

## Backend Changes

### 1. Add `expense_count` to `/summary/{month_key}`

For Scenario A (onboarding):
```python
# In the summary computation, add:
expense_count = db.query(func.count(Expense.id)).filter(
    Expense.user_id == user_id,
    Expense.date.startswith(month_key)
).scalar() or 0
# Include in response: "expense_count": expense_count
```

### 2. Add `days_tracked` to `/insights/mom/{month_key}`

For Scenario D (tracking quality):
```python
# For each month in the MoM window, compute distinct expense dates:
days_tracked = {}
for m in months_in_window:
    count = db.query(func.count(func.distinct(Expense.date))).filter(
        Expense.user_id == user_id,
        Expense.date.startswith(m)
    ).scalar() or 0
    days_tracked[m] = count
# Include in response: "days_tracked": days_tracked  (dict: month_key → int)
```

### 3. Update `Summary` and `MoMData` types (frontend)

```typescript
// types/index.ts
interface Summary {
  // ... existing fields
  expense_count?: number;
}

interface MoMData {
  months: string[];
  categories: Record<string, Record<string, number>>;
  days_tracked: Record<string, number>;   // add this
}
```

---

## Frontend — Scenario Selector

Replace the current `mom && (() => { ... })()` IIFE with a clean scenario selector:

```tsx
{mom && (() => {
  const curr = mom.months[mom.months.length - 1];
  const prev = mom.months.length >= 2 ? mom.months[mom.months.length - 2] : null;
  const isFirstMonth     = !prev;
  const isConsecutive    = prev ? isConsecutiveMonth(curr, prev) : false;
  const currDaysTracked  = mom.days_tracked?.[curr] ?? 0;
  const prevDaysTracked  = prev ? (mom.days_tracked?.[prev] ?? 0) : 0;
  const isQualityData    = prevDaysTracked >= 10;

  const scenario =
    isFirstMonth                    ? "A" :
    isConsecutive && isQualityData  ? "B" :
    isConsecutive && !isQualityData ? "D" :
    "C";

  return (
    <section>
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-xs font-syne font-bold tracking-widest"
            style={{ color: "var(--text-sub)" }}>
          💡 Insights
        </h2>
        {scenario === "B" && prev && (
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>
            vs {new Date(prev + "-01").toLocaleString("en-IN", { month: "short" })}
          </span>
        )}
      </div>

      {scenario === "A" && <InsightsScenarioA summary={summary} />}
      {scenario === "B" && <InsightsScenarioB mom={mom} curr={curr} prev={prev} />}
      {scenario === "C" && <InsightsScenarioC summary={summary} prev={prev} />}
      {scenario === "D" && <InsightsScenarioD curr={curr} prev={prev} currDays={currDaysTracked} prevDays={prevDaysTracked} />}
    </section>
  );
})()}
```

Extract each scenario into a named sub-component for clarity. Keep them in `OverviewTab.tsx` unless the file becomes unwieldy — in that case extract to `frontend/react/src/components/shared/InsightsSection.tsx`.

---

## Implementation Order

| # | Item | Scope | Effort |
|---|------|-------|--------|
| 1 | Backend: add `expense_count` to `/summary/` | Backend | XS |
| 2 | Backend: add `days_tracked` to `/insights/mom/` | Backend | S |
| 3 | Frontend: update `Summary` + `MoMData` types | Frontend | XS |
| 4 | Frontend: Scenario A — Onboarding Insights | Frontend | S |
| 5 | Frontend: Scenario B — MoM (refactor existing into sub-component) | Frontend | S |
| 6 | Frontend: Scenario C — Gap + Highlights | Frontend | S |
| 7 | Frontend: Scenario D — Tracking Quality | Frontend | S |
| 8 | Frontend: Scenario selector + heading rename | Frontend | S |

Items 1–3 must precede items 4–8. Items 4–7 can be parallelised.

---

## Open Decisions

| Decision | Options | Status |
|----------|---------|--------|
| `expense_count` — add to summary or separate endpoint? | Add to summary (simpler) vs new endpoint (cleaner separation) | Unresolved — recommend summary |
| Sparse tracking threshold | < 10 days tracked in prior month | Proposed — confirm before build |
| Scenario D framing when current month is also sparse | Neutral ("Keep logging…") vs skip section entirely | Proposed neutral framing — confirm |
| Extract InsightsSection to own file? | Depends on OverviewTab.tsx line count after spec 11 | Decide at implementation time |
| "View all →" in Scenario B | Keep existing toast behaviour | Carry forward from spec 10 |

---

## Acceptance Criteria (full spec)

- Section heading reads "💡 Insights" in all scenarios.
- Scenario A: shown when no prior month; displays expense count, top category %, encouragement line. No comparison language.
- Scenario B: shown when prior is consecutive and prior days_tracked ≥ 10; displays existing MoM rows unchanged.
- Scenario C: shown when prior exists but gap ≥ 2 months; displays gap notice + top 3 current categories.
- Scenario D: shown when prior is consecutive but prior days_tracked < 10; displays tracking quality message with day counts.
- Exactly one scenario renders at a time — no overlap.
- "📊 What changed?" heading string removed from the codebase.
- TypeScript build clean.
- No crash on any combination of null/empty `mom`, `summary`, or `prevSummary`.

---

## Files Modified

- `backend/main.py` — extend `/summary/` and `/insights/mom/` responses
- `frontend/react/src/types/index.ts` — extend `Summary` and `MoMData`
- `frontend/react/src/components/tabs/OverviewTab.tsx` — scenario selector + sub-components (or extract to `InsightsSection.tsx`)

## Files NOT Modified

- `backend/ai_parser.py` — no changes (Tara integration deferred to a future spec)
- All other shared components — unchanged
