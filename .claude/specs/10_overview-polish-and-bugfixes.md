# Spec: Overview Page Polish + Bug Fixes
**Date**: 2026-06-26
**Status**: ✅ Complete — All 8 items done (Items 1–7: 2026-06-26; Item 8: 2026-06-27)
**Branch**: `feature/sprint06261-ui-enhancement` (continue on same branch)
**Follows**: `09_overview-refinement.md` — implement spec 09 items first, then this spec.

## Context

After reviewing a second visual mockup (`ChatGPT_Image_Jun_26__2026__05_06_15_PM.png`) alongside two feedback documents (`Wallet_Mantra_Peace_of_Mind_and_Spending_Signals_Feedback.md` and `Wallet_Mantra_Peace_of_Mind_and_Spending_Signals_Feedback2.md`), several gaps in spec 09 were identified alongside three bugs reported by the user.

The second mockup significantly raises the bar in four areas not covered by spec 09:
1. Peace of Mind score breakdown and delta movement
2. Budget Health renamed to Spending Signals with traffic-light 3-card design
3. Top Spends renamed to Money Moments with contextual purchase badges
4. Monthly Breakdown Insight row — achievable with 2-month average (not 6), unblocking the R6 deferral

Three bugs are also captured here:
- B1: June in One Sentence shows stale savings figure after transaction edits (cache invalidation)
- B2: Spend by Category filter tab says "Day-to-day" — should be "Variable"
- B3: Due-reminders label shows "-2d overdue" for future bills (sign logic bug)

**All open decisions resolved 2026-06-26:**
1. "What Changed?" — kept as standalone section at position 9 (after Money Moments)
2. Spending Signals "View all" — full bottom-sheet modal built this sprint (not a toast)
3. Money Moments "View all" toast copy — "See all transactions in the History tab →"

**Responsive layout confirmed 2026-06-26:**
- Two section pairs sit side-by-side at ≥ 580px (desktop browser): Monthly Breakdown + Spend by Category; Peace of Mind + Spending Signals
- Both pairs stack to single column below 580px (iPhone Safari)
- Implemented with Tailwind `md:grid-cols-2` (or CSS `@media(min-width:580px)`)
- All other sections remain full-width single column at all viewport sizes

---

## Bug B1 — "June in One Sentence" shows stale data after expense reshuffle

**Symptom**: User moved savings transactions; the story sentence still quoted the old savings figure (₹36,062) instead of the updated amount.

**Root cause**: `_story_cache` in `backend/main.py` is keyed by `(user_id, month_key)` and never invalidated. Once generated, the story is served from cache regardless of subsequent expense changes.

**Fix**: Add a helper `_invalidate_month_caches(user_id, month_key)` that deletes from both `_story_cache` and `_mantra_cache` if the key exists. Call this helper at the end of every expense mutation endpoint (`POST /expenses`, `PUT /expenses/{id}`, `DELETE /expenses/{id}`).

**Affected files**:
- `backend/main.py` — add `_invalidate_month_caches()` helper; call it in all three expense mutation endpoints

**Acceptance criteria**:
- After editing or deleting an expense, the next load of June in One Sentence fetches a freshly generated sentence.
- Cache invalidation does not affect other months' cached stories.
- `_mantra_cache` is also invalidated on expense mutation via the same helper.

**Priority**: High — data integrity issue visible to the user.

---

## Bug B2 — Spend by Category filter tab says "Day-to-day" — should be "Variable"

**Symptom**: Filter tab reads "Day-to-day" instead of "Variable".

**Fix**: Find the string `"Day-to-day"` in the Spend by Category filter tab and replace with `"Variable"`.

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` (or the relevant child component)

**Acceptance criteria**:
- Filter tab reads "Variable | Fixed Bills | All".
- Filter logic unchanged.

**Priority**: Low — one-line cosmetic fix.

---

## Bug B3 — Due-reminders label shows overdue for future bills

**Symptom**: Term Insurance due on the 28th shows "-2d overdue" when today is the 26th.

**Root cause**: Label logic treats any non-zero `days_overdue` as past-due without checking the sign.

**Fix**:
```
days_overdue < 0  → "Due in {Math.abs(days_overdue)} day(s)"
days_overdue === 0 → "Due today"
days_overdue > 0  → "{days_overdue} day(s) overdue"
```
Sort reminders ascending by `days_overdue`. Show first item where `days_overdue <= 0`; fall back to the most overdue if all are past due.

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — Upcoming Reality label logic and sort order

**Acceptance criteria**:
- Bill due in 3 days shows "Due in 3 days".
- Bill due today shows "Due today".
- Bill 2 days past due shows "2 day(s) overdue".
- Sort order surfaces the next upcoming bill first.

**Priority**: High — factually incorrect information shown to the user.

---

## Issue R7 — Peace of Mind: score breakdown + delta movement

**What spec 08/09 planned**: Single score (0–100) with summary line and expandable "Why this score?" panel.

**What the mockup shows**: Richer card with circular dial, inline factor breakdown always visible, and score delta vs yesterday.

**Backend — extend `/insights/peace-of-mind/{month_key}` response**:

```python
{
  "score": 68,
  "summary": "Your finances are stable but three areas need attention.",
  "delta": 3,       # int or null; positive = improved, negative = declined
  "factors": [
    { "label": "Bills paid on time",        "points": 25 },
    { "label": "Positive remaining balance","points": 20 },
    { "label": "Consistent tracking",       "points": 15 },
    { "label": "Grocery overspend",         "points": -15 },
    { "label": "Shopping overspend",        "points": -10 },
    { "label": "Pending bills",             "points": -16 },
  ]
}
```

**Factor derivation rules** (rules-based):

Positive:
- "Bills paid on time" → `+round(25 * fixed_paid / (fixed_paid + fixed_unpaid))`, max +25
- "Positive remaining balance" → +20 when `remaining > 0`, else 0
- "Consistent tracking" → +15 always (placeholder — `// TODO: replace with real streak`)

Negative (only when condition triggers; omit otherwise):
- Top 2 overspent budget categories → `-round(min(15, overspent / budget * 10))` each, labelled "{Category} overspend"
- "Pending bills" → `-round(min(16, fixed_unpaid_total / total_income * 100))` when `fixed_unpaid_total > 0`

Total = 60 (base) + sum of all factor points, clamped to [0, 100].

**Delta**: Store computed score in `_score_history: dict[tuple, int]` keyed by `(user_id, month_key, date_str)`. Compare today vs yesterday. Return `null` if no prior score.

**Summary line** (rules-based):
- 0 negative factors → "Your finances are on track this month."
- 1–2 → "Your finances are stable but {N} area(s) need attention."
- 3+ → "A few areas need your attention this month."

**Frontend**:
- Extend `PeaceOfMind` type: add `delta: number | null`, `factors: {label: string, points: number}[]`, `summary: string`
- Redesign card:
  - SVG circular dial using `stroke-dasharray` — colour: ≥70 → `#34d399`, 40–69 → `#f59e0b`, <40 → `#f87171`
  - Score + "/100" centred in dial
  - Delta badge: "↑ {n} pts vs yesterday" green / "↓ {n} pts" red / omitted when null
  - Factor list always visible: positive factors first (green `+N`), then negative (red `−N`)
  - "Why this score?" expand toggle — shows methodology text only, not a repeat of factors

**Responsive**: Peace of Mind card is the left panel of the second pair (sits beside Spending Signals at ≥580px).

**Affected files**:
- `backend/main.py` — extend endpoint response; add `_score_history`; factor derivation logic
- `frontend/react/src/types/index.ts` — extend `PeaceOfMind` interface
- `frontend/react/src/components/tabs/OverviewTab.tsx` — redesign card

**Acceptance criteria**:
- Dial colour reflects score range correctly.
- All factors shown inline without needing to expand.
- Delta shows correctly or is omitted when null.
- Summary line matches negative factor count.
- Score clamped to [0, 100].

**Priority**: High.

---

## Issue R8 — Rename Budget Health → Spending Signals; top-3 traffic-light design + "View all" modal

**What exists**: `BudgetHealthCard` renders all categories with extendable progress bars.

**What the mockup shows**: "Spending Signals" — 3 cards (one red/over, one amber/watch, one green/on-track), no progress bars, with "View all →" opening a full bottom-sheet modal.

**Signal selection**:
- Sort all budgeted categories by `spent / budget` descending.
- Take: highest ratio (red), second highest (amber), lowest with spend > 0 (green).

**Traffic light thresholds**:
- 🔴 `spent > budget` → badge "Over by ₹{spent − budget}", colour `#f87171`
- 🟡 80–100% → badge "Almost full", colour `#f59e0b`
- 🟢 < 80% → badge "On track", colour `#34d399`

**Daily rate** (right side of each card):
- Under budget: `₹{round((budget − spent) / days_left)}/day left`
- Over budget: omit daily rate, show overage amount instead

**"View all" bottom-sheet modal** (`SpendingSignalsModal`):
- `fixed inset-x-0 bottom-0 max-h-[85vh]` with drag handle and backdrop
- Shows ALL budgeted categories as traffic-light cards (same component, no limit)
- Close on backdrop tap or swipe down
- No new data fetch — reuses budget data already in scope

**Responsive**: Spending Signals card is the right panel of the second pair (beside Peace of Mind at ≥580px).

**Affected files**:
- `frontend/react/src/components/shared/BudgetHealthCard.tsx` — full redesign or replace with inline JSX
- `frontend/react/src/components/shared/SpendingSignalsModal.tsx` — new file
- `frontend/react/src/components/tabs/OverviewTab.tsx` — section heading, modal trigger state

**Acceptance criteria**:
- Section reads "Spending Signals" with "View all →".
- Exactly 3 cards: one each red/amber/green (fewer if fewer budgeted categories exist).
- No progress bars.
- "View all →" opens bottom-sheet modal showing all budgeted categories.
- Modal closes on backdrop tap.

**Priority**: High.

---

## Issue R9 — Rename Top Spends → Money Moments with context badges

**What exists**: "Top Spends This Month" — ranked list of 5 largest transactions.

**What the mockup shows**: "💎 Money Moments" — same 5 transactions with summary line, rank badges, and context badges.

**Context badge rules** (frontend-only, first matching rule wins):
| Badge | Condition |
|-------|-----------|
| 🏆 Biggest Purchase | Rank 1 always |
| 📈 Investment | Category in ["Savings", "Investments", "Mutual Fund"] |
| 📚 Learning Investment | Category in ["Course", "Education"] |
| 🚗 Essential Spend | Category in ["Travel", "Medical", "Rent", "Cook", "Milk", "Electricity"] |
| ❤️ Special Moment | Category is "Gifts" |
| 👑 Top Spend | Rank 2, no other badge matched |
| — | All others — no badge |

**Summary line**: `"Largest 5 purchases contributed {X}% of this month's spending."` where `X = round(sum_top5 / balance.variable_total * 100)`. Omit when `variable_total === 0`.

**"View all" toast**: `"See all transactions in the History tab →"`

**Backend**: Verify existing top-spends endpoint returns `vendor`, `category`, `date`, `amount`. No changes expected.

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — rename, summary line, badge logic

**Acceptance criteria**:
- Heading reads "💎 Money Moments" with "View all →".
- Summary line present when `variable_total > 0`.
- Each row: rank, icon, vendor, category + date, amount, % of total spending, context badge.
- Rank 1 always gets 🏆 regardless of category.
- "View all →" fires toast: "See all transactions in the History tab →".

**Priority**: Medium.

---

## Issue R10 — Un-defer Monthly Breakdown Insight row (2-month average)

**Root cause**: Spec 09 R6 deferred this as needing 6-month aggregation. The mockup uses 2-month average — achievable with a single additional `/summary/{prevMonthKey}` call.

**Frontend**:
- Derive `prevMonthKey` from `selMonth` (handle Jan→Dec rollover).
- Add to `load()`'s Promise.all: `api.get(\`/summary/${prevMonthKey}\`).then(r => r.data).catch(() => null)` → `prevSummary` state.
- Compute `currVarPct` and `prevVarPct` from respective `balance.variable_total / balance.total_income`.
- Render below `<BalanceBreakdown>`:
  - "⚡ INSIGHT" label
  - "Variable spending consumed {currVarPct}% of income this month."
  - When `prevVarPct` available: "Your average over the last 2 months is {round((curr+prev)/2)}%."
  - When not: "No prior month data to compare."
- Remove the `// TODO: Insight row — see spec 09 R6` comment.

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx`

**Acceptance criteria**:
- Insight row renders below the BalanceBreakdown bar.
- 2-month average shown when prior month data available; fallback message otherwise.
- No crash when prior month returns null.
- TODO comment removed.

**Priority**: Medium.

---

## Issue R11 — Final section order + responsive pairs (supersedes spec 09 R3)

**Canonical section order**:

| # | Section | Layout |
|---|---------|--------|
| 1 | Financial Snapshot | Full width (2×2 grid) |
| 2 | June in One Sentence | Full width |
| 3+4 | Monthly Breakdown + Insight ∥ Spend by Category + Winner | **Responsive pair** — side-by-side ≥580px, stacked below |
| 5+6 | Peace of Mind ∥ Spending Signals | **Responsive pair** — side-by-side ≥580px, stacked below |
| 7 | Upcoming Reality | Full width |
| 8 | Money Moments | Full width |
| 9 | What Changed? | Full width (2×2 grid) |
| 10 | Financial Pulse | Full width (2×2 grid) |
| 11 | Tiny Win | Full width |
| — | Tara footer strip | Full width |

**Responsive pair implementation** (Tailwind):
```tsx
<div className="grid grid-cols-1 md:grid-cols-2 gap-3 px-4 mt-4">
  <div>/* left section */</div>
  <div>/* right section */</div>
</div>
```
Where `md:` breakpoint is 640px by default — adjust Tailwind config to 580px if needed, or use inline `@media` style.

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — reorder and wrap pairs

**Acceptance criteria**:
- Section order matches table above exactly.
- At ≥580px: pairs 3+4 and 5+6 each render side-by-side in equal-width columns.
- At <580px: all sections stack single column.
- No section accidentally removed (count before and after reorder).
- Reorder done after R7, R8, R9, R10 are complete.

**Priority**: Low — do last.

---

## Implementation Order

| # | Issue | Type | Effort | Depends on |
|---|-------|------|--------|------------|
| 1 | B2 — "Variable" label | Frontend | XS | — |
| 2 | B3 — Due-reminders sign logic | Frontend | XS | — |
| 3 | B1 — Story cache invalidation | Backend | S | — |
| 4 | R10 — Insight row (2-month avg) | Frontend | S | — |
| 5 | R9 — Money Moments badges | Frontend | S | — |
| 6 | R8 — Spending Signals + modal | Frontend | M | — |
| 7 | R7 — Peace of Mind breakdown | Backend + Frontend | M | — |
| 8 | R11 — Section reorder + responsive pairs | Frontend | S | Items 4–7 done |

---

## Open decisions — all resolved

| Decision | Resolution | Date |
|----------|-----------|------|
| "What Changed?" standalone vs inline | Keep as standalone at position 9 | 2026-06-26 |
| Spending Signals "View all" | Full bottom-sheet modal this sprint | 2026-06-26 |
| Money Moments "View all" copy | "See all transactions in the History tab →" | 2026-06-26 |
| Financial Pulse layout | 2×2 tile grid (confirmed) | 2026-06-26 |
| Responsive layout approach | Responsive pairs for sections 3+4 and 5+6; breakpoint 580px | 2026-06-26 |

---

## Files NOT modified by this spec
- `backend/ai_parser.py` — no changes (Tara stays Today-only per spec 09 R4)
- `frontend/react/src/components/shared/SummaryStrip.tsx` / `SummaryFlipCard.tsx` — unchanged
- `frontend/react/src/components/shared/MoMTable.tsx` — unchanged (removed by spec 08)
