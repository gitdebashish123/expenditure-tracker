# Implementation Plan: User-Type AI Classification
**Spec**: `.claude/specs/30_user-type-ai-classification.md`
**Date**: 2026-07-02
**Branch**: `feature/sprint0726p1-ui-enhancement` *(actual current branch per `git branch --show-current`; the spec header says `feature/sprint06261-ui-enhancement`, which doesn't match — same stale-branch-name issue already flagged in plan 29, no branch switch needed)*

---

## Overview

6 spec items, all backend-only (`backend/budget_rules.py`, `backend/ai_parser.py`, `backend/main.py`). No frontend changes — `user_type` never reaches the API response, it's purely a prompt-shaping input.

Spec 29 (day-1 guard) is already implemented and merged into this branch (confirmed via `git diff` — `daily_mantra` passes `day_of_month`, `monthly_story` short-circuits on day 1, `monthly_insight` short-circuits on day 1–3 via `DAY1_GRACE`). This plan builds on that code as it exists today, not as the spec assumed it would look.

Plan items are reordered from the spec's own numbering (smallest blast radius first). The five `ai_parser.py`/`budget_rules.py` edits are isolated, single-function changes that are inert until wired up; the `main.py` wiring item touches three shared endpoints and is deliberately last, since it's what activates everything else end-to-end.

One divergence found and flagged below (not a stale-spec issue, but a consequence the spec doesn't spell out): wiring `user_type` into `monthly_insight` makes the existing `is_first_month`/`has_prior_activity` logic in `main.py` dead code. See Item 6 (main.py wiring) for the call and reasoning.

---

## Item 1 — User-type classifier (Spec Item 1)
**Scope**: Backend-only
**Files**: `backend/budget_rules.py:1` (import line), insert new function after `has_prior_activity` (currently ends line 160, before `compute_peace_of_mind` at line 163)

**Root cause**: No such function exists yet — this is net-new. Confirmed `backend/budget_rules.py` currently has no `classify_user_type` and no `group_by`/`func.count` usage anywhere in the file (`has_prior_activity` at line 143 does a simpler existence check).

**What to do**:

1. Add `func` to the existing import (line 1):
   ```python
   # before:
   from sqlmodel import Session, select
   # after:
   from sqlmodel import Session, select, func
   ```
   `Expense` is already imported at line 2 (`from backend.models import Expense, BudgetLimit, IncomeEntry, FixedExpenseTemplate, PoolEntry`) — no new model import needed. `func` is already proven to work as a sqlmodel import elsewhere (`backend/main.py:7`, used for `func.count()` at lines 982, 1167, 1916, 1918, 1920, 1935), so this is a safe, established pattern in this codebase, just not yet inside `budget_rules.py`.

2. Insert after `has_prior_activity` (after line 160, before the blank line + `compute_peace_of_mind` def at line 163):
   ```python
   def classify_user_type(session: Session, user_id: int, current_month_key: str) -> str:
       """
       Returns one of: "new", "inconsistent", "consistent".
       "day_one" is handled upstream in the endpoint before this is called
       (Spec 29's day_of_month / DAY1_GRACE guards in backend/main.py).
       """
       prior_months = session.exec(
           select(Expense.month_key, func.count(Expense.id).label("n"))
           .where(
               Expense.user_id == user_id,
               Expense.is_fixed == False,
               Expense.month_key < current_month_key,
           )
           .group_by(Expense.month_key)
           .order_by(Expense.month_key.desc())
           .limit(4)
       ).all()

       if not prior_months:
           return "new"

       active_months = [m for m in prior_months if m.n >= 5]

       if len(active_months) >= 3:
           return "consistent"

       return "inconsistent"
   ```

**Note on scope of "new"**: this only checks variable `Expense` rows (`is_fixed == False`), not `IncomeEntry` — narrower than `has_prior_activity`, which also counts income entries and fixed expenses. This is per the spec's own pseudocode (spec lines 53-58 filter `Expense.is_fixed == False` only), so implemented as specced, not flagged as a divergence — just noting it's an intentional narrower definition than the existing helper.

---

## Item 2 — Mantra: user-type prompt branches (Spec Item 3)
**Scope**: Backend-only
**Files**: `backend/ai_parser.py:79-153` (`generate_daily_mantra`)

**Root cause**: Confirmed current code — the day-1 branch (Spec 29) returns early at line 109 (`if day_of_month == 1: ... return message.content[0].text.strip()`). Everything from line 111 (`angle_hint = {...}`) onward runs for every other day with no user-type awareness; `comparison_line` (lines 119-123) is built purely from whether `top_category_prev_month_spent` is present, regardless of how sparse the user's tracking history is.

**What to do**: insert immediately after the day-1 branch's `return` (after line 109), before `angle_hint = {...}` (line 111):

```python
user_type = context.get("user_type", "consistent")

user_type_hint = ""
if user_type == "new":
    user_type_hint = (
        "This is the user's first tracked month. Focus on encouragement and what "
        "they can look forward to. No comparisons to prior months.\n"
    )
elif user_type == "inconsistent":
    user_type_hint = (
        "The user tracks inconsistently. Be warm and encouraging rather than "
        "analytical. Avoid percentage comparisons unless the numbers are clearly "
        "meaningful (both months > ₹1,000).\n"
    )
```

Then change the `comparison_line` block (lines 119-123) to suppress it for inconsistent users:
```python
# before:
comparison_line = ""
if context.get("top_category_prev_month_spent") is not None:
    comparison_line = (
        f"- Same category last month: ₹{context['top_category_prev_month_spent']:.0f}\n"
    )

# after:
comparison_line = ""
if user_type != "inconsistent" and context.get("top_category_prev_month_spent") is not None:
    comparison_line = (
        f"- Same category last month: ₹{context['top_category_prev_month_spent']:.0f}\n"
    )
```

Finally, prepend `user_type_hint` to the prompt string (the `prompt = f"""A user's financial snapshot..."""` block starting at line 125):
```python
prompt = user_type_hint + f"""A user's financial snapshot for the rest of this month:
...
```

This is inert until Item 6 (main.py wiring) adds `"user_type"` to the context dict — `context.get("user_type", "consistent")` defaults to `"consistent"` (today's unchanged behavior) until then, so this change alone is safe to land standalone.

---

## Item 3 — Monthly story: user-type guard (Spec Item 5)
**Scope**: Backend-only
**Files**: `backend/ai_parser.py:156-201` (`generate_monthly_story`)

**Root cause**: Confirmed — `generate_monthly_story` has no user-type awareness today; the prompt (lines 171-194) is built purely from `context['month_label']`, `fixed_completion_pct`, `savings_total`, `remaining`, `days_left`.

**What to do**: insert before the existing `prompt = f"""Generate a single sentence summary...` (line 171):
```python
user_type_note = {
    "new":          "This is the user's first month. Do not reference prior months.",
    "inconsistent": "The user tracks inconsistently. Focus on this month's data only.",
    "consistent":   "",
}.get(context.get("user_type", "consistent"), "")
```
Then after the prompt string is fully built (after line 194, before `message = client.messages.create(...)` at line 196), add:
```python
if user_type_note:
    prompt = user_type_note + "\n\n" + prompt
```

**Interaction to be aware of**: `backend/main.py`'s `monthly_story` endpoint already short-circuits before this function is ever called when `today.day == 1` for the live month (main.py:1431-1433, added by Spec 29). So the `"new"` branch here only fires on day 2+ of a user's first tracked month — day 1 itself always gets the Spec-29 static sentence regardless of user type. This matches the spec's intent (Spec 29 "takes precedence over all" per spec 30's own table, line 40) — no conflict, just noting why `"new"` won't visibly trigger this exact code path on day 1.

---

## Item 4 — Monthly insight: user-type branches + Miscellaneous nudge (Spec Items 4 & 6)
**Scope**: Backend-only
**Files**: `backend/ai_parser.py:204-264` (`generate_monthly_insight`)

**Root cause**: Confirmed current code — line 226 branches on `if context.get("is_first_month"):`, a binary flag with no notion of "inconsistent." The `else` branch (lines 240-258) is the only place `top_category` is used without any category-specific nudge.

**What to do**:

1. Replace the branch condition (line 226) and vary the wording by exact user type:
   ```python
   # before:
   if context.get("is_first_month"):
       prompt = (
           "This is the user's first tracked month in Wallet Mantra. Generate exactly ONE short, "
           ...
       )

   # after:
   if context.get("user_type") in ("new", "inconsistent"):
       tracking_phrase = (
           "first tracked month" if context.get("user_type") == "new"
           else "a month where tracking was lighter than usual"
       )
       prompt = (
           f"This is the user's {tracking_phrase} in Wallet Mantra. Generate exactly ONE short, "
           "encouraging, forward-looking observation (maximum 20 words). Do not reference any "
           "comparison to prior months, percentages, or changes. Focus only on what is notable "
           "or positive about this month's actual data.\n\n"
           f"Month: {context.get('month_key', 'this month')}\n"
           f"Top spending category: {context.get('top_category') or 'N/A'} "
           f"at ₹{context.get('top_category_spent', 0):.0f}\n"
           f"Savings this month: ₹{context.get('savings_total', 0):.0f} "
           f"({context.get('savings_pct', 0)}% of income)\n"
           f"Bills paid: {context.get('bills_status', 'unknown')}\n\n"
           "Respond with a single sentence only. No preamble."
       )
   ```

2. In the `else` branch (now implicitly the `"consistent"` branch — lines 240-258), add the Miscellaneous nudge (Spec Item 6) right before the prompt is assembled:
   ```python
   else:
       prev_var = (
           f"₹{context['prev_variable_total']:.0f}"
           if context.get("prev_variable_total") is not None
           else "N/A"
       )
       misc_note = ""
       if context.get("top_category") == "Miscellaneous":
           misc_note = (
               "\nNote: the top category is Miscellaneous, which may indicate "
               "uncategorized expenses. If relevant, gently suggest the user review "
               "and recategorize."
           )
       prompt = (
           "You are a financial assistant. Generate exactly ONE concise observation sentence "
           "(maximum 20 words) about this user's financial behaviour this month. "
           "Do not restate totals already visible on the dashboard. "
           "Focus on a pattern, trend, or notable behaviour.\n\n"
           f"Variable spending: ₹{context['variable_total']:.0f} ({context['variable_pct_of_income']}% of income)\n"
           f"Top category: {context.get('top_category') or 'N/A'} at ₹{context.get('top_category_spent', 0):.0f}\n"
           f"Prior month variable: {prev_var}\n"
           f"Bills paid: ₹{context['fixed_paid_total']:.0f} of ₹{context['fixed_total']:.0f}\n"
           f"{misc_note}\n\n"
           "Respond with a single sentence only. No preamble, no punctuation beyond the sentence itself. "
           "Only state a percentage change if BOTH months' variable totals exceed ₹1,000; "
           "otherwise describe the trend qualitatively (e.g. 'higher', 'similar') with no number."
       )
   ```

Also update the function's docstring (lines 208-224) — `is_first_month: bool` under "Required context keys" should become `user_type: str  # "new" | "inconsistent" | "consistent"`.

Bundled here rather than as a separate plan item because both edits land in the same function and the nudge only makes sense once the branch is keyed on `user_type` — splitting them would mean touching `generate_monthly_insight` twice for no isolation benefit.

---

## Item 5 — Wire `user_type` into all three endpoints; remove now-dead `is_first_month` logic (Spec Item 2)
**Scope**: Backend-only
**Files**: `backend/main.py` — imports (line 27-31), `daily_mantra` (1318-1400), `monthly_story` (1404-1459), `monthly_insight` (1463-1529)

**Root cause**: None of the three endpoints currently compute or pass `user_type`. Confirmed exact insertion points against current code (post-Spec-29):
- `daily_mantra`: no early-return before context is built (the day-1 short-circuit lives inside `generate_daily_mantra` itself, not in the endpoint) — so `classify_user_type` must run unconditionally.
- `monthly_story`: already short-circuits at lines 1431-1433 (`if month_key == today... and today.day == 1: return ...`) before `context` is built — `classify_user_type` only needs to run for the non-day-1 path.
- `monthly_insight`: already short-circuits at lines 1473-1474 (`if ... today.day <= DAY1_GRACE: return ...`) before `balance` is computed — same pattern.

**What to do**:

### Imports (line 27-31)
```python
# before:
from backend.budget_rules import (
    get_month_key, check_budget_warnings, get_balance_summary,
    seed_fixed_expenses, get_monthly_spent_by_category, get_budget_limits,
    compute_peace_of_mind, has_prior_activity,
)
# after:
from backend.budget_rules import (
    get_month_key, check_budget_warnings, get_balance_summary,
    seed_fixed_expenses, get_monthly_spent_by_category, get_budget_limits,
    compute_peace_of_mind, classify_user_type,
)
```
`has_prior_activity` is dropped from the import — see the `monthly_insight` change below for why it becomes unused.

### `daily_mantra` (insert before `context = {` at line 1371)
```python
user_type = classify_user_type(session, current_user.id, month_key)
```
Add to the context dict (after `"fixed_unpaid_total": balance["fixed_unpaid_total"],` at line 1379):
```python
    "user_type": user_type,
```

### `monthly_story` (insert after the day-1 short-circuit, e.g. after `month_label = ...` at line 1439, before `context = {` at line 1441)
```python
user_type = classify_user_type(session, current_user.id, month_key)
```
Add to the context dict (after `"days_left": days_left,` at line 1449):
```python
    "user_type": user_type,
```

### `monthly_insight` — replace dead `is_first_month` logic with `user_type`
Current code (lines 1491-1497):
```python
is_first_month = not has_prior_activity(session, month_key, current_user.id)

# A near-zero / missing prior variable total can never anchor a meaningful
# comparison — force the encouraging, non-comparative branch in that case.
prev_variable = prev_balance["variable_total"] if prev_balance else None
if not prev_variable:
    is_first_month = True
```

**Why this changes**: after Item 4's `ai_parser.py` edit, `generate_monthly_insight` no longer reads `context["is_first_month"]` at all — it reads `context["user_type"]`. Once that lands, `is_first_month` becomes a computed-but-unread local variable, and the `"is_first_month"` context key (line 1509) becomes dead. Per this repo's own conventions (CLAUDE.md: no half-finished implementations, don't leave unused code), this plan removes it rather than leaving it alongside the new `user_type` key. `prev_variable` itself is **kept** — it's still consumed by `generate_monthly_insight`'s `"consistent"` branch as `context['prev_variable_total']`.

Replace with:
```python
user_type = classify_user_type(session, current_user.id, month_key)

prev_variable = prev_balance["variable_total"] if prev_balance else None
```

Update the context dict (line 1508-1521) — replace `"is_first_month": is_first_month,` with `"user_type": user_type,`:
```python
    context = {
        "user_type":              user_type,
        "month_key":              month_key,
        "variable_total":         balance["variable_total"],
        "variable_pct_of_income": variable_pct,
        "top_category":           top_category,
        "top_category_spent":     top_category_spent,
        "savings_total":          savings_total,
        "savings_pct":            savings_pct,
        "bills_status":           bills_status,
        "prev_variable_total":    prev_variable,
        "fixed_paid_total":       balance["fixed_paid_total"],
        "fixed_total":            fixed_total,
    }
```

**Behavior note**: today, `is_first_month` is forced `True` whenever `prev_variable` is falsy (₹0 or missing), regardless of how many months of history exist further back. `classify_user_type` instead looks at up to 4 prior months and requires 3+ active months (≥5 entries) to call a user `"consistent"` — a user with one ₹0 variable month sandwiched between two active months would have read as `is_first_month=True` under the old logic, but may read as `"inconsistent"` or even `"consistent"` under the new classifier depending on the other 3 months. This is the intended behavior change per the spec (a richer, multi-month view replacing a single-month binary), not a bug — flagging so it's understood as a deliberate behavior shift when testing.

---

## Files
| Item | File(s) |
|---|---|
| 1 — Classifier | `backend/budget_rules.py` |
| 2 — Mantra branches | `backend/ai_parser.py` |
| 3 — Story guard | `backend/ai_parser.py` |
| 4 — Insight branches + Misc nudge | `backend/ai_parser.py` |
| 5 — Endpoint wiring + cleanup | `backend/main.py` |

## Execution Order

| # | Item | Effort | Risk | Depends on |
|---|------|--------|------|-------------|
| 1 | Classifier (`budget_rules.py`) | S | None — new pure function, no callers yet | — |
| 2 | Mantra branches (`ai_parser.py`) | S | None — inert until wired, defaults to `"consistent"` | — |
| 3 | Story guard (`ai_parser.py`) | XS | None — inert until wired | — |
| 4 | Insight branches + Misc nudge (`ai_parser.py`) | S | None — inert until wired | — |
| 5 | Endpoint wiring + `is_first_month` cleanup (`main.py`) | M | Medium — touches 3 shared endpoints, removes a helper import, changes real classification behavior for edge-case histories (see note in Item 5) | 1, 2, 3, 4 |

Start with Item 1 (foundation). Items 2, 3, 4 can be done in any order or together — each is a self-contained, inert edit to `ai_parser.py`. Land Item 5 last since it's what actually activates the new prompts and is the only item with real behavior-change risk.

## Definition of Done
- Manual test against a live backend for three distinct users/months representing `"new"`, `"inconsistent"`, and `"consistent"` — confirm `/insights/mantra`, `/insights/story`, `/insights/monthly-insight` return copy matching the intended tone per type (no comparisons/percentages for new/inconsistent, full analytics for consistent).
- Manual test: a `"consistent"` user whose top category is `"Miscellaneous"` — confirm the insight text includes a recategorize nudge.
- Confirm Spec 29's day-1 / `DAY1_GRACE` short-circuits still fire before any `user_type` logic runs (day 1 mantra, day 1 story, day 1–3 insight) — this plan must not regress that.
- `python -m py_compile backend/budget_rules.py backend/ai_parser.py backend/main.py` (or equivalent import check) — clean.
- Confirm `has_prior_activity` has no remaining callers after Item 5 (or keep the import if a caller is found elsewhere at implementation time — re-check `grep -rn has_prior_activity backend/` before deleting the import, since this plan's grep found only the one call site being removed).

---

## Execution Log — 2026-07-02

Items 1–5 implemented in plan order (classifier first, the three `ai_parser.py` prompt edits next, `main.py` wiring last).

- **Item 1** — `classify_user_type()` added to `backend/budget_rules.py` after `has_prior_activity`, exactly as specced (grouped `Expense` count over the last 4 prior months, `>= 3` active months → `"consistent"`). `func` added to the module's `sqlmodel` import.
- **Item 2** — `generate_daily_mantra` (`backend/ai_parser.py`) gained a `user_type_hint` preamble (defaults to `"consistent"` behavior via `context.get("user_type", "consistent")`) and `comparison_line` is now suppressed outright for `"inconsistent"` users.
- **Item 3** — `generate_monthly_story` (`backend/ai_parser.py`) gained a `user_type_note` preamble, prepended to the prompt only when non-empty (i.e. never for `"consistent"`).
- **Item 4** — `generate_monthly_insight` (`backend/ai_parser.py`) branch condition changed from `is_first_month` to `user_type in ("new", "inconsistent")`, with distinct wording per type (`"first tracked month"` vs `"a month where tracking was lighter than usual"`). Miscellaneous-category nudge added to the `"consistent"` branch prompt. Docstring updated to reflect `user_type` replacing `is_first_month`.
- **Item 5** — `daily_mantra`, `monthly_story`, `monthly_insight` (`backend/main.py`) each call `classify_user_type(session, current_user.id, month_key)` and add `"user_type"` to their context dicts. In `monthly_insight`, the dead `is_first_month`/`has_prior_activity` computation (forced-true-on-zero-prior-variable hack) was removed and replaced with the `user_type` call, per the plan's stated rationale — `prev_variable` itself was kept since `generate_monthly_insight`'s consistent-user branch still reads `prev_variable_total`. `has_prior_activity` dropped from the `backend.budget_rules` import in `main.py`.

**Verification performed**:
- `uv run python -m py_compile backend/budget_rules.py backend/ai_parser.py backend/main.py` — clean.
- `uv run python -c "import backend.main"` — clean, no import errors.
- `grep -rn has_prior_activity` across the repo — only the function definition in `budget_rules.py` remains; no callers. Left the function in place (out of this plan's file scope — only the `main.py` import/call site was slated for removal); flagged as a minor follow-up cleanup opportunity, not blocking.
- Ran `classify_user_type` against the real local dataset (`data/expenses.db`) for a few existing user IDs — returned `"new"`/`"inconsistent"` without error, confirming the grouped query executes correctly against live data (no `"consistent"` case present in current local data, so that branch wasn't exercised against real data — logic was still verified by code inspection against the spec's stated threshold).
- Did **not** make live Anthropic API calls to inspect actual generated mantra/story/insight sentence tone for each user type — that requires `ANTHROPIC_API_KEY`-backed manual QA against a running backend per the Definition of Done above, and was out of scope for this execution pass.

Status: **5/5 items complete.** See `.claude/blocked/30-followups-for-reevaluation.md` for two follow-up items worth revisiting later, neither of which blocks this plan's completion.
