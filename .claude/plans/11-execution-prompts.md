# Execution Prompts: Overview Review Fixes — Sprint 11
**Plan**: `.claude/plans/11-overview-review-fixes.md`
**Date**: 2026-06-27
**Branch**: `feature/sprint06261-ui-enhancement`

Run these prompts in order. Each prompt references plan item numbers — read the plan item before executing. Paste one prompt at a time into a Claude Code session with the project open.

---

## Prompt 1 — Items 1–5 (all XS frontend fixes — run together)

```
Read `.claude/plans/11-overview-review-fixes.md` items 1 through 5.

Before making any changes, read `frontend/react/src/components/tabs/OverviewTab.tsx` to understand the current structure. Also check whether a `BalanceBreakdown` component exists at `frontend/react/src/components/shared/BalanceBreakdown.tsx` or similar — if so, read it too (plan Flag 2).

Then implement all five items in a single pass:

Item 1 (F3): Add segment labels inside the stacked breakdown bar. Segments ≥12% wide show "{label} {pct}%"; narrower segments show "{pct}%" only. Labels: Fixed Paid → "Bills", Variable Spent → "Variable", Balance Left → "Balance". Style: 10px white text, truncated with ellipsis if needed.

Item 2 (P1): Bills Paid KPI subtext — when `fixed_unpaid_total === 0`, show "All bills cleared ✓"; otherwise keep existing "Out of ₹{total}" format.

Item 3 (P2): What Changed? MoM percentage display — add `fmtMoM` formatter per the plan. Zero prior-month base → "New this month". >300% absolute change → "↑ New high" or "↓ Major drop". Use `prev_amount` from the API response if available; otherwise infer from pct_change > 300.

Item 4 (P3): Add emoji icons to 6 section headings: 🧘 Peace of mind, 📡 Spending signals, 📅 Upcoming reality, 📊 What changed?, 💓 Financial pulse, 🎉 Tiny win. Convert all-caps headings to sentence case (remove `uppercase` class or `text-transform: uppercase` if present).

Item 5 (L3): Add a `border-t mt-3 pt-3` divider above the Top Spending Category block inside the Spend by Category card.

After all five changes, confirm TypeScript build is clean (`npm run build` or `tsc --noEmit` in `frontend/react/`).
```

---

## Prompt 2 — Item 6 (F1: Spending Signals percentage reformatting)

```
Read `.claude/plans/11-overview-review-fixes.md` item 6 and plan Flag 1.

First, search for where the primary large-number stat (the "168%", "118%", "21%" values) is rendered in the Spending Signals section. It may be inline in `OverviewTab.tsx` or inside a sub-component like `SpendingSignalCard` created in sprint 10. Read whichever file contains it.

Implement the `getSignalStat` helper from the plan:
- `spent > budget` → `"{overagePct}% over budget"` where `overagePct = Math.round((spent/budget - 1) * 100)`
- Otherwise → `"{pct}% of budget"` where `pct = Math.round(spent/budget * 100)`

Replace the current primary stat display with this helper's output.

Do NOT change the secondary badge text ("Over by ₹X", "On track", "Almost full") or the card colours.

Confirm TypeScript build clean after.
```

---

## Prompt 3 — Item 7 (L1: Card height parity in responsive pairs)

```
Read `.claude/plans/11-overview-review-fixes.md` item 7 and plan Flag 2.

Read `frontend/react/src/components/tabs/OverviewTab.tsx` and locate both responsive pair wrappers (the divs containing Monthly Breakdown ∥ Spend by Category, and Peace of Mind ∥ Spending Signals).

For each pair wrapper:
1. Ensure the grid div does NOT have `items-start` or `align-items: flex-start` — remove if present. Grid default is `align-items: stretch`, which is what we need.
2. Add `h-full` to each direct child div of the pair wrapper.
3. Add `h-full` to the card root element inside each child.

If the card components are extracted (e.g. `<SpendByCategoryCard />`), check whether they accept a `className` prop and pass `className="h-full"`. If they don't accept className, add `h-full` to their root element directly.

Do NOT change any layout at <580px (single-column stacking must be unchanged).

Confirm TypeScript build clean after.
```

---

## Prompt 4 — Item 8 (L2: Financial Pulse full-width placement)

```
Read `.claude/plans/11-overview-review-fixes.md` item 8 and plan Flag 3.

Read `frontend/react/src/components/tabs/OverviewTab.tsx`. Find the Financial Pulse section. Trace its parent elements up to the top-level section list — specifically check whether Financial Pulse is accidentally inside a grid column div alongside Money Moments or What Changed?.

If it is inside a column div:
- Move the Financial Pulse JSX block outside that column div, placing it as a sibling of the pair wrapper (same level as Upcoming Reality, Tiny Win, etc.).
- Wrap it in `<div className="px-4 mt-4">` matching the pattern of other full-width sections.

If it is already at the correct level, verify nothing in its CSS constrains its width (no `max-width`, no `w-1/2` etc.).

After the fix, the Financial Pulse section must span the full page width at all viewport sizes and appear between What Changed? and Tiny Win.

Confirm TypeScript build clean after.
```

---

## Prompt 5 — Item 9 (F2: Standalone Insight card — backend)

```
Read `.claude/plans/11-overview-review-fixes.md` item 9 — backend steps only.

Read `backend/main.py` to understand the current structure before making any changes. Specifically:
- Find `_story_cache` and `_mantra_cache` declarations to place `_insight_cache` near them.
- Find `_invalidate_month_caches` to add the insight cache line.
- Confirm the route `/insights/monthly-insight/{month_key}` does NOT already exist (plan Flag 4).
- Identify the actual names of `_call_ai`, `_compute_balance`, `_get_category_totals` (or their equivalents) to use in the new endpoint.

Then implement:
1. Add `_insight_cache: dict[tuple, str] = {}` near the other cache dicts.
2. Add `_insight_cache.pop((user_id, month_key), None)` to `_invalidate_month_caches` (plan Flag 5).
3. Add the `GET /insights/monthly-insight/{month_key}` endpoint per the plan, adapting helper function names to match what actually exists in main.py.

Do NOT change any existing endpoint behaviour.

Confirm the Python file has no syntax errors after (`python -c "import backend.main"` or equivalent).
```

---

## Prompt 6 — Item 9 (F2: Standalone Insight card — frontend)

```
Read `.claude/plans/11-overview-review-fixes.md` item 9 — frontend steps only.

Read `frontend/react/src/components/tabs/OverviewTab.tsx`. Identify:
- Where existing AI insight states are declared (e.g. `story`, `pomData`) to place `monthlyInsight` state nearby.
- The `load()` function's Promise.all block to add the new fetch.
- The exact DOM position between the Monthly Breakdown ∥ Spend by Category pair and the Peace of Mind ∥ Spending Signals pair where the new card should be inserted.

Then implement:
1. Add `const [monthlyInsight, setMonthlyInsight] = useState<string | null>(null);`
2. Add the fetch call to `load()`:
   `api.get<{ insight: string | null }>(\`/insights/monthly-insight/${selMonth}\`).then(r => setMonthlyInsight(r.data.insight)).catch(() => setMonthlyInsight(null))`
3. Insert the Insight card JSX at position 5 (after the first pair, before the second pair):
```tsx
{monthlyInsight && (
  <div className="mx-4 mt-4 rounded-2xl border p-4" style={{ borderColor: "var(--border)", background: "var(--card)" }}>
    <p className="text-[11px] font-semibold tracking-wide mb-2" style={{ color: "var(--accent)" }}>
      ✨ Insight
    </p>
    <p className="text-[13px] leading-relaxed" style={{ color: "var(--text)" }}>
      {monthlyInsight}
    </p>
  </div>
)}
```

Confirm TypeScript build clean after (`npm run build` or `tsc --noEmit` in `frontend/react/`).
```

---

## Final verification prompt (run after all 6 prompts complete)

```
Sprint 11 is complete. Please do a final check:

1. Read `frontend/react/src/components/tabs/OverviewTab.tsx` and confirm:
   - Stacked bar segments ≥12% show label + percentage.
   - Bills Paid KPI shows "All bills cleared ✓" when unpaid total is zero.
   - What Changed? uses fmtMoM formatter (no raw >300% percentages).
   - All 6 section headings have emoji icons and are sentence case.
   - Top Spending Category has a border-t divider above it.
   - Spending Signals primary stat uses "X% over budget" / "X% of budget" format.
   - Both responsive pairs have h-full on child divs.
   - Financial Pulse is a sibling of pair wrappers (not inside one).
   - monthlyInsight state and fetch are present; Insight card is at position 5.

2. Read `backend/main.py` and confirm:
   - `_insight_cache` dict is declared.
   - `_invalidate_month_caches` evicts all three caches.
   - `/insights/monthly-insight/{month_key}` endpoint exists.

3. Run `tsc --noEmit` in `frontend/react/` — must be clean.

4. Report any item that did not pass its acceptance criteria.
```
