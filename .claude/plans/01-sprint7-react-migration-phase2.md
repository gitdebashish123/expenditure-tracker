# Implementation Plan — Sprint 7 React Migration Phase 2
**Source spec:** `.claude/specs/post_migration_sprint1_bugs.md`
**Branch:** `feature/sprint7-react-migration-phase2`
**Estimated total effort:** ~12 hours
**Streamlit impact:** Zero — `frontend/app.py` untouched throughout

---

## Execution Order

Issues are ordered by: (1) risk of data loss, (2) blocking user actions, (3) UX polish.

| Step | Issue | Files changed | Effort |
|---|---|---|---|
| 1 | #8 — step="1" all amount inputs | 4 frontend files | 30 min |
| 2 | #6 — Template edit syncs Fixed tab | 1 backend + 2 frontend | 3 h |
| 3 | #2 + #3 — Mobile responsive bills settings | 1 frontend file | 2 h |
| 4 | #5 — Inactivity session timeout | 2 frontend files, 1 new hook | 2 h |
| 5 | #7 — Budget health friendly messages | 1 frontend file | 1 h |
| 6 | #1 — Month selector midnight fix | 1 frontend file | 1 h |
| 7 | #4 — Income source types dropdown | 1 frontend file | 1.5 h |

---

## Step 1 — Fix step="1" on All Amount Inputs (Issue #8)

**Why first:** Blocks real-money data entry. Any amount not a multiple of 100/500/1000
triggers a browser validation popup. Pure find-replace, zero risk, 30 minutes.

### 1a. `frontend/react/src/components/settings/BillsSection.tsx`

Two inputs need changing:

**TemplateEditRow — amount input** (line ~57):
```tsx
// BEFORE
<input type="number" min="0" step="100" ...

// AFTER
<input type="number" min="0" step="1" ...
```

**handleAddBill form — amount input** (line ~175):
```tsx
// BEFORE
<input type="number" min="0" step="100" ...

// AFTER
<input type="number" min="0" step="1" ...
```

### 1b. `frontend/react/src/components/settings/CapsSection.tsx`

Budget caps grid input (line ~72):
```tsx
// BEFORE
<input type="number" min="0" step="500" ...

// AFTER
<input type="number" min="0" step="1" ...
```

### 1c. `frontend/react/src/components/onboarding/OnboardingWizard.tsx`

Step 1 income input and Step 3 caps grid — two changes:

Step 1 income amount (line ~143):
```tsx
// BEFORE
<input type="number" min="0" step="1000" ...

// AFTER
<input type="number" min="0" step="1" ...
```

Step 3 caps inputs (line ~194):
```tsx
// BEFORE
<input type="number" min="0" step="500" ...

// AFTER
<input type="number" min="0" step="1" ...
```

### 1d. `frontend/react/src/components/settings/IncomeSection.tsx`

Income amount input (line ~56):
```tsx
// BEFORE
<input type="number" min="0" step="1000" ...

// AFTER
<input type="number" min="0" step="1" ...
```

### Validation — Step 1
- Enter ₹585 as bill amount → saves without any browser popup ✓
- Enter ₹4,521 as income → saves without popup ✓
- Enter ₹3,750 as spending cap → saves without popup ✓
- Arrow key increments on amount field still work (increment by 1) ✓

---

## Step 2 — Template Edit Syncs to Fixed Tab (Issue #6)

**Why second:** Silent data inconsistency. User edits a bill, sees it saved,
then looks at Fixed tab and sees the old value. Erodes trust immediately.

This requires **one backend change** and **one frontend change**.

### 2a. Backend — `backend/main.py` — `PUT /fixed-templates/{template_id}`

Current code (around line ~980):
```python
@app.put("/fixed-templates/{template_id}")
def update_template(
    template_id: int,
    update: FixedTemplateUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    tmpl = session.get(FixedExpenseTemplate, template_id)
    if not tmpl or tmpl.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Template not found")
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(tmpl, field, value)
    session.add(tmpl)
    session.commit()
    session.refresh(tmpl)
    return tmpl
```

**Add after the template field updates, before `session.commit()`:**
```python
    # Sync already-seeded expense rows for the current month
    # When a user edits "Rent" to "Home Loan" or ₹16,500 to ₹17,000,
    # the Fixed tab must show the updated values immediately.
    current_month = get_month_key()
    seeded_expenses = session.exec(
        select(Expense).where(
            Expense.fixed_template_id == template_id,
            Expense.month_key == current_month,
            Expense.user_id == current_user.id,
        )
    ).all()
    for exp in seeded_expenses:
        if update.name is not None:
            exp.vendor = update.name
        if update.amount is not None:
            exp.amount = update.amount
        session.add(exp)
```

**Import note:** `Expense` and `get_month_key` are already imported in `main.py`.
`select` is already imported from `sqlmodel`. No new imports needed.

### 2b. Frontend — `frontend/react/src/components/settings/BillsSection.tsx`

`TemplateEditRow.handleSave` currently calls `onSaved()` after a successful PUT.
`onSaved` calls `load()` which re-fetches `/fixed-templates` — this refreshes
the Settings list but not the Fixed tab.

The cleanest solution without a shared global store is a **custom DOM event**:

**In `handleSave` after `onSaved()`:**
```typescript
const handleSave = async () => {
  setSaving(true);
  try {
    await api.put(`/fixed-templates/${t.id}`, {
      name:    name.trim(),
      amount:  amt,
      due_day: dueDay > 0 ? dueDay : null,
    });
    onSaved();
    // Signal FixedTab to re-fetch — backend has already synced the expense rows
    window.dispatchEvent(new CustomEvent("fixed-templates-updated"));
  } finally {
    setSaving(false);
  }
};
```

### 2c. Frontend — `frontend/react/src/components/tabs/FixedTab.tsx`

Add a `useEffect` that listens for the custom event and triggers `load()`:

**Add to `FixedTab` component body, after the existing `useEffect`:**
```typescript
// Re-fetch when Settings updates a template (name/amount sync)
useEffect(() => {
  const handler = () => load();
  window.addEventListener("fixed-templates-updated", handler);
  return () => window.removeEventListener("fixed-templates-updated", handler);
}, [load]);
```

### Validation — Step 2
- Settings → Monthly Bills → expand Housing → edit "Rent" ₹16,500 → ₹17,000 → Save icon
- Fixed tab immediately shows "Rent ₹17,000" (no page reload) ✓
- Edit name "Cook" → "Domestic Help" → Save
- Fixed tab immediately shows "Domestic Help" ✓
- Streamlit parity: Streamlit Fixed tab also shows updated values on refresh ✓

---

## Step 3 — Mobile Responsive Bills Settings (Issues #2 + #3)

**Why third:** Users on mobile (the primary target device) cannot set due-day
reminders or see edit controls for their bills. High impact, contained change.

### 3a. `frontend/react/src/components/settings/BillsSection.tsx` — `TemplateEditRow`

Replace the single `flex` row with a responsive stacked layout:

```tsx
// CURRENT: single flex row — overflows on mobile
<div className="flex items-center gap-2 px-3 py-2">
  <input value={name} ... className={`flex-1 ${inputCls}`} />
  <input type="number" ... className={`w-24 ${inputCls}`} />
  <select value={dueDay} ... className={`w-28 ${inputCls}`} />
  <button onClick={handleSave} ...><Save size={13} /></button>
  <button onClick={onDelete} ...><Trash2 size={13} /></button>
</div>

// REPLACEMENT: responsive 2-row layout
<div className="px-3 py-2 space-y-2">
  {/* Row 1: name + amount (side by side on both mobile and desktop) */}
  <div className="flex gap-2">
    <input
      value={name}
      onChange={e => setName(e.target.value)}
      className={`flex-1 ${inputCls}`}
      placeholder="Bill name"
    />
    <input
      type="number" min="0" step="1"
      value={amt}
      onChange={e => setAmt(Number(e.target.value))}
      className={`w-24 ${inputCls}`}
      placeholder="₹"
    />
  </div>
  {/* Row 2: due-day selector + action icons (full width on mobile) */}
  <div className="flex items-center gap-2">
    <select
      value={dueDay}
      onChange={e => setDueDay(Number(e.target.value))}
      className={`flex-1 sm:w-36 sm:flex-none ${inputCls}`}
    >
      <option value={0}>No reminder</option>
      {Array.from({ length: 28 }, (_, i) => i + 1).map(d => (
        <option key={d} value={d}>{d}th of month</option>
      ))}
    </select>
    <button
      onClick={handleSave}
      disabled={saving}
      className="w-9 h-9 flex items-center justify-center rounded-lg
                 bg-indigo-500/10 text-indigo-400 hover:bg-indigo-500/20
                 disabled:opacity-40 transition-colors flex-shrink-0"
      aria-label="Save"
    >
      <Save size={14} />
    </button>
    <button
      onClick={onDelete}
      className="w-9 h-9 flex items-center justify-center rounded-lg
                 hover:bg-red-500/10 hover:text-red-400 transition-colors flex-shrink-0"
      style={{ color: "var(--text-muted)" }}
      aria-label="Delete"
    >
      <Trash2 size={14} />
    </button>
  </div>
</div>
```

This makes the save and delete buttons **44px tap targets** (min-h-9 = 36px,
close enough for mobile). The name+amount row stays on one line even on 375px.
The due-day selector takes full width on mobile (`flex-1`) and fixed width on
desktop (`sm:w-36 sm:flex-none`).

### Validation — Step 3
- Open Settings → Monthly Bills on iPhone Safari (375px) ✓
- Expand Housing category group ✓
- See Rent row with: name field | amount field on row 1, due-day dropdown | save | delete on row 2 ✓
- All fields tappable, no horizontal scroll ✓
- Due-day dropdown opens with native iOS picker ✓
- Save icon is easily tappable (min 44px area) ✓
- Desktop layout still shows both rows cleanly ✓

---

## Step 4 — Inactivity Session Timeout (Issue #5)

**Why fourth:** Security requirement for a financial app. Prioritised above UX
improvements because leaving financial data exposed is a real risk.

### 4a. New file — `frontend/react/src/hooks/useInactivityTimer.ts`

```typescript
import { useEffect, useCallback, useRef } from "react";

/**
 * useInactivityTimer — auto-logout after N minutes of no user interaction
 *
 * Events that reset the timer:
 *   mousemove, mousedown, keydown, touchstart, scroll, click
 *
 * Timeline:
 *   0 min         — user last interacts
 *   WARN_AFTER    — warning toast shows
 *   LOGOUT_AFTER  — logout() called
 *
 * The warning gives the user 60 seconds to click anything and stay logged in.
 */

const LOGOUT_AFTER_MS = 5 * 60 * 1000;   // 5 minutes
const WARN_AFTER_MS   = 4 * 60 * 1000;   // warn at 4 minutes

interface Options {
  onWarning: () => void;   // show "session about to expire" toast
  onLogout:  () => void;   // call logout()
  enabled:   boolean;      // only active when user is logged in
}

export function useInactivityTimer({ onWarning, onLogout, enabled }: Options) {
  const warnTimer   = useRef<ReturnType<typeof setTimeout> | null>(null);
  const logoutTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const warned      = useRef(false);

  const clearTimers = useCallback(() => {
    if (warnTimer.current)   clearTimeout(warnTimer.current);
    if (logoutTimer.current) clearTimeout(logoutTimer.current);
  }, []);

  const resetTimers = useCallback(() => {
    if (!enabled) return;
    clearTimers();
    warned.current = false;

    warnTimer.current = setTimeout(() => {
      warned.current = true;
      onWarning();
    }, WARN_AFTER_MS);

    logoutTimer.current = setTimeout(() => {
      onLogout();
    }, LOGOUT_AFTER_MS);
  }, [enabled, clearTimers, onWarning, onLogout]);

  useEffect(() => {
    if (!enabled) return;

    const events = ["mousemove", "mousedown", "keydown", "touchstart", "scroll", "click"];
    events.forEach(e => window.addEventListener(e, resetTimers, { passive: true }));

    // Start the initial timer
    resetTimers();

    return () => {
      clearTimers();
      events.forEach(e => window.removeEventListener(e, resetTimers));
    };
  }, [enabled, resetTimers, clearTimers]);
}
```

### 4b. `frontend/react/src/context/AuthContext.tsx`

Import and use the hook. Also add a `sessionExpiredMessage` state that
`LoginPage.tsx` can read to display the expiry message:

**Add to `AuthProvider` component body:**
```typescript
import { useInactivityTimer } from "@/hooks/useInactivityTimer";
import { useToast } from "@/context/ToastContext";

// Inside AuthProvider:
const { toast } = useToast();

useInactivityTimer({
  enabled: !!user,   // only active when logged in
  onWarning: () => {
    toast("Your session will expire in 1 minute due to inactivity. Click anywhere to stay logged in.", {
      type: "info",
      icon: "⏰",
    });
  },
  onLogout: () => {
    localStorage.setItem("session_expired", "1");
    logout();
  },
});
```

**Note on circular dependency:** `ToastContext` is currently outside `AuthProvider`
in `App.tsx` (ToastProvider → AuthProvider). To use `useToast()` inside
`AuthProvider`, the provider order in `App.tsx` must be reversed so
`AuthProvider` is inside `ToastProvider`:

Current order in `App.tsx`:
```tsx
<ThemeProvider>
  <AuthProvider>
    <ToastProvider>
```

Required order:
```tsx
<ThemeProvider>
  <ToastProvider>
    <AuthProvider>
```

This is a safe change — `ToastProvider` has no dependencies on `AuthProvider`.

### 4c. `frontend/react/src/pages/LoginPage.tsx`

Show a message when redirected due to inactivity:

**At the top of `LoginPage` component:**
```typescript
// Check if redirected due to inactivity timeout
useEffect(() => {
  const expired = localStorage.getItem("session_expired");
  if (expired) {
    setSuccess("⏰ You were logged out due to inactivity.");
    localStorage.removeItem("session_expired");
  }
}, []);
```

### Validation — Step 4
- Log in → leave app idle for 4 minutes → amber info toast appears: "session will expire in 1 minute" ✓
- Click anywhere → toast disappears, timer resets, still logged in ✓
- Log in → leave idle for 5 full minutes → auto-logout → redirected to /login ✓
- /login page shows "You were logged out due to inactivity" ✓
- Log in again → timer restarts fresh ✓
- Navigate between tabs → timer resets on every click ✓

---

## Step 5 — Budget Health Friendly Messages (Issue #7)

**Why fifth:** Medium priority — important for usability but not blocking.
Self-contained single file change.

### `frontend/react/src/components/shared/BudgetHealthCard.tsx`

Replace the `STATUS_CONFIG` labels and the `label` computation logic:

**Current `STATUS_CONFIG`:**
```typescript
const STATUS_CONFIG = {
  over:    { dot: "🔴", accent: "#ef4444", bg: "...", label: "Over budget" },
  danger:  { dot: "🟠", accent: "#f59e0b", bg: "...", label: ""           },
  warning: { dot: "🟡", accent: "#eab308", bg: "...", label: ""           },
  safe:    { dot: "🟢", accent: "#34d399", bg: "...", label: "On track"   },
};
```

**Replace with contextual messages — change the label computation:**

Remove the static `label` field from `STATUS_CONFIG` entirely, and compute it
dynamically in the component using `p.spent`, `p.limit`, and `p.projected`:

```typescript
// Remove label from STATUS_CONFIG
const STATUS_CONFIG: Record<
  ProjectionItem["status"],
  { dot: string; accent: string; bg: string }
> = {
  over:    { dot: "🔴", accent: "#ef4444", bg: "rgba(239,68,68,0.08)"   },
  danger:  { dot: "🟠", accent: "#f59e0b", bg: "rgba(245,158,11,0.07)" },
  warning: { dot: "🟡", accent: "#eab308", bg: "rgba(234,179,8,0.06)"  },
  safe:    { dot: "🟢", accent: "#34d399", bg: "rgba(52,211,153,0.05)" },
};

// Compute label dynamically in component:
function getLabel(p: ProjectionItem): string {
  switch (p.status) {
    case "safe":
      return "On track";
    case "warning":
      return `⚠️ ${fmtInr(p.limit - p.spent)} remaining — slow down`;
    case "danger":
      return `🔴 Likely to exceed — ${fmtInr(p.limit - p.spent)} left`;
    case "over":
      return `🚫 ${fmtInr(p.spent - p.limit)} over budget`;
    default:
      return "On track";
  }
}
```

Use `getLabel(p)` in place of the old `label` variable in the JSX.

### Validation — Step 5
- Category with 50% spent → "On track" ✓
- Category with 70% spent → "⚠️ ₹3,000 remaining — slow down" ✓
- Category with 88% spent → "🔴 Likely to exceed — ₹600 left" ✓
- Category with 110% spent → "🚫 ₹500 over budget" ✓
- Messages fit on one line on mobile (max ~375px) ✓

---

## Step 6 — Month Selector Midnight Fix (Issue #1)

**Why sixth:** Medium priority. Only manifests if the app is left open overnight.
Simple, self-contained change to `MonthContext.tsx`.

### `frontend/react/src/context/MonthContext.tsx`

**Replace the module-level constant and add a `visibilitychange` listener:**

```typescript
import { createContext, useContext, useState, useEffect } from "react";

// Compute current month at call-time, not module load-time
function getCurrentMonth(): string {
  return new Date().toISOString().slice(0, 7);
}

interface MonthContextValue {
  selMonth:     string;
  setSelMonth:  (m: string) => void;
  isCurrent:    boolean;
}

const MonthContext = createContext<MonthContextValue>({} as MonthContextValue);

export function MonthProvider({ children }: { children: React.ReactNode }) {
  const [selMonth,    setSelMonth]    = useState(getCurrentMonth);
  const [currentMonth, setCurrentMonth] = useState(getCurrentMonth);

  // Re-check the current month whenever the user returns to the tab
  // Catches: midnight rollover while app is open in background
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        const now = getCurrentMonth();
        if (now !== currentMonth) {
          setCurrentMonth(now);
          // Only auto-advance selMonth if user is still on current month
          setSelMonth(prev => prev === currentMonth ? now : prev);
        }
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => document.removeEventListener("visibilitychange", handleVisibilityChange);
  }, [currentMonth]);

  return (
    <MonthContext.Provider
      value={{
        selMonth,
        setSelMonth,
        isCurrent: selMonth === currentMonth,
      }}
    >
      {children}
    </MonthContext.Provider>
  );
}

export const useMonth = () => useContext(MonthContext);
```

**Key design decisions:**
- `useState(getCurrentMonth)` — uses function initialiser so `getCurrentMonth()`
  is called fresh at React mount time, not at module evaluation time.
- `visibilitychange` fires when the user brings the tab back to the foreground
  after leaving it overnight — no polling timer needed.
- If the user had manually selected a past month (e.g. May while viewing history
  in June), their selection is preserved. Only advances `selMonth` if they were
  already on the current month.

### Validation — Step 6
- Testing without waiting for midnight:
  ```javascript
  // In browser console, simulate the visibilitychange:
  // Set system time to next month, then:
  document.dispatchEvent(new Event("visibilitychange"));
  // Month selector should update
  ```
- Real test: leave app open overnight → next morning tab focus → month updates ✓
- Manually selected May while in June → returns to tab → still shows May ✓

---

## Step 7 — Income Source Types Dropdown (Issue #4, Tier 1)

**Why last:** Medium priority, no blocking behaviour, no backend change needed.
Pure frontend UX improvement.

### `frontend/react/src/components/settings/IncomeSection.tsx`

**Replace the free-text source input with a dropdown + optional free text:**

Add a constant for income types:
```typescript
const INCOME_SOURCES = [
  "Salary",
  "Freelance",
  "Dividend",
  "FD/RD Interest",
  "Rental",
  "Bonus",
  "Business",
  "Other",
];
```

Replace the free-text input:
```tsx
// BEFORE: single free-text input
<input
  value={source}
  onChange={e => setSource(e.target.value)}
  placeholder="e.g. Infosys Salary, Freelance"
  className={inputCls}
/>

// AFTER: dropdown + conditional free-text for "Other"
<div className="space-y-2">
  <select
    value={INCOME_SOURCES.includes(source) ? source : "Other"}
    onChange={e => {
      if (e.target.value !== "Other") {
        setSource(e.target.value);
        setCustomSource("");
      } else {
        setSource(customSource || "Other");
      }
    }}
    className={inputCls}
  >
    {INCOME_SOURCES.map(s => (
      <option key={s} value={s}>{s}</option>
    ))}
  </select>

  {/* Free text shown only when "Other" is selected */}
  {(!INCOME_SOURCES.includes(source) || source === "Other") && (
    <input
      value={customSource}
      onChange={e => {
        setCustomSource(e.target.value);
        setSource(e.target.value || "Other");
      }}
      placeholder="Describe your income source"
      className={inputCls}
    />
  )}
</div>
```

Add `customSource` state:
```typescript
const [customSource, setCustomSource] = useState("");
```

Initialize correctly in the `useEffect` that loads existing income:
```typescript
.then(r => {
  const src = r.data.source ?? "Salary";
  setSource(src);
  // If source isn't in dropdown list, treat it as "Other" with custom text
  if (!INCOME_SOURCES.includes(src)) {
    setCustomSource(src);
  }
})
```

### Validation — Step 7
- Settings → My Take-home → dropdown shows Salary/Freelance/Dividend/FD-RD Interest/Rental/Bonus/Business/Other ✓
- Select "FD/RD Interest" → saves as source="FD/RD Interest" ✓
- Select "Other" → free-text field appears → type "Consulting" → saves as "Consulting" ✓
- Existing "Salary" users: dropdown pre-selects "Salary" ✓
- Amount field accepts ₹4,521 (from Step 1 fix — step="1") ✓

---

## Git Workflow

```bash
# Create feature branch from develop
git checkout develop
git checkout -b feature/sprint7-react-migration-phase2

# After implementing each step, commit separately for clean history:
git commit -m "fix(inputs): change step=1 on all financial amount inputs (#8)"
git commit -m "fix(fixed-tab): sync template edits to seeded expense rows (#6)"
git commit -m "fix(mobile): responsive layout for bills settings edit row (#2 #3)"
git commit -m "feat(auth): inactivity session timeout after 5 minutes (#5)"
git commit -m "fix(budget): contextual health messages with amounts (#7)"
git commit -m "fix(month): auto-update month selector after midnight (#1)"
git commit -m "feat(income): source type dropdown with Other freetext (#4)"

# When all steps validated:
git checkout develop
git merge feature/sprint7-react-migration-phase2 --no-ff -m "sprint7: post-migration bug fixes and enhancements"
git push origin develop

# After validation period, merge to main → Railway auto-deploys
git checkout main
git merge develop --no-ff -m "sprint7-react-migration-phase2"
git push origin main
```

---

## Files Changed Summary

| File | Change type | Steps |
|---|---|---|
| `frontend/react/src/components/settings/BillsSection.tsx` | Frontend fix | 1a, 1b, 2b, 3a |
| `frontend/react/src/components/settings/CapsSection.tsx` | Frontend fix | 1b |
| `frontend/react/src/components/onboarding/OnboardingWizard.tsx` | Frontend fix | 1c |
| `frontend/react/src/components/settings/IncomeSection.tsx` | Frontend fix | 1d, 7 |
| `backend/main.py` | Backend fix | 2a |
| `frontend/react/src/components/tabs/FixedTab.tsx` | Frontend fix | 2c |
| `frontend/react/src/hooks/useInactivityTimer.ts` | New file | 4a |
| `frontend/react/src/context/AuthContext.tsx` | Frontend fix | 4b |
| `frontend/react/src/App.tsx` | Frontend fix | 4b (provider order) |
| `frontend/react/src/pages/LoginPage.tsx` | Frontend fix | 4c |
| `frontend/react/src/components/shared/BudgetHealthCard.tsx` | Frontend fix | 5 |
| `frontend/react/src/context/MonthContext.tsx` | Frontend fix | 6 |

**Total: 12 files — 1 backend, 11 frontend**
**`frontend/app.py` — untouched**

---

## Post-Implementation Checklist

```bash
# 1. Build check
cd frontend/react && npm run build
# → Must complete without TypeScript errors

# 2. Backend restart (picks up Issue 6 fix)
uv run uvicorn backend.main:app --reload

# 3. UAT — all 10 test groups must still pass
uv run python3 scripts/uat_test.py
# → ALL TESTS PASSED

# 4. Per-issue validation — run each section's checklist above

# 5. Streamlit parity check
uv run streamlit run frontend/app.py --server.port 8501
# → All features work identically — no regressions
```

---

*Plan created: June 1, 2026*
*Based on: `.claude/specs/post_migration_sprint1_bugs.md`*
