# Implementation Plan: KPI Carousel — Native Scroll-Snap Rebuild (Mobile)
**Spec**: `.claude/specs/21_kpi-carousel-slide-math-fix.md`
**Date**: 2026-06-28
**Branch**: `feature/sprint06261-ui-enhancement`

---

## Overview

2 files modified — no backend changes.
5 items total, ordered smallest-blast-radius-first.
Items 1–4 are in `OverviewTab.tsx` and must be executed in order. Item 5 (CSS) is independent.

---

## Item 1 — Delete 4 dead gesture refs

**Scope**: Frontend-only
**File**: `frontend/react/src/components/tabs/OverviewTab.tsx`, lines 203–206

**Root cause (verified)**: Four `useRef` hooks exist solely to track touch gesture state for the deleted gesture handler. After Item 2 removes the `useEffect`, these are unused:

```tsx
const touchStartX       = useRef<number>(0);       // line 203
const touchStartTime    = useRef<number>(0);       // line 204
const touchStartY       = useRef<number>(0);       // line 205
const isHorizontalSwipe = useRef<boolean | null>(null); // line 206
```

**What to do**: Delete lines 203–206. Keep `carouselRef` (line 207) — it moves to the new `.kpi-scroller` element.

---

## Item 2 — Delete the touch gesture useEffect

**Scope**: Frontend-only
**File**: `frontend/react/src/components/tabs/OverviewTab.tsx`, lines 251–295

**Root cause (verified)**: The second `useEffect` (lines 251–295) attaches `touchstart`/`touchmove`/`touchend` listeners with `{ passive: false }`. This is the recurring iOS Safari failure point across specs 17, 18, 19, 21a.

**What to do**: Delete lines 251–295 in their entirety. The `useEffect` on line 245 (`load()`) is unrelated — keep it.

Keep `navigateTo` (lines 247–249) — it is still used by the desktop row `onClick` (line 410).

---

## Item 3 — Add handleScroll and scrollToCard callbacks

**Scope**: Frontend-only
**File**: `frontend/react/src/components/tabs/OverviewTab.tsx`, insert after line 249

**What to do**: Insert after the `navigateTo` block:

```tsx
const handleScroll = useCallback(() => {
  const el = carouselRef.current;
  if (!el) return;
  const slideWidth = el.querySelector('.kpi-slide')?.clientWidth ?? el.clientWidth;
  const index = Math.round(el.scrollLeft / slideWidth);
  setActiveKpiIndex(Math.max(0, Math.min(2, index)));
}, []);

const scrollToCard = useCallback((index: number) => {
  const el = carouselRef.current;
  if (!el) return;
  const slide = el.children[index] as HTMLElement | undefined;
  if (slide) {
    el.scrollTo({ left: slide.offsetLeft, behavior: 'smooth' });
  }
}, []);
```

`handleScroll` uses the first `.kpi-slide` child's `clientWidth` as divisor (more accurate than `el.clientWidth` when slides have a peek). `scrollToCard` uses `slide.offsetLeft` so it works correctly regardless of gap or padding.

**Dependency**: Items 1 and 2 first.

---

## Item 4 — Replace mobile carousel JSX and update dot buttons

**Scope**: Frontend-only
**File**: `frontend/react/src/components/tabs/OverviewTab.tsx`, lines 366–401

**Root cause (verified)**: Current structure is two elements — outer `.kpi-viewport` (lines 366, 389) clips overflow, inner `.kpi-track` (lines 368–388) slides via inline `translateX`. The JS-transform approach breaks on iOS Safari.

**What to do**:

Replace lines 366–389 with a single scrollable element:

```tsx
{/* Mobile: native scroll-snap carousel */}
<div
  ref={carouselRef}
  className="kpi-scroller md:hidden"
  onScroll={handleScroll}
>
  {kpiCards.map((card) => (
    <div key={card.id} className={`kpi-slide kpi-card-${card.id}`}>
      <div className="kpi-accent" />
      <span className="kpi-watermark">WM</span>
      <div className="kpi-slide-header">
        <span className="kpi-slide-icon">{card.icon}</span>
        <span className="kpi-card-label">{card.label}</span>
      </div>
      <p className="kpi-card-value">{card.value}</p>
      <p className="kpi-card-sub">{card.subtitle}</p>
      {card.pending && <p className="kpi-card-pending">{card.pending}</p>}
    </div>
  ))}
</div>
```

`ref` moves to `.kpi-scroller`. No `transform`/`transition` inline styles. All card inner content unchanged.

Also update dot button onClick (line 397):

```tsx
// from:
onClick={() => navigateTo(i)}
// to:
onClick={() => scrollToCard(i)}
```

**Dependency**: Items 1, 2, 3 first.

---

## Item 5 — Update CSS in index.css

**Scope**: Frontend-only
**File**: `frontend/react/src/index.css`
**Independent** — can be done in any order relative to Items 1–4.

**Root cause (verified)**:
- `.kpi-viewport` (lines 273–277) — clip container, delete
- `.kpi-track` (lines 279–283) — flex + `will-change: transform`, delete
- `.kpi-slide` (lines 285–292) — `flex: 0 0 calc(100% - 24px)`, no snap alignment
- `@media (min-width: 768px)` block (lines 344–346) — hides `.kpi-viewport`; update to `.kpi-scroller`

**What to do**:

### 5a — Delete `.kpi-viewport` (lines 273–277)
```css
/* DELETE */
.kpi-viewport {
  overflow: hidden;
  padding: 0 18px;
  margin: 0 -2px;
}
```

### 5b — Delete `.kpi-track` (lines 279–283)
```css
/* DELETE */
.kpi-track {
  display: flex;
  gap: 12px;
  will-change: transform;
}
```

### 5c — Add `.kpi-scroller` in their place
```css
/* Mobile native scroll-snap carousel */
.kpi-scroller {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;
  scroll-behavior: smooth;
  padding: 0 18px;
  scroll-padding-left: 18px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.kpi-scroller::-webkit-scrollbar { display: none; }
```

### 5d — Update `.kpi-slide` (lines 285–292)

Before:
```css
.kpi-slide {
  flex: 0 0 calc(100% - 24px);
  height: 150px;
  border-radius: 22px;
  position: relative;
  overflow: hidden;
  padding: 18px 20px;
}
```

After (change `flex`, add `scroll-snap-align`):
```css
.kpi-slide {
  flex: 0 0 calc(100% - 52px);   /* next card peeks ~34px on the right */
  scroll-snap-align: start;
  height: 150px;
  border-radius: 22px;
  position: relative;
  overflow: hidden;
  padding: 18px 20px;
}
```

Adjust `52px` to taste — larger = more peek.

### 5e — Update @media block (lines 344–346)

Before:
```css
  .kpi-viewport,
  .kpi-dots { display: none; }
```

After:
```css
  .kpi-scroller,
  .kpi-dots { display: none; }
```

All other rules inside the `@media` block are unchanged.

---

## Execution Order

| # | Item | Blast radius | Dependency |
|---|------|-------------|------------|
| 5 | CSS: viewport/track → scroller | CSS-only | None |
| 1 | Delete 4 dead refs | Trivial | None |
| 2 | Delete touch useEffect | One block | After 1 |
| 3 | Add handleScroll + scrollToCard | Additive | After 1, 2 |
| 4 | Replace mobile JSX + dot onClick | JSX restructure | After 1, 2, 3 |

---

## Definition of Done

- `npm run build` passes — zero TS errors, zero ESLint warnings
- iPhone 15 Safari: swipe left/right scroll-snaps between the three KPI cards natively
- Dot indicator updates as user swipes
- Tapping a dot smooth-scrolls to that card
- Next card peeks ~30–40px on the right when not on the last card
- No horizontal scrollbar visible
- No `touchstart`/`touchmove`/`touchend` listeners remain in the file
- `touchStartX`, `touchStartY`, `touchStartTime`, `isHorizontalSwipe` refs gone
- Desktop (≥768px): `.kpi-desktop-row` and click-to-activate unchanged
