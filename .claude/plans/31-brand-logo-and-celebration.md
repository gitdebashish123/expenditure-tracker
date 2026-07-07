# Implementation Plan: Brand Logo + Fixed Tab Celebration Animation
**Spec**: `.claude/specs/31_brand-logo-and-celebration.md`
**Date**: 2026-07-02
**Branch**: `feature/sprint0726p1-ui-enhancement` *(current active branch — spec listed `feature/sprint06261-ui-enhancement`, which does not match; confirmed via `git branch --show-current` that the actual branch is `feature/sprint0726p1-ui-enhancement`)*
**Status**: ✅ Complete and visually verified (2026-07-02) — all 3 items implemented, `npm run build` (tsc + vite) passes clean, and confirmed end-to-end in a real Playwright/Chromium session (both light/dark mode, header + KPI watermarks on Overview and Fixed tabs, celebration fire-once + no-replay-on-reload). `npm run lint` could not run (eslint missing from `node_modules`, pre-existing gap). Item 3's edge-trigger effect needed a `loading`-guard correction vs. this doc's original pseudocode to satisfy its own "no re-trigger on reload" acceptance criterion — confirmed working live. A follow-up round also chroma-keyed `public/wallet-mantra-logo.png` itself (the source PNG had an opaque background, not a transparent logomark) and dropped `mix-blend-mode: overlay` from the KPI watermark CSS — see the spec's post-implementation addendum and `.claude/blocked/31-followups-for-reevaluation.md`.

---

## Overview

3 items total — all frontend-only. `public/wallet-mantra-logo.png` already exists
on disk, so no asset work is needed. All three items were verified against the
current file contents and match the spec's "before" description exactly — no
drift found.

Items are ordered smallest-blast-radius-first: a single-file emoji swap, then a
two-file CSS/JSX watermark swap, then the celebration animation (new state,
`useEffect`, and CSS keyframes touching `FixedTab.tsx`, the largest and only
item with behavioral logic).

---

## Item 1 — Header logo: replace emoji with real PNG
**Scope**: Frontend-only
**File**: `frontend/react/src/components/layout/Header.tsx` (lines 28–33)

**Root cause**: The header currently renders a static emoji instead of the brand
logo:
```tsx
{/* Logo */}
<div className="flex-shrink-0">
  <h1 className="font-syne font-bold text-white text-lg leading-none tracking-tight">
    💸 Wallet Mantra
  </h1>
</div>
```
`public/wallet-mantra-logo.png` already exists in `frontend/react/public/` and is
served at `/wallet-mantra-logo.png` — no asset needs to be added.

**What to do**: Replace the `<h1>` contents with a flex row containing the logo
`<img>` (32px, decorative/`aria-hidden`) followed by the "Wallet Mantra" text
node:

```tsx
{/* Logo */}
<div className="flex-shrink-0">
  <h1 className="font-syne font-bold text-white text-lg leading-none tracking-tight
                 flex items-center gap-2">
    <img
      src="/wallet-mantra-logo.png"
      alt=""
      aria-hidden="true"
      className="h-8 w-8 flex-shrink-0 object-contain"
    />
    Wallet Mantra
  </h1>
</div>
```

`h-8 w-8` = 32px per the spec's locked decision. The spec calls out a possible
dark halo around the PNG in light mode — verify visually after the build (see
Definition of Done); if the halo is visible in light mode, add
`html.light & className="..."` scoped `mix-blend-mode: multiply` to the `<img>`
at that point, but don't pre-emptively add it since it's unconfirmed.

**Acceptance**: header shows the real logo at 32px, left of "Wallet Mantra", in
both dark and light mode; no 💸 emoji visible anywhere.

---

## Item 2 — KPI card watermark: logo PNG with mix-blend-mode
**Scope**: Frontend-only
**Files**:
- `frontend/react/src/components/shared/KpiCarousel.tsx` (lines 46, 80)
- `frontend/react/src/index.css` (lines 289–299)

**Root cause**: Both the mobile slide and desktop card render a text watermark:
```tsx
// line 46 (mobile slide):
<span className="kpi-watermark">WM</span>
// line 80 (desktop card):
<span className="kpi-watermark" style={{ fontSize: 18, top: 10, right: 14 }}>WM</span>
```
backed by `.kpi-watermark` in `index.css` (lines 289–299):
```css
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
```
This renders on every `KpiCarousel` card — used by both the Overview KPI row
(Remaining/Income/Bills Paid) and the Fixed tab KPI row (Fixed total/paid/left),
since both consume the same shared component.

**What to do**:

### 2a. `KpiCarousel.tsx`
Replace **both** occurrences of the `<span className="kpi-watermark">WM</span>`
(mobile slide, line 46, and desktop card, line 80) with an `<img>` using a new
`kpi-watermark-img` class. The desktop card currently overrides size/position
inline via `style={{ fontSize: 18, top: 10, right: 14 }}` — drop that inline
override since the new fixed 54×54px sizing from the spec's CSS block applies
uniformly to both slide types (the spec's CSS gives one size for all cards, no
mobile/desktop distinction):

```tsx
// mobile slide (was line 46):
<img
  src="/wallet-mantra-logo.png"
  alt=""
  aria-hidden="true"
  className="kpi-watermark-img"
/>

// desktop card (was line 80):
<img
  src="/wallet-mantra-logo.png"
  alt=""
  aria-hidden="true"
  className="kpi-watermark-img"
/>
```

### 2b. `index.css`
Replace the `.kpi-watermark` rule (lines 289–299) with:
```css
.kpi-watermark-img {
  position: absolute;
  right: 10px;
  top: 8px;
  width: 54px;
  height: 54px;
  object-fit: contain;
  mix-blend-mode: overlay;
  opacity: 0.55;
  pointer-events: none;
  user-select: none;
}
```

No other file references `.kpi-watermark` (confirmed via grep — the class only
appears in `KpiCarousel.tsx` and `index.css`), so this is a clean rename, not
an addition alongside the old rule.

**Visual note (from spec, pre-confirmed)**: `mix-blend-mode: overlay` should pop
on the amber Bills card; on the dark green Remaining card the logo's navy region
may partially fade — if so, add `filter: brightness(2)` to `.kpi-watermark-img`.
Verify after first build (see Definition of Done) before deciding whether to add it.

**Acceptance**: all KPI cards (Remaining/Income/Bills Paid on Overview; Fixed
total/paid/left on Fixed tab) show the real logo watermark top-right, on both
mobile slides and desktop cards. No "WM" text visible anywhere.

---

## Item 3 — Fixed tab 100% celebration animation
**Scope**: Frontend-only
**Files**:
- `frontend/react/src/components/tabs/FixedTab.tsx` (state near line 45–49, derived values near line 108, JSX near line 172)
- `frontend/react/src/index.css` (new block, append near the KPI carousel styles)

**Depends on**: nothing — independent of Items 1–2, but ordered last since it's
the only item introducing new component state/effects rather than a pure
JSX/CSS swap.

**Root cause**: `FixedTab.tsx` already computes `pct` (line 108:
`grandTotal > 0 ? Math.round(paidTotal / grandTotal * 100) : 0`) and renders a
static "All fixed expenses paid" card when `pct === 100` (lines 172–186). There
is currently no edge-triggered celebration — the existing 100% card renders on
every load/re-render once `pct` is 100, which is correct for that card but
insufficient for a one-time celebratory animation. `paidCount` is also already
computed (line 107).

**What to do**:

### 3a. State + edge-trigger effect
Add `useRef` to the existing `import { useEffect, useState, useCallback }` on
line 1 (becomes `useEffect, useState, useCallback, useRef`).

Add new state below the existing `collapsed` state (after line 49):
```tsx
const [celebrating, setCelebrating] = useState(false);
const prevPctRef = useRef<number | null>(null);
```

Add a new `useEffect` **after** `pct` is computed (i.e. after line 108, before
the `byCategory` reduce). Note: `pct` and `paidCount` are computed after the
early-return `if (loading) return <FixedTabSkeleton />;` on line 101 — this
effect must therefore go after that point too, which means it's a `useEffect`
call happening conditionally relative to the early return. This is a
**pre-existing pattern violation risk**: React hooks must not be called
conditionally. Since `pct`/`paidCount` are plain derived `const`s (not hooks)
computed post-loading-check, but the new `useEffect` itself IS a hook — placing
it after the `if (loading) return ...` on line 101 would violate the Rules of
Hooks (hook call count would differ between the loading and loaded renders).

**Resolution**: the effect must be declared **before** the `if (loading) return`
early return (i.e. up with the other `useEffect` calls near lines 73–80), computing
`pct` and `paidCount` inline within the effect from `fixedExps` state directly
(not from the post-return `const pct`/`paidCount`), since those consts aren't in
scope yet at that point in the file. Add this effect after the existing
`fixedTemplateUpdated` listener effect (after line 80), before the `togglePaid`
function:

```tsx
useEffect(() => {
  const paid   = fixedExps.reduce((s, e) => s + (e.paid ? e.amount : 0), 0);
  const total  = fixedExps.reduce((s, e) => s + e.amount, 0);
  const paidN  = fixedExps.filter(e => e.paid).length;
  const curPct = total > 0 ? Math.round(paid / total * 100) : 0;

  if (prevPctRef.current !== null &&
      prevPctRef.current < 100 &&
      curPct === 100 &&
      paidN > 0) {
    setCelebrating(true);
    const t = setTimeout(() => setCelebrating(false), 5200); // 5s + fade
    return () => clearTimeout(t);
  }
  prevPctRef.current = curPct;
}, [fixedExps]);
```

This duplicates the `paid`/`total`/`pct` arithmetic that already exists later in
the render body (lines 104–108), but it must run before the loading gate, so it
cannot share those `const`s. Do not refactor the later `const pct = ...` block
to reuse this effect's locals — they're computed at different points in the
component lifecycle (this effect runs on every `fixedExps` change including
before `loading` flips false; the render-body consts only exist post-loading-gate).

### 3b. `CEL_POSITIONS` constant
Add above the `FixedTab` function (module scope, alongside `FixedTabSkeleton`),
so it's computed once rather than on every render:
```tsx
const CEL_POSITIONS = Array.from({ length: 28 }, (_, i) => {
  const angle = (i / 28) * 2 * Math.PI;
  const dist = 80 + (i % 4) * 20;   // 80–140px radius
  return {
    dx: Math.cos(angle) * dist,
    dy: Math.sin(angle) * dist,
    delay: (i % 4) * 0.06,
    size: 18 + (i % 3) * 8,          // 18, 26, or 34px
  };
});
```

### 3c. Overlay JSX
Render the overlay as the first child inside the component's returned
top-level `<div className="space-y-6">` (line 119), before the Due Reminders
section, so it's present regardless of which sections are populated:

```tsx
{celebrating && (
  <div className="fixed-cel-overlay" aria-live="assertive" role="status">
    <div className="fixed-cel-center">🎉</div>
    {CEL_POSITIONS.map((pos, i) => (
      <span
        key={i}
        className="fixed-cel-piece"
        style={{
          '--dx': `${pos.dx}px`,
          '--dy': `${pos.dy}px`,
          '--delay': `${pos.delay}s`,
          '--size': `${pos.size}px`,
        } as React.CSSProperties}
        aria-hidden="true"
      >🎉</span>
    ))}
  </div>
)}
```

The overlay uses `position: fixed` (defined in CSS below), so its placement in
the DOM tree doesn't affect layout — only mount/unmount timing matters, and
mounting it inside the main content `<div>` is sufficient since `celebrating`
already gates on `loading` having completed (the effect that sets it only runs
after `fixedExps` is populated).

### 3d. `index.css` — append celebration CSS
Append after the KPI carousel block (after the `.kpi-slide-icon` rule ending
around line 309, or anywhere else CSS is appended in the file — exact position
doesn't matter since these are new, uniquely-named classes with no collisions,
confirmed via grep):

```css
/* ── Fixed tab 100% celebration overlay ─────────────────────── */

.fixed-cel-overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
  pointer-events: none;
  display: flex;
  align-items: center;
  justify-content: center;
}

.fixed-cel-center {
  font-size: 64px;
  animation: celCenterPop 0.3s ease-out forwards,
             celFadeOut 0.8s ease-in 4.2s forwards;
  z-index: 51;
}

.fixed-cel-piece {
  position: absolute;
  top: 50%;
  left: 50%;
  font-size: var(--size, 22px);
  opacity: 0;
  animation: celPieceBurst 1.6s ease-out var(--delay, 0s) forwards,
             celFadeOut 0.5s ease-in 4.5s forwards;
  transform-origin: center center;
}

@keyframes celCenterPop {
  0%   { opacity: 0; transform: scale(0.4); }
  60%  { opacity: 1; transform: scale(1.2); }
  100% { opacity: 1; transform: scale(1.0); }
}

@keyframes celPieceBurst {
  0%  {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.3);
  }
  15% {
    opacity: 1;
    transform: translate(calc(-50% + var(--dx) * 0.4),
                         calc(-50% + var(--dy) * 0.4)) scale(1.15);
  }
  70% {
    opacity: 1;
    transform: translate(calc(-50% + var(--dx)),
                         calc(-50% + var(--dy))) scale(1);
  }
  100% {
    opacity: 0;
    transform: translate(calc(-50% + var(--dx) * 1.3),
                         calc(-50% + var(--dy) * 1.3)) scale(0.8);
  }
}

@keyframes celFadeOut {
  from { opacity: 1; }
  to   { opacity: 0; }
}

/* Respect reduced motion — skip burst, just flash the center emoji */
@media (prefers-reduced-motion: reduce) {
  .fixed-cel-piece { display: none; }
  .fixed-cel-center {
    animation: celFadeOut 0.5s ease-in 4.5s forwards;
    opacity: 1;
  }
}
```

**Acceptance**:
- Marking the last unpaid commitment triggers a 5-second 🎉 burst radiating
  from the center of the Fixed tab, then disappears automatically.
- Page reload at 100% does NOT re-trigger the animation (verified by the
  `prevPctRef.current !== null` guard — on first mount `prevPctRef.current` is
  `null`, so the very first effect run after data loads only sets the ref and
  never fires the celebration, regardless of the loaded `pct`).
- With `prefers-reduced-motion: reduce`, only the large center 🎉 appears
  briefly; no flying pieces.
- The existing "All fixed expenses paid ✅" card (lines 172–186, Spec 22)
  remains untouched and continues to render whenever `pct === 100`, independent
  of the new one-shot overlay.

---

## Execution Order

| # | Item | Effort | Risk |
|---|------|--------|------|
| 1 | Header logo swap | XS | None — single static JSX change |
| 2 | KPI watermark swap | S | Low — two files, no state/logic change |
| 3 | Fixed tab celebration | M | Medium — new hook ordering constraint (effect must sit above the `loading` early return); verify no double-fire on `fixedExps` reference changes from unrelated re-fetches |

Start with Item 1, then Item 2 (both are mechanical swaps and can be done in
one pass). Item 3 last — it's the only item with new behavioral logic and
needs manual verification of the edge-trigger (toggle last item paid → confirm
burst fires once; reload page at 100% → confirm no burst).

---

## Definition of Done
- `npm run build` passes (zero TypeScript errors, zero ESLint warnings) inside `frontend/react/`
- Header logo visible at 32px in both dark and light mode; check for dark-halo artifact in light mode
- KPI watermark logo visible on all Overview and Fixed tab cards (mobile scroll + desktop row), both gradient variants (amber Bills card and dark green Remaining card) — check whether `filter: brightness(2)` is needed on the dark card
- Fixed tab: toggle the last unpaid commitment → celebration fires once, auto-dismisses after ~5s; reload at 100% → no re-trigger; test with OS-level reduced-motion enabled → only center emoji flashes
- No regressions to the existing Spec 22 "All fixed expenses paid" static card
