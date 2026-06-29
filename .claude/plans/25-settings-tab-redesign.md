# Implementation Plan: Settings Tab Redesign ✅ COMPLETED 2026-06-29
**Spec**: `.claude/specs/25_settings-tab-redesign.md`
**Date**: 2026-06-29
**Branch**: `feature/sprint06261-ui-enhancement`
**Prereq**: Plan 24 ✅ completed — `CurrencyInput` exists, "commitments" naming applied.

---

## Overview

8 items — all **frontend-only**. No backend changes needed (backend-gated parts of Item 3
are explicitly deferred). Ordered smallest-blast-radius first.

**Verify during implementation (from spec):**
1. Caps-history route — confirmed absent (grep shows no route); omit the "View all caps & history" link.
2. Income `updated_at` / `is_recurring` backend fields — not present on `IncomeRow`; badge + last-updated deferred.
3. Pool avg/mo — pools have `amount: 0` by convention; omit avg.

---

## Item 1 — ProfileDropdown: add scrim + confirm opaque panel (Spec Item 7)
**Scope**: Frontend-only
**File**: `frontend/react/src/components/layout/ProfileDropdown.tsx`

**Root cause**: The dropdown panel (`line 47`) is `absolute` with no overlay behind it. Page content is visually accessible under and around it — no scrim prevents background interaction or provides visual separation. `bg-dark-card` maps to `var(--card)` = `#111118` (dark) / `#ffffff` (light), both opaque, but the lack of a scrim layer causes the "bleed through" appearance noted in the review screenshots.

**What to do**: When `open === true`, render a `fixed inset-0` backdrop div at `z-[49]` (one below the panel's `z-50`) with `bg-black/20` that calls `setOpen(false)` on click. This blocks background interaction and provides visual separation. The panel's `z-50` already puts it on top.

```tsx
{/* Scrim — render BEFORE the panel so z-order is correct */}
{open && (
  <div
    className="fixed inset-0 z-[49]"
    style={{ background: "rgba(0,0,0,0.20)" }}
    onClick={() => setOpen(false)}
  />
)}

{/* Dropdown panel — unchanged except z-index confirmed at z-50 */}
{open && (
  <div className="absolute right-0 top-11 w-56 bg-dark-card border border-white/10
                  rounded-2xl shadow-2xl p-2 z-50">
    {/* ...existing content unchanged... */}
  </div>
)}
```

Keep the `mousedown` outside-click handler — it still serves keyboard/programmatic closes. The scrim handles tap-outside on mobile (where `mousedown` may be less reliable).

---

## Item 2 — Export polish (Spec Item 5)
**Scope**: Frontend-only
**File**: `frontend/react/src/components/settings/ExportSection.tsx`

Four independent sub-fixes:

### 2a — Rename heading
Line 70: change `📥 My Data` → `📥 Export data`.

### 2b — Contrast on preset buttons
Line 63–65: `btnCls` applies `style={{ color: "var(--text-sub)" }}` inline on both buttons (lines 89, 109). `--text-sub` = `rgba(255,255,255,0.55)` — reads as disabled. Remove the inline `style` override from both buttons and use `text-white` in `btnCls` instead:

```tsx
// Before
const btnCls =
  "flex-1 flex items-center justify-center gap-2 bg-dark-card2 border border-white/10 " +
  "hover:bg-white/5 py-3 rounded-xl text-sm disabled:opacity-50 transition-colors";
// (buttons also have style={{ color: "var(--text-sub)" }})

// After — add text-white to class, remove inline style from both buttons
const btnCls =
  "flex-1 flex items-center justify-center gap-2 bg-dark-card2 border border-white/10 " +
  "hover:bg-white/5 py-3 rounded-xl text-sm text-white disabled:opacity-50 transition-colors";
```

Remove `style={{ color: "var(--text-sub)" }}` from both `<button>` elements.

### 2c — Custom-range default trap
Lines 25–26: both `fromDate` and `toDate` default to today. Change `fromDate` to default to the selected month's start:

```tsx
// Replace the useState initializers
const [fromDate, setFromDate] = useState(() => `${selMonth}-01`);
const [toDate,   setToDate]   = useState(() => new Date().toISOString().slice(0, 10));
```

Add a `useEffect` so navigating to a different month also resets `fromDate`:
```tsx
useEffect(() => {
  setFromDate(`${selMonth}-01`);
}, [selMonth]);
```
(`selMonth` is already in scope from `useMonth()` on line 21.)

### 2d — Date-format split in button label
Line 171: `Download {fromDate} → {toDate}` shows ISO strings while the date inputs render locale format (DD/MM/YYYY on Safari/iOS). Add a local formatter and apply it to the label only:

```tsx
const fmtD = (iso: string) =>
  new Date(iso + "T00:00:00").toLocaleDateString("en-IN", {
    day: "numeric", month: "short", year: "numeric",
  });

// In JSX:
Download {fmtD(fromDate)} → {fmtD(toDate)}
```

---

## Item 3 — Income: sources count on total row (Spec Item 3 — derivable part only)
**Scope**: Frontend-only
**File**: `frontend/react/src/components/settings/IncomeSection.tsx`

**Root cause**: The "Total Income" row (lines 151–161) shows only the ₹ sum. The spec adds a sources count alongside it (`{n} sources`), which is directly derivable from `entries.length`.

**What to do**: In the "Total Income" `<span>` on the left side (line 153–156), add the count:

```tsx
// Before
<span className="text-xs font-semibold uppercase tracking-widest"
      style={{ color: "var(--text-sub)" }}>
  Total Income
</span>

// After
<span className="text-xs font-semibold uppercase tracking-widest"
      style={{ color: "var(--text-sub)" }}>
  Total Income
  <span className="normal-case tracking-normal font-normal ml-1.5"
        style={{ color: "var(--text-muted)" }}>
    · {entries.length} source{entries.length !== 1 ? "s" : ""}
  </span>
</span>
```

**Deferred (backend-gated)**: `updated_at` timestamp and `is_recurring` badge. `IncomeRow` at line 8–13 has no such fields; adding them requires a backend model change and migration. Split to a follow-up spec once backend support lands.

---

## Item 4 — Commitment group: ₹/month totals (Spec Item 4)
**Scope**: Frontend-only
**File**: `frontend/react/src/components/settings/BillsSection.tsx`

Three sub-changes, all client-side arithmetic:

### 4a — Per-group total in collapse header
In `FixedTemplateCategoryGroup` (line 111), the `items` prop contains `FixedExpenseTemplate[]`. Add the group sum to the header button:

```tsx
// After "({items.length} item…)" on line 134, add:
const groupTotal = items.reduce((s, t) => s + t.amount, 0);

// In the button label, after the item-count span:
<span className="ml-2 text-xs" style={{ color: "var(--text-sub)" }}>
  {fmtInr(groupTotal)}/mo
</span>
```

Import `fmtInr` at the top of `BillsSection.tsx` (not yet imported).

### 4b — "Fixed total" anchor above fixed groups
In `BillsSection`, compute the total of all active fixed templates (line 180). Above the fixed-group list (`line 234 div.mb-4`), insert a total summary row:

```tsx
const fixedTotal = activeFixed.reduce((s, t) => s + t.amount, 0);

// Above the fixed-groups section (before <div className="mb-4">):
{activeFixed.length > 0 && (
  <div className="flex justify-between items-center px-4 py-2 mb-3
                  bg-indigo-500/5 border border-indigo-500/15 rounded-xl">
    <span className="text-xs font-semibold uppercase tracking-widest"
          style={{ color: "var(--text-sub)" }}>
      Fixed total
    </span>
    <span className="font-syne font-bold text-indigo-300 text-sm">
      {fmtInr(fixedTotal)}/mo
    </span>
  </div>
)}
```

### 4c — Variable group (pools): omit avg
Pools have `amount: 0` by convention and no expense history in the template data. No avg/mo figure to show. No change to the pool list rendering.

---

## Item 5 — Destructive deletes: confirm step + tap targets (Spec Item 8)
**Scope**: Frontend-only
**Files**:
- `frontend/react/src/components/settings/IncomeSection.tsx`
- `frontend/react/src/components/settings/BillsSection.tsx`

**Do after Items 3 and 4** to avoid editing the same files twice.

### 5a — Income delete confirm (`IncomeSection.tsx`)
Current `handleDelete` (line 91) fires immediately on the Trash2 button click (line 138). Add per-entry confirm state using a local `confirmId` state:

```tsx
const [confirmId, setConfirmId] = useState<number | null>(null);
```

Replace the Trash2 button (lines 137–145) with a two-step pattern:
- If `confirmId !== entry.id`: show Trash2 button that sets `setConfirmId(entry.id)`.
- If `confirmId === entry.id`: show "Remove?" text + "Yes" button (calls `handleDelete`) + "No" button (clears `confirmId`). Style as small inline text, no modal.

```tsx
{confirmId === entry.id ? (
  <div className="flex items-center gap-1.5 text-xs">
    <span style={{ color: "var(--text-sub)" }}>Remove?</span>
    <button
      onClick={() => { handleDelete(entry.id); setConfirmId(null); }}
      className="text-red-400 hover:text-red-300 font-semibold transition-colors"
    >Yes</button>
    <button
      onClick={() => setConfirmId(null)}
      className="transition-colors"
      style={{ color: "var(--text-muted)" }}
    >No</button>
  </div>
) : (
  <button
    onClick={() => setConfirmId(entry.id)}
    className="w-10 h-10 flex items-center justify-center rounded-lg
               hover:text-red-400 hover:bg-red-500/10 transition-colors"
    style={{ color: "var(--text-muted)" }}
    aria-label={`Remove ${entry.source}`}
  >
    <Trash2 size={14} />
  </button>
)}
```

Note: tap target raised to `w-10 h-10` (40px) from current `w-7 h-7` (28px).

### 5b — Pool template delete confirm (`BillsSection.tsx`)
The pool delete button (line 279) is one-tap. Apply the same `confirmId` pattern inside `BillsSection`:

```tsx
const [confirmPoolId, setConfirmPoolId] = useState<number | null>(null);
```

Replace the pool `<button onClick={() => handleDelete(t.id)} ...>` with the two-step pattern (same structure as 5a, `confirmPoolId` keyed to `t.id`). Tap target: wrap icon in `w-10 h-10` container.

### 5c — Tap targets in `TemplateEditRow`
`TemplateEditRow` save (line 90) and delete (line 97) buttons use `size={13}` icons with no padding container — approximately 13px touch target. Wrap each in a `className="w-10 h-10 flex items-center justify-center rounded-lg"` container and keep existing colour classes. No functional change — purely padding.

Fixed-template inline delete in `TemplateEditRow` (`onDelete` prop): since this already triggers a parent-level `handleDelete` which fires `api.delete` immediately, add the confirm step in the row itself or via `confirmId` in the parent. Simplest: add local `[confirmDel, setConfirmDel]` boolean state inside `TemplateEditRow` — same two-step pattern applied to that button.

---

## Item 6 — Caps → progress-bar cards with auto-save (Spec Item 1)
**Scope**: Frontend-only
**File**: `frontend/react/src/components/settings/CapsSection.tsx`

**Root cause**: Current cell (line 94–112) is `label + spent text + CurrencyInput`. No progress bar. Save is explicit form submit (line 55–69). Add-cap form is inline below (lines 127–172).

**What to do** (significant rework of `CapsSection`):

### Remove the `<form>` + explicit save
Delete the `handleSave` function (lines 55–69) and the `<form onSubmit={handleSave}>` wrapper. Remove the "Save Spending Caps" `<button>` (lines 115–124). Remove `saving` and `saved` state.

### Add debounced auto-save
```tsx
import { useRef } from "react";

const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
const [savedCat, setSavedCat] = useState<string | null>(null); // which cat just saved

const handleCapChange = (category: string, value: number) => {
  setUpdates(prev => ({ ...prev, [category]: value }));
  if (debounceRef.current) clearTimeout(debounceRef.current);
  debounceRef.current = setTimeout(async () => {
    await api.put("/budget", { category, limit_amount: value });
    setSavedCat(category);
    setTimeout(() => setSavedCat(null), 2000);
  }, 600);
};
```

### Redesign each cap cell → card
Replace the per-budget cell (`div key={b.category}`, lines 94–112) with a card that has:
- Row 1: icon + category name (left) · `{pct.toFixed(0)}%` in threshold colour + state cue (right)
- Row 2: `₹{spent} / ₹{cap}` in small text (left) · "✓" if `savedCat === b.category` (right)
- Row 3: progress bar (`div` full-width, inner `div` at `width: min(pct, 100)%`, background = threshold colour, height 4px, rounded)
- Row 4: `CurrencyInput` (compact, no label)

State cue: `pct >= 100 ? "Over" : pct >= 80 ? "Near" : "On track"` rendered in a small `<span>` next to the `%`.

```tsx
const stateCue = pct >= 100 ? "Over" : pct >= 80 ? "Near" : "On track";

<div key={b.category}
     className="bg-dark-card2 border border-white/10 rounded-xl p-3 space-y-2">
  {/* Row 1 */}
  <div className="flex items-center justify-between">
    <span className="text-white text-xs font-medium">
      {CATEGORY_ICONS[b.category] ?? "📦"} {b.category}
    </span>
    <span className="text-xs font-semibold" style={{ color: colour }}>
      {pct.toFixed(0)}% · {stateCue}
      {savedCat === b.category && (
        <span className="ml-1 text-emerald-400">✓</span>
      )}
    </span>
  </div>
  {/* Row 2 */}
  <div className="text-xs" style={{ color: "var(--text-muted)" }}>
    {fmtInr(spent)} / {fmtInr(limit)}
  </div>
  {/* Progress bar */}
  <div className="h-1 rounded-full bg-white/10 overflow-hidden">
    <div
      className="h-full rounded-full transition-all"
      style={{ width: `${Math.min(pct, 100)}%`, background: colour }}
    />
  </div>
  {/* Input */}
  <CurrencyInput
    value={updates[b.category] ?? 0}
    onChange={v => handleCapChange(b.category, v)}
    className="w-full bg-dark-bg border border-white/10 rounded-lg
               px-2.5 py-1.5 text-white text-xs
               focus:border-accent focus:outline-none transition-colors"
  />
</div>
```

At ≤360px, the 2-col grid may pinch "₹7,815 / ₹5,000" text. Mitigate with `text-xs` (already planned) and `overflow-hidden` on the spend line. If it still breaks, add a responsive class: `grid-cols-1 xs:grid-cols-2` — but test first; the `text-xs` treatment should be sufficient.

### Move add-cap to "+ Set cap" button in section header
Replace the bottom add-cap section (lines 127–172) with a header that has a right-aligned "+ Set cap" button:

```tsx
<div className="mb-4">
  <div className="flex items-center justify-between">
    <div>
      <h2 className="font-syne font-bold text-white">🎯 Spending Caps</h2>
      <p className="text-sm mt-0.5" style={{ color: "var(--text-sub)" }}>
        Monthly limit per category. You'll get a warning when you're close.
      </p>
    </div>
    {availableCats.length > 0 && (
      <button
        onClick={() => setAddOpen(o => !o)}
        className="flex-shrink-0 text-xs font-semibold px-3 py-1.5 rounded-lg
                   border border-accent/40 text-indigo-300 hover:bg-accent/10
                   transition-colors"
      >
        + Set cap
      </button>
    )}
  </div>
  <div className="border-b border-white/10 mt-3" />
</div>
```

Add `addOpen` state. When `addOpen`, show the `<select>` + `CurrencyInput` + "Add" button inline below the divider (same logic as existing, just relocated and toggled by "+ Set cap"). Keep the "no categories left" guard (`availableCats.length > 0`).

**Omit** "View all caps & history →" link — no caps-history route exists.

---

## Item 7 — Shortcuts → icon tiles (Spec Item 6)
**Scope**: Frontend-only
**File**: `frontend/react/src/components/settings/ShortcutsSection.tsx`

**Root cause**: Current display (lines 146–153) is `ShortcutEditRow` inline-edit rows. Spec calls for horizontally-scrollable icon tiles. `CurrencyInput` already in use.

**What to do**: Replace the display and add logic; keep all API calls unchanged.

### New state
```tsx
const [addOpen,   setAddOpen]   = useState(false);
const [viewAll,   setViewAll]   = useState(false);
```

### Section header with "+ Add shortcut" button
```tsx
<div className="mb-4">
  <div className="flex items-center justify-between">
    <div>
      <h2 className="font-syne font-bold text-white">⚡ Saved Shortcuts</h2>
      <p className="text-sm mt-0.5" style={{ color: "var(--text-sub)" }}>
        Expenses you log frequently. Appear as chips in Today tab.
      </p>
    </div>
    <button
      onClick={() => setAddOpen(o => !o)}
      className="flex-shrink-0 text-xs font-semibold px-3 py-1.5 rounded-lg
                 border border-accent/40 text-indigo-300 hover:bg-accent/10
                 transition-colors"
    >
      + Add shortcut
    </button>
  </div>
  <div className="border-b border-white/10 mt-3" />
</div>
```

### Horizontally-scrollable tiles
Replace the `shortcuts.map(t => <ShortcutEditRow ...>)` block with:
```tsx
{shortcuts.length > 0 && (
  <div className="flex gap-3 overflow-x-auto pb-2 mb-3 scrollbar-none">
    {shortcuts.map(t => (
      <button
        key={t.id}
        onClick={() => setViewAll(true)}
        className="flex-shrink-0 flex flex-col items-center gap-1
                   bg-dark-card2 border border-white/10 rounded-xl px-4 py-3
                   min-w-[80px] hover:bg-white/5 transition-colors"
      >
        <span className="text-xl">{CATEGORY_ICONS[t.category] ?? "📦"}</span>
        <span className="text-xs text-white font-medium truncate max-w-[72px]">{t.name}</span>
        <span className="text-xs" style={{ color: "var(--text-sub)" }}>
          {fmtInr(t.amount)}
        </span>
      </button>
    ))}
    {/* Dashed "+" add tile */}
    <button
      onClick={() => setAddOpen(true)}
      className="flex-shrink-0 flex flex-col items-center justify-center
                 border-2 border-dashed border-white/20 rounded-xl px-4 py-3
                 min-w-[64px] min-h-[80px] text-white/30 hover:border-accent/40
                 hover:text-accent/60 transition-colors"
      aria-label="Add shortcut"
    >
      <span className="text-xl">+</span>
    </button>
  </div>
)}
```

### "View all shortcuts →" link
Below the tiles, when shortcuts exist and `!viewAll`:
```tsx
{shortcuts.length > 0 && !viewAll && (
  <button
    onClick={() => setViewAll(true)}
    className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
  >
    View all shortcuts →
  </button>
)}
```

### Expanded view ("View all")
When `viewAll === true`, render the existing `ShortcutEditRow` list below the tiles (keep `ShortcutEditRow` component unchanged). Add a "Done" / "▲ Hide" toggle to collapse it again.

```tsx
{viewAll && (
  <div className="mt-3 border-t border-white/10 pt-3">
    {shortcuts.map(t => (
      <ShortcutEditRow
        key={t.id}
        template={t}
        onDelete={() => handleDelete(t.id)}
        onSave={updates => handleSave(t, updates)}
      />
    ))}
    <button
      onClick={() => setViewAll(false)}
      className="mt-2 text-xs transition-colors"
      style={{ color: "var(--text-muted)" }}
    >
      ▲ Hide
    </button>
  </div>
)}
```

### Add shortcut form
Move the existing 3-col form (lines 162–195) to render only when `addOpen === true`, wrapped in a collapsed section below the tiles. Add a cancel / dismiss mechanism. No functional change to the form itself — same fields, same `handleAdd`, just conditionally shown.

---

## Item 8 — Over-budget notification bell (Spec Item 2)
**Scope**: Frontend-only (new component + `Header.tsx` wired in)
**Files**:
- `frontend/react/src/components/layout/NotificationBell.tsx` *(create)*
- `frontend/react/src/components/layout/Header.tsx` (add import + render)

**Do last** — this is the only change that touches `Header.tsx` and introduces a new global element.

**Root cause**: No bell exists. Header right-controls (line 40–50) currently has only theme toggle + `ProfileDropdown`.

### Create `NotificationBell.tsx`

```tsx
import { useEffect, useState, useRef } from "react";
import { Bell } from "lucide-react";
import { api } from "@/api/client";
import { useMonth } from "@/context/MonthContext";
import { CATEGORY_ICONS } from "@/utils/categories";
import { fmtInr } from "@/utils/formatInr";
import type { BudgetLimit, Summary } from "@/types";

interface Alert { category: string; spent: number; limit: number; pct: number; }

export function NotificationBell() {
  const { selMonth } = useMonth();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [open,   setOpen]   = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    Promise.all([
      api.get<BudgetLimit[]>("/budgets"),
      api.get<Summary>(`/summary/${selMonth}`),
    ]).then(([budgetsRes, summaryRes]) => {
      const catSpent = Object.fromEntries(
        summaryRes.data.categories.map(c => [c.category, c.spent])
      );
      const over = budgetsRes.data
        .map(b => {
          const spent = catSpent[b.category] ?? 0;
          const pct   = b.limit_amount > 0 ? (spent / b.limit_amount) * 100 : 0;
          return { category: b.category, spent, limit: b.limit_amount, pct };
        })
        .filter(a => a.pct >= 100);
      setAlerts(over);
    }).catch(() => {});
  }, [selMonth]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(o => !o)}
        className="relative w-9 h-9 rounded-xl bg-dark-card2 flex items-center
                   justify-center text-white/60 hover:text-white transition-colors"
        aria-label={alerts.length ? `${alerts.length} over-budget alerts` : "Notifications"}
      >
        <Bell size={16} />
        {alerts.length > 0 && (
          <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-red-500
                           flex items-center justify-center text-[10px] font-bold text-white">
            {alerts.length}
          </span>
        )}
      </button>

      {open && (
        <>
          {/* Scrim */}
          <div className="fixed inset-0 z-[49]" onClick={() => setOpen(false)} />
          {/* Panel */}
          <div className="absolute right-0 top-11 w-64 bg-dark-card border border-white/10
                          rounded-2xl shadow-2xl p-3 z-50 space-y-1">
            {alerts.length === 0 ? (
              <p className="text-xs text-center py-2" style={{ color: "var(--text-muted)" }}>
                No over-budget alerts this month.
              </p>
            ) : (
              <>
                <p className="text-xs font-semibold uppercase tracking-widest mb-2"
                   style={{ color: "var(--text-muted)" }}>
                  Over budget · {selMonth}
                </p>
                {alerts.map(a => (
                  <div key={a.category}
                       className="flex items-center justify-between px-2 py-1.5
                                  bg-red-500/10 border border-red-500/20 rounded-lg">
                    <span className="text-sm text-white">
                      {CATEGORY_ICONS[a.category] ?? "📦"} {a.category}
                    </span>
                    <span className="text-xs text-red-400 font-semibold">
                      {fmtInr(a.spent)} / {fmtInr(a.limit)}
                    </span>
                  </div>
                ))}
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
}
```

### Wire into `Header.tsx`
In the right-controls `<div>` (line 40), insert `<NotificationBell />` between the theme toggle and `<ProfileDropdown />`:

```tsx
import { NotificationBell } from "./NotificationBell";

// In JSX right-controls:
<div className="flex items-center gap-2 flex-shrink-0">
  <button onClick={toggle} ...>...</button>
  <NotificationBell />          {/* ← add */}
  <ProfileDropdown />
</div>
```

**No inline over-budget banner** remains in `CapsSection` — the bell is the sole alert surface.

---

## Execution order summary

| Step | Spec Item | File(s) | Blast radius |
|------|-----------|---------|--------------|
| 1 | Item 7 | `ProfileDropdown.tsx` | Tiny — CSS-only |
| 2 | Item 5 | `ExportSection.tsx` | Small — 4 isolated fixes |
| 3 | Item 3 | `IncomeSection.tsx` | Small — 1 line in total row |
| 4 | Item 4 | `BillsSection.tsx` | Small — 2 display-only additions |
| 5 | Item 8 | `IncomeSection.tsx` + `BillsSection.tsx` | Medium — UX interaction change |
| 6 | Item 1 | `CapsSection.tsx` | Medium-high — major rework |
| 7 | Item 6 | `ShortcutsSection.tsx` | Medium-high — major rework |
| 8 | Item 2 | `NotificationBell.tsx` (new) + `Header.tsx` | Highest — new global element |

Steps 3 and 5 both touch `IncomeSection.tsx` — complete step 3 before step 5.
Steps 4 and 5 both touch `BillsSection.tsx` — complete step 4 before step 5.
