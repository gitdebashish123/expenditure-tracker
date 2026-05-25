# SpendSense — Commit 2.2 Implementation Prompt
## Sprint 2 — Data Isolation: API Query Isolation

Reference: `design/MULTI_USER_ROADMAP.md` → Sprint 2, Commit 2.2

---

## Context

Commit 2.1 added `user_id` to all 6 data tables and migrated existing rows.
Commit 2.2 makes every query use that `user_id` — so each authenticated user
sees and modifies only their own data.

**The rule is simple:** every `select()`, `INSERT`, and `session.get()` that
touches a data table must be scoped to `current_user.id`.

**Project root:** `/Users/debashish/Desktop/ai-projects/expenditure-tracker`  
**Files changed:** `backend/main.py` and `backend/budget_rules.py` only  
**No frontend changes. No model changes. No migration scripts.**

---

## The Core Pattern

Every protected endpoint already receives `current_user: User` from
`Depends(get_current_user)`. That object has a `.id` field. Use it.

```python
# BEFORE (Commit 2.1 — unscoped)
expenses = session.exec(
    select(Expense).where(Expense.month_key == month_key)
).all()

# AFTER (Commit 2.2 — scoped to current user)
expenses = session.exec(
    select(Expense).where(
        Expense.month_key == month_key,
        Expense.user_id == current_user.id,
    )
).all()
```

For INSERTs, always set `user_id=current_user.id` on the new object:
```python
# BEFORE
exp = Expense(date=..., vendor=..., amount=..., ...)

# AFTER
exp = Expense(date=..., vendor=..., amount=..., user_id=current_user.id, ...)
```

For `session.get()` lookups, verify ownership after fetch:
```python
# BEFORE
exp = session.get(Expense, expense_id)
if not exp:
    raise HTTPException(status_code=404, ...)

# AFTER
exp = session.get(Expense, expense_id)
if not exp or exp.user_id != current_user.id:
    raise HTTPException(status_code=404, ...)
```

Always use `404` not `403` on ownership failure — do not reveal that the
resource exists for another user.

---

## Changes Required in `backend/main.py`

### on_startup() — Seed budget limits for admin only

The startup seeding of `BudgetLimit` currently uses a global query. Since
`on_startup` runs without an authenticated user, budget limits are seeded for
the admin user only (id retrieved from DB, not from `current_user`).

```python
@app.on_event("startup")
def on_startup():
    create_db()
    with Session(engine) as session:
        # Find admin user id for seeding
        admin = session.exec(select(User).where(User.is_admin == True)).first()
        admin_id = admin.id if admin else None

        # Seed budget limits for admin only if none exist
        existing = session.exec(
            select(BudgetLimit).where(BudgetLimit.user_id == admin_id)
        ).first() if admin_id else None
        if not existing and admin_id:
            for cat, limit in config.get("budget_limits", {}).items():
                session.add(BudgetLimit(
                    category=cat, limit_amount=limit, user_id=admin_id
                ))
            session.commit()

        # Seed current month fixed expenses for admin only
        if admin_id:
            seed_fixed_expenses(session, get_month_key(), user_id=admin_id)

        # Default admin user creation (unchanged from Sprint 1)
        existing_user = session.exec(select(User)).first()
        if not existing_user:
            ...  # keep existing admin creation code unchanged
```

---

### parse_and_save — POST /expenses/parse

**Expense INSERT:** add `user_id=current_user.id`

```python
exp = Expense(
    date=expense_date,
    vendor=item["vendor"],
    amount=item["amount"],
    category=item["category"],
    note=item.get("note"),
    is_fixed=False,
    paid=True,
    month_key=month_key,
    user_id=current_user.id,   # ← add
)
```

**Pass user_id to helpers:**
```python
warnings = check_budget_warnings(session, month_key, user_id=current_user.id)
balance  = get_balance_summary(session, month_key, user_id=current_user.id)
```

---

### add_manual_expense — POST /expenses/manual

**Expense INSERT:** add `user_id=current_user.id`

**Pass user_id to helpers:**
```python
warnings = check_budget_warnings(session, month_key, user_id=current_user.id)
```

---

### get_expenses — GET /expenses/{month_key}

```python
expenses = session.exec(
    select(Expense).where(
        Expense.month_key == month_key,
        Expense.user_id == current_user.id,
    ).order_by(Expense.date.desc())
).all()
```

---

### edit_expense — PATCH /expenses/{expense_id}

```python
exp = session.get(Expense, expense_id)
if not exp or exp.is_fixed or exp.user_id != current_user.id:
    raise HTTPException(status_code=404, detail="Expense not found")
```

---

### bulk_delete_expenses — POST /expenses/bulk-delete

```python
exp = session.get(Expense, expense_id)
if exp and not exp.is_fixed and exp.user_id == current_user.id:
    session.delete(exp)
    deleted.append(expense_id)
```

---

### delete_expense — DELETE /expenses/{expense_id}

```python
exp = session.get(Expense, expense_id)
if not exp or exp.user_id != current_user.id:
    raise HTTPException(status_code=404, detail="Expense not found")
```

---

### get_fixed_expenses — GET /fixed/{month_key}

```python
seed_fixed_expenses(session, month_key, user_id=current_user.id)
expenses = session.exec(
    select(Expense).where(
        Expense.month_key == month_key,
        Expense.is_fixed == True,
        Expense.user_id == current_user.id,
    ).order_by(Expense.category, Expense.vendor)
).all()
```

---

### toggle_paid — PATCH /fixed/{expense_id}/toggle

```python
exp = session.get(Expense, expense_id)
if not exp or not exp.is_fixed or exp.user_id != current_user.id:
    raise HTTPException(status_code=404, detail="Fixed expense not found")
```

---

### update_fixed_amount — PATCH /fixed/{expense_id}/amount

```python
exp = session.get(Expense, expense_id)
if not exp or not exp.is_fixed or exp.user_id != current_user.id:
    raise HTTPException(status_code=404, detail="Fixed expense not found")
```

---

### list_expense_templates — GET /expense-templates

```python
return session.exec(
    select(ExpenseTemplate).where(
        ExpenseTemplate.is_active == True,
        ExpenseTemplate.user_id == current_user.id,
    ).order_by(ExpenseTemplate.use_count.desc())
).all()
```

---

### create_expense_template — POST /expense-templates

```python
new = ExpenseTemplate(
    name=tmpl.name, vendor=tmpl.vendor,
    category=tmpl.category, amount=tmpl.amount,
    user_id=current_user.id,   # ← add
)
```

---

### update_expense_template — PUT /expense-templates/{tmpl_id}

```python
tmpl = session.get(ExpenseTemplate, tmpl_id)
if not tmpl or tmpl.user_id != current_user.id:
    raise HTTPException(status_code=404, detail="Template not found")
```

---

### delete_expense_template — DELETE /expense-templates/{tmpl_id}

```python
tmpl = session.get(ExpenseTemplate, tmpl_id)
if not tmpl or tmpl.user_id != current_user.id:
    raise HTTPException(status_code=404, detail="Template not found")
```

---

### log_from_template — POST /expense-templates/{tmpl_id}/log

```python
tmpl = session.get(ExpenseTemplate, tmpl_id)
if not tmpl or tmpl.user_id != current_user.id:
    raise HTTPException(status_code=404, detail="Template not found")

# Expense INSERT
exp = Expense(
    ...,
    user_id=current_user.id,   # ← add
)

# Helpers
warnings = check_budget_warnings(session, month_key, user_id=current_user.id)
balance  = get_balance_summary(session, month_key, user_id=current_user.id)
```

---

### check_income_set — GET /income/check/{month_key}

```python
entry = session.exec(
    select(IncomeEntry).where(
        IncomeEntry.month_key == month_key,
        IncomeEntry.user_id == current_user.id,
    )
).first()
```

---

### get_due_reminders — GET /fixed/due-reminders/{month_key}

```python
expenses = session.exec(
    select(Expense).where(
        Expense.month_key == month_key,
        Expense.is_fixed == True,
        Expense.paid == False,
        Expense.user_id == current_user.id,
    )
).all()
```

Also scope the template lookup — only return reminders for templates
owned by this user:
```python
tmpl = session.get(FixedExpenseTemplate, exp.fixed_template_id)
if tmpl and tmpl.user_id != current_user.id:
    continue
```

---

### list_templates — GET /fixed-templates

```python
return session.exec(
    select(FixedExpenseTemplate).where(
        FixedExpenseTemplate.user_id == current_user.id,
    ).order_by(FixedExpenseTemplate.sort_order, FixedExpenseTemplate.id)
).all()
```

---

### create_template — POST /fixed-templates

```python
new = FixedExpenseTemplate(
    name=tmpl.name,
    category=tmpl.category,
    amount=tmpl.amount,
    sort_order=tmpl.sort_order or 0,
    template_type=tmpl.template_type or "fixed",
    user_id=current_user.id,   # ← add
)
```

---

### update_template — PUT /fixed-templates/{template_id}

```python
tmpl = session.get(FixedExpenseTemplate, template_id)
if not tmpl or tmpl.user_id != current_user.id:
    raise HTTPException(status_code=404, detail="Template not found")
```

---

### delete_template — DELETE /fixed-templates/{template_id}

```python
tmpl = session.get(FixedExpenseTemplate, template_id)
if not tmpl or tmpl.user_id != current_user.id:
    raise HTTPException(status_code=404, detail="Template not found")

# Scope the cleanup query too
rows_to_delete = session.exec(
    select(Expense).where(
        Expense.fixed_template_id == template_id,
        Expense.month_key >= current_month,
        Expense.user_id == current_user.id,
    )
).all()
```

---

### get_summary — GET /summary/{month_key}

```python
seed_fixed_expenses(session, month_key, user_id=current_user.id)
balance  = get_balance_summary(session, month_key, user_id=current_user.id)
warnings = check_budget_warnings(session, month_key, user_id=current_user.id)
spent_by_cat = get_monthly_spent_by_category(session, month_key,
                                              user_id=current_user.id)
limits = get_budget_limits(session, user_id=current_user.id)

fixed_exps = session.exec(
    select(Expense).where(
        Expense.month_key == month_key,
        Expense.is_fixed == True,
        Expense.user_id == current_user.id,
    )
).all()
```

---

### update_budget — PUT /budget

```python
bl = session.exec(
    select(BudgetLimit).where(
        BudgetLimit.category == update.category,
        BudgetLimit.user_id == current_user.id,
    )
).first()
if bl:
    bl.limit_amount = update.limit_amount
else:
    bl = BudgetLimit(
        category=update.category,
        limit_amount=update.limit_amount,
        user_id=current_user.id,   # ← add on create
    )
    session.add(bl)
```

---

### list_budgets — GET /budgets

```python
return session.exec(
    select(BudgetLimit).where(BudgetLimit.user_id == current_user.id)
).all()
```

---

### upsert_income — POST /income

```python
existing = session.exec(
    select(IncomeEntry).where(
        IncomeEntry.month_key == month_key,
        IncomeEntry.user_id == current_user.id,
    )
).first()
if existing:
    existing.source = income.source
    existing.amount = income.amount
    existing.note   = income.note
    session.add(existing)
else:
    entry = IncomeEntry(
        source=income.source, amount=income.amount,
        month_key=month_key, note=income.note,
        user_id=current_user.id,   # ← add
    )
    session.add(entry)
```

---

### get_income — GET /income/{month_key}

```python
entry = session.exec(
    select(IncomeEntry).where(
        IncomeEntry.month_key == month_key,
        IncomeEntry.user_id == current_user.id,
    )
).first()
```

---

### list_months — GET /months

```python
expenses = session.exec(
    select(Expense.month_key).where(
        Expense.user_id == current_user.id
    ).distinct()
).all()
```

---

### seed_month — POST /seed/{month_key}

```python
seed_fixed_expenses(session, month_key, user_id=current_user.id)
```

---

### month_over_month — GET /insights/mom/{month_key}

```python
expenses = session.exec(
    select(Expense).where(
        Expense.month_key.in_(months),
        Expense.is_fixed == False,
        Expense.user_id == current_user.id,
    )
).all()

incomes = session.exec(
    select(IncomeEntry).where(
        IncomeEntry.month_key.in_(months),
        IncomeEntry.user_id == current_user.id,
    )
).all()
```

---

### top_spends — GET /insights/top-spends/{month_key}

```python
expenses = session.exec(
    select(Expense).where(
        Expense.month_key == month_key,
        Expense.is_fixed == False,
        Expense.user_id == current_user.id,
    ).order_by(Expense.amount.desc())
).all()
```

---

### budget_projection — GET /insights/projection/{month_key}

```python
expenses = session.exec(
    select(Expense).where(
        Expense.month_key == month_key,
        Expense.is_fixed == False,
        Expense.user_id == current_user.id,
    )
).all()

limits_rows = session.exec(
    select(BudgetLimit).where(BudgetLimit.user_id == current_user.id)
).all()
```

---

### get_pools_for_month — GET /pools/{month_key}

```python
pool_templates = session.exec(
    select(FixedExpenseTemplate).where(
        FixedExpenseTemplate.is_active == True,
        FixedExpenseTemplate.template_type == "pool",
        FixedExpenseTemplate.user_id == current_user.id,
    ).order_by(FixedExpenseTemplate.sort_order, FixedExpenseTemplate.id)
).all()
```

---

### add_pool_entry — POST /pools/{pool_template_id}/entries/{month_key}

```python
tmpl = session.get(FixedExpenseTemplate, pool_template_id)
if not tmpl or tmpl.template_type != "pool" or tmpl.user_id != current_user.id:
    raise HTTPException(status_code=404, detail="Pool template not found")

new_entry = PoolEntry(
    pool_template_id=pool_template_id,
    month_key=month_key,
    label=entry.label,
    amount=entry.amount,
    paid=True,
    paid_date=date.today(),
    note=entry.note,
    user_id=current_user.id,   # ← add
)
```

---

### update_pool_entry — PATCH /pools/entries/{entry_id}

```python
entry = session.get(PoolEntry, entry_id)
if not entry or entry.user_id != current_user.id:
    raise HTTPException(status_code=404, detail="Pool entry not found")
```

---

### toggle_pool_entry_paid — PATCH /pools/entries/{entry_id}/toggle

```python
entry = session.get(PoolEntry, entry_id)
if not entry or entry.user_id != current_user.id:
    raise HTTPException(status_code=404, detail="Pool entry not found")
```

---

### delete_pool_entry — DELETE /pools/entries/{entry_id}

```python
entry = session.get(PoolEntry, entry_id)
if not entry or entry.user_id != current_user.id:
    raise HTTPException(status_code=404, detail="Pool entry not found")
```

---

## Changes Required in `backend/budget_rules.py`

Every function in `budget_rules.py` is called from `main.py` endpoints that
have `current_user`. Add `user_id: int` as a required parameter to all
data-querying functions, and filter every query.

### get_monthly_spent_by_category

```python
def get_monthly_spent_by_category(session: Session, month_key: str,
                                   user_id: int) -> dict[str, float]:
    expenses = session.exec(
        select(Expense).where(
            Expense.month_key == month_key,
            Expense.user_id == user_id,
        )
    ).all()
    totals = {}
    for e in expenses:
        totals[e.category] = totals.get(e.category, 0) + e.amount
    return totals
```

---

### get_budget_limits

```python
def get_budget_limits(session: Session, user_id: int) -> dict[str, float]:
    limits = session.exec(
        select(BudgetLimit).where(BudgetLimit.user_id == user_id)
    ).all()
    if limits:
        return {bl.category: bl.limit_amount for bl in limits}
    return config.get("budget_limits", {})
```

---

### check_budget_warnings

```python
def check_budget_warnings(session: Session, month_key: str,
                           user_id: int) -> list[dict]:
    spent  = get_monthly_spent_by_category(session, month_key, user_id=user_id)
    limits = get_budget_limits(session, user_id=user_id)
    # rest of function unchanged
```

---

### get_balance_summary

```python
def get_balance_summary(session: Session, month_key: str,
                         user_id: int) -> dict:
    incomes = session.exec(
        select(IncomeEntry).where(
            IncomeEntry.month_key == month_key,
            IncomeEntry.user_id == user_id,
        )
    ).all()

    fixed_all = session.exec(
        select(Expense).where(
            Expense.month_key == month_key,
            Expense.is_fixed == True,
            Expense.user_id == user_id,
        )
    ).all()

    pool_all = session.exec(
        select(PoolEntry).where(
            PoolEntry.month_key == month_key,
            PoolEntry.user_id == user_id,
        )
    ).all()

    variable = session.exec(
        select(Expense).where(
            Expense.month_key == month_key,
            Expense.is_fixed == False,
            Expense.user_id == user_id,
        )
    ).all()
    # rest of calculation unchanged
```

---

### seed_fixed_expenses

```python
def seed_fixed_expenses(session: Session, month_key: str, user_id: int):
    year, month = map(int, month_key.split("-"))
    expense_date = date(year, month, 1)

    templates = session.exec(
        select(FixedExpenseTemplate).where(
            FixedExpenseTemplate.is_active == True,
            FixedExpenseTemplate.user_id == user_id,
        ).order_by(FixedExpenseTemplate.sort_order, FixedExpenseTemplate.id)
    ).all()

    if not templates:
        _seed_from_config(session, month_key, expense_date, user_id=user_id)
        return

    for tmpl in templates:
        if tmpl.template_type == "pool":
            continue
        existing = session.exec(
            select(Expense).where(
                Expense.month_key == month_key,
                Expense.fixed_template_id == tmpl.id,
                Expense.user_id == user_id,
            )
        ).first()
        if existing:
            continue

        exp = Expense(
            date=expense_date,
            vendor=tmpl.name,
            amount=tmpl.amount,
            category=tmpl.category,
            is_fixed=True,
            paid=False,
            month_key=month_key,
            fixed_template_id=tmpl.id,
            note="Auto-seeded fixed expense",
            user_id=user_id,   # ← add
        )
        session.add(exp)

    session.commit()
```

---

### _seed_from_config

```python
def _seed_from_config(session: Session, month_key: str,
                       expense_date: date, user_id: int):
    fixed_list = config.get("fixed_expenses", [])
    for i, item in enumerate(fixed_list):
        tmpl = FixedExpenseTemplate(
            name=item["name"],
            category=item["category"],
            amount=item["amount"],
            is_active=True,
            sort_order=i,
            user_id=user_id,   # ← add
        )
        session.add(tmpl)
        session.flush()

        existing = session.exec(
            select(Expense).where(
                Expense.month_key == month_key,
                Expense.fixed_template_id == tmpl.id,
                Expense.user_id == user_id,
            )
        ).first()
        if not existing:
            exp = Expense(
                date=expense_date,
                vendor=item["name"],
                amount=item["amount"],
                category=item["category"],
                is_fixed=True,
                paid=False,
                month_key=month_key,
                fixed_template_id=tmpl.id,
                note="Auto-seeded fixed expense",
                user_id=user_id,   # ← add
            )
            session.add(exp)
    session.commit()
```

---

## Files Modified in This Commit

| File | Change |
|---|---|
| `backend/main.py` | All 34 data endpoints scoped to `current_user.id` |
| `backend/budget_rules.py` | All 5 functions accept and use `user_id` parameter |

### Files NOT changed
- `backend/models.py` — schema done in Commit 2.1
- `backend/auth.py` — no changes
- `frontend/app.py` — no frontend changes
- `migrate_add_user_id.py` — migration already run
- Any `.env` or config files

---

## Critical Implementation Rules

1. **Never use `403` for ownership failures** — always `404`. Do not reveal
   that a resource exists for another user.

2. **Every `session.get()` must check ownership** — `session.get(Expense, id)`
   returns rows from any user. Always follow with:
   `if not exp or exp.user_id != current_user.id: raise 404`

3. **Pass `user_id` not `current_user`** to `budget_rules.py` functions —
   keeps the rules module decoupled from FastAPI types.

4. **`on_startup` has no current_user** — use the admin user's id from a DB
   query. Never skip seeding; admin's data must still be seeded on startup.

5. **`BudgetLimit.category` uniqueness** — the `BudgetLimit` table has
   `category: str = Field(unique=True)` in the model. With multi-user,
   two users can both have a "Food" budget limit. The unique constraint
   must be changed to unique per `(category, user_id)` pair.
   Add this to the `BudgetLimit` model:
   ```python
   class BudgetLimit(SQLModel, table=True):
       __table_args__ = (
           UniqueConstraint("category", "user_id", name="uq_budgetlimit_cat_user"),
       )
   ```
   And import `UniqueConstraint` from `sqlalchemy`:
   ```python
   from sqlalchemy import UniqueConstraint
   ```
   Also update the `on_startup` budget seeding and `update_budget` endpoint
   to query by both `category` AND `user_id` (not just category).

---

## Verification Steps

### V1 — Backend starts cleanly
```bash
uv run uvicorn backend.main:app --port 8000 --reload
# expect: Application startup complete — no errors
```

### V2 — Login and get token for admin
```bash
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@spendsense.local","password":"changeme123"}' \
  | python3 -m json.tool
# expect: {"access_token": "eyJ...", "token_type": "bearer"}
export TOKEN_ADMIN=<token>
```

### V3 — Register a second test user and login
```bash
curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user2@test.com","password":"testpass123"}' \
  | python3 -m json.tool
# expect: {"id": 2, "email": "user2@test.com", ...}

curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user2@test.com","password":"testpass123"}' \
  | python3 -m json.tool
export TOKEN_USER2=<token>
```

### V4 — Admin's expenses not visible to user2
```bash
# Admin: add an expense
curl -s -X POST http://localhost:8000/expenses/parse \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -H "Content-Type: application/json" \
  -d '{"text":"zomato 500"}' | python3 -m json.tool

# User2: fetch expenses — must return empty list, not admin's zomato
MONTH=$(date +%Y-%m)
curl -s "http://localhost:8000/expenses/$MONTH" \
  -H "Authorization: Bearer $TOKEN_USER2" | python3 -m json.tool
# expect: [] — empty, not admin's data
```

### V5 — User2 cannot access admin's expense by ID
```bash
# Get admin's first expense ID
EXPENSE_ID=$(curl -s "http://localhost:8000/expenses/$MONTH" \
  -H "Authorization: Bearer $TOKEN_ADMIN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['id'] if d else 'none')")

# User2 tries to delete it — must get 404
curl -s -X DELETE "http://localhost:8000/expenses/$EXPENSE_ID" \
  -H "Authorization: Bearer $TOKEN_USER2"
# expect: 404 Not Found
```

### V6 — Budget limits are user-scoped
```bash
# Admin sets a food limit
curl -s -X PUT http://localhost:8000/budget \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -H "Content-Type: application/json" \
  -d '{"category":"Food","limit_amount":5000}'

# User2 fetches budgets — must be empty (their own, not admin's)
curl -s http://localhost:8000/budgets \
  -H "Authorization: Bearer $TOKEN_USER2" | python3 -m json.tool
# expect: [] — user2 has no budgets yet
```

### V7 — Dashboard summary shows only own data
```bash
curl -s "http://localhost:8000/summary/$MONTH" \
  -H "Authorization: Bearer $TOKEN_USER2" | python3 -m json.tool
# expect: balance shows 0 income, 0 expenses (user2 has no data)
```

### V8 — Month list shows only own months
```bash
curl -s http://localhost:8000/months \
  -H "Authorization: Bearer $TOKEN_USER2"
# expect: [] or only months where user2 has data
```

---

*Last updated: May 2026*
*Owner: Debashish*
*Status: Prompt ready — awaiting execution approval*
