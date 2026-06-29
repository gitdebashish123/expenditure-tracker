# Implementation Plan: Fixed Tab — Paid-State Redesign, Privacy & Category Polish
**Spec**: `.claude/specs/22_fixed-tab-ux-redesign.md`  
**Date**: 2026-06-29  
**Status**: 🟢 All items (1–9) implemented and build-verified (2026-06-29).  
**Branch**: `feature/sprint06261-ui-enhancement`

---

## Overview

9 items total — **0 require backend changes** for Tiers 1–2 (Tier 3 is deferred).  
**1 item is blocked** (Item 9 / spec 1.2) pending user decision on privacy model.  
Items are ordered smallest-blast-radius first; tackle in sequence.

---

## Item 1 — Pool amount input: remove stepper affordance (spec 1.4)
**Scope**: Frontend-only  
**File**: `frontend/react/src/components/tabs/PoolCard.tsx` — lines 168–178

**Root cause** (verified): The amount `<input>` at line 169 is `type="number" step="1"`, which renders a browser spinner / step widget on some platforms and invites tap-by-1 interaction — wrong for rupee entry.

```tsx
// current (line 169):
<input
  type="number"
  min="0"
  step="1"
  value={amount || ""}
  ...
```

**What to do**: Replace `type="number"` with `type="text"`, add `inputMode="decimal"` so mobile keyboards show a numeric pad, and handle parsing in the `onChange` handler. Remove `step` and `min` attributes (validate positivity in `handleAdd`, which already does `amount <= 0` guard).

```tsx
// after:
<input
  type="text"
  inputMode="decimal"
  value={amount || ""}
  onChange={e => setAmount(parseFloat(e.target.value) || 0)}
  placeholder="₹"
  className="w-24 bg-dark-card2 border border-white/10 rounded-lg
             px-3 py-2 text-white text-sm [appearance:textfield]
             [&::-webkit-outer-spin-button]:appearance-none
             [&::-webkit-inner-spin-button]:appearance-none
             focus:border-accent focus:outline-none"
/>
```

**Co-located note**: `FixedExpenseRow.tsx` lines 85–98 has the same `type="number" step="1"` pattern on the inline amount editor. The spec does not call it out, but it is the same defect. Fix it in the same commit: switch to `type="text" inputMode="decimal"` and update `onChange` to `e => setAmt(parseFloat(e.target.value) || 0)`.

---

## Item 2 — Household vs Housing icons (spec 1.3)
**Scope**: Frontend-only  
**File**: `frontend/react/src/utils/categories.ts` — lines 15 and 21

**Root cause** (verified): `Housing: "🏠"` (line 15) and `Household: "🏡"` (line 21) are both house emojis, nearly identical at small sizes.

**What to do**: Change `Household` to a basket/cleaning icon. Confirmed distinct choice: `🧺` (laundry basket) is unambiguous, in-scope for household chores/cook/milk, and not used elsewhere in the map.

```ts
// current (line 21):
Household:     "🏡",

// after:
Household:     "🧺",
```

**Blocked sub-decision**: Renaming "Household" → "Home Services" (or similar) is a separate open decision. The icon swap above does **not** require a rename and can ship independently. If a rename is approved, it also requires a data migration (all existing `Expense.category = "Household"` rows must be updated, and `config.yaml` vendor→category mappings must be updated). Do **not** rename without that migration.

---

## Item 3 — ₹0 pending must not render red (spec 1.1)
**Scope**: Frontend-only  
**File**: `frontend/react/src/components/tabs/FixedTab.tsx` — line 144

**Root cause** (verified): Line 144 is unconditionally `text-red-400`:

```tsx
// current (line 144):
<span className="text-red-400">{fmtInr(unpaidTotal)} pending</span>
```

**What to do**: Make color conditional on `unpaidTotal`. At zero, show emerald "All paid ✓" with no "pending" label. At non-zero, keep red/amber.

```tsx
// after (replaces line 144):
{unpaidTotal === 0 ? (
  <span className="text-emerald-400 font-semibold">All paid ✓</span>
) : (
  <span className="text-red-400">{fmtInr(unpaidTotal)} pending</span>
)}
```

**Guardrail**: This only changes the summary header span. `reminders` rendering (Section 1) is entirely separate — the red banners there are unaffected.

---

## Item 4 — Surface completion % as a number (spec 2.1)
**Scope**: Frontend-only  
**File**: `frontend/react/src/components/tabs/FixedTab.tsx` — line 141–145 (summary header block)

**Root cause** (verified): `pct` is computed at line 100 (`Math.round(paidTotal / grandTotal * 100)`) but is only used for the progress bar width. The header shows raw counts and amounts but no percentage.

**What to do**: Append the percentage to the left side of the summary header.

```tsx
// current (line 141–142):
<span style={{ color: 'var(--text-sub)' }}>
  {paidCount} of {fixedExps.length} paid · {fmtInr(paidTotal)} done
</span>

// after:
<span style={{ color: 'var(--text-sub)' }}>
  {paidCount} of {fixedExps.length} paid · {pct}%
</span>
```

The `{fmtInr(paidTotal)} done` clause moves to the Item 8 celebration card (spec 2.4) so it has a dedicated visible home. If spec 2.4 is not implemented in the same session, keep it here as well.

---

## Item 5 — Unify pool status iconography (spec 2.5)
**Scope**: Frontend-only  
**File**: `frontend/react/src/components/tabs/PoolCard.tsx` — lines 41–46

**Root cause** (verified): `poolStatus` at lines 41–46 uses raw emoji `✅` and `⚠️` in a text string, while the tick buttons inside the same component use a plain `✓` text glyph inside a CSS circle (line 120). The two coexist visually in the same card.

```tsx
// current (lines 41–46):
const poolStatus =
  pool.entry_count === 0
    ? "⚠️ No entries yet"
    : totalUnpaid === 0
    ? `✅ ${fmtInr(totalPaid)} paid`
    : `${fmtInr(totalPaid)} paid · ${fmtInr(totalUnpaid)} unpaid`;
```

**What to do**: Replace the emoji with inline JSX that uses lucide `CheckCircle2` (already available in lucide-react) and `AlertCircle`. Keep the logic identical, but render JSX instead of a string — which means `poolStatus` must become a JSX element (or render it inline).

Move the status from a `const string` to inline JSX in the header render:

```tsx
// In the header <div className="flex items-center gap-2"> block,
// replace <span>{poolStatus}</span> with:
<span className="flex items-center gap-1 text-xs" style={{ color: 'var(--text-sub)' }}>
  {pool.entry_count === 0 ? (
    <><AlertCircle size={12} className="text-amber-400" /> No entries yet</>
  ) : totalUnpaid === 0 ? (
    <><CheckCircle2 size={12} className="text-emerald-400" /> {fmtInr(totalPaid)} paid</>
  ) : (
    <>{fmtInr(totalPaid)} paid · {fmtInr(totalUnpaid)} unpaid</>
  )}
</span>
```

Add `CheckCircle2, AlertCircle` to the lucide-react import on line 6. Remove the `poolStatus` const.

The `⚡` / Utilities overlap (same emoji for category icon and pool icon) is a cosmetic overlap only — no change needed unless the user wants a dedicated pool icon per pool type, which is not in scope.

---

## Item 6 — Per-category paid counts in group header (spec 2.2)
**Scope**: Frontend-only  
**File**: `frontend/react/src/components/tabs/FixedTab.tsx` — lines 164–167 (category group header)

**Root cause** (verified): The group header at line 166–167 shows `{cat} · {subtotal}` only — no paid/total count.

```tsx
// current (lines 164–167):
<p className="text-xs font-syne font-bold uppercase tracking-widest mb-2"
   style={{ color: 'var(--text-muted)' }}>
  {CATEGORY_ICONS[cat] ?? "📦"} {cat} ·{" "}
  {fmtInr(items.reduce((s, e) => s + e.amount, 0))}
</p>
```

**What to do**: Compute paid count per group inline and add it to the header. No new state needed — `items` is already the full group array at render time.

```tsx
// after:
<p className="text-xs font-syne font-bold uppercase tracking-widest mb-2"
   style={{ color: 'var(--text-muted)' }}>
  {CATEGORY_ICONS[cat] ?? "📦"} {cat} ·{" "}
  {items.filter(e => e.paid).length}/{items.length} paid ·{" "}
  {fmtInr(items.reduce((s, e) => s + e.amount, 0))}
</p>
```

**Depends on**: None. Safe to do before or after Item 7.

---

## Item 7 — Collapsible category groups (spec 2.3)
**Scope**: Frontend-only  
**File**: `frontend/react/src/components/tabs/FixedTab.tsx` — the `byCategory` render block, lines 158–182

**Root cause** (verified): No collapse/expand mechanism exists on category groups. `PoolCard.tsx` already has the pattern: `useState(true)` per card + chevron in the header button.

**What to do**: Lift collapse state into `FixedTab` as a `Record<string, boolean>` (keyed by category name). Default to expanded (`true`). The group header becomes a `<button>` wrapping the existing `<p>` content plus a chevron.

```tsx
// Add state after the existing useState declarations (around line 47):
const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});

const toggleCategory = (cat: string) =>
  setCollapsed(prev => ({ ...prev, [cat]: !prev[cat] }));

// Replace the group header <p> and the items list (lines 162–182) with:
{Object.entries(byCategory)
  .sort(([a], [b]) => a.localeCompare(b))
  .map(([cat, items]) => {
    const isCollapsed = collapsed[cat] ?? false;
    const catPaid = items.filter(e => e.paid).length;
    return (
      <div key={cat} className="mb-5">
        <button
          onClick={() => toggleCategory(cat)}
          className="w-full flex items-center justify-between mb-2
                     hover:opacity-80 transition-opacity"
        >
          <p className="text-xs font-syne font-bold uppercase tracking-widest"
             style={{ color: 'var(--text-muted)' }}>
            {CATEGORY_ICONS[cat] ?? "📦"} {cat} ·{" "}
            {catPaid}/{items.length} paid ·{" "}
            {fmtInr(items.reduce((s, e) => s + e.amount, 0))}
          </p>
          {isCollapsed
            ? <ChevronDown size={13} style={{ color: 'var(--text-muted)' }} />
            : <ChevronUp   size={13} style={{ color: 'var(--text-muted)' }} />
          }
        </button>
        {!isCollapsed && (
          <div className="space-y-0">
            {items.map(item => (
              <FixedExpenseRow
                key={item.id}
                item={item}
                onToggle={() => togglePaid(item.id)}
                onAmountChange={load}
              />
            ))}
          </div>
        )}
      </div>
    );
  })
}
```

Add `ChevronDown, ChevronUp` to the lucide-react import (line 9 currently only imports `Bell`).

**Note on Item 6 overlap**: Item 7 already incorporates the per-category paid count from Item 6 in the button label. If Item 7 is implemented, Item 6 does not need a separate edit — they land together.

---

## Item 8 — Designed 100% done-state / remove strikethrough wall (spec 2.4)
**Scope**: Frontend-only  
**Files**:
- `frontend/react/src/components/tabs/FixedExpenseRow.tsx` — lines 70–75 (vendor span)
- `frontend/react/src/components/tabs/FixedTab.tsx` — after progress bar (line 155), before category groups

**Root cause** (verified):

`FixedExpenseRow.tsx` line 71–75: vendor span uses `line-through` unconditionally when `item.paid`:
```tsx
// current:
<span className={`flex-1 text-sm transition-all duration-200 ${
  item.paid ? "line-through" : "text-white"
}`}
style={item.paid ? { color: "var(--text-muted)" } : {}}>
```

`FixedTab.tsx` has no 100% celebration card — at `pct === 100`, the UI is just every row greyed + struck through.

**What to do**:

**A) FixedExpenseRow.tsx — remove strikethrough, keep muted color + emerald check**

```tsx
// after (lines 71–75):
<span
  className="flex-1 text-sm transition-all duration-200"
  style={{ color: item.paid ? "var(--text-muted)" : "var(--text-primary, white)" }}
>
```

No `line-through`. Paid items are already visually distinguished by the filled emerald circle + emerald amount — muted text is sufficient.

**B) PoolCard.tsx entry rows (lines 124–128) — same change**

```tsx
// current:
<span className={`flex-1 text-sm ${
  entry.paid ? "line-through" : "text-white"
}`}
style={entry.paid ? { color: 'var(--text-muted)' } : {}}>

// after:
<span
  className="flex-1 text-sm"
  style={{ color: entry.paid ? "var(--text-muted)" : "white" }}
>
```

**C) FixedTab.tsx — add 100% celebration card**

Insert after the progress bar (`</div>` on line 155) and before the category groups (`{Object.entries...}` on line 159):

```tsx
{pct === 100 && (
  <div className="flex items-center gap-3 p-4 rounded-2xl mb-4
                  bg-emerald-500/10 border border-emerald-500/20">
    <span className="text-2xl">✅</span>
    <div>
      <p className="text-sm font-syne font-semibold text-emerald-400">
        All fixed expenses paid
      </p>
      <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
        {fixedExps.length} bills · {fmtInr(paidTotal)} settled · ₹0 pending
      </p>
    </div>
  </div>
)}
```

**Guardrail**: Section 1 (due reminders) renders above this entire block and is unaffected. When `pct === 100`, `reminders.length` is 0 (all are paid), so both sections coexist cleanly.

---

## Item 9 — Privacy model consistency (spec 1.2) — ✅ DONE (option A, 2026-06-29)
**Scope**: Frontend-only  
**Files**: `DashboardPage.tsx` (lines 100–104), `SummaryFlipCard.tsx` (per-card `flipped` state), `SummaryStrip.tsx` (no gating), `FixedTab.tsx` (line 142, inline total)

**Blocked by**: Open decision #1 from the spec — Debashish must pick A / B / C before this can be implemented.

**Current state verified**:
- Desktop (lines 100–104 of `DashboardPage.tsx`): three `SummaryFlipCard`s, each with independent `useState(false)` for `flipped` (line 12 of `SummaryFlipCard.tsx`). Three separate taps to reveal.
- Mobile (lines 87–97): `SummaryStrip` — shows all three values immediately via `useCountUp`, no gating.
- `FixedTab.tsx` line 142: `{fmtInr(paidTotal)} done` in plain text — ungated on both breakpoints.
- `FixedTab.tsx` line 144: `{fmtInr(unpaidTotal)} pending` — same.

**What to do (once decision is made)**:

**(A) Single global toggle (recommended by spec)**:  
- Lift a `valuesHidden: boolean` state into `DashboardShell` (or a new `PrivacyContext`).
- Pass it as a prop (or read from context) in `SummaryStrip`, `SummaryFlipCard`, and `FixedTab`.
- Remove individual `flipped` state from `SummaryFlipCard`; instead toggle between label and value based on the shared flag.
- Add an eye icon button (lucide `Eye`/`EyeOff`) in the header or summary band.
- In `FixedTab`, gate both the `paidTotal` and `unpaidTotal` inline spans with the same flag: `valuesHidden ? "••••" : fmtInr(...)`.
- Mobile `SummaryStrip` chips: show `"••••"` when `valuesHidden`.
- Persist the toggle in `localStorage` (`"walletmantra_privacy_mode"`) so preference survives tab changes.

**(B) Gate nothing**:  
- Delete flip state from `SummaryFlipCard`. Show the value directly on the front face.
- Remove the "tap to reveal" affordance text (line 47 of `SummaryFlipCard.tsx`).
- No change to `FixedTab` (already ungated).

**(C) Gate everything**:  
- Same global flag as (A), but default `valuesHidden = true` (everything hidden until toggled).
- Same changes to `FixedTab` inline totals.

---

## Tier 3 — Out of scope for this sprint

**3.1 Per-row due date + paid date** requires:
- New `paid_date: Optional[datetime]` field on `backend/models.py` → `Expense`
- Backend write on `PATCH /fixed/{id}/toggle`
- Migration script
- `types/index.ts` update
- `FixedExpenseRow.tsx` display

**3.2 Overdue banner restyling** is low priority — banner is functional and the red `border-l-4` reads correctly. Defer.

Both are Tier 3 per the spec and should be scoped in a follow-up spec.

---

## Execution order summary

| # | Spec item | File(s) | Blocked? |
|---|-----------|---------|---------|
| 1 | 1.4 Pool input stepper | `PoolCard.tsx`, `FixedExpenseRow.tsx` | No |
| 2 | 1.3 Household icon | `categories.ts` | No (rename TBD separately) |
| 3 | 1.1 ₹0 pending color | `FixedTab.tsx` | No |
| 4 | 2.1 Show pct % | `FixedTab.tsx` | No |
| 5 | 2.5 Pool status icons | `PoolCard.tsx` | No |
| 6 | 2.2 Category paid counts | `FixedTab.tsx` | No (absorbed into #7) |
| 7 | 2.3 Collapsible groups | `FixedTab.tsx` | No (absorbs #6) |
| 8 | 2.4 100% done-state | `FixedExpenseRow.tsx`, `PoolCard.tsx`, `FixedTab.tsx` | No |
| 9 | 1.2 Privacy model | `DashboardPage.tsx`, `SummaryFlipCard.tsx`, `SummaryStrip.tsx`, `FixedTab.tsx` | **Yes — awaiting decision** |
