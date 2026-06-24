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

## Issue 3 — Month-over-Month table "—" ambiguity (investigated and found NOT to need a fix)

**Status: Closed, no code change — 2026-06-22.**

**Original symptom**: Empty cells in the Month-over-Month table (e.g.
April/May 2026 for categories with no history) show as a bare "—", with no
way to tell whether that means "no expenses logged that month" vs
"category didn't exist / wasn't tracked yet".

**Why this turned out not to be a real issue**: The original write-up
assumed two distinct states (a genuine ₹0 spend month, and a no-data month)
were colliding into the same "—" display. Re-verifying against the actual
backend during planning (`.claude/plans/05-overview-page-ux-improvements.md`)
showed this premise doesn't hold:

- `GET /insights/mom/{month_key}` in `backend/main.py` builds its response
  exclusively from real `Expense` rows — a category only gets an entry for
  a given month if at least one expense exists for it that month. There is
  no "tracked, spent nothing" state in the data at all.
- A literal ₹0 expense cannot be created in this app — `ManualExpense`'s
  `positive_amount` validator rejects any `amount <= 0`.

So every "—" the frontend shows already means exactly one thing
unambiguously: no expenses were logged that month. There was never a second
state being collapsed into it. The frontend's
`frontend/react/src/components/shared/MoMTable.tsx` rendering
(`v > 0 ? fmtInr(v) : "—"`) is already correct as-is.

**Decision**: No code change (Option A — confirmed by user 2026-06-22).
This entry is kept in the spec, rather than deleted, so the investigation
and reasoning aren't lost if the question resurfaces later.

**Priority**: N/A — closed, not actionable.

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

**Status update (2026-06-22): blocked indefinitely.** This issue's only
planned resolution path — Item E in
`.claude/plans/04-spending-caps-export-custom-categories.md` (custom
categories) — has been skipped indefinitely, not just delayed within the
current sprint. See that plan's Overview section for the skip note. This
issue should be treated as open and unresolved, not as "handled elsewhere,"
until custom categories are explicitly picked back up.

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

**Fix approach (revised — original approach no longer applies)**: The
original fix approach assumed Item E would ship soon and resolve this as a
side effect. Since Item E is now deferred indefinitely, two paths forward:

- **Option A — wait.** Leave this unresolved until/unless custom
  categories are picked back up. No code change now. Lowest effort, but the
  readability gap persists indefinitely with no committed timeline.
- **Option B — small interim fix, independent of custom categories.**
  Without a full custom-categories system, a lighter-weight improvement is
  possible: derive a distinct icon or colour per *vendor* (not category)
  using a deterministic hash of the vendor name (e.g. pick from a small
  fixed palette of icons/colours based on a hash of `item.vendor`), so
  "SBI" and "Beena" — both "Miscellaneous" — at least render visually
  distinct from each other even though they share a category icon. This is
  a self-contained frontend-only change, doesn't touch the backend or wait
  on Item E, and would need its own small spec/plan if pursued.

**Acceptance criteria**: N/A while blocked. If Option B is chosen, new
acceptance criteria would need to be written for that specific approach.

**Priority**: Low — informational only; now explicitly blocked rather than
"resolved by upcoming work." Revisit if vendor-level visual distinction
(Option B) becomes worth doing on its own, independent of full custom
categories.

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
- `backend/main.py` — investigated for Issue 3; confirmed no backend
  change is needed (see Issue 3, closed).
- `frontend/react/src/components/shared/MoMTable.tsx` — investigated for
  Issue 3; confirmed no frontend change is needed either (see Issue 3,
  closed). Still in scope for Issue 4.
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
| 4 | MoM trend % misleading at small baselines | Low | ~1h (pending threshold decision) | `MoMTable.tsx` |
| 5 | Top Spends generic icon | Low | N/A — resolved by existing Item E | — |
| 3 | ~~MoM table: ₹0 vs no-data ambiguity~~ | — | — | **Closed, no fix needed** — see Issue 3 |

Note: Issue 2 and Issue 1 are both Medium priority and roughly similar
effort — fine to batch in the same session, in either order. Issue 3 is
closed and no longer part of implementation; kept in the table only for
traceability against the original numbering.
