# Spec 31 — Brand Logo + Fixed Tab Celebration Animation
**Date**: 2026-07-01
**Status**: ✅ Implemented and visually verified in a live browser (2026-07-02). All 3 items landed, `npm run build` clean, confirmed via real Playwright/Chromium session in both light and dark mode. See `.claude/blocked/31-followups-for-reevaluation.md` for the one remaining deviation (Item 2's watermark blend approach, superseded — see below) and the still-open eslint gap.
**Branch**: `feature/sprint0726p1-ui-enhancement` *(actual branch differed from the `feature/sprint06261-ui-enhancement` named above; confirmed via `git branch --show-current`)*
**Follows**: `30_user-type-ai-classification.md`
**Source**: User review items 1, 2, 9 (logo on cards, logo in header, celebration on 100% paid).

---

## Decisions (locked)
| Decision | Choice |
|---|---|
| Header logo | `wallet-mantra-logo.png` at 32px, **left** of "Wallet Mantra" wordmark, replacing 💸 emoji |
| Card watermark | **Option A** — real PNG with `mix-blend-mode: overlay`, ~55% opacity, top-right corner *(superseded — see post-implementation addendum below: the source asset's opaque dark background made this produce a muddy sticker/visible-halo look; fixed by chroma-keying the asset's background to true transparency and dropping the blend mode)* |
| Celebration emoji | 🎉 **radiating from center**, 28 pieces at varied angles + sizes, large center piece, 5s auto-dismiss |
| Celebration trigger | Fires **once** on the `pct` 99→100 edge transition — not on page load, not on re-render |

---

## Post-implementation addendum (2026-07-02) — asset fix for halo/legibility complaints

After the initial implementation, the user reported via screenshots that (a) the header logo showed a visible dark square halo in light mode, and (b) the card watermark wasn't clearly legible. Root cause: `public/wallet-mantra-logo.png` was not a transparent logomark — it was an app-icon-style asset with an **opaque** dark rounded-square background baked into the RGB data (confirmed via pixel sampling: alpha=255 at fill regions, only the four true corners outside the rounded rect had alpha=0). No CSS blend-mode trick could fix that cleanly, since `mix-blend-mode: overlay`/`multiply` still composites against opaque dark pixels.

**Fix**: chroma-keyed the source PNG in place — computed a luminance-based alpha ramp (fully transparent below ~42 luminance, fully opaque above ~78, linear ramp between) and multiplied it into the existing alpha channel, removing the background fill while preserving the navy-to-gold artwork (including its soft edge gradients). Verified via pixel-level compositing against the app's actual KPI gradient colors (green/purple/orange, both theme variants) before touching any component code, then confirmed end-to-end in a live Playwright/Chromium session.

Consequence for Item 2's CSS: `mix-blend-mode: overlay` was removed from `.kpi-watermark-img` (now true alpha transparency + `opacity: 0.6` is sufficient and reads more cleanly). Header (`Header.tsx`) and Login page (`LoginPage.tsx`, out of this spec's scope but sharing the same asset) needed no code changes — they benefit automatically since the fix was to the shared PNG.

---

## Item 1 — Header logo: replace emoji with real PNG (`Header.tsx`)

**Current:** `💸 Wallet Mantra` — the money-with-wings emoji inline in `<h1>`.
**File:** `frontend/react/src/components/layout/Header.tsx`

**Change:** replace the emoji `div` with an `<img>` tag:

```tsx
{/* before: */}
{/* <div className="text-5xl mb-3">💸</div> */}

{/* after: */}
<img
  src="/wallet-mantra-logo.png"
  alt=""                          {/* decorative — wordmark is the text label */}
  aria-hidden="true"
  className="h-8 w-8 flex-shrink-0 object-contain"
  style={{ imageRendering: 'crisp-edges' }}
/>
```

Full header logo block becomes:
```tsx
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

**Note:** `h-8` = 32px per decision. The PNG has a dark halo from background-removal
— it renders correctly on the dark header (`var(--card)` / `--bg`). If the halo is
visible in light mode, add `mix-blend-mode: multiply` only under `html.light`.

**Acceptance:** header shows real logo at 32px left of "Wallet Mantra" in both
dark and light mode; no emoji visible.

---

## Item 2 — KPI card watermark: logo PNG with mix-blend-mode (`KpiCarousel.tsx` + `index.css`)

**Current:** `<span className="kpi-watermark">WM</span>` — italic near-transparent
text in the top-right corner of each card. Defined in `index.css`.

**Files:**
- `frontend/react/src/components/shared/KpiCarousel.tsx` — card JSX
- `frontend/react/src/index.css` — `.kpi-watermark` rule

### 2a. Replace JSX in `KpiCarousel.tsx`

In both the mobile scroll slide and the desktop card, replace the `<span>`:

```tsx
{/* before: */}
{/* <span className="kpi-watermark">WM</span> */}

{/* after: */}
<img
  src="/wallet-mantra-logo.png"
  alt=""
  aria-hidden="true"
  className="kpi-watermark-img"
/>
```

### 2b. Replace the CSS rule in `index.css`

```css
/* before: */
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

/* after: */
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

**Visual note (pre-confirmed):** `mix-blend-mode: overlay` on the amber Bills
card will pop well (light gradient). On the dark green Remaining card the
logo's navy region may partially fade — if so, add `filter: brightness(2)` to
the `.kpi-watermark-img` rule to force it lighter without changing the blend.
Verify after first build.

**Acceptance:** all three KPI cards (Remaining/Income/Bills Paid on Overview;
Fixed total/paid/left on Fixed tab) show the real logo watermark in the
top-right. No "WM" text visible anywhere.

---

## Item 3 — Fixed tab 100% celebration animation (`FixedTab.tsx` + `index.css`)

**Trigger:** fires exactly **once** per session when `pct` transitions from < 100
to 100 (i.e. the last commitment is marked paid). Does **not** fire:
- On page reload when already at 100% (would feel intrusive every visit).
- On initial load even if already at 100% (same reason).

### 3a. `FixedTab.tsx` — edge-trigger + overlay state

```tsx
// Add to existing state:
const [celebrating, setCelebrating] = useState(false);
const prevPctRef = useRef<number | null>(null);

// Add after pct is computed (alongside existing derived values):
useEffect(() => {
  if (prevPctRef.current !== null &&
      prevPctRef.current < 100 &&
      pct === 100 &&
      paidCount > 0) {
    setCelebrating(true);
    const t = setTimeout(() => setCelebrating(false), 5200); // 5s + fade
    return () => clearTimeout(t);
  }
  prevPctRef.current = pct;
}, [pct, paidCount]);
```

The overlay renders **full-tab** (covers the entire `FixedTab` content area,
not the header/nav) using `position: fixed` with a high z-index so it sits above
the checklist but below the sticky header:

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

```tsx
// Pre-computed positions (28 pieces radiating from center):
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

### 3b. `index.css` — celebration CSS

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

**Acceptance:**
- Marking the last unpaid commitment triggers a 5-second 🎉 burst radiating
  from the center of the Fixed tab, then disappears automatically.
- Page reload at 100% does NOT re-trigger the animation.
- With `prefers-reduced-motion: reduce`, only the large center 🎉 appears
  briefly; no flying pieces.
- The existing "All fixed expenses paid ✅" celebration card (Spec 22) remains
  — the new animation is additive, not a replacement.

---

## Files
| Item | File(s) |
|---|---|
| 1 — Header logo | `components/layout/Header.tsx` |
| 2a — Card watermark JSX | `components/shared/KpiCarousel.tsx` |
| 2b — Card watermark CSS | `index.css` (replace `.kpi-watermark` → `.kpi-watermark-img`) |
| 3a — Celebration logic | `components/tabs/FixedTab.tsx` |
| 3b — Celebration CSS | `index.css` |

## Out of scope
- AI savings-threshold recommendations (user review item 1) — separate spec.
- Notification bell consolidation (user review item 4) — addressed alongside
  Spec 25's bell work.
- Login page logo/video work — separate (LoginPage.tsx, already in progress).
