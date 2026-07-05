# Implementation Plan: Login Always-Dark (Option A) + Logo Cleanup & Theme-Swap
**Spec**: `.claude/specs/34_login-always-dark.md`
**Date**: 2026-07-04 (login items) · 2026-07-04 extended (logo items 4–6)
**Branch**: `feature/sprint0726p1-ui-enhancement`

---

## Overview

**Execution status (2026-07-05): Items 1–3 and 6 DONE and verified live in-browser
(both themes, both breakpoints — screenshots confirmed no split-brain, no invisible
text, no pale CTA, dark mode unchanged). Items 4–5 BLOCKED — see
`.claude/blocked/34-followups-for-reevaluation.md`.**

6 items total, all frontend-only. Two independent blocks:

- **Login block (Items 1–3)** — `index.css` ×2 + `LoginPage.tsx` ×1. Fixes the
  broken light-mode login by forcing the login route dark, plus two polish edits.
- **Logo block (Items 4–6)** — new/replaced assets in `public/` + a header
  conditional + one CSS size change. Fixes the muddy mark on dark and adds a
  clean light-header variant via a two-asset theme-swap.

No backend changes. All line numbers verified against current file state; the
login-block code matches the spec exactly (no drift).

Ordering within the login block is smallest-blast-radius-first (the two
single-line polish edits before the token re-scope). The logo block is
independent and can land in a separate commit; within it, assets (Item 4) must
exist before the header swap (Item 5) and are unrelated to the watermark size
(Item 6).

---

## Item 1 — Lift the form-card border (spec 2a)
**Scope**: Frontend-only
**Files**: `frontend/react/src/index.css` (lines 493–500)

**Root cause**: `.login-form-card`'s border is `1px solid var(--gold-border)`,
resolving to `#4a3a12` in dark mode — nearly invisible against `--card: #111118`.

**What to do**: Change the `border` line to a hardcoded brighter muted gold
(field borders elsewhere keep `--gold-border`):

```css
@media (min-width: 900px) {
  .login-form-card {
    background: var(--card);
    border: 1px solid #6b5620;   /* was var(--gold-border) #4a3a12 — lifted so the card boundary reads */
    border-radius: 16px;
    padding: 26px;
  }
}
```

**Acceptance**: Desktop dark login — form-card border clearly visible as a card
boundary. Mobile untouched (`min-width: 900px`-gated).

---

## Item 2 — Widen the form card (spec 2b)
**Scope**: Frontend-only
**Files**: `frontend/react/src/pages/LoginPage.tsx` (line 155)

**Root cause**: `<div className="w-full max-w-sm relative login-form-card">` caps
the form at 384px, floating small inside the 48% right panel.

**What to do**: `max-w-sm` → `max-w-md` (448px):

```tsx
<div className="w-full max-w-md relative login-form-card">
```

**Acceptance**: Desktop — card visibly wider, better balanced. Mobile — no effect
(`max-w-*` only constrains).

---

## Item 3 — Always-dark token re-scope on `.login-split` (spec Item 1)
**Scope**: Frontend-only
**Files**: `frontend/react/src/index.css` (insert after line 424)

**Root cause**: `.login-split` (lines 421–424) declares no tokens, so it inherits
`:root`/`html.light`. In `html.light`: `.login-visual` (line 440) hardcodes
`#08080d` while `.login-form-panel` (line 487) uses `var(--bg)` → split-brain;
the `.text-white*` remaps (lines 113–128) turn left-panel text dark-navy →
invisible on the dark panel; `.login-cta-gold` (lines 607–610) goes pale
lavender. The global `input` rule (lines 157–164) is part of the same cascade.

**What to do**: Insert immediately after the `.login-split { min-height:100vh;
display:flex; }` rule (at line 425):

```css
/* ── Login is ALWAYS dark — Option A (Spec 34) ─────────────────────
   The rest of the app honors html.light; the login route opts out.
   Re-declaring the dark token values on .login-split means html.light's
   overrides never cascade in — the .text-white* remaps, input bg override,
   form-panel var(--bg), and gold accents all resolve dark downstream with
   no element-level overrides needed. */
.login-split {
  --bg:        #0a0a0f;
  --card:      #111118;
  --card2:     #1a1a28;
  --card3:     #22223a;

  --text:      #ffffff;
  --text-sub:  rgba(255, 255, 255, 0.65);
  --text-muted:rgba(255, 255, 255, 0.45);

  --border:    rgba(255, 255, 255, 0.08);
  --border-lg: rgba(255, 255, 255, 0.12);

  --gold:        #facc15;
  --gold-border: #4a3a12;
  --gold-navy:   #1e1b4b;
}
```

**Verify during implementation** (per spec edge-cases):
- `.login-visual` (`#08080d`, line 440) and `.login-preview-card` (`#000`, line
  459) already dark — confirm unaffected.
- `:focus-visible` (lines 85–88) uses `--accent` (not re-scoped) — confirm fine.
- If any overscroll/sub-pixel gap shows light behind the split, add
  `background-color: var(--bg)` to `.login-split` itself (now dark). Don't add
  pre-emptively.
- Applies at both breakpoints — mobile (<900px) login also goes dark under
  `html.light`. Intended, not a regression.

**Acceptance**: With `html.light` active, `/login` renders fully dark at both
breakpoints — both panels dark, all text legible, CTA vivid navy/gold, no
split-brain / invisible text / pale CTA. Theme toggle has no effect on `/login`
but still works everywhere else. Dark-mode login unchanged.

---

## Item 4 — Generate & place the two clean logo assets (spec Item 3)
**Scope**: Frontend-only (assets + build-time script)
**Files**:
- `frontend/react/public/wallet-mantra-logo.png` — **replace** with dark mark (B)
- `frontend/react/public/wallet-mantra-logo-light.png` — **new**, light mark (A)
- `frontend/react/brand/wallet-mantra-source.png` — **new**, committed source
- `scripts/process-logo.py` — **new**, reproducible generator

**Root cause**: The deployed `public/wallet-mantra-logo.png` is muddy on dark (no
clean transparency; dark-navy "W" vanishes on near-black). Source artwork
(`walletmantralogo.png`) is a fully-opaque white-background raster — needs real
keying, not the CSS "chroma-keyed" comment's claim.

**What to do**:
1. Commit the white-bg source to `frontend/react/brand/wallet-mantra-source.png`.
2. Add `scripts/process-logo.py` with this logic (PIL + numpy + scipy):
   - Flood-fill light/near-neutral background inward from the four borders →
     alpha 0 (keeps interior gold highlights intact; a naive luminance key would
     hole them).
   - Feather alpha (Gaussian ~1.2px), crop to bbox, pad square.
   - **Variant A** (`wallet-mantra-logo-light.png`): stop here — clean transparent,
     untouched brand navy.
   - **Variant B** (`wallet-mantra-logo.png`): additionally add a dilated light
     ring (white ~150α, blurred ~1px) as an outline so the mark separates on dark.
   - Export both at 256×256 (LANCZOS).
3. Drop the two exported PNGs into `public/`.

Pre-generated 256×256 assets and the exact script were produced during review and
can be dropped in directly (they're deterministic from the source); re-running the
script must reproduce them.

**Acceptance**: Both files in `public/`, truly transparent (no rectangular ghost),
clean at 32px+. B reads on dark, A reads on white.

---

## Item 5 — Header logo theme-swap (spec Item 4)
**Scope**: Frontend-only
**Files**: `frontend/react/src/components/layout/Header.tsx` (the brand-row `<img>`, ~line 32–37)

**Root cause**: Header renders `src="/wallet-mantra-logo.png"` unconditionally, so
in light mode the dark mark sits muddily on the white header. `theme` is already
in scope from `useTheme()` (line 20) — no new wiring.

**What to do**: Swap the `<img>` source by theme:

```tsx
<img
  src={theme === "dark" ? "/wallet-mantra-logo.png" : "/wallet-mantra-logo-light.png"}
  alt=""
  aria-hidden="true"
  className="h-8 w-8 flex-shrink-0 object-contain"
/>
```

No other placement changes — login (always dark, Item 3) and the two KPI
watermarks keep `/wallet-mantra-logo.png` (the dark mark), correct for their
dark surfaces.

**Acceptance**: Header dark → outlined dark mark (no muddy ghost); header light →
clean true-navy mark on white; toggling swaps with no layout shift (both 256×256
at `h-8 w-8`).

---

## Item 6 — Shrink the KPI card watermark 54px → 32px (spec Item 5)
**Scope**: Frontend-only
**Files**: `frontend/react/src/index.css` (`.kpi-watermark-img` rule, ~lines 356–366 region)

**Root cause**: `.kpi-watermark-img` is `width: 54px; height: 54px` — ~70% larger
than the 32px header mark, competing with the card value. Both the mobile slide
and desktop shell share this class.

**What to do**: Set width/height to 32px; keep `opacity: 0.6` and position; refresh
the stale comment (which references "chroma-keyed"/`mix-blend-mode`) to note the
Spec-34 two-asset reality:

```css
.kpi-watermark-img {
  position: absolute;
  right: 10px;
  top: 8px;
  width: 32px;    /* was 54px — Spec 34 D4: match the 32px header mark */
  height: 32px;
  object-fit: contain;
  opacity: 0.6;
  pointer-events: none;
  user-select: none;
}
```

**Acceptance**: Watermark renders at 32px on gradient cards and the "Fixed left"
slate, both themes; quiet, no overlap with label/value.

---

## Files touched (summary)

| Item | File | Change |
|---|---|---|
| 1 — Card border lift | `frontend/react/src/index.css` | line 496 (1 line) |
| 2 — Form card widen | `frontend/react/src/pages/LoginPage.tsx` | line 155 (1 line) |
| 3 — Always-dark re-scope | `frontend/react/src/index.css` | insert after 424 (~24 lines) |
| 4 — Logo assets | `public/wallet-mantra-logo.png` (replace), `public/wallet-mantra-logo-light.png` (new), `brand/wallet-mantra-source.png` (new), `scripts/process-logo.py` (new) | assets + script |
| 5 — Header swap | `frontend/react/src/components/layout/Header.tsx` | ~line 33 (1 attr) |
| 6 — Watermark size | `frontend/react/src/index.css` | 2 lines (54→32) |

## Dependencies between items
- Login block (1, 2, 3): none — one commit.
- Logo block: Item 4 (assets) before Item 5 (header swap consumes them). Item 6
  independent. Blocks are independent of each other; either order.

## Verification (per spec)
- **Login: drive live in LIGHT theme** at <900px and ≥900px with `html.light` —
  confirm fully-dark; toggle to dark, confirm no regression. Ephemeral-Playwright
  (Chromium at `~/Library/Caches/ms-playwright`) available.
- **Logo: both themes** — header mark clean on dark AND white after swap;
  watermark 32px on cards in both themes.
- `npm run build` (tsc + Vite) must pass clean.
- `npm run lint` expected still unavailable on this branch (pre-existing, see
  `.claude/blocked/33-followups-for-reevaluation.md` item 2) — note in summary if
  still true; don't silently skip without confirming it's still broken.

## Out of scope
Fixed-tab light-mode contrast (due-reminder alerts, `.kpi-card-fixed-left`, unpaid
rows), login brand-row/mobile logo resize (only the *card watermark* shrinks per
D4), and redrawing the logo artwork — all deferred per the spec. Do not fold in.
