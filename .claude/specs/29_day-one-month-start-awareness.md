# Spec 29 — Day-1 / Month-Start Awareness
**Date**: 2026-07-01
**Status**: 🟢 Implemented — items 1–5 done 2026-07-01; item 6 blocked, see `.claude/blocked/29-item6-month-end-projection.md`
**Branch**: `feature/sprint06261-ui-enhancement` *(confirm active branch before starting)*
**Follows**: `28_accessibility-and-parser-fallback.md`
**Source**: User review on first day of July 2026 — items 5–8 and partial item 4.
**Scope**: Backend (prompt guards) + frontend (copy, reminder threshold, projection guard).
No data-model changes; no new endpoints. Purely defensive/guard logic.

---

## Context

On day 1 of a new month the app has **no current-month data** — zero variable spend,
zero fixed items paid, zero days elapsed — yet every AI surface and derived metric
tries to compute something meaningful from that empty baseline. The results are
universally wrong or misleading:

- Mantra quotes last month's balance, not July's outlook.
- Monthly story says "Bills are 0% paid with ₹1,46,899 remaining."
- Insight says "Variable spending dropped significantly" (it's ₹0 vs last month).
- Tiny win fires "Food spending is down from last month" (food is ₹0).
- Due reminders surface bills due on the 28th on day 1 (27 days early).
- Month-end projection is nonsensical (no variable spend yet to extrapolate from).

All fixes are **guards and tone shifts** — no new features, no data-model changes.

---

## Item 1 — Mantra: day-1 prompt branch (`backend/ai_parser.py`)

**Root cause:** `generate_daily_mantra` receives `days_left = 30` and
`daily_budget = remaining / days_left`, but the context was built before any
spending, so all spending values are ₹0. The model writes about last month's
numbers because the `comparison_line` is present and the "top category" is N/A.

**Fix:** in `backend/main.py`, compute `day_of_month = date.today().day` in the
`/insights/mantra/{month_key}` endpoint and pass it into `generate_daily_mantra`.
Add a `day_of_month` parameter to `generate_daily_mantra`; when `day_of_month == 1`
use a **day-1-specific prompt branch**:

```python
# in generate_daily_mantra — new branch:
if day_of_month == 1:
    prompt = f"""It's the very first day of a new month. The user has:
- Income this month: ₹{context['total_income']:.0f}
- Fixed commitments to track: ₹{context.get('fixed_unpaid_total', 0):.0f}
- Days in the month ahead: {context['days_left']}

Write ONE warm, forward-looking sentence (max 25 words) welcoming the fresh start.
Do NOT reference last month, prior spending, or percentage changes.
Use ₹ symbol. Return ONLY the sentence, no preamble."""
```

**Acceptance:** on day 1, the mantra reads as a forward-looking welcome
("₹X in commitments to plan across 30 days — your fresh start begins now"),
never quoting last-month figures.

---

## Item 2 — Monthly story: day-1 framing (`backend/ai_parser.py` + endpoint)

**Root cause:** `generate_monthly_story` with `fixed_completion_pct = 0`,
`remaining = full_income`, `days_left = 30` produces grammatically correct but
semantically alarming sentences like "Bills are 0% paid with ₹1,46,899 remaining."

**Fix:** same `day_of_month` guard. When `day_of_month == 1`:

```python
if day_of_month == 1:
    return f"Your month is just starting — ₹{context['remaining']:,.0f} ready to allocate across {context['days_left']} days."
```

Return a static formatted string directly; skip the Claude call. This avoids
wasting an API call on a deterministic message and guarantees the tone is right.

**Acceptance:** on day 1, the "June in one sentence" card (now July) shows a
fresh-start sentence, never a "0% paid" alarm.

---

## Item 3 — Insight: suppress comparisons on day 1–3 (`backend/ai_parser.py` + endpoint)

**Root cause:** `generate_monthly_insight` uses the returning-user branch
(`not is_first_month`) and computes `prev_variable_total` vs current
`variable_total = ₹0`. The existing guard
(`if not prev_variable_total: is_first_month = True`) only fires when *last*
month's variable spend is zero — it doesn't catch when *this* month is day 1.

**Fix:** pass `day_of_month` into `generate_monthly_insight`. Add a guard:

```python
DAY1_GRACE = 3  # suppress comparisons for first 3 days of any month

if context.get("day_of_month", 1) <= DAY1_GRACE:
    return "Your month is just starting — insights will appear once you log your first expenses."
```

Return a static string; skip the Claude call. Constant `DAY1_GRACE = 3` defined
at module level so it's easy to tune.

**Acceptance:** on days 1–3 with no variable spend, the Insight card shows a
neutral "just started" message — no percentage comparisons, no "dropped
significantly."

---

## Item 4 — Tiny Win: suppress on day 1–3 when category spend is ₹0

**Root cause:** the Tiny Win endpoint computes `current_month_category_spent`
and compares against `prev_month_category_spent`. On day 1, any category with
₹0 this month is "down 100%" from last month — a meaningless win.

**Fix:** in the `/insights/tiny-win/{month_key}` endpoint, add:

```python
if day_of_month <= DAY1_GRACE or total_variable_this_month == 0:
    return {"win": None, "message": "Start logging to unlock your first Tiny Win."}
```

Return `win: null` so the frontend can hide the Tiny Win card entirely on day 1.
Frontend already handles `win: null` (confirm during impl — if not, add a null
check in the Tiny Win rendering component).

**Acceptance:** on day 1 the Tiny Win card is hidden or shows a neutral
"start logging" prompt; never claims "Food is down from last month" on day 1.

---

## Item 5 — Due reminders: threshold guard (`backend/main.py`)

**Root cause:** `/fixed/due-reminders/{month_key}` surfaces any bill whose
`due_day` falls this month, regardless of how far away it is. On July 1, bills
due on July 28 appear as "upcoming" — 27 days early.

**Confirmed code:** `DueReminder` is built with `days_overdue = today.day - due_day`.
Negative `days_overdue` means the bill is upcoming (not yet due). The frontend
renders these in red banners in Section 1 of `FixedTab`.

**Fix:** in the endpoint, filter out reminders where the bill is more than
`DUE_REMINDER_WINDOW = 5` days away:

```python
DUE_REMINDER_WINDOW = 5  # days before due date to start showing reminder

# Only surface:
# 1. Overdue bills (days_overdue > 0)
# 2. Bills due today (days_overdue == 0)
# 3. Bills due within the next N days (days_overdue >= -DUE_REMINDER_WINDOW)
reminders = [r for r in reminders if r.days_overdue >= -DUE_REMINDER_WINDOW]
```

**Acceptance:** on July 1 a bill due July 28 is not shown in reminders. A bill
due July 4 (3 days away) is shown. A bill due July 1 (today) is shown.

---

## Item 6 — Month-end projection: suppress on day 1–3 (`OverviewTab.tsx`)

**Root cause:** the "Expected month-end balance" shown in the Overview's "Coming
up" / summary section divides remaining balance by days elapsed, which is 0 or 1
on day 1, producing nonsensical projections like ₹55k.

**Fix:** in `OverviewTab.tsx`, compute `dayOfMonth = new Date().getDate()`.
When `dayOfMonth <= 3`, replace the projection figure with a neutral message:

```tsx
const projection = dayOfMonth <= 3
  ? "Check back in a few days"
  : fmtInr(computedProjection);
```

**Acceptance:** on day 1–3 the month-end projection shows "Check back in a
few days" instead of a mathematically-derived but meaningless figure.

---

## Files
| Item | File(s) |
|---|---|
| 1 — Mantra | `backend/ai_parser.py`, `backend/main.py` (mantra endpoint) |
| 2 — Story | `backend/ai_parser.py`, `backend/main.py` (story endpoint) |
| 3 — Insight | `backend/ai_parser.py`, `backend/main.py` (insight endpoint) |
| 4 — Tiny Win | `backend/main.py` (tiny-win endpoint), `frontend/react/src` (null-check) |
| 5 — Due reminders | `backend/main.py` (`/fixed/due-reminders/{month_key}`) |
| 6 — Projection | `frontend/react/src/components/tabs/OverviewTab.tsx` |

## Sequencing
Items 1–4 all follow the same pattern (compute `day_of_month`, pass to function,
add guard at top). Land together in one backend commit. Items 5 and 6 are
independent — can land in any order after 1–4.

## Out of scope
User-type classification for AI messages (New / Inconsistent / Consistent user
branches) — that's Spec 30, which builds on the guards introduced here.
