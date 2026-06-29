# Spec 23 — Fixed Tab Follow-up: Instant Reflection, Eye Removal, KPI-Carousel Cards
**Date**: 2026-06-29
**Status**: ✅ Implemented 2026-06-29
**Branch**: `feature/sprint06261-ui-enhancement` *(confirm active branch before starting)*
**Follows**: `22_fixed-tab-ux-redesign.md`
**Source**: re-review of the **shipped** Spec 22 build (iPhone 15 Safari + desktop), June 29 2026; carousel reference from Specs 17/19/21; approved interactive mockup (Option A, amber "fixed" deck).

---

## Revision history
- **v1** — privacy eye *relocation* + summary cards to mockup tiles (option b metrics).
- **v2 (this)** — superseded after re-review + decisions:
  - Eye is **removed for now** (not relocated) — frees a row; revisit later.
  - Summary cards adopt the **Overview KPI carousel** look & feel (**Option A**), as a
    distinct **single amber "fixed" deck**.
  - Labels: **Fixed total / Fixed paid / Fixed left**; count noun **"items"** (not
    "bills" — the tab holds EMIs, rent, transfers, SIPs/savings, subscriptions, not only bills).
  - New **instant-reflection** fix: ticking a bill must update the summary cards immediately.

---

## Context

Spec 22 shipped Tier 1–2 (Option A privacy, ₹0-pending fix, completion %, category
counts, collapsible groups, 100% celebration, paid-state rows, pool input). Re-review of
the live build + a look-and-feel pass against the Overview carousel produced three
changes, all **frontend-only, 0 backend**:

1. **Instant reflection** — ticking/unticking a fixed item doesn't move the summary cards.
2. **Remove the privacy eye** for now (it occupies a row; revisit later).
3. **Summary cards → KPI carousel** (Option A) as a distinct amber "fixed" deck.

### Decisions (all locked 2026-06-29)
| Decision | Choice |
|---|---|
| Card layout | **Option A — swipe carousel** (same pattern as Overview) |
| Visual identity | **Single amber deck** (reuse `.kpi-card-bills` gradient for all 3) — distinct from Overview's green/purple/amber trio |
| Labels | **Fixed total / Fixed paid / Fixed left** |
| Count noun | **items** (e.g. "18 of 20 items") |
| Metrics | option (b): Total fixed / Fixed paid / Fixed unpaid (+ counts) |
| Privacy eye | **Remove** + force-unhide; keep `PrivacyContext` plumbing dormant |

---

## Item 1 — Instant reflection: toggle must refresh the summary cards (NEW)

**Root cause (verified):** the checklist and the summary cards are fed by **two
independent fetches that don't communicate**.
- `FixedTab.togglePaid` optimistically updates its own `fixedExps` state and PATCHes
  `/fixed/{id}/toggle` — and stops.
- The summary cards live in `DashboardShell`, fed by a separate `/summary/{month}` call
  (`fetchSummary`), re-run only when `refreshKey` changes.
- `bumpRefresh` is wired to `QuickAddTab` (`onExpenseAdded={bumpRefresh}`) but **not** to
  `FixedTab` (rendered as a bare `<FixedTab />`). So a tick never tells the parent to
  refetch → cards stay stale until `selMonth` changes.

**Fix:** pass `onChanged={bumpRefresh}` to `FixedTab`; call it after a successful toggle
(and after amount edits). Optionally also on pool changes if they affect summary totals.

**Note (optimistic lag):** rows update instantly; the refetch lags by one network round
trip, so cards update a beat later. Acceptable for now. (Lockstep would require lifting
the fixed totals to share `FixedTab`'s already-updated data — out of scope.)

**Why first:** Item 3 makes staleness far more visible (big "Fixed paid/left" cards that
don't move on tick). This must land before/with the carousel.

**Files:** `pages/DashboardPage.tsx`, `components/tabs/FixedTab.tsx`.

---

## Item 2 — Remove the privacy eye (for now) + force-unhide

**Why:** the shipped eye sits in the global `Header` (wrong scope) and occupies a row on
Fixed. Rather than relocate it now, **remove it**; revisit privacy later.

**Changes:**
1. `Header.tsx` — remove the eye `<button>`, the `Eye/EyeOff` imports, the
   `usePrivacy()` line. Keep theme toggle + `ProfileDropdown`.
2. **Force-unhide** so no one is stranded: `valuesHidden` persists to `localStorage`
   (`walletmantra_privacy_mode`). With the only control gone, a user who previously chose
   "hide" would be stuck masked. On load, **default `valuesHidden` to `false`** and clear
   the stored key (one-time).
3. **Keep the plumbing dormant:** leave `PrivacyContext` and the `valuesHidden` reads in
   `FixedTab` etc. in place (they resolve to "visible"), so re-adding an eye later is a
   one-line change, not a re-plumb.

**Files:** `components/layout/Header.tsx`, `context/PrivacyContext.tsx`.

---

## Item 3 — Summary cards → KPI carousel, single amber "fixed" deck (Option A)

**Goal:** the Fixed summary uses the **same carousel** as Overview (swipe + dots on
mobile, all-3 on desktop), but as a clearly **distinct deck** so it's never confused with
Overview's KPIs.

### 3.1 Extract the carousel into a shared component
The carousel is currently **inline in `OverviewTab.tsx`** (`carouselRef`, `kpiCards`
array, `.kpi-slide` children, `handleScroll`, `scrollToCard`, `navigateTo`,
`activeKpiIndex`, dots, desktop row). Extract it to
`components/shared/KpiCarousel.tsx` taking a `cards` prop, and parameterize the
**accent color** and **gradient class** (currently keyed by card id) as per-card props.

```ts
interface KpiCard {
  id: string;
  label: string;
  value: string;        // pre-formatted via fmtInr
  subtitle: string;
  accent: string;       // accent-bar color (was hardcoded per id)
  gradientClass: string;// e.g. "kpi-card-bills"
  pending?: string | null;
}
```

`OverviewTab` then renders `<KpiCarousel cards={kpiCards} />` (regression-safe — same
markup, just moved), with its three cards gaining `accent` + `gradientClass`
(remaining→`#00c96e`/`kpi-card-remaining`, income→`#a78bfa`/`kpi-card-income`,
bills→`#fbbf24`/`kpi-card-bills`).

### 3.2 Fixed deck
`DashboardShell` builds the fixed deck and renders `<KpiCarousel cards={fixedCards} />`
in the `tab === 'fixed'` block, **replacing `SummaryStrip` + `SummaryFlipCard`**.

```ts
const totalFixed = balance.fixed_paid_total + balance.fixed_unpaid_total;
const totalCount = fixedProgress?.total ?? 0;
const paidCount  = fixedProgress?.paid  ?? 0;
const left       = balance.fixed_unpaid_total;
const fixedCards = [
  { id:"fx-total", label:"Fixed total", value: fmtInr(totalFixed),
    subtitle: `${totalCount} items this month`, accent:"#fbbf24", gradientClass:"kpi-card-bills" },
  { id:"fx-paid",  label:"Fixed paid",  value: fmtInr(balance.fixed_paid_total),
    subtitle: `${paidCount} of ${totalCount} items`, accent:"#34d399", gradientClass:"kpi-card-bills" },
  { id:"fx-left",  label:"Fixed left",  value: fmtInr(left),
    subtitle: left === 0 ? "All clear" : `${totalCount - paidCount} pending`,
    accent: left === 0 ? "#34d399" : "#f59e0b", gradientClass:"kpi-card-bills" },
];
```

**Differentiation (the whole point):** all three Fixed cards share the **amber**
`.kpi-card-bills` gradient → reads as one "fixed" deck, visually distinct from Overview's
three-hue KPIs. The only semantic color is the **accent bar** (gold/emerald/amber). The
**"Fixed …"** labels never echo Overview's "Remaining / Income / Bills Paid".

### 3.3 Data wiring (counts)
Amounts are on `balance`; the **counts** come from `fixed_progress: { paid, total }`,
which `DashboardShell` does **not** currently store (keeps only `r.data.balance`). Store
`r.data.fixed_progress` alongside `balance` in `fetchSummary`.

### 3.4 Retire the old cards
`SummaryStrip` and `SummaryFlipCard` were Fixed-only; once the carousel replaces them,
remove their usage from `DashboardPage` and delete the files (confirm no other importers
first). The `.flip-card*` CSS in `index.css` becomes dead — remove.

**Files:** `components/shared/KpiCarousel.tsx` (new), `components/tabs/OverviewTab.tsx`
(use shared component), `pages/DashboardPage.tsx` (fixed deck + `fixed_progress` wiring),
`components/shared/SummaryStrip.tsx` + `SummaryFlipCard.tsx` (remove), `index.css`
(retire `.flip-card*`).

---

## Guardrail (carried from Spec 22 — do not regress)
- `FixedTab` **Section 1 (due reminders)** untouched; overdue banner stays pinned at top.
- Nothing here reads/alters `reminders` or `due_day`.
- The instant-reflection refetch hits `/summary/{month}` only — same endpoint already in use.

---

## Out of scope (still)
Search, filters, priority indicators, named "Tara" persona, any "Pay Now"/payment-rail
implication. **Tier 3** (per-row due/paid dates; needs `paid_date` on `Expense` +
backend) remains deferred to its own spec.

---

## Open decisions — none remaining
Layout (A/carousel), labels (Fixed total/paid/left), count noun (items), eye (remove),
and instant-reflection are all locked. Ready for the plan.
