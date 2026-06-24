# Spec: Overview Page Refinement
**Date**: 2026-06-25
**Status**: Open — awaiting implementation
**Branch**: `feature/sprint06261-ui-enhancement` (continue on same branch)
**Supersedes**: Portions of `08_today-overview-redesign.md` that touch OverviewTab layout, Financial Pulse design, and What Changed? rendering. Today tab items (T1–T4) in spec 08 are unaffected.

## Context

After sprint 08 was planned and partially executed, a visual mockup (`suggested_overview.png`) and written feedback document (`Wallet_Mantra_Overview_Refinement.md`) were reviewed. Both converge on the same principle:

> Overview should answer: **What happened? What's important? What happens next?**
> It must not become a complex analytics dashboard.
> Tara's coaching and emotional engagement belong on the Today tab.

Three specific areas in the spec 08 plan require refinement before or during implementation:

1. **Financial Pulse** — the 4-tile design (Bills / Food / Spending / Tracking) feels machine-generated. Replace with a compact narrative health summary using 3–4 human-readable signal lines.
2. **What Changed?** — percentage changes for new or sparse users are misleading. Add scenario-aware rendering: historical comparisons when data exists, spending highlights when it doesn't.
3. **Section order** — the mockup proposes a cleaner flow that differs from spec 08's recommended order. Adopt the mockup's order.
4. **Two new elements** — the mockup introduces a "Tara's Observation" card and a "Category Winner" tile. "Tara's Observation" is dropped (Option A confirmed 2026-06-25 — Tara stays Today-only). "Category Winner" is included as R5.
5. **Monthly Breakdown Insight row** — the mockup adds a contextual insight below the `BalanceBreakdown` bar ("Variable spending consumed 32% of income this month. Your average over the last 6 months is 27%."). Requires historical aggregation not currently available — deferred as R6.

---

## Issue R1 — Redesign Financial Pulse as compact health summary

**What spec 08 planned**: 4 tile cards in a 2×2 grid — Bills, Food, Spending, Tracking — each with a coloured dot and a 1-2 word status label.

**What the mockup and feedback show**: The 4-tile grid feels machine-generated and adds visual noise. Replace with a compact vertical list of 3–4 signal lines inside a single card, each with a coloured icon and a plain-English one-liner. The mockup uses: **Stability** (fixed obligations), **Lifestyle** (food/spending behaviour), **Savings** (% of income protected), **Consistency** (days tracked this month).

### Revised signal design

| Signal | Icon | Data source | Green | Amber | Red |
|--------|------|-------------|-------|-------|-----|
| Stability | 🛡️ | `fixed_unpaid_total` | == 0 → "Fixed obligations complete" | > 0 and < 30% of total fixed → "Bills nearly complete" | ≥ 30% unpaid → "Fixed obligations pending" |
| Lifestyle | 🔥 | Food spend + variable pace vs prev month | Both ≤ 100% of prev → "Spending pace normal" | Food or pace 100–130% → "Food/Spending above normal" | Either > 130% → "Spending accelerated this month" |
| Savings | 🐷 | `savings_total / total_income` | ≥ 20% → "X% of income protected" | 10–20% → "Savings moderate this month" | < 10% → "Savings below target" |
| Consistency | 🎯 | Placeholder — days tracked count not yet available from backend | Always green — "Tracked expenses on X days this month" (use `new Date().getDate()` as proxy until real streak data is built) | — | — |

**Layout change**: Replace the 2×2 grid with a vertical list of 3–4 lines inside a single card. Each line: coloured icon + signal name on the left, status copy on the right.

**New backend requirement — `savings_total`**: Not currently returned by `/summary/{month_key}`. Add it to `get_balance_summary()` as the sum of all expenses in "Savings" and "Investments" categories for the month. Also add `savings_total: number` to the `balance` shape in `frontend/react/src/types/index.ts`.

**Affected files**:
- `backend/main.py` — `get_balance_summary()`: add `savings_total`
- `frontend/react/src/types/index.ts` — add `savings_total: number` to the `balance` shape
- `frontend/react/src/components/tabs/OverviewTab.tsx` — replace the 2×2 Financial Pulse grid with the compact list design

**Acceptance criteria**:
- Financial Pulse renders as a compact vertical list inside a single card (not a 2×2 grid).
- Stability, Lifestyle, Savings, Consistency all show with correct colour and copy.
- Savings signal uses real `savings_total / total_income` ratio.
- Consistency shows `new Date().getDate()` as a proxy day count, with a `// TODO: replace with real streak` comment in code.
- No regression on existing colour inversion logic in What Changed?.

**Priority**: High — most visible structural difference between spec 08 and the mockup.

---

## Issue R2 — Scenario-aware "What Changed?" rendering

**What spec 08 planned**: Always show top 4 categories by absolute ₹ change vs previous month, with percentage.

**What the feedback shows**: Percentage changes are meaningless or misleading for new/sparse users (e.g. "↑ Groceries +272%" with no prior baseline). Three scenarios apply:

### Scenario 1 — Historical data available (`mom.months.length >= 3`)

Show top 4 changes by absolute ₹ delta with percentage. Colour: spending up = red, spending down = green, Savings/Investments inverted. Same as spec 08's plan.

### Scenario 2 — First month user (`mom.months.length < 2`)

No directional arrows, no percentages. Show spending highlights from existing `spent_by_cat` state:
- 🏆 Top Category: [name] ₹[amount]
- 📦 Top 3 categories by spend, labelled as highlights (not comparisons)

**Note**: "Most Frequent Category" and "Largest Single Expense" require per-transaction data not in current payloads — deferred to a future `/insights/highlights/{month_key}` endpoint.

### Scenario 3 — Limited history (`mom.months.length === 2`)

Directional arrows + ₹ absolute delta only — no percentage. Categories where `prevAmt === 0 && currAmt > 0` labelled "New this month" instead of any delta figure.

**Implementation branching**:
```
mom.months.length < 2  → Scenario 2 (highlights only)
mom.months.length === 2 → Scenario 3 (absolute ₹, no %)
mom.months.length >= 3  → Scenario 1 (full comparison with %)
```

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — update the What Changed? block to branch on `mom.months.length`

**Acceptance criteria**:
- First-month users see spending highlights, no percentages or arrows.
- Users with exactly 1 prior month see ₹ deltas only; new categories show "New this month".
- Users with 2+ prior months see the full view with percentages.
- Colour and direction logic unchanged for Scenario 1.

**Priority**: High — the misleading percentage problem affects real users with sparse data today.

---

## Issue R3 — Revised section order for Overview tab

**Adopted order from mockup** (replaces spec 08's recommended order):

1. Financial Snapshot (O1)
2. June in One Sentence / This Month's Story (O2)
3. Monthly Breakdown / BalanceBreakdown bar (existing — Insight row deferred, see R6)
4. Spend by Category + Category Winner tile (existing donut + R5)
5. Financial Pulse compact list (R1)
6. Upcoming Reality (O6)
7. What Changed? scenario-aware (R2)
8. Peace of Mind Score (O3)
9. Budget Health (existing)
10. Tiny Win (O7)

Note: Tara's Observation (R4) removed from the order — Option A confirmed.

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — reorder JSX sections

**Acceptance criteria**:
- Sections render in the order listed above.
- No section accidentally removed during reorder.
- BalanceBreakdown bar stays in position 3 — no Insight row below it yet (see R6).

**Priority**: Medium — do after R1 and R2 are complete to avoid reorganising incomplete sections.

---

## Issue R4 — Tara's Observation card — DROPPED

**Decision**: Option A confirmed 2026-06-25. Tara stays on Today tab only. No Tara card on Overview. `backend/ai_parser.py` is not modified by this spec.

---

## Issue R5 — "Category Winner" tile below Spend by Category

**What the mockup shows**: A tile immediately below the Spend by Category donut: 🏆 category name, total amount, "X% of variable expenses", MoM change (e.g. "↑ 16% vs May").

**Data sources** (all already in scope in `OverviewTab`):
- Top category by spend: `max` of `spent_by_cat`
- % of variable expenses: `top_category_spent / balance.variable_total * 100`
- MoM change: `mom.categories[topCat][curr]` vs `mom.categories[topCat][prev]`

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — add Category Winner tile after the Spend by Category section

**Acceptance criteria**:
- Shows top spending category, total amount, % of variable spend, and MoM % change.
- When no prior month data exists, MoM change shows "First month".
- Trophy icon (🏆) in amber, category name in `font-syne font-bold`.

**Priority**: Medium — frontend-only, all data already available, high visual impact.

---

## Issue R6 — Monthly Breakdown Insight row (DEFERRED)

**What the mockup shows**: Below the `BalanceBreakdown` bar:
> "Variable spending consumed 32% of income this month. Your average over the last 6 months is 27%."

**Why deferred**: Requires aggregating `variable_total` across 6 historical months — `get_balance_summary()` works on a single month only. A new query or endpoint would be needed.

**Action**: Add a `// TODO: Insight row — see spec 09 R6, deferred` comment in `OverviewTab.tsx` below the `<BalanceBreakdown>` render. No other change.

---

## Implementation Order

| # | Issue | Type | Effort | Depends on |
|---|-------|------|--------|------------|
| 1 | R2 — What Changed? scenario-aware | Frontend | S | — |
| 2 | R1 — Financial Pulse compact list | Backend + Frontend | M | — |
| 3 | R5 — Category Winner tile | Frontend | S | — |
| 4 | R3 — Section reorder | Frontend | XS | R1 + R2 done first |

**Items from spec 08 unchanged by this spec** (implement as originally planned):
- O1 Financial Snapshot grid
- O2 This Month's Story
- O3 Peace of Mind Score (formula confirmed 2026-06-25)
- O6 Upcoming Reality
- O7 Tiny Win
- T1–T4 Today tab items

---

## Open decisions

1. **R6 timeline** — When to spec the Monthly Breakdown Insight row ("average over 6 months")? Candidate for the sprint immediately following this one.

---

## Files NOT modified by this spec
- `backend/ai_parser.py` — R4 dropped, no changes needed
- `frontend/react/src/components/shared/MoMTable.tsx` — unchanged
- `frontend/react/src/components/shared/BudgetHealthCard.tsx` — unchanged
- `frontend/react/src/components/shared/SummaryStrip.tsx` / `SummaryFlipCard.tsx` — unchanged
