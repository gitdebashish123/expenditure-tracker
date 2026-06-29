# Implementation Plan: KPI Carousel Rebuild — Sliding Track + Interactions
**Spec**: `.claude/specs/19_kpi-carousel-rebuild.md`
**Date**: 2026-06-28
**Branch**: `feature/sprint06261-ui-enhancement`

---

## Overview

3 items — all frontend-only. No backend changes.
Ordered smallest blast-radius first: CSS-only fixes before JSX rebuild.

| # | Item | Files | Effort |
|---|------|-------|--------|
| 1 | 19B — Subtitle contrast fix | `index.css` only | XS |
| 2 | 19C — Desktop card select animation | `index.css` only | XS |
| 3 | 19A — Rebuild mobile carousel as sliding track | `OverviewTab.tsx` + `index.css` | M |

Do 19B and 19C first (pure CSS, zero risk). Then 19A (the JSX rebuild that replaces the stacked-deck).

---

## Item 1 — 19B: Card Subtitle Text Too Faint

**Scope**: Frontend-only
**File**: `frontend/react/src/index.css` — lines 211–214

**Root cause** (verified against disk):
```css
/* line 212 */ .kpi-card-label   { color: rgba(255, 255, 255, 0.70); }
/* line 213 */ .kpi-card-sub     { color: rgba(255, 255, 255, 0.50); }
/* line 214 */ .kpi-card-pending { color: rgba(255, 180, 100, 0.90); }
```
`.kpi-card-sub` at 0.50 opacity is the primary readability problem. `.kpi-card-label` at 0.70 is borderline. `.kpi-card-pending` at 0.90 is close but can go brighter.

**What to do**:
Replace lines 212–214 with:
```css
.kpi-card-label   { color: rgba(255, 255, 255, 0.85); }  /* was 0.70 */
.kpi-card-sub     { color: rgba(255, 255, 255, 0.72); text-shadow: 0 1px 2px rgba(0,0,0,0.15); }  /* was 0.50 */
.kpi-card-pending { color: rgba(255, 210, 130, 0.95); }  /* was rgba(255,180,100,0.90) */
```

Note: The `text-shadow` on `.kpi-card-sub` is additive — it gives a subtle lift on the lighter green/amber gradient stops without affecting layout.

---

## Item 2 — 19C: Desktop Card Select Animation

**Scope**: Frontend-only
**File**: `frontend/react/src/index.css` — lines 345–353 (inside `@media (min-width: 768px)`)

**Root cause** (verified against disk):
```css
/* lines 345–350 */
.kpi-desktop-row .kpi-card-shell {
  flex: 1;
  height: 140px;
  cursor: pointer;
  transition: box-shadow 250ms ease;   /* ← no transform or opacity */
}
/* lines 351–353 */
.kpi-desktop-row .kpi-card-shell.active {
  box-shadow: 0 0 0 2px rgba(255,255,255,0.15), 0 8px 32px rgba(0,0,0,0.4);
  /* ← no translateY/scale — clicking feels static */
}
```
No hover rule, no opacity dimming, no transform — selecting a card shows only a box-shadow change with no motion.

**What to do**:
Replace the desktop block (lines 345–353) with:
```css
.kpi-desktop-row .kpi-card-shell {
  flex: 1;
  height: 140px;
  cursor: pointer;
  transition: transform 250ms cubic-bezier(0.25,0.46,0.45,0.94),
              box-shadow 250ms ease,
              opacity 250ms ease;
  opacity: 0.85;
}
.kpi-desktop-row .kpi-card-shell:hover {
  transform: translateY(-2px);
  opacity: 1;
}
.kpi-desktop-row .kpi-card-shell.active {
  transform: translateY(-4px) scale(1.02);
  opacity: 1;
  box-shadow: 0 0 0 2px rgba(255,255,255,0.18), 0 12px 36px rgba(0,0,0,0.45);
}
.kpi-desktop-row .kpi-card-shell.side {
  opacity: 0.78;
}
```

The `.side` class is already applied in JSX (`OverviewTab.tsx` line 447: `i === activeKpiIndex ? "active" : "side"`), so no JSX change is needed.

---

## Item 3 — 19A: Rebuild Mobile Carousel as Sliding Track

**Scope**: Frontend-only
**Files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — lines 362–483 (the entire `<section>` KPI block)
- `frontend/react/src/index.css` — lines 253–354 (mobile carousel rules + desktop block)

**Root cause** (verified against disk):
The mobile JSX (OverviewTab.tsx lines 364–427) uses a stacked-deck: one `kpi-carousel-stage` div holds 3 absolute-positioned card shells (`pos-far-behind`, `pos-behind`, `kpi-active-card`, `pos-peek-right`). The `carouselRef` points to `.kpi-carousel-stage`. When `activeKpiIndex` changes via `navigateTo()`, only the active card's *content* swaps (via React conditional rendering of `kpiCards[activeKpiIndex]`). There is a `transition: transform` on `.kpi-active-card` (index.css line 274) but no transform is ever changed, so nothing slides. The gesture detection code in the `useEffect` (lines 251–295) is correct and carries over unchanged.

**What to do — JSX (OverviewTab.tsx)**:

Replace the entire `<section>` block at lines 362–483 (from `{/* ── Section 0: KPI Carousel */}` through `</section>`) with:

```tsx
{/* ── Section 0: KPI Carousel ─────────────────────── */}
<section>
  <div className="kpi-carousel-wrapper">

    {/* Mobile: sliding track */}
    <div className="kpi-viewport">
      <div
        ref={carouselRef}
        className="kpi-track"
        style={{
          transform: `translateX(calc(-${activeKpiIndex} * (100% + 12px)))`,
          transition: 'transform 350ms cubic-bezier(0.25,0.46,0.45,0.94)',
        }}
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
    </div>

    {/* Dot indicators — mobile only */}
    <div className="kpi-dots md:hidden">
      {kpiCards.map((card, i) => (
        <button
          key={card.id}
          className={`kpi-dot ${i === activeKpiIndex ? "active" : ""}`}
          onClick={() => navigateTo(i)}
          aria-label={`View ${card.label}`}
        />
      ))}
    </div>

    {/* Desktop: all 3 cards side by side */}
    <div className="kpi-desktop-row hidden md:flex">
      {kpiCards.map((card, i) => (
        <div
          key={card.id}
          className={`kpi-card-shell kpi-card-${card.id} ${i === activeKpiIndex ? "active" : "side"}`}
          style={{ padding: "14px 20px" }}
          onClick={() => navigateTo(i)}
        >
          <div className="kpi-accent" />
          <span className="kpi-watermark" style={{ fontSize: 18, top: 10, right: 14 }}>WM</span>
          <div className="kpi-slide-header" style={{ marginBottom: 10 }}>
            <span className="kpi-slide-icon" style={{ fontSize: 14 }}>{card.icon}</span>
            <span className="kpi-card-label" style={{ fontSize: 10 }}>{card.label}</span>
          </div>
          <p className="kpi-card-value" style={{ fontSize: 24 }}>{card.value}</p>
          <p className="kpi-card-sub" style={{ fontSize: 10, marginTop: 3 }}>{card.subtitle}</p>
          {card.pending && (
            <p className="kpi-card-pending" style={{ fontSize: 10, marginTop: 2 }}>{card.pending}</p>
          )}
        </div>
      ))}
    </div>

  </div>
</section>
```

Key changes from old JSX:
- The stacked `pos-far-behind` / `pos-behind` / `kpi-active-card` / `pos-peek-right` divs are gone.
- A single `.kpi-viewport` wraps a `.kpi-track` (flex row of all 3 slides).
- `carouselRef` now points to `.kpi-track` — the element that actually moves.
- `transform: translateX(...)` on the track drives all animation; index change automatically slides all content.
- WM watermark moved to a `.kpi-watermark` CSS class (matches the new CSS below), keeping inline overrides only for desktop size differences.
- Desktop section is unchanged structurally — still uses `.kpi-card-shell` with `active`/`side` classes.

**No state changes needed.** `activeKpiIndex`, `navigateTo`, and the `carouselRef` touch-event `useEffect` all stay exactly as they are. The only behavioral difference: `carouselRef` now attaches to `.kpi-track` (inside `.kpi-viewport`) instead of `.kpi-carousel-stage`. Since the `useEffect` already passes the element to `addEventListener`, no code change is needed there.

**What to do — CSS (index.css)**:

**A. Remove obsolete mobile stage rules** (lines 260–308):
Delete the entire block from `.kpi-carousel-stage {` through the closing `}` of `.kpi-card-shell.pos-peek-right` — that's lines 260–308.

**B. Add new sliding-track rules** in their place (after line 258 `.kpi-carousel-wrapper` block):

```css
/* ── Mobile sliding carousel ─────────────────────────────────── */
.kpi-viewport {
  overflow: hidden;
  padding: 0 18px;
  margin: 0 -2px;
}

.kpi-track {
  display: flex;
  gap: 12px;
  will-change: transform;
}

.kpi-slide {
  flex: 0 0 calc(100% - 24px);
  height: 150px;
  border-radius: 22px;
  position: relative;
  overflow: hidden;
  padding: 18px 20px;
}

/* Watermark */
.kpi-watermark {
  position: absolute;
  right: 16px;
  top: 12px;
  font-size: 20px;
  font-weight: 900;
  font-style: italic;
  color: rgba(255, 255, 255, 0.07);
  pointer-events: none;
}

/* Slide header (icon + label row) */
.kpi-slide-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
}
.kpi-slide-icon { font-size: 16px; }
```

Note: `.kpi-card-label`, `.kpi-card-value`, `.kpi-card-sub`, `.kpi-card-pending` rules at lines 211–214 are shared between mobile slides and desktop cards. Keep them — they will be updated by Item 1 (19B).

**C. Update the `@media (min-width: 768px)` block** (lines 339–354):

Replace:
```css
@media (min-width: 768px) {
  .kpi-carousel-stage,
  .kpi-dots { display: none; }

  .kpi-desktop-row { display: flex; }
  ...
}
```
With:
```css
@media (min-width: 768px) {
  .kpi-viewport,
  .kpi-dots { display: none; }

  .kpi-desktop-row { display: flex; }
  ...
}
```
The only change is `.kpi-carousel-stage` → `.kpi-viewport` in the hide rule. The rest of the desktop block is handled by Item 2 (19C).

---

## Dependency order

```
19B (Item 1) → can be done first, no deps
19C (Item 2) → can be done first, no deps
19A (Item 3) → do last; its JSX references .kpi-slide-header and .kpi-watermark classes
               that are added in the CSS portion of this same item
```

Items 1 and 2 can be committed independently. Item 3 must be done as a single atomic change (JSX + CSS together, since the new JSX depends on the new CSS classes).

---

## Testing Notes

- **19A must be verified on real iPhone 15 Safari** (not desktop responsive mode). The carousel has failed twice under responsive mode testing. Check: swipe left/right, dot tap, vertical scroll still works.
- **19B**: Read each card's subtitle on both dark and light themes. Green card ("Left for the month") is the hardest case.
- **19C**: Click between desktop cards — expect a smooth 250ms lift+scale transition. Hover a non-active card — expect a 2px lift.
