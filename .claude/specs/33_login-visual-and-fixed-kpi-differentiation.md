# Spec 33 — Login Visual Rebalance, Gold Brand Token, Fixed-tab KPI Differentiation
**Date**: 2026-07-04
**Status**: ✅ Implemented (2026-07-04) — all 6 items landed per `.claude/plans/33-login-visual-and-fixed-kpi-differentiation.md`. `npm run build` passes clean; live browser verification not performed this session (see `.claude/blocked/33-followups-for-reevaluation.md`).
**Branch**: `feature/sprint0726p1-ui-enhancement` *(spec originally listed `feature/sprint06261-ui-enhancement` — corrected to match actual `git status` at implementation time)*
**Follows**: `32_login-page-polish.md`
**Source**: In-house design review (Jul 2026) grounded in actual codebase
(`LoginPage.tsx`, `index.css`, `DashboardPage.tsx`, `KpiCarousel.tsx`).
Three approved interactive mockups: login mobile card, login desktop split,
Fixed-tab KPI cards (mobile + desktop).

---

## Context

Spec 32 landed the login form UX layer (labels, validation icon, show/hide,
trust strip, privacy URL). This spec addresses what 32 did **not** touch: the
*visual composition* of the desktop login and the *color semantics* of the
Fixed-tab KPI cards — the two areas that still read as "generic dark-SaaS
template" rather than Wallet Mantra.

Two root problems identified in review:

1. **Desktop login left panel** splits into two rigid `flex: 1` halves
   (`.login-visual-top` + `.login-visual-bottom` in `index.css`). The video
   fills a full ~50% of a tall column, so it renders as a large cropped block
   with the quotes floating in dead space above it. The two halves never read
   as one composition, and the right-hand form floats on bare `--bg` with no
   container, so it looks like an unrelated panel bolted on.

2. **Fixed-tab KPI cards** (`fixedCards` in `DashboardPage.tsx`) all use
   `gradientClass: "kpi-card-bills"` — the same amber gradient ×3. The cards
   are indistinguishable at a glance; you must read the number to know which is
   which. (Overview's KPI set already differentiates by hue and reads correctly
   — this brings Fixed to parity.)

A third thread runs through both: the brand's **gold** (from the logo) never
appears anywhere in the live UI — every accent is Tailwind indigo/purple. This
spec introduces a reusable gold token and spends it deliberately on the login.

**What's NOT in this spec (deliberately excluded):**
- Biometric / Face ID, remember-me, social proof / ratings, "bank-level
  security / 256-bit encryption" claims — all excluded in Spec 32 for the same
  reasons (no infra / no real data / inaccurate). Not reintroduced here.
- Recoloring Overview KPI cards or any other tab — Overview already reads
  correctly; scope stays on Fixed.
- Light-mode gold treatment beyond what the token provides — dark mode is the
  primary surface; verify light mode doesn't break but don't optimize it here.

---

## Decisions (confirmed in review)

| # | Decision | Choice |
|---|----------|--------|
| D1 | Gold accent scope | **Promote to a reusable token** (`--gold`, `--gold-border`, `--gold-bg`) in `index.css`, not login-only local classes |
| D2 | Fixed "Left" card treatment | **Neutral lit card, always** — no conditional warning tint |
| D3 | Login CTA treatment | **Navy fill + gold border + gold text** (per mockup), replacing the indigo→purple gradient on the login button only |

---

## Item 1 — Gold brand token (`index.css`)

**Current:** no gold anywhere in `:root`. Logo PNG carries gold; UI does not.

**Change:** add gold tokens to the `:root` block alongside the existing brand
vars, and a light-mode consideration under `html.light`.

```css
:root {
  /* Brand */
  --accent:    #6366f1;
  --accent2:   #8b5cf6;
  --accent-bg: rgba(99, 102, 241, 0.15);

  /* Brand — gold (from logo mark). Introduced Spec 33. Used sparingly:
     login CTA/accents now; reserved for future milestone/celebration surfaces. */
  --gold:        #facc15;
  --gold-border: #4a3a12;   /* muted gold — borders on dark fields/cards */
  --gold-bg:     rgba(250, 204, 21, 0.10);
  --gold-navy:   #1e1b4b;   /* deep indigo-navy fill paired with gold text/border */
}
```

Light-mode override (gold reads too bright on light surfaces — darken slightly):

```css
html.light {
  --gold:        #b8860b;   /* darker gold for contrast on light bg */
  --gold-border: rgba(184, 134, 11, 0.30);
  --gold-bg:     rgba(184, 134, 11, 0.10);
  --gold-navy:   #ede9fe;   /* light lavender fill for the CTA in light mode */
}
```

**Acceptance:** tokens resolve in both themes; no visual change yet until Items
2–4 consume them. Grep confirms `--gold` used only where this spec specifies.

---

## Item 2 — Desktop login left-panel recomposition (`index.css`, `LoginPage.tsx`)

**Current:** `.login-visual` is a 50%-width flex column split into
`.login-visual-top` (flex:1, logo+quotes) and `.login-visual-bottom` (flex:1,
full-bleed video). The 50/50 split is the core problem.

**Change:** replace the two rigid halves with a single flowing column:
brand block → tagline → **framed preview card (fixed aspect ratio)** → rotating
quote. The preview is no longer full-bleed; it sits in a bordered, rounded card
so it reads as a deliberate product shot, not a cropped video.

**2a — CSS (`index.css`):** rework the `.login-visual` internals.

```css
@media (min-width: 900px) {
  .login-visual {
    display: flex;
    flex-direction: column;
    width: 52%;               /* was 50% — slightly favor the visual panel */
    gap: 20px;
    padding: 32px 30px;
    background: #08080d;
    justify-content: flex-start;
  }
  .login-form-panel { width: 48%; }
}

/* Brand block — logo + wordmark inline, tagline below */
.login-brand-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

/* Framed preview card — fixed aspect ratio, NOT full-bleed.
   Replaces .login-visual-bottom full-height video. */
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

/* Rotating quote sits at the bottom of the column, not absolutely
   positioned over the video anymore */
.login-quote-flow {
  margin-top: auto;
  text-align: center;
  padding-top: 4px;
}
```

Retain the existing `.login-quote` rotation keyframes; only the positioning
wrapper changes (`.login-quote-zone` absolute → `.login-quote-flow` in-flow).
The `.login-visual-top` / `.login-visual-bottom` rules are removed.

**2b — JSX (`LoginPage.tsx`):** restructure the `.login-visual` subtree to
match. Brand row (logo + wordmark + "Beyond expense tracking"), AI badge,
three-line value prop, framed preview card containing the existing
`<video>` + `Product preview` pill, then the rotating quote block in-flow at
the bottom. **The real `<img src="/wallet-mantra-logo.png">` stays** — mockup
"W" is a placeholder only.

**Acceptance:**
- Desktop ≥900px: left panel is one continuous composition top-to-bottom; the
  preview video sits in a 16:10 framed card, never full-bleed or cropped.
- The `Product preview` pill remains bottom-left of the preview card.
- Mobile <900px: unchanged (left panel still `display:none`; form is full screen).
- No absolutely-positioned quote overlapping the video.

---

## Item 3 — Login form container + gold accents (`LoginPage.tsx`)

**Current:** the form panel content sits in `.login-form-panel` centered on bare
`--bg` — no card boundary. Field icons, focus states, and CTA are all indigo.

**Change:** wrap the form column in a bordered card and apply gold accents.

**3a — Form card:** the inner `max-w-sm` wrapper gets a card treatment
(desktop): background `#12121c` (or `var(--card)`), `1px solid var(--gold-border)`,
`border-radius: 16px`, padding ~26px. On mobile keep it borderless/transparent
(the form is already the whole screen — a card would look boxed-in). Gate the
card styling behind the same 900px breakpoint or a dedicated class.

**3b — Gold field + icon accents:** the Mail/Lock field icons and the
`:focus-within` field border use gold instead of the current muted white /
indigo:

```css
.login-field > svg:first-child { color: var(--gold); }          /* was --text-muted */
.login-field:focus-within > svg:first-child { color: var(--gold); }
/* field border on focus: use --gold-border (rest) → --gold (focus) */
```

Adjust the shared `inputCls` border to `var(--gold-border)` at rest — verify it
doesn't fight the global `input { border-color: var(--border-lg) }` override in
`index.css` (may need a scoped `.login-field input` rule to win specificity).

**Acceptance:**
- Desktop: form sits in a visible bordered card matching the left panel's weight.
- Mail/Lock icons render gold; focused field shows a gold border.
- Mobile: form remains uncontained (no boxed card).

---

## Item 4 — Login CTA: navy fill + gold border + gold text (`LoginPage.tsx`)

**Current:** the Sign In / Create Account buttons use
`bg-gradient-to-r from-accent to-accent2` (indigo→purple gradient).

**Change (D3):** on the login page only, the primary CTA becomes navy fill +
gold border + gold text.

```tsx
// replace the gradient button className with a gold-navy treatment:
className="w-full font-syne font-semibold py-3 rounded-xl transition-colors
           disabled:opacity-50"
style={{
  background:  "var(--gold-navy)",
  border:      "1px solid var(--gold)",
  color:       "var(--gold)",
}}
```

Applies to both the login-mode and register-mode submit buttons for consistency.
Hover: subtle — lift background toward a slightly lighter navy or add a faint
gold glow via box-shadow; keep it restrained.

**Acceptance:**
- Both login and register submit buttons render navy fill / gold border / gold
  text in dark mode, and remain legible in light mode (uses `--gold-navy` +
  `--gold` light overrides from Item 1).
- Disabled (`loading`) state still visibly dims via `disabled:opacity-50`.
- No other button in the app changes — gradient CTA style stays everywhere else.

---

## Item 5 — Trust footer consolidation (`LoginPage.tsx`)

**Current:** three trust badges (`Passwords encrypted` / `Data stays private` /
`You're in control`) rendered at `text-[10px]` and `text-white/25` — effectively
unreadable, and remapped to `--text-muted` in light mode but still tiny.

**Change:** consolidate to a single legible line with one gold lock icon:

> 🔒 Your data stays private and encrypted

Render at ~`text-[11px]` / `text-white/55` (not `/25`), lock icon in `--gold`.
Drop the three-item map. This is honest (no new claims — just the two true ones
merged) and readable.

**Acceptance:**
- One trust line, single gold lock icon, legible contrast (passes AA against
  `--bg`).
- No three-badge row; no unreadable 10px/25%-opacity text remaining on login.

---

## Item 6 — Fixed-tab KPI differentiation + reorder (`DashboardPage.tsx`, `index.css`)

**Current:** `fixedCards` in `DashboardPage.tsx` builds three cards, all with
`gradientClass: "kpi-card-bills"` (amber ×3), in order total → paid → left.

**Change (D2):** reorder to **left → paid → total** and give each a distinct
treatment: Left = neutral lit card (always), Paid = green (settled), Total =
amber (baseline). Left needs a new gradient/surface class because it must read
as clearly *off* the near-black `--bg` — the earlier dashed-outline attempt was
near-invisible.

**6a — New CSS class (`index.css`), near the KPI gradient block:**

```css
/* Fixed-tab "Left / pending" card — neutral lit surface (Spec 33 D2).
   Deliberately NOT a gradient: a flat lit slate reads as its own state and
   sits clearly above the #0a0a0f page bg. Stays dark in BOTH themes so the
   forced-white card text (.kpi-card-value etc.) remains legible. */
.kpi-card-fixed-left {
  background: #2a2a3d;
  border: 1px solid rgba(255, 255, 255, 0.22);
}
```

Note: `.kpi-card-remaining` (green) already exists and is reused for the Paid
card. `.kpi-card-bills` (amber) already exists and is reused for the Total card.
Text-on-card classes (`.kpi-card-value` etc.) already force white — `#2a2a3d`
gives sufficient contrast. Deliberately no `html.light` override (see Light-mode
risk below).

**6b — JSX (`DashboardPage.tsx`):** rebuild `fixedCards` in the new order with
the new classes:

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

**Acceptance:**
- Fixed tab shows cards in order: Fixed left, Fixed paid, Fixed total.
- Left = neutral lit slate (visibly distinct from page bg), Paid = green,
  Total = amber — distinguishable at a glance without reading numbers.
- Mobile carousel order and desktop row order both reflect left → paid → total.
- Dot indicators and desktop active/side states still work (component unchanged).

---

## Light-mode risk (KPI item)

The `.kpi-card-value` / `.kpi-card-label` / `.kpi-card-sub` classes force
**white text** regardless of theme (by design — the gradient cards are dark in
both modes). Therefore `.kpi-card-fixed-left` must **stay a dark slate in light
mode too** (no `html.light` override), consistent with the gradient cards which
are already dark in light mode. This is baked into Item 6a above — do not add a
light surface variant or the white card text becomes invisible.

---

## Files
| Item | File(s) |
|---|---|
| 1 — Gold token | `index.css` |
| 2 — Desktop left-panel recompose | `index.css`, `pages/LoginPage.tsx` |
| 3 — Form card + gold accents | `index.css`, `pages/LoginPage.tsx` |
| 4 — CTA navy/gold | `pages/LoginPage.tsx` |
| 5 — Trust footer consolidation | `pages/LoginPage.tsx` |
| 6 — Fixed KPI differentiation + reorder | `pages/DashboardPage.tsx`, `index.css` |

## Sequencing
1. **Item 1 first** (gold token) — Items 2–5 consume it.
2. Items 2–5 (login) can land together in one commit; they touch the same file.
3. **Item 6 (Fixed KPI) is fully independent** of the login work and can land
   separately / first if preferred — no shared surface with Items 1–5 except the
   pre-existing KPI gradient block in `index.css`.

## Out of scope
- Any biometric / remember-me / social-proof / security-claim reintroduction.
- Overview or other tab KPI recoloring.
- Fixed "Left" conditional warning tint (rejected — D2 is always-neutral).
- New logo asset work (real PNG already in place from Spec 31).
