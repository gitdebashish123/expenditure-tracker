# Spec: Today Tab + Overview Tab Redesign
**Date**: 2026-06-23
**Status**: Open — awaiting implementation

## Context

Three rounds of external product feedback, two AI-generated reference
mockups, and an iterative visual review converged on a clear direction:
both the Today tab and Overview tab need structural redesigns, not just
polish. The core shift: Wallet Mantra should answer "Am I okay? Am I on
track? What changed? What should I know today?" — not present an
accounting dashboard.

Key decisions confirmed before this spec was written:
- **Tara lives on Today tab only** — not Overview, to avoid assistant
  fatigue and keep Tara intentional.
- **Overview section order**: Financial Snapshot → This Month's Story →
  Peace of Mind → Financial Pulse → What Changed? → Upcoming Reality →
  Budget Health → Tiny Win (hybrid of reference screenshot order and
  feedback document suggestions, with Tara removed).
- **Financial Pulse does not appear on the Today tab** — Today tab is
  for action (log expenses) and a single daily Tara insight, not a
  full dashboard.
- **"Ask Tara" appears twice on Today tab**: as a button inside the
  mantra card, and as a floating action button (FAB) — both are shells
  only (no chat backend yet); FAB and button open a "Coming soon" state.
- **Peace of Mind Score** is included but the scoring formula weights
  must be confirmed before implementation (see Issue 3).

Visual reference: `overview-feedback.png` and `Today_s-feedback.png`
(uploaded during review session). Tara avatar asset: `Tara-image.png`
(uploaded, to be saved as `frontend/react/public/tara.png`).

---

## Today Tab Changes

### Issue T1 — Replace summary strip/flip-cards with hero balance card + 3 chips

**What exists today**: `DashboardPage.tsx` renders either `SummaryStrip`
(mobile, `md:hidden`) or three `SummaryFlipCard` components (desktop,
`hidden md:flex`) above all tabs when `showSummary` is true. These are
generic — same treatment regardless of which tab is active. The flip-card
mechanic (hover-only reveal) is a known discoverability gap (spec 05,
Issue 1).

**What's missing**: A rich, tab-specific hero section on Today that
immediately answers "how much do I have left?" without any hover gesture
or strip-style compression. The reference mockup shows: a large card with
a wallet icon, the remaining balance in large green text, "Remaining this
month" label, and a short contextual sub-label ("Comfortable for the next
7 days") — followed by three compact chips for Income, Fixed Paid, and
Pending Bills.

**Affected file(s)**:
- `frontend/react/src/pages/DashboardPage.tsx` — render a different
  summary component when `tab === "today"` instead of the generic
  strip/flip-cards
- New component:
  `frontend/react/src/components/shared/HeroBalanceCard.tsx` — the
  large remaining card + 3 chips
- `frontend/react/src/components/shared/SummaryStrip.tsx` and
  `SummaryFlipCard.tsx` — kept for Fixed/Overview tabs (not removed)

**Fix approach**:
In `DashboardPage.tsx`, when `tab === "today"`, render `<HeroBalanceCard
balance={balance} />` instead of the strip/flip-cards. For other tabs
that `showSummary` covers (Fixed, Overview), keep the existing strip/flip
behaviour unchanged.

`HeroBalanceCard` receives the `Summary["balance"]` object (already
fetched in `DashboardShell`) and renders:
- Large card: wallet icon, `fmtInr(balance.remaining)` in `--success`
  green at ~26px Syne bold, "Remaining this month" label, sub-label
  (see Note below)
- Below it: a 3-chip row — Income (`balance.total_income`, indigo),
  Fixed Paid (`balance.fixed_paid_total`, green), Pending Bills
  (`balance.fixed_unpaid_total`, amber)

**Sub-label note**: "Comfortable for the next X days" requires computing
days-left and a daily-budget comfort threshold — this is the same
`days_left` logic already in `daily_mantra()`. For Phase 1 of this spec,
derive it client-side: `days_left = days_in_month - today.day`,
`daily_budget = remaining / days_left`, then a simple threshold:
`remaining > 0 && daily_budget > 500 → "Comfortable for the next
{days_left} days"`, else `"₹{fmtInr(daily_budget)}/day remaining"`.
Do not add a new backend endpoint for this — it's derivable from the
`balance` object already in the client.

**Acceptance criteria**:
- Today tab shows the hero card immediately on load, no hover required.
- The 3 chips (Income, Fixed Paid, Pending Bills) show real values.
- Fixed and Overview tabs continue to show the existing SummaryStrip /
  SummaryFlipCard — no regression.

**Priority**: High — this is the most visible single change in the whole
spec; the hero card is the first thing the user sees on opening the app.

---

### Issue T2 — Tara mantra card: add avatar, "Ask Tara" button, rename "Why?" label

**What exists today**: `TodaysMantraCard` in `QuickAddTab.tsx` renders
the mantra sentence with a "🪷 From Tara" heading and a "Why?" toggle
(spec 07, Item 5 — may or may not be implemented yet depending on where
Phase 2 is). No avatar, no "Ask Tara" action.

**What's missing**:
1. Tara's avatar image, right-aligned inside the card, bleeding to the
   card's right/bottom edge (portrait crop, upper half of the image
   visible). Asset: `Tara-image.png` → save to
   `frontend/react/public/tara.png`.
2. "Ask Tara" as a pill button below the mantra sentence (inside the
   card, left-aligned), styled in indigo (`--accent` background, white
   text). For now: clicking opens a toast or modal saying "Ask Tara is
   coming soon." Do not wire to any chat backend.
3. Rename "Why?" / "How Tara calculated this" label — spec 07 Phase 2
   used "Why?"; the reference mockup uses a chevron-down expand; the
   feedback document suggests "How Tara calculated this →". Use
   "How Tara calculated this" as the final label (warmer, more
   specific than "Why?"). If spec 07 Phase 2 hasn't been implemented
   yet, this is the first time the expand label gets built; if it has,
   this is a copy update only.

**Affected file(s)**:
- `frontend/react/public/` — add `tara.png` (copy from uploaded asset)
- `frontend/react/src/components/tabs/QuickAddTab.tsx`
  (`TodaysMantraCard`)

**Fix approach**: Restructure `TodaysMantraCard`'s outer div to
`display: flex`, with the content section (`flex: 1`) on the left and
the avatar (`width: 110px, align-self: stretch`) on the right, bleeding
into the card's padding via negative margin on the right/bottom edges
(matching the mockup's portrait-crop treatment). Add the "Ask Tara" pill
button below the mantra text, before the "How Tara calculated this"
expand. The card's existing accent border (`border-color: var(--accent)`)
stays.

**Acceptance criteria**:
- Tara's avatar is visible on the right side of the mantra card.
- "Ask Tara" pill button is present and shows a "coming soon" state on
  click.
- The expand label reads "How Tara calculated this" not "Why?".
- On narrow screens (< 360px), the avatar gracefully hides
  (`display: none` below a breakpoint) so the text doesn't get
  squeezed.

**Priority**: High — the avatar is the single visual element that most
distinguishes Wallet Mantra from a generic dashboard in the reference
mockup.

---

### Issue T3 — Today tab section order and improved empty state

**What exists today**: `QuickAddTab.tsx` renders:
`TodaysMantraCard → NL Input Form → Favourites → Today's Entries`

**What's missing**:
- Section order should be: `TodaysMantraCard → Quick Log → Today's
  Entries` (Favourites stays where it is, between log form and entries
  — no change needed there).
- The empty state for Today's Entries currently shows "Nothing logged
  today." with a generic sub-message. The reference mockup shows a
  richer empty state: icon, "Nothing logged today.", "You usually log
  your first expense around 10:30 AM." (behaviour insight — placeholder
  text for now since time-of-day analytics aren't built yet; use a
  static friendly message like "Start with something small — tea 20?"),
  and 3 quick-suggestion chips ("tea 20", "uber 180", "milk 60") that
  pre-fill the NL input on tap.

**Affected file(s)**:
- `frontend/react/src/components/tabs/QuickAddTab.tsx`

**Fix approach**: The section order is already correct after spec 06's
implementation (mantra card first). The main new work is the empty state:
replace the current minimal empty state with a richer version including
the suggestion chips. Each chip's `onClick` calls
`setText("tea 20")` (or the relevant string) so the NL input is
pre-filled and the user just taps "Add Expenses". The time-of-day
insight ("You usually log around 10:30 AM") should be a static
placeholder for now: "Start your day by logging something small."

**Acceptance criteria**:
- Today's Entries empty state shows an icon, friendly message, static
  sub-label, and 3 tappable chips.
- Tapping a chip pre-fills the NL input with that expense string.
- Non-empty state (when entries exist) is completely unchanged.

**Priority**: Medium — genuinely improves the new-user/morning experience
but doesn't block the higher-priority visual changes.

---

### Issue T4 — Ask Tara floating action button (FAB)

**What exists today**: No FAB anywhere in the app.

**What's missing**: A purple circular FAB pinned to the bottom-right of
the Today tab (above the bottom nav), showing a chat/message icon. For
now: tapping it shows a "coming soon" toast. This reserves the UI
real estate for the future "Ask Tara" conversational feature without
building the chat backend.

**Affected file(s)**:
- `frontend/react/src/components/tabs/QuickAddTab.tsx` — render the FAB
  as a fixed-position element within the tab's scrollable area

**Fix approach**: Add a `position: fixed; bottom: 72px; right: 16px`
circular button (52×52px, `background: var(--accent)`, white chat icon,
`border-radius: 50%`, `z-index: 30`) at the bottom of
`QuickAddTab`'s return. `72px` bottom offset clears the bottom nav bar
(which is `h-16` = 64px, plus safe area). On click: fire the existing
`toast("Ask Tara is coming soon! 🪷")` pattern already used elsewhere
in the app.

**Acceptance criteria**:
- FAB visible on Today tab, correctly positioned above the bottom nav.
- Tapping shows a friendly "coming soon" toast.
- FAB does not appear on other tabs.

**Priority**: Low — visual placeholder only; high visibility but zero
functionality risk.

---

## Overview Tab Changes

### Issue O1 — Add Financial Snapshot section (replaces/augments existing summary)

**What exists today**: `OverviewTab.tsx` opens with `<BalanceBreakdown>`
(the stacked percentage bar) as its first section. The 4 key numbers
(Remaining, Income, Fixed Paid, Pending Bills) are available in
`summary.balance` but only shown in the bar segments and the
strip/flip-cards above, not as a dedicated section within the tab.

**What's missing**: A clean 2×2 grid of the 4 key numbers as the
Overview tab's opening section, before anything else — directly answering
"where do I stand?" without needing to read the breakdown bar. The
`BalanceBreakdown` bar can remain below this as a visual complement, not
as the primary information.

**Affected file(s)**:
- `frontend/react/src/components/tabs/OverviewTab.tsx`
- New component (optional, or inline):
  `FinancialSnapshotGrid` — 4 stat tiles

**Fix approach**: Add a new section as the first child of
`OverviewTab`'s return div, before `<BalanceBreakdown>`. Render 4 tiles
in a `grid-cols-2` layout:
- Remaining (`balance.remaining`, green if ≥ 0 else red)
- Income (`balance.total_income`, indigo)
- Fixed Paid (`balance.fixed_paid_total`, amber)
- Pending Bills (`balance.fixed_unpaid_total`, red if > 0 else muted
  green with a "✓ All clear" label)

Each tile: small label (10px Syne uppercase), large value (18px Syne
bold), subtle icon. Same card background as the rest of the tab.

**Acceptance criteria**:
- Overview tab opens with 4 key numbers visible immediately, no scroll.
- Values match what the existing SummaryStrip/flip-cards show for the
  same month.
- `BalanceBreakdown` bar still renders below as a secondary visual.

**Priority**: High — this is the Overview tab's equivalent of the Today
tab's hero card; it anchors everything else.

---

### Issue O2 — Add "This Month's Story" AI sentence

**What exists today**: No narrative summary anywhere on the Overview tab.

**What's missing**: A single AI-generated sentence that summarises the
month in plain English — e.g. "Most fixed commitments are complete, food
spending improved, and you're projected to finish with ₹8,400 remaining."
This is distinct from Tara's daily mantra (which is personal and
motivational) — this is a factual monthly summary, unbranded (no "From
Tara" attribution on Overview per Issue decision above).

**Affected file(s)**:
- `backend/ai_parser.py` — new function `generate_monthly_story()`
- `backend/main.py` — new endpoint `GET /insights/story/{month_key}`
- `frontend/react/src/types/index.ts` — new `MonthlyStory` type
- `frontend/react/src/components/tabs/OverviewTab.tsx` — new section

**Fix approach**:

`generate_monthly_story(context: dict) -> str`: similar pattern to
`generate_daily_mantra()` — compute numbers in Python, ask LLM for one
sentence only. Context:
```python
{
  "month_label": "June 2026",
  "remaining": 8400,
  "fixed_completion_pct": 95,   # fixed_paid / (fixed_paid + fixed_unpaid) * 100
  "top_category": "Miscellaneous",
  "top_category_spent": 27792,
  "variable_total": 48212,
  "days_left": 9,
}
```
Prompt: one factual sentence, max 35 words, past-tense framing for
completed items, forward-looking for projections, no motivational
language (this is a summary, not encouragement — that's Tara's job on
Today). Cache same-day in-memory keyed by `(user_id, month_key)` —
same pattern as `_mantra_cache`, but a separate dict since this is
per-month not per-day (a past month's story doesn't change once
generated).

`GET /insights/story/{month_key}` returns `{"story": "<sentence>"}`.

In `OverviewTab.tsx`, fetch this endpoint alongside the existing 4
parallel fetches in `load()`, add `story` to component state, render
below the Financial Snapshot grid (Issue O1) with a small "June in one
sentence" kicker label above the text.

**Acceptance criteria**:
- Overview tab shows a one-sentence month summary below the Financial
  Snapshot grid.
- Sentence references real numbers from the user's data.
- Sentence does not start with "I" or contain motivational language
  (this is factual summary, not encouragement).
- If the endpoint fails, the section simply doesn't render (same silent
  fail pattern as the mantra card).

**Priority**: High — this is the narrative anchor the feedback has asked
for across all three rounds; cheap to build given the LLM pattern
already exists.

---

### Issue O3 — Add Peace of Mind Score

**What exists today**: No score anywhere in the app. Discussed across all
three feedback rounds; deferred each time pending a formula decision.

**What's missing**: A score (0–100) computed from 4 sub-signals with a
one-line explanation ("Great going! Keep it up." / "A few bills are
pending." etc.) and a "Why this score?" expand showing the sub-signal
breakdown.

**Formula (to confirm before implementation)**:

| Sub-signal | Weight | Condition |
|---|---|---|
| Bills paid | 35 pts | `fixed_unpaid_total == 0` → 35, else `35 * (fixed_paid / (fixed_paid + fixed_unpaid))` |
| Remaining buffer | 30 pts | `remaining / total_income`: ≥ 20% → 30, 10–20% → 20, 5–10% → 10, < 5% → 0 |
| Spending pace | 20 pts | `variable_total / (total_income * 0.4)`: ≤ 80% → 20, 80–100% → 10, > 100% → 0 |
| Tracking consistency | 15 pts | Placeholder: 15 pts always, until streak tracking is built (spec 07 Phase 2 deferred item) |

Total: 0–100. Thresholds for label: ≥ 80 → "Great going!", 60–79 →
"On track, keep it up.", 40–59 → "A few areas need attention.", < 40 →
"Let's get back on track."

**⚠️ User must confirm these weights before implementation begins.**
The formula above is the suggested default — if any weight feels wrong
(e.g. "spending pace" at 20pts seems too harsh given variable income
months), adjust before building. A wrong formula is worse than no score.

**Affected file(s)**:
- `backend/budget_rules.py` — new `compute_peace_of_mind(balance: dict)
  -> dict` helper (returns `score`, `label`, `breakdown`)
- `backend/main.py` — expose via `GET /insights/peace-of-mind/{month_key}`
  OR fold into `GET /summary/{month_key}` response (simpler — avoids a
  new endpoint)
- `frontend/react/src/types/index.ts` — extend `Summary` or new type
- `frontend/react/src/components/tabs/OverviewTab.tsx` — new section

**Fix approach**: Compute in `budget_rules.py` (pure Python, no LLM —
this is rules-based, not AI-generated). Return `{"score": 84, "label":
"Great going!", "breakdown": {"bills": 35, "buffer": 25, "pace": 16,
"tracking": 15}}`. Fold into `/summary/{month_key}` response to avoid
a new network call. In `OverviewTab.tsx`, render as a card showing the
score prominently (large Syne bold, `--success` green) with the label
below and a "Why this score?" expand that shows the 4 sub-signals as a
simple list with their points.

**Acceptance criteria**:
- Score shown on Overview tab, computed from real user data.
- Score changes meaningfully between a month with all bills paid vs.
  a month with pending bills.
- "Why this score?" expands to show the 4 sub-signal breakdown.
- Tracking sub-signal is always 15/15 until streak tracking is built
  (noted as a placeholder in the breakdown display itself).

**Priority**: Medium — genuinely compelling feature, but blocked on
formula confirmation. Do not implement with a placeholder formula.

---

### Issue O4 — Add Financial Pulse section (Overview only)

**What exists today**: Nothing equivalent in `OverviewTab.tsx`.

**What's missing**: 4 signal tiles — Bills, Food, Spending, Tracking —
each with a green/amber/red indicator and a 1-2 word status label.

**Signals computation**:
- **Bills**: `fixed_unpaid_total == 0` → green "On Track" / else amber
  "X pending"
- **Food**: compare `spent_by_cat["Food"]` to previous month's food
  spend (available from MoM data already fetched in `OverviewTab`'s
  `load()`) — ≤ 100% of prev → green "Healthy" / 100–130% → amber
  "Slightly High" / > 130% → red "High"
- **Spending**: `variable_total / days_elapsed` vs `variable_total_prev
  / days_in_prev_month` daily rate comparison — ≤ 110% → green
  "Healthy" / 110–130% → amber "Above Avg" / > 130% → red "High"
- **Tracking**: placeholder green "Consistent" with "X-day streak"
  sub-label (static "tracking" label until streak is built, same as
  Peace of Mind)

All 4 signals are computable from data `OverviewTab` already fetches
(`summary`, `mom`) — no new backend endpoint needed.

**Affected file(s)**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — new
  `FinancialPulse` section, using existing state

**Fix approach**: Inline component in `OverviewTab.tsx` (no separate
file needed — it's a simple 2×2 grid of tiles, each tile having a dot,
a name, a status label, and a sub-label). Compute the 4 signals from
`summary` and `mom` state already in scope.

**Acceptance criteria**:
- 4 tiles visible on Overview tab, each with a real computed signal.
- Food tile correctly reflects comparison to previous month when MoM
  data exists; shows neutral "–" when no previous month data.
- Tracking tile shows a placeholder consistent state with a static
  sub-label noting streak tracking is coming.

**Priority**: Medium — visually compelling, all data already available,
no new backend work.

---

### Issue O5 — Replace MoM table with "What Changed?" compact rows

**What exists today**: `OverviewTab.tsx` Section 5 renders `<MoMTable
mom={mom} />` — a dense horizontal-scrolling table of all categories
across 3 months. The feedback document explicitly says to remove this
from the main overview screen.

**What's missing**: A compact, readable replacement: 3-4 highlighted
rows showing the most significant month-over-month changes, each with
a direction icon (↑ green / ↓ context-dependent), a plain-English label,
and the absolute or percentage change. A "vs [Previous Month]" label in
the section header.

**Affected file(s)**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — replace
  `<MoMTable>` with a new inline `WhatChanged` section
- `frontend/react/src/components/shared/MoMTable.tsx` — keep the
  component (don't delete); it may be reused in History or a future
  "View details" expansion

**Fix approach**: From the existing `mom` state (already fetched), derive
the top 3-4 most significant changes between `months[1]` (previous) and
`months[2]` (current). Significance = absolute ₹ change, descending.
For each: determine direction (up/down), compute % change, render as a
row with a coloured circle-icon, description string, and value. Color
logic: decreasing spend → green (saving), increasing spend → red
(spending more), unless the category is "Savings" or "Investments" where
the logic inverts. Cap at 4 rows; add a small "View all →" link that
could expand the full MoMTable in a future iteration (for now, the link
can be present but non-functional or open a toast "Full breakdown coming
soon").

**Acceptance criteria**:
- MoM dense table no longer appears on the main Overview screen.
- "What Changed?" section shows 3-4 rows of the most significant
  category changes.
- Each row has a direction icon, plain-English label, and ₹ or %
  change value.
- Colour logic correctly inverts for savings/investment categories.

**Priority**: High — the MoM table is the most consistently criticised
element across all feedback rounds; replacing it with compact rows is
a frontend-only change using existing data.

---

### Issue O6 — Add Upcoming Reality section

**What exists today**: No "upcoming bills" or "month-end projection"
card on the Overview tab. The data exists: `fixed_unpaid_total` is in
`summary.balance`, and `/insights/projection/{month_key}` returns
per-category projected spend including `days_left`. Month-end remaining
can be estimated as `remaining - fixed_unpaid_total`.

**What's missing**: A side-by-side card (or stacked on narrow screens)
showing: next due bill (vendor name + amount + days until due) and
expected month-end balance.

**Affected file(s)**:
- `backend/main.py` — the existing `GET /insights/due-reminders/
  {month_key}` endpoint already returns due reminders with `vendor`,
  `amount`, `due_day`, `days_overdue`; re-use this, the frontend just
  needs to fetch it
- `frontend/react/src/components/tabs/OverviewTab.tsx` — new section,
  new fetch in `load()`

**Fix approach**: Add `GET /insights/due-reminders/{selMonth}` to
`OverviewTab`'s parallel fetch in `load()`. From the response, take the
first item (most imminent due bill). Compute estimated month-end balance:
`remaining - fixed_unpaid_total` (simple, no new endpoint). Render as
a compact card: top row shows next due bill (calendar icon, vendor,
amount, "in X days"), divider, bottom row shows "Expected month-end
balance: ₹X" in green.

**Acceptance criteria**:
- Upcoming Reality card shows real next-due bill data when unpaid bills
  exist.
- When all bills are paid (`fixed_unpaid_total == 0`), the bill row
  shows "All bills paid this month ✓" in green instead.
- Month-end balance estimate is `remaining - fixed_unpaid_total`.

**Priority**: Medium — data already exists, mostly a frontend layout
addition.

---

### Issue O7 — Add Tiny Win section

**What exists today**: No "achievement" or "milestone" card on Overview.

**What's missing**: A single "Tiny Win" card at the bottom of Overview
showing a positive milestone for the month. Examples: "Lowest
miscellaneous spend in 3 months", "All fixed bills paid by mid-month",
"Food spending down for the second month in a row."

**Affected file(s)**:
- `backend/main.py` — new endpoint `GET /insights/tiny-win/{month_key}`
- `backend/ai_parser.py` — new function `generate_tiny_win(context)`
  OR rules-based (no LLM) for Phase 1
- `frontend/react/src/components/tabs/OverviewTab.tsx`

**Fix approach**: Rules-based for Phase 1 (no LLM cost). Check a small
ordered list of conditions against current month's data:
1. `fixed_unpaid_total == 0` and `days_left > 5` → "All bills cleared
   with {days_left} days to spare."
2. Food spend < previous month's food spend → "Food spending is down
   from last month."
3. `remaining / total_income > 0.15` → "You're keeping over 15% of
   income available — solid buffer."
4. Fallback: "You've been tracking consistently. That itself is
   progress."

Return the first condition that matches. No LLM call, no new model
cost. Render as a card with a trophy icon (amber), "Tiny Win" heading,
and the one-line message. A chevron-right on the card is decorative
for now (no detail view yet).

**Acceptance criteria**:
- Tiny Win card appears at the bottom of Overview with a real,
  condition-matched message.
- Falls back gracefully to the tracking message when no other condition
  matches.
- Card has trophy icon, "Tiny Win" heading, message.

**Priority**: Low — a delightful addition, purely additive, rules-based
so no LLM cost, but lowest functional value of the new sections.

---

## Explicitly out of scope

- **Ask Tara chat backend** — FAB and button are shells only.
- **Streak tracking** — Tracking signal in Financial Pulse and Peace of
  Mind use a placeholder; real streak computation deferred.
- **Time-of-day empty state insight** ("You usually log at 10:30 AM") —
  requires behavioral analytics not yet built; replaced with static
  friendly copy.
- **Peace of Mind arc/gauge chart** — the reference mockup shows a
  semicircle gauge; for Phase 1 a large number + label is sufficient.
  The arc chart is a visual enhancement for a future pass.
- **Multiple Tara avatar states** (eyes-open vs. eyes-closed variants
  on different tabs) — one asset (`tara.png`) used only on Today tab.
- **"View all" MoM table expansion** — "View all →" link present but
  non-functional; full expansion is a future feature.
- **Monthly Reflection / Letters from your wallet** — deferred since
  spec 06.

---

## Files NOT modified by this spec
- `backend/budget_rules.py` — modified only for Issue O3 (Peace of
  Mind helper); all other backend issues use `main.py` only.
- `frontend/react/src/components/shared/MoMTable.tsx` — kept as-is,
  just no longer rendered on the main Overview screen (Issue O5).
- `frontend/react/src/components/shared/BudgetHealthCard.tsx` —
  unchanged; the existing Budget Health section stays on Overview,
  just lower in the page order.
- `frontend/react/src/components/shared/SummaryStrip.tsx` and
  `SummaryFlipCard.tsx` — unchanged; still used on Fixed and Overview
  tabs.

---

## Implementation Order

| # | Issue | Priority | Effort | Type | Depends on |
|---|-------|----------|--------|------|------------|
| T1 | Hero balance card + 3 chips | High | ~2h | Frontend | — |
| T2 | Tara avatar + Ask Tara button in mantra card | High | ~1h | Frontend + asset | — |
| O1 | Financial Snapshot grid on Overview | High | ~1h | Frontend | — |
| O5 | Replace MoM table with What Changed? rows | High | ~2h | Frontend | — |
| O2 | This Month's Story AI sentence | High | ~2h | Backend + Frontend | — |
| T3 | Today empty state + suggestion chips | Medium | ~45min | Frontend | — |
| O4 | Financial Pulse on Overview | Medium | ~1.5h | Frontend | — |
| O6 | Upcoming Reality card | Medium | ~1h | Frontend (reuses existing endpoint) | — |
| O3 | Peace of Mind Score | Medium | ~2h | Backend + Frontend | Formula confirmed by user |
| T4 | Ask Tara FAB (shell only) | Low | ~20min | Frontend | — |
| O7 | Tiny Win card | Low | ~1.5h | Backend + Frontend | — |

**Recommended implementation sequence**: T1 + T2 first (Today tab
hero and mantra card — highest visibility, zero backend risk), then O1
+ O5 (Overview anchors, frontend-only), then O2 (first new backend
work), then T3 + O4 + O6 together (medium-effort, all frontend or
reusing existing endpoints), then O3 once formula is confirmed, then
T4 + O7 last (lowest risk, smallest blast radius).
