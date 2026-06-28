# Implementation Plan: Heading Case Consistency + Descender Clipping
**Spec**: `.claude/specs/20_heading-consistency-and-descenders.md`
**Date**: 2026-06-28
**Branch**: `feature/sprint06261-ui-enhancement`

---

## Overview

3 items total — 0 require backend changes, all are frontend-only.  
Items ordered smallest-blast-radius first: additive CSS → isolated child component → main tab file.

---

## Item 1 — Add `.section-heading` shared CSS class
**Scope**: Frontend-only  
**File**: `frontend/react/src/index.css`  
**Insert after**: the `.scrollbar-hide` block (~line 170), before the `/* ══ KPI CAROUSEL */` comment

**Root cause**: No shared heading class exists today; every section heading in `OverviewTab.tsx` and `BalanceBreakdown.tsx` replicates the same `text-xs font-syne font-bold tracking-widest` combination inline with no `line-height` set. This is the root of both 20A (no guard against `uppercase` reappearing) and 20B (Syne font descenders overflow a cap-height line-box when `line-height` defaults to ~1.2 on `text-xs`).

**What to do**: Add the following block to `index.css`:

```css
/* ── Section headings — shared class (Spec 20) ───────────────── */
.section-heading {
  font-family: 'Syne', sans-serif;
  font-weight: 700;
  font-size: 0.75rem;      /* = text-xs */
  letter-spacing: 0.1em;   /* ≈ tracking-widest */
  line-height: 1.4;         /* descender room — fixes 20B */
  color: var(--text-sub);
  padding-bottom: 2px;      /* extra descender safety */
  /* NO text-transform — sentence case lives in source text (20A) */
}
```

This is purely additive — no existing code touched. Items 2 and 3 migrate headings onto this class; until then it has no effect.

---

## Item 2 — Fix `BalanceBreakdown.tsx` heading
**Scope**: Frontend-only  
**File**: `frontend/react/src/components/shared/BalanceBreakdown.tsx`  
**Lines**: 44–48

**Root cause** (verified against current code): The heading `<p>` at line 44 reads:

```tsx
<p
  className="text-xs uppercase tracking-widest mb-3"
  style={{ color: "var(--text-sub)" }}
>
  Monthly Breakdown
</p>
```

Two problems: `uppercase` Tailwind class applies `text-transform: uppercase` regardless of source text (20A), and `text-xs` without an explicit `line-height` defaults to Tailwind's `leading-tight` (~1.25) which clips Syne descenders (20B). The literal text "Monthly Breakdown" is also Title Case.

**What to do**: Replace the `<p>` with:

```tsx
<p className="section-heading mb-3">
  Monthly breakdown
</p>
```

- Replaces `text-xs uppercase tracking-widest` + inline `style` with `section-heading` (which encodes font, size, tracking, line-height, color, and pb already).
- Removes `uppercase` — fixes 20A.
- Sets `line-height: 1.4` via the class — fixes 20B.
- Text changes from "Monthly Breakdown" → "Monthly breakdown".
- `mb-3` (bottom margin to the stacked bar below) is kept as a separate Tailwind utility — it's layout, not heading style.

> Note: `BalanceBreakdown.tsx` uses `bg-dark-card border border-white/10 rounded-2xl p-4` on its outer `<div>` — these are unaffected.

---

## Item 3 — Fix all section headings in `OverviewTab.tsx`
**Scope**: Frontend-only  
**File**: `frontend/react/src/components/tabs/OverviewTab.tsx`

**Root cause** (verified against current code): Seven distinct heading elements need changes. They fall into three groups:

### Group A — Have `uppercase` class + Title Case text (worst offenders)
These render visually as ALL CAPS via CSS transform.

| Line(s) | Current className / text | Problem |
|---------|--------------------------|---------|
| 444 | `"text-[10px] font-syne font-bold uppercase tracking-widest"` / `"... in one sentence"` | `uppercase` on an eyebrow inside the story card |
| 503–506 | `"text-xs font-syne font-bold uppercase tracking-widest"` / `Spend by Category` | `uppercase` + Title Case |
| 559–562 | `"text-[10px] font-syne font-bold uppercase tracking-widest mb-2"` / `Category Winner` | `uppercase` + Title Case (no-winner fallback case) |
| 599–602 | `"text-[10px] font-syne font-bold uppercase tracking-widest mb-2"` / `Category Winner` | Same, in the winner-present case |
| 849–852 | `"text-xs font-syne font-bold uppercase tracking-widest"` / `💎 Money Moments` | `uppercase` + Title Case |

### Group B — No `uppercase` class, but text is not sentence case
| Line(s) | Current text | Change |
|---------|--------------|--------|
| 774 | `🔔 Coming Up` | → `🔔 Coming up` |

### Group C — Already sentence case, no `uppercase` — need only descender fix
These headings look fine case-wise but clip descenders because they lack `line-height`.
| Line(s) | Heading text |
|---------|-------------|
| 747 | `📡 Spending signals` |
| 901–909 | Dynamic ("Getting started" / "What changed?" / "Spending highlights" / "Tracking summary") |

The `💓 Financial pulse` heading (line 1018) is inside a card with `border-b` below it. Its `py-3` on the header div gives 12px above + 12px below the heading, which should be enough, but it has the same missing `line-height` issue — include it in the fix for completeness.

---

### What to do — per heading

**3a. Story card eyebrow (line 444)**  

```tsx
// Before
className="text-[10px] font-syne font-bold uppercase tracking-widest"
style={{ color: "var(--accent)" }}

// After — keep text-[10px] because this is 10px not 12px (text-xs), and keep accent colour
className="text-[10px] font-syne font-bold tracking-widest"
style={{ color: "var(--accent)", lineHeight: 1.4, paddingBottom: 2 }}
```

> This heading uses `var(--accent)` not `var(--text-sub)`, so it can't use `.section-heading` directly (which bakes in `color: var(--text-sub)`). Drop `uppercase`, add the line-height inline. Text is already `"{Month} in one sentence"` — no text change needed.

**3b. "Spend by Category" heading (lines 503–506)**

```tsx
// Before
<h2
  className="text-xs font-syne font-bold uppercase tracking-widest"
  style={{ color: "var(--text-sub)" }}
>
  Spend by Category
</h2>

// After
<h2 className="section-heading">
  Spend by category
</h2>
```

**3c. "Category Winner" — no-winner case (lines 559–562)**

```tsx
// Before
<p
  className="text-[10px] font-syne font-bold uppercase tracking-widest mb-2"
  style={{ color: "var(--text-sub)" }}
>
  Category Winner
</p>

// After
<p className="section-heading mb-2">
  Category winner
</p>
```

**3d. "Category Winner" — winner case (lines 599–602)**  
Identical change to 3c; the two `<p>` elements are in separate branches of the IIFE.

```tsx
// Before
<p
  className="text-[10px] font-syne font-bold uppercase tracking-widest mb-2"
  style={{ color: "var(--text-sub)" }}
>
  Category Winner
</p>

// After
<p className="section-heading mb-2">
  Category winner
</p>
```

**3e. "Spending signals" heading (lines 746–751)**  
Already sentence case, no `uppercase`. Only descender fix needed.

```tsx
// Before
<h2
  className="text-xs font-syne font-bold tracking-widest"
  style={{ color: "var(--text-sub)" }}
>
  📡 Spending signals
</h2>

// After
<h2 className="section-heading">
  📡 Spending signals
</h2>
```

**3f. "Coming Up" heading (lines 772–776)**  
No `uppercase` class, but text is not sentence case.

```tsx
// Before
<h2
  className="text-xs font-syne font-bold tracking-widest mb-4"
  style={{ color: "var(--text-sub)" }}
>
  🔔 Coming Up
</h2>

// After
<h2 className="section-heading mb-4">
  🔔 Coming up
</h2>
```

**3g. "Money Moments" heading (lines 849–853)**

```tsx
// Before
<h2
  className="text-xs font-syne font-bold uppercase tracking-widest"
  style={{ color: "var(--text-sub)" }}
>
  💎 Money Moments
</h2>

// After
<h2 className="section-heading">
  💎 Money moments
</h2>
```

**3h. "Getting started / What changed? / Spending highlights / Tracking summary" heading (lines 901–909)**  
Dynamic text, already sentence case. Only descender fix needed. The `<h2>` currently has no layout margin of its own (the `mb-4` is on the wrapper flex row at line 900).

```tsx
// Before
<h2
  className="text-xs font-syne font-bold tracking-widest"
  style={{ color: "var(--text-sub)" }}
>
  {scenario === "A" ? "🌱 Getting started" : ...}
</h2>

// After
<h2 className="section-heading">
  {scenario === "A" ? "🌱 Getting started" : ...}
</h2>
```

**3i. "Financial pulse" heading (lines 1017–1021)**  
Inside a card header div with `border-b`. The `<p>` currently has no pb; the surrounding `py-3` div provides vertical padding but doesn't expand the heading's own line-box.

```tsx
// Before
<p
  className="text-[10px] font-syne font-bold tracking-widest"
  style={{ color: "var(--text-sub)" }}
>
  💓 Financial pulse
</p>

// After — 10px font so can't use section-heading (which is 12px); inline line-height fix
<p
  className="text-[10px] font-syne font-bold tracking-widest"
  style={{ color: "var(--text-sub)", lineHeight: 1.4 }}
>
  💓 Financial pulse
</p>
```

> This heading has no descenders in the label itself, but the `lineHeight: 1.4` is defensive and consistent with the approach.

---

## Headings confirmed already correct — no changes needed

These were audited against the current file and require no edits:

| Heading | Why it's fine |
|---------|---------------|
| `🧘 Peace of mind` (line 652) | Sentence case, no `uppercase`, `tracking-widest` only |
| `🎉 Tiny win` (line 1063) | Sentence case, no `uppercase`; uses `#f59e0b` colour |
| `✨ Insight` (line 483) | Sentence case, no `uppercase`; uses `var(--accent)` |
| KPI card labels ("Remaining", "Income", "Bills Paid") | Inside KPI card, different styling context |
| Month badge (`"Jun"` / year in story card) | Proper-noun abbreviation, not a section heading |

---

## Execution Order

| # | Item | File | Effort | Risk |
|---|------|------|--------|------|
| 1 | Add `.section-heading` to `index.css` | `index.css` | XS | None — additive |
| 2 | Fix `BalanceBreakdown.tsx` heading | `BalanceBreakdown.tsx` | XS | None — isolated child |
| 3a–3i | Fix all headings in `OverviewTab.tsx` | `OverviewTab.tsx` | S | Low — JSX text + class edits |

Do item 1 first so the class is available when items 2 and 3 use it. Items 2 and 3 are independent of each other (different files) but both depend on item 1 being done.

---

## Definition of Done
- `npm run build` passes (zero TypeScript errors, zero ESLint warnings)
- No section heading on the Overview tab renders ALL CAPS
- All headings are sentence case: "Money moments", "Spend by category", "Category winner", "Monthly breakdown", "Coming up"
- Month-name eyebrow keeps proper-noun capital: "June in one sentence"
- No `uppercase` Tailwind class on any Overview section heading
- Descenders fully visible on "Spending signals", "Coming up", "Tracking summary" (desktop + mobile)
- No heading descender touches or overlaps a border/divider
- `tracking-widest` letter spacing retained (premium feel without ALL CAPS)
- Headings without descenders look unchanged — no excess vertical space added
