# Follow-ups — Spec 34: Login Always-Dark + Logo Cleanup & Theme-Swap

**Origin**: `.claude/specs/34_login-always-dark.md`
**Plan**: `.claude/plans/34-login-always-dark.md`
**Status**: Login block (plan Items 1–3 / spec Items 1, 2a, 2b) implemented and
verified live in a real browser (Playwright/Chromium against the Vite dev server),
both themes, both breakpoints. Watermark resize (plan Item 6 / spec Item 5)
implemented. Logo asset generation (plan Item 4 / spec Item 3) and the header
theme-swap that consumes it (plan Item 5 / spec Item 4) are **BLOCKED** — not
implemented this session.
**Date noted**: 2026-07-05

---

## 1. BLOCKED — Logo source artwork and pre-generated assets do not exist

**What the spec assumes**: Spec Item 3 states the source raster
(`walletmantralogo.png`, 1456×840, opaque white background) and a
`scripts/process-logo.py` generator, plus the two pre-generated 256×256 output
assets, "were produced during review and can be dropped in directly."

**What was actually found this session**: none of the following exist anywhere in
the repo or on the filesystem (searched the full repo tree, `frontend/react/`,
`frontend/react/public/`, and did an unrestricted filesystem `find` for the
filenames):
- `walletmantralogo.png` (the claimed source) — not found.
- `scripts/process-logo.py` — not found (`scripts/` only contains `uat_test.py`).
- `frontend/react/brand/` directory — does not exist.
- `frontend/react/public/wallet-mantra-logo-light.png` — does not exist.
- Any pre-generated 256×256 output PNGs matching the spec's description — not found.

The only logo asset actually in the repo is the current
`frontend/react/public/wallet-mantra-logo.png` (882×773, RGBA). Pixel-checked it
this session: the four corners are alpha-0 (transparent), but the background
*within* the bounding box is a near-opaque dark gradient fading to transparent at
the edges — visually this is the "muddy blob with a ragged edge" the spec
describes, not a clean flood-keyed mark. So the spec's diagnosis of the *problem*
is accurate; it's the claim that the *fix assets already exist* that doesn't hold.

**Why this blocks Items 3 and 4 (spec numbering)**:
- Item 3 (asset generation) needs the white-background source to key against —
  without it, there is nothing to run `process-logo.py`-equivalent logic on.
  Fabricating a flood-key/outline treatment from the *already-muddy* current PNG
  would bake in the existing edge artifacts rather than fix them, and inventing
  new brand artwork from scratch is a design decision, not an engineering one —
  not attempted.
- Item 4 (header theme-swap) directly consumes
  `wallet-mantra-logo-light.png`, produced by Item 3. Wiring the conditional
  `src={theme === "dark" ? ... : "/wallet-mantra-logo-light.png"}` without that
  file existing would just point the light-mode header at a 404.

**Action needed**: whoever ran the mockup review that produced the "approved
mockups" referenced in the spec header (logo variants on dark/light swatches) needs
to supply the actual source artwork and/or the two pre-generated PNGs — check
wherever that review's outputs were saved (design tool export, chat attachment,
another machine/session) and add them to this repo (e.g.
`frontend/react/brand/wallet-mantra-source.png`) before Items 3–4 can be
implemented. Once the source exists, `scripts/process-logo.py` can be written per
the spec's documented algorithm (border flood-fill → alpha 0, feather ~1.2px,
crop+pad square, variant B gets a dilated light outline, export both at 256×256).

---

## 2. Partial implementation note — watermark resize shipped ahead of asset rework

Plan Item 6 / spec Item 5 (`.kpi-watermark-img` 54px → 32px) was implemented as
planned since it's a pure CSS size change, independent of which PNG is loaded.
The accompanying code comment in `index.css` was corrected to **not** claim the
asset itself is now flood-keyed/outlined (the original plan's suggested comment
text asserted this) — it explicitly notes the rework is pending Item 1 above.
Visual effect right now: the *existing* muddy asset renders at 32px instead of
54px — smaller, but not yet clean. Re-verify this watermark visually once Item 3
above unblocks and the real asset lands (it should look meaningfully better, not
just smaller).

---

## 3. Verified this session — login block

Live-verified via a Playwright/Chromium session against `npm run dev`
(`http://localhost:5174`, port 5173 was already occupied) with `html.light`
toggled via `document.documentElement.classList`:
- Desktop (1440×900) + light forced: fully dark render, wordmark/tagline/value-prop
  all legible, form-card border visible, CTA vivid navy/gold. Matches acceptance
  criteria exactly.
- Mobile (390×844) + light forced: same — fully dark, legible, no split-brain.
- Desktop + dark (no `.light` class): pixel-identical composition to the
  light-forced screenshot, confirming the theme toggle has zero visible effect on
  `/login` and dark mode is unregressed.

`npm run build` (tsc + Vite) passes clean, zero TypeScript errors.

---

## 4. OPEN (pre-existing, not introduced here) — `npm run lint` cannot run

Same gap recorded in specs 31/32/33's blocked follow-ups. Confirmed still true this
session: `npm run lint` fails with `sh: eslint: command not found`; `eslint` is
absent from `frontend/react/node_modules/.bin`. Type-level correctness is confirmed
via `tsc` (part of `npm run build`), but the CLAUDE.md zero-ESLint-warning policy
still cannot be checked.

**Action needed**: `cd frontend/react && npm install` (or investigate why `eslint`
keeps dropping from the lockfile/`node_modules` across sessions), then re-run
`npm run lint` against `index.css`/`LoginPage.tsx` specifically for this spec's
changes.

---

## Environment note for whoever re-reads this

Confirmed present this session: Chromium cached at `~/Library/Caches/ms-playwright`
(`chromium-1228`), and the JS `playwright`/`playwright-core` packages present in
`frontend/react/node_modules/.bin` — no Python playwright install, so verification
scripts must be written in Node (`require('playwright')` from
`frontend/react/node_modules`), not Python. This differs from what some earlier
blocked-notes assumed (`chromium-cli` was never actually checked/available in this
or prior sessions to my knowledge) — the working pattern is a small Node script
launching `playwright`'s `chromium.launch()` directly against the Vite dev server.
