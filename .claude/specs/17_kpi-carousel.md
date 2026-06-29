# Spec 17 — KPI Carousel (Replacing 3-Column Grid)
**Date**: 2026-06-28
**Status**: ✅ Implemented — 2026-06-28
**Branch**: `feature/sprint06261-ui-enhancement`
**Follows**: `16_overview-followup-fixes.md`
**Source**: KPI carousel design review + preview v2 approved June 28, 2026

---

## Context

The current 3-column KPI grid (Remaining | Income | Bills Paid) breaks on iPhone 15:
- "REMAINING" label clips at the right edge of its tile
- "BILLS PAID" label wraps to two lines, making the tile taller than its siblings
- "Out of ₹97,567" subtitle is unreadably small at ~8px
- No room to add a 4th KPI (e.g. Savings) without breaking the layout entirely

This spec replaces the 3-tile grid with a **swipeable full-width card carousel**
in the style of banking card UIs (ICICI iMobile reference), with a stacked-deck
visual effect. The preview HTML (`kpi-carousel-v2.html`) was approved on June 28, 2026.

---

## Design Decision Record

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Wrap vs stop at ends | **Stop at ends** | 3 finite KPIs — users should know they've seen all cards. Dot indicators confirm position. |
| Auto-advance | **No** | Financial data must never move without user intent |
| Card content on hidden cards | **Empty gradient divs** | Only active + peek-right card need real data. Simplifies implementation, improves perf. |
| Desktop layout | **All 3 visible, center card enlarged** | Desktop has width to show side cards scaled down. No dots needed on desktop ≥ 768px. |
| Swipe direction | **Right-to-left = advance** | iOS/Android standard convention |

---

## Card Definitions

Three cards, fixed order:

| Position | Label | Value | Subtitle | Color family |
|----------|-------|-------|----------|-------------|
| 1 | 💰 Remaining | `remainingBalance` | "Left for the month" | Green |
| 2 | 💼 Income | `totalIncome` | "Total this month" | Purple |
| 3 | ✅ Bills Paid | `billsPaid` | "Out of ₹{totalBills}" + pending line | Amber/Gold |

Bills Paid subtitle has two lines:
- Line 1: `Out of ₹{totalBills}`
- Line 2 (conditional, if pendingAmount > 0): `₹{pendingAmount} still pending` in danger color

---

## Card Colors — Dark & Light Mode

The cards use **self-contained gradients** — they do not inherit from CSS variable tokens
because the gradient must remain bold and legible regardless of theme. However the
**text colors inside the card** and the **subtitle/pending colors** do adapt.

### Card 1 — Remaining (Green)

**Dark mode:**
```css
background: linear-gradient(135deg, #0a4a2e 0%, #0d6b3f 35%, #1a9e58 70%, #00c96e 100%);
```
**Light mode:**
```css
background: linear-gradient(135deg, #0d6b3f 0%, #1a9e58 40%, #00c96e 75%, #34d399 100%);
```
Light mode shifts the gradient lighter (mid-tones become highlights) so the card
doesn't look muddy on a white background. Value and label text stay white on both modes
because the card surface is always dark-enough green.

### Card 2 — Income (Purple)

**Dark mode:**
```css
background: linear-gradient(135deg, #1a0a4a 0%, #2e1080 35%, #5a28c8 70%, #7c55ff 100%);
```
**Light mode:**
```css
background: linear-gradient(135deg, #2e1080 0%, #5a28c8 40%, #7c55ff 75%, #a78bfa 100%);
```
Same logic — lighter endpoint on light mode. White text throughout.

### Card 3 — Bills Paid (Amber/Gold)

**Dark mode:**
```css
background: linear-gradient(135deg, #3a1a00 0%, #7a3800 35%, #c86000 70%, #f0920a 100%);
```
**Light mode:**
```css
background: linear-gradient(135deg, #7a3800 0%, #c86000 40%, #f0920a 75%, #fbbf24 100%);
```

### How to apply theme-aware gradients

Use a CSS class + `html.light` override, matching the existing pattern in `index.css`:

```css
/* Dark (default) */
.kpi-card-remaining { background: linear-gradient(135deg, #0a4a2e, #0d6b3f, #1a9e58, #00c96e); }
.kpi-card-income    { background: linear-gradient(135deg, #1a0a4a, #2e1080, #5a28c8, #7c55ff); }
.kpi-card-bills     { background: linear-gradient(135deg, #3a1a00, #7a3800, #c86000, #f0920a); }

/* Light overrides */
html.light .kpi-card-remaining { background: linear-gradient(135deg, #0d6b3f, #1a9e58, #00c96e, #34d399); }
html.light .kpi-card-income    { background: linear-gradient(135deg, #2e1080, #5a28c8, #7c55ff, #a78bfa); }
html.light .kpi-card-bills     { background: linear-gradient(135deg, #7a3800, #c86000, #f0920a, #fbbf24); }
```

### Text inside cards

Card text is always white regardless of theme — the gradient background is always
dark-enough to maintain contrast on both modes. Do NOT use `var(--text)` inside cards.

```css
.kpi-card-value    { color: #ffffff; }
.kpi-card-label    { color: rgba(255,255,255,0.70); }
.kpi-card-sub      { color: rgba(255,255,255,0.50); }
.kpi-card-pending  { color: rgba(255,180,100,0.90); } /* warm highlight, works on amber bg */
```

---

## Visual Anatomy of Each Card

```
┌─────────────────────────────────────┐
│  💰  REMAINING          [WM]        │  ← label row: icon + label left, watermark right
│                                     │
│                                     │
│  ₹3,479                             │  ← value: 30px bold white
│  Left for the month                 │  ← subtitle: 11px white/50
└─────────────────────────────────────┘
```

Additional card surface details (purely CSS, no extra DOM):
- `::before` pseudo: radial highlight at top-left (white, 25% opacity, overlay blend)
- `::after` pseudo: diagonal shine streak (white, 6% opacity)
- "WM" watermark text: `font-size: 20px`, `font-weight: 900`, `color: rgba(255,255,255,0.07)`, italic
- Left accent bar: `position: absolute; left:0; top:16px; bottom:16px; width:3px; border-radius:0 3px 3px 0`
  - Green card: `#00c96e`
  - Purple card: `#a78bfa`
  - Amber card: `#fbbf24`

---

## Layout & Dimensions

### Mobile (< 768px)

```
┌──── phone width (390px) ────────────────┐
│  [padding 18px]                         │
│  ┌────────────────────────┐  ┌──┐       │
│  │                        │  │  │ peek  │
│  │   ACTIVE CARD          │  │  │ ~28px │
│  │   264px wide           │  │  │       │
│  │   150px tall           │  └──┘       │
│  └────────────────────────┘             │
│       stacked cards behind (abs pos)   │
│  [dots centered below]                  │
└─────────────────────────────────────────┘
```

- Active card: `width: 264px`, `height: 150px`, `border-radius: 22px`
- Card container height: `186px` (card 150px + 18px top + 18px breathing room)
- Peek width: `~28px` visible of the next card at right edge
- Stack behind: 2 empty gradient divs, `rotate(-2deg)` and `rotate(-4deg)`, `scale(0.94)` and `scale(0.88)`
- Dots: centered, active dot `width: 20px border-radius: 3px`, inactive `width: 6px circle`
- Dot active color: `var(--accent)` (#6366f1)

### Desktop (≥ 768px)

All 3 cards visible simultaneously:
- Active (center): `width: 380px`, `height: 140px`, `scale(1)`, `opacity: 1`, `z-index: 3`
- Side cards: `width: 260px`, `height: 140px`, `scale(0.93)`, `opacity: 0.6`, `z-index: 2`
- No stacking effect on desktop — horizontal layout only
- No dot indicators on desktop (position is obvious from visual scale)
- Clicking a side card on desktop makes it the active card (slides to center)

---

## Interaction Specification

### Mobile swipe gesture
- Listen for `touchstart` / `touchmove` / `touchend` on the carousel container
- Swipe threshold: `> 40px` horizontal delta to trigger advance
- Velocity shortcut: fast flick (> 0.3px/ms) triggers advance even under 40px
- Direction: left swipe = advance (1→2→3), right swipe = retreat (3→2→1)
- **No wrap**: swiping left on card 3 does nothing; swiping right on card 1 does nothing
- Visual resistance: on boundary cards, allow slight elastic drag (max 20px) then snap back

### Animation
- Duration: `350ms`
- Easing: `cubic-bezier(0.25, 0.46, 0.45, 0.94)` (iOS-standard decelerate)
- What animates during transition:
  - Active card: `translateX(-100%)` + `scale(0.92)` exit
  - Incoming card: `translateX(0)` + `scale(1)` enter from right
  - Stack behind: rotation and scale update simultaneously
  - Dot: active pill slides to new position

### Dot tap (mobile)
Tapping a dot directly navigates to that card position with the same animation.

### Desktop click
Clicking a side card slides it to center. No swipe gesture needed on desktop.

---

## State Management

```ts
// New state in OverviewTab
const [activeKpiIndex, setActiveKpiIndex] = useState(0); // 0 | 1 | 2

// Cards array (derived from existing data — no new API needed)
const kpiCards = [
  {
    id: 'remaining',
    label: 'Remaining',
    icon: '💰',
    value: formatCurrency(data.remainingBalance),
    subtitle: 'Left for the month',
    pending: null,
    colorClass: 'kpi-card-remaining',
  },
  {
    id: 'income',
    label: 'Income',
    icon: '💼',
    value: formatCurrency(data.totalIncome),
    subtitle: 'Total this month',
    pending: null,
    colorClass: 'kpi-card-income',
  },
  {
    id: 'bills',
    label: 'Bills Paid',
    icon: '✅',
    value: formatCurrency(data.billsPaid),
    subtitle: `Out of ${formatCurrency(data.totalBills)}`,
    pending: data.pendingAmount > 0
      ? `${formatCurrency(data.pendingAmount)} still pending`
      : null,
    colorClass: 'kpi-card-bills',
  },
];
```

No new backend endpoints required. All values come from existing `data` object
already used by the removed 3-tile grid.

---

## Component Structure

```tsx
{/* ── Section: KPI Carousel ─────────────────────── */}
<div className="kpi-carousel-wrapper">

  {/* Card stage */}
  <div
    className="kpi-carousel-stage"
    onTouchStart={handleTouchStart}
    onTouchMove={handleTouchMove}
    onTouchEnd={handleTouchEnd}
  >
    {/* Stacked decorative cards (behind, no content) */}
    <div className={`kpi-card-shell kpi-card-${getCardAt(activeKpiIndex, 2).id} pos-far-behind`} />
    <div className={`kpi-card-shell kpi-card-${getCardAt(activeKpiIndex, 1).id} pos-behind`} />

    {/* Active card */}
    <KpiCard card={kpiCards[activeKpiIndex]} position="active" />

    {/* Peek card (next, right edge) */}
    {activeKpiIndex < 2 && (
      <div className={`kpi-card-shell kpi-card-${kpiCards[activeKpiIndex + 1].id} pos-peek-right`} />
    )}
  </div>

  {/* Dots — mobile only */}
  <div className="kpi-dots md:hidden">
    {kpiCards.map((_, i) => (
      <button
        key={i}
        className={`kpi-dot ${i === activeKpiIndex ? 'active' : ''}`}
        onClick={() => navigateTo(i)}
        aria-label={`View ${kpiCards[i].label}`}
      />
    ))}
  </div>

  {/* Desktop: all 3 visible */}
  <div className="kpi-desktop-row hidden md:flex">
    {kpiCards.map((card, i) => (
      <KpiCard
        key={card.id}
        card={card}
        position={i === activeKpiIndex ? 'active' : 'side'}
        onClick={() => navigateTo(i)}
      />
    ))}
  </div>

</div>
```

---

## CSS to Add to index.css

Add after the existing `/* ── Flip card ──` section:

```css
/* ══════════════════════════════════════════════════════════════
   KPI CAROUSEL — Spec 17
   ══════════════════════════════════════════════════════════════ */

/* Card gradients — dark (default) */
.kpi-card-remaining { background: linear-gradient(135deg, #0a4a2e 0%, #0d6b3f 35%, #1a9e58 70%, #00c96e 100%); }
.kpi-card-income    { background: linear-gradient(135deg, #1a0a4a 0%, #2e1080 35%, #5a28c8 70%, #7c55ff 100%); }
.kpi-card-bills     { background: linear-gradient(135deg, #3a1a00 0%, #7a3800 35%, #c86000 70%, #f0920a 100%); }

/* Card gradients — light mode */
html.light .kpi-card-remaining { background: linear-gradient(135deg, #0d6b3f 0%, #1a9e58 40%, #00c96e 75%, #34d399 100%); }
html.light .kpi-card-income    { background: linear-gradient(135deg, #2e1080 0%, #5a28c8 40%, #7c55ff 75%, #a78bfa 100%); }
html.light .kpi-card-bills     { background: linear-gradient(135deg, #7a3800 0%, #c86000 40%, #f0920a 75%, #fbbf24 100%); }

/* Text inside cards — always white regardless of theme */
.kpi-card-value   { color: #ffffff; }
.kpi-card-label   { color: rgba(255, 255, 255, 0.70); }
.kpi-card-sub     { color: rgba(255, 255, 255, 0.50); }
.kpi-card-pending { color: rgba(255, 180, 100, 0.90); }
```

---

## Acceptance Criteria

### Functional
- [ ] Three cards swipe correctly left/right on iPhone 15 Safari
- [ ] No wrap: card 1 has no right-swipe, card 3 has no left-swipe
- [ ] Elastic resistance on boundary (max 20px drag, snaps back)
- [ ] Dot indicator updates on every card change
- [ ] Dot tap navigates directly to that card
- [ ] Desktop shows all 3 cards, clicking side card activates it

### Visual
- [ ] "REMAINING" label fully visible, no clipping, on iPhone 15
- [ ] "BILLS PAID" label on one line, no wrapping
- [ ] "Out of ₹97,567" subtitle readable (≥ 11px)
- [ ] Pending amount visible in warm highlight color when > 0
- [ ] Stacked cards visible behind active card on mobile
- [ ] Peek of next card visible at right edge on mobile (unless on last card)
- [ ] All card text remains white on both dark and light theme
- [ ] Gradients remain vibrant and distinguishable on light mode (`html.light`)
- [ ] "WM" watermark faintly visible on card surface
- [ ] Left accent bar present on all three cards

### Regression
- [ ] Removing 3-tile grid does not break any data references elsewhere in OverviewTab
- [ ] `formatCurrency` utility reused — no new formatting logic
- [ ] No new API endpoints or backend changes required
- [ ] Light/dark theme toggle still works across entire Overview tab

---

## Files Modified

- `frontend/react/src/components/tabs/OverviewTab.tsx`
  — Remove 3-column KPI grid
  — Add `KpiCarousel` component (can be inline or extracted to `components/ui/KpiCarousel.tsx`)
  — Add `activeKpiIndex` state
  — Add touch gesture handlers

- `frontend/react/src/index.css`
  — Add KPI carousel gradient classes (dark + light overrides)
  — Add card text color helpers

## Files NOT Modified
- `backend/` — no changes
- `frontend/react/src/types/index.ts` — no new types needed
- Any other component
