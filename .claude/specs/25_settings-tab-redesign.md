# Spec 25 — Settings Tab Redesign: Caps Cards, Over-Budget Bell, Income & Commitment Context, Export Polish
**Date**: 2026-06-29
**Status**: ✅ COMPLETED 2026-06-29
**Branch**: `feature/sprint06261-ui-enhancement` *(confirm active branch before starting)*
**Follows**: `24_currency-input-and-naming-system.md`
**Source**: Settings re-review (iPhone 15 Safari + desktop) + external review cross-check + approved interactive mockups (v1 polished, v2 caps-grid/bell/shortcuts), June 29 2026.

---

## Context

The Settings tab works but reads as assembled: bare number inputs for caps, no progress
feedback, a "bills" mislabel, an inconsistent save model, and a few correctness traps.
This spec applies the agreed mockup, **mobile-first**, and deliberately **drops** the
external review's desktop-dashboard framing and named "Tara" persona.

**Decisions locked (from mockup review):**
- Spending caps → **2-per-row cards with inline progress bars** (not bare inputs).
- Over-budget warning → **header notification bell** (not an inline banner).
- Add-cap affordance → **"+ Set cap"** button (top-right).
- Saved shortcuts → **icon tiles** (not inline edit rows by default).
- Caps **auto-save** (no Save button).

**Depends on Spec 24:** uses `CurrencyInput` for all amount fields and assumes the
"commitments / items" naming rule is applied.

**Out of scope / deferred:** named AI persona; desktop left-nav + right summary rail +
Quick Actions (the external mockup's layout); IA reorg into Setup/Account/Data; profile-
menu expansion; richer variable-bill stats (last/avg/high/low); AI suggestions.

---

## Item 1 — Spending caps → progress-bar cards (`settings/CapsSection.tsx`)

**Current:** `grid grid-cols-2` of cells = `label + "{spent} spent"` + a bare
`type="number"` input; one explicit **"Save Spending Caps"** submit; a separate
"➕ Add a category cap" form (select + "₹ limit" + "Add") shown only when categories
remain. Colour thresholds already exist: `pct >= 100 → #ef4444`, `>= 80 → #f59e0b`,
else `#34d399`.

**New (keep the 2-col grid, change the cell to a card):** each cap card shows
- icon + category name + **`%`** (in the threshold colour) + a non-colour state cue
  ("Over" / "Near" / "On track") for accessibility;
- **`₹{spent} / ₹{cap}`** (currently only "spent" is shown — add the cap side);
- a **progress bar**, `width = min(pct, 100)%`, filled in the threshold colour.
- Reuse the existing `pct`/`colour` logic verbatim.

**Editing:** replace the always-visible bare input with edit via **`CurrencyInput`**
(Spec 24) — inline on the card or on tap (implementer's choice; keep it one tap to edit).

**Auto-save:** remove the "Save Spending Caps" button; `PUT /budget` per cap on change
(debounced ~600ms) with a subtle "Saved" microcopy/check. Preserve the existing
add-cap PUT + reload flow.

**"+ Set cap":** move the add-cap affordance to a **top-right "+ Set cap" button**
(renames "Add a category cap" / "Add"); it reveals the category `<select>` +
`CurrencyInput` limit. Keep the "no categories left" guard.

**"View all caps & history →" link:** include **only if** a caps-history view/route
exists; otherwise omit or stub for a future spec (verify during impl).

**Mobile note:** 2-per-row is tight at ≤360px (e.g. "₹7,815 / ₹5,000" + %). If it
pinches on the narrowest target, fall back to a single column with the same in-card bar.

---

## Item 2 — Over-budget warning → header notification bell (`layout/Header.tsx` + new)

**Goal:** the over-budget alert lives in a header **bell**, not an inline banner (frees
the caps section, and is a pattern that can grow).

- Add a bell button to `Header.tsx` right-controls (where the removed eye sat — Spec 23),
  with a **badge** when alerts exist.
- Bell opens a small dropdown listing alerts; first/only source = **"N categories over
  budget this month"** (compute from caps vs `/summary` spend; reuse the caps pct logic).
- Dropdown: opaque panel + closes on outside click (same care as Item 6's scrim).
- **No inline over-budget banner** in the caps section.

**Note:** this is a **new global element** and the seed of a broader notifications
pattern (could later aggregate due reminders, etc.). Scope here = the bell shell + the
over-budget alert only. If a shared place to compute "over budget" doesn't exist, derive
it where the bell renders.

---

## Item 3 — Income context (`settings/IncomeSection.tsx`)

A **Total Income** row already exists. Add:
- **sources count** (derivable: `entries.length`) and a summary treatment per the mockup
  (total + "{n} sources").

**Backend-dependent (flag, don't assume):** the mockup also shows a **"Updated on …"**
timestamp and **"Auto recurring" / "Manual" badges**. `IncomeRow` currently has only
`{ id, source, amount, note }` — no timestamp, no recurring flag. These need backend
fields (e.g. `updated_at`, `is_recurring`). **Ship the derivable parts now; gate badges
+ last-updated behind a backend change** (split to a follow-up if backend isn't in scope).

---

## Item 4 — Commitment group context (`settings/BillsSection.tsx`)

- Show a **₹/month total per collapsed group** alongside the item count
  (`(3 items) … ₹4,785 / month`) — derivable client-side from the group's templates.
- Add a **"Fixed total ₹{sum}/month"** anchor above the fixed groups.
- Variable group: show **avg/mo** if available (else omit).
- Naming ("commitments" / "items") comes from Spec 24 — not repeated here.

---

## Item 5 — Export polish (`settings/ExportSection.tsx`)

- **Rename** "📥 My Data" → "📥 Export data".
- **Contrast:** the two preset buttons use `color: var(--text-sub)` on `bg-dark-card2`,
  so they read as **disabled**. Raise to a clearly-enabled treatment (these are primary
  actions).
- **Custom-range default trap:** `fromDate` and `toDate` both default to **today**
  (`new Date().toISOString().slice(0,10)`), so expanding the range and downloading yields
  a single day. Default `fromDate` to the **selected month's start** and `toDate` to
  today (or month end). 
- **Date-format split:** inputs are `type="date"` (render DD/MM/YYYY by locale) while the
  button label prints ISO `{fromDate} → {toDate}`. Pick one display format for the label.
- Progressive disclosure (showRange toggle) already exists — keep.

---

## Item 6 — Saved shortcuts → icon tiles (`settings/ShortcutsSection.tsx`)

**Current:** inline edit rows (name/category/amount per row) + a 3-col add form.
**New (per mockup):** display shortcuts as **icon tiles** (category emoji + name +
`₹amount`) in a horizontally-scrollable row, with a dashed **"+"** add tile and a
**"View all shortcuts →"** link; "+ Add shortcut" top-right. Editing moves behind a tap
on a tile (or "view all"). Amount fields use `CurrencyInput` (Spec 24).

---

## Item 7 — Profile dropdown bleed (`layout/ProfileDropdown.tsx`)

The dropdown is an absolute panel (`bg-dark-card`) with **no scrim**, so page content
shows through behind it (visible in the review screenshots). Make the panel fully opaque
and/or add a light scrim. It already closes on outside click — keep.

---

## Item 8 — Destructive deletes + tap targets (`IncomeSection`, `BillsSection`)

- Income/commitment/pool deletes are one-tap with no confirmation — add a confirm step
  (inline "Remove?" or a small confirm).
- Bump trash/save/chevron tap targets toward ~44px (currently `size={12–14}` icons with
  little padding).

---

## Guardrail
No change to the income/budget/template **save semantics** beyond Item 1's auto-save and
Item 8's confirmation. Export download mechanics (iOS blob handling) untouched. Spec 24's
`CurrencyInput` + naming are prerequisites.

---

## Files
`settings/CapsSection.tsx`, `layout/Header.tsx` (+ notification bell piece),
`settings/IncomeSection.tsx`, `settings/BillsSection.tsx`, `settings/ExportSection.tsx`,
`settings/ShortcutsSection.tsx`, `layout/ProfileDropdown.tsx`.

## Verify during implementation
1. Caps-history view/route exists? (gates the "View all caps & history" link)
2. Income backend fields for last-updated + recurring badge (Item 3) — present or new?
3. Variable-bill avg availability (Item 4).

## Open decisions — none blocking
All layout/pattern decisions are locked from the mockup review. The only conditional
items are the three "verify" points above, which scope down gracefully if unavailable.
