# Spec 20 — Heading Case Consistency + Descender Clipping
**Date**: 2026-06-28
**Status**: 🔴 Ready to implement
**Branch**: `feature/sprint06261-ui-enhancement`
**Follows**: `19_kpi-carousel-rebuild.md`
**Source**: Desktop + iPhone 15 screenshots, June 28, 2026 (3:35 PM)

---

## Context

Two heading issues span the entire Overview tab on both desktop and mobile:

1. **Inconsistent case** — some section headings are ALL CAPS, others are
   sentence case, with no hierarchy logic. They appear adjacent in a single
   scroll, making the page look styled by two different conventions.

2. **Descender clipping** — the bottom of letters with descenders (g, p, y) is
   cut off or visually overlapped on several headings (notably "Spending
   signals", "Coming Up", "Tracking summary").

**Decision (confirmed):** Standardize ALL section headings to **sentence case**.

---

## Current State Audit

Headings found across `OverviewTab.tsx`, written two different ways in source:

| Heading (as rendered) | Source casing | CSS transform | Target |
|----------------------|---------------|---------------|--------|
| JUNE IN ONE SENTENCE | sentence ("...in one sentence") | `uppercase` via class | **Sentence case** |
| MONTHLY BREAKDOWN | literal caps in JSX | none | **Sentence case** |
| SPEND BY CATEGORY | literal "Spend by Category" | `uppercase` | **Sentence case** |
| MONEY MOMENTS | literal "Money Moments" | `uppercase` | **Sentence case** |
| CATEGORY WINNER | literal "Category Winner" | `uppercase` | **Sentence case** |
| Tracking summary | sentence | none | Keep (fix clipping) |
| Financial pulse | sentence | none | Keep |
| Peace of mind | sentence | none | Keep |
| Spending signals | sentence | none | Keep (fix clipping) |
| Coming Up | sentence | none | Keep (fix clipping) |
| Tiny win | sentence | none | Keep |
| Insight | sentence | none | Keep |

The inconsistency comes from a mix of: literal-caps text in JSX, `text-transform:
uppercase` applied via Tailwind `uppercase` class, and plain sentence-case text
with no transform. Three different mechanisms produce the visual mismatch.

---

## Issue 20A — Standardize All Headings to Sentence Case

**Goal:** Every section heading renders in sentence case (first word capitalized,
rest lowercase except proper nouns/month names). No `text-transform: uppercase`
on section headings anywhere.

### Changes required in `OverviewTab.tsx`

**1. Remove `uppercase` from heading className wherever it appears on section
headings**, and rewrite any literal-caps text to sentence case.

Specific edits:

| Location | Current | New |
|----------|---------|-----|
| Story card eyebrow | `{month} in one sentence` + `uppercase` class | Remove `uppercase`; keep text as "{Month} in one sentence" |
| Monthly breakdown | inside `BalanceBreakdown` component — check its heading | "Monthly breakdown" sentence case, no uppercase |
| Spend by Category | "Spend by Category" + `uppercase` | "Spend by category", remove `uppercase` |
| Category Winner | "Category Winner" + `uppercase` | "Category winner", remove `uppercase` |
| Money Moments | "Money Moments" + `uppercase` | "Money moments", remove `uppercase` |

> Note: "Coming Up" → consider "Coming up" for strict sentence case, OR keep
> "Coming Up" if you prefer the title-case proper-noun feel. **Recommendation:
> "Coming up"** for full consistency, since every other heading will be sentence
> case.

**2. The month-name eyebrow** ("June in one sentence") — keep the month name
capitalized (it's a proper noun) but ensure no `uppercase` transform. The
`.toLocaleString("en-IN", { month: "long" })` already returns "June"
capitalized, so just removing `uppercase` gives "June in one sentence" correctly.

### Tailwind classes to remove from section headings
- `uppercase` (the Tailwind utility)

### Keep
- `tracking-widest` or `tracking-wide` — letter spacing is fine and looks good
  in sentence case too (gives the premium feel without the shouty caps)
- `font-syne font-bold` — the heading font weight
- `text-[10px]` / `text-xs` sizing — unchanged
- `var(--text-sub)` color — unchanged

### Note on BalanceBreakdown component
The "Monthly breakdown" heading lives inside
`frontend/react/src/components/shared/BalanceBreakdown.tsx`, not OverviewTab.
That heading must be updated there. This is the ONE allowed exception to the
"OverviewTab only" file scope — it's a heading on the Overview tab that happens
to be extracted into a child component.

**Affected files:**
- `frontend/react/src/components/tabs/OverviewTab.tsx`
- `frontend/react/src/components/shared/BalanceBreakdown.tsx` (only the heading text/class)

**Acceptance criteria:**
- [ ] No section heading on the Overview tab is ALL CAPS
- [ ] All headings render sentence case: "Money moments", "Spend by category",
      "Category winner", "Monthly breakdown", "Coming up", etc.
- [ ] Month-name eyebrow keeps proper-noun capital: "June in one sentence"
- [ ] No `uppercase` Tailwind class remains on any Overview section heading
- [ ] `tracking-*` letter spacing retained for the premium look
- [ ] Consistent on both desktop and mobile

---

## Issue 20B — Fix Descender Clipping on Headings

**Symptom:** The bottom of g/p/y letters is cut off or overlapped on:
- "Spending signals" (the g and p)
- "Coming Up" / "Coming up" (the g and p)
- "Tracking summary" (the g and y)

Headings without descenders (e.g. "Category winner", "Monthly breakdown") are
unaffected — confirming this is vertical clipping, not a rendering glitch.

**Root cause (most likely, in priority order):**
1. `line-height` too tight on heading (e.g. `leading-none` / `line-height: 1`)
   — the Syne font has tall descenders that overflow a cap-height line box.
2. A fixed `height` or `overflow: hidden` on a heading wrapper clipping the
   descender.
3. A `border-bottom` / divider rendered too close to the baseline, visually
   overlapping descenders.

The Syne heading font (`font-syne`) has descenders that sit lower than many
sans-serifs, so any line-box sized for cap-height clips them.

**Fix:**

1. **Add bottom breathing room to the heading line-box.** On the section heading
   class/elements, ensure `line-height` is at least `1.3`. In Tailwind terms,
   replace any `leading-none` / `leading-tight` on headings with `leading-normal`
   or `leading-relaxed`, or add explicit `pb-0.5` (2px) to `pb-1` (4px).

2. **Audit the three flagged headings' wrappers** for `overflow: hidden` +
   tight height, and remove the height constraint so the heading can render its
   full line-box.

3. **Check divider/border proximity.** For headings immediately followed by a
   `border-b` or a `<div className="h-px">` divider, ensure there is at least
   4–6px gap (`mb-1` or `pb-1`) between the heading text and the border so
   descenders don't collide with the line.

**Specific elements to check in OverviewTab.tsx:**

| Heading | Likely fix |
|---------|-----------|
| "Spending signals" (`📡` heading) | Add `leading-relaxed` + `pb-0.5` to the `<h2>`; the `mb-4` margin exists but line-height is clipping internally |
| "Coming up" (`🔔` heading) | Same — `<h2>` with `tracking-widest`, add `leading-relaxed pb-0.5` |
| "Tracking summary" heading | Same treatment; check the `<h2>` line-height |
| Financial pulse header (inside bordered card) | The header has `border-b` below it — ensure `py-3` gives descenders room above the border |

**General approach:** Rather than fixing each heading individually, the cleanest
solution is to add `leading-relaxed` (or `line-height: 1.4`) to the shared
heading styling so every section heading has descender room. If a shared class
doesn't exist, this spec is a good opportunity to introduce one (see optional
refactor below).

**Affected files:**
- `frontend/react/src/components/tabs/OverviewTab.tsx`
- `frontend/react/src/components/shared/BalanceBreakdown.tsx` (if its heading clips)
- `frontend/react/src/index.css` (if introducing a shared heading class)

**Acceptance criteria:**
- [ ] "Spending signals" — full g and p visible, no clipping (desktop + mobile)
- [ ] "Coming up" — full g and p visible
- [ ] "Tracking summary" — full g and y visible
- [ ] No heading descender touches or is overlapped by a border/divider
- [ ] Headings without descenders look unchanged (no added excess space)

---

## Optional Refactor — Shared Heading Class

Both 20A and 20B touch every section heading. This is a natural point to
introduce a single shared class so future headings are consistent by default.

```css
/* index.css — add near other component styles */
.section-heading {
  font-family: 'Syne', sans-serif;
  font-weight: 700;
  font-size: 0.75rem;          /* text-xs */
  letter-spacing: 0.1em;        /* tracking-wide-ish */
  line-height: 1.4;             /* descender room — fixes 20B */
  color: var(--text-sub);
  /* NO text-transform — sentence case via source text (20A) */
  padding-bottom: 2px;          /* extra descender safety */
}
```

Then each heading becomes:
```tsx
<h2 className="section-heading">📡 Spending signals</h2>
```

This is **optional** — if it expands scope too much, apply the inline Tailwind
fixes (`leading-relaxed pb-0.5`, remove `uppercase`) per heading instead. But the
shared class is the more maintainable path and prevents this drift from
recurring.

**Recommendation:** Do the shared class. It solves 20A and 20B simultaneously and
permanently, and the diff is cleaner than editing ~10 headings individually.

---

## Implementation Order

| # | Issue | Where | Effort |
|---|-------|--------|--------|
| 1 | Introduce `.section-heading` class (optional but recommended) | index.css | XS |
| 2 | 20A — Convert all headings to sentence case + apply class | OverviewTab + BalanceBreakdown | S |
| 3 | 20B — Verify descender room (handled by class line-height) | OverviewTab + BalanceBreakdown | XS |

If using the shared class, 20A and 20B are mostly solved together: the class sets
`line-height: 1.4` (fixes clipping) and omits `text-transform` (enforces sentence
case from source text).

---

## Files Modified

- `frontend/react/src/components/tabs/OverviewTab.tsx`
  — Convert all section headings to sentence case
  — Remove `uppercase` classes
  — Apply `.section-heading` class (or inline `leading-relaxed pb-0.5`)

- `frontend/react/src/components/shared/BalanceBreakdown.tsx`
  — "Monthly breakdown" heading only (case + clipping)

- `frontend/react/src/index.css`
  — Add `.section-heading` shared class (if doing the refactor)

## Files NOT Modified
- `backend/` — no changes
- `frontend/react/src/types/index.ts`
- Any other component or tab (Today, Fixed, History, Settings headings are out of
  scope for this spec — though the same `.section-heading` class could be applied
  to them in a future consistency pass)
