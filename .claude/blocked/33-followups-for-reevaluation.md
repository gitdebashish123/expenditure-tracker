# Follow-ups — Spec 33: Login Visual Rebalance, Gold Brand Token, Fixed-tab KPI Differentiation

**Origin**: `.claude/specs/33_login-visual-and-fixed-kpi-differentiation.md`
**Plan**: `.claude/plans/33-login-visual-and-fixed-kpi-differentiation.md`
**Status**: All 6 plan items implemented, in execution order (1 → 6 → 5 → 4 → 3 → 2).
`npm run build` passes clean (zero TypeScript errors). **Live visual verification
was not performed this session** — the dev server was not started (the tool call
to launch it was rejected mid-session), so nothing below has been confirmed in an
actual browser. Treat this as code-complete but visually unverified.
**Date noted**: 2026-07-04

---

## 1. OPEN — No live browser verification performed

**What's missing**: Per this project's own convention ("For UI or frontend
changes, start the dev server and use the feature in a browser before reporting
the task as complete" — root `CLAUDE.md`), this change should be driven live at
both <900px and ≥900px viewport widths, in both dark and light theme, before
being considered fully done. That didn't happen this session.

**Specific things to check first**, in rough risk order:

- **Item 2 (left-panel recompose)** is the highest-risk item — it's a full JSX
  restructure plus CSS removal of `.login-visual-top`/`.login-visual-bottom`/
  `.login-quote-zone`. Confirm at ≥900px that:
  - the brand row (logo + wordmark) renders inline without overlap or awkward
    wrapping,
  - the AI badge (`Your AI money companion`) doesn't collide with the brand row
    above it or the value-prop copy below it (it now has no explicit margin —
    relies on the parent `.login-visual`'s `gap: 20px`, which may look uneven
    since the badge is short and inline-flex `align-self: flex-start` was added
    inline rather than via a class — verify this doesn't look like a stray gap),
  - the preview card holds a clean 16:10 frame and the video doesn't get
    letterboxed oddly (it's `object-fit: cover`, so should crop instead of
    letterbox, but confirm the source video's actual aspect ratio against 16:10),
  - the quote crossfade at the bottom doesn't clip or overflow now that it's
    `margin-top: auto` in a flex column instead of absolutely positioned.
- **Item 3 border-specificity fix**: confirm in devtools that
  `.login-split .login-field input` (index.css, added at specificity `(0,2,1)`)
  actually beats the global `input:not(...):not(...) { border-color: var(--border-lg) !important }`
  rule now — this was a targeted fix for a bug that was silently broken before
  this spec (see plan Item 3 root-cause section), so it's worth explicit
  confirmation rather than assuming the specificity math holds in the real
  cascade.
- **Item 4/CTA hover**: confirm the `.login-cta-gold:hover:not(:disabled)`
  box-shadow glow reads as "subtle" per the spec's ask, not garish — this was
  eyeballed from the token values, not tuned against a live render.
- **Mobile (<900px)**: confirm `.login-visual` is still fully hidden and the
  form fills the screen exactly as before — nothing in Items 2/3 should touch
  mobile, but the `.login-form-card` media-query gating and the JSX
  restructuring inside `.login-visual` both deserve a quick sanity check since
  the whole subtree changed.
- **Light mode**: confirm `--gold`/`--gold-navy`/`--gold-border` light overrides
  (Item 1) actually look intentional on the login CTA and form card border, not
  washed out — this spec explicitly deprioritized light-mode polish ("dark mode
  is the primary surface... don't optimize it here") but "don't break" is still
  in scope.
- **Fixed tab (Item 6)**: confirm `.kpi-card-fixed-left` (`#2a2a3d` flat slate)
  is visually distinct from both the page background (`--bg: #0a0a0f`) and the
  green/amber gradient cards next to it, on a real device — the plan reasoned
  through contrast on paper but didn't render it.

**Action needed**: run `npm run dev` (or `docker compose up` for the full stack)
and manually click through login (both modes), then the Fixed tab, at both
viewport breakpoints and both themes. Take screenshots if using Playwright —
the prior spec-32 session (`.claude/blocked/32-followups-for-reevaluation.md`)
has a working ephemeral-Playwright pattern (Chromium already cached at
`~/Library/Caches/ms-playwright`, confirmed still present this session) if
`chromium-cli` isn't available.

---

## 2. OPEN (pre-existing, not introduced here) — `npm run lint` cannot run

Same gap recorded in `.claude/blocked/31-followups-for-reevaluation.md` item 3
and `.claude/blocked/32-followups-for-reevaluation.md` item 3. Confirmed still
true on this branch: `npm run lint` fails with `sh: eslint: command not found`,
and `eslint`/`eslint-config-*` are absent from `frontend/react/node_modules/.bin`.
`npm run build` (which runs `tsc` ahead of `vite build`) passed with zero
TypeScript errors, so type-level correctness is confirmed; the CLAUDE.md
zero-ESLint-warning policy still could not be checked for this spec's changes —
this matters more than usual for Item 5, which removes the `Shield`/`UserCheck`
lucide-react imports and would be exactly the kind of change ESLint's
`no-unused-vars` rule exists to catch.

**Action needed**: same as prior two occurrences — `cd frontend/react && npm
install` (or check whether `eslint` was dropped from `devDependencies` in a
lockfile update), then re-run `npm run lint` specifically against
`LoginPage.tsx`, `DashboardPage.tsx`, and `index.css`.

---

## 3. JUDGMENT CALL made without mockup confirmation — inline logo size

**Context**: Spec Item 2's CSS snippet defines `.login-brand-row` (flex, `gap:
12px`) but never specifies a size for the logo inside it. The pre-existing
`.login-logo-mark` class is `88×88px` with a float+glow animation, sized for a
large centered hero position (its old context). Placed inline next to a
`text-xl` heading in a `gap: 12px` row, 88px would almost certainly look
oversized and unbalanced.

**What was done**: sized it down via an inline `style={{ width: 56, height: 56
}}` override on the `<img className="login-logo-mark" ...>` element in
`LoginPage.tsx`, keeping the `.login-logo-mark` class (and thus its
float/glow keyframe animations) intact. 56px was picked as a reasonable
visual guess relative to the `text-xl` wordmark next to it — **not** validated
against the three approved interactive mockups referenced in the spec's header
("login mobile card, login desktop split, Fixed-tab KPI cards").

**Action needed**: re-open the approved desktop-split mockup (referenced but not
embedded in the spec file) and compare the actual logo:wordmark size ratio.
Adjust the inline `56` px value (or promote it to a proper CSS rule, e.g. a
`.login-logo-mark--inline` modifier class, if it turns out other call sites
need the same sizing) if it doesn't match.

---

## Environment note for whoever re-reads this

Confirmed present this session (same as spec-32's follow-up note): Chromium
cached at `~/Library/Caches/ms-playwright` (`chromium-1228`), Playwright JS
package present in `frontend/react/node_modules/.bin`. `chromium-cli` was not
checked for availability this session since no browser session was actually
started — don't assume it's there without checking again.

The dev-server launch was attempted once via a backgrounded `npm run dev &`
shell command and was rejected by the user mid-session (tool-use denial, not a
technical failure) — re-attempt normally next session; there's no known reason
the dev server itself wouldn't start cleanly.
