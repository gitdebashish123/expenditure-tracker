# Post-Migration Sprint 1 — Bug & Enhancement Spec
**Observed after React Migration (T2.1–T2.10)**
**Date:** June 2026
**Status:** Open — awaiting implementation

---

## Overview

8 issues observed after the first React migration sprint. Each is fully specified
below with root cause, affected files, acceptance criteria, and priority.
No code has been modified — this is a spec-only document.

---

## Issue 1 — Month Selector Stale at Midnight

**Symptom:** At 12:00am on June 1, the month selector still shows "May 2026".
After a few hours (next morning) it corrects itself.

**Root cause:**
`MonthContext.tsx` initialises `CURRENT_MONTH` as a module-level constant:
```typescript
const CURRENT_MONTH = new Date().toISOString().slice(0, 7);
```
This value is computed **once** when the JS bundle first loads. If the app is left
open across midnight, `CURRENT_MONTH` is never recalculated. The context provider
also never re-runs the initialiser — `useState(CURRENT_MONTH)` only reads the
constant once at mount. The month only "corrects" after a full page reload.

**Affected file:** `frontend/react/src/context/MonthContext.tsx`

**Fix approach:**
- Replace the static constant with a function `getCurrentMonth()` that reads
  `new Date()` at call time.
- Add a `useEffect` that runs a daily timer (or `visibilitychange` event listener)
  to recalculate and update `selMonth` when the date ticks over midnight.
- The `visibilitychange` approach (re-check on tab focus) is simpler and catches
  the case where the user opens the app the next morning without a reload.

**Acceptance criteria:**
- Open the app at 11:59pm, wait for midnight without reloading.
- Month selector updates to the new month automatically within 60 seconds.
- OR: Close the app at 11:59pm, reopen at 12:01am → correct month shown immediately.

**Priority:** Medium

---

## Issue 2 — Due Reminder / Fixed Bill Settings Not Visible on Mobile

**Symptom:** The due-day reminder dropdown ("1st of month" etc.) in
Settings → Monthly Bills is not visible or accessible on mobile screens.

**Root cause:**
`TemplateEditRow` in `BillsSection.tsx` renders four elements in a single flex row:
`name input | amount input | due_day select | save icon | delete icon`

On a narrow mobile screen (~375px), this row overflows horizontally or collapses
the `select` to zero width because the name input takes `flex-1` and the
`w-28` select has no minimum constraint. The row has no responsive layout
breakpoint — it uses the same layout on desktop and mobile.

**Affected file:** `frontend/react/src/components/settings/BillsSection.tsx`
  → `TemplateEditRow` component

**Fix approach:**
- On mobile (`< sm`): stack the fields vertically (2-column grid: name+amount
  on one row, due-day select full width on next row, action icons right-aligned).
- On desktop (`sm+`): keep the existing single-row layout.
- Use Tailwind responsive grid: `grid grid-cols-2 sm:flex`.

**Acceptance criteria:**
- Open Settings → Monthly Bills on a 375px viewport.
- Expand a category group → all fields (name, amount, due-day, save, delete) are
  fully visible and tappable.
- Due-day dropdown opens correctly on mobile tap.

**Priority:** High — users cannot set reminders from mobile at all

---

## Issue 3 — Fixed Expense Edit/Delete Not Visible on Mobile

**Symptom:** Edit (pencil) and delete (trash) icons for fixed expense entries
are visible on desktop but completely hidden on mobile.

**Root cause:**
`FixedExpenseRow.tsx` has no inline edit/delete — it only has the tick toggle.
The edit/delete for the **template** (name, amount) is in `BillsSection.tsx`
`TemplateEditRow`, which has the same overflow issue described in Issue 2.

Additionally, the `FixedTab` itself shows the seeded expense rows from
`GET /fixed/{month}` — these rows only have a tick. There is no way to edit
or delete individual fixed expense instances from the Fixed tab on any device.
The template management (which controls future months) is only in Settings.

**Affected files:**
- `frontend/react/src/components/tabs/FixedExpenseRow.tsx`
- `frontend/react/src/components/settings/BillsSection.tsx`

**Fix approach:**
- Cascades from Issue 2 fix (responsive TemplateEditRow).
- Additionally: add a subtle edit icon to `FixedExpenseRow` that opens an
  inline edit for the current month's instance amount (useful when a bill
  is slightly different this month vs the template amount).

**Acceptance criteria:**
- On mobile, Settings → Monthly Bills → expand Housing → Rent row shows
  all edit controls without horizontal scroll.
- Tapping the edit icon works and the save confirms via toast.

**Priority:** High

---

## Issue 4 — Income Source Restricted to "Salary"

**Symptom:** The income section placeholder text says "e.g. Infosys Salary,
Freelance" but the `source` field defaults to "Salary" and the step is ₹1000.
Users receiving dividends, FD interest, rental income, or bonus can't naturally
represent their income type.

**Root cause:**
`IncomeSection.tsx` uses a single text input for source with `step="1000"` on
the amount. This is functional but the UX implies salary-only. More importantly,
the backend `POST /income` only stores a single income record per month — users
with multiple income sources (salary + dividend + FD maturity) cannot add them
separately.

**Affected files:**
- `frontend/react/src/components/settings/IncomeSection.tsx`
- Backend: `POST /income` endpoint — currently upserts a single record per
  `(user_id, month_key)`. Would need to support multiple records for full fix.

**Fix approach (two tiers):**

*Tier 1 — UI only (quick win, no backend change):*
- Replace the free-text source input with a dropdown of common types:
  Salary, Freelance, Dividend, FD/RD Interest, Rental, Bonus, Other.
- With "Other" allowing a free-text override.
- Change `step` on amount from `1000` to `1` so odd amounts like ₹4,521
  (FD interest) can be entered without browser validation warnings.
- Update placeholder to reflect multiple source types.

*Tier 2 — Full multi-income (backend change required):*
- Change `POST /income` to support multiple income entries per month.
- Add a list UI that allows adding/removing income sources.
- This is a more significant change — should be a separate sprint item.

**Acceptance criteria (Tier 1):**
- Source dropdown contains at least: Salary, Freelance, Dividend, FD/RD Interest,
  Rental, Bonus, Other.
- Amount field accepts ₹4,521 without browser validation warning.
- Existing Salary users see no change in behaviour.

**Priority:** Medium (Tier 1), Low (Tier 2)

---

## Issue 5 — Session Never Expires (No Inactivity Timeout)

**Symptom:** User leaves the app open for hours (or overnight). The session
remains active — no logout occurs. The JWT token stored in `localStorage`
has a server-side expiry but the frontend never checks it proactively.

**Root cause:**
`AuthContext.tsx` only validates the token **on mount** (app load). After that,
the 401 interceptor in `api/client.ts` handles expired tokens reactively —
only when an API call returns 401. If the user leaves the app idle, no API
calls are made and the stale session is never detected.

The app has no inactivity timer. `localStorage` tokens persist across browser
sessions indefinitely (unlike `sessionStorage` which clears on tab close).

**Affected files:**
- `frontend/react/src/context/AuthContext.tsx`
- `frontend/react/src/api/client.ts`

**Fix approach:**
- Add an inactivity timer (5 minutes of no user interaction).
- Reset the timer on `mousemove`, `keydown`, `touchstart`, `scroll` events.
- On timeout: call `logout()` and redirect to `/login` with a "Session expired
  due to inactivity" message shown on the login page.
- Show a 60-second warning toast before the timeout fires so the user can
  extend the session by clicking anywhere.
- Timer should be a `useEffect` in `AuthContext` or a dedicated
  `useInactivityTimer` hook.

**Acceptance criteria:**
- User logs in, does not interact for 5 minutes → "Your session is about to expire"
  toast appears at 4 minutes.
- At 5 minutes → auto logout → redirected to `/login` with message.
- Any click/keypress/scroll resets the 5-minute timer.
- Timer only active when user is logged in.

**Priority:** High — security requirement

---

## Issue 6 — Editing Fixed Template in Settings Does Not Reflect in Fixed Tab

**Symptom:** User edits a bill name or amount in Settings → Monthly Bills,
saves successfully (API call succeeds), but the Fixed tab still shows the
old values until a full page reload.

**Root cause:**
`BillsSection.tsx` calls `onSaved()` after a successful save, which calls
`load()` to re-fetch templates. However, `FixedTab.tsx` has its own independent
state — it fetches from `GET /fixed/{month}` which returns **seeded expense
rows**, not templates. These seeded rows are created once by `seed_fixed_expenses`
on the backend and stored in the `expense` table with their original values.

When a template is updated (`PUT /fixed-templates/{id}`), the backend updates
the template record but does NOT update already-seeded expense rows for the
current month. So:
- Settings shows the new template name/amount (because it reads from templates).
- Fixed tab shows the old name/amount (because it reads from already-seeded expenses).

**Affected files:**
- Backend: `PUT /fixed-templates/{id}` endpoint — should also update the current
  month's seeded expense rows for this template.
- `frontend/react/src/components/settings/BillsSection.tsx`
- `frontend/react/src/components/tabs/FixedTab.tsx`

**Fix approach:**

*Backend fix (correct approach):*
When `PUT /fixed-templates/{id}` is called, also update any existing `Expense`
rows for the current month that were seeded from this template:
```python
# After updating the template, sync current month's seeded expenses
session.exec(
    update(Expense)
    .where(Expense.fixed_template_id == template_id)
    .where(Expense.month_key == get_month_key())
    .where(Expense.user_id == current_user.id)
    .values(vendor=updated.name, amount=updated.amount)
)
```

*Frontend fix (cache bust):*
After `onSaved()` in `TemplateEditRow`, emit a custom event or use a shared
state signal to tell `FixedTab` to re-fetch its data.

**Acceptance criteria:**
- Edit "Rent" from ₹16,500 to ₹17,000 in Settings → Save.
- Fixed tab immediately shows "Rent ₹17,000" without page reload.
- Edit "Cook" to "Domestic Help" in Settings → Save.
- Fixed tab immediately shows "Domestic Help" without page reload.

**Priority:** High — data consistency bug, very visible to users

---

## Issue 7 — Budget Health Messages Need User-Friendly Text

**Symptom:**
- "On track" status is fine but `warning` and `danger` statuses show only
  "Projected ₹X,XXX" which is not a clear user action message.
- `over` status shows "Over budget" which is correct but lacks actionable guidance.
- The projected amount label for `danger`/`warning` statuses is a number,
  not a human-readable warning.

**Root cause:**
`BudgetHealthCard.tsx` `STATUS_CONFIG`:
```typescript
danger:  { label: ""   },   // empty — falls back to "Projected ₹X,XXX"
warning: { label: ""   },   // empty — falls back to "Projected ₹X,XXX"
```
The fallback `label = cfg.label || \`Projected ${fmtInr(p.projected)}\`` is
technically informative but not action-oriented. Users don't immediately
understand what "Projected ₹8,500" means in the context of a budget.

**Affected file:**
`frontend/react/src/components/shared/BudgetHealthCard.tsx`

**Fix approach:**
Replace status labels with human-readable messages that include the % threshold:

| Status | Condition | New label |
|---|---|---|
| `safe` | < 60% spent | "On track" |
| `warning` | 60–79% spent | "⚠️ Slow down — 80% of limit near" |
| `danger` | 80–99% spent, projected to exceed | "🔴 Likely to exceed limit" |
| `over` | ≥ 100% spent | "🚫 Limit exceeded — ₹X over" |

For `over`, show the actual overage amount: `fmtInr(p.spent - p.limit)` over budget.

For `warning`/`danger`, show remaining budget prominently:
`fmtInr(p.limit - p.spent) remaining` rather than the projected amount.

**Acceptance criteria:**
- Category at 65% → "⚠️ Slow down — 80% of limit near" shown.
- Category at 85% → "🔴 Likely to exceed limit" shown.
- Category at 110% → "🚫 Limit exceeded — ₹2,500 over" shown (actual overage).
- Messages shown on both mobile and desktop without truncation.

**Priority:** Medium — UX improvement, not blocking

---

## Issue 8 — Amount Input Validation Error on Mobile (step mismatch)

**Symptom:** Entering ₹585 for a fixed bill amount shows a browser validation
popup: "Please enter a valid value. The two nearest valid values are 500 and 600."

**Root cause:**
`TemplateEditRow` in `BillsSection.tsx` amount input has `step="100"`:
```tsx
<input type="number" min="0" step="100" ... />
```
HTML5 number inputs with `step` enforce that `value = min + n * step`. With
`min=0` and `step=100`, valid values are 0, 100, 200, ... 500, 600. The value
585 is not on this grid, so the browser blocks form submission.

The same issue was fixed earlier in `PoolCard.tsx` (changed to `step="1"`)
but `TemplateEditRow` in `BillsSection.tsx` was not updated at the same time.

**Affected file:**
`frontend/react/src/components/settings/BillsSection.tsx`
→ `TemplateEditRow` amount input
→ `handleAddBill` form amount input (also uses `step="100"`)

Also check:
- `frontend/react/src/components/settings/CapsSection.tsx` — uses `step="500"`
  (same issue for budget caps like ₹4,500)
- `frontend/react/src/components/onboarding/OnboardingWizard.tsx` — step 3 caps

**Fix:**
Change all financial amount inputs to `step="1"` with `min="0"`.
The `step` attribute should only be used for UX affordance (arrow key increments)
not for validation. Users entering real Indian bill amounts like ₹585, ₹1,201,
₹4,945 will always hit this on odd amounts.

**Affected inputs and their current step values:**
| File | Input | Current step | Fix |
|---|---|---|---|
| `BillsSection.tsx` TemplateEditRow | amount | 100 | → 1 |
| `BillsSection.tsx` Add Bill form | amount | 100 | → 1 |
| `CapsSection.tsx` | budget caps | 500 | → 1 |
| `OnboardingWizard.tsx` step 3 | caps | 500 | → 1 |
| `IncomeSection.tsx` | income amount | 1000 | → 1 |

**Acceptance criteria:**
- Enter ₹585 as bill amount → saves without browser validation popup.
- Enter ₹4,521 as income → saves without browser validation popup.
- Enter ₹3,750 as spending cap → saves without browser validation popup.
- Arrow keys on amount inputs still increment by a sensible amount (can use
  `step="1"` and rely on keyboard UX rather than browser enforcement).

**Priority:** High — validation error actively blocks data entry on mobile

---

## Implementation Order (suggested)

| # | Issue | Priority | Effort | Files |
|---|---|---|---|---|
| 8 | step="1" on all amount inputs | High | 30 min | 4 files, trivial change |
| 5 | Inactivity session timeout | High | 2h | AuthContext, new hook |
| 6 | Template edit syncs to Fixed tab | High | 3h | backend + 2 frontend files |
| 2 | Reminder dropdown visible on mobile | High | 2h | BillsSection |
| 3 | Edit/delete visible on mobile | High | 1h | cascades from #2 |
| 7 | Budget health friendly messages | Medium | 1h | BudgetHealthCard |
| 1 | Month selector midnight fix | Medium | 1h | MonthContext |
| 4 | Income source types | Medium | 2h | IncomeSection |

---

## Files NOT modified by this spec

- `frontend/app.py` — Streamlit reference app, untouched throughout
- `backend/main.py` — only Issue 6 requires a backend change
- All other React components not listed above

---

*Spec created: June 1, 2026*
*Observed on: SanchaySaathi React frontend post T2.1–T2.10 migration*
