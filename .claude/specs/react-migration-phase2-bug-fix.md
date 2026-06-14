# Spec: React Migration Phase 2 — Bug Fixes & UX Observations

**Date**: 2026-06-02  
**Branch**: feature/sprint7-react-migration-phase3  
**Status**: Ready for implementation

---

## 1. Forgot Password Option Missing on Login Page

**Observation**: The login page has no "Forgot password?" link or flow.

**Acceptance Criteria**:
- A "Forgot password?" link is visible below the login form.
- Clicking it shows a UI that informs the user to contact the admin or provides a reset flow.
- For MVP: display a message such as "Please contact your administrator to reset your password." (full email-based reset is a future feature).

**Files likely affected**: `frontend/react/src/pages/LoginPage.tsx`

---

## 2. Dividend / Bonus Should Add to Main Income

**Observation**: Dividend and bonus income entries are not being reflected in the main (net) income displayed on the dashboard.

**Acceptance Criteria**:
- Any expense entries categorised as `Income` (or sub-types like `Dividend`, `Bonus`) must be **added** to the net monthly income figure shown on the dashboard.
- The balance/remaining calculation should use `salary + additional_income - expenses` rather than `salary - expenses`.
- The overview and budget summary sections must reflect the updated income total.

**Files likely affected**:
- `backend/budget_rules.py` — `get_balance_summary()`
- `frontend/react/src/` — dashboard overview components

---

## 3. Pie Chart Tooltip Text Invisible (Black on Dark Background)

**Observation**: When hovering over the "Spend by Categories" pie chart, the tooltip renders with black text on a dark/black background, making the amount unreadable.

**Acceptance Criteria**:
- Tooltip text colour must have sufficient contrast against its background in both light and dark themes.
- Amount and category name must be clearly readable on hover.
- Fix should use the theme's tooltip token or force white text with a semi-transparent dark background.

**Files likely affected**:
- `frontend/react/src/` — the component rendering the spend-by-category pie chart (likely uses Recharts or Chart.js tooltip configuration)

---

## 4. Monthly Breakdown Section — Revised Field Set

**Observation**: The current monthly breakdown section does not show the right breakdown fields.

**Required fields** (in order):
1. **Fixed Paid** — fixed expenses already marked as paid this month
2. **Fixed Remaining** — fixed expenses not yet paid this month
3. **Variable Already Paid** — variable/discretionary spending so far this month
4. **Total Remaining** — what is left of the total budget (income − fixed total − variable paid)

**Acceptance Criteria**:
- Remove any fields not in the above list from this section.
- Each field displays a currency-formatted ₹ amount.
- Labels match exactly the names above.

**Files likely affected**:
- `backend/budget_rules.py` — ensure API returns these four values
- `frontend/react/src/` — monthly breakdown component

---

## 5. Top Spends This Month — Limit to Top 5

**Observation**: The "Top Spends This Month" section currently shows more than 5 entries.

**Acceptance Criteria**:
- Only the top 5 highest-value expense entries for the current month are shown.
- If there are fewer than 5 entries, show all available.
- No "show more" / pagination needed at this stage.

**Files likely affected**:
- `frontend/react/src/` — top spends component (query or slice should limit to 5)
- Possibly `backend/main.py` — if the limit is applied server-side via a query parameter

---

## 6. Fixed Tab — Remove "Auto Seeded Fixed Expense" Subtitle from List Items

**Observation**: Every item in the Fixed Expenses tab shows an "auto seeded fixed expense" sub-label beneath the name (e.g. "Rent" followed by lighter text "auto seeded fixed expense"). This is noise.

**Acceptance Criteria**:
- The secondary label "auto seeded fixed expense" must not be rendered for any list item.
- The item should display only the expense name (e.g. "Rent") and its amount/status.
- If a description/note field genuinely contains user-entered text, it may still be shown; only the auto-seeded marker text should be suppressed.

**Files likely affected**:
- `frontend/react/src/` — fixed expenses list/card component

---

## 7. Today / History Tab — Entries in Descending Order (Latest First)

**Observation**: Expense entries in the Today and History tabs are displayed in ascending chronological order; the most recent entry appears last.

**Acceptance Criteria**:
- Entries must be sorted in **descending** order by date/time — most recent at the top.
- Applies to both the "Today" view and the "History" view.
- The sort should be consistent regardless of the data source (client-side sort or server-side `ORDER BY`).

**Files likely affected**:
- `backend/main.py` — expense list endpoint(s): change `ORDER BY created_at ASC` → `ORDER BY created_at DESC`
- `frontend/react/src/` — if sorting is also applied client-side, reverse the sort direction

---

## 8. Cross-Tab Summary Cards — Persistent Financial Snapshot

**Observation**: The Income, Fixed Paid, Fixed Remaining, and Balance Remaining cards are only accessible under the Overview tab. Users on the Today or Fixed tabs must navigate away just to check their financial position.

**Desired behaviour**: These four summary figures should be visible from the Today and Fixed tabs too, so the financial snapshot is always one glance away.

**Agreed approach**: Responsive — two different presentations based on screen width:

### Mobile (< 768 px) — Persistent Summary Strip
- A compact horizontal strip pinned directly below the tab bar, always visible regardless of active tab.
- Displays four stat chips inline: **Income · Fixed Paid · Fixed Remaining · Balance Left**
- Each chip: small label above, bold ₹ amount below.
- On mount / tab switch, amounts animate with a **count-up** effect (0 → final value, ~600 ms, ease-out) to give a lively feel without adding tap overhead.
- Strip does not scroll with content — it stays fixed under the tab bar.

### Desktop (≥ 768 px) — Flip Cards
- Four cards arranged in a row, each showing the label on the **front face**.
- On hover, the card flips (CSS 3D transform, ~300 ms) to reveal the ₹ amount on the **back face**.
- Cards are shown in the Today and Fixed tabs (in addition to the existing Overview layout).
- A subtle shadow lift on hover signals interactivity.

### Shared Acceptance Criteria
- The four metrics are: **Income** (salary + additional income), **Fixed Paid**, **Fixed Remaining**, **Balance Left** (income − fixed total − variable paid).
- Data is fetched from the same balance summary API endpoint already used by the Overview tab — no new endpoint needed.
- Values update in real time after a new expense is added (re-fetch or state propagation).
- Both presentations must respect the active colour theme (light / dark).

**Files likely affected**:
- `frontend/react/src/components/` — new `SummaryStrip.tsx` (mobile) and `SummaryFlipCard.tsx` (desktop)
- `frontend/react/src/pages/DashboardPage.tsx` — render summary component above tab content for Today and Fixed tabs
- Tailwind responsive utilities (`md:hidden`, `hidden md:flex`) to switch between the two presentations

---

## Implementation Notes

- All fixes are independent and can be done in parallel or sequentially.
- Items 3, 5, 6, 7 are frontend-only changes.
- Items 2 and 4 require backend + frontend coordination.
- Item 1 is frontend-only for the MVP stub.
- Item 8 is frontend-only; reuses the existing balance summary API.
- Prioritise items 7 (sort order) and 6 (noise removal) as they affect every session.
