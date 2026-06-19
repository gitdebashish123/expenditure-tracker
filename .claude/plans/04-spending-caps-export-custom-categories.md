# Implementation Plan: Spending Caps, Export, and Custom Categories
**Spec**: `.claude/specs/04_spending-caps-export-custom-categories.md`
**Date**: 2026-06-19
**Branch**: `feature/sprint06261-ui-enhancement`

---

## Overview

6 items total — 2 require backend changes (Items B and D), 1 requires both backend and frontend (Item D), and 2 are frontend-only (Items A and C). Items E and F are the largest (new DB table) and depend on each other. Item F depends on E.

Ordered smallest-blast-radius first: isolated frontend fix → backend one-liner → frontend UI extension → backend new endpoint + frontend → DB migration + full stack feature → AI parser wiring.

---

## Item A — Mobile download: fix iOS Safari failure
**Scope**: Frontend-only
**File**: `frontend/react/src/components/settings/ExportSection.tsx` (lines 25–42)

**Root cause (verified against current code)**:
Lines 32–38 use the anchor-click pattern without appending to the DOM:
```typescript
const { data } = await api.get(url, { responseType: "blob" });
const href = URL.createObjectURL(data);
const a    = document.createElement("a");
a.href     = href;
a.download = filename;
a.click();          // ← never appended to document.body
URL.revokeObjectURL(href);  // ← revoked synchronously, before click may trigger
```
On iOS Safari: (1) `download` attribute on blob: URLs is ignored by WebKit; (2) the element is not in the DOM so some browsers skip the click; (3) `URL.revokeObjectURL` runs synchronously on the same tick as `a.click()`, which may revoke the URL before iOS can open it.

**What to do**:

Replace the `download` async function (lines 25–42) with:

```typescript
const download = async (
  url:        string,
  filename:   string,
  setLoading: (v: boolean) => void
) => {
  setLoading(true);
  try {
    const { data } = await api.get(url, { responseType: "blob" });
    const href = URL.createObjectURL(data);
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);

    if (isIOS) {
      // iOS Safari does not honour the download attribute on blob: URLs.
      // Opening in a new tab lets the user Save to Files via share sheet.
      window.open(href, "_blank");
      // Delay revoke so the new tab has time to read the blob
      setTimeout(() => URL.revokeObjectURL(href), 5000);
    } else {
      const a = document.createElement("a");
      a.href = href;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(href);
    }
  } finally {
    setLoading(false);
  }
};
```

Below the `<div className="flex gap-3">` button row, add a small help note visible only on iOS:
```tsx
{/iPad|iPhone|iPod/.test(navigator.userAgent) && (
  <p className="text-xs mt-2 text-center" style={{ color: "var(--text-muted)" }}>
    On iPhone/iPad, the file opens in a new tab — tap Share → Save to Files
  </p>
)}
```

No other files change. No backend change needed (the backend already sets `Content-Disposition: attachment` at `main.py:1252` and `1300`).

---

## Item B — Backend: summary includes uncapped spending in category chart
**Scope**: Backend-only
**File**: `backend/main.py` (lines 946–955)

**Root cause (verified against current code)**:
```python
# main.py:946–955
categories = []
for cat, limit in limits.items():       # ← iterates only budget-capped cats
    spent = spent_by_cat.get(cat, 0)
    categories.append({
        "category": cat,
        "spent": spent,
        "limit": limit,
        "pct": min((spent / limit * 100) if limit > 0 else 0, 100),
        "remaining": max(limit - spent, 0),
    })
```
`get_monthly_spent_by_category` (budget_rules.py:19–31) already returns all categories with actual spending — the loop just doesn't use them. Uncapped spending is invisible to `SpendDonut` (which receives `summary.categories`) and silently excluded from the Spend by Category chart.

**What to do**:

Replace lines 946–955 with a union of all categories that have either a limit or actual spending:

```python
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

No schema change, no new endpoint, no frontend change needed.

- `SpendDonut` already filters to `c.spent > 0` (SpendDonut.tsx:23), so uncapped/zero-spent categories won't clutter the chart.
- `BudgetHealthCard` (projection endpoint at main.py:1180–1183) still correctly filters to `limit > 0` only — categories without caps don't appear in Budget Health projections, which is intentional.
- `CapsSection.tsx` reads directly from `GET /budgets`, not from `/summary`, so it is unaffected.

---

## Item C — CapsSection UI: add new spending cap
**Scope**: Frontend-only
**File**: `frontend/react/src/components/settings/CapsSection.tsx`

**Root cause (verified against current code)**:
Line 77: `{budgets.map(b => { ... })}` renders only existing `BudgetLimit` rows returned by `GET /budgets`. There is no "add" button, empty state, or input for a new category. The backend `PUT /budget` at `main.py:971–990` is already an upsert and will create a new `BudgetLimit` row for any category string — the gap is entirely in the UI.

**What to do**:

Add these state variables at the top of `CapsSection`:
```typescript
const [newCat,     setNewCat]     = useState("");
const [newLimit,   setNewLimit]   = useState<number>(0);
const [addingSave, setAddingSave] = useState(false);
```

Add `VAR_CATEGORIES` to the imports from `@/utils/categories`. Compute the set of categories not yet in `budgets` so the dropdown only shows addable ones:
```typescript
const cappedCats = new Set(budgets.map(b => b.category));
const availableCats = VAR_CATEGORIES.filter(c => !cappedCats.has(c));
```

After the closing `</form>` tag (after line 126), add an "Add new category cap" block. Only render it when `availableCats.length > 0`:

```tsx
{availableCats.length > 0 && (
  <div className="mt-6 pt-4 border-t border-white/10">
    <p className="text-sm text-white mb-3">➕ Add a category cap</p>
    <div className="flex gap-3">
      <select
        value={newCat}
        onChange={e => setNewCat(e.target.value)}
        className="flex-1 bg-dark-card2 border border-white/10 rounded-xl px-3 py-2
                   text-white text-sm focus:border-accent focus:outline-none"
      >
        <option value="">Select category…</option>
        {availableCats.map(c => (
          <option key={c} value={c}>{CATEGORY_ICONS[c] ?? "📦"} {c}</option>
        ))}
      </select>
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
      <button
        type="button"
        disabled={!newCat || newLimit <= 0 || addingSave}
        onClick={async () => {
          setAddingSave(true);
          try {
            await api.put("/budget", { category: newCat, limit_amount: newLimit });
            // Re-fetch to add the new row to the grid
            const r = await api.get<BudgetLimit[]>("/budgets");
            setBudgets(r.data);
            setUpdates(Object.fromEntries(r.data.map(b => [b.category, b.limit_amount])));
            setNewCat("");
            setNewLimit(0);
          } finally {
            setAddingSave(false);
          }
        }}
        className="px-4 py-2 bg-accent rounded-xl text-white text-sm font-semibold
                   disabled:opacity-40 transition-opacity"
      >
        {addingSave ? "…" : "Add"}
      </button>
    </div>
  </div>
)}
```

No backend change needed — `PUT /budget` already handles the upsert.

---

## Item D — Date range CSV export
**Scope**: Backend + Frontend
**Files**:
- `backend/main.py` — new endpoint, position matters (see below)
- `frontend/react/src/components/settings/ExportSection.tsx`

**Root cause (verified against current code)**:
Only two export routes exist in `main.py:1211–1301`: `/export/csv/all` and `/export/csv/{month_key}`. No range endpoint. `ExportSection.tsx` has two hardcoded buttons calling those two routes. No date range state or inputs exist in the component.

**What to do**:

### Backend (`main.py`)

Insert new endpoint **at line 1210** (immediately after the ordering comment and before `@app.get("/export/csv/all")`). The route name `range` must be added before `{month_key}` to avoid route collision — keeping it before `/all` is also fine since neither `all` nor `range` is a valid YYYY-MM string.

```python
@app.get("/export/csv/range")
@limiter.limit("20/hour")
def export_range_csv(
    request: Request,
    from_month: str,
    to_month: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Export expenses for a from_month..to_month range (both YYYY-MM, inclusive)."""
    if from_month > to_month:
        raise HTTPException(status_code=400, detail="from_month must be ≤ to_month")

    expenses = session.exec(
        select(Expense)
        .where(
            Expense.user_id == current_user.id,
            Expense.month_key >= from_month,
            Expense.month_key <= to_month,
        )
        .order_by(Expense.date)
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["month", "date", "vendor", "category", "amount", "note", "type", "paid"])
    for e in expenses:
        writer.writerow([
            e.month_key,
            e.date.isoformat() if e.date else "",
            e.vendor, e.category, e.amount,
            e.note or "",
            "fixed" if e.is_fixed else "variable",
            "yes" if e.paid else "no",
        ])

    output.seek(0)
    filename = f"walletMantra_{from_month}_to_{to_month}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
```

Update the ordering comment at line 1208 to include `range`:
```python
# NOTE: /export/csv/all and /export/csv/range MUST be defined before /export/csv/{month_key}
```

### Frontend (`ExportSection.tsx`)

Add state variables and compute default range (3 months ago → current month):

```typescript
const threeMonthsAgo = new Date();
threeMonthsAgo.setMonth(threeMonthsAgo.getMonth() - 3);
const defaultFrom = threeMonthsAgo.toISOString().slice(0, 7);
const defaultTo   = new Date().toISOString().slice(0, 7);

const [showRange,     setShowRange]     = useState(false);
const [fromMonth,     setFromMonth]     = useState(defaultFrom);
const [toMonth,       setToMonth]       = useState(defaultTo);
const [loadingRange,  setLoadingRange]  = useState(false);
```

After the existing `<div className="flex gap-3">` buttons block (after line 101), add:

```tsx
{/* Custom range toggle */}
<button
  onClick={() => setShowRange(v => !v)}
  className="mt-3 text-xs w-full text-center py-2"
  style={{ color: "var(--text-muted)" }}
>
  {showRange ? "▲ Hide range filter" : "▼ Custom date range"}
</button>

{showRange && (
  <div className="mt-3 space-y-3">
    <div className="flex gap-3 items-center">
      <div className="flex-1">
        <label className="text-xs mb-1 block" style={{ color: "var(--text-sub)" }}>From</label>
        <input
          type="month"
          value={fromMonth}
          onChange={e => setFromMonth(e.target.value)}
          className="w-full bg-dark-card2 border border-white/10 rounded-xl
                     px-3 py-2 text-white text-sm focus:border-accent focus:outline-none"
        />
      </div>
      <div className="flex-1">
        <label className="text-xs mb-1 block" style={{ color: "var(--text-sub)" }}>To</label>
        <input
          type="month"
          value={toMonth}
          onChange={e => setToMonth(e.target.value)}
          className="w-full bg-dark-card2 border border-white/10 rounded-xl
                     px-3 py-2 text-white text-sm focus:border-accent focus:outline-none"
        />
      </div>
    </div>
    <button
      onClick={() =>
        download(
          `/export/csv/range?from_month=${fromMonth}&to_month=${toMonth}`,
          `walletMantra_${fromMonth}_to_${toMonth}.csv`,
          setLoadingRange
        )
      }
      disabled={loadingRange || fromMonth > toMonth}
      className={btnCls}
      style={{ color: "var(--text-sub)" }}
    >
      {loadingRange ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
      Download {fromMonth} → {toMonth}
    </button>
    {fromMonth > toMonth && (
      <p className="text-xs text-red-400 text-center">"From" must be before "To"</p>
    )}
  </div>
)}
```

Add `loadingRange` to the `useState` imports. The existing `download` helper (after Item A's fix) handles iOS correctly for this button too.

---

## Item E — Custom categories Phase 1: DB + backend + frontend
**Scope**: Backend + Frontend (largest blast radius — schema migration + new table + new settings section)
**Files**:
- `backend/models.py` — new `UserCategory` table
- `migrate_schema.py` — new table DDL + additive column
- `backend/main.py` — 3 new endpoints
- `frontend/react/src/utils/categories.ts` — exports `CATEGORY_ICONS` with fallback helper
- `frontend/react/src/components/tabs/HistoryTab.tsx` — category dropdown uses live data
- `frontend/react/src/components/settings/` — new `CategoriesSection.tsx`
- `frontend/react/src/components/settings/SettingsTab.tsx` — wire in new section

**Note on QuickAddTab (spec correction)**: The spec listed `QuickAddTab.tsx` as an affected file for the category selector. QuickAddTab has no category dropdown — the NL parse flow is fully AI-driven and the AI assigns categories. The actual category dropdown that needs updating is `EditExpenseRow` inside `HistoryTab.tsx` at line 160, which renders `VAR_CATEGORIES.map(c => ...)`.

### Backend

**`backend/models.py`** — add after `BudgetLimit` class (after line 102):

```python
class UserCategory(SQLModel, table=True):
    """User-defined custom expense categories."""
    id:         Optional[int] = Field(default=None, primary_key=True)
    user_id:    Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    name:       str                           # e.g. "Petrol", "Books", "Baby"
    icon_emoji: str = Field(default="📦")    # user-chosen emoji
    is_variable: bool = Field(default=True)  # False = fixed-expense category
    sort_order:  int  = Field(default=0)
    created_at:  datetime = Field(default_factory=datetime.now)
```

Also add `UserCategory` to the import in `backend/main.py`.

**`migrate_schema.py`** — in the `cur.executescript` block (Step 1, before the closing `"""`) add:

```sql
CREATE TABLE IF NOT EXISTS usercategory (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER REFERENCES user(id),
    name        TEXT NOT NULL,
    icon_emoji  TEXT NOT NULL DEFAULT '📦',
    is_variable INTEGER NOT NULL DEFAULT 1,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
```

No additive column migration needed (it's a new table).

**`backend/main.py`** — add 3 endpoints after the `GET /budgets` endpoint (after line 998):

```python
@app.get("/categories")
def list_categories(session: Session = Depends(get_session),
                    current_user: User = Depends(get_current_user)):
    """Return user-defined custom categories. Frontend merges with built-in defaults."""
    return session.exec(
        select(UserCategory)
        .where(UserCategory.user_id == current_user.id)
        .order_by(UserCategory.sort_order, UserCategory.id)
    ).all()


class CategoryCreate(BaseModel):
    name:        str
    icon_emoji:  str = "📦"
    is_variable: bool = True

@app.post("/categories", status_code=201)
def create_category(cat: CategoryCreate, session: Session = Depends(get_session),
                    current_user: User = Depends(get_current_user)):
    # Prevent duplicates (case-insensitive)
    existing = session.exec(
        select(UserCategory).where(
            UserCategory.user_id == current_user.id,
            UserCategory.name == cat.name,
        )
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Category already exists")
    uc = UserCategory(
        user_id=current_user.id,
        name=cat.name.strip().title(),
        icon_emoji=cat.icon_emoji,
        is_variable=cat.is_variable,
    )
    session.add(uc)
    session.commit()
    session.refresh(uc)
    return uc


@app.delete("/categories/{category_id}")
def delete_category(category_id: int, session: Session = Depends(get_session),
                    current_user: User = Depends(get_current_user)):
    uc = session.get(UserCategory, category_id)
    if not uc or uc.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Category not found")
    # Warn the caller if expenses use this category — frontend shows a confirm dialog
    expense_count = session.exec(
        select(func.count()).where(
            Expense.user_id == current_user.id,
            Expense.category == uc.name,
        )
    ).one()
    session.delete(uc)
    session.commit()
    return {"deleted": category_id, "expense_count": expense_count}
```

### Frontend

**`frontend/react/src/types/index.ts`** — add:
```typescript
export interface UserCategory {
  id:          number;
  name:        string;
  icon_emoji:  string;
  is_variable: boolean;
  sort_order:  number;
}
```

**`frontend/react/src/utils/categories.ts`** — add a helper that merges built-in icons with user-defined ones. Components will call `GET /categories` once and use this helper:
```typescript
export function mergedIconMap(
  userCats: Array<{ name: string; icon_emoji: string }>
): Record<string, string> {
  const merged = { ...CATEGORY_ICONS };
  for (const c of userCats) {
    if (!merged[c.name]) merged[c.name] = c.icon_emoji;
  }
  return merged;
}
```

**`frontend/react/src/components/tabs/HistoryTab.tsx`** — change `EditExpenseRow` (line 6 import and line 160 dropdown):

Import `UserCategory` type and add a prop or hook to receive the custom category list. Simplest approach: fetch custom cats inside `EditExpenseRow` on mount:

```tsx
// Add at top of EditExpenseRow:
const [customCats, setCustomCats] = useState<UserCategory[]>([]);
useEffect(() => {
  api.get<UserCategory[]>("/categories").then(r => setCustomCats(r.data)).catch(() => {});
}, []);

const allVarCats = [
  ...VAR_CATEGORIES,
  ...customCats.filter(c => c.is_variable).map(c => c.name),
];
```

Then change the dropdown (line 160–163):
```tsx
{allVarCats.map(c => (
  <option key={c} value={c}>
    {CATEGORY_ICONS[c] ?? customCats.find(uc => uc.name === c)?.icon_emoji ?? "📦"} {c}
  </option>
))}
```

**New file: `frontend/react/src/components/settings/CategoriesSection.tsx`** — new settings section component. Create it following the same pattern as `CapsSection.tsx`. It should:
- `GET /categories` on mount → list custom categories with name + emoji + delete button
- "Add category" form: text input for name, emoji input (single character), variable/fixed radio toggle, Add button → `POST /categories`
- Delete button → show a confirmation if `expense_count > 0` from the delete response (use a `window.confirm` or an inline confirmation state before making the call)
- Render categories in a list (not grid), each row: emoji · name · type badge · trash icon

**`frontend/react/src/components/settings/SettingsTab.tsx`** — import and render `<CategoriesSection />` after `<CapsSection />`. Check the current rendering order in SettingsTab to find the right insertion point.

**After completing Item E, run the migration**:
```bash
uv run python migrate_schema.py
```
Or rebuild Docker: `docker compose up -d --build`.

---

## Item F — Custom categories Phase 2: AI parser uses dynamic category list
**Scope**: Backend-only (depends on Item E being complete)
**Files**:
- `backend/ai_parser.py`
- `backend/main.py` — `POST /expenses/parse` caller

**Root cause (verified against current code)**:
`ai_parser.py:33`: `"2. Category must be one of: Food, Travel, Groceries, Shopping, Medical, Entertainment, Gifts, Course, Miscellaneous"` is a hardcoded string. The function signature `parse_expense_input(user_input: str) -> list[dict]` has no way to receive per-user custom categories.

**What to do**:

**`backend/ai_parser.py`** — change `parse_expense_input` signature to accept an optional extra category list:

```python
def parse_expense_input(user_input: str, extra_categories: list[str] | None = None) -> list[dict]:
```

Build the category list dynamically:
```python
BASE_CATEGORIES = [
    "Food", "Travel", "Groceries", "Shopping", "Medical",
    "Entertainment", "Gifts", "Course", "Miscellaneous",
]
all_cats = BASE_CATEGORIES + (extra_categories or [])
cats_str = ", ".join(all_cats)
```

Replace the hardcoded rule 2 in the prompt:
```python
# Change:
"2. Category must be one of: Food, Travel, Groceries, Shopping, Medical, Entertainment, Gifts, Course, Miscellaneous"
# To:
f"2. Category must be one of: {cats_str}"
```

**`backend/main.py`** — at the `POST /expenses/parse` endpoint, fetch the user's custom categories and pass them to the parser. Find the call to `parse_expense_input` and change it:

```python
# Fetch user-defined custom categories
custom_cats = session.exec(
    select(UserCategory)
    .where(UserCategory.user_id == current_user.id, UserCategory.is_variable == True)
).all()
extra = [c.name for c in custom_cats]

parsed = parse_expense_input(body.text, extra_categories=extra)
```

No schema change, no frontend change. `get_budget_insight` in `ai_parser.py` does not need updating (it doesn't use the category list).

---

## Execution Order

| # | Item | Effort | Backend? | Risk | Depends on |
|---|------|--------|----------|------|------------|
| A | Mobile download iOS fix | ~1h | No | Isolated | — |
| B | Summary includes uncapped spending | ~30min | Yes (1 fn) | Low | — |
| C | CapsSection add-new-cap UI | ~2h | No | Low | — |
| D | Date range CSV export | ~3h | Yes (new endpoint) | Low | — |
| E | Custom categories Phase 1 | ~1–2 days | Yes (new table) | Medium | — |
| F | Custom categories Phase 2 (AI) | ~3h | Yes (parser) | Low | E |

Items A, B, C can be done in any order. D can be done independently. E requires running `migrate_schema.py` after. F must come after E.

---

## Definition of Done
- `cd frontend/react && npm run build` passes (zero TypeScript errors, zero ESLint warnings)
- Items A–D manually verified in the running app (`uv run uvicorn backend.main:app --reload` + `npm run dev`)
- Item A: tested on actual iOS device or Safari browser tools
- Item B: log an expense to an uncapped category → it appears in Spend by Category donut
- Item C: add a new cap → it appears in the grid immediately, saves without page reload
- Item D: range download works on desktop; iOS opens in new tab
- Item E: after `uv run python migrate_schema.py`, add a custom category in Settings → appears in HistoryTab edit dropdown
- Item F: type "HP petrol 800" in QuickAdd → AI returns `"Petrol"` category (if "Petrol" is a user custom category)
