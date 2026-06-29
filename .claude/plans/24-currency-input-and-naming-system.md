# Implementation Plan: Shared CurrencyInput + "Commitments" Naming Rule ✅ COMPLETED 2026-06-29
**Spec**: `.claude/specs/24_currency-input-and-naming-system.md`
**Date**: 2026-06-29
**Branch**: `feature/sprint06261-ui-enhancement`

---

## Overview

10 items — all frontend-only. Items are ordered smallest-blast-radius first.

Items 1 and 2–4 are independent.
Items 5–10 depend on Item 1 (CurrencyInput must exist first).

---

## Item 1 — Create `CurrencyInput` shared component
**Scope**: Frontend-only (new file)
**File**: `frontend/react/src/components/shared/CurrencyInput.tsx` *(create)*

**Root cause**: No shared currency input exists; each file rolls its own `type="number"` which renders spinner arrows.

**What to do**:

Create a controlled text-based currency input. Props match today's `type="number"` usage so callers need minimal changes:

```tsx
interface CurrencyInputProps {
  value: number;
  onChange: (value: number) => void;
  placeholder?: string;
  min?: number;
  className?: string;
  autoFocus?: boolean;
}

export function CurrencyInput({
  value,
  onChange,
  placeholder,
  className,
  autoFocus,
}: CurrencyInputProps) {
  return (
    <input
      type="text"
      inputMode="numeric"
      value={value || ""}
      onChange={e => {
        const digits = e.target.value.replace(/\D/g, "");
        onChange(digits === "" ? 0 : Number(digits));
      }}
      placeholder={placeholder}
      className={className}
      autoFocus={autoFocus}
    />
  );
}
```

Key decisions:
- `type="text"` + `inputMode="numeric"` → no spinner on any browser or mobile platform; numeric keypad on iOS/Android
- `replace(/\D/g, "")` strips all non-digits on every keystroke — rupee amounts are always whole numbers in this app
- Emits `number` (never a string); downstream state stays as `number`
- No `min` prop enforcement at the DOM level (callers already validate `> 0` before saving)
- No `₹` prefix slot needed — callers use `placeholder="Amount (₹)"` or `placeholder="₹ limit"` which already communicates the currency

**Acceptance**: File at `src/components/shared/CurrencyInput.tsx`; no other files changed yet.

---

## Item 2 — Copy fix: `QuickAddTab.tsx` — single string
**Scope**: Frontend-only
**File**: `frontend/react/src/components/tabs/QuickAddTab.tsx` line 128

**Root cause**: "Fixed bills pending:" uses "bills" as an umbrella term.

**Current code** (line 128):
```tsx
<p><span className="font-semibold">Fixed bills pending:</span> {fmtRs(ctx.fixed_unpaid_total)}</p>
```

**What to do**: Change label to "Fixed commitments pending:".

```tsx
<p><span className="font-semibold">Fixed commitments pending:</span> {fmtRs(ctx.fixed_unpaid_total)}</p>
```

---

## Item 3 — Copy fixes: `FixedTab.tsx` — 4 strings
**Scope**: Frontend-only
**File**: `frontend/react/src/components/tabs/FixedTab.tsx` — lines 182, 239, 259, 263

**Root cause** (verified against current code):

| Line | Current | Change to |
|------|---------|-----------|
| 182 | `` `${fixedExps.length} bills ·` `` | `` `${fixedExps.length} item${fixedExps.length === 1 ? '' : 's'} ·` `` |
| 239 | `"Bills with variable amount — add each payment as it happens."` | `"Commitments with variable amount — add each payment as it happens."` |
| 259 | `"No bills set up yet."` | `"No commitments set up yet."` |
| 263 | `"Settings → Monthly Bills"` | `"Settings → Monthly commitments"` |

Line 182 also fixes the "1 items" / "1 bills" grammar bug via the ternary.

**What to do**: Apply each replacement in-place. The surrounding JSX is unchanged.

---

## Item 4 — Copy fixes: `OverviewTab.tsx` — 3 strings
**Scope**: Frontend-only
**File**: `frontend/react/src/components/tabs/OverviewTab.tsx` — lines 59, 298, 663

**Root cause** (verified):

| Line | Current | Change to |
|------|---------|-----------|
| 59 | `label: "Fixed Bills"` (donut filter) | `label: "Commitments"` |
| 298 | `label: "Bills Paid"` (KPI carousel card) | `label: "Commitments Paid"` |
| 663 | `"🎉 All bills paid this month"` | `"🎉 All commitments paid this month"` |

Note: `gradientClass: "kpi-card-bills"` on line 303 is an internal CSS class name — do not change it (visual redesign is Spec 25's scope).

**What to do**: Apply each string replacement in place.

---

## Item 5 — Currency + copy: `BillsSection.tsx`
**Scope**: Frontend-only
**File**: `frontend/react/src/components/settings/BillsSection.tsx`
**Depends on**: Item 1

**Root cause** (verified):
- Line 69–75: `TemplateEditRow` amount uses `type="number" step="1"` (spinner)
- Line 332–342: Add-bill amount uses `type="number" step="1"` (spinner)
- Line 136: `({items.length} bills)` — grammar bug ("1 bills") + wrong noun
- Line 228: `h2` "📋 Monthly Bills" — umbrella term
- Line 303: "Add a new bill" — accordion trigger
- Line 384: "＋ Add Bill" — submit button

**What to do**:

1. Add import at top: `import { CurrencyInput } from "@/components/shared/CurrencyInput";`

2. In `TemplateEditRow` (line 69–76), replace the `<input type="number" ...>` for `amt`:
   ```tsx
   // before
   <input
     type="number"
     min="0"
     step="1"
     value={amt}
     onChange={e => setAmt(Number(e.target.value))}
     className={`${inputCls}`}
   />
   // after
   <CurrencyInput
     value={amt}
     onChange={v => setAmt(v)}
     className={`${inputCls}`}
   />
   ```

3. In add-bill form (line 332–342), replace the amount `<input type="number" ...>`:
   ```tsx
   // before
   <input
     type="number"
     min="0"
     step="1"
     value={newAmt || ""}
     onChange={e => setNewAmt(Number(e.target.value))}
     placeholder={newKind === "fixed" ? "Monthly amount (₹)" : "Typical amount (₹)"}
     className={inputCls}
   />
   // after
   <CurrencyInput
     value={newAmt}
     onChange={v => setNewAmt(v)}
     placeholder={newKind === "fixed" ? "Monthly amount (₹)" : "Typical amount (₹)"}
     className={inputCls}
   />
   ```

4. Copy changes:
   - Line 136: `({items.length} bills)` → `({items.length} item{items.length === 1 ? '' : 's'})`
   - Line 228: `"📋 Monthly Bills"` → `"📋 Monthly commitments"`
   - Line 303: `"Add a new bill"` → `"Add a commitment"`
   - Line 384: `"＋ Add Bill"` → `"＋ Add commitment"`

---

## Item 6 — Currency swap: `CapsSection.tsx`
**Scope**: Frontend-only
**File**: `frontend/react/src/components/settings/CapsSection.tsx`
**Depends on**: Item 1

**Root cause** (verified):
- Lines 102–116: Cap-edit input — `type="number" step="1"` (in the `.map()` per budget row)
- Lines 149–157: Add-cap input — `type="number" step="1" placeholder="₹ limit"`

**What to do**:

1. Add import: `import { CurrencyInput } from "@/components/shared/CurrencyInput";`

2. Cap-edit input (inside `.map()`, lines 102–116):
   ```tsx
   // before
   <input
     type="number"
     min="0"
     step="1"
     value={updates[b.category] ?? ""}
     onChange={e =>
       setUpdates(prev => ({
         ...prev,
         [b.category]: Number(e.target.value),
       }))
     }
     className="w-full bg-dark-card2 border border-white/10 rounded-xl
                px-3 py-2 text-white text-sm
                focus:border-accent focus:outline-none transition-colors"
   />
   // after
   <CurrencyInput
     value={updates[b.category] ?? 0}
     onChange={v => setUpdates(prev => ({ ...prev, [b.category]: v }))}
     className="w-full bg-dark-card2 border border-white/10 rounded-xl
                px-3 py-2 text-white text-sm
                focus:border-accent focus:outline-none transition-colors"
   />
   ```

3. Add-cap input (lines 149–157):
   ```tsx
   // before
   <input
     type="number"
     min="0"
     step="1"
     placeholder="₹ limit"
     value={newLimit || ""}
     onChange={e => setNewLimit(Number(e.target.value))}
     className="w-28 bg-dark-card2 border border-white/10 rounded-xl px-3 py-2
                text-white text-sm focus:border-accent focus:outline-none"
   />
   // after
   <CurrencyInput
     value={newLimit}
     onChange={v => setNewLimit(v)}
     placeholder="₹ limit"
     className="w-28 bg-dark-card2 border border-white/10 rounded-xl px-3 py-2
                text-white text-sm focus:border-accent focus:outline-none"
   />
   ```

---

## Item 7 — Currency swap: `IncomeSection.tsx`
**Scope**: Frontend-only
**File**: `frontend/react/src/components/settings/IncomeSection.tsx` line 192–200
**Depends on**: Item 1

**Root cause** (verified): Income amount input at line 192 uses `type="number" step="1"`.

**What to do**:

1. Add import: `import { CurrencyInput } from "@/components/shared/CurrencyInput";`

2. Replace income amount input (lines 192–200):
   ```tsx
   // before
   <input
     type="number"
     min="0"
     step="1"
     value={amount || ""}
     onChange={e => setAmount(Number(e.target.value))}
     placeholder="Amount (₹)"
     className={inputCls}
     autoFocus
   />
   // after
   <CurrencyInput
     value={amount}
     onChange={v => setAmount(v)}
     placeholder="Amount (₹)"
     className={inputCls}
     autoFocus
   />
   ```

---

## Item 8 — Currency swap: `ShortcutsSection.tsx`
**Scope**: Frontend-only
**File**: `frontend/react/src/components/settings/ShortcutsSection.tsx`
**Depends on**: Item 1

**Root cause** (verified):
- Lines 54–61: `ShortcutEditRow` amount — `type="number" step="50"`
- Lines 172–178: Add-shortcut amount — `type="number" step="50"`

**What to do**:

1. Add import: `import { CurrencyInput } from "@/components/shared/CurrencyInput";`

2. `ShortcutEditRow` amount (lines 54–61):
   ```tsx
   // before
   <input
     type="number"
     min="0"
     step="50"
     value={amt}
     onChange={e => setAmt(Number(e.target.value))}
     className={`w-20 ${inputCls}`}
   />
   // after
   <CurrencyInput
     value={amt}
     onChange={v => setAmt(v)}
     className={`w-20 ${inputCls}`}
   />
   ```

3. Add-shortcut amount (lines 172–178):
   ```tsx
   // before
   <input
     type="number"
     min="0"
     step="50"
     value={newAmt || ""}
     onChange={e => setNewAmt(Number(e.target.value))}
     placeholder="Amount (₹)"
     className={inputCls}
   />
   // after
   <CurrencyInput
     value={newAmt}
     onChange={v => setNewAmt(v)}
     placeholder="Amount (₹)"
     className={inputCls}
   />
   ```

---

## Item 9 — Currency standardize: `PoolCard.tsx`
**Scope**: Frontend-only
**File**: `frontend/react/src/components/tabs/PoolCard.tsx` lines 167–178
**Depends on**: Item 1

**Root cause** (verified): PoolCard already avoids spinners via `type="text" inputMode="decimal"` + CSS to hide webkit controls (lines 167–178). This is compliant but non-standard across the codebase. Replace with `CurrencyInput` to consolidate.

Note: Current code uses `parseFloat` — changing to `CurrencyInput` (integer only) is correct since pool payment amounts are whole rupees.

**What to do**:

1. Add import: `import { CurrencyInput } from "@/components/shared/CurrencyInput";`

2. Replace the amount input (lines 167–178):
   ```tsx
   // before
   <input
     type="text"
     inputMode="decimal"
     value={amount || ""}
     onChange={e => setAmount(parseFloat(e.target.value) || 0)}
     placeholder="₹"
     className="w-24 bg-dark-card2 border border-white/10 rounded-lg
                px-3 py-2 text-white text-sm
                [appearance:textfield]
                [&::-webkit-outer-spin-button]:appearance-none
                [&::-webkit-inner-spin-button]:appearance-none
                focus:border-accent focus:outline-none"
   />
   // after
   <CurrencyInput
     value={amount}
     onChange={v => setAmount(v)}
     placeholder="₹"
     className="w-24 bg-dark-card2 border border-white/10 rounded-lg
                px-3 py-2 text-white text-sm focus:border-accent focus:outline-none"
   />
   ```
   The three `[appearance:...]` classes can be dropped since `type="text"` never has spinners.

---

## Item 10 — Currency + copy: `OnboardingWizard.tsx`
**Scope**: Frontend-only
**File**: `frontend/react/src/components/onboarding/OnboardingWizard.tsx`
**Depends on**: Item 1

**Root cause** (verified):
- Line 197–205: Step 1 income amount — `type="number" step="1"`
- Line 306–317: Step 2 bill amount — `type="number" step="1"`
- Lines 399–410: Step 3 cap inputs — `type="number" step="1"`, but **these have an overlay ×-clear button using absolute-positioned `div style`**. Use an inline fix here instead of `CurrencyInput` since the overlay architecture ties to the raw `<input>`.
- Line 229: `"📋 Step 2 of 3 — Your Monthly Bills"` — umbrella term
- Line 240: `{addedBills.length} bill(s) added` — count noun + grammar
- Line 361: `"＋ Add Bill"` — submit button

**What to do**:

1. Add import: `import { CurrencyInput } from "@/components/shared/CurrencyInput";`

2. Step 1 income amount (lines 197–205):
   ```tsx
   // before
   <input
     type="number"
     min="0"
     step="1"
     value={incomeAmt || ""}
     onChange={(e) => setIncomeAmt(Number(e.target.value))}
     placeholder="Amount (₹)"
     className={inputCls}
   />
   // after
   <CurrencyInput
     value={incomeAmt}
     onChange={v => setIncomeAmt(v)}
     placeholder="Amount (₹)"
     className={inputCls}
   />
   ```

3. Step 2 bill amount (lines 306–317):
   ```tsx
   // before
   <input
     type="number"
     min="0"
     step="1"
     value={billAmt || ""}
     onChange={(e) => setBillAmt(Number(e.target.value))}
     placeholder={billKind === "fixed" ? "Amount (₹)" : "Typical amount (optional)"}
     className="bg-dark-card2 border border-white/10 rounded-xl px-3 py-3
                text-white text-sm placeholder-white/30 focus:border-accent focus:outline-none"
   />
   // after
   <CurrencyInput
     value={billAmt}
     onChange={v => setBillAmt(v)}
     placeholder={billKind === "fixed" ? "Amount (₹)" : "Typical amount (optional)"}
     className="bg-dark-card2 border border-white/10 rounded-xl px-3 py-3
                text-white text-sm placeholder-white/30 focus:border-accent focus:outline-none"
   />
   ```

4. Step 3 cap inputs (lines 399–410) — inline fix only, not `CurrencyInput` (overlay ×-button architecture):
   Change `type="number"` → `type="text"` and `step="1"` → `inputMode="numeric"`.
   Update onChange to strip non-digits:
   ```tsx
   // before
   <input
     type="number"
     min="0"
     step="1"
     value={val}
     onFocus={(e) => e.target.select()}
     onChange={(e) => setCaps((prev) => ({ ...prev, [cat]: e.target.value }))}
     ...
   />
   // after
   <input
     type="text"
     inputMode="numeric"
     value={val}
     onFocus={(e) => e.target.select()}
     onChange={(e) =>
       setCaps((prev) => ({
         ...prev,
         [cat]: e.target.value.replace(/\D/g, ""),
       }))
     }
     ...
   />
   ```
   The `""` empty-string case is preserved (allows the placeholder to show after ×-clear).

5. Copy changes:
   - Line 229: `"📋 Step 2 of 3 — Your Monthly Bills"` → `"📋 Step 2 of 3 — Your Monthly commitments"`
   - Line 240: `` `${addedBills.length} bill(s) added` `` → `` `${addedBills.length} commitment${addedBills.length === 1 ? '' : 's'} added` ``
   - Line 361: `"＋ Add Bill"` → `"＋ Add commitment"`

---

## Excluded (per spec)

- `FixedExpenseRow.tsx` — uses `inputMode="decimal"` already (no `type="number"`); not a currency field anyway (it's a pay-in amount field, already handled correctly)
- `QuickAddTab.tsx` — confirmed no `type="number"` currency inputs (grep returned empty)
- Category names ("Electric Bills") and the `gradientClass: "kpi-card-bills"` CSS identifier — untouched
- Any backend changes — spec is frontend-only throughout
- Layout/visual redesign — Spec 25's scope

---

## Summary

| # | File | Changes | Type |
|---|------|---------|------|
| 1 | `shared/CurrencyInput.tsx` (new) | Create component | Currency |
| 2 | `tabs/QuickAddTab.tsx` | 1 string | Copy |
| 3 | `tabs/FixedTab.tsx` | 4 strings | Copy |
| 4 | `tabs/OverviewTab.tsx` | 3 strings | Copy |
| 5 | `settings/BillsSection.tsx` | 2 inputs + 4 strings | Both |
| 6 | `settings/CapsSection.tsx` | 2 inputs | Currency |
| 7 | `settings/IncomeSection.tsx` | 1 input | Currency |
| 8 | `settings/ShortcutsSection.tsx` | 2 inputs | Currency |
| 9 | `tabs/PoolCard.tsx` | 1 input | Currency |
| 10 | `onboarding/OnboardingWizard.tsx` | 2 inputs + 1 inline fix + 3 strings | Both |

**Start with Item 1** — it's the prerequisite for 5–10. Items 2–4 can be done in any order independently of 1.
