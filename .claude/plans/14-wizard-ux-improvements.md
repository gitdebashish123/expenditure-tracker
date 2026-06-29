# Implementation Plan: Wizard UX Improvements — Auto-Suggest & Spending Caps
**Spec**: `.claude/specs/14_wizard-ux-improvements.md`
**Date**: 2026-06-28
**Branch**: `feature/sprint06261-ui-enhancement`

---

## Overview

6 items total — all frontend-only. No backend changes.
Items are ordered smallest-blast-radius first. Items 2–4 depend on Item 1; Items 5–6 are independent of Items 1–4 and can be done in any order relative to them.

---

## Spec Divergences (code vs. spec)

> Read the actual file before planning — two meaningful divergences found:

**Divergence 1 — Step 2 bill form is not a list.**
The spec describes a `BillEntry[]` array with per-entry `categoryAutoSet` / `userOverrode` fields. The actual code (`OnboardingWizard.tsx` lines 54–59) has a **single flat form** (`billName`, `billCat`, `billKind`, `billAmt`) that resets after each "Add Bill" click. There is never more than one bill being entered at a time. The per-entry array approach in the spec does not apply. Plan adapts to two flat boolean state vars instead.

**Divergence 2 — `saveCaps` already filters zeros.**
The spec says "add a filter for empty/zero entries on save". The current `saveCaps` (line 117) already has `.filter(([, v]) => v > 0)`. After the `Record<string, string>` type change the filter condition just needs updating from `v > 0` to `Number(raw) > 0` — the semantic behaviour is unchanged.

---

## Item 1 — Create `categoryKeywords.ts`
**Scope**: Frontend-only
**File**: `frontend/react/src/utils/categoryKeywords.ts` (**new file**)
**Depends on**: nothing — do this first

**Root cause**: File does not exist. `suggestCategory()` is needed by Item 2.

**What to do**:
Create the file with the exact content from the spec. One note: the spec imports `FIXED_CATEGORIES` at the top but does not actually use it in the file body — omit that import to avoid a lint warning. The `CATEGORY_KEYWORDS` array and `suggestCategory` function are the only exports needed.

```ts
// frontend/react/src/utils/categoryKeywords.ts

export type CategoryKeywordRule = {
  category: string;
  keywords: string[];
};

export const CATEGORY_KEYWORDS: CategoryKeywordRule[] = [
  { category: 'EMI',           keywords: ['emi','loan','instalment','installment','car loan','home loan','bike loan','personal loan','education loan','credit card emi','no cost emi','bajaj finserv'] },
  { category: 'Insurance',     keywords: ['insurance','premium','lic','term plan','mediclaim','health insurance','policy','star health','hdfc life','bajaj allianz','max life','tata aia'] },
  { category: 'Savings',       keywords: ['rd','recurring deposit','fd','fixed deposit','ppf','savings','piggy','emergency fund','chit fund'] },
  { category: 'Investments',   keywords: ['sip','nps','elss','mutual fund','stocks','shares','zerodha','groww','kuvera','coin','demat','investment'] },
  { category: 'Utilities',     keywords: ['electricity','water','gas','internet','broadband','wifi','postpaid','mobile bill','jio','airtel','bsnl','vi ','bescom','tangedco','piped gas','landline'] },
  { category: 'Housing',       keywords: ['rent','maintenance','society','pg','hostel','flat','apartment','hoa','strata'] },
  { category: 'Household',     keywords: ['maid','cook','driver','nanny','bai','dhobi','laundry','helper','housekeeper','cleaning','watchman','security','garbage'] },
  { category: 'Entertainment', keywords: ['netflix','spotify','prime','hotstar','disney','youtube premium','zee5','sonyliv','gym','fitness','subscription','membership','cult.fit','apple one'] },
  { category: 'Course',        keywords: ['tuition','coaching','school fees','college fees','course','udemy','coursera','unacademy','byju','fees'] },
];

export function suggestCategory(billName: string): string | null {
  const lower = billName.toLowerCase().trim();
  if (!lower) return null;
  for (const rule of CATEGORY_KEYWORDS) {
    for (const kw of rule.keywords) {
      if (lower.includes(kw)) return rule.category;
    }
  }
  return null;
}
```

---

## Item 2 — Add auto-suggest state vars and wire into bill name onChange
**Scope**: Frontend-only
**File**: `frontend/react/src/components/onboarding/OnboardingWizard.tsx`
**Depends on**: Item 1

**Root cause**: The bill name `onChange` (line 250) calls only `setBillName(e.target.value)`. There is no call to `suggestCategory` and no `categoryAutoSet` / `userOverrode` tracking.

**What to do**:

**Step A — add import** at the top of the file (after the existing imports, around line 5):
```ts
import { suggestCategory } from "@/utils/categoryKeywords";
```

**Step B — add two new state vars** after the existing Step 2 state block (after line 58):
```ts
const [billCatAutoSet,    setBillCatAutoSet]    = useState(false);
const [billCatUserOverrode, setBillCatUserOverrode] = useState(false);
```

**Step C — replace the bill name input's `onChange`** (currently line 250, a single `setBillName` call):

Before:
```tsx
onChange={(e) => setBillName(e.target.value)}
```

After:
```tsx
onChange={(e) => {
  const val = e.target.value;
  setBillName(val);
  if (!val) {
    setBillCat(FIXED_CATEGORIES[0]);
    setBillCatAutoSet(false);
    setBillCatUserOverrode(false);
    return;
  }
  if (!billCatUserOverrode) {
    const suggested = suggestCategory(val);
    if (suggested) {
      setBillCat(suggested);
      setBillCatAutoSet(true);
    } else {
      setBillCatAutoSet(false);
    }
  }
}}
```

**Step D — mark category as user-overridden** when the select changes (currently line 256):

Before:
```tsx
onChange={(e) => setBillCat(e.target.value)}
```

After:
```tsx
onChange={(e) => {
  setBillCat(e.target.value);
  setBillCatAutoSet(false);
  setBillCatUserOverrode(true);
}}
```

**Step E — reset auto-suggest flags in `addBill`** alongside the existing form reset (lines 107–110). Add after `setBillKind("fixed")`:
```ts
setBillCatAutoSet(false);
setBillCatUserOverrode(false);
setBillCat(FIXED_CATEGORIES[0]);
```
Note: `setBillCat` is not currently called in the reset block — `billCat` was left sticky between entries. This reset aligns with the spec ("clearing the bill name → category resets to default") and ensures each new bill starts from "Housing".

---

## Item 3 — Add "✨ suggested" badge next to category select
**Scope**: Frontend-only
**File**: `frontend/react/src/components/onboarding/OnboardingWizard.tsx`
**Depends on**: Item 2 (needs `billCatAutoSet` state)

**Root cause**: The category `<select>` at line 254 has no `<label>` wrapper — it sits bare in a grid cell. There is nowhere to render the badge yet.

**What to do**:
Wrap the select in a `<div>` that adds a small label row above it. Replace the bare `<select>` (lines 254–265) with:

```tsx
<div>
  <div className="flex items-center gap-2 mb-1">
    <span className="text-white/60 text-xs">Category</span>
    {billCatAutoSet && (
      <span style={{ fontSize: 10, opacity: 0.55 }}>✨ suggested</span>
    )}
  </div>
  <select
    value={billCat}
    onChange={(e) => {
      setBillCat(e.target.value);
      setBillCatAutoSet(false);
      setBillCatUserOverrode(true);
    }}
    className="w-full bg-dark-card2 border border-white/10 rounded-xl px-3 py-3
               text-white text-sm focus:border-accent focus:outline-none"
  >
    {FIXED_CATEGORIES.map((c) => (
      <option key={c} value={c}>
        {CATEGORY_ICONS[c]} {c}
      </option>
    ))}
  </select>
</div>
```

The `onChange` here supersedes the version from Item 2 Step D — write it once here, not twice.

**Grid layout note**: The bill form uses `grid grid-cols-2 gap-3` (line 247). The name input spans both columns via `col-span-2` (line 252). The category select and amount input each occupy one column. Adding the wrapper `<div>` around the select does not change the column count — it replaces the bare `<select>` in that grid cell.

---

## Item 4 — Handle `FIXED_CATEGORIES` vs. all categories for auto-suggest
**Scope**: Frontend-only
**File**: `frontend/react/src/components/onboarding/OnboardingWizard.tsx`
**Depends on**: Items 1–3

**Root cause**: The category dropdown in Step 2 renders only `FIXED_CATEGORIES` (line 260). The spec's `CATEGORY_KEYWORDS` includes `Entertainment` and `Course`, which are in `VAR_CATEGORIES` (not `FIXED_CATEGORIES`). If `suggestCategory` returns "Entertainment" or "Course", `setBillCat` sets the value but the select's option list won't contain it — the select will silently show a blank or fall back to the first option.

**What to do**:
Import `VAR_CATEGORIES` alongside `FIXED_CATEGORIES` (already at line 4) and build a combined list for the Step 2 dropdown:

```ts
// At the top of the component body (before the return), add:
const ALL_BILL_CATEGORIES = [...FIXED_CATEGORIES, ...VAR_CATEGORIES];
```

Then in the `<select>` from Item 3, replace `FIXED_CATEGORIES.map(...)` with `ALL_BILL_CATEGORIES.map(...)`.

This makes Entertainment, Course, and other VAR categories selectable as bill categories — appropriate for subscriptions (Netflix → Entertainment) and tuition (Byju → Course).

---

## Item 5 — Change `caps` state type to `Record<string, string>`
**Scope**: Frontend-only
**File**: `frontend/react/src/components/onboarding/OnboardingWizard.tsx`
**Depends on**: nothing (independent of Items 1–4)

**Root cause**: Line 62 declares `caps` as `Record<string, number>`. Line 364 stores `Number(e.target.value)` — an empty input field resolves to `Number("") = 0`, which means the field can never hold a true empty/mid-edit state. `onFocus` select-all and the × clear button (Item 6) both require the field to hold an empty string.

**What to do**:

**Step A — change state declaration** (line 62):

Before:
```ts
const [caps, setCaps] = useState<Record<string, number>>(DEFAULT_CAPS);
```

After:
```ts
const [caps, setCaps] = useState<Record<string, string>>(
  Object.fromEntries(Object.entries(DEFAULT_CAPS).map(([k, v]) => [k, String(v)]))
);
```

**Step B — change `onChange` in the caps input** (line 363–365):

Before:
```ts
onChange={(e) =>
  setCaps((prev) => ({ ...prev, [cat]: Number(e.target.value) }))
}
```

After:
```ts
onChange={(e) => setCaps((prev) => ({ ...prev, [cat]: e.target.value }))}
```

**Step C — update `saveCaps` filter** (line 117):

Before:
```ts
.filter(([, v]) => v > 0)
.map(([category, limit_amount]) =>
  api.put("/budget", { category, limit_amount })
)
```

After:
```ts
.filter(([, raw]) => Number(raw) > 0)
.map(([category, raw]) =>
  api.put("/budget", { category, limit_amount: Number(raw) })
)
```

**Step D — update `Object.entries(caps)` destructuring** in the JSX render (line 353):
`val` becomes a string. The `value={val}` on the input is now a string — correct for a `type="number"` controlled input (React accepts string values for number inputs). No type cast needed.

---

## Item 6 — Add `onFocus` select-all, placeholder, `pr-8`, and × button to cap inputs
**Scope**: Frontend-only
**File**: `frontend/react/src/components/onboarding/OnboardingWizard.tsx`
**Depends on**: Item 5 (needs `caps` to be `Record<string, string>` for the `caps[cat] !== ""` check)

**Root cause**: The cap inputs (lines 358–369) have no `onFocus`, no placeholder, no `pr-8` padding, and no × button. The outer `<div>` at line 354 is bare with no `position: relative`.

**What to do**:
Replace the entire `{Object.entries(caps).map(([cat, val]) => ( ... ))}` block (lines 353–370) with:

```tsx
{Object.entries(caps).map(([cat, val]) => (
  <div key={cat}>
    <label className="text-white/60 text-xs mb-1 block">
      {CATEGORY_ICONS[cat] ?? "📦"} {cat}
    </label>
    <div style={{ position: 'relative' }}>
      <input
        type="number"
        min="0"
        step="1"
        value={val}
        onFocus={(e) => e.target.select()}
        onChange={(e) => setCaps((prev) => ({ ...prev, [cat]: e.target.value }))}
        placeholder="No cap"
        className="w-full bg-dark-card2 border border-white/10 rounded-xl
                   px-3 py-2 pr-8 text-white text-sm focus:border-accent focus:outline-none"
      />
      {val !== "" && (
        <button
          type="button"
          onClick={() => setCaps((prev) => ({ ...prev, [cat]: "" }))}
          style={{
            position: 'absolute', right: 8, top: '50%',
            transform: 'translateY(-50%)',
            color: 'rgba(255,255,255,0.3)',
            fontSize: 14, lineHeight: 1, background: 'none', border: 'none',
            cursor: 'pointer', padding: '2px 4px',
          }}
          aria-label={`Clear ${cat} cap`}
        >
          ×
        </button>
      )}
    </div>
  </div>
))}
```

Note `val` here is already a string (after Item 5), so `val !== ""` is correct. The `onChange` here matches Step B from Item 5 — write it once here rather than in Item 5 and again here.

---

## Implementation Order Summary

| # | Item | Depends on | Effort |
|---|------|-----------|--------|
| 1 | Create `categoryKeywords.ts` | — | XS |
| 2 | Auto-suggest state + bill name onChange | 1 | S |
| 3 | "✨ suggested" badge + label wrapper | 2 | XS |
| 4 | ALL_BILL_CATEGORIES for dropdown | 1–3 | XS |
| 5 | `caps` state → `Record<string, string>` + saveCaps filter | — | XS |
| 6 | `onFocus`, placeholder, pr-8, × button on cap inputs | 5 | XS |

**Start with Item 1** (new file, zero risk). Then Items 2 → 3 → 4 in sequence. Items 5 and 6 can be done in parallel with Items 1–4 or after — no shared state between the two features.
