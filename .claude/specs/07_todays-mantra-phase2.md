# Spec: Today's Mantra — Phase 2 (richer context + insight variation + "Why?")
**Date**: 2026-06-22
**Status**: Open — awaiting implementation

## Context

Phase 1 (`.claude/specs/06_todays-mantra-phase1.md`, implemented
2026-06-22) shipped a single daily mantra card on the Today tab. Follow-up
feedback after using the shipped feature converged on one precise
diagnosis: the generated sentence is structurally limited to a single
"remaining ÷ days left" calculation, because that's literally all the data
`generate_daily_mantra()`'s `context` dict contains today. No matter how
the prompt is worded, the substance can't vary day to day because the
underlying numbers don't either (until the user logs new expenses).

Verified directly against the implemented code
(`backend/main.py`'s `daily_mantra()` endpoint): the context passed to the
LLM is `remaining, days_left, daily_budget, total_income, top_category,
top_category_spent` — five numbers, all from a single point-in-time
snapshot of the *current* month. There is no month-over-month comparison
anywhere in this context, despite the data existing elsewhere in the
codebase (`/insights/mom/{month_key}` already computes exactly this
comparison for the Overview tab's Month-over-Month table). There is also
no concept of a logging streak anywhere in the schema — that part of the
feedback's wishlist is genuinely new, not just unwired.

**This spec scopes Phase 2 down to what's buildable from data that mostly
already exists**, deliberately leaving out anything requiring new
multi-month pattern-recognition logic or a second generation pass. See
"Explicitly out of scope" below — the same discipline Phase 1 applied to
the original two feedback rounds applies here to round three.

---

## Issue 1 — Mantra context is missing month-over-month comparison data that already exists elsewhere

**What exists today**: `daily_mantra()` in `backend/main.py` builds its
context from `get_balance_summary()` and
`get_monthly_spent_by_category()` only — both scoped to the current month.
Separately, `month_over_month()` (the `/insights/mom/{month_key}`
endpoint, same file) already computes per-category spend across the
current month and the two preceding months, in the exact shape needed for
a comparison (`data[category][month_key] = total`). These two code paths
have never been connected.

**What's missing**: A previous-month total for at least the user's top
category (or ideally a couple of categories), passed into
`generate_daily_mantra()`'s context so the prompt has something to compare
against. Without this, sentences like "you spent less on food than last
month" are not stylistic choices the prompt is failing to make — they are
factually unavailable to generate.

**Affected file(s)**:
- `backend/main.py` — `daily_mantra()` endpoint needs to compute a
  previous-month comparison before calling `generate_daily_mantra()`
- `backend/ai_parser.py` — `generate_daily_mantra()`'s context dict and
  prompt need new optional fields

**Fix approach**: Inside `daily_mantra()`, after computing `top_category`
the same way it already does, also fetch the previous month's spend for
that same category. The previous month's key can be derived the same way
`month_over_month()` already does it (subtract one from the current
`month_key`, handling year rollover) — reuse that exact logic rather than
reinventing it, ideally by calling `get_monthly_spent_by_category()` a
second time with the previous month's key (this function already exists
and is already imported in `main.py`; no new query logic needed beyond
computing the previous month-key string).

Add to the context dict:
```python
"top_category_prev_month_spent": <float or None>,
```
`None` (or omitted) when there's no previous-month data at all (e.g. a
new user, or month 1 of usage) — the prompt must handle this gracefully,
not assume the field is always present.

Update `generate_daily_mantra()`'s prompt to include this figure when
present, and explicitly instruct the model: only make a comparison claim
when the previous-month figure is actually provided; never imply a trend
it wasn't given data for. This directly addresses the original Phase
1 spec's own caution about not inventing trend claims the model has no
basis for — Phase 2 doesn't relax that caution, it just gives the model
one more real number to work with when available.

**Acceptance criteria**:
- When previous-month data exists for the top category, the generated
  mantra is capable of (not guaranteed to, since phrasing is still the
  model's choice) referencing a real comparison, e.g. "less than last
  month" or "more than last month," grounded in actual numbers passed in.
- When no previous-month data exists, the mantra still generates
  successfully (no error) and makes no comparison claim.
- No fabricated comparisons — every comparative statement in a generated
  sentence must be traceable to a real number in the context dict.

**Priority**: High — this is the actual prerequisite everything else in
this spec and in the feedback's "rotate insight types" idea depends on.

---

## Issue 2 — Mantra never reflects "all fixed commitments covered," despite the data already being computed

**What exists today**: `get_balance_summary()` (in `budget_rules.py`,
unchanged, already called by `daily_mantra()`) returns
`fixed_unpaid_total` in its response dict. `daily_mantra()` currently
discards this value — only `remaining` and `total_income` are pulled out
of the balance dict into the mantra context.

**What's missing**: Surfacing `fixed_unpaid_total == 0` as a fact the
prompt can choose to lead with. This is the cheapest possible win in this
spec — the number is already computed, already available in a variable
`daily_mantra()` already has in scope; it just isn't passed through.

**Affected file(s)**:
- `backend/main.py` — `daily_mantra()`, one additional context field
- `backend/ai_parser.py` — `generate_daily_mantra()`, prompt update

**Fix approach**: Add `"fixed_unpaid_total": balance["fixed_unpaid_total"]`
to the context dict (the variable `balance` already exists in scope in
`daily_mantra()` — this is a one-line addition, not a new query). Update
the prompt to note: if `fixed_unpaid_total` is 0, this is worth
highlighting ("everything remaining is a choice, not an obligation," per
the feedback's own example) — but only as one possible angle, not a
forced inclusion every time, to avoid the rotation problem this whole
spec exists to solve.

**Acceptance criteria**: When a user has fully paid all fixed expenses for
the month, the mantra is capable of reflecting that fact when it's the
most relevant thing to say that day.

**Priority**: Medium — very cheap (one field, already computed), genuinely
useful, but a smaller piece of the puzzle than Issue 1.

---

## Issue 3 — No variation mechanism; same "type" of insight could repeat indefinitely

**What exists today**: `generate_daily_mantra()`'s prompt asks for one
sentence with no instruction about *what kind* of sentence relative to
what was said previously. Nothing tracks what was said on prior days.

**What's missing**: Some lightweight signal so the prompt doesn't default
to the same shape of sentence (e.g. always a forecast) every single day.
The feedback's "Tara Mood Types" enum (CELEBRATION, PATTERN, FORECAST,
REMINDER, ACHIEVEMENT, REFLECTION) is the right shape of idea, but most of
those categories need data this spec doesn't build (PATTERN and
ACHIEVEMENT specifically need streak/multi-month trend detection — see
"Explicitly out of scope"). This issue covers only what's achievable with
Issue 1 and Issue 2's data: a forecast angle (existing), a comparison
angle (Issue 1, when available), and a "commitments covered" angle (Issue
2, when true).

**Affected file(s)**:
- `backend/main.py` — `daily_mantra()`, lightweight type-tracking
- `backend/ai_parser.py` — `generate_daily_mantra()`, prompt update

**Fix approach**: Reuse the existing `_mantra_cache` dict (already
in-memory, per-process, keyed by `(user_id, date)`) rather than building
new persistent storage — extend it minimally to also remember which
"angle" was used on the *previous* day for that user, so two consecutive
days don't pick the same one when more than one is available. This can be
as simple as a second small in-memory dict,
`_mantra_last_type: dict[int, str]`, storing the chosen type
(`"forecast" | "comparison" | "commitments"`) per user_id, checked before
generating and updated after. This deliberately mirrors Phase 1's own
choice to avoid new DB tables for Phase 1 — Phase 2 extends the same
lightweight, in-memory approach rather than introducing the persistent
`mantra_history` table the original feedback proposed.

In `daily_mantra()`, before calling `generate_daily_mantra()`: determine
which angles are *available* this run (forecast is always available;
comparison is available if Issue 1's previous-month data exists;
commitments is available if `fixed_unpaid_total == 0`). If more than one
is available and the last-used type for this user matches one of them,
prefer instructing the prompt toward a different available angle. Pass
the preferred angle as a hint in the prompt (e.g. "Today, prefer focusing
on: comparison" if that's what was picked), but the model still writes
the actual sentence — this is a soft steer, not a rigid template.

**Acceptance criteria**:
- Across two consecutive days where more than one angle is available
  (e.g. both a comparison and a forecast could be made), the generated
  mantras do not both lead with the same angle.
- When only one angle is available (e.g. no previous-month data and fixed
  expenses aren't fully paid), the mantra still generates normally — no
  error from having nothing to rotate between.
- This is best-effort variation, not a strict guarantee — acceptable if,
  over many days, sentences are noticeably more varied than Phase 1's
  single-shape output, not a formal proof of non-repetition.

**Priority**: Medium — meaningfully improves the experience but depends
entirely on Issues 1 and 2 existing first to have anything to rotate
between.

---

## Issue 4 — No way to see the numbers behind a mantra ("Why?")

**What exists today**: `TodaysMantraCard` (in `QuickAddTab.tsx`) renders
only the generated sentence — none of the underlying numbers used to
generate it are exposed to the frontend at all. The `GET
/insights/mantra/{month_key}` endpoint returns `{"mantra": "<sentence>"}`
only.

**What's missing**: A lightweight way for a curious user to see the real
numbers behind the sentence, without a second LLM call (which would
double the cost and latency of every card view). The feedback's example —
clicking "Why?" reveals "Food spending is ₹3,200 compared to your 3-month
average of ₹4,100" — is, on inspection, just a restatement of numbers the
backend already has in hand by the time it calls the LLM. This spec
implements that cheap version, not a second generation pass.

**Affected file(s)**:
- `backend/main.py` — `daily_mantra()` response shape
- `frontend/react/src/types/index.ts` — `DailyMantra` type
- `frontend/react/src/components/tabs/QuickAddTab.tsx` — `TodaysMantraCard`

**Fix approach**: Change `daily_mantra()`'s response to include the
context numbers alongside the sentence, not just the sentence:
```python
return {
    "mantra": mantra,
    "context": {
        "remaining": remaining,
        "days_left": days_left,
        "top_category": top_category,
        "top_category_spent": top_category_spent,
        "top_category_prev_month_spent": <value from Issue 1>,
        "fixed_unpaid_total": balance["fixed_unpaid_total"],
    },
}
```
Update `DailyMantra` in `types/index.ts` to match. In
`TodaysMantraCard`, add a small "Why?" toggle (text button, no icon
needed) below the sentence. On click, expand a small inline detail block
rendering the relevant numbers in plain text/labels (no new API call) —
e.g. "Top category: Food, ₹3,200 this month vs ₹4,100 last month."
Collapsed by default, matching the spec's general preference for the card
staying compact (per the original UI feedback round, the card should feel
like "a thought," not another data widget — keep the expanded state
simple, not a mini-dashboard).

**Acceptance criteria**:
- A "Why?" toggle appears below the mantra sentence.
- Clicking it reveals the actual numbers behind the sentence, with no
  additional network request.
- The detail view is collapsed by default and doesn't change the card's
  visual weight when collapsed.

**Priority**: Medium — clearly valuable per the feedback, cheap once
Issue 1's data exists in the response, but reasonably deferrable on its
own if time-constrained, since it doesn't change what the mantra says,
only what's available on demand.

---

## Issue 5 — Mantra card visual distinctness

**What exists today**: `TodaysMantraCard` uses the same
`bg-dark-card border border-white/10 rounded-2xl` styling as most other
cards in the app (e.g. matches the pattern used in `QuickAddTab.tsx`'s
own saved-expense cards). It currently has a "🪷 From Tara" label heading
in small caps, matching `BudgetHealthCard`'s general text styling.

**What's missing**: Nothing functionally — this is a pure visual
treatment request, independent of every other issue in this spec. Can be
implemented standalone, in any order, with no dependency on Issues 1–4.

**Affected file(s)**:
- `frontend/react/src/components/tabs/QuickAddTab.tsx` —
  `TodaysMantraCard` styling only

**Fix approach**: Adjust the card's visual treatment to read more like a
quoted thought than another analytics widget, per the feedback's specific
suggestions: a subtle accent glow (e.g. a soft box-shadow or gradient
border using the existing `--accent`/`--accent2` CSS variables already
defined in `index.css`, rather than introducing new colors), a thin
divider line between the heading and the sentence, and slightly more
generous padding/line-height than the app's denser data cards. Avoid
introducing a literal handwritten/script font — the app's existing
typography (`font-syne` for headings, default sans for body) should stay
consistent; "handwritten quote style" from the feedback is better
interpreted as italic body text and generous whitespace than an actual
font change, to avoid clashing with the rest of the app's typographic
system.

**Acceptance criteria**: The mantra card is visually distinguishable from
the app's standard data cards (donut chart card, budget health cards,
etc.) at a glance, while remaining consistent with the app's existing
color palette and typography — no new fonts, no new colors outside the
existing CSS variable set.

**Priority**: Low — purely cosmetic, but cheap and independent; can be
done first, last, or in parallel with everything else in this spec.

---

## Explicitly out of scope (deferred, not part of this spec)

- **True streak tracking** ("haven't missed a log in 24 days") — requires
  a new computation (likely a new small query: distinct dates with at
  least one expense logged, checked for consecutive-day runs) that
  doesn't exist anywhere in the schema today. Not free, unlike Issues 1–2
  which reuse existing data. Worth a future Phase 3 if streaks prove to be
  a compelling angle once basic variation (this spec) is in place.
- **"Salary-day spending spike" and other multi-month pattern detection**
  — same reasoning as Phase 1's original deferral: needs historical trend
  computation across many months that a small number of real users
  haven't generated enough data for yet to be reliable, and risks
  fabricating patterns from noise.
- **Monthly Reflection / "Money Memories"** — explicitly named and
  deferred in Phase 1's spec already; nothing in this round of feedback
  changes that reasoning. If anything, this being the third round of
  feedback before a full month of daily-mantra usage has elapsed is a
  small signal the original sequencing (prove the daily card first) was
  correct.
- **"Ask Tara" conversational layer** — still the largest single scope
  item across all three rounds of feedback; still deserves its own
  dedicated spec, not a sub-item here.
- **A second LLM call for "Why?"** — Issue 4 implements the cheap version
  (rendering numbers already in hand). A richer, separately-generated
  explanation is a different, costlier feature; not built here.
- **Persistent `mantra_history` / `TaraType` enum as a DB-backed system**
  — Issue 3 deliberately uses a second small in-memory dict rather than
  new schema, consistent with Phase 1's reasoning for avoiding new tables
  at this stage of usage.

---

## Files NOT modified by this spec
- `backend/budget_rules.py` — `get_balance_summary` and
  `get_monthly_spent_by_category` are reused as-is; no changes.
- `backend/models.py` — no schema changes; Phase 2 continues Phase 1's
  choice to avoid new tables.
- Any file outside `backend/main.py`, `backend/ai_parser.py`,
  `frontend/react/src/types/index.ts`, and
  `frontend/react/src/components/tabs/QuickAddTab.tsx`.

---

## Implementation Order

| # | Issue | Priority | Effort | Files | Depends on |
|---|-------|----------|--------|-------|------------|
| 1 | Month-over-month comparison data in mantra context | High | ~1.5h | `main.py`, `ai_parser.py` | — |
| 2 | Surface `fixed_unpaid_total` in context | Medium | ~20 min | `main.py`, `ai_parser.py` | — |
| 3 | Lightweight angle rotation | Medium | ~1h | `main.py`, `ai_parser.py` | Issues 1, 2 |
| 4 | "Why?" reveal (numbers, no new LLM call) | Medium | ~1h | `main.py`, `types/index.ts`, `QuickAddTab.tsx` | Issue 1 (for the comparison number to show) |
| 5 | Card visual distinctness | Low | ~30 min | `QuickAddTab.tsx` | — (independent) |

Issues 1 and 2 can be done together in one backend pass (both touch the
same function, same return-dict edit). Issue 3 only makes sense once both
exist. Issue 4 is frontend-adjacent and can follow once Issue 1's data is
in the response shape. Issue 5 has no dependencies and can be done at any
point, including first, if a quick visible win is wanted before the
backend work.
