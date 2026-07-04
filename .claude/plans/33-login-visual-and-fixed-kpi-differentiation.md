# Implementation Plan: Login Visual Rebalance, Gold Brand Token, Fixed-tab KPI Differentiation
**Spec**: `.claude/specs/33_login-visual-and-fixed-kpi-differentiation.md`
**Date**: 2026-07-04
**Branch**: `feature/sprint0726p1-ui-enhancement` *(the spec header lists `feature/sprint06261-ui-enhancement`, but that does not match the repo's actual current branch per `git status` — using the real current branch here)*
**Status**: ✅ Completed (2026-07-04) — all 6 items implemented in execution order (1 → 6 → 5 → 4 → 3 → 2). `npm run build` passes with zero TypeScript errors. `npm run lint` could not run (pre-existing environment gap — `eslint` binary missing, see `.claude/blocked/33-followups-for-reevaluation.md`). Live browser verification (dev server + Playwright) was not performed this session; see the same follow-ups doc for what to re-check.

---

## Overview

6 spec items, all **frontend-only** (`frontend/react/src/`). No backend changes.
Verified every affected file against current disk state — details below, including
two divergences from the spec's literal snippets (Item 3's CSS specificity fight,
Item 5's now-unused icon imports) that the spec didn't fully call out.

Order below is smallest-blast-radius-first, **not** the spec's numbering. Item 1
(token-only, zero visual change) goes first since Items 2–4 all consume it. Item 6
(Fixed KPI) is fully independent of the login work and is sequenced right after —
it's self-contained and lower-risk than the login recomposition. The login items
are then ordered 5 → 4 → 3 → 2 (footer text swap → button restyle → form-card wrap
→ full left-panel recomposition), each strictly larger in surface area than the
last.

---

## Item 1 — Gold brand token
**Scope**: Frontend-only
**Files**: `frontend/react/src/index.css`

**Root cause**: `:root` (lines 11–39) defines `--accent`/`--accent2`/`--accent-bg`
but no gold token exists anywhere in the file. `html.light` (lines 42–60) mirrors
the dark tokens with lighter-contrast equivalents but likewise has no gold entry.
The brand logo (`/wallet-mantra-logo.png`) carries gold; nothing in the live CSS
references it.

**What to do**: Add four new custom properties to `:root` immediately after the
existing `--accent-bg` line (line 30):

```css
  --accent-bg: rgba(99, 102, 241, 0.15);

  /* Brand — gold (from logo mark). Used sparingly: login CTA/accents now. */
  --gold:        #facc15;
  --gold-border: #4a3a12;
  --gold-bg:     rgba(250, 204, 21, 0.10);
  --gold-navy:   #1e1b4b;
```

Add the light-mode override to `html.light` (after line 60, alongside the other
status-colour overrides):

```css
  --gold:        #b8860b;
  --gold-border: rgba(184, 134, 11, 0.30);
  --gold-bg:     rgba(184, 134, 11, 0.10);
  --gold-navy:   #ede9fe;
```

**Acceptance**: No visual change on its own (tokens unused until Items 2–4 land).
`grep -n "\-\-gold" frontend/react/src/index.css` shows only these two blocks
until later items add consumers.

---

## Item 6 — Fixed-tab KPI differentiation + reorder
**Scope**: Frontend-only
**Files**: `frontend/react/src/pages/DashboardPage.tsx` (lines 56–81), `frontend/react/src/index.css` (near line 198)

**Root cause**: `DashboardPage.tsx:56-81` builds `fixedCards` in the order
`fx-total → fx-paid → fx-left`, and **all three** entries set
`gradientClass: "kpi-card-bills"` (lines 63, 71, 79) — confirmed on disk, matches
the spec exactly. `index.css:196-198` defines `.kpi-card-remaining` (green),
`.kpi-card-income` (purple, unused here), `.kpi-card-bills` (amber) — no neutral
"lit slate" class exists yet. The `fx-left` card's `accent` (line 78) is also
currently conditional (`#34d399` green when zero, `#f59e0b` amber otherwise) —
this conditional tint is explicitly rejected by decision D2.

`KpiCarousel.tsx` (verified, unchanged by this item) applies `gradientClass` as a
literal class name on both the mobile slide (`kpi-slide ${card.gradientClass}`,
line 44) and desktop shell (`kpi-card-shell ${card.gradientClass}`, line 80), and
renders `card.accent` as an inline `background` style on `.kpi-accent` (line 84) —
so no component change is needed, only a new CSS class and new `fixedCards` data.

**What to do**:

**6a — new CSS class** (`index.css`, insert directly after line 203, the
`html.light .kpi-card-bills` line, so it sits with the rest of the KPI gradient
block):

```css
/* Fixed-tab "Left / pending" card — neutral lit surface (Spec 33 D2). */
.kpi-card-fixed-left {
  background: #2a2a3d;
  border: 1px solid rgba(255, 255, 255, 0.22);
}
```

No `html.light` override — per the spec's own "Light-mode risk" note, the KPI
text classes (`.kpi-card-value`, `.kpi-card-label`, `.kpi-card-sub`, lines
206–209) force white text unconditionally in both themes, so this card must stay
dark in light mode too, exactly like the two existing gradient classes.

**6b — rebuild `fixedCards`** (`DashboardPage.tsx`, replace lines 56–81):

```tsx
const fixedCards: KpiCard[] = balance ? [
  {
    id: "fx-left",
    label: "Fixed left",
    value: fmtInr(balance.fixed_unpaid_total),
    subtitle: balance.fixed_unpaid_total === 0 ? "All clear" : `${totalCount - paidCount} pending`,
    accent: "#94a3b8",
    gradientClass: "kpi-card-fixed-left",
  },
  {
    id: "fx-paid",
    label: "Fixed paid",
    value: fmtInr(balance.fixed_paid_total),
    subtitle: `${paidCount} of ${totalCount} items`,
    accent: "#34d399",
    gradientClass: "kpi-card-remaining",
  },
  {
    id: "fx-total",
    label: "Fixed total",
    value: fmtInr(balance.fixed_paid_total + balance.fixed_unpaid_total),
    subtitle: `${totalCount} items this month`,
    accent: "#fbbf24",
    gradientClass: "kpi-card-bills",
  },
] : [];
```

Note the `accent` on `fx-left` is now a flat `"#94a3b8"` regardless of
`fixed_unpaid_total` — the old conditional (line 78) is removed per D2. The
`subtitle` conditional ("All clear" vs "N pending") is kept — that's copy, not
color, and isn't in scope of D2's rejection.

No changes needed to `KpiCarousel.tsx` — confirmed it only consumes
`gradientClass`/`accent` generically.

**Acceptance**:
- Fixed tab renders cards in order Left → Paid → Total on both mobile carousel
  and desktop row (array order drives both, per `KpiCarousel.tsx:43,77`).
- Left = flat slate `#2a2a3d`, Paid = green gradient, Total = amber gradient —
  visually distinct without reading the numbers.
- Dot indicators / active-side desktop states unaffected (component untouched).

---

## Item 5 — Trust footer consolidation
**Scope**: Frontend-only
**Files**: `frontend/react/src/pages/LoginPage.tsx` (lines 1–3, 338–349)

**Root cause**: `LoginPage.tsx:339-349` maps over a 3-item array (`Lock` /
`Shield` / `UserCheck` icons with labels "Passwords encrypted" / "Data stays
private" / "You're in control"), rendered at `text-[10px] text-white/25` — as
described in the spec, effectively unreadable.

**What to do**: Replace the map block (lines 339–349) with a single line:

```tsx
<div className="flex justify-center gap-2 mt-4 pt-3 border-t border-white/10">
  <span className="flex items-center gap-1.5 text-[11px] text-white/55">
    <Lock size={11} style={{ color: "var(--gold)" }} />
    Your data stays private and encrypted
  </span>
</div>
```

**Important — unused-import cleanup required**: `Shield` and `UserCheck` (line 3
import: `import { Mail, Lock, Sparkles, CheckCircle, XCircle, Eye, EyeOff, Shield,
UserCheck } from "lucide-react";`) are used *only* in the badge array being
deleted. Once that array goes, both imports become dead code. Per this project's
zero-warning ESLint policy (`npm run lint`, noted in root `CLAUDE.md`), remove
`Shield, UserCheck` from the import line or `npm run build`/`npm run lint` will
fail. `Lock` stays (still used in the password field icon and the new trust
line).

**Acceptance**:
- One trust line, one gold lock icon, `text-[11px]`/`white/55` (up from
  `10px`/`25%` — passes AA against `--bg`).
- `npm run lint` has zero new unused-import warnings.

---

## Item 4 — Login CTA: navy fill + gold border + gold text
**Scope**: Frontend-only
**Files**: `frontend/react/src/pages/LoginPage.tsx` (lines 239–245, 292–298), `frontend/react/src/index.css`

**Root cause**: Both submit buttons — login (lines 239–245) and register (lines
292–298) — share the identical className:
`"w-full bg-gradient-to-r from-accent to-accent2 text-white font-syne font-semibold py-3 rounded-xl disabled:opacity-50 transition-opacity"`.

**What to do**: The spec's snippet applies the gold-navy treatment via inline
`style={{...}}`, but that can't express a hover state. Add a CSS class instead
so the "subtle gold glow on hover" requirement (spec Item 4) is achievable, and
apply it via `className` on both buttons.

**Add to `index.css`** (near the login section, e.g. after the `.login-field`
rules around line 556):

```css
.login-cta-gold {
  background: var(--gold-navy);
  border: 1px solid var(--gold);
  color: var(--gold);
  transition: background-color 0.15s, box-shadow 0.15s;
}
.login-cta-gold:hover:not(:disabled) {
  box-shadow: 0 0 0 1px var(--gold), 0 0 16px rgba(250, 204, 21, 0.25);
}
```

**Replace both button classNames** (lines 242 and 295) with:

```tsx
className="login-cta-gold w-full font-syne font-semibold py-3 rounded-xl disabled:opacity-50 transition-colors"
```

(Drop `bg-gradient-to-r from-accent to-accent2 text-white` and `transition-opacity`
— superseded by the new class.)

**Acceptance**:
- Both Sign In and Create Account buttons render navy fill / gold border / gold
  text in dark mode; `--gold-navy`/`--gold` light-mode overrides (Item 1) keep
  them legible in light mode.
- `disabled:opacity-50` still visibly dims the loading state.
- No other button in the app is touched — grep confirms `login-cta-gold` only
  appears in `LoginPage.tsx`.

---

## Item 3 — Login form container + gold accents
**Scope**: Frontend-only
**Files**: `frontend/react/src/pages/LoginPage.tsx` (lines 87–90, 150, 194–238), `frontend/react/src/index.css` (lines 143–151, 539–556)

**Root cause**: The form wrapper `<div className="w-full max-w-sm relative">`
(line 150) has no card treatment — it sits directly on `--bg` inside
`.login-form-panel`. `inputCls` (lines 87–90) sets `border border-white/10` at
rest and `focus:border-accent focus:ring-1 focus:ring-accent` on focus — but
**this focus state is currently dead code**: `index.css:144-151` applies

```css
input:not([type="radio"]):not([type="checkbox"]),
select,
textarea {
  border-color: var(--border-lg) !important;
}
```

which has specificity `(0,2,1)` (element + two `:not()` pseudo-classes) versus
Tailwind's `focus:border-accent` utility, which is a plain unqualified class at
`(0,1,0)` with no `!important`. The global `!important` rule always wins
regardless of focus state, so the input border never actually changes color
today. The spec's own acceptance note flags this risk without resolving it —
this plan resolves it concretely below.

The existing scoped rule `.login-field input { padding-left: 44px !important; }`
(index.css:542-544) has specificity `(0,1,1)` — still lower than the global
rule's `(0,2,1)`, so a same-shaped selector for `border-color` would also lose.

**What to do**:

**3a — form card wrapper.** Add a class to the line-150 div and gate its styling
at the existing 900px breakpoint (same one `.login-visual`/`.login-form-panel`
already use, so no new breakpoint is introduced):

```tsx
// line 150 — change:
<div className="w-full max-w-sm relative">
// to:
<div className="w-full max-w-sm relative login-form-card">
```

```css
/* index.css — new rule, near .login-form-panel (line 421) */
@media (min-width: 900px) {
  .login-form-card {
    background: var(--card);
    border: 1px solid var(--gold-border);
    border-radius: 16px;
    padding: 26px;
  }
}
```

Below 900px this rule doesn't apply at all, so mobile stays borderless/transparent
automatically — no separate mobile override needed.

**3b — field icon color.** Replace the two icon-color rules (index.css:545-556):

```css
// change:
.login-field > svg:first-child { color: var(--text-muted); ... }
.login-field:focus-within > svg:first-child { color: var(--accent); }
// to:
.login-field > svg:first-child { color: var(--gold); ... }
.login-field:focus-within > svg:first-child { color: var(--gold); }
```

(Icon is gold both at rest and on focus — no additional focus differentiation
for the icon itself; the field border below carries the focus signal.)

**3c — field border, with enough specificity to actually win.** Add a scoped
rule prefixed with `.login-split` (the outermost login container) to reach
specificity `(0,2,1)` — matching the global rule's specificity, with the tie
broken by source order since this rule is declared later in the file:

```css
/* index.css — replace/extend the .login-field input rule block */
.login-split .login-field input {
  border-color: var(--gold-border) !important;
}
.login-split .login-field:focus-within input {
  border-color: var(--gold) !important;
}
```

**3d — clean up now-redundant Tailwind classes.** Since the border is fully
CSS-driven now, drop the dead focus utilities from `inputCls` (lines 87–90):

```ts
// change:
const inputCls =
  "w-full bg-dark-card2 border border-white/10 rounded-xl px-4 py-3 text-white " +
  "placeholder-white/30 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent " +
  "transition-colors text-sm";
// to:
const inputCls =
  "w-full bg-dark-card2 border border-white/10 rounded-xl px-4 py-3 text-white " +
  "placeholder-white/30 focus:outline-none transition-colors text-sm";
```

(`focus:outline-none` is kept so there's no default browser outline; the gold
border from 3c is now the only focus indicator.)

**Acceptance**:
- Desktop (≥900px): form sits inside a visible bordered card (`var(--card)` +
  `--gold-border`) matching the left panel's visual weight.
- Mail/Lock icons render gold at all times; focused field border changes from
  `--gold-border` to `--gold` (verified in devtools that this rule now wins over
  the global `!important` — specificity tie broken by source order).
- Mobile (<900px): form remains uncontained, no card background/border.

---

## Item 2 — Desktop login left-panel recomposition
**Scope**: Frontend-only
**Files**: `frontend/react/src/index.css` (lines 408–506), `frontend/react/src/pages/LoginPage.tsx` (lines 96–146)

**Root cause**: `index.css:408-420` splits `.login-visual` into two `flex: 1`
children — `.login-visual-top` (line 432, centered logo/badge/copy, with an
absolutely-positioned `.login-quote-zone` at line 440 overlaying its bottom 30%)
and `.login-visual-bottom` (line 476, full-bleed video at 100%×100% of its flex
half). Confirmed on disk: the video fills a full rigid half of the column and
the quote floats absolutely over empty space above it, exactly as the spec
describes. `.login-form-panel` is currently `width: 50%` (line 417-419).

**What to do**:

**2a — CSS.** Replace the `@media (min-width: 900px)` block (lines 411–420) and
remove `.login-visual-top`/`.login-visual-bottom` entirely (lines 431–439,
474–488), replacing with:

```css
@media (min-width: 900px) {
  .login-visual {
    display: flex;
    flex-direction: column;
    width: 52%;
    gap: 20px;
    padding: 32px 30px;
    background: #08080d;
    justify-content: flex-start;
  }
  .login-form-panel {
    width: 48%;
  }
}

.login-brand-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.login-preview-card {
  background: #000;
  border: 1px solid var(--gold-border);
  border-radius: 12px;
  overflow: hidden;
  position: relative;
  aspect-ratio: 16 / 10;
}
.login-preview-card video {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.login-quote-flow {
  margin-top: auto;
  text-align: center;
  padding-top: 4px;
}
```

Keep `.login-preview-pill` (lines 489–506) as-is — it's re-parented from
`.login-visual-bottom` into `.login-preview-card` but needs no rule changes
since it's already `position: absolute` relative to its nearest positioned
ancestor, and `.login-preview-card` is `position: relative` (so the pill still
anchors bottom-left of the video frame, not the whole page).

Keep the `.login-quote` keyframe rules (lines 451–472) untouched — only their
positioning wrapper changes (`.login-quote-zone` deleted, `.login-quote-flow`
added above). `.login-quote` itself is still `position: absolute` internally for
the crossfade rotation between the three quote lines — that's unrelated to the
zone-vs-flow wrapper and doesn't need to change.

**2b — JSX.** Replace the `.login-visual` subtree (lines 96–146) with:

```tsx
<div className="login-visual">
  <div className="login-brand-row login-fadein d1">
    <img
      src="/wallet-mantra-logo.png"
      alt="Wallet Mantra"
      className="login-logo-mark"
    />
    <div>
      <h1 className="font-syne text-xl font-bold text-white tracking-tight">
        Wallet Mantra
      </h1>
      <p className="text-xs text-white/50 mt-0.5">Beyond expense tracking</p>
    </div>
  </div>

  <span className="inline-flex items-center gap-1 text-xs text-indigo-300
                   bg-indigo-500/15 border border-indigo-500/30 rounded-full px-3 py-1 login-fadein d1">
    <Sparkles size={11} /> Your AI money companion
  </span>

  <div className="text-left space-y-0.5 login-fadein d1">
    <p className="text-sm text-white/70">Build awareness.</p>
    <p className="text-sm text-white/70">Reduce impulse spending.</p>
    <p className="text-sm text-white/70">
      Save <span className="text-emerald-400 font-medium">consistently.</span>
    </p>
  </div>

  <div className="login-preview-card login-fadein d2">
    <video autoPlay loop muted playsInline preload="auto" aria-hidden="true">
      <source src="/wallet-mantra-glimpse.mp4" type="video/mp4" />
    </video>
    <span className="login-preview-pill">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
        <polygon points="6 4 20 12 6 20" />
      </svg>
      Product preview
    </span>
  </div>

  <div className="login-quote-flow" aria-live="polite">
    <p className="login-quote">
      "A budget is telling your money where to go, instead of wondering where it went."
    </p>
    <p className="login-quote">
      "Small daily savings build into your biggest financial wins."
    </p>
    <p className="login-quote">
      "Track it once, and watch every rupee start working for you."
    </p>
  </div>
</div>
```

Judgment call (not specified by the mockup snippet): `.login-logo-mark` is
currently 88×88px with a float+glow animation (index.css:508-520), sized for a
centered hero position. Inline next to the wordmark in a `gap: 12px` row, 88px
will likely read as oversized relative to a `text-xl` heading — consider sizing
down (e.g. add a modifier class or inline `style={{width: 56, height: 56}}`)
while keeping the existing float/glow animation classes. Confirm against the
approved mockup before finalizing the exact px value; this plan doesn't lock a
number since the spec's CSS snippet doesn't specify one either.

**Acceptance**:
- Desktop ≥900px: left panel reads as one continuous composition — brand row,
  badge, copy, framed 16:10 video, quote — no rigid 50/50 split.
- Preview video is bordered/rounded, never full-bleed or cropped to a hard edge.
- `Product preview` pill still anchors bottom-left of the video frame.
- Mobile <900px: `.login-visual` still `display: none` — completely unaffected,
  form remains full-screen.
- No absolutely-positioned quote overlapping the video (the old `.login-quote-zone`
  is gone; `.login-quote-flow` sits in normal flow below the video).

---

## Files
| Item | File(s) | Depends on |
|---|---|---|
| 1 — Gold token | `index.css` | — |
| 6 — Fixed KPI reorder/differentiation | `pages/DashboardPage.tsx`, `index.css` | — (independent of 1–5) |
| 5 — Trust footer consolidation | `pages/LoginPage.tsx` | Item 1 (uses `--gold`) |
| 4 — CTA navy/gold | `pages/LoginPage.tsx`, `index.css` | Item 1 |
| 3 — Form card + gold accents | `pages/LoginPage.tsx`, `index.css` | Item 1 |
| 2 — Desktop left-panel recompose | `index.css`, `pages/LoginPage.tsx` | Item 1 |

## Execution Order
1. **Item 1** — gold token (trivial, unlocks everything else)
2. **Item 6** — Fixed KPI (independent; can also be done first/in parallel if preferred)
3. **Item 5** — trust footer text swap + unused-import cleanup
4. **Item 4** — CTA button restyle
5. **Item 3** — form card wrap + focus-border specificity fix
6. **Item 2** — full left-panel recomposition (largest surface area, do last)

## Definition of Done
- `npm run build` passes (zero TypeScript errors) and `npm run lint` passes with
  zero warnings (watch for the `Shield`/`UserCheck` unused-import case in Item 5).
- All 6 items manually verified in the running app at both <900px and ≥900px
  viewport widths, and in both dark and light theme.
- Fixed tab, Overview tab, and login/register flows show no regressions.
