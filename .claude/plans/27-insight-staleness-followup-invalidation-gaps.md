# Implementation Plan: Insight Staleness Follow-up — Invalidation Gaps
**Spec**: `.claude/specs/27_insight-staleness-followup-invalidation-gaps.md`
**Date**: 2026-06-30
**Status**: ✅ Complete (implemented 2026-06-30)
**Branch**: `feature/sprint06261-ui-enhancement`

---

## Overview

3 actionable items (1 backend, 1 frontend, 1 verify-only).  
**Critical divergence from spec**: the spec's "confirmed missing" table overstates the problem.
After reading current code, only **one** backend endpoint is actually missing an invalidation call;
the other three listed in the spec's table already have it.

Items ordered smallest-blast-radius-first.

---

## Item 1 — Add missing cache invalidation to `log_from_template` (backend)
**Scope**: Backend-only
**File**: `backend/main.py` — line 795 (after `session.commit()` in `log_from_template`)

### Root cause (verified against current code)

The spec lists four endpoints as missing `_invalidate_month_caches`. **Three are already fixed**:

| Endpoint | Status |
|---|---|
| `PATCH /fixed/{id}/toggle` (`toggle_paid`) | ✓ has `_invalidate_month_caches` at line 704 |
| `PATCH /fixed/{id}/amount` (`update_fixed_amount`) | ✓ has `_invalidate_month_caches` at line 718 |
| `POST /expenses/bulk-delete` (`bulk_delete_expenses`) | ✓ has `_invalidate_month_caches` at line 663 |
| `POST /expense-templates/{id}/log` (`log_from_template`) | ✗ **missing** — see below |

The spec's "Also audit" list is also already handled:
- `POST /income` → `_invalidate_month_caches` at line 1055 ✓
- `PUT /income/{id}` → `_invalidate_month_caches` at line 1107 ✓
- `DELETE /income/{id}` → `_invalidate_month_caches` at line 1086 ✓
- `PUT /budget` → `_invalidate_all_user_caches` at line 1019 ✓
- `PUT /fixed-templates/{id}` → `_invalidate_all_user_caches` at line 916 ✓
- `DELETE /fixed-templates/{id}` → `_invalidate_all_user_caches` at line 939 ✓

`POST /fixed-templates` (line 863) has no invalidation, but this is correct: creating a new
template definition does not alter any seeded `Expense` rows or change balance-summary values
for existing months. No change needed there.

The **one real gap**: `log_from_template` (lines 778–799). It calls `session.commit()` at
line 795, returns at line 799, but never calls `_invalidate_month_caches`. Because this is
the "quick-add favourite" path, it is one of the highest-traffic mutation routes — which is
why the staleness symptom is so visible on the Today tab.

```python
# Current (main.py lines 793–799)
    session.add(tmpl)
    session.commit()
    session.refresh(exp)
    warnings = check_budget_warnings(session, month_key, user_id=current_user.id)
    balance  = get_balance_summary(session, month_key, user_id=current_user.id)
    return {"expense": exp, "warnings": warnings, "balance": balance}
```

### What to do

After `session.commit()` on line 795, add:

```python
    session.add(tmpl)
    session.commit()
    _invalidate_month_caches(current_user.id, month_key)   # ← add this line
    session.refresh(exp)
    warnings = check_budget_warnings(session, month_key, user_id=current_user.id)
    balance  = get_balance_summary(session, month_key, user_id=current_user.id)
    return {"expense": exp, "warnings": warnings, "balance": balance}
```

`month_key` is already computed at line 785 (`month_key = get_month_key(exp_date)`), so no
additional work is needed.

**Acceptance**: after logging a quick-add favourite and re-fetching
`/insights/mantra/{selMonth}` (or switching to Overview), the returned text reflects the
updated variable total / remaining balance.

---

## Item 2 — Re-fetch Today's Mantra after mutation on the Today tab (frontend)
**Scope**: Frontend-only
**File**: `frontend/react/src/components/tabs/QuickAddTab.tsx`

*(Depends on Item 1 being done first — without the backend invalidation, a re-fetch will
still return stale cached text.)*

### Root cause (verified against current code)

`TodaysMantraCard` (lines 38–130) is a self-contained component that owns its own fetch:

```tsx
useEffect(() => {
  api.get<DailyMantra>(`/insights/mantra/${selMonth}`)
    .then(r => setData(r.data))
    .catch(() => {});
}, [selMonth]);
```

The dep array is `[selMonth]` only. The component accepts no props and has no external
refresh signal.

`QuickAddTab` has two mutation handlers that call `onExpenseAdded?.()` when they succeed:
- `handleParse` (line 200)
- `handleFavLog` (line 218)

Neither triggers `TodaysMantraCard` to re-fetch. `onExpenseAdded` is wired to the parent
`DashboardPage` (which bumps the history tab's refresh counter) but has no path back into
`TodaysMantraCard`.

### What to do

1. **Add a `refreshKey` prop to `TodaysMantraCard`** — convert the internal `useEffect`
   dep array from `[selMonth]` to `[selMonth, refreshKey]`.

   ```tsx
   // Before
   function TodaysMantraCard() {
     const { selMonth } = useMonth();
     ...
     useEffect(() => {
       api.get<DailyMantra>(`/insights/mantra/${selMonth}`)
         .then(r => setData(r.data))
         .catch(() => {});
     }, [selMonth]);
   ```

   ```tsx
   // After
   function TodaysMantraCard({ refreshKey }: { refreshKey: number }) {
     const { selMonth } = useMonth();
     ...
     useEffect(() => {
       api.get<DailyMantra>(`/insights/mantra/${selMonth}`)
         .then(r => setData(r.data))
         .catch(() => {});
     }, [selMonth, refreshKey]);
   ```

2. **Add `mantraRefresh` state to `QuickAddTab`** and pass it down:

   ```tsx
   // In QuickAddTab (near the top of the component, alongside existing state)
   const [mantraRefresh, setMantraRefresh] = useState(0);
   ```

3. **Bump `mantraRefresh` in both mutation handlers** after success:

   In `handleParse` (currently calls `onExpenseAdded?.()` at line 200):
   ```tsx
   onExpenseAdded?.();
   setMantraRefresh(k => k + 1);
   ```

   In `handleFavLog` (currently calls `onExpenseAdded?.()` at line 218):
   ```tsx
   onExpenseAdded?.();
   setMantraRefresh(k => k + 1);
   ```

4. **Pass `refreshKey` to the card** at the render site (line 242):

   ```tsx
   // Before
   <TodaysMantraCard />

   // After
   <TodaysMantraCard refreshKey={mantraRefresh} />
   ```

No debounce is needed — the re-fetch fires once immediately after the mutation completes,
and the backend's in-memory cache has already been invalidated by Item 1.

**Acceptance**: logging an expense or tapping a favourite on the Today tab causes the
Today's Mantra card to update in place without switching tabs.

---

## Item 3 — Verify Overview Story/Insight and first-month guard (no code changes expected)
**Scope**: Verification only — implement only if gaps are found

### Item 3a — Overview re-fetch on tab switch (Story/Insight)

`DashboardPage` renders `OverviewTab` with a conditional (line 105):

```tsx
{tab === "overview" && <ErrorBoundary><OverviewTab onTabChange={onTabChange} /></ErrorBoundary>}
```

This means switching away from Overview unmounts the component; switching back remounts it
and triggers a full re-fetch via `useEffect([load])`. Once Item 1 lands, returning to Overview
after a mutation on the Today or Fixed tab will fetch fresh Story/Insight text from the
server (which is no longer cached for the current month per Spec 26 Item 3).

**Verification step**: with Item 1 applied, log a quick-add expense → switch to Overview.
Confirm Story and monthly-insight reflect the updated numbers.

**If "instant, without leaving the view" is required** (i.e., Story/Insight must refresh in
place on the Overview tab itself after a Today-tab mutation): this would require threading a
cross-tab refresh signal from `DashboardPage` down into `OverviewTab` — a non-trivial
addition. Only do this if verification shows it's needed by the acceptance criteria.

### Item 3b — First-month comparative insight guard

**Frontend** (`OverviewTab.tsx` lines 267–268):

```tsx
const isFirstMonth =
  prevSummary === null || (prevSummary.balance?.variable_total ?? 0) === 0;
```

`prevSummary` is fetched with `.catch(() => null)`, so it is `null` only on network error.
For a true first-month user, the prior month's summary returns a zero-filled object (not null),
but `variable_total` is 0 — so `isFirstMonth` evaluates to `true`. The `isSafeInsight()`
backstop (line 179) then filters out any comparative text that slipped through.
**This path appears correct; no change expected.**

**Backend** (`budget_rules.py` `has_prior_activity`, line 143–160):

The function returns `True` if any `Expense` or `IncomeEntry` exists with
`month_key < this_month` — including auto-seeded fixed rows. If a new user's signup triggers
retroactive seeding into prior months, this could make them appear as "returning". However:
- `seed_fixed_expenses` typically only seeds the *current* month.
- The `monthly_insight` backend guard additionally checks `if not prev_variable` (the prior
  month's `variable_total`) and exits the comparative branch when it is falsy. A prior month
  with only auto-seeded fixed rows and no variable spending produces `variable_total = 0`,
  so the guard fires correctly.

**Verification step**: create a test user with only seeded fixed expenses in prior months (no
variable spending history). Confirm `/insights/monthly-insight/{current_month}` returns an
absolute (non-comparative) insight.

**If a gap is found**: update `has_prior_activity` to require at least one **variable**
`Expense` row (`is_fixed == False`) in a prior month, not just any row. This is a two-line
change in `budget_rules.py`.

---

## Execution order

1. **Item 1** — single line insertion in `backend/main.py:795`. No tests to update. Lowest
   risk; unblocks Items 2 and 3 from being testable.
2. **Item 2** — three small edits in `QuickAddTab.tsx` (prop, state, bump×2, pass-down). Can
   be done immediately after Item 1.
3. **Item 3** — verify manually; write the gap fix (if any) only after verification confirms
   it's needed.
