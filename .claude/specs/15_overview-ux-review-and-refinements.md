# Spec: Overview Tab — UX Review & Refinements
**Date**: 2026-06-28
**Status**: 🔴 Ready to implement
**Branch**: `feature/sprint06261-ui-enhancement`
**Follows**: `14_wizard-ux-improvements.md`
**Source**: iPhone 15 Safari screenshots review + independent UX audit (June 28, 2026)

---

## Context

A full UX review of the Overview tab was conducted using 8 iPhone 15 Safari screenshots
captured at 1:37–1:38 AM on June 28, 2026, cross-referenced with an independent reviewer's
annotated mockup and written report (score: 9.2/10).

This spec documents **all identified issues** — bugs, polish gaps, and structural improvements —
in priority order. Items are grouped into three tiers:

- **Tier 1 — Fix before sharing with new users** (bugs and trust-eroding issues)
- **Tier 2 — High value, low effort** (polish and naming)
- **Tier 3 — Structural / longer horizon** (IA and personalisation direction)

---

## Tier 1 — Critical (Fix Before Wider Sharing)

---

### Issue 1A — Miscellaneous as Category Winner *(Data quality / Trust)*

**Priority**: P0

**Symptom**: The Category Winner trophy tile shows **Miscellaneous — ₹9,880 (19% of variable)**
with a 59% ↓ vs May badge. Miscellaneous is not a real spending category — it is the AI
parser's fallback when it cannot classify a transaction.

**Why this matters**: This is the highest-trust issue in the entire app. The Overview tab
projects financial intelligence through Peace of Mind scores, Spending Signals, and AI
sentences. Awarding a trophy to an uncategorized bucket contradicts that intelligence. A user
seeing this will question whether the app understands their spending at all.

**Root cause**: Two compounding problems:
1. The AI expense categorization defaults too heavily to "Miscellaneous" (known open issue).
2. The Category Winner logic does not filter out "Miscellaneous" before selecting the winner.

**Fix — Part A (Category Winner filter)**:
In the Category Winner computation, exclude "Miscellaneous" from the winner candidates.
If all categories are Miscellaneous, fall back to: "No clear winner this month."

```ts
// Pseudocode
const winner = categories
  .filter(c => c.name !== 'Miscellaneous')
  .sort((a, b) => b.amount - a.amount)[0] ?? null;
```

If `winner === null`, render a neutral fallback tile:
> 🏅 **No clear winner this month**
> Most spending was uncategorized. Try reviewing your transaction categories.

**Fix — Part B (AI categorization — tracked separately)**:
Improving the AI parser's categorization accuracy is a prerequisite for the monthly report
card feature and should be scheduled as its own sprint item. Ref: known open issue
"AI expense categorization defaulting too heavily to Miscellaneous."

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — Category Winner section
- `backend/ai_parser.py` — (Part B, separate sprint)

**Acceptance criteria**:
- "Miscellaneous" never appears as the Category Winner label.
- If no non-Miscellaneous category exists, a neutral fallback tile renders instead of the trophy.
- All other Category Winner logic (% of variable, vs last month delta) unchanged.

---

### Issue 1B — Spending Signals cards clipped on iPhone 15 *(Layout bug)*

**Priority**: P1

**Symptom**: In the Spending Signals section, the right edge of each card is cut off.
"₹2,815 over" renders as "₹2,815 ove" and "₹1,976 over" is similarly truncated.
This occurs on an iPhone 15 (390px viewport width) in Safari.

**Root cause**: Likely a missing `overflow: hidden` on the card container, or the card's
right-side content block has no `min-width: 0` causing it to overflow its flex parent.

**Fix**:
1. On the Spending Signals card container, ensure `overflow: hidden` is set.
2. On the right-side content block (percentage label + amount), add `flex-shrink: 0` and
   sufficient right padding so text does not extend beyond the card boundary.
3. If the layout uses `flex` without `min-width: 0` on children, add it to the left block
   (category name + amounts) so the right block is not squeezed off-screen.

**Do NOT switch to a 3-column horizontal layout** (Groceries | Shopping | Entertainment
side by side) as suggested in the independent review mockup — at 390px this would give
each card ~130px, which is insufficient for the content inside them.

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — Spending Signals card layout
- Possibly `frontend/react/src/index.css` — if card styles are global

**Acceptance criteria**:
- All Spending Signal card content fully visible on iPhone 15 (390px) Safari.
- No horizontal scroll introduced.
- Card layout (vertical stack or 2-up) unchanged.

---

## Tier 2 — High Value, Low Effort (Polish & Naming)

---

### Issue 2A — "Upcoming Reality" section name is unclear *(Naming)*

**Symptom**: The section showing upcoming due bills and expected month-end balance is
labelled "Upcoming reality". The content is excellent (Term Insurance due in 1 day,
expected balance ₹1,417) but the name reads as abstract and slightly dramatic.

**Fix**: Rename to **"📅 Coming Up"**.

- Section heading: `📅 Coming Up`
- Section comment: `{/* ── Section N: Coming Up (due bills + month-end balance) ─── */}`

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — section heading text

**Acceptance criteria**:
- Section heading reads "📅 Coming Up".
- No other content in the section changed.

---

### Issue 2B — Balance segment invisible in Monthly Breakdown stacked bar *(Visual)*

**Symptom**: The stacked bar shows Bills 63% + Variable 34% + Balance ~2%. The Balance
segment (₹3,479) is a sliver of green that is functionally invisible — it gets clipped
at the right edge of the bar.

**Fix**: Two options — choose one:

**Option A (preferred)**: Give the Balance segment a CSS `min-width` of 32px regardless
of its percentage, so it always renders as a visible chip.

**Option B**: Remove Balance from the stacked bar entirely and instead show it as a
separate labelled row below the bar legend:
> `🟢 Balance  ₹3,479  (2%)`

The legend row below the bar already lists Balance with its value — Option B avoids
duplication while solving the visibility problem.

**Recommendation**: Option B. The legend row is already there. No need to force a pixel
minimum on a proportional bar.

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — Monthly Breakdown bar + legend

**Acceptance criteria**:
- Balance amount is clearly legible (either as a visible bar segment or as a legend-only row).
- Total percentage still adds up to 100% in the bar (Bills + Variable fill the bar if Balance
  is legend-only).

---

### Issue 2C — Duplicate trophy icon across two sections *(Visual polish)*

**Symptom**: The 🏆 trophy emoji appears in both:
1. **Category Winner** — "🏆 Miscellaneous — ₹9,880"
2. **Tiny Win** — "🏆 You've been tracking consistently. That itself is progress."

Using the same icon for two different concepts in a single scroll dilutes both.

**Fix**: Change the Tiny Win section icon from 🏆 to 🌱.

> `🌱 Tiny win`

This better reflects the behavioural design intent (growth, not winning) and
differentiates it clearly from the category performance trophy.

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — Tiny Win section header emoji

**Acceptance criteria**:
- Tiny Win heading uses 🌱 emoji.
- Category Winner section retains 🏆 emoji.

---

### Issue 2D — Financial Pulse tile heights are uneven *(Visual polish)*

**Symptom**: In the 2×2 Financial Pulse grid, tile heights differ between rows because
some descriptions wrap to two lines ("Tracked expenses on 28 days this month.") while
others are one line ("Savings below target."). This makes the grid feel visually unbalanced.

**Fix**: Add a `min-height` CSS constraint to each Financial Pulse tile so all four tiles
share the same minimum height regardless of description length.

Suggested: `min-height: 120px` on the tile card element (adjust to match actual content height).

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — Financial Pulse tile styles
- Possibly `frontend/react/src/index.css`

**Acceptance criteria**:
- All four Financial Pulse tiles render at the same height in the 2×2 grid.
- No text is truncated; longer descriptions still wrap fully within their tile.

---

### Issue 2E — Tracking Summary: disclaimer shown when user cannot act on it *(UX tone)*

**Symptom**: The Tracking Summary card shows:
> Last month: **2 days** (orange)
> "Monthly comparisons become more accurate with consistent daily tracking."

The disclaimer is shown immediately after a stat the user cannot retroactively fix.
It reads as a mild rebuke.

**Fix**: Only show the disclaimer text when the gap is large enough to affect data accuracy
AND the current month still has days remaining where the user can course-correct.
If the current month is nearly over (e.g. last 3 days), suppress the disclaimer entirely.

**Condition**:
```ts
const daysRemaining = getDaysRemainingInMonth();
const showDisclaimer = lastMonthDays < 7 && daysRemaining > 3;
```

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — Tracking Summary disclaimer

**Acceptance criteria**:
- Disclaimer hidden when fewer than 3 days remain in the current month.
- Disclaimer visible when tracking gap is meaningful and there are days left to improve.
- Orange "2 days" stat still shows regardless of disclaimer visibility.

---

### Issue 2F — Header consumes excessive vertical space on mobile *(Space efficiency)*

**Symptom**: The app header on iPhone 15 occupies ~140px of vertical space across two rows:
- Row 1: 🤑 Wallet Mantra logo + tagline "Beyond expense tracking" + theme button + avatar
- Row 2: "June 2026" pill (standalone row)

**Fix**: Compress into a single row:
`🤑 Wallet Mantra  |  June 2026 ▼  |  ☀️  |  D`

- Move the month picker pill inline with the logo row.
- Remove the "Beyond expense tracking" tagline from the header (it can live on the Settings
  or About page — users who are already in the app don't need to see the tagline on every scroll).
- Result: single 56px header row instead of ~140px two-row header.

**Affected files**:
- `frontend/react/src/components/layout/Header.tsx` (or equivalent header component)

**Acceptance criteria**:
- Header renders in a single row on mobile (≤ 390px).
- Logo, month picker, theme toggle, and avatar all visible in that single row.
- No tagline visible in the header on mobile.
- No regression on desktop layout.

---

## Tier 3 — Structural Direction (Plan, Don't Implement This Sprint)

These items are directionally correct and should inform future sprint planning.
No implementation in the current sprint.

---

### Issue 3A — Financial Pulse tiles are generic, not personal

**Current state**: Tiles show labels like "Fixed obligations are nearly complete." and
"Food spending accelerated this month." These are accurate but could be more specific.

**Direction**: Replace generic descriptions with data-anchored one-liners:
- Stability: "2 bills still pending. All others on track."
- Lifestyle: "Grocery spending up 32% vs last month."
- Savings: "₹34,000 set aside this month. Keep going!"
- Consistency: "Tracked on 26 of 28 days. Great consistency!"

This makes Financial Pulse feel significantly smarter without adding new sections.

**Scheduled for**: Sprint after current (post-wizard sprint).

---

### Issue 3B — Information Architecture: 3-layer flow

**Current scroll order** is approximately:
KPI Cards → June in One Sentence → Monthly Breakdown → Spend by Category →
Category Winner → Peace of Mind → Spending Signals → Upcoming Reality →
Money Moments → Tracking Summary → Financial Pulse → Tiny Win (~9–10 screens)

**Recommended IA** (from independent review, endorsed):

| Layer | Purpose | Sections |
|-------|---------|----------|
| Layer 1 — Snapshot | How am I doing? | KPI Cards, June in One Sentence, Peace of Mind |
| Layer 2 — Understand | Why? | Monthly Breakdown, Spend by Category, Spending Signals, Insight card |
| Layer 3 — Reflect | What's next? | Upcoming Reality, Money Moments, Financial Pulse, Tiny Win |

Moving Peace of Mind up to Layer 1 (immediately after the summary sentence) would
dramatically increase its visibility. It's the strongest differentiator in the app and
currently buried below the category chart.

**Target scroll depth**: 4–5 screens (from current ~9–10). Achieve by:
- Collapsing Tracking Summary into a single line within Financial Pulse or Peace of Mind.
- Making Money Moments "View all" the primary CTA rather than showing 3 items inline.
- Keeping Financial Pulse as a 2×2 grid but using it as a footer/closer, not a mid-page section.

**Scheduled for**: Major IA sprint (new branch).

---

### Issue 3C — Money Moments: rank labels over transaction list format

**Current state**: Money Moments shows a ranked numbered list (1, 2, 3...) with
category, date, amount, and % of spending. Reads like a transaction list.

**Direction**: Use story labels instead of ranks:
- 🏆 Biggest Purchase — Esplanade · ₹4,779
- 🎁 Largest Gift — Birthday Gift · ₹2,170
- 📚 Learning Investment — Course · ₹5,000
- 👑 Top Category Spend — SBI Mutual Fund · ₹4,000

This transforms the section from a filtered transaction list into a memorable financial
narrative — which is the app's core brand promise.

**Scheduled for**: Sprint after current.

---

### Issue 3D — Adaptive Insights for new / data-sparse users

**Current state**: Spec 12 defines 4 scenarios (A: first month, B: MoM comparison,
C: gap + highlights, D: tracking quality). Scenario D is live. Others are not yet built.

**Direction** (confirmed): Complete the scenario selector per spec 12. The independent
review's scenario breakdown (A/B/C/D) maps almost exactly to spec 12's design.
Prioritize Scenario B (MoM comparison) next, as it's the most valuable for returning users.

**Scheduled for**: After wizard improvements sprint.

---

## Summary Table

| # | Issue | Tier | Type | Effort | File |
|---|-------|------|------|--------|------|
| 1A | Miscellaneous as Category Winner | 1 | Bug + Data | S | OverviewTab.tsx |
| 1B | Spending Signals cards clipped | 1 | Layout bug | S | OverviewTab.tsx |
| 2A | Rename "Upcoming Reality" → "Coming Up" | 2 | Naming | XS | OverviewTab.tsx |
| 2B | Balance segment invisible in stacked bar | 2 | Visual | XS | OverviewTab.tsx |
| 2C | Duplicate 🏆 icon (Category Winner + Tiny Win) | 2 | Polish | XS | OverviewTab.tsx |
| 2D | Financial Pulse tile heights uneven | 2 | Visual | XS | OverviewTab.tsx |
| 2E | Tracking Summary disclaimer shown too aggressively | 2 | UX tone | XS | OverviewTab.tsx |
| 2F | Header too tall on mobile | 2 | Space | S | Header.tsx |
| 3A | Financial Pulse generic descriptions | 3 | Personalisation | M | OverviewTab.tsx |
| 3B | IA: 3-layer scroll restructure | 3 | Structure | L | OverviewTab.tsx |
| 3C | Money Moments: story labels over ranked list | 3 | Storytelling | S | OverviewTab.tsx |
| 3D | Complete Adaptive Insights scenario selector | 3 | Feature | M | OverviewTab.tsx |

**Effort key**: XS = <30 min, S = 30–90 min, M = half-day, L = full sprint

---

## Files Likely Modified (Tier 1 + Tier 2 only)

- `frontend/react/src/components/tabs/OverviewTab.tsx` — Issues 1A, 1B, 2A, 2B, 2C, 2D, 2E
- `frontend/react/src/components/layout/Header.tsx` — Issue 2F
- `backend/ai_parser.py` — Issue 1A Part B (separate sprint, do not bundle)

## Files NOT Modified

- `backend/main.py` — no API changes needed for Tier 1 or Tier 2
- `frontend/react/src/types/index.ts` — no type changes needed
- Any shared UI component outside Header — no changes
