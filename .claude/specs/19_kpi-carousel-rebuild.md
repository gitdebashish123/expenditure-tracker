# Spec 19 — KPI Carousel Rebuild (Sliding Track + Interactions)
**Date**: 2026-06-28
**Status**: 🔴 Ready to implement
**Branch**: `feature/sprint06261-ui-enhancement`
**Follows**: `18_kpi-carousel-fixes.md`
**Source**: Desktop + iPhone 15 Safari screenshots, June 28, 2026 (post spec 18 implementation)

---

## Context

Spec 18 attempted to fix the Safari swipe via imperative `addEventListener` with
`{ passive: false }`. The handler code was added correctly, BUT the carousel still
does not work on mobile — the user sees only card 1, and neither swipe nor dot-tap
reveals cards 2 and 3.

**Root cause — architectural, not gesture-related:**

The current carousel is built as a **static stacked deck**. The active card's
*content* swaps when `activeKpiIndex` changes, but:

1. There is **no sliding track** — cards are positioned with `position: absolute`
   in a stack. When the index changes, the active card's text content swaps
   instantly with no motion. There is a `transition: transform` declared on
   `.kpi-active-card` but no transform is ever applied on index change, so
   nothing visibly moves.

2. The dot-tap calls `navigateTo(i)` which updates state correctly, but because
   all three gradient cards are stacked at the same position and only the front
   card shows content, a state change produces little or no visible difference —
   making it *appear* that tapping does nothing.

3. `overflow: visible` on `.kpi-carousel-stage` means there is no clipped viewport,
   so the "sliding" metaphor cannot work — there's nothing to slide within.

**The fix is to rebuild the carousel as a true horizontal sliding track** — the
standard, reliable carousel pattern — instead of a content-swapping stacked deck.
This is more robust, animates naturally, and works identically across Safari,
Chrome, and desktop.

Additionally, two smaller issues from the screenshots:
- Card subtitles ("Left for the month", "Total this month") are too faint to read
- Desktop cards have no interaction feedback / animation when clicked

---

## Issues Addressed

| # | Issue | Type | Priority |
|---|-------|------|----------|
| 19A | Mobile carousel non-functional — rebuild as sliding track | Bug (rebuild) | P0 |
| 19B | Card subtitle text too faint to read | Visual | P1 |
| 19C | Desktop: add slide/scale animation on card select | Enhancement | P2 |

---

## Issue 19A — Rebuild Mobile Carousel as Sliding Track

**Replace** the stacked-deck approach with a horizontal sliding track. The key
change: instead of one active card whose content swaps, render **all three cards
in a row inside a clipped viewport**, and slide the row left/right by changing a
single `translateX` value.

### New structure

```tsx
{/* Mobile carousel — sliding track */}
<div className="kpi-viewport">          {/* clipped window, overflow: hidden */}
  <div
    ref={carouselRef}
    className="kpi-track"                {/* flex row of 3 full cards */}
    style={{
      transform: `translateX(calc(-${activeKpiIndex} * (100% + 12px)))`,
      transition: isDragging ? 'none' : 'transform 350ms cubic-bezier(0.25,0.46,0.45,0.94)',
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
```

### Why this works where the stacked deck failed
- **One transform drives everything.** `translateX(-index * slideWidth)` — when
  index changes, the whole row slides. The `transition` makes it animate.
- **All cards always rendered** with real content — no content-swapping, no
  "front card only" problem.
- **Clipped viewport** (`overflow: hidden`) gives the slide somewhere to happen
  and naturally hides the off-screen cards, showing a small peek of the next.

### CSS to replace the existing mobile carousel CSS

Remove these now-obsolete rules:
- `.kpi-carousel-stage` and all its children
- `.kpi-active-card`
- `.kpi-card-shell.pos-behind`
- `.kpi-card-shell.pos-far-behind`
- `.kpi-card-shell.pos-peek-right`

Replace with:

```css
/* ── Mobile sliding carousel ─────────────────────────────────── */
.kpi-viewport {
  overflow: hidden;
  padding: 0 18px;          /* viewport gutter — creates the peek effect */
  margin: 0 -2px;            /* slight bleed so peek is visible */
}

.kpi-track {
  display: flex;
  gap: 12px;
  will-change: transform;
}

.kpi-slide {
  flex: 0 0 calc(100% - 24px);  /* each slide nearly full width, leaving peek */
  height: 150px;
  border-radius: 22px;
  position: relative;
  overflow: hidden;
  padding: 18px 20px;
}

@media (min-width: 768px) {
  /* Hide mobile carousel on desktop */
  .kpi-viewport { display: none; }
}

/* Watermark */
.kpi-watermark {
  position: absolute;
  right: 16px; top: 12px;
  font-size: 20px; font-weight: 900; font-style: italic;
  color: rgba(255,255,255,0.07);
  pointer-events: none;
}

/* Slide header */
.kpi-slide-header {
  display: flex; align-items: center; gap: 6px;
  margin-bottom: 12px;
}
.kpi-slide-icon { font-size: 16px; }
.kpi-card-label {
  font-size: 11px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.08em;
}
.kpi-card-value { font-size: 30px; font-weight: 700; line-height: 1.1; }
.kpi-card-sub   { font-size: 12px; margin-top: 4px; }
.kpi-card-pending { font-size: 11px; margin-top: 2px; }
```

### Swipe handler — keep the spec 18 imperative listener, simplify the end logic

The `addEventListener('touchmove', ..., { passive: false })` approach from spec 18
is correct and stays. Just point `carouselRef` at the `.kpi-track` element and
ensure the end handler calls `navigateTo`. Optionally add live-drag (move the
track with the finger) for a premium feel:

```tsx
// Optional live drag — set a dragOffset state during touchmove
const [dragOffset, setDragOffset] = useState(0);
const [isDragging, setIsDragging] = useState(false);

// in onTouchMove, when horizontal:
//   setIsDragging(true);
//   setDragOffset(dx);

// in onTouchEnd:
//   setIsDragging(false);
//   setDragOffset(0);
//   ...then navigateTo based on dx threshold

// track transform becomes:
transform: `translateX(calc(-${activeKpiIndex} * (100% + 12px) + ${dragOffset}px))`
```

Live drag is **optional** — the core requirement is that index changes slide the
track. If live drag adds risk, ship without it; the snap-animation alone is enough.

### Boundary behaviour (no wrap, per spec 17 decision)
`navigateTo` already clamps to `[0, 2]` via `Math.max(0, Math.min(2, index))`.
Keep that. Swiping past either end simply snaps back (the clamp prevents index
change, and the transition animates the track back to position).

**Affected files:**
- `frontend/react/src/components/tabs/OverviewTab.tsx` — replace mobile carousel JSX
- `frontend/react/src/index.css` — replace mobile carousel CSS

**Acceptance criteria:**
- [ ] Swiping left on iPhone 15 Safari slides from card 1 → 2 → 3
- [ ] Swiping right slides back
- [ ] Tapping a dot slides to that card
- [ ] The track visibly animates (350ms) between cards — not an instant swap
- [ ] A small peek (~12–18px) of the next card is visible at the right edge
- [ ] No wrap — past either end snaps back
- [ ] Vertical page scroll still works when starting a vertical drag on the carousel

---

## Issue 19B — Card Subtitle Text Too Faint

**Symptom**: Subtitles "Left for the month", "Total this month", "Out of ₹92,783"
render at `rgba(255,255,255,0.50)` which is too faint to read comfortably against
the vibrant card gradients, especially on the lighter green and amber cards.

**Fix**: Increase subtitle and label opacity for better contrast on the gradients.

```css
/* Was 0.70 / 0.50 — increase for readability on gradient */
.kpi-card-label   { color: rgba(255, 255, 255, 0.85); }  /* was 0.70 */
.kpi-card-sub     { color: rgba(255, 255, 255, 0.72); }  /* was 0.50 */
.kpi-card-pending { color: rgba(255, 210, 130, 0.95); }  /* warm, brighter */
```

Optionally add a subtle text shadow to subtitles for extra legibility on the
lighter gradient stops:
```css
.kpi-card-sub { text-shadow: 0 1px 2px rgba(0,0,0,0.15); }
```

**Affected files:**
- `frontend/react/src/index.css` — kpi card text color rules

**Acceptance criteria:**
- [ ] "Left for the month" clearly readable on green card (both themes)
- [ ] "Total this month" clearly readable on purple card
- [ ] "Out of ₹X" clearly readable on amber card
- [ ] Label and value contrast unchanged or improved
- [ ] Readable in both dark and light theme

---

## Issue 19C — Desktop: Animation on Card Select

**Symptom**: On desktop, clicking a card sets it active (the box-shadow ring
appears) but there is no motion — the change feels static.

**Fix**: Add a subtle scale + lift animation to the active desktop card, and a
gentle transition on all cards so selection feels responsive.

```css
@media (min-width: 768px) {
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
}
```

This gives: inactive cards slightly dimmed, hover lifts a card, the active card
lifts higher and scales up subtly with a glow ring. Clicking animates smoothly
between states.

**Affected files:**
- `frontend/react/src/index.css` — desktop carousel rules

**Acceptance criteria:**
- [ ] Clicking a desktop card animates it to active (lift + scale, 250ms)
- [ ] Hover on a non-active card lifts it slightly
- [ ] Inactive cards are subtly dimmed (opacity ~0.78)
- [ ] Active card is full opacity with glow ring
- [ ] No layout shift / reflow when cards scale (scale is transform-based)

---

## Implementation Order

| # | Issue | Where | Effort |
|---|-------|--------|--------|
| 1 | 19A — Rebuild mobile carousel as sliding track | Frontend (JSX + CSS) | M |
| 2 | 19B — Subtitle contrast | CSS | XS |
| 3 | 19C — Desktop select animation | CSS | XS |

Do 19A first (the rebuild) — it's the core fix. Then 19B and 19C are quick CSS
passes that apply to the rebuilt structure.

---

## Testing Notes

The mobile carousel has now failed twice (spec 18 gesture fix did not resolve it).
**Before marking 19A complete, test on a real iPhone 15 Safari** — not just
desktop responsive mode, which does not reproduce Safari's touch behaviour.
Verify all three of: swipe left, swipe right, dot tap.

If the sliding track still does not respond to touch after this rebuild, the next
diagnostic step is to check whether a parent element (page scroll container,
pull-to-refresh handler, or a `touch-action` rule on an ancestor) is intercepting
the touch events before they reach `.kpi-track`. But the sliding-track rebuild
should resolve it, because the failure mode in 18 was the absence of a slide
mechanism, not the gesture detection itself.

---

## Files Modified

- `frontend/react/src/components/tabs/OverviewTab.tsx`
  — Replace mobile carousel JSX (stacked deck → sliding track)
  — Point `carouselRef` at `.kpi-track`
  — Optionally add `dragOffset` / `isDragging` state for live drag

- `frontend/react/src/index.css`
  — Replace mobile carousel CSS (remove `.kpi-carousel-stage` + `pos-*` rules)
  — Add `.kpi-viewport` / `.kpi-track` / `.kpi-slide` rules
  — Increase subtitle/label contrast (19B)
  — Add desktop select animation (19C)

## Files NOT Modified
- `backend/` — no changes
- `frontend/react/src/types/index.ts`
- Any other component
