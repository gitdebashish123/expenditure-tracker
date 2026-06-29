# Spec: Wizard UX Improvements — Smart Category Auto-Suggest & Spending Caps
**Date**: 2026-06-28
**Status**: 🔴 Ready to implement
**Branch**: `feature/sprint06261-ui-enhancement`
**Follows**: `13_ui-fixes-and-naming.md`

---

## Overview

Two independent UX improvements to the onboarding wizard:

- **Feature 1 (Step 2)** — Smart keyword-to-category auto-suggest on the bill name field
- **Feature 2 (Step 3)** — Easier clear & edit for spending cap fields (focus-to-select, × button, "No cap" placeholder)

---

## Feature 1 — Smart Category Auto-Suggest (Step 2)

### Context

Step 2 of 3 (Monthly Bills) asks users to enter a bill name and manually select a category. New users make predictable mistakes — e.g. entering "Car Loan" but leaving the default category "Housing" because the dropdown default never changes. The fix is a deterministic keyword → category auto-suggest that fires on every keystroke. No AI involved.

### Scope

**In scope**: Step 2 bill name input → auto-sets category dropdown; new constants file; subtle "suggested" badge; user can override (override persists).

**Out of scope**: Fuzzy matching or AI categorisation; Settings page fixed expenses editor.

---

### 1A — Keyword-to-category mapping constants

**New file**: `frontend/react/src/utils/categoryKeywords.ts`

```ts
import { FIXED_CATEGORIES } from './categories';

export type CategoryKeywordRule = {
  category: string;   // must match a key in CATEGORY_ICONS
  keywords: string[]; // all lowercase; matched as "bill name contains keyword"
};

/**
 * Ordered priority list — first match wins.
 * All keywords lowercase. Matching is case-insensitive contains.
 */
export const CATEGORY_KEYWORDS: CategoryKeywordRule[] = [
  {
    category: 'EMI',
    keywords: [
      'emi', 'loan', 'instalment', 'installment',
      'car loan', 'home loan', 'bike loan', 'personal loan',
      'education loan', 'credit card emi', 'no cost emi', 'bajaj finserv',
    ],
  },
  {
    category: 'Insurance',
    keywords: [
      'insurance', 'premium', 'lic', 'term plan', 'mediclaim',
      'health insurance', 'policy', 'star health', 'hdfc life',
      'bajaj allianz', 'max life', 'tata aia',
    ],
  },
  {
    category: 'Savings',
    keywords: [
      'rd', 'recurring deposit', 'fd', 'fixed deposit',
      'ppf', 'savings', 'piggy', 'emergency fund', 'chit fund',
    ],
  },
  {
    category: 'Investments',
    keywords: [
      'sip', 'nps', 'elss', 'mutual fund', 'stocks', 'shares',
      'zerodha', 'groww', 'kuvera', 'coin', 'demat', 'investment',
    ],
  },
  {
    category: 'Utilities',
    keywords: [
      'electricity', 'water', 'gas', 'internet', 'broadband',
      'wifi', 'postpaid', 'mobile bill', 'jio', 'airtel', 'bsnl',
      'vi ', 'bescom', 'tangedco', 'piped gas', 'landline',
    ],
  },
  {
    category: 'Housing',
    keywords: [
      'rent', 'maintenance', 'society', 'pg', 'hostel',
      'flat', 'apartment', 'hoa', 'strata',
    ],
  },
  {
    category: 'Household',
    keywords: [
      'maid', 'cook', 'driver', 'nanny', 'bai', 'dhobi',
      'laundry', 'helper', 'housekeeper', 'cleaning', 'watchman',
      'security', 'garbage',
    ],
  },
  {
    category: 'Entertainment',
    keywords: [
      'netflix', 'spotify', 'prime', 'hotstar', 'disney',
      'youtube premium', 'zee5', 'sonyliv', 'gym', 'fitness',
      'subscription', 'membership', 'cult.fit', 'apple one',
    ],
  },
  {
    category: 'Course',
    keywords: [
      'tuition', 'coaching', 'school fees', 'college fees', 'course',
      'udemy', 'coursera', 'unacademy', 'byju', 'fees',
    ],
  },
];

/**
 * Returns the best-matching category key for a given bill name,
 * or null if no keyword matches.
 */
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

**Priority note**: EMI is checked before Insurance deliberately — "Bajaj Finserv loan" should match EMI, not Insurance. Multi-word keywords (e.g. `car loan`) prevent Housing or Travel from matching on the noun alone.

---

### 1B — Wire auto-suggest into Step 2

**Target component**: Onboarding wizard Step 2. Locate by grepping for "Monthly Bills" or "Step 2" — likely `frontend/react/src/components/Onboarding.tsx` or a sub-component.

**Behaviour**:

1. On every keystroke in the bill name field, call `suggestCategory(value)`.
2. If a match is returned and the user has not manually overridden the category for this entry, set the category dropdown to the matched value.
3. If the user manually changes the category via the dropdown, set a `userOverrode` flag. Do not auto-suggest again for this entry.
4. If the bill name is cleared, reset category to default (`"Housing"`) and clear `userOverrode`.
5. Show a subtle **"✨ suggested"** badge next to the category label when auto-set. Remove it on manual override.

**State shape (per bill entry)**:

```ts
type BillEntry = {
  name: string;
  category: string;
  amount: string;
  isFixed: boolean;
  categoryAutoSet: boolean; // true = auto-set by suggestCategory
  userOverrode: boolean;    // true = user manually picked a category
};
```

**Handler pseudocode**:

```ts
function handleNameChange(index: number, value: string) {
  const suggested = suggestCategory(value);
  setBills(prev => prev.map((b, i) => {
    if (i !== index) return b;
    const autoSet = !!suggested && !b.userOverrode;
    return {
      ...b,
      name: value,
      category: autoSet ? suggested! : (value === '' ? 'Housing' : b.category),
      categoryAutoSet: value === '' ? false : autoSet,
      userOverrode: value === '' ? false : b.userOverrode,
    };
  }));
}

function handleCategoryChange(index: number, value: string) {
  setBills(prev => prev.map((b, i) =>
    i !== index ? b : { ...b, category: value, categoryAutoSet: false, userOverrode: true }
  ));
}
```

**"✨ suggested" badge**:

```tsx
<label>
  Category
  {bill.categoryAutoSet && (
    <span style={{ fontSize: 11, marginLeft: 6, opacity: 0.6 }}>✨ suggested</span>
  )}
</label>
```

---

### Feature 1 — Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC1 | Typing "Car Loan" → category auto-switches to "EMI" |
| AC2 | Typing "SIP" → auto-switches to "Investments" |
| AC3 | Typing "Rent" → auto-switches to "Housing" |
| AC4 | Typing "Netflix" → auto-switches to "Entertainment" |
| AC5 | Typing "Maid" → auto-switches to "Household" |
| AC6 | Unrecognised name (e.g. "Miscellaneous") → category unchanged |
| AC7 | "✨ suggested" badge appears when category was auto-set |
| AC8 | User manually changes category → badge disappears, no further auto-suggest |
| AC9 | Clearing bill name → category resets to default, badge disappears |
| AC10 | Multiple bill entries — auto-suggest is per-entry, not global |
| AC11 | No regression to any other wizard step |

---

## Feature 2 — Spending Caps Easier Clear & Edit (Step 3)

### Context

Step 3 pre-fills spending cap fields with hardcoded defaults (Food ₹5,000, Groceries ₹8,000, etc.) using controlled `value={number}` inputs. This means users must manually select-all before typing, have no quick way to zero out a field, and get no affordance that blank means "skip". Three focused fixes address this.

### Scope

**In scope**: Step 3 caps fields in `OnboardingWizard.tsx` only — focus-to-select, × clear button, "No cap" placeholder, save filter.

**Out of scope**: Changing default values; income-proportional defaults; Settings page budget editor; Steps 1 and 2.

---

### 2A — Switch caps state to `Record<string, string>`

Allows inputs to hold an empty string mid-edit; convert to number only on save.

```ts
// Before
const [caps, setCaps] = useState<Record<string, number>>(DEFAULT_CAPS);

// After
const [caps, setCaps] = useState<Record<string, string>>(
  Object.fromEntries(Object.entries(DEFAULT_CAPS).map(([k, v]) => [k, String(v)]))
);
```

On `onChange`, store raw string:
```ts
onChange={(e) => setCaps(prev => ({ ...prev, [cat]: e.target.value }))}
```

---

### 2B — Focus selects all text

```ts
onFocus={(e) => e.target.select()}
```

User clicks the field and can immediately type a replacement without selecting manually.

---

### 2C — × clear button + "No cap" placeholder

```tsx
<div key={cat} style={{ position: 'relative' }}>
  <label className="text-white/60 text-xs mb-1 block">
    {CATEGORY_ICONS[cat] ?? "📦"} {cat}
  </label>
  <div style={{ position: 'relative' }}>
    <input
      type="number"
      min="0"
      step="1"
      value={caps[cat]}
      onFocus={(e) => e.target.select()}
      onChange={(e) => setCaps(prev => ({ ...prev, [cat]: e.target.value }))}
      placeholder="No cap"
      className="w-full bg-dark-card2 border border-white/10 rounded-xl
                 px-3 py-2 pr-8 text-white text-sm focus:border-accent focus:outline-none"
    />
    {caps[cat] !== "" && (
      <button
        type="button"
        onClick={() => setCaps(prev => ({ ...prev, [cat]: "" }))}
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
```

`pr-8` on the input prevents text overlapping the × button.

---

### 2D — Filter empty/zero on save

```ts
const saveCaps = async (skip = false) => {
  if (!skip) {
    await Promise.all(
      Object.entries(caps)
        .filter(([, raw]) => Number(raw) > 0)   // skip empty string and 0
        .map(([category, raw]) =>
          api.put("/budget", { category, limit_amount: Number(raw) })
        )
    );
  }
  await complete();
};
```

---

### Feature 2 — Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC1 | Clicking a pre-filled field selects all text — user can immediately type a new value |
| AC2 | × button appears inside each field that has a value |
| AC3 | Clicking × clears the field; placeholder "No cap" appears |
| AC4 | × button is hidden when field is already empty |
| AC5 | Empty fields are not submitted as budget limits |
| AC6 | Fields with valid numbers still save correctly on "Let's Go!" |
| AC7 | "Skip" still skips all caps as before |
| AC8 | No visual regression — field height and layout unchanged |

---

## Files to Create / Modify

| File | Action |
|------|--------|
| `frontend/react/src/utils/categoryKeywords.ts` | **Create** — keyword map + `suggestCategory()` helper |
| `frontend/react/src/components/Onboarding.tsx` (or equivalent Step 2 component) | **Modify** — wire `suggestCategory` into bill name `onChange`, add `categoryAutoSet` state, add badge |
| `frontend/react/src/components/onboarding/OnboardingWizard.tsx` | **Modify** — caps state type to `string`, `onFocus` select-all, × button, `placeholder`, save filter |

## Files NOT Modified

- `frontend/react/src/utils/categories.ts`
- `backend/main.py`
- Any other component

---

## Implementation Order

| # | Task | Feature | Effort |
|---|------|---------|--------|
| 1 | Create `categoryKeywords.ts` with map + `suggestCategory()` | 1 | XS |
| 2 | Locate Step 2 bill entry state; add `categoryAutoSet` / `userOverrode` fields | 1 | XS |
| 3 | Wire `suggestCategory` to name `onChange` handler | 1 | S |
| 4 | Add "✨ suggested" badge to category label | 1 | XS |
| 5 | Change `caps` state type to `Record<string, string>` | 2 | XS |
| 6 | Add `onFocus` select-all + `placeholder="No cap"` + `pr-8` to each cap input | 2 | XS |
| 7 | Add × clear button per field | 2 | XS |
| 8 | Update `saveCaps` to filter empty/zero entries | 2 | XS |
| 9 | Test all AC criteria for both features | — | S |
