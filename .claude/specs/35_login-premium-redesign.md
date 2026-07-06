# Spec 35 — Login Page Premium Redesign (dense left hero + right-anchored card)
**Date**: 2026-07-05
**Status**: 📝 Draft — approved via interactive mockup review (2026-07-05). Not yet implemented.
**Branch**: `feature/sprint0726p1-ui-enhancement` *(confirm active branch before starting)*
**Follows / depends on**: `34_login-always-dark.md` — **34 stays as-is; 35 builds on top of it.**
35 assumes 34 has landed: login route already always-dark (`.login-split` token
re-scope), the gold token, the two cleaned logo assets + header theme-swap, and the
login polish (card border lift, `max-w-md`).
**Source**: Live-browser review of the Spec-34 login outcome (Jul 5) — the layout
still reads as two loose fragments (left content top-left, form floating in empty
space, nothing sharing a baseline). One approved interactive mockup (premium
redesign), informed by a user-supplied reference + design guide
(`Wallet_Mantra_Login_Design_Guide.md`). The reference's layout/density is adopted;
its fabricated content is not (see D4).

---

## Context

Spec 34 fixed the *correctness* of the login (always-dark, clean marks) but not its
*composition*. Live review of the 34 outcome confirms the core complaint: the left
column is top-aligned and floats in the upper-left while the lower-right sits empty;
the form card is vertically centered but the left content is not, so the two halves
never share a top/bottom baseline. It reads as fragments, not a page.

The user supplied a reference (premium fintech login) and a design guide describing a
55/45 two-column layout: a dense left hero (headline, feature list with gold-outline
icons, floating insight cards, product preview) balanced against a right sign-in card
anchored near the right edge. This spec adopts that **layout and density** while
keeping Wallet Mantra's real identity and honest content.

**Decisions (confirmed via mockup):**

| # | Decision | Choice |
|---|----------|--------|
| D1 | Layout | **55/45 two-column.** Dense left hero; right sign-in card **anchored to the right edge** with a generous gap from center. Both columns span full height and share a top/bottom baseline (fixes the fragment problem). Builds on Spec 34; 34's login items are unchanged. |
| D2 | Insight cards | **Clean in-flow strip** of three illustrative cards (not overlapping the preview), with a visible "illustrative" label. |
| D3 | Tagline under wordmark | **"Beyond expense tracking"** (the live tagline). Not "Know. Plan. Grow." |
| D4 | Content integrity | **Honest content only.** No fabricated stats/user-counts/ratings, no testimonials, no Google/Apple sign-in, no "256-bit / Bank-level / SOC 2" badges. Carried from Specs 32–34. Insight-card figures are sample data, labeled illustrative. Real features, real brand (blue/gold/charcoal), real product-preview video. |

---

## Item 1 — Layout & split ratio (`index.css`, `LoginPage.tsx`)

**Current (post-34):** `.login-split` is a flex row; `.login-visual` ~52% (left,
always-dark), `.login-form-panel` ~48% with the form centered via `max-w-md`. Left
content is top-aligned; right form is vertically centered — mismatched baselines.

**Change:**
- Split to **55% / 45%** (`.login-visual` / `.login-form-panel`).
- **Left hero** becomes a full-height flex column (`flex-direction: column`) that
  distributes its blocks top→bottom, with the product preview pushed toward the
  lower area (`margin-top: auto` on the preview or a spacer) so the column visually
  fills the height — brand at top, quote at the very bottom.
- **Right card** hugs the right edge: the form panel uses
  `justify-content: flex-end` with right padding, and the card is capped at
  ~380–400px (the guide's 560–620px is sized for a 1600px canvas; scale to the app).
  This leaves deliberate whitespace between center and the card's left edge (the
  "generous gap").
- Keep the whole thing gated to desktop (≥900px). Below 900px, unchanged from 34
  (left hero hidden, form full-screen, always-dark).

**Acceptance:** Desktop ≥900px — left hero and right card share top/bottom baselines
(no floating fragment); card is clearly near the right border with open space to its
left; nothing centered-and-lonely. Mobile <900px — visually unchanged from Spec 34.

---

## Item 2 — Left hero restructure (`LoginPage.tsx`, `index.css`)

Rebuild the `.login-visual` subtree, top→bottom:

1. **Brand row** — the cleaned logo mark (Spec 34 dark asset) + "Wallet Mantra"
   wordmark + **"Beyond expense tracking"** subtitle (D3). (Replaces the current
   brand row; drops the standalone "Your AI money companion" pill — that line
   becomes the headline below.)
2. **Headline** — "Your AI money companion" at ~26–28px, with "AI" accented
   (indigo). This is the hero statement.
3. **Value prop** — "Build awareness. Reduce impulse spending. Save
   consistently." ("consistently" in green, as today).
4. **Feature list** — five rows, each a **gold-outline rounded-square icon chip**
   (~34px, 1px gold border, gold `lucide-react` icon) + label. Honest WM features:
   - `Sparkles` — Tara, your AI money companion
   - `Sun` — Daily mantra & monthly story
   - `Bookmark` — Fixed commitments & reminders
   - `HeartHandshake` (or `Heart`) — Insights & peace-of-mind score
   - `Lock` — Private & secure
   (Icons are `lucide-react`, already the project's icon lib — not Tabler.)
5. **Insight strip (D2)** — a single in-flow row of three cards (illustrative
   sample data), followed by a small muted "Illustrative preview data" caption:
   - Saved this month — `+₹8,450` (green)
   - Peace of mind — `Excellent` (indigo)
   - Insight — `−18% on Food` (gold)
   These are **static/hardcoded** — the login is pre-auth, so no real data is or
   should be wired here. The caption makes that explicit.
6. **Product preview** — keep the existing framed 16:10 `.login-preview-card`
   (autoplay video + "Product preview" pill) from Spec 33/34, pushed toward the
   lower area so the column fills height.
7. **Rotating quote** — keep the existing `.login-quote-flow` block at the bottom.

New CSS classes as needed (e.g. `.login-hero-headline`, `.login-feature`,
`.login-feature-chip`, `.login-insight-strip`, `.login-insight-card`), all inside
the always-dark `.login-split` scope from Spec 34 (so they inherit dark tokens).

**Acceptance:** Left hero renders brand → headline → value prop → 5 feature rows →
3-card insight strip (+ illustrative caption) → framed preview → quote, in that
order, filling the column height. Feature icon chips are gold-outlined and legible.
No fabricated stats or testimonials anywhere.

---

## Item 3 — Right sign-in card (`LoginPage.tsx`, `index.css`)

**Current (post-34):** `.login-form-card` with the existing fields, `.login-cta-gold`
(navy/gold) CTA, trust line, privacy notice.

**Change:** reposition per Item 1 and keep the card treatment the user approved
(Image 2): `#12121a` fill, **visibly gold border** (the mock uses ~`rgba(224,184,74,0.45)`;
tune against the Spec-34 `#6b5620` card border — pick the more legible), ~20px radius.
Contents stay as-is from Specs 32–34:
- "Welcome back" / "Sign in to Wallet Mantra"
- Email field (gold icon, gold focus border)
- Password field + show/hide + "Forgot password?"
- `.login-cta-gold` Sign In (navy fill / gold border / gold text)
- "Don't have an account? Create one"
- Divider → "Your data stays private and encrypted" (gold lock) → Privacy notice

**Explicitly NOT added (D4):** no Google/Apple/social sign-in, no "Remember me"
(not implemented), no security/compliance badges. The card stays honest.

**Acceptance:** Card sits near the right edge, gold border clearly reads, all
existing fields/CTA/links intact, no social-sign-in or badge rows introduced.

---

## Item 4 — Subtle premium background (optional, `index.css`)

The guide calls for low-opacity navy + gold radial hints on the base. Add two very
subtle radial gradients to the `.login-split` (or `.login-visual`) background —
navy top-left, gold top-right, both low-opacity — over the base `#0b0b10`/`#08080d`.
Keep it restrained (no particles, no animation, no glow). Skip if it muddies the
video preview.

**Acceptance:** Background has a faint navy/gold depth cue, not a flat black slab;
no banding or distraction behind the form or preview.

---

## Item 5 — Mobile (no change beyond Spec 34)

Below 900px the left hero stays hidden and the form is full-screen and always-dark
(Spec 34). The new hero content (headline, feature list, insight strip) is
desktop-only and must not leak into the mobile DOM in a way that shows. Confirm no
regression at <900px.

**Acceptance:** Mobile login unchanged from Spec 34 — form-only, dark, legible.

---

## Files
| Item | File(s) |
|---|---|
| 1 — Layout / split ratio | `index.css`, `pages/LoginPage.tsx` |
| 2 — Left hero restructure | `pages/LoginPage.tsx`, `index.css` |
| 3 — Right card reposition | `pages/LoginPage.tsx`, `index.css` |
| 4 — Subtle background (optional) | `index.css` |
| 5 — Mobile check | (verification only) |

No new assets — uses the Spec 34 cleaned logo marks. Icons are existing
`lucide-react`.

## Sequencing
1. **Depends on Spec 34 landing first** (always-dark scope, cleaned marks, gold
   token, login polish). Do not implement 35 before 34.
2. Within 35: Item 1 (layout) first, then Items 2–3 (content into the new frame),
   then Item 4 (polish). Item 5 is verification.
3. Independent of any Fixed-tab work.

## Verification
- Drive live in a browser at ≥900px and <900px. At desktop: confirm shared
  top/bottom baselines, right-anchored card, dense hero, honest content. At mobile:
  confirm no regression from Spec 34.
- Login is always dark (Spec 34) so no light-mode variant to check here — but
  confirm the theme toggle still has no effect on `/login`.
- `npm run build` clean (tsc). `npm run lint` still expected unavailable on this
  branch (pre-existing).

## Out of scope
- **All fabricated content** (D4): user-count/ratings/testimonials, social/biometric
  sign-in, security/compliance badges, "watch 60 sec demo" — none reintroduced.
- **Wiring insight cards to real data** — they're static illustrative (pre-auth).
- The reference's **purple-forward palette** — WM keeps blue/gold/charcoal.
- **Fixed-tab light-mode contrast issues** (deferred since the Jul-4 review).
- **Spec 34's items** — unchanged; 35 does not re-open the always-dark re-scope,
  the logo assets, or the header swap.
