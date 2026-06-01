# Plan: Post-Migration Sprint 1 Bug Fixes
**Source spec:** `.claude/specs/post_migration_sprint1_bugs.md`
**Target plan file:** `.claude/plans/01-sprint7-react-migration-phase2-v2.md`
**Branch:** `feature/sprint7-react-migration-phase2`

---

## Context

8 bugs observed after the React migration (T2.1–T2.10). They span mobile layout
failures, a security gap (no inactivity logout), a data-consistency bug
(template edits not propagating to the Fixed tab), and UX copy issues.
The spec prioritises them by impact; this plan follows that order.

No changes to `frontend/app.py` (Streamlit legacy) or any file not listed below.

---

## Ordered Implementation Steps

### Step 1 — Issue 8: `step="1"` on all financial amount inputs
**Priority: High | Effort: ~30 min**

Root cause: HTML5 `step` attribute treats value grid as a validation constraint.
`step="100"` blocks saving ₹585; `step="500"` blocks ₹4,521.

**Files & changes:**

| File | Location | Current | Fix |
|---|---|---|---|
| `frontend/react/src/components/settings/BillsSection.tsx` | `TemplateEditRow` amount input | `step="100"` | `step="1"` |
| `frontend/react/src/components/settings/BillsSection.tsx` | `handleAddBill` form amount | `step="100"` | `step="1"` |
| `frontend/react/src/components/settings/CapsSection.tsx` | budget cap inputs | `step="500"` | `step="1"` |
| `frontend/react/src/components/settings/IncomeSection.tsx` | income amount | `step="1000"` | `step="1"` |
| `frontend/react/src/components/onboarding/OnboardingWizard.tsx` | Step 1 income amount | `step="1000"` | `step="1"` |
| `frontend/react/src/components/onboarding/OnboardingWizard.tsx` | Step 2 bill amount | `step="100"` | `step="1"` |
| `frontend/react/src/components/onboarding/OnboardingWizard.tsx` | Step 3 caps | `step="500"` | `step="1"` |

All inputs keep `min="0"` and `type="number"`.

---

### Step 2 — Issue 5: Inactivity session timeout
**Priority: High | Effort: ~2h**

Root cause: `AuthContext` only validates the JWT on mount. No activity tracking.

**New file:** `frontend/react/src/hooks/useInactivityTimer.ts`
- Accepts `{ timeoutMs, warningMs, onWarn, onTimeout, enabled }` params
- Attaches `mousemove`, `keydown`, `touchstart`, `scroll` listeners on `window`
- `useEffect` cleanup removes listeners on unmount
- `setTimeout` chain: at `warningMs` (4 min = 240 000ms) calls `onWarn()`;
  at `timeoutMs` (5 min = 300 000ms) calls `onTimeout()`
- Each user activity event resets both timers via `clearTimeout` + restart
- Only active when `enabled: boolean` is true (i.e. user is logged in)

**Change: `frontend/react/src/context/ToastContext.tsx`**
- Add `"warning"` to `ToastType` union
- Add entry to `TYPE_CLASSES`: `warning: "bg-amber-500/15 border-amber-500/30 text-amber-300"`

**Change: `frontend/react/src/context/AuthContext.tsx`**
- Import `useInactivityTimer` hook and `useToast`
- Wire up:
  ```typescript
  const { toast } = useToast();
  useInactivityTimer({
    enabled: !!user,
    warningMs: 4 * 60 * 1000,
    timeoutMs: 5 * 60 * 1000,
    onWarn: () => toast("Your session expires in 1 minute — click to stay logged in",
                        { type: "warning", icon: "⏱️" }),
    onTimeout: logout,
  });
  ```
- No change to `client.ts` (401 interceptor already handles server-side expiry)

---

### Step 3 — Issue 6: Template edit syncs to Fixed tab
**Priority: High | Effort: ~3h**

Root cause (two parts):
1. Backend `PUT /fixed-templates/{id}` updates template but NOT already-seeded `Expense` rows.
2. Frontend `FixedTab` fetches `GET /fixed/{month}` independently; has no signal that a template changed.

**Backend fix — `backend/main.py`, `update_template()` function (~line 863):**

After `session.commit()` on the template, add:
```python
# Sync name/amount to current+future seeded expense rows
if update.name is not None or update.amount is not None:
    current_month = get_month_key()
    seeded_rows = session.exec(
        select(Expense).where(
            Expense.fixed_template_id == template_id,
            Expense.month_key >= current_month,
            Expense.user_id == current_user.id,
        )
    ).all()
    for row in seeded_rows:
        if update.name is not None:
            row.vendor = tmpl.name
        if update.amount is not None:
            row.amount = tmpl.amount
        session.add(row)
    session.commit()
```

**Frontend fix — custom event bus (no new context needed):**

In `BillsSection.tsx` `TemplateEditRow.handleSave()`, after successful PUT:
```typescript
window.dispatchEvent(new CustomEvent('fixedTemplateUpdated'));
```

In `FixedTab.tsx`, add a second `useEffect`:
```typescript
useEffect(() => {
  const handler = () => load();
  window.addEventListener('fixedTemplateUpdated', handler);
  return () => window.removeEventListener('fixedTemplateUpdated', handler);
}, [load]);
```

---

### Step 4 — Issues 2 & 3: `TemplateEditRow` responsive layout
**Priority: High | Effort: ~2h**

Root cause: 5 elements in one `flex` row overflow on 375px screens.

**Change: `BillsSection.tsx` `TemplateEditRow` wrapper div and its children**

Replace single flex row with a responsive grid:
```tsx
// Wrapper
<div className="grid grid-cols-[1fr_auto] gap-x-2 gap-y-2 sm:flex sm:items-center px-3 py-2">
  {/* Name — spans 2 cols on mobile, flex-1 on desktop */}
  <input className="col-span-2 sm:flex-1 min-w-0 ..." ... />
  {/* Amount — col 1 on mobile */}
  <input className="..." ... />
  {/* Due-day — col 2 on mobile, w-28 on desktop */}
  <select className="w-full sm:w-28 ..." ... />
  {/* Action icons — col 2 of row 2 on mobile */}
  <div className="flex gap-2 justify-end sm:justify-start col-start-2">
    <save icon> <delete icon>
  </div>
</div>
```

**`FixedExpenseRow.tsx` inline edit (Issue 3 extension):**

Add a pencil icon to `FixedExpenseRow` that reveals an inline amount field for
editing the current month's instance (calls `PATCH /fixed/{id}/amount`):
- Tapping pencil → shows `<input type="number" step="1" defaultValue={item.amount} />`
  inline replacing the amount display
- On blur / Enter → `api.patch('/fixed/{item.id}/amount', { params: { amount } })` +
  calls a new `onAmountChange` prop to signal parent to refresh
- This edit is month-specific only (template is unaffected)

---

### Step 5 — Issue 7: Budget health card user-friendly messages
**Priority: Medium | Effort: ~1h**

Root cause: `danger` and `warning` labels are empty strings in `STATUS_CONFIG`.

**Change: `frontend/react/src/components/shared/BudgetHealthCard.tsx`**

Update `STATUS_CONFIG`:
```typescript
const STATUS_CONFIG = {
  over:    { dot: "🔴", accent: "#ef4444", bg: "rgba(239,68,68,0.08)",   label: "" },        // computed dynamically
  danger:  { dot: "🟠", accent: "#f59e0b", bg: "rgba(245,158,11,0.07)",  label: "🔴 Likely to exceed limit" },
  warning: { dot: "🟡", accent: "#eab308", bg: "rgba(234,179,8,0.06)",   label: "⚠️ Slow down — 80% of limit near" },
  safe:    { dot: "🟢", accent: "#34d399", bg: "rgba(52,211,153,0.05)",  label: "On track" },
};
```

Update label computation (line 31 area):
```typescript
const label =
  p.status === "over"
    ? `🚫 Limit exceeded — ${fmtInr(p.spent - p.limit)} over`
    : cfg.label || `Projected ${fmtInr(p.projected)}`;
```

---

### Step 6 — Issue 1: Month selector midnight fix
**Priority: Medium | Effort: ~1h**

Root cause: `CURRENT_MONTH` is a static module-level constant evaluated once at bundle load.

**Change: `frontend/react/src/context/MonthContext.tsx`**

```typescript
// Replace module-level constant with a function
const getCurrentMonth = () => new Date().toISOString().slice(0, 7);

export function MonthProvider({ children }: { children: React.ReactNode }) {
  const [selMonth, setSelMonth]         = useState(getCurrentMonth);
  const [currentMonth, setCurrentMonth] = useState(getCurrentMonth);

  // Re-check on tab focus — catches "open app next morning" case
  useEffect(() => {
    const handler = () => {
      const now = getCurrentMonth();
      if (now !== currentMonth) setCurrentMonth(now);
    };
    document.addEventListener("visibilitychange", handler);
    return () => document.removeEventListener("visibilitychange", handler);
  }, [currentMonth]);

  return (
    <MonthContext.Provider
      value={{ selMonth, setSelMonth, isCurrent: selMonth === currentMonth }}
    >
      {children}
    </MonthContext.Provider>
  );
}
```

Add `useEffect` to React import (already has `useState`).

---

### Step 7 — Issue 4: Income source types (Tier 1 only)
**Priority: Medium | Effort: ~2h**

Backend stays unchanged (`POST /income` still upserts a single record per month).

**Change: `frontend/react/src/components/settings/IncomeSection.tsx`**

- Replace `<input type="text" value={source}>` with a `<select>` containing:
  `Salary | Freelance | Dividend | FD/RD Interest | Rental | Bonus | Other`
- Add conditional `<input type="text" placeholder="Specify source...">` rendered
  only when `source === "Other"` (stored in a separate `customSource` state)
- Value submitted to API: `source === "Other" ? customSource : source`
- `step="1000"` → `step="1"` on amount (already done in Step 1)
- Backward compat: if saved source doesn't match any preset, pre-select "Other"
  and populate `customSource` with the saved value

---

## Files Modified Summary

| File | Issues |
|---|---|
| `backend/main.py` | 6 |
| `frontend/react/src/context/MonthContext.tsx` | 1 |
| `frontend/react/src/context/AuthContext.tsx` | 5 |
| `frontend/react/src/context/ToastContext.tsx` | 5 |
| `frontend/react/src/hooks/useInactivityTimer.ts` *(new)* | 5 |
| `frontend/react/src/components/settings/BillsSection.tsx` | 2, 3, 8 |
| `frontend/react/src/components/settings/CapsSection.tsx` | 8 |
| `frontend/react/src/components/settings/IncomeSection.tsx` | 4, 8 |
| `frontend/react/src/components/onboarding/OnboardingWizard.tsx` | 8 |
| `frontend/react/src/components/tabs/FixedTab.tsx` | 6 |
| `frontend/react/src/components/tabs/FixedExpenseRow.tsx` | 3 |
| `frontend/react/src/components/shared/BudgetHealthCard.tsx` | 7 |

---

## Verification

After implementation:

1. **Step 1**: Enter ₹585 bill, ₹4,521 income, ₹3,750 cap → no browser validation popup on any.
2. **Step 2**: Log in, leave idle 5 min → warning toast at 4 min, auto-logout at 5 min. Any click/keypress resets the timer.
3. **Step 3**: Edit "Rent" template amount in Settings → Fixed tab shows updated amount without page reload.
4. **Step 4**: Open Settings → Monthly Bills on 375px viewport → all edit controls visible and tappable.
5. **Step 5**: Category at 65% → warning message. 85% → danger. 110% → "Limit exceeded — ₹X over".
6. **Step 6**: After midnight, switch tab and back → month selector updates to new month.
7. **Step 7**: Income section shows source dropdown. "Other" reveals free-text. Existing "Salary" users unaffected.

Run integration tests after Step 3 backend change:
```bash
uv run python tests/test_isolation.py
```
