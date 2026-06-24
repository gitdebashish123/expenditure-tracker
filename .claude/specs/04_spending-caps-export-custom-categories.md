# Spending Caps, Export, and Custom Categories — Bug & Enhancement Spec
**Date:** 2026-06-18
**Status:** Open — awaiting implementation

---

## Overview

5 observations grouped into 4 numbered issues (issues 1 and 2 are grouped because they share the same backend root cause). Two are High-priority defects (mobile download broken, and charts silently hiding spending data), one is High-priority missing feature (can't extend Spending Caps), and two are Medium enhancements (date-range export, custom categories).

No code has been modified — this is a spec-only document.

---

## Issue 1 — Spending Caps: Cannot add a new category limit + charts only show capped categories

> *Groups user observations 1 and 2. Both stem from the same backend constraint.*

**Symptom (1a):** The Spending Caps section in Settings shows a fixed grid of categories that were set up during the onboarding wizard. There is no button or UI to add a cap for any category that isn't already listed (e.g. if a user wants to start capping "Petrol" or any other currently uncapped category).

**Symptom (1b):** The Overview tab's "Spend by Category" donut and "Budget Health" section only show categories that have a cap defined in Spending Caps. Expenses logged to any uncapped category are silently invisible in both charts.

**Root cause:**

The summary endpoint at `backend/main.py:946–955` builds the `categories` array by iterating over `limits.keys()` (the user's `BudgetLimit` rows) rather than over actual spending:

```python
# main.py:946–955
categories = []
for cat, limit in limits.items():          # ← only budget-capped cats
    spent = spent_by_cat.get(cat, 0)
    categories.append({"category": cat, "spent": spent, ...})
```

So `Summary.categories` (used by `SpendDonut`) only contains budget-capped categories. The same pattern applies to the projection endpoint:

```python
# main.py:1180–1183
for cat, limit in limits.items():          # ← only budget-capped cats
    projections.append({...})
```

On the frontend, `CapsSection.tsx:77` renders only the rows returned by `GET /budgets`:

```tsx
{budgets.map(b => { ... })}                // no "add" button, no empty-state prompt
```

The `PUT /budget` backend endpoint (`main.py:971–990`) already supports upsert — creating a new `BudgetLimit` for any category string — but the frontend never calls it with a new category.

The existing preset categories were seeded for the admin user from `config.yaml:budget_limits` (Food, Travel, Groceries, Shopping, Medical, Entertainment, Gifts, Miscellaneous, Course) and for onboarded users from `OnboardingWizard.tsx:34–41` `DEFAULT_CAPS` (Food, Groceries, Travel, Shopping, Entertainment, Medical).

**Affected files:**
- `backend/main.py` — `GET /summary/{month_key}` (lines 946–955)
- `frontend/react/src/components/settings/CapsSection.tsx`
- `frontend/react/src/components/shared/SpendDonut.tsx` (data source is the symptom)
- `frontend/react/src/components/shared/BudgetHealthCard.tsx` (data source is the symptom)

**Fix approach:**

*Part A — CapsSection UI: add new cap*
- Below the existing caps grid, add an "Add category cap" row: a dropdown of known variable categories (`VAR_CATEGORIES` from `categories.ts`) minus any already in `budgets`, plus a number input for the limit amount, plus an Add button.
- On click, call `PUT /budget` with the new `{ category, limit_amount }` and re-fetch `GET /budgets` to add the row to the grid.
- The existing Save button can remain for bulk-editing existing caps; the new add row has its own immediate-save action.

*Part B — Summary categories: include uncapped spending*
Change `GET /summary/{month_key}` in `main.py` to build `categories` from all categories with actual spending, then union with budget-limited categories (so caps show even if zero-spent):

```python
# All categories actually spent in this month
all_cats = set(spent_by_cat.keys()) | set(limits.keys())
categories = []
for cat in sorted(all_cats):
    spent = spent_by_cat.get(cat, 0)
    limit = limits.get(cat, 0)
    categories.append({
        "category": cat,
        "spent": spent,
        "limit": limit,
        "pct": min((spent / limit * 100) if limit > 0 else 0, 100),
        "remaining": max(limit - spent, 0),
    })
```

`SpendDonut` already filters to `spent > 0` so uncapped/zero-spent cats won't clutter the chart. `BudgetHealthCard` (the projection endpoint) already filters to `limit > 0` so uncapped categories won't appear there — that's correct behaviour.

*Part C — QuickAdd category dropdown (secondary)*
When a user logs an expense and assigns it a custom/uncapped category, there's no feedback that it won't appear in charts. Consider adding a "(no cap set)" label in the category selector so users understand visibility.

**Acceptance criteria:**
- Settings → Spending Caps: a "Add category cap" control is visible below the grid.
- Select a category not currently in the list (e.g. "Gifts" if not already showing) → enter a limit → click Add → the new cap appears in the grid immediately, with a "Saved" confirmation.
- Log a ₹500 expense to a category with no cap (e.g. manually assign category "Books" via expense edit).
- Overview → Spend by Category donut now shows "Books ₹500" as a segment.
- Overview → Budget Health does NOT show "Books" (no limit set, so projection makes no sense) — correct.
- After adding a cap for "Books" via Spending Caps, it DOES appear in Budget Health.

**Priority:** High — users with spending outside the six wizard defaults are operating blind; their data exists but is invisible in all charts.

---

## Issue 2 — Mobile download does not trigger a file save

**Symptom:** Tapping "Download [Month]" or "Download Full History" on a mobile device (iOS Safari / Chrome on iOS) shows a spinner briefly but no file is saved or opened.

**Root cause:**

`ExportSection.tsx:32–38` uses the programmatic anchor-click download pattern:

```typescript
const { data } = await api.get(url, { responseType: "blob" });
const href = URL.createObjectURL(data);
const a    = document.createElement("a");
a.href     = href;
a.download = filename;
a.click();
URL.revokeObjectURL(href);
```

Two problems:
1. The anchor element is never appended to the DOM. Desktop Chrome works without appending; iOS Safari and Firefox Mobile require `document.body.appendChild(a)` before `a.click()` and `document.body.removeChild(a)` after.
2. The `download` attribute on `<a>` tags is **not honoured on iOS Safari** for blob URLs. iOS Safari opens blob URLs in the browser viewport (or ignores them) instead of triggering a file save. This is a long-standing WebKit limitation. The reliable iOS fallback is `window.open(href)` which opens the CSV in a new tab, from which the user can use the share sheet to "Save to Files".

The backend `Content-Disposition: attachment` header (`main.py:1252, 1300`) is correct but irrelevant once the frontend converts the response to a blob URL — the header is no longer in play.

**Affected file:** `frontend/react/src/components/settings/ExportSection.tsx`

**Fix approach:**

Replace the current `download` function with a platform-aware version:

```typescript
const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;

const { data } = await api.get(url, { responseType: "blob" });
const href = URL.createObjectURL(data);
const a    = document.createElement("a");
a.href     = href;
a.download = filename;

if (isIOS) {
  // iOS Safari: open in new tab — user can Save to Files via share sheet
  window.open(href, "_blank");
} else {
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}
URL.revokeObjectURL(href);
```

Add a short help caption on mobile below the download buttons: "On iPhone/iPad, the file opens in a new tab — tap Share → Save to Files."

**Acceptance criteria:**
- On desktop Chrome/Firefox: clicking a download button saves a `.csv` file to the Downloads folder.
- On iOS Safari (tested on iPhone): clicking a download button opens the CSV content in a new tab. User can tap the Share icon → Save to Files / AirDrop.
- On Android Chrome: file saves directly (unchanged behaviour from the DOM-append fix).
- The spinner/loading state functions correctly on all platforms.

**Priority:** High — download is completely non-functional on iOS devices which is the primary mobile platform.

---

## Issue 3 — Date range filter missing in CSV export

**Symptom:** The export section offers only two options: the currently selected month, and full history. There is no way to download a custom date range (e.g. April–June 2026, or financial year Apr 2025–Mar 2026).

**Root cause:**

`ExportSection.tsx` has two hardcoded download targets: `GET /export/csv/{selMonth}` and `GET /export/csv/all`. Neither endpoint accepts a `start`/`end` parameter. The backend `export_all_csv` at `main.py:1213–1253` fetches all expenses with no date filtering other than `user_id`.

There is no `GET /export/csv/range?from=YYYY-MM&to=YYYY-MM` endpoint anywhere in `main.py`.

**Affected files:**
- `frontend/react/src/components/settings/ExportSection.tsx`
- `backend/main.py` — new endpoint needed

**Fix approach:**

*Backend:* Add `GET /export/csv/range` accepting `from_month` and `to_month` query params (both `YYYY-MM` strings). Filter expenses by `month_key >= from_month` and `month_key <= to_month`. Reuse the CSV writer pattern from `export_all_csv`. Place the route **before** `/export/csv/{month_key}` to avoid FastAPI route-ordering issues.

```python
@app.get("/export/csv/range")
def export_range_csv(from_month: str, to_month: str, ...):
    expenses = session.exec(
        select(Expense)
        .where(
            Expense.user_id == current_user.id,
            Expense.month_key >= from_month,
            Expense.month_key <= to_month,
        )
        .order_by(Expense.date)
    ).all()
    ...
```

*Frontend:* Below the two existing download buttons, add a collapsible "Custom range" section with two `<input type="month">` fields (From / To) defaulting to 3 months ago → current month, and a third download button that calls `GET /export/csv/range?from_month=...&to_month=...`.

**Acceptance criteria:**
- Settings → My Data shows a "Custom range" toggle/section.
- User sets From = "2026-04", To = "2026-06" → clicks Download Range → CSV contains only April–June 2026 expenses.
- `from_month > to_month` → disabled button or validation error shown (no API call made).
- The two original buttons (current month, full history) continue to work unchanged.
- New route `/export/csv/range` is registered **before** `/export/csv/{month_key}` in `main.py`.

**Priority:** Medium — workaround exists (download full history and filter in Excel), but the missing feature is a gap for any financial year review workflow.

---

## Issue 4 — Cannot add custom expense categories

**Symptom:** All expense categories (Food, Travel, Groceries, etc.) are fixed. There is no UI anywhere in the app to define a new category like "Petrol", "Books", or "Baby". If a user wants expenses grouped under a custom label, they must piggyback on "Miscellaneous" or use an existing category that doesn't semantically fit.

**Root cause:**

Categories are hardcoded in three separate places with no dynamic extension mechanism:

1. **Frontend constant** — `frontend/react/src/utils/categories.ts`: `CATEGORY_ICONS`, `VAR_CATEGORIES`, `FIXED_CATEGORIES` are static arrays. Any category not in `CATEGORY_ICONS` falls back to the `"📦"` generic icon.

2. **AI parser prompt** — `backend/ai_parser.py:31–33`:
   ```python
   "2. Category must be one of: Food, Travel, Groceries, Shopping, "
   "Medical, Entertainment, Gifts, Course, Miscellaneous"
   ```
   The list is hardcoded in the prompt string. Claude will map any custom vendor to one of these nine fixed values, ignoring user-defined categories.

3. **No backend storage for user-defined categories** — `backend/models.py` has no `UserCategory` table. `PUT /budget` accepts any `category` string and stores it, so the backend is category-agnostic, but no endpoint exists to CRUD user-defined categories with metadata (icon, display name).

**Affected files:**
- `frontend/react/src/utils/categories.ts`
- `backend/ai_parser.py`
- `backend/models.py` (new table needed)
- `backend/main.py` (new endpoints needed)
- `frontend/react/src/components/settings/` (new UI section needed)
- `frontend/react/src/components/tabs/QuickAddTab.tsx` (category selector)

**Fix approach:**

This is a multi-layer feature. Recommended phased approach:

*Phase 1 — UI-only custom categories (no AI support):*
- Add a `UserCategory` table: `(id, user_id, name, icon_emoji, is_variable, sort_order)`.
- New endpoints: `GET /categories`, `POST /categories`, `DELETE /categories/{id}`.
- Settings: new "Custom Categories" section — text input for name, emoji picker (or text input for emoji), toggle for variable vs fixed type.
- `QuickAddTab` category dropdown and `HistoryTab` edit modal pull from `GET /categories` (merged with the hardcoded defaults) instead of the static `VAR_CATEGORIES` array.
- `CATEGORY_ICONS` lookup falls back to the user's emoji if the name isn't in the static map.

*Phase 2 — AI parser support (requires Phase 1):*
- `parse_expense_input()` in `ai_parser.py` fetches the user's full category list (defaults + customs) at call time and injects it into the Claude prompt dynamically, replacing the hardcoded list.
- This requires passing `user_id` into `parse_expense_input()` and querying the DB (or receiving the list as a parameter from the calling endpoint in `main.py`).

**Acceptance criteria (Phase 1):**
- Settings → Custom Categories: user can add "Petrol" with emoji "⛽" as a variable category.
- After adding, "Petrol" appears in the QuickAdd category dropdown and in expense edit modals.
- Spend by Category donut shows "Petrol" entries.
- User can add a Spending Cap for "Petrol" via the CapsSection (see Issue 1 Part A fix).
- Deleting a custom category shows a warning if any expenses are tagged with it; user confirms before deletion (expenses retain the category string — no orphaned data, just no cap/icon lookup).

**Acceptance criteria (Phase 2):**
- User types "HP petrol 800" → AI categorises as "Petrol" (custom category), not "Miscellaneous".

**Priority:** Medium — workaround is "Miscellaneous", which many users will tolerate. Phase 1 is a meaningful improvement without AI complexity; Phase 2 can follow in a separate sprint.

---

## Implementation Order

| # | Issue | Priority | Effort | Files |
|---|---|---|---|---|
| 2 | Mobile download — iOS fix | High | 1h | `ExportSection.tsx` |
| 1 | Spending Caps — add new cap UI | High | 2h | `CapsSection.tsx`, `main.py` |
| 1 | Summary categories — include uncapped spending | High | 30 min | `main.py` |
| 3 | Date range CSV export | Medium | 3h | `ExportSection.tsx`, `main.py` (new endpoint) |
| 4 | Custom categories — Phase 1 (UI + DB) | Medium | 1–2 days | `models.py`, `main.py`, `categories.ts`, `QuickAddTab`, new Settings section |
| 4 | Custom categories — Phase 2 (AI parser) | Low | 3h | `ai_parser.py`, `main.py` |

---

## Files NOT modified by this spec

- `frontend/app.py` — legacy Streamlit frontend, untouched throughout
- `frontend/react/src/components/shared/BudgetHealthCard.tsx` — no change needed; it correctly filters to budget-capped categories only via the projection endpoint
- `frontend/react/src/components/shared/SpendDonut.tsx` — no change needed; it already filters `c.spent > 0`; fix is in the data source (`main.py` summary endpoint)
- `backend/auth.py`, `backend/budget_rules.py`, `backend/models.py` (Issues 1–3 only)

---

*Spec created: 2026-06-18*
*Observed on: Wallet Mantra React frontend (post sprint 7 migration)*
