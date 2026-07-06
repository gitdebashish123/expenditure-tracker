# Spec 35 — Login Page Premium Redesign (dense left hero + right-anchored card)
**Date**: 2026-07-05 · **Refined**: 2026-07-07 (alignment mechanics made concrete after reviewing the live pre-35 build) · **Refined again**: 2026-07-07 (logo mark replacement added as Item 0, superseding the Spec-34 asset assumption below)
**Status**: ✅ Implemented 2026-07-07 — all 6 items landed and verified live (build clean, both breakpoints, mobile unregressed). See `.claude/plans/35-login-premium-redesign.md` for the executed plan and `.claude/blocked/35-followups-for-reevaluation.md` for deviations/gaps found during implementation (short-viewport overflow fix, header light-mode not live-verified, minor asset-quality notes).
**Branch**: `feature/sprint0726p1-ui-enhancement` *(confirm active branch before starting)*
**Follows / depends on**: `34_login-always-dark.md` — **34's login-block items (1–3:
always-dark re-scope, gold token, card border lift) landed and stay as-is.**
**Correction (2026-07-07): the logo assets + header theme-swap did NOT land** — per
`.claude/blocked/34-followups-for-reevaluation.md`, they were re-blocked on
2026-07-06/07 after pixel inspection found the "cleaned" marks are an opaque
squircle canvas with a baked-in glow/vignette that has no separable edge (three
keying approaches failed structurally, not from bad parameters). Spec 35 previously
assumed these were done; **they are not, and this is still visibly true** in
`frontend/react/public/wallet-mantra-logo.png` today. This refinement adds **Item 0**
to replace the mark entirely using a new user-supplied reference, rather than
continuing to chase a keying fix on an unfixable master.
**Source**: Live-browser review of the pre-35 login (Jul 5 and Jul 7) — the layout
reads as two loose fragments (left content top-left, form floating vertically
centered and mid-panel, large empty space below both, nothing sharing a baseline).
One approved interactive mockup (premium redesign), informed by a user-supplied
reference + design guide (`Wallet_Mantra_Login_Design_Guide.md`). The reference's
layout/density is adopted; its fabricated content is not (see D4).

---

## Context

Spec 34 fixed the *correctness* of the login (always-dark, clean marks) but not its
*composition*. The current live build is still pre-35: the left hero is sparse
(brand + pill + value prop + preview, top-aligned) and the right card floats
vertically centered around the middle of its panel, not near the right edge, with a
large empty band below both columns. It reads as fragments, not a page.

**Why this refinement (2026-07-07):** the original 35 stated the *goals* ("share a
top/bottom baseline", "hug the right edge") but not the concrete flex mechanics, so
an implementation could satisfy the wording and still float the card. Item 1 and
Item 3 below now pin down the exact layout behavior. Decisions D1–D4 are unchanged;
this only makes the mechanics unambiguous.

**Decisions (confirmed via mockup):**

| # | Decision | Choice |
|---|----------|--------|
| D1 | Layout | **55/45 two-column, both full-height.** Dense left hero pinned top-and-bottom; right sign-in card **anchored near the right edge** and **filling most of the column height**, so the two columns share top/bottom baselines. Builds on Spec 34; 34's login items unchanged. |
| D2 | Insight cards | **Clean in-flow strip** of three illustrative cards (not overlapping the preview), with a visible "illustrative" label. |
| D3 | Tagline under wordmark | **"Beyond expense tracking"** (the live tagline). Not "Know. Plan. Grow." |
| D4 | Content integrity | **Honest content only.** No fabricated stats/user-counts/ratings, no testimonials, no Google/Apple sign-in, no "256-bit / Bank-level / SOC 2" badges. Carried from Specs 32–34. Insight-card figures are sample data, labeled illustrative. Real features, real brand (blue/gold/charcoal), real product-preview video. |

---

## Item 0 — Logo mark replacement (prerequisite) (`public/`, `Header.tsx`, `LoginPage.tsx`)

**Why this is separate from, and blocks, the brand-row visuals in Items 2–3**: the
login hero brand row and the mobile/desktop card both render the logo mark. Landing
Items 1–4's layout with the current squircle-halo asset would just move the same
known-broken mark into a nicer frame. This item replaces the source asset before
the rest of the spec's visual acceptance criteria are judged.

**New reference** (user-supplied 2026-07-07, not yet in the repo):
`/Users/debashish/Desktop/01_business/feedback-self/login/logo-v1/suggestion/ChatGPT Image Jul 7, 2026, 12_27_53 AM.png`
(4-panel comp: Dark BG / Navy BG / Deep Black BG / Light BG) and a solo `dark.png`
crop of the Deep-Black variant. A stylized 3D neon-glow mark — wallet outline +
"W" in blue, upward growth-arrow + padlock in gold — on-brand (blue/gold/black
matches the existing palette; this is not the previously-rejected purple-forward
reference from the design guide).

**Verified this session (pixel inspection, not eyeballing):**
- Both files are **flattened concept comps, not production assets** — confirmed via
  `sips`/PIL: 8-bit **RGB, no alpha channel**. Cannot be dropped into `public/` as-is;
  each needed variant must be extracted/re-cropped first.
- **Dark-surface variant is good news**: unlike the currently-blocked master, the
  glow on the Deep-Black-BG crop is a *bounded* region on a genuinely flat `(0,0,0)`
  background (glow bbox ~206–607 × 32–436 inside an 825×477 canvas; everything
  outside it is near-pure-black). A border-seeded flood-fill/threshold key — the
  same technique that failed on the old master — should work here, because this
  background has an actual flat region to seed from instead of a gradient with no
  edge.
- **Light-surface variant needs care**: the "Light BG" panel's backdrop is ~`(238,
  238,238)` (off-white) with a mild vignette (~230 at corners), not a flat pure
  white and not the app's actual light-header background color. Extracting alpha
  from it risks reproducing the same (smaller-scale) "smudge against the real
  white header" problem noted in the blocked doc. **Prefer regenerating/exporting
  this variant directly against the app's actual light-mode header background
  color** rather than keying it out of this off-white comp.

**Change:**
- Produce two real production assets from this reference (via image-editor cutout,
  a fresh export against the correct exact background colors, or a redraw as SVG —
  SVG is preferable long-term since it stays crisp at any size and sidesteps
  raster-keying entirely):
  1. **Dark-surface mark** → replaces `wallet-mantra-logo.png` (login hero/card,
     dark-mode header).
  2. **Light-surface mark** → replaces `wallet-mantra-logo-light.png` (light-mode
     header only; login is always-dark per Spec 34 and never needs this variant).
- Wire the header theme-swap that Spec 34 drafted but held back
  (`Header.tsx` — conditional `src` on `theme`), now that a genuinely clean
  light-surface asset exists.

**Acceptance (do not sign off on comp size alone):**
- Both variants render with **no visible halo, smudge ring, or squircle box edge**
  against their real target backgrounds (`#0a0a0f` login / actual light-header
  color), inspected at 2× zoom, not just eyeballed at native size.
- **Legibility at real render size** — check at the actual sizes used in the app,
  not the large source comp: 32px (`Header.tsx`'s `h-8 w-8`), 56px (login desktop
  brand row), 64px (login mobile mark). The mark's thin wireframe top-shape,
  padlock detail, and outline weight are fine detail that can turn into an
  illegible blob when shrunk this far — if the full mark doesn't hold up at 32px,
  use a simplified/reduced-detail crop for the header specifically rather than
  forcing the full illustration into 32px.
- Both themes checked live (light header bg + dark header bg), plus the login
  page (always dark).

---

## Item 1 — Layout & split ratio (concrete mechanics) (`index.css`, `LoginPage.tsx`)

**Current (pre-35):** `.login-split` flex row; `.login-visual` ~52% top-aligned;
`.login-form-panel` ~48% with the form vertically centered and horizontally mid-panel.
Baselines mismatched, card floats.

**Change — exact mechanics:**

- **Both panels full height.** `.login-split { min-height: 100vh; align-items: stretch; }`
  so the two columns are the same height and can share baselines.
- **Split 55 / 45.** `.login-visual` = 55%, `.login-form-panel` = 45%.
- **Equal top anchor.** Give both panels the same top padding (e.g. `padding-block`
  ~48–56px) so the left brand row and the right card top start at the same Y.
- **Left hero = `space-between` full-height column.**
  `.login-visual { display:flex; flex-direction:column; justify-content:space-between; }`
  → brand row pinned to the top, rotating quote pinned to the bottom, and the middle
  blocks (headline → value prop → feature list → insight strip → preview) distributed
  between. This removes the empty band; the column visibly fills top→bottom.
- **Right card anchored right AND filling height.**
  `.login-form-panel { display:flex; justify-content:flex-end; align-items:stretch; padding-right: 48–64px; }`
  The card (`.login-form-card`) sits at the right with an explicit gap from the panel's
  right edge (the padding), leaving deliberate open space to its LEFT (the "generous
  gap from center"). The card **stretches toward the column height** — its top aligns
  with the hero's brand row and its bottom aligns near the hero's quote — via
  `align-self: stretch` plus internal vertical centering of the form (see Item 3), NOT
  by padding it with fake content. Card `max-width` ~420–460px (guide's 560–620px is
  for a 1600px canvas; scale down).
- **Desktop-gated (≥900px).** Below 900px unchanged from Spec 34 (left hero hidden,
  form full-screen, always-dark).

**Acceptance (measurable):**
- Left brand-row top and right card top are within ~8px of the same Y.
- Left quote bottom and right card bottom are within ~24px of the same Y (card fills
  most of the height; no large empty band below either column).
- Card's right edge is a fixed 48–64px from the viewport right edge; there is clear
  open space between the card's left edge and horizontal center.
- Mobile <900px visually unchanged from Spec 34.

---

## Item 2 — Left hero restructure (`LoginPage.tsx`, `index.css`)

Rebuild the `.login-visual` subtree, top→bottom (this is the density that lets the
`space-between` column fill height without gaps):

1. **Brand row** — cleaned dark logo mark (Spec 34) + "Wallet Mantra" wordmark +
   **"Beyond expense tracking"** subtitle (D3). Drops the standalone "Your AI money
   companion" pill — that line becomes the headline.
2. **Headline** — "Your AI money companion" ~26–28px, "AI" accented (indigo).
3. **Value prop** — "Build awareness. Reduce impulse spending. Save consistently."
   ("consistently" green).
4. **Feature list** — five rows, each a gold-outline rounded-square icon chip (~34px,
   1px gold border, gold `lucide-react` icon) + label:
   - `Sparkles` — Tara, your AI money companion
   - `Sun` — Daily mantra & monthly story
   - `Bookmark` — Fixed commitments & reminders
   - `HeartHandshake` (or `Heart`) — Insights & peace-of-mind score
   - `Lock` — Private & secure
5. **Insight strip (D2)** — one in-flow row of three cards (illustrative), then a
   small muted "Illustrative preview data" caption:
   - Saved this month — `+₹8,450` (green)
   - Peace of mind — `Excellent` (indigo)
   - Insight — `−18% on Food` (gold)
   Static/hardcoded (pre-auth); caption makes that explicit.
6. **Product preview** — keep the existing framed 16:10 `.login-preview-card` (video +
   "Product preview" pill).
7. **Rotating quote** — keep `.login-quote-flow`, pinned to the column bottom by the
   `space-between`.

New CSS classes inside the always-dark `.login-split` scope (inherit dark tokens):
`.login-hero-headline`, `.login-feature`, `.login-feature-chip`,
`.login-insight-strip`, `.login-insight-card`.

**Note on density vs. `space-between`:** with all seven blocks present the column is
dense enough that `space-between` yields even, intentional gaps rather than one big
void. If any single gap still reads too large at common heights, add a small `gap`
and let the preview take the slack (it's the natural spacer above the quote) — do NOT
reintroduce a top-pinned-only layout.

**Acceptance:** Left hero renders the seven blocks in order, filling the column height
with even spacing; feature chips gold-outlined and legible; no fabricated content.

---

## Item 3 — Right sign-in card (reposition + vertical fill) (`LoginPage.tsx`, `index.css`)

**Current (post-34):** `.login-form-card` with existing fields, `.login-cta-gold` CTA,
trust line, privacy notice — floats vertically centered and small.

**Change:**
- **Position** per Item 1: right-anchored with the 48–64px right gap, `max-width`
  ~420–460px.
- **Vertical fill.** The card `align-self: stretch` to the column height; inside, the
  form content is vertically centered (`justify-content: center` on the card's inner
  flex) with **generous vertical rhythm** between title block → fields → CTA → footer
  so the card reads full and balanced against the dense hero — achieved by spacing,
  NOT by adding social sign-in / badges / fake rows. If stretching the card to full
  height leaves too much internal air at very tall viewports, cap the inner content
  block and center it (card stays tall, content stays comfortable).
- **Card treatment** (approved, Image 2): `#12121a` fill, visibly gold border
  (`~rgba(224,184,74,0.45)`; reconcile with the Spec-34 `#6b5620` card border — pick
  the more legible), ~20–24px radius.
- **Contents unchanged** from Specs 32–34: "Welcome back" / subtitle; Email (gold
  icon, gold focus); Password + show/hide + "Forgot password?"; `.login-cta-gold`
  Sign In; "Don't have an account? Create one"; divider → "Your data stays private and
  encrypted" (gold lock) → Privacy notice.

**Explicitly NOT added (D4):** no Google/Apple/social sign-in, no "Remember me", no
security/compliance badges.

**Acceptance:** Card near the right edge (fixed gap), stretched to fill most of the
column height with comfortably-spaced content vertically centered, gold border reads,
all existing fields/CTA/links intact, no social/badge rows.

---

## Item 4 — Subtle premium background (optional, `index.css`)

Two very low-opacity radial gradients on `.login-split`/`.login-visual` — navy
top-left, gold top-right — over the base `#0b0b10`/`#08080d`. Restrained (no
particles, no animation, no glow). Skip if it muddies the video preview.

**Acceptance:** Faint navy/gold depth cue, no banding or distraction.

---

## Item 5 — Mobile (no change beyond Spec 34)

Below 900px the left hero stays hidden and the form is full-screen, always-dark. The
new hero content is desktop-only and must not show on mobile. Confirm no regression.

**Acceptance:** Mobile login unchanged from Spec 34 — form-only, dark, legible.

---

## Files
| Item | File(s) |
|---|---|
| 0 — Logo mark replacement | `public/wallet-mantra-logo.png`, `public/wallet-mantra-logo-light.png`, `components/layout/Header.tsx` |
| 1 — Layout / split ratio | `index.css`, `pages/LoginPage.tsx` |
| 2 — Left hero restructure | `pages/LoginPage.tsx`, `index.css` |
| 3 — Right card reposition + vertical fill | `pages/LoginPage.tsx`, `index.css` |
| 4 — Subtle background (optional) | `index.css` |
| 5 — Mobile check | (verification only) |

New assets for Item 0 (replacing the blocked Spec-34 marks) — see reference path in
Item 0. Icons are existing `lucide-react`.

## Sequencing
1. **Depends on Spec 34's login-block items** (always-dark scope, gold token, card
   border lift) — these landed and are unaffected. Spec 34's logo/header-swap items
   did **not** land; Item 0 above supersedes them rather than waiting further.
2. **Item 0 first** — the mark is visible in every other item's brand row/card, so
   swap the asset before judging Items 1–3's visual acceptance criteria against it.
3. Within 35: Item 1 (layout frame), then Items 2–3 (content into the frame), then
   Item 4 (polish). Item 5 is verification. Item 0 can run in parallel with Item 1
   since they touch different concerns (asset vs. layout mechanics) — just land
   Item 0 before calling Items 2–3 visually done.
4. Independent of any Fixed-tab work.

## Verification
- Drive live at ≥900px and <900px. Desktop: check the four measurable criteria in
  Item 1 (top-Y match, bottom-Y match, fixed right gap, open space to card's left),
  plus dense hero and honest content. Mobile: no regression from Spec 34.
- **Item 0**: inspect the new marks at their real render sizes (32px header, 56px
  desktop hero, 64px mobile) against their real backgrounds, both themes — not just
  the source comp at full size.
- Login is always dark (Spec 34) — no light-mode variant to check on `/login`
  itself; confirm theme toggle has no effect there. The header **does** need both
  themes checked now that Item 0 wires its theme-swap.
- `npm run build` clean (tsc). `npm run lint` still expected unavailable (pre-existing).

## Out of scope
- **All fabricated content** (D4): user-count/ratings/testimonials, social/biometric
  sign-in, security/compliance badges, "watch 60 sec demo".
- **Wiring insight cards to real data** — static illustrative (pre-auth).
- The reference's **purple-forward palette** — WM keeps blue/gold/charcoal.
- **Fixed-tab light-mode contrast issues** (deferred since the Jul-4 review).
- **Spec 34's layout/token items** (always-dark re-scope, gold token, card border
  lift) — unchanged, not reopened. Its logo-asset and header-swap items **are**
  reopened, via Item 0 above, since they never actually landed.
