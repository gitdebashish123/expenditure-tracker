# Spec 22 — Fixed Tab: Paid-State Redesign, Privacy & Category Polish
**Date**: 2026-06-29
**Status**: 🟢 Fully implemented — all Items 1–9 shipped (2026-06-29). Option A (single global toggle) chosen for privacy model. Tier 3 deferred.
**Branch**: `feature/sprint06261-ui-enhancement` *(confirm active branch before starting)*
**Follows**: `21_kpi-carousel-slide-math-fix.md`
**Follow-up**: `23_fixed-tab-followup-fixes.md` (post-ship re-review: eye placement + card treatment)
**Source**: iPhone 15 Safari + desktop screenshots, June 29 2026; external ChatGPT UX review (`Wallet_Mantra_Fixed_Tab_UX_Review_v1.md`) + redesign mockup; code-grounded analysis + approved HTML mockup of the all-paid state.

---

## Context

The Fixed tab works well conceptually but has a few correctness/semantic defects
in its **all-paid (100%) state** plus polish opportunities. This spec consolidates
two inputs:

1. An external screenshot-only review (enthusiastic, vision-heavy) — useful as a
   backlog, but it over-scopes and assumes features that aren't in the product.
2. A code-grounded pass over `FixedTab.tsx`, `FixedExpenseRow.tsx`, `PoolCard.tsx`,
   `DashboardPage.tsx`, `SummaryFlipCard.tsx`, `SummaryStrip.tsx`, and `types/index.ts`.

A reviewed HTML mockup of the redesigned all-paid state was approved as the visual
target (single privacy toggle, calm 100% celebration, per-category counts,
collapsible groups, distinct Household/Housing icons, plain pool input, paid-state
rows instead of a strikethrough wall).

### Responsive note (important — affects Tier 1.2)
`DashboardPage.tsx` renders the summary differently per breakpoint:
- **Mobile (`md:hidden`)** → `SummaryStrip` — values shown outright, **no** reveal step.
- **Desktop (`hidden md:flex`)** → three `SummaryFlipCard`s — each flips independently
  on tap ("tap to reveal").

So the "three separate taps to reveal" + "₹93,253 shown inline anyway" contradiction
is a **desktop-only** issue. On mobile there is no gating at all. This is why 1.2 is
framed as a product decision, not a pure bug.

### Out of scope (deliberate — do not implement here)
- **Search & filters** — premature at ~20 bills; revisit at 50–100+.
- **Bill priority indicators (🔴🟠🟢)** — adds taxonomy + visual noise; low value.
- **A named "Tara" AI persona** — does not appear in the files reviewed
  (`FixedTab`, `DashboardPage`, `types`); the app's AI surfaces are unnamed
  (Peace of Mind, Monthly Story, Daily Mantra, Tiny Win). Naming the assistant is a
  separate brand decision, not a Fixed-tab change. *(Note: not verified via full-repo
  content grep — only the files above were read.)*
- **"Pay Now" / one-tap payment** — Wallet Mantra is a tracker; there is no payment
  rail. The honest verb stays **"Mark as paid."**

---

## Tier 1 — Critical / correctness

### 1.1 ₹0 pending must not render red
**File:** `FixedTab.tsx` (summary header, Section 2)
**Problem:** Pending is hardcoded `text-red-400` regardless of value, so the *best*
state (nothing pending) is painted as an alert.
**Fix:** Conditional color — emerald/neutral when `unpaidTotal === 0`, red/amber only
when `unpaidTotal > 0`. Optional: add a check glyph + "all paid" affordance at zero.
```tsx
// current: <span className="text-red-400">{fmtInr(unpaidTotal)} pending</span>
// change to a conditional: unpaidTotal === 0 ? emerald "₹0 pending" : red/amber
```

### 1.2 Privacy model consistency  ⟵ NEEDS DECISION
**Files:** `DashboardPage.tsx` (renders strip + flip cards), `SummaryFlipCard.tsx`
(per-card flip), `FixedTab.tsx` (inline `… done` total).
**Problem:** Desktop gates each card behind an independent flip while the inline
"₹93,253 done" total sits in plain text below — protecting a number in one place,
exposing it inches away. Mobile gates nothing.
**Decision needed (pick one):**
- **(A) Single global toggle** — one eye control (header or summary band); values
  visible by default, one tap hides all (cards + inline total). Matches the approved
  mockup and the mobile "values visible" philosophy. *(Recommended.)*
- **(B) Gate nothing** — drop the flip entirely; show values on both breakpoints
  (mobile already does this).
- **(C) Gate everything** — extend gating to the inline total too; replace 3
  independent flips with one flip that reveals/hides all three.
Whichever is chosen, the inline `… done` total in `FixedTab` must obey the same rule.

### 1.3 Household vs Housing differentiation
**File:** `utils/categories.ts` (`CATEGORY_ICONS`)
**Problem:** Near-identical labels + near-identical house emojis (🏡 vs 🏠) sit close
together; hard to tell apart and to know which bucket a bill belongs in.
**Fix:** Give the two categories clearly distinct icons (e.g. Housing → house;
Household → basket/cart/cleaning). **Open question:** also rename one for intent
clarity (e.g. "Home services" vs "Housing")? See decision list.

### 1.4 Pool amount input — remove stepper affordance
**File:** `PoolCard.tsx` (add-payment form, amount `<input>`)
**Problem:** `type="number" step="1"` invites step-by-rupee interaction and shows
spinner affordance on some platforms; wrong for currency entry.
**Fix:** Switch to a clean numeric entry — `inputMode="numeric"` (or `"decimal"`),
strip spinner appearance, keep validation. No step arrows.

---

## Tier 2 — High-value, low-effort polish

### 2.1 Surface completion % as a number
**File:** `FixedTab.tsx`
`pct` is **already computed** and only feeds the progress bar. Print it
("100% complete" / "{pct}% paid") near the progress bar / celebration. Near-zero cost.

### 2.2 Per-category paid counts
**File:** `FixedTab.tsx` (`byCategory` group header)
Add "X of Y paid" to each category header alongside the subtotal. Data is already in
the grouped array; just count `paid` per group.

### 2.3 Collapsible category groups
**File:** `FixedTab.tsx`
Make each category group collapsible (chevron + count + subtotal in the header).
Reuse the expand/collapse pattern already in `PoolCard.tsx`. On a fully-paid month,
collapsed-by-default-with-subtotals turns a long scroll into a clean summary.
*(Streaming/SSR note N/A — client component.)*

### 2.4 Designed 100% done-state (replace the strikethrough wall)
**Files:** `FixedExpenseRow.tsx`, `PoolCard.tsx` (entry rows)
**Problem:** At 100%, every row is grey + `line-through`, which reads as
*disabled/inactive* rather than *accomplished*, and legibility drops.
**Fix:**
- Paid rows keep **normal-weight** label text (not strikethrough) with the green
  check + emerald amount; optional subtle muted "Paid" tag.
- Add an explicit celebration treatment at 100% (calm check badge + "All fixed
  expenses paid" + "₹0 pending" in emerald) — the approved mockup's top card.
- Keep strikethrough, if anywhere, only for the *single completed item among pending
  ones* case — not for a fully-paid month.

### 2.5 Unify check iconography
**Files:** `PoolCard.tsx` (status string uses emoji `✅` / `⚠️`), row tick components.
**Problem:** Three "checked" visuals coexist — circular green ✓ on items, emoji ✅ in
the pool status pill, and ⚡ doing double duty (Utilities category icon *and* Electric
Bills pool icon).
**Fix:** One check system. Replace the emoji `✅`/`⚠️` pool-status glyphs with the same
icon language used elsewhere (lucide / consistent set). Accept the ⚡ overlap or
differentiate the pool icon.

*(Optional, low priority: bump pencil/trash hit areas toward ~44px — currently
`size={12}`/`size={13}` with no padding.)*

---

## Tier 3 — Structural direction (scope separately / confirm timing)

### 3.1 Per-row due date + paid date
**Files:** backend model + `types/index.ts` (`Expense`), `FixedExpenseRow.tsx`
**Reality check from the data model:**
- `due_day` exists on **`FixedExpenseTemplate`**, not on the monthly `Expense`
  instance → showing "Due 5 Jun" per row needs a template→instance join.
- **No `paid_date` on `Expense`** (only `PoolEntry` has `paid_date`) → the "Paid 5 Jun"
  tags shown in the mockup need a **new field on `Expense` + backend write** on toggle.
This is additive backend work; the mockup's paid-date tags are illustrative, not free.

### 3.2 Cleaner overdue treatment
**File:** `FixedTab.tsx` (Section 1 — due reminders)
Optionally restyle the red `border-l-4` banners into a tidier card. **Keep
"Mark as paid"** — no "Pay Now"/payment-rail implication. (Coordinate with the
guardrail below.)

---

## Guardrail — Due-date / reminder integrity (do not regress)

The existing **due-reminder logic stays untouched and keeps working** through every
change in this spec:
- It lives in **Section 1** of `FixedTab.tsx`: `load()` fetches
  `/fixed/due-reminders/{month}` only when `isCurrent`, stores it in `reminders`, and
  renders the banners **at the very top, above the summary/celebration card**.
- Tier 1.1 (pending color) only touches the summary header's pending span — it does
  not read or alter `reminders`, and only changes the **zero-value** case (non-zero
  still shows red/amber).
- Tiers 2.x live in the fixed-expense section / row component (downstream of Section 1,
  no shared state). 1.2 lives in `DashboardPage`/`SummaryFlipCard` (further removed).
- The banner relies on `due_day` from `FixedExpenseTemplate`, which we are **not**
  modifying. Tier 3.1's new `paid_date` is additive and unrelated to the banner.
- **Placement rule:** the overdue banner remains pinned at the top, above the new
  summary/celebration card. In the all-paid mockup it simply isn't shown because
  `reminders.length === 0`.

---

## Open decisions for Debashish (block implementation)
1. **Privacy model** — 1.2 option (A) global toggle / (B) gate nothing / (C) gate all?
2. **Household rename** — keep "Household" with a new icon, or rename (e.g. "Home
   services") in addition to the icon change?
3. **Tier 3 timing** — paid-date + due-date this sprint, or split into a follow-up
   spec once Tier 1–2 ships?

---

## Suggested sequencing
1. Tier 1.1, 1.3, 1.4 (self-contained, no decisions blocking 1.1/1.3/1.4 except the
   rename in 1.3).
2. Tier 2.1–2.5 (FixedTab + row + pool polish; the visible redesign).
3. Tier 1.2 once the privacy model is chosen.
4. Tier 3 as a separate spec (backend field + join) if timing is "follow-up".

---

## Files touched (reference)
| Concern | File |
|---|---|
| Pending color, completion %, category counts, collapsibility | `frontend/react/src/components/tabs/FixedTab.tsx` |
| Row paid-state (strikethrough → accomplished), paid-date tag, hit area | `frontend/react/src/components/tabs/FixedExpenseRow.tsx` |
| Pool input, pool entry paid-state, status iconography | `frontend/react/src/components/tabs/PoolCard.tsx` |
| Category icons (Household vs Housing) | `frontend/react/src/utils/categories.ts` |
| Privacy model (flip cards / strip) | `frontend/react/src/pages/DashboardPage.tsx`, `frontend/react/src/components/shared/SummaryFlipCard.tsx`, `…/SummaryStrip.tsx` |
| Tier 3: `paid_date` on Expense | backend model + `frontend/react/src/types/index.ts` |
