# Spec 28 — Accessibility Pass + Parser-Failure Manual Fallback
**Date**: 2026-06-30
**Status**: ✅ Implemented 2026-06-30
**Branch**: `feature/sprint06261-ui-enhancement` *(confirm active branch before starting)*
**Follows**: `27_insight-staleness-followup-invalidation-gaps.md`
**Source**: external UX review cross-check (two near-duplicate review docs, June 30 2026)
+ code-grounded verification. This spec deliberately extracts only the items that are
**safe, behavior-neutral, and genuinely missing** from the reviews — see "Explicitly
rejected from the reviews" below for what was *not* carried forward and why.

---

## Context

Two external review documents (effectively one review, duplicated) scored the app
91/100 and proposed a large list of renames, a new AI-explainability pattern, and some
genuine accessibility gaps. Most of the renames conflict with decisions already made in
Specs 24/25 (commitments-not-bills naming) and would re-introduce the exact "1 bills"
class of inconsistency those specs fixed — **rejected**. Two items, however, are
genuine, low-risk, and verified against the current code: **accessibility** (contrast,
touch targets, screen-reader support, motion, chart text alternatives) and **graceful
parser failure** (the app already has an unused manual-entry endpoint).

**No functional change.** This spec changes input controls, ARIA attributes, color
tokens, and adds a *fallback path* when the AI parser fails — it removes no existing
behavior and changes no business logic.

### Explicitly rejected from the reviews (do not implement)
- Renaming "Fixed" → "Bills" / "Monthly Bills", "Add Commitment" → "Add Monthly Bill" —
  reverses the Spec 24 naming decision (EMIs/SIPs/transfers aren't bills).
- Renaming Tara-branded surfaces ("Peace of Mind", "June in one sentence", "How Tara
  calculated this") to generic equivalents — strips the product's differentiation; the
  reviews praise Tara's personality and then propose removing it from every surface.
- "Spending Caps" → "Budgets" — plausible but a real naming decision touching Spec 25;
  not bundled here.
- Voice logging, adaptive home screen, haptics, weekly AI recap, achievement
  celebrations — net-new features; the reviews' own conclusion ("refine, don't add
  dashboards") argues against bundling these now.

---

## Item 1 — Accessibility: contrast tokens
**Scope**: Frontend-only, CSS tokens · **Confirmed** in `frontend/react/src/index.css`

`--text-muted: rgba(255, 255, 255, 0.30)` on `--bg: #0a0a0f` is ~2:1 contrast — well
under WCAG AA's 4.5:1 (normal text) / 3:1 (large text/UI). This single token feeds
`.text-dark-muted` etc. used throughout (placeholders, captions, sub-labels). `--text-sub`
at 0.55 opacity is closer to passing but should be verified, not assumed.

**Fix:** raise `--text-muted` opacity (e.g. ~0.45–0.50 on dark, recompute the light-mode
equivalent at `rgba(26,26,46,0.35)` similarly) until it clears 4.5:1 against `--bg` and
`--card`. Spot-check `--text-sub` the same way. Re-test both light and dark mode (the
tokens are duplicated under `html.light`).

**Acceptance:** automated contrast check (e.g. axe/Lighthouse) shows no AA contrast
violations on muted/secondary text in either theme.

---

## Item 2 — Accessibility: touch targets
**Scope**: Frontend-only · **Priority**: confirmed pattern across multiple components
(independently flagged in Specs 22/25 reviews — this generalizes the fix)

Several interactive icons render at `size={12}`–`size={14}` with no padding (edit/trash
icons in Fixed rows, pool entries, income rows; checkboxes). WCAG 2.1 target size wants
≥24×24 CSS px minimum, with 44×44 as the comfortable mobile standard already adopted
elsewhere in this project's specs.

**Fix:** wrap small interactive icons in a tap-target wrapper (min 44×44px hit area,
icon can stay visually small inside it) rather than enlarging every icon glyph. Apply
project-wide to: Fixed row edit/trash, pool entry edit/trash, income row trash, caps
edit/save, shortcut tile actions, checkbox controls in History.

**Acceptance:** no interactive control has a computed hit area under 44×44px on mobile
viewports.

---

## Item 3 — Accessibility: screen-reader labels + keyboard focus
**Scope**: Frontend-only

- Icon-only buttons (eye/bell/trash/edit/chevron controls across Header, Fixed,
  Settings, History) need `aria-label`s describing the action, not just an icon.
- Verify visible `:focus-visible` styles exist for keyboard navigation on buttons, tabs,
  and form controls (spot-check — Tailwind defaults may already cover this; don't
  assume either way).
- Charts (Overview's category donut, the Bills/Variable breakdown bar) need a text
  equivalent. The category breakdown already has a legend with values — confirm it's
  programmatically associated (not just visually adjacent) so a screen reader gets the
  same information as the visual.

**Acceptance:** icon-only controls have descriptive `aria-label`s; keyboard tab order
reaches all interactive elements with a visible focus indicator; chart data is available
as text to assistive tech.

---

## Item 4 — Accessibility: reduced motion
**Scope**: Frontend-only

Respect `prefers-reduced-motion: reduce` for the KPI carousel's scroll-snap animation,
any count-up number animations, and transition effects. Provide a non-animated
equivalent (instant value display, no smooth-scroll) when the preference is set.

**Acceptance:** with `prefers-reduced-motion: reduce` set, no animated transitions or
count-up effects play; content is still fully accessible.

---

## Item 5 — Parser-failure manual fallback (Today tab)
**Scope**: Frontend-only · backend already supports this

**Confirmed in code:** `POST /expenses/manual` exists (`backend/main.py`), accepts
`{vendor, amount, category, note?, expense_date?}`, validates via `ManualExpense`,
already calls `_invalidate_month_caches`. **It is unused by the frontend** —
`QuickAddTab.tsx` only calls `/expenses/parse`, and on any parser failure (AI outage,
malformed input, no amount detected, the credit-balance 422 seen recently) the user gets
an error with no path forward.

**Fix:** when `/expenses/parse` fails or returns an error, show an inline fallback
form — vendor/description, amount, category picker — that submits to
`/expenses/manual`. This does not change `/expenses/parse`'s behavior; it adds a
recovery path when parsing fails for *any* reason (AI outage, ambiguous input, no
amount found), so expense entry never hard-blocks on the AI being unavailable.

**Acceptance:** when the parser call fails, the user can still log an expense via the
fallback form without leaving the Today tab.

---

## Out of scope
- Any terminology change beyond what's already decided in Specs 24/25.
- New AI explainability UI beyond what Specs 22/25/26 already cover (mantra's
  "How Tara calculated this" already exists as a pattern).
- Voice/gesture features, adaptive layouts, haptics — net-new, not this spec.
- Full WCAG audit tooling/CI integration (manual + spot-check verification only, here).

## Files
- `frontend/react/src/index.css` — Item 1 (contrast tokens)
- Fixed/Pool/Income/Caps/Shortcuts row components — Item 2 (tap targets, same files
  identified across Specs 22/24/25)
- `components/layout/Header.tsx` and icon-only controls across Settings/Fixed — Item 3
- KPI carousel component, any count-up hooks — Item 4
- `frontend/react/src/components/tabs/QuickAddTab.tsx` — Item 5 (fallback UI calling the
  existing `/expenses/manual`)

## Order
1. Item 1 (token change, lowest risk, widest reach).
2. Item 5 (fixes a real incident path — manual fallback).
3. Items 2–4 (touch targets, ARIA/focus, reduced motion — can proceed in parallel).
