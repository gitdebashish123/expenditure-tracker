# Spec 24 — System-Level: Shared Currency Input + "Commitments" Naming Rule
**Date**: 2026-06-29
**Status**: ✅ Implemented
**Branch**: `feature/sprint06261-ui-enhancement` *(confirm active branch before starting)*
**Follows**: `23_fixed-tab-followup-fixes.md`
**Source**: cross-cutting issues surfaced in the Fixed-tab (Spec 22/23) and Settings-tab reviews, June 29 2026.

---

## Context

Two problems recur across multiple tabs. Fixing them per-screen guarantees drift, so
this spec fixes both **once, at the system level**, and other specs depend on it.

1. **Currency steppers** — currency is entered through `<input type="number" step=…>`,
   which renders spinner arrows and invites step-by-rupee interaction. Wrong control for
   money. Found in at least 7 places (below).
2. **"Bills" mislabel** — the recurring-commitments world includes EMIs, rent, transfers,
   SIPs/savings and subscriptions, not just bills. The UI calls them "bills" (including a
   "1 bills" grammar bug). Spec 23 already moved the Fixed deck to "Fixed …/items"; this
   generalizes the rule.

This spec is **frontend-only** except where noted; it changes the **input control** and
**copy**, not business logic.

---

## Item 1 — Shared `CurrencyInput` component

**Confirmed stepper locations** (`type="number"`):
| File | Field | step |
|---|---|---|
| `settings/CapsSection.tsx` | cap edit; "₹ limit" add-cap | 1 |
| `settings/BillsSection.tsx` | `TemplateEditRow` amount; add-bill amount | 1 |
| `settings/IncomeSection.tsx` | income amount | 1 |
| `settings/ShortcutsSection.tsx` | `ShortcutEditRow` amount; add-shortcut amount | 50 |
| `tabs/PoolCard.tsx` | pool payment amount (Fixed tab) | — |

**Audit also** (not yet read — confirm during impl): `tabs/QuickAddTab.tsx` amount, the
onboarding wizard amount fields (Specs 14–15). **Exclude** genuinely non-currency numeric
controls (e.g. the due-day `<select>` in `BillsSection`, and `type="date"` pickers in
`ExportSection`).

**Fix:** add `components/shared/CurrencyInput.tsx` — a controlled numeric text field:
- `type="text"` + `inputMode="numeric"` (digit-only; no spinner on any platform)
- sanitize to digits on change; emit a `number` via `onChange(value: number)`
- optional `₹` prefix slot; same Tailwind look as the inputs it replaces
- props mirror today's usage (`value`, `onChange`, `placeholder`, `min`, `className`)

Replace every currency `type="number"` with `<CurrencyInput>`.

**Acceptance:** no spinner/step arrows on any currency field; mobile shows a numeric
keypad; values still validate (≥ 0); existing save logic unchanged.

---

## Item 2 — "Commitments" naming rule

**Rule:**
- **Umbrella / section term** → "commitments" (not "bills"). E.g. `BillsSection` title
  "📋 Monthly Bills" → "📋 Monthly commitments".
- **Count noun** → "items", correctly pluralized: **"1 item" / "3 items"** (fixes the
  "1 bills" bug).
- Keep the literal word "bill" **only** where it's truly a bill — e.g. the "Electric
  Bills" pool name, the variable-bill explanation copy ("like electric bill").
- Align with Spec 23's Fixed deck ("Fixed total / paid / left", "items").

**Confirmed copy to change** (`settings/BillsSection.tsx`):
- `h2` "📋 Monthly Bills" → "📋 Monthly commitments"
- group label `({items.length} bills)` → `({items.length} item{items.length===1?'':'s'})`
- "Same amount every month" / "Amount changes each month" sub-labels — keep (accurate)
- add-commitment accordion: "Add a new bill" → "Add a commitment"; submit "＋ Add Bill"
  → "＋ Add commitment"; placeholder "e.g. Rent, Car Loan, Netflix" stays (good examples)
- pool row caption "Add payments in Fixed tab" — keep

**Also audit** for "bill(s)" copy: Fixed tab strings, onboarding wizard, any tooltips.
**Leave** category names and the "Electric Bills" template name untouched.

**Acceptance:** no "1 bills" anywhere; SIP/EMI/transfer items are not labelled "bills";
vocabulary consistent across Fixed + Settings.

---

## Files
- New: `components/shared/CurrencyInput.tsx`
- Edits: `settings/CapsSection.tsx`, `settings/BillsSection.tsx`, `settings/IncomeSection.tsx`,
  `settings/ShortcutsSection.tsx`, `tabs/PoolCard.tsx`, plus audit hits in
  `tabs/QuickAddTab.tsx` and the onboarding wizard.

## Out of scope
Layout/visual redesign (that's Spec 25); any backend change.

## Dependency note
Spec 25 (Settings redesign) consumes `CurrencyInput` and assumes the naming rule is in
place — land Spec 24 first.
