# Spec: Overview Page UX Improvements
**Date**: 2026-06-21
**Status**: Open — awaiting implementation

## Context

Visual review of the Overview tab (desktop view, screenshots taken June 2026)
surfaced several UX/clarity issues across the balance summary cards, budget
breakdown bar, spend donut, budget health cards, top spends list, and
month-over-month table. Each item below was verified against the actual
component code, not just the screenshots. Issue 1 was revised after a
follow-up screenshot corrected the original finding (see that section).

---

## Issue 1 — Desktop summary cards: hover-to-reveal works, but has no touch fallback or affordance

**Symptom (revised 2026-06-21)**: Originally flagged as "values are hidden
and unreachable." A follow-up screenshot showed the "Remaining" card mid-
hover — green border, ₹15,439 and the "REMAINING" label both visible — so
the flip mechanic **does work correctly on mouse hover**. The earlier write-
up overstated this as a data-visibility bug; it is not. The real gap is
narrower: the reveal only triggers on `:hover`, so it has no equivalent on
touch devices (tablets, touchscreen laptops, anyone on a trackpad who
doesn't rest the pointer over the card), and there's no visual affordance
(icon, hint text, subtle animation) indicating the cards are interactive at
all — someone who never hovers, or can't, will only ever see the front
face.

**Root cause**:
`frontend/react/src/components/shared/SummaryFlipCard.tsx` renders a 3D
flip-card: the front face (label + underline only) is shown at rest; the
back face (the actual `{fmtInr(value)}`) is revealed via a CSS transform
triggered purely by `.flip-card:hover` in `frontend/react/src/index.css`:
```css
.flip-card:hover .flip-card-inner { transform: rotateY(180deg); }
```
This is wired up in `frontend/react/src/pages/DashboardPage.tsx` —
`SummaryFlipCard` is used for the `hidden md:flex` desktop view, while the
mobile view (`SummaryStrip.tsx`, `md:hidden`) shows the value immediately
via a count-up animation, no gesture required. Confirmed working as
designed for mouse users; the gap is purely touch support + discoverability,
not functionality.

**Affected file(s)**:
- `frontend/react/src/components/shared/SummaryFlipCard.tsx`
- `frontend/react/src/index.css` (`.flip-card` rules)
- `frontend/react/src/pages/DashboardPage.tsx` (wiring — likely unchanged)

**Fix approach**: Add a touch-friendly equivalent (e.g. `onClick`/`onTouchStart`
toggling a flipped state in React, in addition to the existing CSS `:hover`)
so tablet/touchscreen users can reveal the value without a mouse. Add a
small visual affordance on the front face (e.g. a subtle corner icon or
"tap/hover to reveal" micro-hint) so first-time users know the card is
interactive at all, since nothing currently signals that today. Keeping the
flip interaction itself is fine — it works and looks good on hover — this
is additive, not a rebuild.

**Acceptance criteria**:
- On desktop, hovering each of the three cards reveals its value as it
  already does today (no regression).
- On a touch device (or with mouse emulation off), tapping a card reveals
  its value via an equivalent interaction.
- The front face of each card has some visible indication that it's
  interactive, even before any interaction occurs.

**Priority**: Medium — downgraded from High. The original "values are
inaccessible" framing was incorrect; this is now a touch-accessibility and
discoverability gap, not a data-visibility bug.

---

## Issue 2 — Budget Health "danger" tier label colour mismatches its card accent

**Symptom**: Cards in the orange ("danger") tier (e.g. "Shopping", "Medical"
in the screenshots) show a 🔴 red alarm emoji in the status label
("🔴 Likely to exceed limit") while every other visual element on the same
card — dot, left border, progress bar — is consistently orange. This reads
as a severity mismatch against the genuinely red "over limit" cards.

**Root cause**:
`frontend/react/src/components/shared/BudgetHealthCard.tsx`,
`STATUS_CONFIG.danger`:
```ts
danger: { dot: "🟠", accent: "#f59e0b", bg: "rgba(245,158,11,0.07)", label: "🔴 Likely to exceed limit" },
```
The `danger` tier's `dot` and `accent` are orange, but its hardcoded `label`
string embeds a red 🔴 emoji — inconsistent with every other colour signal
on the same card.

**Affected file(s)**:
- `frontend/react/src/components/shared/BudgetHealthCard.tsx` (`STATUS_CONFIG`)

**Fix approach**: Change the `danger` tier's label emoji from 🔴 to 🟠 to
match the rest of the card's colour signal. Optionally, consider whether a
four-tier system (over/danger/warning/safe) with closely-worded labels
("Likely to exceed" vs "Slow down — 80% limit near") is scannable enough at
a glance when 5+ cards are stacked — a simpler label hierarchy could be a
follow-up, not required for this fix.

**Acceptance criteria**:
- The danger-tier card's status label emoji visually matches its dot/border/
  progress-bar colour (orange, not red).
- The "over" (exceeded) tier remains the only card using red, preserving a
  clear single most-urgent signal.

**Priority**: Medium — confusing but not data-hiding; quick, low-risk fix.

---

## Issue 3 — Month-over-Month table: ₹0 and "no data" render identically

**Symptom**: Empty cells in the Month-over-Month table (e.g. April/May 2026
for categories with no history) show as a bare "—", with no way to tell
whether that means "no expenses logged that month" vs "category didn't
exist / wasn't tracked yet".

**Root cause**:
`frontend/react/src/components/shared/MoMTable.tsx`:
```tsx
{v > 0 ? fmtInr(v) : "—"}
```
Any value of exactly 0 (genuine zero spend) and any genuinely-missing month
(`monthData[m] ?? 0` defaulting to 0 when the key doesn't exist) both
collapse to the same `v > 0` false branch and render as "—". There's no
distinction in the data model passed to the component between "tracked,
spent nothing" and "not tracked this month".

**Affected file(s)**:
- `frontend/react/src/components/shared/MoMTable.tsx`
- Likely also `backend/main.py` (`/insights/mom/{month_key}` endpoint) if
  the distinction needs to be sourced from the backend — needs
  investigation at implementation time to confirm whether the backend
  currently differentiates "no data" from "zero spend" at all.

**Fix approach**: Investigate whether the backend response already
distinguishes a missing month from a zero-spend month. If it does, surface
the distinction in the UI (e.g. a lighter "—" with a tooltip "No data" vs a
"₹0" with normal styling). If the backend doesn't currently distinguish
them, this becomes a two-part fix (backend + frontend) — flag this in the
plan rather than assuming frontend-only.

**Acceptance criteria**:
- A category with genuine ₹0 spend in a tracked month is visually
  distinguishable from a category with no data that month (tooltip, label,
  or styling difference).

**Priority**: Low — ambiguous but not misleading in a damaging way; mostly
a clarity nice-to-have.

---

## Issue 4 — Month-over-Month trend % can be misleading at small baselines

**Symptom**: Categories with a small but nonzero prior-month baseline
produce dramatic trend percentages (e.g. "Groceries ↑272%" from ₹912 →
₹3,395, "Travel ↑217%" from ₹400 → ₹1,270) that visually read as alarming
but are really just normal variance at small absolute amounts.

**Root cause**:
`frontend/react/src/components/shared/MoMTable.tsx`:
```ts
const chg = prev > 0 ? ((last - prev) / prev) * 100 : null;
```
This correctly suppresses a trend badge when `prev` is exactly 0 (avoiding
a literal infinite/undefined %), but any nonzero `prev`, however small,
produces a mathematically correct but perceptually misleading large
percentage. A jump from ₹912 to ₹3,395 and a jump from ₹50,000 to ₹65,000
would both show as prominent red ↑ badges despite very different real-world
significance.

**Affected file(s)**:
- `frontend/react/src/components/shared/MoMTable.tsx`

**Fix approach**: Consider suppressing or visually softening the trend
badge when the prior-month baseline is below a meaningful threshold (e.g.
< ₹500, or some proportion of the user's average monthly spend) — possibly
showing the absolute ₹ change instead of a % in that case. Exact threshold
is a product decision, not strictly technical — flag for confirmation
before implementation.

**Acceptance criteria**:
- Trend badges for categories with very small prior-month baselines no
  longer show large, attention-grabbing percentages without context, while
  genuinely significant trend changes are still surfaced clearly.

**Priority**: Low — a refinement, not a bug; needs a product decision on
threshold before implementation.

---

## Issue 5 — Top Spends: generic 📦 icon flattens distinct entries

**Symptom**: In the Top Spends list, multiple distinct top entries
(e.g. "SBI" and "Beena", both categorised "Miscellaneous") render with the
same generic 📦 fallback icon, making two of the five biggest expenses
visually indistinguishable at a glance — working against the section's
purpose of helping users quickly recognise where money went.

**Root cause**:
`frontend/react/src/components/tabs/OverviewTab.tsx`:
```ts
const icon = CATEGORY_ICONS[item.category] ?? "📦";
```
`CATEGORY_ICONS` (in `frontend/react/src/utils/categories.ts`) is a fixed
map; "Miscellaneous" has an icon (📦) but any sub-distinction within it is
lost. This is expected behaviour given the current fixed category list, not
a bug — but it's a real readability gap.

**Affected file(s)**:
- `frontend/react/src/components/tabs/OverviewTab.tsx`
- `frontend/react/src/utils/categories.ts`

**Fix approach**: This resolves naturally once custom categories ship (see
`.claude/plans/04-spending-caps-export-custom-categories.md`, Item E) —
once users can create and assign icons to finer-grained categories instead
of dumping everything into "Miscellaneous", top spends will differentiate
better automatically. No standalone fix recommended ahead of that work;
noting it here as supporting motivation, not a new task.

**Acceptance criteria**: N/A — tracked as a benefit of existing planned
work (Item E), not a new acceptance-testable item.

**Priority**: Low — informational only, no action needed independent of
Item E.

---

## Investigated and found NOT to be a bug

**Spend by Category donut legend "cut off"** — initially flagged as a
possible overflow/scroll issue. On reading
`frontend/react/src/components/shared/SpendDonut.tsx`, the legend is a
plain `grid grid-cols-2` with no max-height, scroll container, or fade —
it has no scroll boundary at all and simply grows with the number of
categories. The apparent cutoff in the reviewed screenshot was the
screenshot's own frame ending, not a UI bug. No fix needed; not included
as a numbered issue above.

---

## Files NOT modified by this spec
- `backend/main.py` — Issue 3 may require backend investigation, but no
  confirmed backend change is in scope until that investigation happens
  during planning/implementation.
- `frontend/react/src/components/shared/BalanceBreakdown.tsx` — the
  near-invisible "Fixed Due" segment was discussed in review but is
  edge-case-dependent (only visible when that value is small relative to
  income) and not included as a numbered issue here; revisit if it recurs.

---

## Implementation Order

| # | Issue | Priority | Effort | Files |
|---|-------|----------|--------|-------|
| 2 | Budget Health danger-tier emoji mismatch | Medium | ~10 min | `BudgetHealthCard.tsx` |
| 1 | Summary cards: touch fallback + affordance | Medium | ~1–2h | `SummaryFlipCard.tsx`, `index.css` |
| 3 | MoM table: ₹0 vs no-data ambiguity | Low | ~1–3h (depends on backend investigation) | `MoMTable.tsx`, possibly `backend/main.py` |
| 4 | MoM trend % misleading at small baselines | Low | ~1h (pending threshold decision) | `MoMTable.tsx` |
| 5 | Top Spends generic icon | Low | N/A — resolved by existing Item E | — |

Note: Issue 2 and Issue 1 are both Medium priority now and roughly similar
effort — fine to batch in the same session, in either order.
