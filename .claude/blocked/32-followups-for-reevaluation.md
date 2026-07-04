# Follow-ups — Spec 32: Login Page Polish

**Origin**: `.claude/specs/32_login-page-polish.md`
**Plan**: `.claude/plans/32-login-page-polish.md`
**Status**: Plan fully implemented (7/7 items) and verified live via Playwright/Chromium
against the Vite dev server (desktop 1280×900, mobile 390×844, register-form
regression check), plus a clean `npm run build`. Two bugs below were found during
that verification and fixed in the same pass — kept as a record, not open items.
One item remains genuinely open (pre-existing, not introduced by this spec).
**Date noted**: 2026-07-04

---

## 1. RESOLVED — `.login-field svg` descendant selector clobbered the new icons

**What was wrong**: `index.css:545` had `.login-field svg { position: absolute; left:
14px; ...; pointer-events: none; }`, written when `.login-field` only ever contained
one icon (the leading `Mail`/`Lock`). Item 3 (email validation icon) and Item 4
(password show/hide toggle) both add a *second* `<svg>` inside the same
`.login-field` wrapper — the descendant selector matched those too, so:

- The email validation icon (`CheckCircle`/`XCircle`) got silently forced to
  `left: 14px` (the same spot as the `Mail` icon) and `pointer-events: none`,
  making it invisible/unclickable instead of appearing at `right-3` as intended.
- The password show/hide toggle button collapsed to a **0×0 box** — its only child
  (the `Eye`/`EyeOff` svg) got pulled out of normal flow by the same rule, so the
  wrapping `<button>` had no in-flow content left to size itself against. The icon
  then rendered outside the input's right border (visually floating in the margin),
  and the button was unclickable (confirmed via Playwright: `boundingBox()` returned
  `{width: 0, height: 0}`, and `.click()` timed out with "element is not visible").

Neither the spec nor the plan anticipated this — both assumed `.login-field` CSS
was scoped narrowly enough already; it wasn't, because it was written for a
one-icon-per-field world.

**Fix applied** (`frontend/react/src/index.css`): narrowed the selector from
`.login-field svg` to `.login-field > svg:first-child` (and the matching
`:focus-within` rule). This targets only the always-first, always-leading icon
(`Mail`/`Lock`) and leaves any later sibling icon (validation checkmark, or an
icon nested inside a toggle `<button>`) to be positioned by its own Tailwind
classes instead.

**Verified live**: bounding boxes for both the email check/X icon and the password
toggle button now report real, correctly-positioned sizes (`{x: ~1016, width: 14,
height: 14}`, inside the field's right edge), and clicking the toggle button
successfully flips the input's `type` between `password`/`text`. Screenshots
confirm both icons sit cleanly inside their fields.

**Action needed**: none — closed. Worth remembering for any *future* field that
adds a third icon to `.login-field`: the `:first-child` selector only protects the
leading icon; a third icon would need its own explicit Tailwind positioning
(as Items 3 and 4's icons already have) rather than relying on this CSS block.

---

## 2. RESOLVED — `/privacy` silently served the SPA shell, not the static page

**What was wrong**: the spec and plan both assumed an extensionless `href="/privacy"`
would resolve to `public/privacy.html` "automatically... with no backend change, no
new route." That's true only if something rewrites `/privacy` → `/privacy.html`.
Neither Vite's dev server nor the production Nginx config do that:

- `nginx/react.conf` has `try_files $uri $uri/ /index.html;` for React Router
  support — `/privacy` isn't a real `$uri` (the real file is `/privacy.html`), so
  it falls through to `/index.html`, i.e. the React app shell.
- Vite's dev server behaves the same way for the same reason (SPA fallback).

Both returned HTTP 200, which made the bug easy to miss without actually reading
the response body — `curl -o /dev/null -w '%{http_code}'` for `/privacy` looked
identical to `/privacy.html`. Only inspecting the HTML (or loading it in a real
page and checking for the expected `<h1>`) revealed that `/privacy` was rendering
`<title>Wallet Mantra</title>` (the SPA) instead of the privacy page.

**Fix applied**: changed both link targets (`LoginPage.tsx` footer,
`ProfileDropdown.tsx` menu item) from `/privacy` to `/privacy.html`, which is a
real static file and resolves correctly under both Vite dev and the Nginx
`try_files` rule in every environment, with no server config changes needed.

**Verified live**: navigating to the resolved `href` now loads the actual privacy
page (`<h1>Wallet Mantra — Privacy Notice</h1>`, all 8 sections rendered, dark
theme matching the app).

**Action needed**: none required. If a clean extensionless `/privacy` URL is
wanted later (e.g. for a nicer look in the address bar or app-store review), add
an explicit Nginx rewrite (`location = /privacy { rewrite ^ /privacy.html
last; }` in `nginx/react.conf`) and a matching Vite dev `server.proxy`/middleware
rule — deliberately not done here since it touches shared server config beyond
this spec's frontend-only scope.

---

## 3. OPEN (pre-existing, not introduced here) — `npm run lint` cannot run

Same gap as recorded in `.claude/blocked/31-followups-for-reevaluation.md` item 3:
`eslint` is not present in `frontend/react/node_modules/.bin` despite the `lint`
script existing in `package.json`. Confirmed still true on this branch —
`npm run lint` fails with `sh: eslint: command not found`, and `node_modules/.bin`
has no `eslint` entry. `npm run build` (which runs `tsc` ahead of `vite build`)
passed with zero TypeScript errors, so type-level correctness is confirmed; the
CLAUDE.md zero-ESLint-warning policy still could not be checked for this spec's
changes.

**Action needed**: same as before — `cd frontend/react && npm install` (or check
whether `eslint` was dropped from `devDependencies`), then re-run `npm run lint`
against this branch's changes specifically (`LoginPage.tsx`, `ProfileDropdown.tsx`,
`index.css`, `public/privacy.html`).

---

## Environment note for whoever re-reads this

Verification used the same ephemeral Playwright setup noted in spec 31's
follow-ups doc — Chromium was already cached at `~/Library/Caches/ms-playwright`
from that prior session, so no reinstall was needed this time. `chromium-cli`
(the project's normal browser-driving tool) was not available in this environment;
fell back to a raw Playwright script per the `/run` skill's documented fallback
path. No new dependencies were added to `package.json`/`package-lock.json`.

One mechanical gotcha hit this session: the local shell's `timeout` command
doesn't exist on this macOS environment (`/bin/bash: line X: timeout: command not
found`) — polling loops (`for i in $(seq...); do curl ...; sleep 1; done`) were
used instead of `timeout ... curl`. Also, port 5173 was already occupied by a
stale process from an earlier session, so Vite auto-selected 5174 — worth checking
for stray `vite`/`node` processes if a future session hits the same port bump.
