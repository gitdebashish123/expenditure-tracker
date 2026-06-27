# Implementation Plan: UI Fixes & Naming Cleanup — Sprint 13
**Spec**: `.claude/specs/13_ui-fixes-and-naming.md`
**Date**: 2026-06-27
**Branch**: `feature/sprint06261-ui-enhancement` (same branch as spec 11)
**Prerequisite**: None — all three items are pure frontend, independent of each other and of spec 11 remaining items.

---

## Overview

3 items, all XS effort, all in a single file (`OverviewTab.tsx`), all independent.
No backend changes. No type changes. Can be done in a single Claude Code session.

---

## ⚠️ Flags & Gaps

### Flag 1 — Two KPI blocks coexist in Section 0
The file currently has TWO KPI structures in Section 0:
- **Old block**: `<h2>Financial Snapshot</h2>` + `<div className="grid grid-cols-2 gap-3">` containing a `.map()` over a 4-tile array. This is the one to remove.
- **New block**: A `<div className="grid grid-cols-3 gap-3">` containing 3 tiles (Remaining, Income, Bills Paid). This is the one to keep.

Do NOT remove the new block. Confirm by reading the file and identifying both grids before deleting.

### Flag 2 — Story card decorative div is `hidden sm:flex`
The calendar illustration div uses `hidden sm:flex` — it only shows on `sm` breakpoint and above. Remove the entire div regardless. Do not change the surrounding flex container or the text content.

### Flag 3 — Scenario D heading location
The current What Changed? IIFE has three internal branches. Scenario D (tracking quality) is the branch that checks `prevDaysTracked < 10`. The heading "💡 Insights" sits inside the `<section>` wrapper of this branch. Only change the heading text — do not touch the branch logic, the card content, or the day counts display.

### Flag 4 — Section comment location
The section comment `{/* ── Section 9: ... */}` may sit outside the IIFE (above the `{mom && (() => {` line) or inside it. Update whichever comment is present. If both exist, update both.

---

## Item 1 — Issue A: Remove duplicate KPI cards + Financial Snapshot heading
**Spec ref**: Issue A
**Scope**: Frontend-only
**Files**: `OverviewTab.tsx` — Section 0

**Pre-read**: Before making any changes, read the Section 0 block fully. Identify:
- The old `<h2>Financial Snapshot</h2>` element and its wrapping `<section>` or `<div>`.
- The old `grid-cols-2` array mapping over 4 tiles (Remaining, Income, Bills Paid, Pending Bills / All Bills Clear).
- The new `grid-cols-3` array mapping over 3 tiles (Remaining, Income, Bills Paid with subtitle logic).

**What to do**:
Remove the old `<h2>Financial Snapshot</h2>` heading element and the old `grid-cols-2` 4-tile grid entirely. Leave the new `grid-cols-3` 3-tile grid exactly as-is.

If the old and new blocks share a wrapping `<section>` tag, keep the `<section>` tag and remove only the heading + old grid from inside it.

**Do not touch**:
- The new `grid-cols-3` 3-tile array.
- The "Bills Paid" tile subtitle logic (`fixed_unpaid_total === 0 ? "All bills cleared ✓" : ...`).
- Any other section below Section 0.

**Acceptance criteria**:
- One KPI grid visible: `grid-cols-3` with 3 tiles.
- No `"Financial Snapshot"` string in JSX.
- No `"FIXED PAID"` string in JSX.
- No `grid-cols-2` KPI grid in JSX.
- Bills Paid subtitle logic intact.

---

## Item 2 — Issue B: Remove calendar emoji illustration from story card
**Spec ref**: Issue B
**Scope**: Frontend-only
**Files**: `OverviewTab.tsx` — Section 0b (story card)

**Pre-read**: Find the story card section. Locate the decorative div:
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

**What to do**:
Remove this entire `<div>` block including the comment above it. Do not change:
- The story card outer container div.
- The `flex-1 min-w-0` text content div.
- The heading ("JUNE IN ONE SENTENCE") and story text.
- Any other part of the story card.

After removal, the story card's outer container (`flex items-start gap-4`) will have only one child (the text div). This is correct — verify it renders cleanly without the illustration.

**Acceptance criteria**:
- No `📅` emoji in the story card.
- Story heading and AI sentence text unchanged.
- No layout collapse or misalignment after removal.

---

## Item 3 — Issue C: Rename Scenario D heading to "📋 Tracking summary"
**Spec ref**: Issue C
**Scope**: Frontend-only
**Files**: `OverviewTab.tsx` — Section 9, Scenario D heading

**Pre-read**: Find the What Changed? IIFE (`mom && (() => { ... })()`). Inside it, locate the branch that renders the tracking quality card — it checks `prevDaysTracked < 10` or equivalent. Find the `<h2>` heading element inside that branch's `<section>` wrapper.

**What to do**:

**Step 1** — Change the heading text:
```tsx
// From:
💡 Insights

// To:
📋 Tracking summary
```

**Step 2** — Update the section comment. Find the comment above Section 9 (may be inside or outside the IIFE):
```tsx
// From (any variant of):
{/* ── Section 9: 💡 Insights ─── */}
{/* ── Section 9: What Changed? ─── */}

// To:
{/* ── Section 9: Tracking summary / What Changed? ─── */}
```

**Do not touch**:
- The tracking quality card content (day counts, explanation text).
- The "✨ Insight" card in the Monthly Breakdown column.
- Any other section heading.
- Scenario A / B / C branches (they don't exist yet — will be built in spec 12).

**Acceptance criteria**:
- Section 9 Scenario D heading reads "📋 Tracking summary".
- "✨ Insight" heading in Monthly Breakdown column unchanged.
- Section comment updated.
- No other headings changed.

---

## Execution Summary

| Item | Issue | Scope | Effort | Depends on | Status |
|------|-------|-------|--------|------------|--------|
| 1 | A — Remove duplicate KPI / Financial Snapshot | Frontend | XS | Flag 1 | ⬜ |
| 2 | B — Remove calendar emoji from story card | Frontend | XS | Flag 2 | ⬜ |
| 3 | C — Rename Scenario D heading | Frontend | XS | Flag 3, 4 | ⬜ |

---

## Spec 12 Alignment Note

Issue C introduces per-scenario headings for Section 9. When spec 12 is implemented, `InsightsScenarioD` in `InsightsSection.tsx` must use "📋 Tracking summary" as its heading. The full per-scenario heading table is in spec 13. The "💡 Insights" umbrella heading in spec 12 Item 8 is superseded — update spec 12 before starting that sprint.
