# Follow-ups — Spec 31: Brand Logo + Fixed Tab Celebration

**Origin**: `.claude/specs/31_brand-logo-and-celebration.md`
**Plan**: `.claude/plans/31-brand-logo-and-celebration.md`
**Status**: Plan fully implemented (3/3 items) and visually verified end-to-end in a
real Playwright/Chromium browser session on 2026-07-02 (see spec's
"Post-implementation addendum" section for what changed after the user's
first-round screenshot feedback). One item below is now resolved and kept
only as a record of what happened; two remain genuinely open.
**Date noted**: 2026-07-02 (updated same day after live verification)

---

## 1. RESOLVED — Header halo / card watermark legibility (user-reported via screenshots)

**What was wrong**: the user reported the header logo showed a visible dark
square halo in light mode, and the KPI card watermark wasn't clearly legible.
Root cause, confirmed via pixel sampling of `public/wallet-mantra-logo.png`:
the PNG had an **opaque** dark rounded-square background baked into the RGB
data (alpha=255 across the fill, alpha=0 only at the four true corners
outside the rounded rect) — it was an app-icon-style asset, not a transparent
logomark. No CSS blend-mode trick (`overlay`, `multiply`, etc.) can cleanly
remove an opaque backing image; that's why the original spec's "Option A —
`mix-blend-mode: overlay`" approach produced a muddy, semi-opaque sticker
instead of a subtle watermark.

**Fix applied**: chroma-keyed the source PNG in place using a luminance
threshold (transparent below ~42, opaque above ~78, linear ramp between),
removing the background fill while preserving the navy-to-gold artwork.
Removed `mix-blend-mode: overlay` from `.kpi-watermark-img` in `index.css`
(no longer needed — true alpha transparency + `opacity: 0.6` is sufficient).
No component code changes were needed beyond that CSS tweak — `Header.tsx`
and `LoginPage.tsx` (which shares the same asset, though outside this spec's
scope) both benefit automatically since the fix lives in the shared PNG.

**Verified live** (Playwright/Chromium, both themes):
- Header logo: clean in dark mode and light mode, no halo — confirmed via
  screenshot comparison.
- KPI watermark: legible on all three Overview cards (green Remaining,
  purple Income, orange Commitments Paid) and all three Fixed cards (amber
  Fixed total/paid/left), in both dark and light mode.
- Celebration: marked all 19 fixed items paid on a live account → 🎉 burst
  fired once, screenshot caught it mid-animation. Reloaded the page at 100%
  → confirmed via both a screenshot and a DOM check (`.fixed-cel-overlay`
  element count === 0) that it does **not** replay.

**Action needed**: none — closed. Kept here only so a future "why does the
logo look different from the original spec's mix-blend-mode decision" question
traces back to this record instead of looking like an undocumented drift.

---

## 2. Hooks-guard correction to Item 3's edge-trigger effect — now confirmed working live

**What changed vs. the plan doc**: the plan's Item 3a pseudocode placed the
edge-trigger `useEffect` before `FixedTab`'s `if (loading) return
<FixedTabSkeleton />;` early return (required — otherwise it's a Rules-of-Hooks
violation), but as originally drafted it had no guard against running while
`fixedExps` is still `[]` on first mount. Tracing it through: the initial
mount effect run (before the first fetch resolves) would have computed
`curPct = 0`, set `prevPctRef.current = 0`, and the *second* run (once real
data loads) would see `0 < 100 && curPct === 100` and incorrectly fire the
celebration on every page load of an already-100%-paid month.

**Fix applied** (`FixedTab.tsx`): added `if (loading) return;` as the first
line inside the effect, and added `loading` to the effect's dependency array
(`[fixedExps, loading]`). The effect is now a no-op until the initial fetch
completes, so `prevPctRef.current` only ever gets its first real value from
actual data.

**Now confirmed, not just reasoned through**: live-browser test (see item 1
above) exercised exactly this path — mark last item paid → burst fires once;
reload at 100% → no replay, confirmed via DOM query. Closed.

**Known remaining edge case, intentionally not fixed**: `prevPctRef` is never
reset on month change (`selMonth` isn't in the effect's dependency array).
Switching from a partially-paid month to a *different, already-100%-paid*
historical month could fire the celebration on month switch rather than on
"marking the last item paid." Neither the spec nor the plan addressed month
switching, and adding a reset would be scope creep beyond the locked
decisions — this was not exercised in the live verification pass (only
same-month toggle-then-reload was tested). Flagging only so a future report
of "the confetti fired when I just switched months" traces back here
(`FixedTab.tsx`, the edge-trigger `useEffect`) instead of looking like a
fresh bug.

**Action needed**: none required now. Worth a quick manual check
(switch from an in-progress month to a fully-paid one) if it's ever reported
as unexpected behavior; the fix would be adding `selMonth` to the effect's
dependency array and resetting `prevPctRef.current = null` when it changes.

---

## 3. `npm run lint` cannot run — pre-existing environment gap, not introduced by this change

`frontend/react/package.json` has a `lint` script (`eslint . --ext ts,tsx
--report-unused-disable-directives --max-warnings 0`) but `eslint` is not
present in `node_modules/.bin` and isn't listed as an installed dependency in
this checkout. This predates Spec 31's edits. `npm run build` (which runs
`tsc` ahead of `vite build`) passed with zero TypeScript errors both times
(initial implementation and the post-screenshot-feedback follow-up), so
type-level correctness is confirmed; the zero-ESLint-warning policy from
`CLAUDE.md` still could not be checked.

**Action needed**: `cd frontend/react && npm install` (or check whether
`eslint` was recently removed from `package.json`'s devDependencies) to
restore the lint script, then re-run `npm run lint` against this branch.

---

## Environment note for whoever re-reads this

Live browser verification for this spec required installing Playwright's
Chromium build (`npx playwright install chromium`, ~280MB download) since
none was cached in this environment and no project-level browser-testing
skill existed yet. It was installed as an ephemeral, unsaved dependency
(`npm install --no-save playwright`) purely to drive the verification
session — not added to `package.json`/`package-lock.json`. One side effect
worth knowing about: `frontend/react/node_modules/.package-lock.json` is (for
historical reasons) a **tracked** file despite living under a gitignored
`node_modules/` path — any local `npm install` will dirty it, and it should
be reverted (`git checkout -- frontend/react/node_modules/.package-lock.json`)
before committing unrelated work, exactly as was done here. Consider
`/run-skill-generator` in a future session to capture this app's launch +
browser-verification steps (login credentials, rate-limit gotcha below) as a
reusable project skill.

**Rate-limit gotcha hit during this verification**: `POST /auth/login` is
limited to `10/hour` per `backend/main.py:410` (`@limiter.limit("10/hour")`).
Repeated test logins (via curl + multiple Playwright runs) tripped this
mid-session, causing a confusing "Fixed tab never appears" failure that was
actually a silent 429 on the login POST with the login page still showing its
own "Wallet Mantra" wordmark (easy to mistake for a successfully-loaded
dashboard when only checking for that text). The limiter uses in-memory
storage (no `storage_uri` configured), so restarting the backend process
resets it — that's the workaround used here. Worth remembering next time:
batch interactions into as few login calls as possible.
