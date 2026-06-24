# Implementation Plan: Overview Page UX Improvements
**Spec**: `.claude/specs/05_overview-page-ux-improvements.md`
**Date**: 2026-06-21
**Branch**: Not specified in spec or CLAUDE.md — confirm with user before starting
work. Given the active branch from plan 04
(`feature/sprint06261-ui-enhancement`) may still be in flight, decide
whether this continues there or gets its own `feature/*` branch before
implementation begins.

---

## Overview

4 implementable items (Issue 5 has no standalone task — it's resolved by
existing Item E in plan 04, not duplicated here). All 4 are frontend-only.
One item (Issue 3) has a materially different scope than the spec
describes — see the note below before that section.

Ordered smallest-blast-radius first: trivial string fix → additive
interaction enhancement → table label-only fix → table threshold logic.

---

## ⚠️ Pre-implementation correction: Issue 3 scope has changed since the spec was written

The spec flagged Issue 3 as needing investigation into whether
`backend/main.py`'s `/insights/mom/{month_key}` endpoint distinguishes
"no data" from "genuine ₹0 spend," with a possible backend change in scope.

**Current code says no backend change is needed, for a different reason
than expected.** Re-reading `/insights/mom/{month_key}` (main.py, search
`month_over_month`) shows the `data` dict is built **exclusively from
actual `Expense` rows**:
```python
data.setdefault(e.category, {})
data[e.category][e.month_key] = data[e.category].get(e.month_key, 0) + e.amount
```
A category/month combination only gets a key if at least one expense exists
for it. There is no "tracked but zero" state in this data model at all —
and it can't exist, because `ManualExpense.amount` validation
(`positive_amount` validator) rejects any amount `<= 0`. **A real ₹0 expense
is impossible to create in this app.** So every "—" the frontend currently
shows is unambiguously "no expenses logged," never a true zero collapsed
into the same display. The spec's premise (two real states colliding into
one display) does not hold against the current backend.

This downgrades Issue 3 from a two-state disambiguation bug to, at most, a
labelling clarity nice-to-have (see Item 3 below) — and arguably not worth
doing at all. Flagging this prominently rather than silently planning
against the spec's original (incorrect) assumption.

---

## Item 1 — Budget Health danger-tier emoji mismatch

**Scope**: Frontend-only
**File**: `frontend/react/src/components/shared/BudgetHealthCard.tsx`

**Root cause (verified against current code)**:
`STATUS_CONFIG.danger.label` hardcodes a red 🔴 emoji while the tier's
`dot` and `accent` are both orange:
```ts
danger: { dot: "🟠", accent: "#f59e0b", bg: "rgba(245,158,11,0.07)", label: "🔴 Likely to exceed limit" },
```

**What to do**:
Change the emoji in the `danger` tier's `label` string from 🔴 to 🟠:
```ts
// change:
danger: { dot: "🟠", accent: "#f59e0b", bg: "rgba(245,158,11,0.07)", label: "🔴 Likely to exceed limit" },
// to:
danger: { dot: "🟠", accent: "#f59e0b", bg: "rgba(245,158,11,0.07)", label: "🟠 Likely to exceed limit" },
```
One-line change. No other tiers (`over`, `warning`, `safe`) need changes —
their emoji already matches their accent colour.

---

## Item 2 — Summary cards: touch fallback + visual affordance

**Scope**: Frontend-only
**Files**:
- `frontend/react/src/components/shared/SummaryFlipCard.tsx`
- `frontend/react/src/index.css` (`.flip-card` rules)

**Root cause (verified against current code)**:
The card flips via pure CSS on hover only:
```css
.flip-card:hover .flip-card-inner { transform: rotateY(180deg); }
```
`SummaryFlipCard.tsx`'s outer wrapper is `className="flip-card flex-1
rounded-2xl cursor-default"` — note `cursor-default`, which actively signals
non-interactivity despite the card being interactive via hover. There is no
`onClick`/`onTouchStart` handler, no React state for a flipped/unflipped
toggle, and no visual hint (icon, label change, animation) indicating the
card responds to interaction. Confirmed via screenshot that hover-to-reveal
works correctly for mouse users — this item is additive, not a rewrite.

**What to do**:

### `SummaryFlipCard.tsx`
Convert the component to a hybrid: keep the existing CSS hover behaviour
for desktop, and add a React-managed `flipped` state toggled on click/tap
so touch devices (no `:hover` state) get an equivalent interaction.

```tsx
import { useState } from "react";
import { fmtInr } from "@/utils/formatInr";

interface Props {
  label:   string;
  value:   number;
  colour:  string;
}

export function SummaryFlipCard({ label, value, colour }: Props) {
  const [flipped, setFlipped] = useState(false);

  return (
    <div
      className={`flip-card flex-1 rounded-2xl cursor-pointer ${flipped ? "flip-card-flipped" : ""}`}
      style={{ height: "80px" }}
      onClick={() => setFlipped(f => !f)}
      role="button"
      tabIndex={0}
      aria-label={`${label}: tap to reveal amount`}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          setFlipped(f => !f);
        }
      }}
    >
      <div className="flip-card-inner rounded-2xl">
        {/* Front — label */}
        <div
          className="flip-card-front rounded-2xl border border-white/10 p-3"
          style={{ backgroundColor: "var(--card)" }}
        >
          <span
            className="text-[10px] font-syne font-bold uppercase tracking-widest text-center"
            style={{ color: "var(--text-sub)" }}
          >
            {label}
          </span>
          <div
            className="w-8 h-0.5 rounded-full mt-1.5"
            style={{ backgroundColor: colour, opacity: 0.6 }}
          />
          {/* New: subtle affordance hint */}
          <span
            className="text-[8px] mt-1.5 opacity-50"
            style={{ color: "var(--text-muted)" }}
          >
            tap to reveal
          </span>
        </div>

        {/* Back — amount (unchanged) */}
        <div
          className="flip-card-back rounded-2xl border p-3"
          style={{
            backgroundColor: "var(--card2)",
            borderColor: colour + "40",
            borderTopWidth: "2px",
            borderTopColor: colour,
          }}
        >
          <span
            className="font-syne font-bold text-base leading-none"
            style={{ color: colour }}
          >
            {fmtInr(value)}
          </span>
          <span
            className="text-[9px] uppercase tracking-widest mt-1"
            style={{ color: "var(--text-muted)" }}
          >
            {label}
          </span>
        </div>
      </div>
    </div>
  );
}
```

Key changes from current file:
- `cursor-default` → `cursor-pointer` (the card genuinely is interactive)
- Added `onClick` toggling local `flipped` state
- Added `role="button"`, `tabIndex={0}`, `aria-label`, and `onKeyDown` for
  keyboard/screen-reader accessibility — currently the card has none
- Added a small "tap to reveal" hint text on the front face, so the
  affordance is visible before any interaction
- Added conditional class `flip-card-flipped` to drive the flip via React
  state in addition to the existing `:hover` CSS path

### `index.css`
Add a class-driven flip rule alongside the existing hover rule, so either
trigger (hover OR the new `flip-card-flipped` class) rotates the card:
```css
/* change: */
.flip-card:hover .flip-card-inner { transform: rotateY(180deg); }

/* to: */
.flip-card:hover .flip-card-inner,
.flip-card-flipped .flip-card-inner { transform: rotateY(180deg); }
```
No other CSS rules need to change — `.flip-card-front`/`.flip-card-back`
backface-visibility rules already work regardless of what triggers the
rotation.

**Note**: `DashboardPage.tsx` wiring is unaffected — `SummaryFlipCard` is
called with the same `label`/`value`/`colour` props; no prop interface
change.

---

## Item 3 — MoM table: clarify "—" meaning (downgraded scope, see correction above)

**Scope**: Frontend-only — **no backend change**, contrary to the spec's
original "possibly two-part fix" framing (see correction note at top of
this plan).

**File**: `frontend/react/src/components/shared/MoMTable.tsx`

**Root cause (re-verified against current code)**:
```tsx
{v > 0 ? fmtInr(v) : "—"}
```
Confirmed: since the backend can only ever report a category/month
combination if a real (necessarily positive) expense exists for it, every
"—" in this table means "no expenses logged," full stop. There's no second
state being collapsed. The original ambiguity concern doesn't apply to
current code.

**What to do — two options, pick one before implementing**:

**Option A (recommended, minimal): do nothing.** The display is already
unambiguous given the current data model; the spec's concern was based on
an incorrect assumption. Close this item without a code change, and update
the spec to reflect the corrected understanding (mirroring how Issue 1 was
corrected earlier in this spec's history).

**Option B (if still desired for clarity): add a tooltip on hover/long-press
explaining the dash.** Wrap the `"—"` in a `<span>` with a `title`
attribute:
```tsx
{v > 0 ? fmtInr(v) : <span title="No expenses logged this month">—</span>}
```
This is purely cosmetic — it doesn't change what's shown, only clarifies it
for anyone who hovers. Minimal risk, but also minimal value given the dash
is already correct, not ambiguous.

**Recommendation**: confirm with the user whether to take Option A (skip)
or Option B (trivial tooltip) before implementing — this is a product call,
not a technical one, especially since the original "fix" was based on a
premise that turned out to be false.

---

## Item 4 — MoM trend % misleading at small baselines

**Scope**: Frontend-only
**File**: `frontend/react/src/components/shared/MoMTable.tsx`

**Root cause (verified against current code)**:
```ts
const chg = prev > 0 ? ((last - prev) / prev) * 100 : null;
```
Correctly suppresses the badge when `prev` is exactly 0, but any small
nonzero `prev` (e.g. ₹400, ₹912) produces a mathematically correct but
perceptually alarming large percentage (217%, 272% in the reviewed
screenshots).

**What to do**:
Add a minimum-baseline threshold below which the trend badge is suppressed
(rendered as "—" same as the no-prior-data case) rather than showing a
potentially misleading large percentage. Pending product decision on exact
threshold — implementing with a placeholder constant the user can tune:

```ts
// Add near the top of the component, above the JSX:
const MIN_TREND_BASELINE = 500; // ₹ — below this, trend % is suppressed as noise

// change:
const chg = prev > 0 ? ((last - prev) / prev) * 100 : null;
// to:
const chg = prev >= MIN_TREND_BASELINE ? ((last - prev) / prev) * 100 : null;
```

This means categories with a prior-month baseline under ₹500 will show "—"
in the Trend column instead of a percentage, regardless of how large the
swing is in relative terms. The absolute ₹ values are still fully visible
in the month columns themselves — only the derived trend badge is
suppressed.

**Open question for the user before implementing**: is ₹500 the right
threshold, or should it scale with the user's typical monthly spend per
category? A fixed constant is the simplest correct implementation; a
dynamic threshold (e.g. 10% of average monthly spend across all categories)
would be more adaptive but adds complexity not requested in the spec.
Recommend starting with the fixed constant and revisiting only if it proves
wrong in practice.

---

## Execution Order

| # | Item | Effort | Risk | Depends on |
|---|------|--------|------|------------|
| 1 | Budget Health emoji fix | ~5 min | None | — |
| 2 | Summary cards touch + affordance | ~1h | Low — additive, no existing prop/behaviour removed | — |
| 3 | MoM "—" clarity | 0 (Option A) or ~15 min (Option B) | None | User decision: A or B |
| 4 | MoM trend threshold | ~20 min | Low — one constant, one comparison change | User decision: threshold value |

Items 1 and 2 can be implemented immediately with no further input needed.
Items 3 and 4 each have one open question for the user — confirm those
before writing code for those two items, but Items 1/2 don't need to wait.

---

## Definition of Done
- `cd frontend/react && npm run build` passes (zero TypeScript errors, zero
  ESLint warnings)
- Item 1: in Budget Health, a category in the "danger" (orange) tier shows
  an orange 🟠 emoji in its status label, not red 🔴; the "over" (exceeded)
  tier remains the only card using red anywhere
- Item 2: on desktop, hovering a summary card still flips it (no
  regression); on a touch device or with a mouse-emulation-off devtools
  check, tapping a card flips it; the front face shows a "tap to reveal"
  hint before any interaction; keyboard (Tab + Enter/Space) also triggers
  the flip
- Item 3: confirmed with user whether Option A (no change) or Option B
  (tooltip) was chosen, and implemented accordingly
- Item 4: confirmed minimum-baseline threshold value with user; categories
  with a prior-month spend below that threshold show "—" instead of a
  percentage in the Trend column; categories above the threshold are
  unaffected
