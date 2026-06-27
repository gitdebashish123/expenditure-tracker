# Spec: Overview Page Review Fixes
**Date**: 2026-06-27
**Status**: 🔵 Mostly Complete — 9/11 items done; F2a, F4, W1 pending
**Branch**: `feature/sprint06261-ui-enhancement` (continue on same branch)
**Follows**: `10_overview-polish-and-bugfixes.md` — all 8 items from sprint 10 are complete.
**Review source**: `Wallet_Mantra_Overview_Review_Final.md` + screenshot audit (2026-06-27)

---

## Context

A final review of the Overview page against the `Wallet_Mantra_Overview_Review_Final.md` document and a live screenshot identified 9 items: 3 spec violations, 3 layout/alignment issues, and 3 polish items. These are captured here as a clean-up sprint before closing the current branch.

---

## Information Architecture — Current State vs Spec

The canonical 12-section IA from the review doc is **fully present** in the current UI. Section order matches. No sections are missing from the visual flow. However, position 5 ("Insight") is ambiguous — see Issue F2.

---

## Issues

### F1 — Spending Signals: reformat raw percentages → plain-English labels *(Spec violation)* ✅ Done 2026-06-27

**Symptom**: Signal tiles show "168%", "118%", "21%" as the primary stat.

**Spec requirement** (`Wallet_Mantra_Overview_Review_Final.md` → Spending Signals):
> "Replace percentages like 168% with '68% over budget'."

**Rule**:
- `spent > budget` → primary stat: `"{overage}% over budget"` where `overage = Math.round((spent / budget - 1) * 100)`
- `80% ≤ spent/budget ≤ 100%` → primary stat: `"{pct}% of budget"` where `pct = Math.round(spent / budget * 100)`
- `spent < 80% of budget` → primary stat: `"{pct}% of budget"` (same formula, green context)

**Secondary line** (keep as-is): "Over by ₹{amount}" / "On track" badge.

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — Spending Signals card primary stat rendering

**Acceptance criteria**:
- No signal tile shows a raw percentage > 100%.
- Over-budget tile reads e.g. "68% over budget" (not "168%").
- On-track tile reads e.g. "21% of budget".
- Secondary badge and amount unchanged.

---

### F2 — "Insight" section (IA position 5): verify it is present and distinct; fix first-month messaging *(Spec violation)* ✅ Core done 2026-06-27 / ⬜ F2a pending

**Context**: The review doc IA lists "Insight" at position 5 (between Spend by Category and Peace of Mind) as "one AI-generated observation per month". The Monthly Breakdown already has a 2-month-average insight row (R10, sprint 10). These may be the same thing or two separate items.

**Rule**:
- If the Monthly Breakdown insight row (⚡ row beneath the stacked bar) is the only "Insight" content, it is incorrectly positioned — it lives inside the Monthly Breakdown card, not as a standalone section between positions 4 and 6.
- The spec intent is a **standalone Insight card** at position 5 with its own section heading ("✨ Insight") and one AI-generated observation sentence distinct from the breakdown percentage note.

**Current position (confirmed from code, 2026-06-27)**:
The Insight card lives inside Section 1 (Monthly Breakdown left column), as the last child of a `flex flex-col gap-3` container. It uses `flex-1` so it fills remaining height to match the Spend by Category card on the right. This is its correct and final position — do not move it.

**What to build** (if not already present):
- An Insight card inside the Monthly Breakdown column, below `<BalanceBreakdown />`.
- Heading: "✨ Insight"
- Body: one sentence from a new backend endpoint `/insights/monthly-insight/{month_key}` that generates an AI observation.
- Card uses `flex-1` so it stretches to fill remaining column height.
- If the endpoint returns null or errors, hide the card entirely (no empty states).
- Cache the response identically to the story endpoint (keyed by `(user_id, month_key)`, invalidated on expense mutation via `_invalidate_month_caches`).

---

#### F2a — First-month prompt bug (discovered 2026-06-27) ⬜ Pending

**Symptom**: A first-time user sees the message:
> "Variable spending jumped 72% from last month while maintaining strong savings discipline with the highest category allocation."

This message is wrong on two counts:
1. **The percentage is fictitious.** When there is no prior month, `prev_balance['variable_total']` is `0` or `None`. The AI receives `Prior month variable: N/A` (or `0`) and either hallucinates a percentage or computes against zero — producing a meaningless number.
2. **The tone is wrong for a new user.** A first-time user has no history to compare against. A comparative stat implies history they don't have, which is confusing and potentially alarming.

**Root cause**: The current prompt does not branch on whether prior month data exists. The AI is handed a `N/A` or `0` value and left to decide what to do with it — which it handles inconsistently.

**Fix — backend prompt branching**:

Detect first month: `is_first_month = (prev_balance is None or prev_balance['variable_total'] == 0)`

When `is_first_month is True` — use this prompt:
```
This is the user's first tracked month in Wallet Mantra. Generate exactly ONE short, encouraging, forward-looking observation (maximum 20 words). Do not reference any comparison to prior months, percentages, or changes. Focus only on what is notable or positive about this month's actual data.

Month: {month_key}
Top spending category: {top_category} at ₹{top_amount}
Savings this month: ₹{savings_total} ({savings_pct}% of income)
Bills paid: all / {unpaid} remaining

Respond with a single sentence only. No preamble.
```

Example outputs the AI should produce for first month:
- "Your savings rate this month sets a strong baseline for the months ahead."
- "Miscellaneous is your top category — labelling those expenses next month will sharpen your picture."
- "All bills cleared with a positive balance remaining — a clean start."

When `is_first_month is False` — use the existing comparative prompt, but add one explicit guard:
```
Do not mention percentage changes unless both the current month and prior month values are non-zero and meaningful.
```

**Fix — frontend safety net**:

If `prevSummary` is `null` in frontend state (confirming first month), apply a client-side filter before rendering: if `monthlyInsight` contains any of the substrings `["% from", "last month", "compared to", "jumped", "increased by", "decreased by"]`, suppress the card rather than display it. This is a fallback — the backend fix is the primary guard.

```tsx
const isSafeInsight = (text: string, isFirstMonth: boolean): boolean => {
  if (!isFirstMonth) return true;
  const comparativeTerms = ["% from", "last month", "compared to", "jumped", "increased by", "decreased by"];
  return !comparativeTerms.some(term => text.toLowerCase().includes(term));
};

const isFirstMonth = prevSummary === null;
{monthlyInsight && isSafeInsight(monthlyInsight, isFirstMonth) && (
  <div ...>{monthlyInsight}</div>
)}
```

**Affected files**:
- `backend/main.py` — new endpoint + cache + prompt branching on `is_first_month`
- `frontend/react/src/components/tabs/OverviewTab.tsx` — Insight card inside Monthly Breakdown column + `isSafeInsight` guard

**Acceptance criteria**:
- A distinct "✨ Insight" card appears inside the Monthly Breakdown column, below `<BalanceBreakdown />`, using `flex-1` to fill remaining height.
- **First-month users**: insight is encouraging, forward-looking, contains no percentage comparison to prior months.
- **Returning users**: insight may include comparative language only when both current and prior values are non-zero.
- If the frontend detects a first-month user and the insight string contains comparative language despite the backend guard, the card is hidden.
- Card is hidden when API returns null or errors.
- Cache invalidated on expense mutation.
- TypeScript build clean.

---

### F3 — Monthly Breakdown: add short segment labels inside the stacked bar *(Spec violation)* ✅ Done (pre-session)

**Symptom**: Bar shows only "62%", "35%", "3%" — no segment names.

**Spec requirement**: "Consider segment labels instead of only percentages."

**Rule**: Each segment in the stacked bar that is wide enough (≥ 12% of total width) should show a short label alongside the percentage. Labels:
- Fixed Paid segment → "Bills"
- Variable Spent segment → "Variable"
- Balance Left segment → "Balance"

Segments narrower than 12% show percentage only (no label — not enough room).

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — stacked progress bar rendering (or extracted `BalanceBreakdown` component if it exists)

**Acceptance criteria**:
- Segments ≥12% wide show e.g. "Bills 62%" inside the segment.
- Segments <12% show percentage only.
- Labels are white, 10–11px, truncated with ellipsis if needed.
- No overflow outside the bar container.

---

### L1 — Card height parity in responsive pairs *(Layout)* ✅ Done 2026-06-27

**Symptom**: In the Monthly Breakdown ∥ Spend by Category pair, the right card (Spend by Category) is significantly taller than the left. The left card has empty whitespace below its content. Same issue in the Peace of Mind ∥ Spending Signals pair.

**Fix**: Each responsive pair wrapper should use `align-items: stretch` (CSS Grid default) and each card inside should have `height: 100%`. Verify the card root elements have `h-full` (Tailwind) or `height: 100%` (inline). Do not set fixed pixel heights.

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — responsive pair grid wrappers and card root divs

**Acceptance criteria**:
- In both responsive pairs, left and right cards always match height.
- Cards stretch to fill the taller sibling's height at ≥580px.
- At <580px (stacked), each card reverts to natural height.

---

### L2 — Financial Pulse must span full width *(Layout)* ✅ Done 2026-06-27 (already correct — no change needed)

**Symptom**: Financial Pulse currently renders only under the right column of the Money Moments ∥ What Changed? area (or appears orphaned depending on DOM structure). It should be a standalone full-width section.

**Fix**: Ensure Financial Pulse is outside any pair grid wrapper, wrapped in its own full-width container (same pattern as Upcoming Reality, Tiny Win). Confirm it is not accidentally nested inside a grid column div.

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — Financial Pulse section wrapper

**Acceptance criteria**:
- Financial Pulse spans the full page width at all viewport sizes.
- It is not visually shifted to the right half of the page.
- Section position: after What Changed?, before Tiny Win.

---

### L3 — "Top Spending Category" tile needs visual separator inside Spend by Category card *(Layout)* ✅ Done (pre-session)

**Symptom**: The "Top Spending Category" tile sits directly below the category list in the Spend by Category card with no visual separation, making it feel like a list item rather than a distinct sub-section.

**Fix**: Add a `border-top: 0.5px solid var(--border)` (or Tailwind `border-t`) divider above the "Top Spending Category" row, with `pt-3 mt-3` spacing.

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — Spend by Category card, Top Spending Category sub-section

**Acceptance criteria**:
- Visible hairline separator between the category list and the Top Spending Category tile.
- Consistent with other intra-card dividers in the app.

---

### P1 — "Bills Paid" KPI: smarter subtext when 100% paid *(Polish)* ✅ Done (pre-session)

**Symptom**: When all bills are paid, the KPI shows "Out of ₹92,783" which repeats the amount shown as the primary value — redundant.

**Fix**:
```tsx
const subtitle = balance.fixed_unpaid_total === 0
  ? "All bills cleared ✓"
  : `Out of ₹${fmtInr(balance.fixed_paid_total + balance.fixed_unpaid_total)}`;
```

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — Bills Paid KPI card subtitle

**Acceptance criteria**:
- When all bills paid: subtitle reads "All bills cleared ✓".
- When bills remain: subtitle reads "Out of ₹{total}" as before.

---

### P2 — "What Changed?" cap extreme MoM percentages *(Polish)* ✅ Done (pre-session)

**Symptom**: "Groceries ↑ 821% (₹7,483)" appears when a category was zero or near-zero the prior month. This misleads users and creates visual alarm.

**Fix**:
```tsx
const displayPct = (pct: number | null, isNew: boolean): string => {
  if (isNew) return "New this month";
  if (pct === null) return "—";
  if (Math.abs(pct) > 300) return pct > 0 ? "↑ New high" : "↓ Major drop";
  return `${pct > 0 ? "↑" : "↓"} ${Math.abs(pct)}%`;
};
```

A category is considered "new" when the prior month amount was 0 or null.

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — What Changed? section percentage display

**Acceptance criteria**:
- Categories with 0 prior-month base show "New this month" instead of a percentage.
- Categories with MoM change > 300% show "↑ New high" or "↓ Major drop".
- Normal MoM percentages (≤300%) render unchanged.

---

### P3 — Section heading icons: add icons to all full-width section headings *(Polish)* ✅ Done (pre-session)

**Symptom**: Some sections have icons (💎 Money Moments, 🏆 Top Spending Category, ⚡ Insight row) but full-width section headings lack them. The desktop improvement spec says "use icons alongside section headings."

**Icon assignments**:
| Section | Icon |
|---------|------|
| Peace of Mind | 🧘 |
| Spending Signals | 📡 |
| Upcoming Reality | 📅 |
| What Changed? | 📊 |
| Financial Pulse | 💓 |
| Tiny Win | 🎉 |

**Fix**: Prepend each section heading `<span>` with the icon followed by a non-breaking space. Keep heading text in sentence case (e.g. "📡 Spending signals" not "📡 SPENDING SIGNALS"). If headings are currently uppercase via CSS `text-transform: uppercase`, remove that and render as sentence case.

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — all section heading strings listed above

**Acceptance criteria**:
- All 6 section headings above have their assigned icon.
- Heading text is sentence case (not all-caps).
- Icon and text are vertically aligned.

---

### W1 — "What Changed?" gap detection: skip comparisons when tracking is inconsistent or months are non-consecutive *(Data integrity)* ⬜ Pending

**Context**: Reviewed against `Wallet_Mantra_Adaptive_Insights_Recommendation.md` (2026-06-27). The current "What Changed?" section assumes the most recent month in `mom.months` is the calendar month immediately before `selMonth`. This is not always true — users may have tracked January and then returned in June, producing a misleading "vs January" comparison that implies continuity.

**Two unhandled scenarios**:
1. **Gap between months** — the prior recorded month is not the immediately preceding calendar month (e.g. current = June, last recorded = March). Comparing these implies steady tracking that didn't happen.
2. **Sparse tracking within a month** — a user logged expenses on only 3–4 days last month. Their MoM numbers are structurally incomparable to a month with 25+ days of tracking.

**Fix — gap detection (frontend-only)**:

Before rendering the comparison, compute whether the prior month in `mom.months` is genuinely the preceding calendar month:

```tsx
const isConsecutiveMonth = (current: string, prior: string): boolean => {
  const [cy, cm] = current.split("-").map(Number);
  const [py, pm] = prior.split("-").map(Number);
  const expectedPriorMonth = cm === 1 ? 12 : cm - 1;
  const expectedPriorYear  = cm === 1 ? cy - 1 : cy;
  return py === expectedPriorYear && pm === expectedPriorMonth;
};

const curr = mom.months[mom.months.length - 1];
const prev = mom.months.length >= 2 ? mom.months[mom.months.length - 2] : null;
const hasValidComparison = prev !== null && isConsecutiveMonth(curr, prev);
```

**When `hasValidComparison` is false** — do not show MoM category rows. Instead render a gap notice:

```tsx
<div className="py-4 text-center">
  <p className="text-sm" style={{ color: "var(--text-sub)" }}>
    📅 Last tracked month was{" "}
    {new Date(prev + "-01").toLocaleString("en-IN", { month: "long", year: "numeric" })}.
  </p>
  <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
    Monthly comparisons work best with consecutive months.
  </p>
</div>
```

**When `hasValidComparison` is true** — existing comparison logic unchanged.

**Note**: sparse tracking detection (Scenario 3 in the recommendation doc) is deferred to spec 12, which requires a days-tracked signal from the backend. This fix addresses only the calendar gap case, which is fully detectable on the frontend.

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — What Changed? section, before the `changes` array is built

**Acceptance criteria**:
- When prior month is non-consecutive (gap ≥ 2 months), comparison rows are hidden and a gap notice is shown.
- When prior month is consecutive, existing behaviour is completely unchanged.
- `isConsecutiveMonth` correctly handles January → December year rollover.
- No crash when `mom.months.length < 2`.

**Future work**: Full adaptive Insights engine (all 4 scenarios from the recommendation doc) is tracked in `12_adaptive-insights.md`.

---

### F4 — Remove Financial Snapshot heading; reduce KPI tiles from 4 to 3 *(Spec violation)* ⬜ Pending

**Symptom**: The Overview page renders a `"Financial Snapshot"` section heading above a 2×2 grid of four tiles: Remaining, Income, Bills Paid, and a fourth tile for "Pending Bills" / "All Bills Clear ✓".

**Spec requirement** (`Wallet_Mantra_Overview_Review_Final.md`):
> KPI Cards — Keep only Remaining, Income and Bills Paid.
> Remove Financial Snapshot — Remove entirely. It duplicated the KPI values.

**What to change**:
1. Remove the `<h2>Financial Snapshot</h2>` heading and its wrapping `<section>` label — the 3 KPI cards should stand alone with no named section heading above them.
2. Remove the 4th tile ("Pending Bills" / "All Bills Clear ✓") from the tiles array — this tile was not in the spec and is redundant with the Bills Paid subtitle.
3. Change the grid from `grid-cols-2` to `grid-cols-3` so the 3 remaining tiles sit in a single row.

**The "Bills Paid" tile already handles the paid/unpaid distinction** via its subtitle:
- All bills paid → subtitle: `"All bills cleared ✓"` (implemented in P1)
- Bills remaining → subtitle: `"Out of ₹{total}"`

No information is lost by removing the 4th tile.

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — Section 0 (Financial Snapshot block)

**Acceptance criteria**:
- No `"Financial Snapshot"` heading visible anywhere on the Overview page.
- Exactly 3 KPI tiles rendered: Remaining, Income, Bills Paid.
- Tiles sit in a single `grid-cols-3` row.
- Bills Paid subtitle correctly shows "All bills cleared ✓" or "Out of ₹{total}".
- No other section or content removed.

---

## Implementation Order

| # | Issue | Type | Effort | Status |
|---|-------|------|--------|--------|
| 1 | F3 — Segment labels in bar | Frontend | XS | ✅ |
| 2 | P1 — Bills Paid smarter subtext | Frontend | XS | ✅ |
| 3 | P2 — Cap extreme MoM % | Frontend | XS | ✅ |
| 4 | P3 — Section heading icons | Frontend | XS | ✅ |
| 5 | L3 — Top Spending Category separator | Frontend | XS | ✅ |
| 6 | F1 — Spending Signals % reformatting | Frontend | S | ✅ |
| 7 | L1 — Card height parity in pairs | Frontend | S | ✅ |
| 8 | L2 — Financial Pulse full width | Frontend | S | ✅ |
| 9 | F2 — Insight standalone card (core) | Backend + Frontend | M | ✅ |
| 9b | F2a — First-month prompt guard | Backend + Frontend | S | ⬜ |
| 10 | F4 — KPI cards: drop 4th tile + remove Financial Snapshot heading | Frontend | XS | ⬜ |
| 11 | W1 — What Changed? gap detection | Frontend | S | ⬜ |

---

## Open Decisions

| Decision | Resolution | Date |
|----------|-----------|------|
| Is the ⚡ Insight row in Monthly Breakdown the same as IA position 5 "Insight"? | No — they are separate. Build standalone Insight card at position 5. | 2026-06-27 |
| Cap threshold for extreme MoM % | 300% | 2026-06-27 |
| Icon style for section headings | Emoji (inline, consistent with existing usage in app) | 2026-06-27 |

---

## Files modified by this sprint

| File | Change |
|------|--------|
| `frontend/react/src/components/tabs/OverviewTab.tsx` | F1–F3, L1–L3, P1–P3, F2 frontend card (all items) |
| `frontend/react/src/components/shared/SpendingSignalsModal.tsx` | F1 — added `getSignalStat` helper, replaced `{pct}%` display |
| `frontend/react/src/components/shared/BalanceBreakdown.tsx` | F3 — segment labels (pre-session) |
| `backend/main.py` | F2 — `_insight_cache`, `_invalidate_month_caches` update, new `/insights/monthly-insight/{month_key}` endpoint |
| `backend/ai_parser.py` | F2 — added `generate_monthly_insight()` function |

## Files NOT modified by this spec
- `frontend/react/src/components/shared/BudgetHealthCard.tsx`
- `frontend/react/src/types/index.ts`
