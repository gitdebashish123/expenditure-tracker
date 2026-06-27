# Execution Prompts: UI Fixes & Naming Cleanup — Sprint 13
**Plan**: `.claude/plans/13-ui-fixes-and-naming.md`
**Spec**: `.claude/specs/13_ui-fixes-and-naming.md`
**Date**: 2026-06-27
**Branch**: `feature/sprint06261-ui-enhancement`

All three items are in `OverviewTab.tsx` only. No backend changes. No type changes.
Run as a single prompt — all items are independent and XS effort.

---

## Prompt 13-A — Items 1 + 2 + 3 (all three fixes in one pass)

```
Read `.claude/specs/13_ui-fixes-and-naming.md` and
`.claude/plans/13-ui-fixes-and-naming.md` in full before making any changes.

Then read `frontend/react/src/components/tabs/OverviewTab.tsx` in full.
Before writing a single line, identify:
  1. The OLD KPI block: <h2>Financial Snapshot</h2> + grid-cols-2 4-tile array
  2. The NEW KPI block: grid-cols-3 3-tile array (Remaining, Income, Bills Paid)
  3. The story card decorative div with 📅 emoji (hidden sm:flex, aria-hidden)
  4. The Section 9 IIFE and the Scenario D branch heading ("💡 Insights" or equivalent)
  5. The Section 9 comment (above or inside the IIFE)

Make exactly these three changes:

─── ITEM 1: Remove duplicate KPI cards (Issue A) ───
Remove the OLD KPI block entirely:
- The <h2>Financial Snapshot</h2> heading element.
- The grid-cols-2 <div> and its entire 4-tile .map() array inside it.

Keep the NEW grid-cols-3 3-tile array exactly as-is. Do not touch it.
If a wrapping <section> tag contains both blocks, keep the <section> and remove
only the heading + old grid from inside it.

─── ITEM 2: Remove calendar emoji from story card (Issue B) ───
Find and remove the decorative illustration div from the story card:
  <div className="hidden sm:flex ..." aria-hidden="true">
    <span>📅</span>
    <span ...>✨</span>
  </div>
Remove the entire div including the {/* Decorative illustration */} comment above it.
Do NOT change the text content div (flex-1 min-w-0) or the outer card container.

─── ITEM 3: Rename Scenario D heading (Issue C) ───
Inside the What Changed? IIFE, find the Scenario D branch (tracking quality —
triggered when prior month has < 10 tracked days, shows day count rows).
Change its section heading text from "💡 Insights" (or current text) to
"📋 Tracking summary".

Update the section comment for Section 9 to:
  {/* ── Section 9: Tracking summary / What Changed? ─── */}

Do NOT touch:
- The tracking quality card content (day counts, explanation text).
- The "✨ Insight" card inside the Monthly Breakdown column.
- Any other section heading or content.

─── AFTER ALL THREE CHANGES ───
Run tsc --noEmit in frontend/react/ — must be clean.

Confirm:
- Only one KPI grid visible: grid-cols-3 with 3 tiles (Remaining, Income, Bills Paid).
- No "Financial Snapshot" string remains in JSX.
- No "FIXED PAID" string remains in JSX.
- No 📅 emoji in the story card.
- Section 9 Scenario D heading reads "📋 Tracking summary".
- "✨ Insight" heading in Monthly Breakdown column is unchanged.
```

---

## Prompt 13-Final — Verification

```
Sprint 13 is complete. Verify all three fixes in
frontend/react/src/components/tabs/OverviewTab.tsx.

Issue A — Duplicate KPI cards:
- Search for "Financial Snapshot" — must not exist in JSX.
- Search for "FIXED PAID" or "Fixed Paid" — must not exist in JSX.
- Search for "grid-cols-2" in the KPI section — must not exist.
- Confirm exactly one KPI grid: grid-cols-3 with 3 tiles.
- Confirm Bills Paid subtitle logic: "All bills cleared ✓" when fixed_unpaid_total === 0.

Issue B — Calendar emoji:
- Search for the decorative illustration div (aria-hidden, hidden sm:flex, 📅).
- Must not exist anywhere in the file.
- Confirm story card outer container and text content are intact.

Issue C — Naming collision:
- Search for "💡 Insights" as a heading in Section 9 — must not exist.
- Confirm Section 9 Scenario D heading reads "📋 Tracking summary".
- Confirm "✨ Insight" heading in Monthly Breakdown column is unchanged.
- Confirm section comment reads "Tracking summary / What Changed?".

Run tsc --noEmit — must be completely clean.
Report any check that fails.
```
