# Spec: UI Fixes & Naming Cleanup
**Date**: 2026-06-27
**Status**: 🔴 Ready to implement
**Branch**: `feature/sprint06261-ui-enhancement` (same as spec 11)
**Follows**: `11_overview-review-fixes.md`
**Source**: Screenshot review 2026-06-27 (10:22 PM and 10:23 PM screenshots)

---

## Context

Three issues identified from live screenshot review:

1. **Duplicate KPI cards** — old "Financial Snapshot" section still rendering alongside the new 3-tile KPI row. F4 from spec 11 was not yet implemented.
2. **Wrong calendar date in story card** — the 📅 emoji hardcodes to "Jul 17" on all platforms. Today is June 27, 2026.
3. **Naming collision** — "✨ Insight" (AI card in Monthly Breakdown column) and "💡 Insights" (Section 9 Scenario D) both use "Insights" for two different purposes.

---

## Issue A — Duplicate KPI cards *(F4 carry-over from spec 11)*

**Symptom**: Two rows of KPI cards render simultaneously:
- Row 1 (old): large value on top, small-caps label below, coloured border. Still says "FIXED PAID".
- Row 2 (new): emoji icon + label on top, value below, subtitle. Says "BILLS PAID" with "All bills cleared ✓".

**Root cause**: The old Section 0 (`<h2>Financial Snapshot</h2>` + `grid-cols-2` 4-tile array) was never removed. The new 3-tile KPI row was added alongside it.

**Fix**:
1. Remove the `<h2>Financial Snapshot</h2>` heading and its wrapping element entirely.
2. Remove the old 4-tile `grid-cols-2` array.
3. Confirm the new `grid-cols-3` 3-tile row (Remaining, Income, Bills Paid) is the only KPI block remaining.
4. Confirm "Bills Paid" subtitle reads "All bills cleared ✓" when `fixed_unpaid_total === 0`.

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — Section 0

**Acceptance criteria**:
- Exactly one KPI row: 3 tiles in `grid-cols-3`.
- No "Financial Snapshot" heading anywhere on the page.
- No "FIXED PAID" label anywhere.
- "BILLS PAID" tile shows "All bills cleared ✓" when all paid, "Out of ₹{total}" otherwise.
- No other content removed.

---

## Issue B — Wrong calendar emoji in story card *(Polish)*

**Symptom**: The decorative element in the "June in One Sentence" story card shows 📅 which renders as **Jul 17** on all platforms. This is a platform hardcode — the emoji is not dynamic.

**Root cause**: 📅 (U+1F4C5) was introduced by Apple with Jul 17 as its appearance (WWDC date). All major platforms followed. It cannot reflect the actual current date.

**Fix**: Remove the decorative calendar illustration block from the story card entirely. The section heading already communicates the month. The illustration adds no information and actively misleads.

The block to remove:
```tsx
{/* Decorative illustration */}
<div className="hidden sm:flex flex-col items-center justify-center flex-shrink-0
               text-4xl leading-none select-none opacity-50"
     style={{ width: 72, height: 72 }}
     aria-hidden="true">
  <span>📅</span>
  <span className="text-xl mt-1">✨</span>
</div>
```

Remove this entire div. The story card text content is unchanged.

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — Section 0b (story card)

**Acceptance criteria**:
- No calendar emoji in the story card.
- Story card text (heading + AI sentence) unchanged.
- Card layout remains clean — no misalignment after removing illustration.

---

## Issue C — Naming collision: "Insights" used for two different things *(UX clarity)*

**Symptom**: Two sections use near-identical names:
- **"✨ Insight"** (Monthly Breakdown left column) — AI-generated behavioural observation.
- **"💡 Insights"** (Section 9, Scenario D) — tracking quality signal showing days tracked.

These serve different purposes but look like the same section to a user.

**Decision**: Keep "✨ Insight" unchanged. Rename the Scenario D heading to **"📋 Tracking summary"**.

**Scope**: Scenario D is the currently active scenario (confirmed from screenshot: 12 days tracked this month, 2 days last month). Scenarios A, B, C are part of spec 12 and not yet built. This rename applies to Scenario D only in this sprint.

**Fix**: In the current What Changed? IIFE, find Scenario D (the tracking quality branch). Change its section heading:

```tsx
// From:
<h2 ...>💡 Insights</h2>

// To:
<h2 ...>📋 Tracking summary</h2>
```

Also update the section comment:
```tsx
// From: {/* ── Section 9: 💡 Insights ─── */}
// To:   {/* ── Section 9: Tracking summary / What Changed? ─── */}
```

**Spec 12 alignment**: When spec 12 scenario selector is built, per-scenario headings must be:

| Scenario | Heading |
|----------|---------|
| A — First month | 🌱 Getting started |
| B — MoM comparison | 📊 What changed? |
| C — Gap + highlights | 📅 Spending highlights |
| D — Tracking quality | 📋 Tracking summary |

The "💡 Insights" umbrella heading proposed in spec 12 is **superseded** by this decision. Spec 12 Item 8 must use per-scenario headings from the table above, not a single "💡 Insights" heading.

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — Section 9, Scenario D heading + comment

**Acceptance criteria**:
- Section 9 in Scenario D shows "📋 Tracking summary" as the heading.
- "✨ Insight" card in Monthly Breakdown column is unchanged.
- No other headings changed.
- Section comment updated.

---

## Implementation Order

| # | Issue | Type | Effort |
|---|-------|------|--------|
| 1 | A — Remove duplicate KPI cards + Financial Snapshot heading | Frontend | XS |
| 2 | B — Remove calendar emoji from story card | Frontend | XS |
| 3 | C — Rename Scenario D heading to "📋 Tracking summary" | Frontend | XS |

All three are independent and can be done in a single prompt.

---

## Files Modified

- `frontend/react/src/components/tabs/OverviewTab.tsx` — all three issues

## Files NOT Modified

- `backend/main.py` — no changes
- `frontend/react/src/types/index.ts` — no changes
- Any shared component — no changes
