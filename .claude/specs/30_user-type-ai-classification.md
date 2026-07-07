# Spec 30 — User-Type Classification for AI Messages
**Date**: 2026-07-01
**Status**: ✅ Completed — see `.claude/plans/30-user-type-ai-classification.md` execution log
**Branch**: `feature/sprint06261-ui-enhancement` *(confirm active branch before starting)*
**Follows**: `29_day-one-month-start-awareness.md`
**Source**: User review July 2026 — item 2 ("Consider AI messages for different
type of users: new user, user with inconsistent entries in previous month,
consistent users etc").

---

## Context

The current AI prompt system has a single binary flag: `is_first_month: bool`.
This is too coarse:
- A **new user** on their very first month needs orientation, not analytics.
- An **inconsistent user** (sparse or skipped prior months) needs encouragement
  and gentle nudges, not trend comparisons that look alarming (comparing ₹5,000
  this month vs ₹0 last month is meaningless).
- A **consistent user** (regular entries across 3+ months) can handle
  comparisons, percentages, and behavioural observations.
- **Day 1** is already handled by Spec 29; user-type builds on top.

This spec introduces a **user classification helper** that feeds the three AI
functions (`generate_daily_mantra`, `generate_monthly_insight`, `generate_monthly_story`)
with a richer context, enabling distinct prompt branches per user type.

---

## Item 1 — User-type classifier (`backend/budget_rules.py`)

Add `classify_user_type(session, user_id, current_month_key) -> str` returning
one of four constants:

| Type | Condition | Behaviour target |
|---|---|---|
| `"new"` | No prior month has any `Expense` rows | Orientation; no comparisons |
| `"inconsistent"` | Has prior months but ≥ 50% of the last 3 months have < 5 variable entries | Encouragement; no hard percentages |
| `"consistent"` | 3+ months of regular activity (≥ 5 entries/month in at least 3 of the last 4 months) | Full analytics; comparisons enabled |
| `"day_one"` | Covered by Spec 29 day-of-month guard; takes precedence over all | Fresh-start tone |

```python
def classify_user_type(session, user_id: int, current_month_key: str) -> str:
    """
    Returns one of: "new", "inconsistent", "consistent".
    "day_one" is handled upstream in the endpoint before this is called.
    """
    from sqlmodel import select, func
    from backend.models import Expense

    # Fetch entry counts for the last 4 months before the current month
    # month_key format: "2026-07", so we can sort lexicographically
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

---

## Item 2 — Pass `user_type` into all three AI functions

**`backend/main.py`** — in the mantra, story, and insight endpoints, call
`classify_user_type` and add `"user_type"` to the context dict passed to each
AI function. The day_of_month check from Spec 29 runs *before* this call so
`day_one` doesn't need to be a return value of the classifier.

```python
user_type = classify_user_type(session, current_user.id, month_key)
context["user_type"] = user_type
```

---

## Item 3 — `generate_daily_mantra`: user-type branches (`backend/ai_parser.py`)

Extend the existing `generate_daily_mantra` with user-type-aware prompt preambles.
The day-1 branch (Spec 29) runs first; the user-type branch runs for all other days.

| User type | Prompt adjustment |
|---|---|
| `"new"` | Add: *"This is the user's first tracked month. Focus on encouragement and what they can look forward to. No comparisons to prior months."* |
| `"inconsistent"` | Add: *"The user tracks inconsistently. Be warm and encouraging rather than analytical. Avoid percentage comparisons unless the numbers are clearly meaningful (both months > ₹1,000)."* Remove the `comparison_line` from context. |
| `"consistent"` | Current prompt — no change. Comparisons and trends enabled. |

---

## Item 4 — `generate_monthly_insight`: user-type branches (`backend/ai_parser.py`)

The existing binary `is_first_month` flag maps cleanly to `user_type == "new"`.
Replace it:

```python
# before:
if context.get("is_first_month"):

# after:
if context.get("user_type") in ("new", "inconsistent"):
```

For `"inconsistent"` users, use the same first-month prompt (no comparisons,
focus on what's notable) with one change: replace "first tracked month" with
"a month where tracking was lighter than usual."

For `"consistent"` users, the returning-user branch runs as today, with
percentages enabled only when `prev_variable_total` is meaningful (existing guard
in `generate_monthly_insight`).

---

## Item 5 — `generate_monthly_story`: user-type guard (`backend/ai_parser.py`)

Currently the story prompt has no user-type awareness. Add a preamble injection:

```python
user_type_note = {
    "new":         "This is the user's first month. Do not reference prior months.",
    "inconsistent":"The user tracks inconsistently. Focus on this month's data only.",
    "consistent":  "",   # no extra note needed
}.get(context.get("user_type", "consistent"), "")

if user_type_note:
    prompt = user_type_note + "\n\n" + prompt
```

---

## Item 6 — Miscellaneous category nudge (user review item 3)

When `top_category == "Miscellaneous"` and the user is `"consistent"`, add a
line to the insight prompt:

```
"Note: the top category is Miscellaneous, which may indicate uncategorized
expenses. If relevant, gently suggest the user review and recategorize."
```

The frontend already shows a "recategorize?" nudge in the Overview Top Category
section (per the design work). This spec adds the same nudge to the AI insight
text so it surfaces in the mantra/insight sentence too.

---

## Files
| Item | File |
|---|---|
| 1 — Classifier | `backend/budget_rules.py` |
| 2 — Wiring | `backend/main.py` (mantra, story, insight endpoints) |
| 3–5 — Prompt branches | `backend/ai_parser.py` |
| 6 — Misc nudge | `backend/ai_parser.py` |

## Depends on
Spec 29 (day_of_month guard must be in place so day-1 fires before user-type
classification — order matters).

## Out of scope
AI-recommended savings thresholds (user review item 1) — requires income vs
fixed-total vs variable-total modelling; separate spec.
Notification consolidation (user review item 4) — addressed in Spec 31.
