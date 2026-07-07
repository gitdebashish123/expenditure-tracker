# Spec 34 — Login Always-Dark (Option A) + Logo Cleanup & Theme-Swap
**Date**: 2026-07-04
**Status**: ✅ Login block (Items 1, 2a, 2b) implemented and verified live in-browser
(both themes, both breakpoints) 2026-07-05. ⛔ Logo block (Items 3–5) BLOCKED — the
source artwork (`walletmantralogo.png`) and pre-generated assets this spec assumes
exist are not present anywhere in the repo or filesystem; see
`.claude/blocked/34-followups-for-reevaluation.md`. Item 5 (watermark resize) was
implemented since it only resizes the existing (unregenerated) asset — the
flood-keying/outline part of the visual improvement is still pending Item 3.
Scope broadened same day to fold in the logo-asset work (Items 3–5) per review decision (Option A).
**Branch**: `feature/sprint0726p1-ui-enhancement` *(confirm active branch before starting)*
**Follows**: `33_login-visual-and-fixed-kpi-differentiation.md`
**Source**: Live-browser design review (Jul 2026, both themes, both breakpoints)
that Spec 33 explicitly deferred (see `.claude/blocked/33-followups-for-reevaluation.md`
item 1 — "'don't break' [light mode] is still in scope", never driven live).
Approved mockups: (a) always-dark login desktop split shown against the current
broken light-mode render; (b) cleaned logo variants on real dark/light header
swatches; (c) settled logo mock — header theme-swap + watermark 54→32px on real
card colors. Logo diagnosis is grounded in pixel analysis of the source artwork
(`walletmantralogo.png`, 1456×840, opaque white background) and the live code
references.

---

## Context — login (Items 1–2)

Spec 33 rebalanced the login and introduced the gold token, but its light-mode
behavior was never verified in a browser. Live testing now shows the light-mode
login is **visibly broken** — three coupled failures, all grounded in `index.css`
+ `LoginPage.tsx`:

1. **Split-brain panel.** `.login-visual` (left) has a hardcoded
   `background: #08080d` that never responds to `html.light`, while
   `.login-form-panel` (right) uses `background-color: var(--bg)`, which flips to
   `#f4f4f8`. Result in light mode: left half black, right half near-white —
   split straight down the middle.

2. **Invisible left-panel text.** The left panel uses Tailwind classes
   (`text-white`, `text-white/70`, `text-white/50`) that the global light-mode
   remap (correctly, for the rest of the app) turns into dark navy
   (`var(--text)` = `#1a1a2e`, `var(--text-sub)`). But the left panel *stayed
   dark*, so it's now dark-navy text on a near-black surface — the wordmark,
   tagline, and value prop all vanish.

3. **Anemic CTA.** In light mode `--gold-navy` becomes `#ede9fe` (pale lavender)
   and `--gold` becomes `#b8860b`, so the primary Sign In button renders as pale
   lavender with brown text — the weakest-looking element on the page.

Because theme is a persisted global `html.light` class and there is **no theme
toggle on the login page** (the sun/moon lives in `Header`, which only exists
post-login), a user who set light mode inside the app, then logs out, is *trapped*
on this broken login every visit with no way to switch it from that screen.

## Context — logo (Items 3–5)

The same review surfaced a logo-legibility problem, now diagnosed against the
actual asset and code:

- **The mark is muddy on dark surfaces.** The deployed `public/wallet-mantra-logo.png`
  does not read cleanly on the dark header — an indistinct dark blob with a
  ragged edge (the navy "W" strokes have almost no contrast on near-black, and
  the background isn't cleanly transparent). The `.kpi-watermark-img` CSS comment
  claiming the PNG is "chroma-keyed out" is inaccurate in practice for dark
  surfaces. Pixel analysis of the *source* artwork (`walletmantralogo.png`) shows
  it's a **fully-opaque white-background** raster (uniform alpha, ~4% of the mark
  is very-dark navy that vanishes on dark). So the asset genuinely needs
  reworking — no CSS change fixes it.
- **The card watermark is oversized.** `.kpi-watermark-img` is 54×54px, ~70%
  larger than the 32×32px header mark (`h-8 w-8`), so it competes with the card
  value instead of reading as a quiet watermark.

**Key framing that drives the logo decision:** of the five logo placements, four
are always on dark — login left panel (now always-dark, Item 1), login mobile
logo, and the two KPI watermarks (which sit on dark gradient/slate cards in both
themes). **Only the header in light mode needs a mark that reads on white.**

## Decisions (confirmed via mockup)

| # | Decision | Choice |
|---|----------|--------|
| D1 | Login theme | **Option A — login route is always dark**, regardless of `html.light`. Rationale: the brand panel (dark video, glowing logo) is designed for dark and never looks as good on white; fixed-dark auth screens are a common pattern; and it kills the whole class of light-mode login bugs at once. Rest of app still honors `html.light`. |
| D2 | Logo approach | **Two-asset theme-swap.** A dark-surface mark used everywhere on dark, and a clean light mark used only for the header in light mode. |
| D3 | Which marks | **Dark surfaces = variant B** (clean transparent + subtle light outline, keeps true gold+navy, outline lets the silhouette separate on dark). **Light header = variant A** (clean transparent, untouched brand navy — reads perfectly on white). Rejected: C (recolors brand navy) and D (chip reintroduces a box on already-dark surfaces). |
| D4 | Card watermark size | **54px → 32px**, both themes, to match the header mark. |

**What this spec does NOT touch (deferred — see Out of scope):** the Fixed-tab
light-mode contrast issues from the same review (washed-out due-reminder alerts,
`.kpi-card-fixed-left` reading as unstyled on white, low-contrast unpaid rows) —
flagged but not mocked or decided, so they wait for their own cycle.

---

## Item 1 — Login always dark: re-scope tokens on `.login-split` (`index.css`)

**Current:** the login subtree inherits `html.light`'s token values, so half of
it flips to light while the hardcoded-dark half does not.

**Change:** re-declare the dark token values scoped to `.login-split`. Because
CSS custom properties inherit from the nearest declaring ancestor, every
downstream rule that reads these vars — the `.text-white*` remaps, the global
`input { background: var(--card2) }` override, `.login-form-panel`'s
`var(--bg)`, and all the gold accents — resolves **dark automatically**, with no
per-element overrides. This is the entire mechanism.

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

Place this in the LOGIN PAGE section of `index.css`, immediately after the
`.login-split { min-height:100vh; display:flex; }` base rule.

**Notes / edge cases to verify at implementation:**
- `.login-visual` (`#08080d`) and `.login-preview-card` (`#000`) are already
  hardcoded dark — unaffected, still correct.
- `:focus-visible` uses `--accent` (indigo), not re-scoped — fine on dark.
- The `<body>` background behind the split is root `var(--bg)` (light in light
  mode), but `.login-split` is `min-height:100vh` with two full-height panels
  covering it. If any overscroll/sub-pixel gap shows light, add
  `background-color: var(--bg)` to `.login-split` itself (now dark via the
  re-scope) — confirm in-browser whether needed.
- Applies at **both** breakpoints: mobile (<900px, form-only) login also becomes
  dark in light mode. That's intended under Option A and is more brand-consistent.

**Acceptance:**
- With `html.light` active app-wide, navigating to `/login` shows a **fully dark**
  login — both panels dark, all text (wordmark, tagline, value prop, quote,
  form labels) legible, CTA a vivid navy/gold. No split-brain, no invisible
  text, no pale CTA.
- Toggling the app theme has **no visible effect on the login page** (it's always
  dark), but still works everywhere else post-login.
- Dark-mode login is unchanged by Item 1 (it was already dark).

---

## Item 2 — Two polish tweaks from the approved mockup (`index.css`, `LoginPage.tsx`)

Both were included in the Option-A mockup that was approved, so they ship with it.

**2a — Lift the form-card border so the card actually reads (`index.css`).**
`.login-form-card` currently uses `border: 1px solid var(--gold-border)`
(`#4a3a12`), which is nearly imperceptible against `--card: #111118`. Bump the
card border specifically to a brighter muted gold:

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

Field borders (`.login-split .login-field input`) **keep** `--gold-border`
(`#4a3a12`) — only the card boundary changes. (If preferred as a token rather
than a literal, introduce `--gold-border-strong: #6b5620` in the `.login-split`
re-scope block and use it here — implementer's call; literal is fine given it's
one rule.)

**2b — Widen the form card so it holds its half (`LoginPage.tsx`).**
The form wrapper is `className="w-full max-w-sm relative login-form-card"`
(384px), which floats small in the 48% right panel. Change `max-w-sm` →
`max-w-md` (448px) so it carries more weight against the fuller left panel.

```tsx
// LoginPage.tsx — the inner form wrapper
<div className="w-full max-w-md relative login-form-card">
```

**Acceptance:**
- Desktop dark login: the form-card border is clearly visible (reads as a card),
  and the card is visibly wider than before, better balanced against the left panel.
- Mobile login: unchanged by 2a (card styling is ≥900px-gated); `max-w-md` has no
  effect below its own width so mobile is unaffected in practice — confirm.

---

## Item 3 — Logo asset cleanup: two clean marks (`public/`)

**Current:** one muddy asset (`public/wallet-mantra-logo.png`) used by every
placement; it does not read cleanly on dark and has no light-optimized counterpart.

**Change:** from the white-background source artwork, produce **two** cleaned,
truly-transparent marks and place them in `public/`:

- **`public/wallet-mantra-logo.png` — REPLACED** with the **dark-surface mark
  (variant B)**: background flood-keyed to true transparency (alpha 0), cropped to
  the mark, square-padded, plus a subtle light outline so the silhouette separates
  on dark. Every current reference to `/wallet-mantra-logo.png` (header, login
  brand row, login mobile logo, both KPI watermarks) keeps pointing here and is
  correct, because all of those sit on dark surfaces.
- **`public/wallet-mantra-logo-light.png` — NEW** = the **light-header mark
  (variant A)**: same clean transparency, **no outline, untouched brand navy** —
  reads perfectly on white. Consumed only by the header in light mode (Item 4).

**Naming convention (documented so it isn't confusing later):**
`wallet-mantra-logo.png` = the dark-surface mark by convention (it's the default
because most placements are dark); `-light.png` = the light-header variant only.

**Reproducible processing.** The two assets are generated deterministically from
the source (`walletmantralogo.png`) by `scripts/process-logo.py` (delivered
alongside this spec):
1. Flood-fill the light/near-neutral background inward from the image borders →
   alpha 0 (this preserves interior gold highlights, unlike a naive luminance key
   that would punch holes in them).
2. Feather the alpha edge (Gaussian ~1.2px), crop to content bbox, pad to square.
3. Variant B only: add a dilated light ring (white ~150α, blurred) as the outline.
4. Export both at 256×256 (crisp for the 32px watermark and 56px login logo at 2×).

Pre-generated 256×256 assets are available for direct drop-in; the script is the
source of truth if they must be regenerated. **Commit the source artwork** into
the repo (e.g. `frontend/react/brand/wallet-mantra-source.png`) alongside the
script so the assets remain reproducible — the current `public/wallet-mantra-logo.png`
is the muddy processed file, NOT a usable source.

**Acceptance:**
- Both files exist in `public/`, are truly transparent (no rectangular ghost),
  and are visually clean at 32px and larger.
- Variant B reads clearly on the dark header/cards; variant A reads clearly on
  a white header.

---

## Item 4 — Header logo theme-swap (`Header.tsx`)

**Current:** `Header.tsx` renders `<img src="/wallet-mantra-logo.png" ...>`
unconditionally. `theme` is already available from `useTheme()` (used for the
sun/moon toggle), so no new wiring is needed.

**Change:** swap the source by theme:

```tsx
// Header.tsx — the brand-row logo <img>
src={theme === "dark" ? "/wallet-mantra-logo.png" : "/wallet-mantra-logo-light.png"}
```

No other placement changes: login (always dark) and the KPI watermarks keep
`/wallet-mantra-logo.png` (the dark mark), which is correct for their surfaces.

**Acceptance:**
- Header in dark mode shows the outlined dark mark (clean, no muddy ghost).
- Header in light mode shows the clean true-navy mark, legible on the white header.
- Toggling the theme swaps the mark with no layout shift (both are 256×256,
  rendered at `h-8 w-8`).

---

## Item 5 — Shrink the KPI card watermark 54px → 32px (`index.css`)

**Current** (`.kpi-watermark-img`): `width: 54px; height: 54px; opacity: 0.6;`.

**Change:** drop to 32px to match the header mark; keep `opacity: 0.6` and the
positioning. Update the stale comment (which claims the PNG is "chroma-keyed" and
warns about `mix-blend-mode`) to reflect the Spec-34 two-asset reality.

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

Single rule, applies in both themes and at both breakpoints (mobile slide +
desktop shell share the class).

**Acceptance:**
- Card watermark renders at 32px on both the gradient cards and the "Fixed left"
  slate, in both themes — quiet, not competing with the value.
- Opacity/position unchanged; no overlap with the card label/value.

---

## Files
| Item | File(s) |
|---|---|
| 1 — Always-dark token re-scope | `index.css` |
| 2a — Card border lift | `index.css` |
| 2b — Form card widen | `pages/LoginPage.tsx` |
| 3 — Two clean logo assets | `public/wallet-mantra-logo.png` (replace), `public/wallet-mantra-logo-light.png` (new), `frontend/react/brand/wallet-mantra-source.png` (new source), `scripts/process-logo.py` (new) |
| 4 — Header theme-swap | `components/layout/Header.tsx` |
| 5 — Watermark 54→32px | `index.css` |

## Sequencing
1. **Login block (Items 1, 2a, 2b)** — independent, can land in one commit; all
   touch only the login surface.
2. **Logo block (Items 3, 4, 5)** — Item 3 (assets) first, then Items 4 & 5 which
   consume them. Independent of the login block.
3. The two blocks can ship together or separately. Whole spec is **independent of
   any Fixed-tab work**.

## Implementation / verification notes
- **Login must be driven live in a browser in LIGHT theme specifically** — the
  whole point, and exactly the check Spec 33 skipped. `/login` at both <900px and
  ≥900px with `html.light` active → confirm fully-dark; toggle back to dark →
  confirm no regression. Ephemeral-Playwright pattern (Chromium cached at
  `~/Library/Caches/ms-playwright`) available per the Spec 33 follow-up.
- **Logo: verify both themes** — header mark clean on dark AND on the white
  header after the swap; watermark at 32px on cards in both themes.
- `npm run build` must pass clean (tsc). `npm run lint` remains unavailable on
  this branch (pre-existing, see `.claude/blocked/33-followups-for-reevaluation.md`
  item 2) — note if still true.

## Out of scope (deferred to a future review → mockup → spec)
Surfaced in the same Jul-04 review but **not** mocked or decided, so not specced here:
- **Fixed-tab due-reminder alerts unreadable in light mode** — `text-red-300` on
  `red-500/10` renders pink-on-pink; the most urgent items on the page, currently
  the least legible (likely fails WCAG AA).
- **`.kpi-card-fixed-left` looks unstyled on white** — the always-dark slate
  (`#2a2a3d`, correct in dark per Spec 33 D2) reads as a heavy block on the light
  page and outweighs the gradient cards. May need a genuine light-mode treatment.
- **Unpaid list rows low-contrast in light mode** — "Car Loan" etc. render very
  light grey on white.
- **Login brand-row logo size (56px) and mobile login logo** — left unchanged;
  only the *card watermark* was requested to shrink (D4). The 56px brand-row guess
  flagged in `.claude/blocked/33-followups-for-reevaluation.md` item 3 is a
  separate sizing question, not addressed here.
- **Redrawing the logo artwork** — this spec cleans/keys the existing raster; it
  does not re-master the source vector.
- Theme *persistence* behavior (login inheriting the last theme is now moot for
  the login's appearance, since login is always dark).
