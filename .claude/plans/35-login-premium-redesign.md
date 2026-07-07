# Implementation Plan: Login Page Premium Redesign (logo replacement + dense hero + right-anchored card)
**Spec**: `.claude/specs/35_login-premium-redesign.md`
**Date**: 2026-07-07
**Branch**: `feature/sprint0726p1-ui-enhancement`
**Status**: ✅ Executed 2026-07-07 — all 6 items complete, `npm run build` clean, live-verified at
1280–1920px desktop widths and 375–390px mobile widths via Playwright screenshots. Two items
required deviating from this plan's original numbers to fix a real defect found during execution
(dense hero overflowed common laptop heights) — see `.claude/blocked/35-followups-for-reevaluation.md`
for the full list of deviations and open follow-ups.

---

## Overview

6 items, all frontend-only. Item 0 (logo assets) is a hard dependency for the
other items' *visual* acceptance criteria (the mark appears in every hero/card
render) but its own code footprint is tiny, so it leads the list. The rest are
ordered smallest-blast-radius-first: isolated/optional CSS additions, then
existing-class edits, then the shared-container structural change, then the
largest item (new JSX content), then a verification-only pass.

All file/line references below were re-read from disk this session (not taken
from the spec's prose) — the spec's description of "current state" matches
what's actually on disk; nothing has drifted.

| # | Item | Depends on |
|---|------|------------|
| 0 | Logo mark replacement | — |
| 4 | Subtle background gradients (optional) | — |
| 3 | Right sign-in card reposition + treatment | Item 1 (frame) for final position |
| 1 | Layout / split mechanics | — |
| 2 | Left hero restructure | Item 1 (needs the `space-between` frame to land in) |
| 5 | Mobile regression check | Items 1–3 |

---

## Item 0 — Logo mark replacement
**Scope**: Frontend-only (binary assets + one component)
**Files**:
- `frontend/react/public/wallet-mantra-logo.png` (replace, dark-surface variant)
- `frontend/react/public/wallet-mantra-logo-light.png` (replace, light-surface variant)
- `frontend/react/src/components/layout/Header.tsx` (lines 32–37)
- `frontend/react/src/pages/LoginPage.tsx` — **no code change needed**, see below

**Root cause**: `Header.tsx:33` hardcodes `src="/wallet-mantra-logo.png"` with no
theme branching — confirmed the header itself *is* theme-reactive (`index.css:140-143`,
`header { background-color: var(--card) !important; }` and `.text-white { color:
var(--text) !important; }`, both flip in `html.light`), so in light mode today the
header renders a **white card background with the dark-surface mark still on it**.
That mark (`public/wallet-mantra-logo.png`, confirmed via PIL: 256×256 RGBA) is the
asset already found broken in `.claude/blocked/34-followups-for-reevaluation.md` — a
squircle canvas with a baked-in glow/vignette, no clean silhouette. `LoginPage.tsx`
(lines 99, 160) and `KpiCarousel.tsx` (lines 47, 86) all reference the same
`/wallet-mantra-logo.png` path directly with no theme branch — login is always-dark
(Spec 34) so it only ever needs the dark-surface variant, which it already points at.

**What to do**:

1. **Produce the two production PNGs** from the new reference
   (`/Users/debashish/Desktop/01_business/feedback-self/login/logo-v1/suggestion/ChatGPT Image Jul 7, 2026, 12_27_53 AM.png`
   + `dark.png`). This is asset work, not a code edit:
   - **Dark-surface** (`wallet-mantra-logo.png`): crop the Deep-Black-BG panel and
     key it to transparency. This session confirmed (via PIL, sampling pixel maxima
     across the canvas) the glow is bounded to roughly x:206–607, y:32–436 inside an
     825×477 crop, and everything outside that box is within 15 of pure black with no
     gradient — a border-seeded flood-fill/threshold at low luminance (e.g. <12)
     should cleanly separate background from mark, unlike the old master where the
     same technique failed because the whole canvas was a gradient with no flat
     region to seed from.
   - **Light-surface** (`wallet-mantra-logo-light.png`): do **not** key this out of
     the comp's "Light BG" panel — its backdrop measured ~`(238,238,238)` with a
     mild vignette (~230 at corners), not the app's actual light-header color
     (`var(--card)` in light mode — check the resolved hex, currently `#ffffff` per
     `index.css` light-mode token block). Re-export/regenerate directly against that
     exact color instead, so there's no matte to key out at all.
   - Export both at a size that stays crisp down to 32px (256×256 or an SVG retrace
     is safer than the old assets' 256×256 raster, given the legibility risk below).
   - **Before treating this item as done**, view both new PNGs at 32px and 56–64px
     (not the source comp's full size) — the reference has thin wireframe linework
     and a small padlock glyph that may not survive that much downscaling. If it
     doesn't hold up at 32px, crop a simplified version for the header specifically.

2. **Drop the two files into `frontend/react/public/`**, overwriting the existing
   ones at the same paths — `LoginPage.tsx` and `KpiCarousel.tsx` need **zero code
   changes**, they already point at `/wallet-mantra-logo.png` and will pick up the
   new asset automatically.

3. **Wire the header theme-swap** in `Header.tsx:32-37` — this exact change was
   drafted in the blocked doc but held back pending a clean light asset:

   ```tsx
   // Header.tsx:20 — add theme to the existing destructure (already imported)
   const { theme, toggle } = useTheme();

   // Header.tsx:32-37 — before:
   <img
     src="/wallet-mantra-logo.png"
     alt=""
     aria-hidden="true"
     className="h-8 w-8 flex-shrink-0 object-contain"
   />

   // after:
   <img
     src={theme === "dark" ? "/wallet-mantra-logo.png" : "/wallet-mantra-logo-light.png"}
     alt=""
     aria-hidden="true"
     className="h-8 w-8 flex-shrink-0 object-contain"
   />
   ```
   `theme` is already destructured from `useTheme()` at line 21 — no new import needed.

**Side effect worth knowing (not in spec's scope, flagging so it isn't a surprise)**:
`KpiCarousel.tsx` (lines 47, 86) renders the same `/wallet-mantra-logo.png` as a
32px watermark (`.kpi-watermark-img`, `index.css:316-324`, opacity 0.6) on top of
`.kpi-slide`/`.kpi-card-shell` backgrounds, with **no light/dark variant swap** —
it always uses the dark-surface file. Replacing that file fixes the watermark in
dark mode for free. In light mode, if a KPI card's background is itself light, the
dark-surface mark may read weakly (low contrast, not a halo problem this time,
just a legibility one) — worth a quick look during verification but not blocking
this item; `index.css:311-314`'s existing comment already flags the watermark as
depending on this same asset.

**Acceptance**: see spec Item 0 (no halo/smudge against real backgrounds at 2×
zoom; legible at 32/56/64px; both header themes checked live; login checked dark).

---

## Item 4 — Subtle premium background (optional)
**Scope**: Frontend-only
**Files**: `frontend/react/src/index.css` (new rule, insert near `.login-split`, ~line 425)

**Root cause**: N/A — pure addition, nothing broken. `.login-split` currently has no
background treatment beyond the flat `--bg`/`#08080d` tokens set at lines 433-449.

**What to do**: Add two very-low-opacity radial gradients layered under the existing
flat background, restrained per the spec (no particles/animation/glow):

```css
.login-split {
  background:
    radial-gradient(ellipse 800px 600px at 0% 0%, rgba(30,27,75,0.35), transparent 60%),
    radial-gradient(ellipse 700px 500px at 100% 0%, rgba(250,204,21,0.06), transparent 55%),
    #0a0a0f;
}
```
Place this *after* the existing `.login-split { --bg: ...; }` token block (line
449) so it doesn't get clobbered by cascade order — gradients are a separate
property (`background`) from the CSS custom properties, so there's no literal
conflict, just keep it visually grouped with the other `.login-split` rules.

**Acceptance**: Faint navy top-left / gold top-right depth cue only; skip entirely
(revert this one rule) if it visibly competes with the video preview once Item 2 lands.

---

## Item 3 — Right sign-in card reposition + vertical fill
**Scope**: Frontend-only
**Files**: `frontend/react/src/index.css` (lines 508-527), `frontend/react/src/pages/LoginPage.tsx` (line 154-155)

**Root cause**: `.login-form-panel` (`index.css:508-516`) is currently
`display:flex; align-items:center; justify-content:center` — the card floats in
the middle of the panel rather than hugging the right edge. `.login-form-card`
(`index.css:520-527`, gated `@media (min-width: 900px)`) has `border: 1px solid
#6b5620` (the Spec-34 "lifted" border) and no height-stretch behavior — it sizes
to its content, leaving empty space below it that doesn't reach the hero's quote.

**What to do**:

1. **`.login-form-panel`** (`index.css:508-516`) — change justify-content and add
   right padding, keep stretch for the height fill:
   ```css
   /* before */
   .login-form-panel {
     width: 100%;
     display: flex;
     align-items: center;
     justify-content: center;
     padding: 32px 24px;
     background-color: var(--bg);
     position: relative;
   }
   /* after */
   .login-form-panel {
     width: 100%;
     display: flex;
     align-items: stretch;
     justify-content: flex-end;
     padding: 32px 56px 32px 24px;   /* 56px right gap per spec's 48–64px range */
     background-color: var(--bg);
     position: relative;
   }
   ```
   Below 900px this rule isn't reached differently than today — the mobile layout
   is governed elsewhere (form panel is full width, no left hero) — confirm no
   regression in Item 5.

2. **`.login-form-card`** (`index.css:520-527`, inside the existing `@media
   (min-width: 900px)` block) — stretch to the panel height, update border/radius,
   and vertically center the inner content:
   ```css
   /* before */
   .login-form-card {
     background: var(--card);
     border: 1px solid #6b5620;
     border-radius: 16px;
     padding: 26px;
   }
   /* after */
   .login-form-card {
     background: #12121a;
     border: 1px solid rgba(224,184,74,0.45);
     border-radius: 22px;
     padding: 32px;
     align-self: stretch;
     display: flex;
     flex-direction: column;
     justify-content: center;
   }
   ```
   The spec asks to "reconcile" the border color with Spec 34's `#6b5620` and pick
   whichever is more legible — using the new `rgba(224,184,74,0.45)` since it's the
   one the spec calls "visibly gold," vs. `#6b5620` which is the same dim tone
   Spec 34 already lifted away from once.

3. **Card width** — `LoginPage.tsx:155` already has `className="w-full max-w-md
   relative login-form-card"`. Tailwind's `max-w-md` is `28rem` = **448px**, which
   already sits inside the spec's 420–460px target — no change needed here.

4. **Inner content cap for very tall viewports** (spec's fallback clause) — if
   manual verification at a tall viewport (e.g. 1920×1200) shows too much internal
   air once the card stretches to full column height, add `max-height` + `margin:
   auto 0` to the form's inner wrapper (the `<div className="login-fadein d2">` at
   `LoginPage.tsx:179`) rather than un-stretching the card itself. Don't pre-emptively
   add this — check first, since `justify-content:center` from step 2 may already
   be enough.

**Acceptance**: see spec Item 3 (right-anchored with fixed gap, stretched height,
gold border reads, all existing fields/CTA/links intact, no social/badge rows).

---

## Item 1 — Layout / split ratio (concrete mechanics)
**Scope**: Frontend-only
**Files**: `frontend/react/src/index.css` (lines 422-471), `frontend/react/src/pages/LoginPage.tsx` (unchanged — this item is CSS-only)

**Root cause**: `.login-split` (`index.css:422-425`) is `min-height:100vh;
display:flex` with no explicit `align-items` (default `stretch`, already correct —
no change needed there). The 900px media query (`index.css:458-471`) sets
`.login-visual` to `width:52%; justify-content:center` (vertically centers the
whole column instead of pinning top/bottom) and `.login-form-panel` to `width:48%`.
This centered-column behavior is what currently causes the shared "floats in the
middle, empty band below" symptom described in the spec's Context section — verified
live in the current build, matches exactly.

**What to do** — in the existing `@media (min-width: 900px)` block (`index.css:458-471`):

```css
/* before */
@media (min-width: 900px) {
  .login-visual {
    display: flex;
    flex-direction: column;
    width: 52%;
    gap: 20px;
    padding: 32px 30px;
    background: #08080d;
    justify-content: center;
  }
  .login-form-panel {
    width: 48%;
  }
}
/* after */
@media (min-width: 900px) {
  .login-visual {
    display: flex;
    flex-direction: column;
    width: 55%;
    gap: 20px;
    padding: 56px 30px;         /* equal top anchor vs. form-panel below */
    background: #08080d;
    justify-content: space-between;
  }
  .login-form-panel {
    width: 45%;
    padding-top: 56px;          /* match .login-visual's top padding */
  }
}
```
Note: `.login-form-panel`'s `padding-top: 56px` here combines with Item 3's
`padding: 32px 56px 32px 24px` — apply Item 3's change first, then override just
`padding-top` here (or fold both into one final declaration once both items are
in the same PR): final panel padding should read `padding: 56px 56px 32px 24px`.
Flag this overlap explicitly during implementation so the two items' edits don't
clobber each other — whichever item lands second should reconcile into a single
`padding` shorthand rather than leaving a stray `padding-top` override.

**Acceptance**: see spec Item 1 (brand-row top / card top within ~8px; quote
bottom / card bottom within ~24px; fixed 48–64px right gap — 56px per Item 3;
mobile <900px unchanged).

---

## Item 2 — Left hero restructure
**Scope**: Frontend-only
**Files**: `frontend/react/src/pages/LoginPage.tsx` (lines 94-151, plus import line 3), `frontend/react/src/index.css` (new classes)
**Depends on**: Item 1 (the `space-between` frame needs to exist for this content to distribute correctly instead of clumping)

**Root cause**: Current `.login-visual` subtree (`LoginPage.tsx:94-151`) has: brand
row → a standalone indigo "pill" badge (`Sparkles` + "Your AI money companion",
lines 112-116) → a 3-line value prop (lines 118-124) → the preview card (lines
126-137) → the quote (lines 139-150). The spec calls for the pill to be dropped
and become the headline, plus a new 5-item feature list and 3-card insight strip
inserted between the value prop and the preview card — neither exists in the
current file.

**What to do**:

1. **Imports** (`LoginPage.tsx:3`) — add the three new icons:
   ```tsx
   // before
   import { Mail, Lock, Sparkles, CheckCircle, XCircle, Eye, EyeOff } from "lucide-react";
   // after
   import { Mail, Lock, Sparkles, CheckCircle, XCircle, Eye, EyeOff, Sun, Bookmark, HeartHandshake } from "lucide-react";
   ```
   Confirmed all three (`Sun`, `Bookmark`, `HeartHandshake`) exist in the installed
   `lucide-react` version this session.

2. **Replace the pill block** (`LoginPage.tsx:112-116`) with a headline:
   ```tsx
   // remove the <span> pill entirely, replace with:
   <h2 className="login-hero-headline login-fadein d1">
     Your <span className="text-indigo-400">AI</span> money companion
   </h2>
   ```

3. **Value prop** (`LoginPage.tsx:118-124`) — keep as-is; already matches the
   spec's copy ("Build awareness." / "Reduce impulse spending." / "Save
   consistently." with green "consistently").

4. **Insert feature list** after the value prop block (after line 124, before the
   preview card at line 126):
   ```tsx
   <div className="login-fadein d1" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
     {[
       { Icon: Sparkles, label: "Tara, your AI money companion" },
       { Icon: Sun, label: "Daily mantra & monthly story" },
       { Icon: Bookmark, label: "Fixed commitments & reminders" },
       { Icon: HeartHandshake, label: "Insights & peace-of-mind score" },
       { Icon: Lock, label: "Private & secure" },
     ].map(({ Icon, label }) => (
       <div key={label} className="login-feature">
         <span className="login-feature-chip"><Icon size={16} style={{ color: "var(--gold)" }} /></span>
         <span className="text-sm text-white/70">{label}</span>
       </div>
     ))}
   </div>
   ```

5. **Insert insight strip** after the feature list, still before the preview card:
   ```tsx
   <div className="login-insight-strip login-fadein d2">
     <div className="login-insight-card">
       <span className="text-xs text-white/50">Saved this month</span>
       <span className="text-emerald-400 font-semibold">+₹8,450</span>
     </div>
     <div className="login-insight-card">
       <span className="text-xs text-white/50">Peace of mind</span>
       <span className="text-indigo-400 font-semibold">Excellent</span>
     </div>
     <div className="login-insight-card">
       <span className="text-xs text-white/50">Insight</span>
       <span style={{ color: "var(--gold)" }} className="font-semibold">−18% on Food</span>
     </div>
   </div>
   <p className="text-center text-[10px] text-white/30">Illustrative preview data</p>
   ```

6. **New CSS classes** — add to `index.css` near the other `.login-*` rules (after
   `.login-brand-row`, ~line 480):
   ```css
   .login-hero-headline {
     font-family: 'Syne', sans-serif;
     font-weight: 700;
     font-size: 27px;
     color: var(--text);
     line-height: 1.25;
   }
   .login-feature {
     display: flex;
     align-items: center;
     gap: 12px;
   }
   .login-feature-chip {
     width: 34px;
     height: 34px;
     border-radius: 10px;
     border: 1px solid rgba(224,184,74,0.45);
     display: flex;
     align-items: center;
     justify-content: center;
     flex-shrink: 0;
   }
   .login-insight-strip {
     display: flex;
     gap: 10px;
   }
   .login-insight-card {
     flex: 1;
     display: flex;
     flex-direction: column;
     gap: 4px;
     padding: 10px 12px;
     border-radius: 12px;
     background: var(--card2);
     border: 1px solid var(--border);
   }
   ```

7. **Preview card and quote** (`LoginPage.tsx:126-150`) — no changes, stay in place
   after the new blocks.

**Acceptance**: see spec Item 2 (seven blocks in order, filling column height with
even `space-between` spacing, gold-outlined legible chips, no fabricated content —
the insight figures above are explicitly labeled illustrative per the caption in
step 5).

---

## Item 5 — Mobile regression check
**Scope**: Verification-only, no files changed
**Depends on**: Items 1–3 landed

**What to do**: Below 900px, `.login-visual` is `display:none` (`index.css:455-457`,
unaffected by any of the above since all structural changes are inside the
`@media (min-width: 900px)` block or apply to `.login-split`'s base background,
which is intentionally kept for the mobile full-bleed dark form too). Load
`/login` at a <900px viewport and confirm: form-only, dark, legible, no visual
regression from Spec 34. No code change expected — if a regression is found,
it means one of Items 1–3's edits leaked outside its media query and needs to be
scoped back in.

**Acceptance**: see spec Item 5.

---

## Verification (all items)
- `npm run build` (tsc + Vite) clean.
- `npm run lint` still expected to fail with `eslint: command not found` — this is
  the same pre-existing gap noted in specs 31-34's blocked docs, not introduced here.
- Live-check both breakpoints and both themes (header) per each item's acceptance
  section above — screenshot comparison against the approved mockup recommended
  given this project's history of "satisfies the wording, still looks wrong" gaps.
