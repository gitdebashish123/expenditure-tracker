# Implementation Plan: Fixed Tab Follow-up — Instant Reflection, Eye Removal, KPI-Carousel Cards
**Spec**: `.claude/specs/23_fixed-tab-followup-fixes.md`
**Date**: 2026-06-29
**Status**: ✅ Implemented 2026-06-29
**Branch**: `feature/sprint06261-ui-enhancement` *(confirm active branch before starting)*

---

## Overview

3 items, **frontend-only, 0 backend changes**. Recommended order: **Item 1 → 2 → 3**
(instant-reflection first so the new cards visibly move on tick). Items 2 & 3 both touch
the Fixed band in `DashboardPage.tsx`.

| # | Item | Files | Risk |
|---|------|-------|------|
| 1 | Instant reflection (toggle → summary refetch) | `DashboardPage.tsx`, `FixedTab.tsx` | Low |
| 2 | Remove privacy eye + force-unhide | `Header.tsx`, `PrivacyContext.tsx` | Low |
| 3 | Cards → shared KPI carousel, amber fixed deck | `KpiCarousel.tsx` (new), `OverviewTab.tsx`, `DashboardPage.tsx`, retire `SummaryStrip`/`SummaryFlipCard` | Med (carousel extraction) |

---

## Item 1 — Instant reflection

**Root cause** (verified): `FixedTab.togglePaid` updates local `fixedExps` + PATCHes
`/fixed/{id}/toggle`, but never triggers `DashboardShell.fetchSummary`. `bumpRefresh` is
wired to `QuickAddTab` only; `FixedTab` is rendered bare.

### 1a. `DashboardPage.tsx` — pass the refresh callback

```tsx
// before:
// {tab === "fixed" && <ErrorBoundary><FixedTab /></ErrorBoundary>}
{tab === "fixed" && <ErrorBoundary><FixedTab onChanged={bumpRefresh} /></ErrorBoundary>}
```

### 1b. `FixedTab.tsx` — accept + fire the callback

```tsx
// signature:
export function FixedTab({ onChanged }: { onChanged?: () => void }) {

// in togglePaid, after the PATCH succeeds:
await api.patch(`/fixed/${id}/toggle`);
onChanged?.();          // refresh summary cards in the parent

// also call onChanged?.() after a successful amount edit save.
```

**Acceptance:** ticking/unticking a fixed item updates the summary cards (amounts +
counts) within ~1 refetch; rows still update instantly (optimistic).

---

## Item 2 — Remove privacy eye + force-unhide

### 2a. `Header.tsx` — remove the control

```tsx
// import: drop Eye, EyeOff
import { Sun, Moon } from "lucide-react";
// remove: import { usePrivacy } from "@/context/PrivacyContext";
// remove inside Header(): const { valuesHidden, togglePrivacy } = usePrivacy();
// DELETE the eye <button> from right-controls; keep theme toggle + <ProfileDropdown/>.
```

### 2b. `PrivacyContext.tsx` — force-unhide (no stranded users)

The value persists to `localStorage` (`walletmantra_privacy_mode`). With the control gone,
anyone previously on "hide" would be stuck masked. Initialize to **false** and clear the
key once:

```tsx
// in the provider init:
const [valuesHidden, setValuesHidden] = useState(false);  // was: read from localStorage
useEffect(() => { localStorage.removeItem("walletmantra_privacy_mode"); }, []);
```

Keep `togglePrivacy`/`valuesHidden` exported and the consumer reads intact (dormant) so
re-adding an eye later is trivial.

**Acceptance:** no eye anywhere; all amounts visible on every tab; no stuck-hidden state.

---

## Item 3 — Cards → shared KPI carousel (Option A), amber fixed deck

### 3a. New `components/shared/KpiCarousel.tsx` (extract from OverviewTab)

Move the inline carousel out of `OverviewTab.tsx`: `carouselRef`, `activeKpiIndex`,
`navigateTo`, `handleScroll`, `scrollToCard`, the `.kpi-slide` stage, dots, and the
desktop row. Parameterize accent + gradient (were keyed by card id).

```tsx
export interface KpiCard {
  id: string; label: string; value: string; subtitle: string;
  accent: string; gradientClass: string; pending?: string | null;
}

export function KpiCarousel({ cards }: { cards: KpiCard[] }) {
  const [activeKpiIndex, setActiveKpiIndex] = useState(0);
  const carouselRef = useRef<HTMLDivElement>(null);
  // ...handleScroll / scrollToCard / navigateTo moved here verbatim from OverviewTab...
  // render: .kpi-slide cards using card.gradientClass + card.accent (accent bar),
  //         kpi-card-value/label/sub, dots (md:hidden), desktop row (hidden md:flex).
}
```

> Accent bar + gradient now come from `card.accent` / `card.gradientClass` instead of a
> per-id switch — that's the only behavioral change to the extracted code.

### 3b. `OverviewTab.tsx` — use the shared component

Replace the inline carousel JSX with `<KpiCarousel cards={kpiCards} />` and remove the
now-moved state/handlers (`activeKpiIndex`, `carouselRef`, `navigateTo`, `handleScroll`,
`scrollToCard`). Add `accent` + `gradientClass` to each `kpiCards` entry:

```ts
// remaining → accent "#00c96e", gradientClass "kpi-card-remaining"
// income    → accent "#a78bfa", gradientClass "kpi-card-income"
// bills      → accent "#fbbf24", gradientClass "kpi-card-bills"
```

**Regression check:** Overview carousel must look/behave identically after extraction
(swipe, dots, desktop scale, light/dark gradients).

### 3c. `DashboardPage.tsx` — fixed deck + counts wiring

```tsx
// add state + wire fixed_progress:
const [fixedProgress, setFixedProgress] = useState<Summary["fixed_progress"] | null>(null);
// in fetchSummary:
.then(r => { setBalance(r.data.balance); setFixedProgress(r.data.fixed_progress); })

// build the deck (all amber → one "fixed" deck):
const totalFixed = balance.fixed_paid_total + balance.fixed_unpaid_total;
const totalCount = fixedProgress?.total ?? 0;
const paidCount  = fixedProgress?.paid  ?? 0;
const left       = balance.fixed_unpaid_total;
const fixedCards: KpiCard[] = [
  { id:"fx-total", label:"Fixed total", value: fmtInr(totalFixed),
    subtitle:`${totalCount} items this month`, accent:"#fbbf24", gradientClass:"kpi-card-bills" },
  { id:"fx-paid",  label:"Fixed paid",  value: fmtInr(balance.fixed_paid_total),
    subtitle:`${paidCount} of ${totalCount} items`, accent:"#34d399", gradientClass:"kpi-card-bills" },
  { id:"fx-left",  label:"Fixed left",  value: fmtInr(left),
    subtitle: left === 0 ? "All clear" : `${totalCount - paidCount} pending`,
    accent: left === 0 ? "#34d399" : "#f59e0b", gradientClass:"kpi-card-bills" },
];

// in the tab === "fixed" block, REPLACE <SummaryStrip/> + <SummaryFlipCard/> with:
<KpiCarousel cards={fixedCards} />
```

### 3d. Retire the old cards

- Remove `SummaryStrip` / `SummaryFlipCard` imports + usage from `DashboardPage.tsx`.
- Delete `components/shared/SummaryStrip.tsx` and `SummaryFlipCard.tsx` **after** confirming
  no other importers.
- Remove the now-dead `.flip-card*` rules from `index.css`.

**Acceptance (Item 3):**
- Fixed shows a 3-card amber carousel: **Fixed total / Fixed paid / Fixed left** with
  "items" counts; swipe + dots on mobile, all-3 on desktop.
- Visually one amber deck, distinct from Overview's green/purple/amber.
- Overview carousel unchanged.
- Ticking a bill (Item 1) moves Fixed paid/left + counts; "Fixed left" accent goes
  emerald at ₹0 ("All clear"), amber otherwise.

---

## Guardrail (carried from Spec 22)
`FixedTab` Section 1 (due reminders) untouched; overdue banner stays pinned at top.
Nothing here reads `reminders` or `due_day`.

---

## Execution order summary

| # | Step | File(s) |
|---|------|---------|
| 1a | pass `onChanged={bumpRefresh}` | `pages/DashboardPage.tsx` |
| 1b | accept + fire `onChanged` in toggle/edit | `components/tabs/FixedTab.tsx` |
| 2a | remove eye | `components/layout/Header.tsx` |
| 2b | force-unhide + clear storage | `context/PrivacyContext.tsx` |
| 3a | extract `KpiCarousel` | `components/shared/KpiCarousel.tsx` (new) |
| 3b | OverviewTab uses shared carousel | `components/tabs/OverviewTab.tsx` |
| 3c | fixed deck + `fixed_progress` wiring | `pages/DashboardPage.tsx` |
| 3d | retire SummaryStrip/SummaryFlipCard + flip-card CSS | `shared/*`, `index.css` |

Land as one Fixed-band feature commit. Build-verify, then re-screenshot Overview (regression)
+ Fixed (new deck) on iPhone 15 Safari + desktop.
