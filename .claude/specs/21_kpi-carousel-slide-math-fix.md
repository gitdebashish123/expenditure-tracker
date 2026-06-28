# Spec 21 — KPI Carousel: Native Scroll-Snap Rebuild (Mobile)
**Date**: 2026-06-28 (revised)
**Status**: 🔴 Ready to implement — HIGH PRIORITY
**Branch**: `feature/sprint06261-ui-enhancement`
**Follows**: `20_heading-consistency-and-descenders.md`
**Related**: `17`, `18`, `19` (carousel history — all superseded for mobile)
**Source**: iPhone 15 Safari screenshots, June 28, 2026

---

## Context

This is the definitive fix for the mobile KPI carousel after three failed
attempts (specs 17, 18, 19). The history matters because it points directly at
the solution:

- **Spec 17** — built a stacked-deck carousel (no real slide). Failed.
- **Spec 18** — added imperative touch listeners with `passive: false`. Failed.
- **Spec 19** — rebuilt as a JS `translateX` sliding track. Failed.
- **Spec 21 (first draft)** — found a slide-math bug in the `%` calc. Fixing it
  made **dot-tap work**, but **swipe still failed**.

**The lesson from all four:** every approach that relies on a custom JS gesture
handler driving a `translateX` transform has failed on iOS Safari. The dot-tap
working (pure React state) while swipe fails (custom gesture) proves the slide
rendering is fine — the **custom gesture layer is the recurring point of failure.**

**Additional UX problem:** even when dot-tap works, asking users to tap a 6px dot
is wrong. Dots are below the ~44px minimum touch target, and users expect to
**swipe** cards, not hunt for a tiny dot. Swipe must be the primary interaction.

**Decision:** Replace the JS-transform carousel with a **native CSS scroll-snap
carousel** on mobile. The browser handles all touch physics natively — there is
no custom gesture code left to break. This is the standard production pattern for
card carousels (including the ICICI-style references provided earlier).

**Desktop is unaffected** — the `.kpi-desktop-row` (all 3 cards, click-to-activate)
works well and stays exactly as is. This spec only changes the mobile path.

---

## Why Native Scroll-Snap

| Problem with JS-transform approach | How scroll-snap solves it |
|-----------------------------------|---------------------------|
| Custom `touchmove` handler fails on Safari | No custom gesture code — native scroll |
| `passive: false` / `preventDefault` fights page scroll | Browser arbitrates scroll natively |
| Slide-math (`%` + `px` calc) error-prone | Browser positions slides via `scroll-snap-align` |
| `useEffect` re-attaching listeners drops events | No listeners needed for the gesture |
| Dots became the only working control | Swipe is primary; dots become passive indicator |

Native horizontal scroll on iOS Safari has momentum, rubber-banding at
boundaries, and snap behaviour built in — it feels better than the custom 350ms
cubic-bezier and cannot fail the way custom gestures do.

---

## The Implementation

### 1. New JSX — mobile carousel (replaces the `.kpi-viewport` / `.kpi-track` block)

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

Key changes from current code:
- The outer `.kpi-viewport` + inner `.kpi-track` (two elements) collapse into
  **one** scrollable element `.kpi-scroller`.
- **No `transform`, no `transition` inline style** — scrolling does the motion.
- `ref` goes on the scroller; `onScroll` updates the dot indicator.

### 2. Replace the touch `useEffect` with a scroll handler

**Remove entirely** the existing `useEffect` block that adds
`touchstart`/`touchmove`/`touchend` listeners (the spec 18 gesture handler). It
is no longer needed and must be deleted to avoid interfering with native scroll.

**Remove** these now-unused refs:
- `touchStartX`, `touchStartY`, `touchStartTime`, `isHorizontalSwipe`

**Keep** `carouselRef` (now points at `.kpi-scroller`) and `activeKpiIndex`.

**Add** a scroll handler that derives the active index from scroll position (for
the dot indicator only):

```tsx
const handleScroll = useCallback(() => {
  const el = carouselRef.current;
  if (!el) return;
  // Each slide is the full scroller width; index = scrollLeft / slideWidth
  const slideWidth = el.clientWidth;
  const index = Math.round(el.scrollLeft / slideWidth);
  setActiveKpiIndex(Math.max(0, Math.min(2, index)));
}, []);
```

> Note: with `scroll-snap-align: start` and each slide at `100%` of the scroller
> width minus the peek (see CSS), `clientWidth` is the correct divisor. If using
> a peek that makes slides < 100%, divide by the actual slide pixel width:
> `el.querySelector('.kpi-slide')?.clientWidth ?? el.clientWidth` plus the gap.
> Simplest reliable approach: compute slide step once from the first slide. See
> CSS below which sizes slides so `clientWidth`-based rounding is robust.

### 3. Dots — passive indicator, optionally tappable

Dots stay for position feedback. They update from `activeKpiIndex` (driven by
scroll). Keep them tappable as a secondary convenience using `scrollTo`:

```tsx
const scrollToCard = useCallback((index: number) => {
  const el = carouselRef.current;
  if (!el) return;
  const slide = el.children[index] as HTMLElement | undefined;
  if (slide) {
    el.scrollTo({ left: slide.offsetLeft, behavior: 'smooth' });
  }
}, []);
```

```tsx
<div className="kpi-dots md:hidden">
  {kpiCards.map((card, i) => (
    <button
      key={card.id}
      className={`kpi-dot ${i === activeKpiIndex ? "active" : ""}`}
      onClick={() => scrollToCard(i)}
      aria-label={`View ${card.label}`}
    />
  ))}
</div>
```

Dots are now a *bonus* control, not the primary one, so their small size is no
longer a usability blocker — swipe is the main interaction.

### 4. New CSS — replace `.kpi-viewport` / `.kpi-track` rules

Remove these rules entirely:
- `.kpi-viewport`
- `.kpi-track`

Add:

```css
/* ── Mobile native scroll-snap carousel ─────────────────────── */
.kpi-scroller {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;   /* momentum scroll on iOS */
  scroll-behavior: smooth;
  /* Side padding creates the peek + centers the first/last card nicely.
     scroll-padding makes snap respect this gutter. */
  padding: 0 18px;
  scroll-padding-left: 18px;
  /* Hide scrollbar */
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.kpi-scroller::-webkit-scrollbar { display: none; }

.kpi-slide {
  flex: 0 0 calc(100% - 52px);   /* full width minus gutters — next card peeks */
  scroll-snap-align: start;
  height: 150px;
  border-radius: 22px;
  position: relative;
  overflow: hidden;
  padding: 18px 20px;
}

@media (min-width: 768px) {
  .kpi-scroller { display: none; }   /* desktop uses .kpi-desktop-row */
}
```

Notes on the numbers:
- `padding: 0 18px` on the scroller gives an 18px gutter each side.
- `flex: 0 0 calc(100% - 52px)` makes each slide slightly narrower than the
  viewport so the next card peeks ~34px on the right. Adjust the `52px` to taste
  (larger = more peek). This does NOT cause the old bug because there is **no JS
  transform** — the browser handles positioning, so there is no math to mismatch.
- `scroll-snap-align: start` + `scroll-padding-left: 18px` snaps each card to the
  left gutter cleanly.

### 5. Keep unchanged
- All `.kpi-card-*` gradient classes, `.kpi-accent`, `.kpi-watermark`,
  `.kpi-slide-header`, `.kpi-card-value/label/sub/pending` — unchanged.
- `.kpi-dots` / `.kpi-dot` styles — unchanged.
- The entire `.kpi-desktop-row` block and its `@media (min-width: 768px)` rules —
  unchanged.

---

## Verification Order

### Step 1 — Swipe is now primary; test it first on real iPhone 15 Safari
- Swipe left → scrolls/snaps to Income, then Bills Paid
- Swipe right → snaps back
- Momentum and rubber-band at the ends feel native
- Dots update to match the visible card as you scroll

### Step 2 — Dots as secondary control
- Tapping dot 2 smooth-scrolls to Income; dot 3 to Bills Paid
- Active dot tracks the visible card during manual swipe

### Step 3 — Peek + boundaries
- Card 1: next card peeks ~34px on the right
- Card 3: snaps cleanly as the last card; no over-scroll into blank space
- No horizontal scrollbar visible

### Step 4 — Desktop regression
- ≥768px: `.kpi-desktop-row` shows all three cards, click-to-activate still works
- `.kpi-scroller` is `display: none` on desktop

---

## Acceptance Criteria

- [ ] **Swipe works on real iPhone 15 Safari** (primary interaction) — left/right
      scroll-snaps between the three cards
- [ ] Native momentum + boundary rubber-band present (browser default)
- [ ] Dot indicator updates automatically as the user swipes
- [ ] Tapping a dot smooth-scrolls to that card (secondary convenience)
- [ ] Next card peeks ~30–40px on the right when not on the last card
- [ ] No horizontal scrollbar visible
- [ ] No custom `touchmove` / `passive:false` gesture code remains
- [ ] `touchStartX/Y/Time` and `isHorizontalSwipe` refs removed (now unused)
- [ ] Desktop (≥768px) layout and click-to-activate unchanged

---

## Cleanup Checklist (remove dead code from prior attempts)

- [ ] Delete the `useEffect` that attached `touchstart`/`touchmove`/`touchend`
- [ ] Delete refs: `touchStartX`, `touchStartY`, `touchStartTime`, `isHorizontalSwipe`
- [ ] Delete `.kpi-viewport` and `.kpi-track` CSS rules
- [ ] Remove the inline `transform` / `transition` style from the old track div
- [ ] Keep `navigateTo` only if still referenced; otherwise replace its callers
      with `scrollToCard`

---

## Why This Will Not Fail Again

The previous three failures all shared one trait: **custom JavaScript driving the
slide.** Whether via touch listeners (18), or a `translateX` transform (19, 21a),
the custom layer was where Safari broke things — passive listeners, calc()
quirks, listener re-attachment, slide-math mismatches.

Native scroll-snap removes that entire layer. The "gesture handler" is now the
browser's own scroll engine, which is the single most battle-tested touch
interaction on the platform. There is no remaining custom code in the swipe path
that *can* fail. The only JS left (`onScroll` → update dot, `scrollTo` on dot tap)
is non-load-bearing: even if the dot indicator lagged, the swipe itself would
still work, because swiping is just scrolling.

---

## Files Modified
- `frontend/react/src/components/tabs/OverviewTab.tsx`
  — Replace mobile carousel JSX (viewport/track → single `.kpi-scroller`)
  — Delete touch `useEffect` and unused refs
  — Add `handleScroll` + `scrollToCard`
- `frontend/react/src/index.css`
  — Remove `.kpi-viewport`, `.kpi-track`
  — Add `.kpi-scroller`, update `.kpi-slide`

## Files NOT Modified
- `backend/` — no changes
- `.kpi-desktop-row` and desktop `@media` rules — working, leave alone
- All `.kpi-card-*`, `.kpi-accent`, `.kpi-watermark`, `.kpi-dots` styles — unchanged
- Any other component
