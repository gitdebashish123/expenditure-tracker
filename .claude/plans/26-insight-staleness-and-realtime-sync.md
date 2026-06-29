# Implementation Plan: Insight/Story/Mantra Staleness + First-Month Comparison Fix
**Spec**: `.claude/specs/26_insight-staleness-and-realtime-sync.md`
**Date**: 2026-06-29
**Branch**: `feature/sprint06261-ui-enhancement` *(confirm active branch before starting)*
**Status**: ✅ Complete — all 4 items implemented 2026-06-29 (backend imports clean, `npm run build`/`tsc` pass)

---

## Overview

4 items total — **all 4 require backend changes**; 1 of those (Item 3) also touches the
frontend. Items are ordered smallest-blast-radius first.

Root issue: the three AI-narrative caches (`_story_cache`, `_insight_cache`, `_mantra_cache`
in `backend/main.py`) go stale because (a) most balance-affecting mutations never call
`_invalidate_month_caches`, (b) the mantra cache is stored under a *date* key but invalidated
under a *month* key (never matches), and (c) the current/live month is cached at all. A
separate logic bug makes first-month users see fabricated month-over-month comparisons.

**Verified divergences from the spec** (flagged during code read):
- Spec's mutation table is correct, but **two more endpoints also lack invalidation** and must
  be included: `POST /expenses/bulk-delete` (line 650) and the template editors
  `PUT /fixed-templates/{id}` (line 874) + `DELETE /fixed-templates/{id}` (line 913), both of
  which rewrite current+future-month `Expense` rows and therefore change the live balance.
- `update_template`/`delete_template` already mutate `Expense` rows for `month_key >= current`
  (multi-month), so they need the broad per-user invalidation, not a single-month call.

---

## Item 1 — Invalidate caches on every balance-affecting mutation
**Scope**: Backend-only
**Files**: `backend/main.py`

**Root cause**: `_invalidate_month_caches(user_id, month_key)` (defined line 1282) is called
**only** from the four expense-CRUD endpoints — `POST /expenses/parse` (584),
`POST /expenses/manual` (610), `PATCH /expenses/{id}` (644/646), `DELETE /expenses/{id}` (672).
Every other mutation that changes `get_balance_summary`'s output leaves the story/insight caches
populated with pre-mutation text. Confirmed by reading each endpoint — none of the following
call the invalidator:

| Endpoint | Line | `month_key` source | Affects |
|---|---|---|---|
| `PATCH /fixed/{id}/toggle` | 691 | `exp.month_key` | bills %, remaining → **Issue #1** |
| `PATCH /fixed/{id}/amount` | 704 | `exp.month_key` | fixed totals, remaining |
| `POST /income` | 1022 | `month_key` (local var, line 1025) | income, remaining → **Issue #2** |
| `PUT /income/{id}` | 1078 | `entry.month_key` | income, remaining → **Issue #2** |
| `DELETE /income/{id}` | 1062 | `entry.month_key` (capture before delete) | income, remaining → **#2** |
| `POST /expenses/bulk-delete` | 650 | per-row `exp.month_key` (collect set) | variable totals |
| `PUT /budget` | 992 | not month-scoped → all-user | insight caps context |
| `POST /pools/{id}/entries/{month}` | 1773 | `month_key` (path param) | paid totals, remaining |
| `PATCH /pools/entries/{id}` | 1800 | `entry.month_key` | amounts/paid |
| `PATCH /pools/entries/{id}/toggle` | 1822 | `entry.month_key` | paid totals, remaining |
| `DELETE /pools/entries/{id}` | 1836 | `entry.month_key` (capture before delete) | totals |
| `PUT /fixed-templates/{id}` | 874 | multi-month (`>= current`) → all-user | seeded row amounts |
| `DELETE /fixed-templates/{id}` | 913 | multi-month (`>= current`) → all-user | seeded rows |

**What to do**:

1. Add a broad helper next to `_invalidate_month_caches` (line 1282) for the cases where the
   affected month set is ambiguous or spans many months (budget, template edits):

   ```python
   def _invalidate_all_user_caches(user_id: int) -> None:
       for cache in (_story_cache, _insight_cache):
           for k in [k for k in cache if k[0] == user_id]:
               cache.pop(k, None)
       # mantra handled in Item 2 (key shape changes there)
       for k in [k for k in _mantra_cache if k[0] == user_id]:
           _mantra_cache.pop(k, None)
   ```

2. After each `session.commit()` in the table above, add the matching call:
   - **Single known month** (fixed toggle/amount, income POST/PUT/DELETE, all pool endpoints):
     `_invalidate_month_caches(current_user.id, <month_key>)`.
     - For `DELETE` endpoints, capture `month_key = entry.month_key` **before** `session.delete`.
     - `toggle_paid` (691): insert between line 699 (`session.commit()`) and 700
       (`session.refresh`). Same shape for the other single-month endpoints.
   - **bulk-delete** (650): collect the distinct month keys while iterating, then invalidate each:
     ```python
     months = set()
     for expense_id in req.ids:
         exp = session.get(Expense, expense_id)
         if exp and not exp.is_fixed and exp.user_id == current_user.id:
             months.add(exp.month_key)
             session.delete(exp); deleted.append(expense_id)
     session.commit()
     for mk in months:
         _invalidate_month_caches(current_user.id, mk)
     ```
   - **Ambiguous / multi-month** (`PUT /budget`, `PUT /fixed-templates/{id}`,
     `DELETE /fixed-templates/{id}`): call `_invalidate_all_user_caches(current_user.id)` after
     commit.

**Depends on**: nothing for the single-month calls; the `_invalidate_all_user_caches` helper is
introduced here and reused by Item 2.

**Acceptance**: toggle a bill paid / edit income / change a cap → re-fetch `/insights/story`,
`/insights/monthly-insight`, `/insights/mantra` and confirm the text reflects new numbers
(no stale %, no stale remaining).

---

## Item 2 — Fix mantra cache key + make it invalidatable
**Scope**: Backend-only
**Files**: `backend/main.py` (`daily_mantra` line 1288; `_invalidate_month_caches` line 1282)
**Depends on**: Item 1 (reuses the per-user invalidation pattern)

**Root cause**: `daily_mantra` stores under a **date** key —
`cache_key = (current_user.id, today.isoformat())` (line 1295), written at line 1369 — but
`_invalidate_month_caches` pops a **month** key: `_mantra_cache.pop((user_id, month_key), None)`
(line 1284). `("2026-06-28")` vs `("2026-06")` never match, so mantra invalidation is a no-op.
The mantra is frozen for the whole calendar day regardless of balance changes → **Issue #4**.

**What to do**:

1. Change the mantra cache key to carry both month and date so it's per-day *and*
   invalidatable per month. At line 1295:
   ```python
   # before
   cache_key = (current_user.id, today.isoformat())
   # after
   cache_key = (current_user.id, month_key, today.isoformat())
   ```
   (No other read/write site to change — only line 1296 lookup and line 1369 store use
   `cache_key`.)

2. Update `_invalidate_month_caches` (line 1284) to pop all mantra entries matching
   `(user_id, month_key, *)`:
   ```python
   def _invalidate_month_caches(user_id, month_key):
       _story_cache.pop((user_id, month_key), None)
       _insight_cache.pop((user_id, month_key), None)
       for k in [k for k in _mantra_cache if k[0] == user_id and len(k) == 3 and k[1] == month_key]:
           _mantra_cache.pop(k, None)
   ```
   (Item 1's `_invalidate_all_user_caches` already clears mantra by `user_id` prefix, which
   stays correct under the new 3-tuple key.)

**Acceptance**: log an expense (or any Item-1 mutation) today → next `/insights/mantra` fetch
regenerates against the updated balance. With no changes, the mantra still caches within the day.

---

## Item 3 — Robust first-month detection + non-comparative insight guard
**Scope**: Backend + Frontend
**Files**:
- `backend/budget_rules.py` — new helper
- `backend/main.py` — `monthly_insight` (line 1424, first-month logic at 1446)
- `backend/ai_parser.py` — `generate_monthly_insight` (comparative branch, line 224)
- `frontend/react/src/components/tabs/OverviewTab.tsx` — `isFirstMonth` (line 265)

**Root cause** (Issue #5 — user only has current-month data, yet Insight asserts "jumped 72%"):
- `get_balance_summary` (`budget_rules.py:77`) **never returns `None`** — always a populated
  (zero-filled) dict.
- Backend `monthly_insight` detects first month via
  `is_first_month = (prev_balance is None or prev_balance.get("variable_total", 0) == 0)`
  (line 1446). `prev_balance is None` is dead (never None); the only real guard is
  `variable_total == 0`, which any stray prior-month row flips, sending it to the comparative
  branch.
- Comparative prompt (`ai_parser.py:230`) only *asks* the model to avoid % "unless both …
  non-zero and meaningful" — the model doesn't reliably comply.
- Frontend `OverviewTab.tsx:265` `const isFirstMonth = prevSummary === null;`, but
  `/summary/{prevMonthKey}` returns a zero-filled object (the `.catch(() => null)` at line 220
  only triggers on a thrown error, not on an empty-but-200 month) → `isFirstMonth` is
  effectively always `false`, so `isSafeInsight()` (lines 178-182) never blocks anything.

**What to do**:

### Backend — `budget_rules.py`
Add a helper that answers "did the user track anything before this month?":
```python
def has_prior_activity(session: Session, month_key: str, user_id: int) -> bool:
    """True if the user has any Expense or IncomeEntry in a month before month_key."""
    exp = session.exec(
        select(Expense.id).where(
            Expense.user_id == user_id, Expense.month_key < month_key
        ).limit(1)
    ).first()
    if exp:
        return True
    inc = session.exec(
        select(IncomeEntry.id).where(
            IncomeEntry.user_id == user_id, IncomeEntry.month_key < month_key
        ).limit(1)
    ).first()
    return inc is not None
```
(String `<` on `"YYYY-MM"` keys is correct lexicographically. Ensure `Expense` and
`IncomeEntry` are imported in `budget_rules.py` — they already are; confirm during impl.)

### Backend — `main.py` `monthly_insight` (line 1446)
Replace the fragile check:
```python
# before
is_first_month = (prev_balance is None or prev_balance.get("variable_total", 0) == 0)
# after
is_first_month = not has_prior_activity(session, month_key, current_user.id)
```
And before building the comparative context, null out a meaningless prior so the prompt can't
manufacture a ratio:
```python
prev_variable = prev_balance["variable_total"] if prev_balance else None
if not prev_variable:          # 0 or None
    is_first_month = True      # force the encouraging, non-comparative branch
```
Pass `prev_variable` into `context["prev_variable_total"]` (replacing the current line 1467
expression). Import the helper at top of `main.py`.

### Backend — `ai_parser.py` `generate_monthly_insight` (line 224 comparative branch)
Harden the instruction so a near-zero prior can never yield a % claim. Since Item-3 backend now
forces `is_first_month=True` whenever prior variable is 0/None, the comparative branch only runs
with a real non-zero prior — keep the existing prompt but tighten line 239-241 to:
"Only state a percentage change if BOTH months' variable totals exceed ₹1,000; otherwise describe
the trend qualitatively (e.g. 'higher', 'similar') with no number."

### Frontend — `OverviewTab.tsx` (line 265)
Stop relying on `prevSummary === null`:
```ts
// before
const isFirstMonth = prevSummary === null;
// after
const isFirstMonth =
  prevSummary === null || (prevSummary.balance?.variable_total ?? 0) === 0;
```
`isSafeInsight()` (lines 178-182) stays as the backstop and will now actually fire for genuine
first-month users.

**Acceptance**: a user whose first entries are this month sees an encouraging, **non-comparative**
insight — no "jumped X%", no "vs last month".

---

## Item 4 — Don't cache the current (live) month
**Scope**: Backend-only
**Files**: `backend/main.py` — `monthly_story` (line 1373, cache read 1377 / write 1420);
`monthly_insight` (line 1424, cache read 1428 / write 1474)
**Do last** — touches the read path of both endpoints; relies on Items 1-2 keeping past months
correctly invalidated.

**Root cause**: Even with perfect invalidation, the live month changes constantly between
mutations (and invalidation only fires on *our* mutations). Past months are immutable, so they
can cache forever; the current month should always regenerate. Per spec Item 3, **option (A)** is
chosen (correctness over a marginal LLM-cost saving).

**What to do**: in both endpoints, gate cache read **and** write on the month being in the past.
Add near the top of each:
```python
from datetime import date as _dt
is_past_month = month_key < _dt.today().strftime("%Y-%m")
```
- `monthly_story`: wrap the line 1377-1378 early-return in `if is_past_month and cache_key in
  _story_cache:` and the line 1420 write in `if is_past_month:`.
- `monthly_insight`: same — guard the line 1428-1429 return with `if is_past_month and …` and the
  line 1474 write with `if is_past_month:`.

Net: current month always fresh (one LLM call per dashboard load); past months cached as today.

**Acceptance**: change today's numbers, reload Overview → story/insight update with no manual
cache reset, and the prior-month narratives are unchanged/instant.

---

## Execution Order

| # | Item | Effort | Risk |
|---|------|--------|------|
| 1 | Invalidate on all balance mutations | M | Low — additive calls; one new helper |
| 2 | Fix mantra cache key + invalidation | S | Low — key-shape change in one endpoint |
| 3 | First-month detection + insight guard | M | Medium — backend helper + 2 prompts + 1 FE line |
| 4 | Don't cache current month | S | Low — read-path guard in 2 endpoints |

Tackle **Item 1 first** (it introduces the shared invalidation helper Item 2 reuses), then Item 2,
then Item 3, then Item 4 last.

---

## Definition of Done
- Backend restarts cleanly (`uv run uvicorn backend.main:app --reload`); no import errors.
- `npm run build` passes (zero TS errors / ESLint warnings) for the OverviewTab change.
- Manual verification on the running app + live backend:
  - Toggle a bill paid → "month in one sentence" and Bills-Paid % agree **immediately**.
  - Edit income → story/insight reflect new remaining on reload.
  - Log an expense today → mantra regenerates against new balance.
  - A current-month-only user sees a non-comparative Insight (no "jumped %").
- No regression in expense CRUD freshness (the four endpoints that already invalidated still do).

## Out of scope
- Persisting caches across process restart (still in-memory by design).
- Redesign of story/insight/mantra copy or prompts beyond the first-month guard.
- Any visual/layout change to Overview cards — render JSX is correct (verified across commits
  `b233121`, `fa59c07`, `44a4909`); the bug is purely data freshness.
