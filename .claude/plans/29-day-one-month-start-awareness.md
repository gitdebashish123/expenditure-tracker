# Implementation Plan: Day-1 / Month-Start Awareness
**Spec**: `.claude/specs/29_day-one-month-start-awareness.md`
**Date**: 2026-07-01
**Branch**: `feature/sprint0726p1-ui-enhancement` *(actual current branch per `git branch --show-current`; the spec header says `feature/sprint06261-ui-enhancement`, which does not match — spec is stale on this point, no branch switch needed)*

---

## Overview

6 items total — 5 are backend-only, 1 is frontend-only **but its spec description does not match the current code** (see Item 6 below — flagged, not silently planned). Items 1–4 share one mechanical pattern (compute `day_of_month`, guard, return early) and land together. Items 5 and 6 are independent.

Two items simplify their file footprint vs. the spec's own file table, explained inline:
- **Items 2 & 3** don't need `ai_parser.py` changes at all — the guard returns a static string *before* `generate_monthly_story`/`generate_monthly_insight` would be called, so those functions are never reached and don't need new parameters.
- **Item 6** cannot be implemented as specced — the code path the spec describes doesn't exist anymore.

---

## Item 1 — Mantra: day-1 prompt branch
**Scope**: Backend-only
**Files**: `backend/ai_parser.py:79-137` (`generate_daily_mantra`), `backend/main.py:1313-1394` (`daily_mantra` endpoint)

**Root cause (confirmed)**: `daily_mantra` (main.py:1318, 1327, 1352-1353) computes `today = dt.today()`, builds `context` from `balance`/`spent_by_cat`, and calls `generate_daily_mantra(context, preferred_angle=chosen_angle)` at main.py:1377. On day 1 every spend figure is ₹0, but nothing tells the prompt it's day 1 — `top_category` is `None`, `comparison_line` may still be populated from last month's data (ai_parser.py:104-107), so the model has enough of last month's numbers in context to write about them.

**What to do**:

### `backend/main.py` (in `daily_mantra`, after line 1318 `today = dt.today()`)
Add:
```python
day_of_month = today.day if month_key == today.strftime("%Y-%m") else None
```
Then change the call at line 1377 from:
```python
mantra = generate_daily_mantra(context, preferred_angle=chosen_angle)
```
to:
```python
mantra = generate_daily_mantra(context, preferred_angle=chosen_angle, day_of_month=day_of_month)
```

### `backend/ai_parser.py` (`generate_daily_mantra`, line 79)
Change signature:
```python
def generate_daily_mantra(context: dict, preferred_angle: str = "forecast", day_of_month: int | None = None) -> str:
```
Insert a new branch immediately after the docstring (before the `angle_hint = {...}` block at line 95), so the day-1 case short-circuits before any angle/comparison logic runs:
```python
if day_of_month == 1:
    prompt = f"""It's the very first day of a new month. The user has:
- Income this month: ₹{context['total_income']:.0f}
- Fixed commitments to track: ₹{context.get('fixed_unpaid_total', 0):.0f}
- Days in the month ahead: {context['days_left']}

Write ONE warm, forward-looking sentence (max 25 words) welcoming the fresh start.
Do NOT reference last month, prior spending, or percentage changes.
Use ₹ symbol. Return ONLY the sentence, no preamble."""
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()
```
The rest of the function (angle_hint, comparison_line, existing prompt) is unchanged and only runs when `day_of_month != 1`.

**Note**: this still makes one Claude call (unlike items 2/3) — the spec's fix is a different *prompt*, not a static string, since the mantra needs a fresh, varied sentence each day-1.

---

## Item 2 — Monthly story: day-1 framing
**Scope**: Backend-only
**Files**: `backend/main.py:1398-1449` (`monthly_story` endpoint)

**Root cause (confirmed)**: `monthly_story` builds `fixed_completion_pct = 0` and `remaining = full income` on day 1 (main.py:1425-1427, 1433) and passes them to `generate_monthly_story` (ai_parser.py:140), which is instructed to mention bills status + one other figure — producing a grammatically fine but alarming "Bills are 0% paid" sentence.

**What to do** — no `ai_parser.py` change needed; short-circuit in the endpoint before `generate_monthly_story` is ever called (avoids the API call entirely, matching the spec's stated intent to skip Claude on day 1):

In `backend/main.py`, after `days_left` is computed (line 1423, right before `fixed_total = ...` at line 1425), insert:
```python
if month_key == today.strftime("%Y-%m") and today.day == 1:
    story = f"Your month is just starting — ₹{balance['remaining']:,.0f} ready to allocate across {days_left} days."
    return {"story": story}
```
This uses the `balance` and `days_left` locals already computed at that point — no new context keys, no cache write (deterministic and cheap to recompute, consistent with `is_past_month` never being true for day-1-of-current-month anyway).

---

## Item 3 — Insight: suppress comparisons on day 1–3
**Scope**: Backend-only
**Files**: `backend/main.py:1453-1516` (`monthly_insight` endpoint)

**Root cause (confirmed)**: `monthly_insight` only forces the non-comparative branch via `if not prev_variable: is_first_month = True` (main.py:1481-1483) — this fires when *last* month had ₹0 variable spend, not when *this* month is day 1–3. On day 1 with a non-zero prior month, `is_first_month` stays `False`, so the returning-user prompt (ai_parser.py:224-242) computes a real percentage against `variable_total = 0`, producing "dropped significantly"-style false comparisons.

**What to do** — no `ai_parser.py` change needed; short-circuit before `generate_monthly_insight` is called. Add module-level constant near the top of the insights section of `backend/main.py` (alongside the cache dicts at line ~1293, before `_invalidate_month_caches`):
```python
DAY1_GRACE = 3  # suppress comparisons for first N days of the live current month
```
In `monthly_insight`, after `from datetime import date as _dt` (line 1455) add `today = _dt.today()`, then immediately after the `is_past_month`/cache-check block (after line 1460, before `balance = get_balance_summary(...)` at line 1462) insert:
```python
if month_key == today.strftime("%Y-%m") and today.day <= DAY1_GRACE:
    return {"insight": "Your month is just starting — insights will appear once you log your first expenses."}
```
**Note**: this is a time-based guard (days 1–3 of the *live* month only), not conditioned on whether expenses were actually logged — matching the spec's literal wording ("suppress comparisons on day 1–3 of any month"), even though a user who logs expenses on day 2 would still see this neutral message until day 4. This is what the spec's acceptance criteria describes, so implementing it as a pure day-of-month gate is correct — flagging only so it's a deliberate choice, not an oversight.

---

## Item 4 — Tiny Win: suppress on day 1–3 when category spend is ₹0
**Scope**: Backend-only (frontend already handles it)
**Files**: `backend/main.py:1519-1557` (`tiny_win` endpoint), `frontend/react/src/types/index.ts:150-152` (`TinyWin`)

**Root cause (confirmed)**: `tiny_win`'s "Condition 2" (main.py:1548-1549) fires `if food_prev > 0 and food_curr < food_prev` — on day 1, `food_curr` is always ₹0, so any category with prior-month spend reads as "down from last month," which is meaningless.

**What to do**:

In `backend/main.py`, in `tiny_win`, after `days_left` is computed (line 1531), insert — reusing `DAY1_GRACE` from Item 3:
```python
day_of_month = today.day if month_key == today.strftime("%Y-%m") else None
if (day_of_month is not None and day_of_month <= DAY1_GRACE) or balance["variable_total"] == 0:
    return {"win": None, "message": "Start logging to unlock your first Tiny Win."}
```
Place this before "Condition 1" (line 1534) so it takes priority.

**Frontend**: confirmed already handled — `OverviewTab.tsx:926` renders `{tinyWin && (...)}`, so `win: null` already hides the card with zero frontend changes needed. The only gap is a type accuracy issue, not a behavior bug: `TinyWin` (types/index.ts:150-152) currently declares `win: string`, but the endpoint can now return `null`. Update:
```ts
export interface TinyWin {
  win: string | null;
}
```
This is a type-correctness fix only — `OverviewTab.tsx:219` (`.then(r => r.data.win)`) already assigns into a `useState<string | null>` and needs no change.

---

## Item 5 — Due reminders: threshold guard
**Scope**: Backend-only
**Files**: `backend/main.py:820-849` (`get_due_reminders`)

**Root cause (confirmed)**: `get_due_reminders` builds `days_overdue = today.day - due_day` for every unpaid fixed expense (main.py:840) and returns all of them sorted, with no distance filter — a bill due on the 28th shows up as a reminder on the 1st.

Confirmed both consumers read this same endpoint with no independent filtering of their own:
- `FixedTab.tsx:60-61,122-142` renders every entry in `reminders` as a red banner (Section 1) — no threshold check.
- `OverviewTab.tsx:217,669-671` picks the least-overdue entry from `dueReminders` for the "Coming up" card — no threshold check either.

So a single backend-side filter fixes both surfaces; no frontend changes needed (matches the spec's file table, which only lists `main.py` for this item).

**What to do**: add a module-level constant near the endpoint (e.g. directly above `get_due_reminders` at line 819):
```python
DUE_REMINDER_WINDOW = 5  # days before due date to start showing a reminder
```
Then, right before the `return sorted(...)` at line 849, insert:
```python
reminders = [r for r in reminders if r["days_overdue"] >= -DUE_REMINDER_WINDOW]
```
so the final line becomes:
```python
reminders = [r for r in reminders if r["days_overdue"] >= -DUE_REMINDER_WINDOW]
return sorted(reminders, key=lambda x: x["days_overdue"], reverse=True)
```

**Acceptance check**: on July 1, a bill due July 28 → `days_overdue = 1 - 28 = -27`, filtered out (`-27 < -5`). A bill due July 4 → `days_overdue = -3`, kept (`-3 >= -5`). A bill due July 1 → `days_overdue = 0`, kept.

---

## Item 6 — Month-end projection guard — ⚠️ SPEC/CODE DIVERGENCE, do not implement as written

**Scope**: N/A until re-scoped with the user
**Spec claims**: `OverviewTab.tsx` computes an "Expected month-end balance" by "dividing remaining balance by days elapsed," producing nonsensical figures like ₹55k on day 1, and that the fix is a `dayOfMonth <= 3` guard replacing `computedProjection` with a static message.

**What's actually in the code today** (verified by reading the full file, not just grepping the name):

1. There is exactly one "Expected month-end balance" element in the app — `OverviewTab.tsx:702-720`, inside the "🔔 Coming up" section. Its formula is:
   ```tsx
   {fmtInr(balance.remaining - balance.fixed_unpaid_total)}
   ```
   This does **not** divide by days elapsed or days left at all. On day 1, `balance.remaining` ≈ full income (nothing spent/paid yet) and `balance.fixed_unpaid_total` ≈ the full unpaid-fixed total, so this resolves to roughly the variable budget available (~₹42,154 per `CLAUDE.md`) — a sensible number, not a "₹55k nonsensical" one. There is no `computedProjection` variable or `dayOfMonth` guard to insert into, because the described bug doesn't reproduce with this formula on any day of the month, including day 1.

2. There *is* a genuine day-1 linear-extrapolation pattern elsewhere in the codebase — `/insights/projection/{month_key}` (`backend/main.py:1212-1269`) computes `daily_rate = spent / days_elapsed` and `projected = daily_rate * days_in_month`, which — with `days_elapsed = 1` on day 1 — would blow up any early expense into a wildly overstated month-end figure. But the component that displays that `projected` field, `BudgetHealthCard.tsx` (`frontend/react/src/components/shared/BudgetHealthCard.tsx:34`, `Projected ${fmtInr(p.projected)}`), is **not rendered anywhere in the app** — `grep -rl BudgetHealthCard frontend/react/src` only matches its own definition file. The live "Spending signals" section in `OverviewTab.tsx:616-649` uses `SignalCard` instead (`SpendingSignalsModal.tsx:19-59`), which never reads `p.projected` — it only shows `pct_spent`/`daily_rate`, both of which resolve to sensible values on day 1 (₹0 spent → 0%, ₹0/day).

3. `HeroBalanceCard.tsx:11` (`dailyBudget = balance.remaining / daysLeft`) divides by days **left**, not elapsed — on day 1 that's `income / ~30`, a normal pacing figure with no anomaly.

**Conclusion**: none of the currently-rendered UI reproduces the "nonsensical month-end projection" the spec describes. The one place that structurally could (`/insights/projection`'s `projected` field) isn't wired into any visible component right now.

**Recommendation — do not implement Item 6 until this is resolved with the user.** Two ways to proceed, and the choice changes the diff entirely:
- (a) Treat Item 6 as **moot** — no user-visible bug exists today, close it out with no code change.
- (b) The user actually wants a guard on the *"Expected month-end balance"* card specifically, even though its current formula isn't day-elapsed-based — in which case the ask is really "this number is only meaningful once some fixed bills are paid or some days have passed," a different root cause than stated, and the guard would need a different condition (e.g. gate on `balance.fixed_paid_total === 0 && dayOfMonth <= 3`, not a division-by-days check).

Do not silently pick one interpretation — ask before touching `OverviewTab.tsx` for this item.

---

## Files
| Item | File(s) |
|---|---|
| 1 — Mantra | `backend/ai_parser.py`, `backend/main.py` |
| 2 — Story | `backend/main.py` only (no `ai_parser.py` change needed) |
| 3 — Insight | `backend/main.py` only (no `ai_parser.py` change needed) |
| 4 — Tiny Win | `backend/main.py`, `frontend/react/src/types/index.ts` (type-only) |
| 5 — Due reminders | `backend/main.py` |
| 6 — Projection | **Blocked — needs user clarification, see above** |

## Execution Order

| # | Item | Effort | Risk | Depends on |
|---|------|--------|------|-------------|
| 5 | Due reminder threshold | XS | None | — |
| 4 | Tiny Win suppression | XS | None | Item 3 (`DAY1_GRACE` constant) |
| 3 | Insight suppression | XS | None | — (introduces `DAY1_GRACE`) |
| 2 | Story day-1 framing | XS | None | — |
| 1 | Mantra day-1 prompt | S | Low — new Claude prompt branch, needs manual QA of tone | — |
| 6 | Projection guard | — | — | **Blocked on user decision** |

Land 5 first (fully isolated, single-line filter). Then 3 before 4 since 4 reuses `DAY1_GRACE`. Then 2. Then 1 last among the backend items since it's the only one still calling Claude with new prompt text and needs a manual read of the actual generated sentence on a day-1 test. Items 1–4 can all go in one backend commit per the spec's own sequencing note, as long as 3 lands before/with 4.

## Definition of Done
- Manual test on a day-1 (or date-mocked) request to `/insights/mantra`, `/insights/story`, `/insights/monthly-insight`, `/insights/tiny-win`, `/fixed/due-reminders` for the current month — confirm each returns the new guarded copy/filtered list.
- `npm run build` passes for the `TinyWin` type change.
- Item 6 resolved (scoped or closed) with the user before any `OverviewTab.tsx` edit.

---

## Execution Log — 2026-07-01

Items 5, 3, 4, 2, 1 implemented in that order, matching the execution table above.

- **Item 5** — `DUE_REMINDER_WINDOW = 5` added above `get_due_reminders`; filter inserted before the final sort (`backend/main.py`).
- **Item 3** — `DAY1_GRACE = 3` added near `_insight_cache`; `monthly_insight` now returns the static neutral message when `today.day <= DAY1_GRACE` for the live month, before any Claude call or `balance` lookup (`backend/main.py`).
- **Item 4** — `tiny_win` reuses `DAY1_GRACE`; returns `{"win": None, "message": ...}` on day 1–3 or when `variable_total == 0`. `TinyWin.win` type widened to `string | null` (`frontend/react/src/types/index.ts`) — no component change needed since `OverviewTab.tsx:926` already gates on `{tinyWin && (...)}`.
- **Item 2** — `monthly_story` returns a static formatted sentence and skips `generate_monthly_story` entirely when `today.day == 1` for the live month (`backend/main.py`).
- **Item 1** — `generate_daily_mantra` gained a `day_of_month: int | None = None` param with a dedicated day-1 prompt branch (`backend/ai_parser.py`); `daily_mantra` endpoint computes and passes `day_of_month` (`backend/main.py`).

Verification: `ast.parse` + module import check on `backend/main.py` and `backend/ai_parser.py` (clean), `npm run build` in `frontend/react/` (clean, zero TS errors).

**Item 6 not implemented** — spec/code divergence, see `.claude/blocked/29-item6-month-end-projection.md` for the full writeup and re-scoping options. No `OverviewTab.tsx` or `BudgetHealthCard.tsx` changes were made.

Status: **5/6 items complete. Item 6 blocked pending user decision.**
