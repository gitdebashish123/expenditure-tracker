# Implementation Plan: Overview Tab — UX Review & Refinements
**Spec**: `.claude/specs/15_overview-ux-review-and-refinements.md`
**Date**: 2026-06-28
**Branch**: `feature/sprint06261-ui-enhancement`

---

## Overview

8 items total — all **frontend-only**, no backend changes.
Tier 3 issues (3A–3D) are explicitly deferred and not planned here.
Items are ordered smallest-blast-radius first.

---

## Spec Divergences (code vs. spec)

**Divergence 1 — Tiny Win has TWO emoji elements; spec only mentions one.**
Line 929 has `<span>🏆</span>` (the large decorative icon). Line 934 has `🎉 Tiny win` in the label text. The spec says "Change the Tiny Win section icon from 🏆 to 🌱" — this refers specifically to the large decorative `<span>` at line 929. The `🎉` in the label text is a different, independent emoji that stays unchanged.

**Divergence 2 — `InsightsScenarioD` disclaimer is not gated on `prevDays < 7`.**
The spec's condition is `lastMonthDays < 7 && daysRemaining > 3`. The current code shows the disclaimer unconditionally whenever the `!bothSparse` branch is taken (i.e. when either month has ≥10 days). The spec's intent is to suppress the disclaimer when the previous month had reasonable tracking (≥7 days) — there's no point telling the user to track more consistently if they already did. Plan adapts accordingly.

**Divergence 3 — Spending Signals clipping root cause confirmed in `SignalCard`.**
The outer card `<div>` (SpendingSignalsModal.tsx line 31) has `rounded-2xl` but no `overflow: hidden`. Without it, content can overflow the rounded corners and bleed to the viewport edge, causing the truncation at 390px. The left column already has `flex-1 min-w-0` (correct) and right has `flex-shrink-0` (correct) — the missing `overflow: hidden` is the primary fix.

---

## Item 1 — Change Tiny Win icon from 🏆 to 🌱
**Scope**: Frontend-only
**File**: `frontend/react/src/components/tabs/OverviewTab.tsx` — line 929
**Depends on**: nothing

**Root cause**: Line 929 renders `🏆` as the large decorative icon for the Tiny Win card, identical to the Category Winner trophy at line 475. The `🎉 Tiny win` text label (line 934) is separate and unchanged.

**What to do**:
Replace only the large icon span (line 929):

Before:
```tsx
<span className="text-2xl flex-shrink-0">🏆</span>
```

After:
```tsx
<span className="text-2xl flex-shrink-0">🌱</span>
```

---

## Item 2 — Rename "Upcoming reality" → "Coming Up"
**Scope**: Frontend-only
**File**: `frontend/react/src/components/tabs/OverviewTab.tsx` — line 647
**Depends on**: nothing

**Root cause**: Line 647 renders `📅 Upcoming reality` as the section heading. The emoji is already correct; only the text label changes.

**What to do**:

Before:
```tsx
          📅 Upcoming reality
```

After:
```tsx
          📅 Coming Up
```

---

## Item 3 — Financial Pulse tile min-height
**Scope**: Frontend-only
**File**: `frontend/react/src/components/tabs/OverviewTab.tsx` — lines 901–903
**Depends on**: nothing

**Root cause**: Each Financial Pulse tile (the IIFE at lines 806–920, grid at line 894) renders:
```tsx
<div
  key={s.name}
  className={`p-4 ${rightBorder} ${bottomBorder}`}
  style={{ borderColor: "var(--border-lg)" }}
>
```
No `min-height` is set. Tiles with two-line descriptions (e.g. "Tracked expenses on 28 days this month.") are taller than tiles with one-line descriptions ("Savings below target."), making the 2×2 grid visually uneven.

**What to do**:
Add `minHeight: 120` to the existing inline style object:

Before:
```tsx
style={{ borderColor: "var(--border-lg)" }}
```

After:
```tsx
style={{ borderColor: "var(--border-lg)", minHeight: 120 }}
```

If 120px turns out visually too tall or too short once tested on device, adjust to match actual content height. No other changes to the tile.

---

## Item 4 — Fix Spending Signals card clipping on iPhone 15
**Scope**: Frontend-only
**File**: `frontend/react/src/components/shared/SpendingSignalsModal.tsx` — line 31
**Depends on**: nothing

**Root cause**: The `SignalCard` outer `<div>` (line 31) applies `rounded-2xl` via className but has no `overflow: hidden`. Without it, inner content (especially the right-column `dailyRate` text like "₹2,815 over") can extend past the rounded corner boundary and bleed toward the viewport edge, rendering truncated at 390px. The flex layout is correct — left has `flex-1 min-w-0` and right has `flex-shrink-0`.

**What to do**:
Add `overflow: 'hidden'` to the inline style on the outer card div (line 31–34):

Before:
```tsx
    <div
      className="rounded-2xl p-4"
      style={{ background: sig.bg, border: `1px solid ${sig.colour}30` }}
    >
```

After:
```tsx
    <div
      className="rounded-2xl p-4"
      style={{ background: sig.bg, border: `1px solid ${sig.colour}30`, overflow: 'hidden' }}
    >
```

---

## Item 5 — Category Winner: filter out Miscellaneous, add fallback
**Scope**: Frontend-only
**File**: `frontend/react/src/components/tabs/OverviewTab.tsx` — lines 445–497 (IIFE)
**Depends on**: nothing

**Root cause**: Lines 446–448:
```tsx
const varCats = summary.categories.filter(c => !FIXED_CATEGORIES.includes(c.category));
if (varCats.length === 0) return null;
const top = [...varCats].sort((a, b) => b.spent - a.spent)[0];
```
`varCats` includes "Miscellaneous". The sort picks the highest spender with no exclusions, so when Miscellaneous dominates (as seen: ₹9,880 / 19%) it wins the trophy.

**What to do**:

**Step A** — after the existing `varCats` derivation (line 446), add a filtered eligible set and make `top` nullable:

Before:
```tsx
const varCats = summary.categories.filter(c => !FIXED_CATEGORIES.includes(c.category));
if (varCats.length === 0) return null;
const top = [...varCats].sort((a, b) => b.spent - a.spent)[0];
```

After:
```tsx
const varCats = summary.categories.filter(c => !FIXED_CATEGORIES.includes(c.category));
if (varCats.length === 0) return null;
const eligibleCats = varCats.filter(c => c.category !== 'Miscellaneous');
const top = eligibleCats.length > 0
  ? [...eligibleCats].sort((a, b) => b.spent - a.spent)[0]
  : null;
```

**Step B** — update `pctOfVar`, `topCurr`, `topPrev`, `momPct`, `prevLabel` derivations: these all reference `top` which is now nullable. Wrap the entire return in a null-guard:

Currently line 463 opens the `return (` JSX block. Before that block, add an early-return fallback when `top` is null:

```tsx
if (!top) {
  return (
    <div
      className="mt-3 pt-3 border-t"
      style={{ borderColor: "var(--border)" }}
    >
      <p
        className="text-[10px] font-syne font-bold uppercase tracking-widest mb-2"
        style={{ color: "var(--text-sub)" }}
      >
        Category Winner
      </p>
      <div className="flex items-center gap-3">
        <span className="text-2xl flex-shrink-0">🏅</span>
        <div>
          <p className="text-sm font-syne font-bold" style={{ color: "var(--text)" }}>
            No clear winner this month
          </p>
          <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
            Most spending was uncategorized. Try reviewing your transaction categories.
          </p>
        </div>
      </div>
    </div>
  );
}
```

The existing happy-path JSX (lines 463–496) is unchanged — it still uses `top.category`, `pctOfVar`, etc., which are all safe once the null guard is in place.

---

## Item 6 — Balance segment: legend-only (remove from stacked bar)
**Scope**: Frontend-only
**File**: `frontend/react/src/components/shared/BalanceBreakdown.tsx` — lines 14–39 (segments array) and lines 50–80 (bar render)
**Depends on**: nothing

**Root cause**: The "Balance Left" segment (lines 35–38) at ~2% of income (₹3,479 / ₹1,46,709 ≈ 2.4%) renders as a near-invisible sliver. The bar render (line 54) only skips segments below 0.5%; at 2.4% it renders but is too narrow to see. The legend row below already shows "Balance ₹3,479" clearly.

**What to do**: Implement Option B from the spec — exclude Balance from the bar while keeping it in the legend.

**Step A** — add a `legendOnly` property to the segments type. Update the "Balance Left" entry:

Before:
```tsx
  const segments = [
    { label: "Fixed Paid",      shortLabel: "Bills",    value: balance.fixed_paid_total,                colour: "#6366f1" },
    { label: "Fixed Due",       shortLabel: "Due",      value: balance.fixed_unpaid_total,              colour: "rgba(99,102,241,0.3)" },
    { label: "Variable Spent",  shortLabel: "Variable", value: balance.variable_total,                  colour: "#f87171" },
    { label: "Balance Left",    shortLabel: "Balance",  value: Math.max(balance.remaining, 0),          colour: "rgba(52,211,153,0.4)" },
  ];
```

After:
```tsx
  const segments: Array<{ label: string; shortLabel: string; value: number; colour: string; legendOnly?: boolean }> = [
    { label: "Fixed Paid",      shortLabel: "Bills",    value: balance.fixed_paid_total,                colour: "#6366f1" },
    { label: "Fixed Due",       shortLabel: "Due",      value: balance.fixed_unpaid_total,              colour: "rgba(99,102,241,0.3)" },
    { label: "Variable Spent",  shortLabel: "Variable", value: balance.variable_total,                  colour: "#f87171" },
    { label: "Balance Left",    shortLabel: "Balance",  value: Math.max(balance.remaining, 0),          colour: "rgba(52,211,153,0.4)", legendOnly: true },
  ];
```

**Step B** — in the stacked bar render, skip `legendOnly` segments (line 54 area):

Before:
```tsx
          if (pct < 0.5) return null;
```

After:
```tsx
          if (pct < 0.5 || s.legendOnly) return null;
```

**Step C** — the legend (lines 83–97) already iterates all `segments` with no filter. Leave it completely unchanged — Balance will continue to appear in the legend.

**Note**: After this change, Bills + Due + Variable fill 100% of the bar proportionally (or sum to the income amount). The `pct` calculation divides by `inc = Math.max(balance.total_income, 1)`, so segments naturally fill their share; removing Balance from the bar just means the bar may not reach 100% if Balance > 0 (a small visual gap at the right). If that looks odd, clamp the remaining 3 segments' widths to collectively fill 100% — but try the simple approach first.

---

## Item 7 — Tracking Summary disclaimer: conditional display
**Scope**: Frontend-only
**File**: `frontend/react/src/components/shared/InsightsSection.tsx` — `InsightsScenarioD`, lines 215–218
**Depends on**: nothing

**Root cause**: In `InsightsScenarioD` (lines 181–223), the disclaimer (lines 215–218):
```tsx
<p className="text-xs pt-1" style={{ color: "var(--text-muted)" }}>
  Monthly comparisons become more accurate with consistent daily tracking.
</p>
```
is shown unconditionally inside the `!bothSparse` branch (line 198). It should only appear when previous tracking was sparse (< 7 days) AND there are days remaining in the month to course-correct (> 3 days).

**What to do**:

**Step A** — add days-remaining calculation inside `InsightsScenarioD` (after the `bothSparse` const, before the return):

```tsx
const today        = new Date();
const daysInMonth  = new Date(today.getFullYear(), today.getMonth() + 1, 0).getDate();
const daysRemaining = daysInMonth - today.getDate();
const showDisclaimer = prevDays < 7 && daysRemaining > 3;
```

**Step B** — wrap the disclaimer `<p>` in a conditional:

Before:
```tsx
          <p className="text-xs pt-1" style={{ color: "var(--text-muted)" }}>
            Monthly comparisons become more accurate with consistent daily tracking.
          </p>
```

After:
```tsx
          {showDisclaimer && (
            <p className="text-xs pt-1" style={{ color: "var(--text-muted)" }}>
              Monthly comparisons become more accurate with consistent daily tracking.
            </p>
          )}
```

No changes to `InsightsScenarioD`'s props, no changes to its call site in `OverviewTab.tsx`.

---

## Item 8 — Compress header to single row on mobile
**Scope**: Frontend-only
**File**: `frontend/react/src/components/layout/Header.tsx`
**Depends on**: nothing

**Root cause**: The header currently has two distinct rows on mobile:
- Row 1 (lines 25–54): Logo (`💸 Wallet Mantra` + tagline "Beyond expense tracking") + theme toggle + avatar. MonthSelector hidden (`hidden sm:block`).
- Row 2 (lines 57–59): `sm:hidden mt-2` div with full-width MonthSelector below.

This consumes ~140px of mobile vertical space. The tagline is not useful to a logged-in user navigating the app.

**What to do** (3 changes):

**Step A** — remove the tagline `<p>` (lines 32–34):

Before:
```tsx
            <p className="text-xs mt-0.5" style={{ color: 'var(--text-sub)' }}>
              Beyond expense tracking
            </p>
```

After: delete those 3 lines entirely.

**Step B** — make the centre MonthSelector always visible, not desktop-only (line 38):

Before:
```tsx
          <div className="hidden sm:block flex-1 flex justify-center">
```

After:
```tsx
          <div className="flex-1 flex justify-center">
```

**Step C** — remove the mobile-only MonthSelector row (lines 56–59):

Before:
```tsx
        {/* Month selector — mobile only (full width below header row) */}
        <div className="sm:hidden mt-2">
          <MonthSelector />
        </div>
```

After: delete those 4 lines entirely.

**Result**: single-row header on all viewport sizes — logo left, MonthSelector centre, theme+avatar right. The `MonthSelector` component itself is already a compact pill; verify it fits comfortably at 390px alongside the logo and right controls.

---

## Implementation Order Summary

| # | Item | Issue | File(s) | Effort |
|---|------|-------|---------|--------|
| 1 | Tiny Win icon 🏆 → 🌱 | 2C | OverviewTab.tsx | XS |
| 2 | Rename "Upcoming reality" → "Coming Up" | 2A | OverviewTab.tsx | XS |
| 3 | Financial Pulse tile min-height | 2D | OverviewTab.tsx | XS |
| 4 | SignalCard overflow:hidden | 1B | SpendingSignalsModal.tsx | XS |
| 5 | Category Winner: exclude Miscellaneous + fallback | 1A | OverviewTab.tsx | S |
| 6 | Balance segment legend-only | 2B | BalanceBreakdown.tsx | XS |
| 7 | Tracking Summary disclaimer conditional | 2E | InsightsSection.tsx | XS |
| 8 | Header single-row on mobile | 2F | Header.tsx | XS |

All 8 items are independent — no dependencies between them. Tackle in order for smallest risk per commit.
