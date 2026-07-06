# Follow-ups — Spec 34: Login Always-Dark + Logo Cleanup & Theme-Swap

**Origin**: `.claude/specs/34_login-always-dark.md`
**Plan**: `.claude/plans/34-login-always-dark.md`
**Status**: Login block (plan Items 1–3 / spec Items 1, 2a, 2b) implemented and
verified live, both themes, both breakpoints. Watermark resize (plan Item 6 /
spec Item 5) implemented. **Logo assets (plan Item 4 / spec Item 3) — BLOCKED
AGAIN as of 2026-07-06/07, superseding the 2026-07-05 "RESOLVED" note below** —
the drop-in PNGs failed inspection (see §1 update) and the actual master source
(now in the repo) turns out to be unusable by automated color-based keying (see
§1b). **Header theme-swap (plan Item 5 / spec Item 4) — still blocked**, depends
on Item 3. Pre-existing lint gap (§4) still open.
**Date noted**: 2026-07-05, corrected 2026-07-07.

---

## 1. RESOLVED (2026-07-05) — Logo assets placed via drop-in path

**Resolution**: The two cleaned marks were generated during the design-review
(in that review's workspace, from the opaque white-background master
`walletmantralogo.png`, 1456×840 — the same raster the spec references), delivered
as downloadable files, and the **user has now placed both directly into
`frontend/react/public/`**:
- `wallet-mantra-logo.png` — **dark-surface mark** (variant B: background
  flood-keyed to true transparency + subtle light outline so it separates on
  dark). Overwrites the old muddy file.
- `wallet-mantra-logo-light.png` — **light-header mark** (variant A: clean
  transparent, untouched true navy).

This satisfies spec Item 3 through the spec's **drop-in alternative** ("pre-generated
assets can be dropped in directly"), rather than the reproducible script path.

**Why the earlier "source doesn't exist" conclusion happened (for the record, not a
re-litigation)**: a repo-only search correctly found no `walletmantralogo.png`,
`scripts/process-logo.py`, `brand/` dir, or pre-generated PNGs — because those lived
in the *design-review workspace*, outside the repo, not because no master existed.
The master and both outputs did exist there; placing the outputs in `public/`
closes the gap.

**Update 2026-07-07**: both now exist in the repo — `scripts/process-logo.py`
(written this session, pure PIL + numpy, no scipy) and
`frontend/react/brand/wallet-mantra-source.png` (the actual master, provided by
the user). Running the script against the real master does **not** produce a
clean result — see §1b for the full investigation and why.

### 1a. NOT applied — header theme-swap deliberately held back (spec Item 4)

The `Header.tsx` two-line conditional-`src` change (below) was drafted but
**intentionally not applied**, because wiring it would have shipped a visibly
broken light-mode header — see §1b for why. Do not apply this until a genuinely
clean `wallet-mantra-logo-light.png` exists:

```tsx
<img
  src={theme === "dark" ? "/wallet-mantra-logo.png" : "/wallet-mantra-logo-light.png"}
  alt=""
  aria-hidden="true"
  className="h-8 w-8 flex-shrink-0 object-contain"
/>
```

### 1b. Root cause — the drop-in assets and even the real master aren't cleanly keyable

**What was checked**: the two PNGs placed in `public/` on 2026-07-05 (the ones
§1's original note called "resolved") were inspected pixel-by-pixel this
session, not just eyeballed:
- Composited both at their actual render size (32px, matching header `h-8 w-8`
  and the post-Item-5 watermark) against solid white and solid dark backgrounds.
  Both show a visible grey/dark halo — on white it reads as a dirty smudge ring,
  failing the spec's own "reads clearly on a white header" bar for variant A.
- Extracted the alpha channel of `wallet-mantra-logo-light.png` directly: it is
  **not a silhouette cutout of the mark at all** — it's the full square canvas
  with only the four corners rounded off (a "squircle"), plus one small
  deliberate notch. Every gap *between* the letterforms, between the wallet
  icon and the arrow, etc. is still fully opaque. So the background was never
  actually removed from around the mark — only the canvas corners were.

**Once the actual master (`walletmantralogo.png`, via the user, 1456×840,
confirmed genuinely opaque/white-cornered) was obtained and placed at
`frontend/react/brand/wallet-mantra-source.png`**: viewing it directly showed
the reason nothing can key cleanly — **the master itself has a soft dark
glow/vignette baked into the pixels around the mark**, fading gradually into
the white canvas over a wide radius. This is real gradient image content, not
a keying artifact, and it has no hard edge for any threshold to find.

**Three separate automated keying approaches were tried against the real
master and all three failed for related reasons** (don't re-attempt these
without a different master):
1. **Border-seeded luminance flood-fill** (`scripts/process-logo.py`'s
   documented approach, threshold 235) — only removes the pure-white area far
   from the mark; the entire glow blob is darker than the threshold, so it
   stays opaque. Re-ran the actual script against the real master and
   confirmed via the output alpha channel: same squircle-blob shape as the
   drop-in assets.
2. **HSV saturation threshold** — hypothesis was that the achromatic glow
   (low saturation) could be separated from the colored blue/gold mark (higher
   saturation). Disproven: HSV saturation is numerically unstable for
   near-black pixels (`S = (max-min)/max` blows up toward 1.0 as `max→0` even
   for visually-grey pixels), so the dark glow reads as *higher* saturation
   than parts of the mark — the mask came out inverted from what was needed.
3. **Raw chroma** (`max(R,G,B) - min(R,G,B)`, avoids the near-black division
   instability) — better than saturation but still fundamentally the same
   problem: the glow-to-mark transition is gradual and the metallic
   shading *inside* the mark itself dips to low-chroma (near-grey highlight/
   shadow areas from the brushed-metal render style), so no chroma threshold
   cleanly separates "glow" from "mark" — result was still a rough blob with
   a couple of interior gaps punched out, not a clean silhouette.
4. **ML-based background removal (`rembg`)** — the correct tool for exactly
   this "soft/glowing subject" case, but couldn't get it installed in this
   environment: `rembg → pymatting → numba → llvmlite` fails to build from
   source for Python 3.13 on this machine (`uv run --with rembg`, `uv pip
   install` into `.venv`, and system-Python `pip install --user` were all
   tried; `llvmlite` 0.48.0 has no prebuilt wheel for this Python/platform
   combo and the source build fails). Not resolved — a machine/Python version
   with a working numba/llvmlite (or a hosted rembg API) would be needed to
   actually test this path.

**What would actually fix this**: either (a) get a re-export of the master
*without* the glow/vignette effect — a genuinely flat white background behind
just the mark, which is what the spec originally assumed existed, or (b)
manual/semi-automated masking in an image editor (Photoshop/GIMP/Figma) by a
human tracing the silhouette, since automated color-space thresholding is not
viable on this specific source no matter how it's tuned.

**Do not re-attempt** border-flood-fill / saturation / chroma threshold tuning
on this same master expecting a different result — all three were tested
directly against it this session and the failure mode is structural (a
continuous gradient with no separable edge), not a parameter-tuning problem.

---

## 2. Watermark resize — still just a size change, asset itself still unfixed

Plan Item 6 / spec Item 5 (`.kpi-watermark-img` 54px → 32px) shipped as a pure CSS
change, independent of which PNG loads. Per §1b, the underlying asset is still
not a clean cutout, so this renders the same not-actually-fixed mark at 32px
instead of 54px — smaller, not cleaner. The `.kpi-watermark-img` comment in
`index.css` correctly says the rework is still blocked and points here — leave
it as-is; it is not stale.

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
