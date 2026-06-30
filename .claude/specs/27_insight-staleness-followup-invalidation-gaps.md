# Spec 27 — Insight Staleness Follow-up: Missing Cache Invalidations + Mantra Re-fetch
**Date**: 2026-06-30
**Status**: ✅ Complete (implemented 2026-06-30)
**Branch**: `feature/sprint06261-ui-enhancement` *(confirm active branch before starting)*
**Follows**: `26_insight-staleness-and-realtime-sync.md`
**Source**: re-verification of Spec 26 against current code (June 30 2026), prompted by
live self-feedback (June 28 screenshots) still showing stale Story / Insight / Mantra.

---

## Why this exists

Spec 26 is marked **✅ Complete**, and most of it did land:
- Mantra cache key is now `(user_id, month_key, today)` with a matching invalidation loop ✓
- `_invalidate_all_user_caches(user_id)` helper exists ✓
- Story/Insight skip caching for the **current** month (regenerate each call) ✓
- `monthly_insight` uses `has_prior_activity` + the `if not prev_variable` first-month guard ✓

**But Spec 26 Item 1 was not fully applied.** The per-endpoint
`_invalidate_month_caches(...)` calls it called for were added to the expense CRUD and the
pool endpoints, but **missed several mutations that change balance-affecting numbers**.
Result: the symptoms persist on exactly the paths the user hits most (marking a bill paid,
quick-add favourites).

This spec closes those gaps and adds the one frontend piece Spec 26 didn't scope: the
Today's-Mantra card never re-fetches after an in-tab mutation.

---

## Item 1 — Add the missing cache invalidations (backend)
**Scope**: Backend-only · **Priority**: highest (fixes the residual #1–#4)

**Confirmed missing in current `backend/main.py`** (read June 30 — no
`_invalidate_month_caches` / `_invalidate_all_user_caches` call present):

| Endpoint | Function | Affects | Maps to |
|---|---|---|---|
| `PATCH /fixed/{id}/toggle` | `toggle_paid` | `fixed_paid/unpaid_total`, remaining, bills % | **Issue #1** (mark bills paid) |
| `PATCH /fixed/{id}/amount` | `update_fixed_amount` | fixed totals, remaining | #1 family |
| `POST /expense-templates/{id}/log` | `log_from_template` | variable_total, remaining | #3 (quick-add favourite) |
| `POST /expenses/bulk-delete` | `bulk_delete_expenses` | variable_total, remaining | #3 family |

**Fix:** after `session.commit()` in each, call `_invalidate_month_caches(current_user.id, <month_key>)`.
- `toggle_paid` / `update_fixed_amount`: month from `exp.month_key`.
- `log_from_template`: month from the `month_key` it already computes for the new expense.
- `bulk_delete_expenses`: the deleted rows may span months — collect their `month_key`s and
  invalidate each, or use `_invalidate_all_user_caches(current_user.id)` (simplest, correct).

**Also audit (Spec 26 listed these under Item 1 — confirm they actually got the call, since
the fixed-toggle one didn't):**
`POST /income`, `PUT /income/{id}`, `DELETE /income/{id}`, `PUT /budget`, and the
`POST/PUT/DELETE /fixed-templates/*` endpoints. Add `_invalidate_month_caches` (or
`_invalidate_all_user_caches` where the affected month set is ambiguous — caps and templates)
to any that are missing it. *(Pool endpoints already have it — leave as-is.)*

**Acceptance:** after marking a bill paid, logging a favourite, bulk-deleting, or editing
income/cap, re-fetching `/insights/story|monthly-insight|mantra` returns text reflecting the
new numbers.

---

## Item 2 — Today's Mantra must re-fetch after an in-tab mutation (frontend)
**Scope**: Frontend-only · **Priority**: high (fixes residual #4)

**Confirmed gap:** `TodaysMantraCard` (in `tabs/QuickAddTab.tsx`) fetches
`/insights/mantra/{selMonth}` only on `[selMonth]`. `handleParse` (add expense) and
`handleFavLog` (quick-add) never re-fetch it — so even with Item 1's cache now correctly
busted server-side, the card keeps showing the previous mantra until the month changes or the
component remounts. That is exactly "Today's mantra out of sync with real-time balance."

**Fix:** re-fetch the mantra after a successful mutation on the Today tab. Wire
`TodaysMantraCard`'s fetch to a refresh signal that bumps on add/log (reuse the
`onExpenseAdded` / `bumpRefresh` mechanism already threaded through `QuickAddTab`, or lift the
mantra fetch so it shares that trigger). A short debounce is fine.

**Acceptance:** logging an expense on the Today tab updates the mantra without leaving the tab.

---

## Item 3 — Verify the Overview Story/Insight refresh path (frontend)
**Scope**: Frontend verification · **Priority**: medium

`OverviewTab` mounts on tab-switch (conditional render in `DashboardPage`), and the current
month is no longer cached server-side (Spec 26 Item 3), so navigating to Overview should fetch
fresh Story/Insight. Confirm this holds — i.e. that switching away and back after a mutation
shows updated text once Item 1 lands.

- If it does: no change needed (the residual staleness was purely the Item 1 backend gap).
- If "instant, without leaving the view" is desired: wire the Story/Insight fetches to the
  same refresh signal as Item 2 so they re-fetch in place after a mutation.

**Acceptance:** Story ("June in one sentence") and Insight reflect the latest numbers after a
mutation + a return to Overview (at minimum), with no stale % / remaining.

---

## Item 4 — Confirm Issue #5 (first-month comparison) is actually resolved
**Scope**: Verification · **Priority**: medium

Backend appears handled in current code (`monthly_insight` uses `has_prior_activity` and
forces the non-comparative branch when `prev_variable` is falsy). Two things to verify rather
than re-implement:
1. **`has_prior_activity`** counts any `Expense`/`IncomeEntry` with `month_key < this month`,
   **including auto-seeded fixed rows** — so a user with seeded prior-month fixed expenses can
   still be treated as "returning". Confirm whether seeded/zero-variable prior months can slip
   a comparison through; if so, gate on *meaningful prior variable activity*, not mere row
   existence.
2. **Frontend `isFirstMonth`** (Spec 26 Item 4, `OverviewTab.tsx`) — confirm it no longer
   relies on `prevSummary === null` (the summary endpoint never returns null) and that the
   `isSafeInsight()` backstop fires for true first-month users.

**Acceptance:** a user whose first real entries are this month never sees a "vs last month" /
"jumped X%" insight.

---

## Out of scope
- Re-doing anything Spec 26 already implemented correctly (mantra key, current-month cache
  policy, first-month backend guard).
- Persisting caches across process restart (still in-memory, acceptable).
- The Anthropic **credit-balance** outage (account-side; already resolved) and the hardcoded
  model string in `ai_parser.py` (separate hygiene item, not staleness).

## Files
- `backend/main.py` — Item 1 invalidation calls + audit.
- `frontend/react/src/components/tabs/QuickAddTab.tsx` — Item 2 (`TodaysMantraCard` re-fetch).
- `frontend/react/src/components/tabs/OverviewTab.tsx` — Items 3 & 4 verification (change only
  if verification shows a gap).
- `backend/budget_rules.py` — only if Item 4 needs a "meaningful prior activity" helper.

## Order
1. Item 1 (closes the actual residual bug — additive, low risk).
2. Item 2 (Today mantra re-fetch).
3. Items 3 & 4 (verify; implement only the confirmed gaps).
