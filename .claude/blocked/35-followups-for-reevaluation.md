# Follow-ups — Spec 35: Login Page Premium Redesign

**Origin**: `.claude/specs/35_login-premium-redesign.md`
**Plan**: `.claude/plans/35-login-premium-redesign.md`
**Status**: All 6 items (0, 1, 2, 3, 4, 5) implemented and live-verified this session.
`npm run build` clean. Nothing is blocked in the sense of "couldn't be done" — this doc
records deviations from the plan's exact numbers (made to fix a real defect found during
execution) and a few things that weren't independently verified, so a future session
doesn't have to rediscover them.
**Date**: 2026-07-07

---

## 1. Logo mark replacement (Item 0) — done, produced via automated keying, not a designer pass

Both `frontend/react/public/wallet-mantra-logo.png` (dark-surface) and
`wallet-mantra-logo-light.png` (light-surface) were replaced this session, generated
from the user-supplied reference
(`/Users/debashish/Desktop/01_business/feedback-self/login/logo-v1/suggestion/ChatGPT Image Jul 7, 2026, 12_27_53 AM.png`
+ `dark.png`) via a one-off Python/PIL script (not committed to the repo — ad hoc,
run from the scratchpad). Originals backed up to
`/private/tmp/claude-501/.../scratchpad/logo/backup-originals/` (session-scoped temp
dir — copy elsewhere if you want to keep them past this session).

**Dark variant** — border-seeded luminance-as-alpha keying against `dark.png`'s flat
`(0,0,0)` background, then unpremultiplied. Verified clean (no halo/box) by compositing
onto white, magenta, and the real login background — see method notes below if
regenerating. Legible at 32/56/64px (padlock glyph and thin wireframe blade shape
lose some definition at 32px, but the core wallet+W+arrow silhouette stays crisp — this
was judged acceptable, not re-attempted with a simplified crop).

**Light variant** — extracted from the 4-panel comp's "Light BG" quadrant (not the dark
one), using a luminance-distance-from-background alpha (background measured ~236,
mild vignette to ~230 at corners). Two bugs were caught and fixed *during* this
session's own extraction (documented so a re-run doesn't repeat them):
- First attempt's bounding-box detection was too sensitive to the panel's vignette and
  grabbed the entire quadrant.
- Second attempt's bbox included the "Light BG" caption text baked into the comp —
  fixed by trimming the bottom 18% of the panel before analysis.

Final result composites cleanly on white with no visible box. **Not independently
verified against the app's actual light-mode header live** (see §3 below) — only
verified via isolated compositing against `#ffffff`, which is what light mode's
`--card` token resolves to (`index.css`, light-mode block), so this should be
equivalent, but hasn't been eyeballed in the running app.

**If redone properly later**: get either an SVG retrace or a designer export with true
alpha instead of ad hoc luminance keying — this session's approach is a solid
approximation but a hand-cut mask would preserve interior fine detail (the padlock,
the thin outline) better at small sizes than automated thresholding can.

**Side effect, not addressed**: `KpiCarousel.tsx` (lines 47, 86) renders the same
`/wallet-mantra-logo.png` as a 32px watermark and does **not** theme-swap — it inherits
the new dark-surface mark automatically (fine in dark mode) but in light mode still
shows the dark-surface asset regardless of a KPI card's own background. Not a halo
problem now (the new asset has none), just a potential low-contrast legibility issue on
light card backgrounds — worth a quick look, not fixed here since it's outside Item 0's
stated file list.

---

## 2. Layout overflow at common laptop heights — plan's exact numbers had to change

The plan specified `padding-block ~56px` and an unconstrained-width preview card
(scaling to the full 55% column width). Testing at 1366×768 and 1280×720 (both real,
common laptop resolutions) surfaced a genuine defect: the 16:10 preview card scaled to
~430px tall at full column width, which — combined with the new feature list and
insight strip from Item 2 — pushed the rotating quote off-screen and produced document
scroll (measured: 36–108px of page overflow depending on viewport). This is the exact
failure mode flagged as a risk during the spec-review conversation before this plan was
written, and it reproduced as predicted.

**Fixes applied (deviating from the plan's literal numbers, not from its intent):**
- `.login-visual`/`.login-form-panel` top padding: 56px → **32px** (still equal between
  the two panels, still satisfies "equal top anchor" — just a smaller number).
- `.login-preview-card`: capped at `width: min(360px, 100%)` instead of stretching to
  full column width (via the container's default `align-items: stretch`).
- Added a `@media (min-width: 900px) and (max-height: 820px)` fallback that further
  tightens gaps (14px→6px) and shrinks the preview to `min(200px, 100%)` — kept the top
  padding identical across this breakpoint so the top-alignment invariant holds at
  every height.
- `.login-split` changed from `min-height: 100vh` to a **desktop-only** `height: 100vh`
  (inside the 900px media query), with `.login-visual` given `overflow-y: auto; min-height: 0`.
  This guarantees the sign-in card always renders in full (it's the functional part);
  if the hero content still doesn't fit at an extreme height, the hero scrolls
  internally rather than growing the page or clipping the card. Mobile
  (`.login-split` base rule) was deliberately left on `min-height: 100vh` — changing it
  there too would remove the safety margin phones need for on-screen keyboards / text
  zoom, which wasn't tested and wasn't part of this defect.
- `.login-quote-flow` given `min-height: 32px` (22px in the short-viewport fallback) and
  `position: relative`. Root cause: `.login-quote`'s children are `position: absolute`,
  so without an explicit min-height the wrapper collapsed to ~4px and didn't reserve
  real space in the `space-between` flex flow — this was actually a **pre-existing**
  latent bug (not introduced by this session), just never surfaced before because the
  pre-35 hero had fewer blocks and enough natural slack to hide it.

**Verified after fixes**: `document.body.scrollHeight === window.innerHeight` (no
overflow) at 1280×720, 1366×768, 1440×900, and 1920×1080 — all four checked via
Playwright, screenshots confirm the full seven-block hero renders with the quote
visible and no scrollbar.

**If re-evaluating**: the exact pixel numbers above (32px, 360px, 820px breakpoint,
200px, 6px) were tuned empirically against these four viewports, not derived from a
formula — if a future redesign changes the feature list length or preview aspect
ratio, re-check at 1280×720 specifically, it's the tightest common case.

---

## 3. Header light-mode theme-swap — wired but not live-screenshotted

`Header.tsx` now branches `src` on `theme` (Item 0's held-back Spec-34 change,
finally applied). `npm run build` confirms it type-checks and the ternary logic is
straightforward, and the light-surface asset was separately verified clean against
`#ffffff` (§1 above, which is what `--card` resolves to in light mode per `index.css`).
However, a **live authenticated screenshot of the actual header in light mode was not
taken** — login with the `.env`-documented default admin
(`admin@spendsense.local` / `changeme123`) failed against the running backend (a
custom password is presumably set), and no further credential guesses were attempted.
**Action needed**: log in once as any user, toggle to light mode, and eyeball the
header logo — expected to be fine given the isolated verification, but not confirmed
in the running app.

---

## 4. Pre-existing — `npm run lint` still unavailable

Same gap noted in specs 31–34's blocked docs. `eslint: command not found` —
`node_modules/.bin` still doesn't have it. Not introduced or touched this session.
`tsc` (via `npm run build`) is clean, which is the only enforceable check available.

---

## 5. Item 4 (background gradients) — landed, not separately stress-tested against the video

The two low-opacity radial gradients were added to `.login-split`'s base rule. Visually
present in every screenshot taken this session (dark corners have a very faint navy/gold
tint) without obviously competing with the video preview, but no dedicated frame-by-frame
check was done against the autoplaying video specifically. If it ever reads as muddying
the preview, the spec itself flags this as skippable — just remove the two
`radial-gradient(...)` layers from `.login-split`'s `background` and fall back to the
flat `#0a0a0f`.
