# SpendSense — Commit 2.1 Implementation Prompt
## Sprint 2 — Data Isolation: Schema Migration

Reference: `design/MULTI_USER_ROADMAP.md` → Sprint 2, Commit 2.1

---

## Context

SpendSense has full JWT authentication (Sprint 1 complete). All endpoints are
protected — every request carries a `current_user: User` object. However, all
users currently share the same data. User A can see User B's expenses.

Commit 2.1 fixes the schema foundation by adding `user_id` as a foreign key to
every data table. Commit 2.2 (next) will update the queries to filter by it.

**Project root:** `/Users/debashish/Desktop/ai-projects/expenditure-tracker`  
**Package manager:** `uv` — never use pip  
**Database:** SQLite at `data/expenses.db`

---

## Current Table Inventory (from `backend/models.py`)

| Table | SQLModel Class | Needs `user_id`? |
|---|---|---|
| `user` | `User` | ❌ No — this IS the user |
| `fixedexpensetemplate` | `FixedExpenseTemplate` | ✅ Yes |
| `poolentry` | `PoolEntry` | ✅ Yes |
| `expensetemplate` | `ExpenseTemplate` | ✅ Yes |
| `expense` | `Expense` | ✅ Yes |
| `budgetlimit` | `BudgetLimit` | ✅ Yes |
| `incomeentry` | `IncomeEntry` | ✅ Yes |

---

## Step 1 — Update `backend/models.py`

Add `user_id` as an optional foreign key field to all 6 tables listed above.

### Rules for every addition:

- Field definition:
  ```python
  user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
  ```
- `Optional[int]` with `default=None` — allows existing rows to be migrated
  without breaking on null values before the migration script runs
- `index=True` — every query in Commit 2.2 will filter by `user_id`; the index
  makes these queries fast even with thousands of rows
- `foreign_key="user.id"` — references the `User` table which is already
  defined first in this file (Sprint 1 placed it there intentionally)
- Place the `user_id` field as the **second field** in each class, immediately
  after `id` — consistent position makes it easy to audit

### Exact placements per model:

**`FixedExpenseTemplate`** — add after `id`:
```python
user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
```

**`PoolEntry`** — add after `id`:
```python
user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
```

**`ExpenseTemplate`** — add after `id`:
```python
user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
```

**`Expense`** — add after `id`:
```python
user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
```

**`BudgetLimit`** — add after `id`:
```python
user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
```

**`IncomeEntry`** — add after `id`:
```python
user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
```

### What NOT to change in models.py:
- The `User` class — no changes
- Any existing fields — no renames, no removals
- `create_db()` and `get_session()` — no changes
- Import block — no changes needed (Optional and Field already imported)

---

## Step 2 — Write `migrate_add_user_id.py`

Create a new file at the project root: `migrate_add_user_id.py`

This script runs once against the existing SQLite database. It:
1. Adds the `user_id` column to each of the 6 tables using `ALTER TABLE`
2. Assigns all existing rows to the default admin user (the first user in the
   `user` table, `id=1`)
3. Is idempotent — safe to run multiple times without breaking anything

### Script requirements:

```python
"""
migrate_add_user_id.py
──────────────────────
Sprint 2, Commit 2.1 — Schema Migration

Adds user_id FK column to all data tables and assigns existing rows
to the default admin user (id=1).

Run once:
    uv run python migrate_add_user_id.py

Safe to re-run — skips columns that already exist.
"""
```

**Tables and columns to migrate:**

```python
MIGRATIONS = [
    ("fixedexpensetemplate", "user_id"),
    ("poolentry",            "user_id"),
    ("expensetemplate",      "user_id"),
    ("expense",              "user_id"),
    ("budgetlimit",          "user_id"),
    ("incomeentry",          "user_id"),
]
```

**For each table, the script must:**

1. Check if the column already exists using `PRAGMA table_info(<table>)` — if
   it does, print `⏭️  <table>.user_id already exists — skipping` and skip
2. If not, run:
   ```sql
   ALTER TABLE <table> ADD COLUMN user_id INTEGER REFERENCES user(id)
   ```
3. Create an index for fast filtering:
   ```sql
   CREATE INDEX IF NOT EXISTS idx_<table>_user_id ON <table>(user_id)
   ```
4. Assign existing rows to admin (id=1):
   ```sql
   UPDATE <table> SET user_id = 1 WHERE user_id IS NULL
   ```
5. Print result: `✅ Migrated <table> — N rows assigned to user_id=1`

**Admin user check at startup:**

Before running migrations, the script must:
- Connect to the database at `data/expenses.db`
- Verify the `user` table exists and has at least one row
- Find the admin user: `SELECT id, email FROM user WHERE is_admin=1 LIMIT 1`
- If no admin user found → print clear error and exit:
  ```
  ❌ No admin user found in the database.
     Start the backend first to auto-create the default admin:
     uv run uvicorn backend.main:app --port 8000
     Then re-run this script.
  ```
- Print: `👤 Assigning existing rows to admin: <email> (id=<id>)`

**Final summary:**

After all migrations complete, print:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Migration complete
   All existing data assigned to: <email>
   Run the backend to verify: uv run uvicorn backend.main:app --port 8000
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Use only stdlib + sqlite3** — no SQLModel, no FastAPI, no imports from
`backend/`. This script must be runnable independently without the venv
being active, purely with Python's built-in `sqlite3` module.

---

## Step 3 — Update `README.md`

Add a short `## Database Migrations` section documenting how to run
the migration. Place it after the existing `## Setup (Mac)` section.

Content:
```markdown
## Database Migrations

When upgrading from a single-user to multi-user setup, run the schema
migration script once:

    uv run python migrate_add_user_id.py

This adds `user_id` to all data tables and assigns any existing data to
the default admin account. Safe to re-run — skips columns that already exist.

Always start the backend at least once before running migrations so the
`user` table and default admin are created.
```

---

## Execution Order

1. Update `backend/models.py` — add `user_id` to all 6 models
2. Create `migrate_add_user_id.py` at project root
3. Update `README.md` with migration instructions
4. Start the backend once to ensure the `user` table and admin exist:
   ```bash
   uv run uvicorn backend.main:app --port 8000
   # wait for "✅ Default admin created" or "Application startup complete"
   # then Ctrl+C
   ```
5. Run the migration:
   ```bash
   uv run python migrate_add_user_id.py
   ```
6. Verify (see Verification Steps below)

---

## Verification Steps

### V1 — models.py syntax clean
```bash
python3 -c "from backend.models import User, Expense, IncomeEntry,
FixedExpenseTemplate, PoolEntry, BudgetLimit, ExpenseTemplate; print('✅ imports OK')"
```

### V2 — user_id present in all 6 models
```bash
python3 -c "
from backend.models import (Expense, IncomeEntry, FixedExpenseTemplate,
    PoolEntry, BudgetLimit, ExpenseTemplate)
tables = [Expense, IncomeEntry, FixedExpenseTemplate, PoolEntry, BudgetLimit, ExpenseTemplate]
for t in tables:
    fields = t.model_fields.keys()
    status = '✅' if 'user_id' in fields else '❌'
    print(f'{status} {t.__name__}: user_id={\"user_id\" in fields}')
"
```

### V3 — migration script runs cleanly
```bash
uv run python migrate_add_user_id.py
# expect: ✅ lines for all 6 tables
# expect: final summary with admin email
```

### V4 — columns exist in DB after migration
```bash
sqlite3 data/expenses.db "PRAGMA table_info(expense);" | grep user_id
sqlite3 data/expenses.db "PRAGMA table_info(incomeentry);" | grep user_id
sqlite3 data/expenses.db "PRAGMA table_info(budgetlimit);" | grep user_id
sqlite3 data/expenses.db "PRAGMA table_info(fixedexpensetemplate);" | grep user_id
sqlite3 data/expenses.db "PRAGMA table_info(poolentry);" | grep user_id
sqlite3 data/expenses.db "PRAGMA table_info(expensetemplate);" | grep user_id
# expect: each shows a user_id INTEGER row
```

### V5 — existing rows assigned to admin
```bash
sqlite3 data/expenses.db "SELECT COUNT(*) FROM expense WHERE user_id IS NULL;"
sqlite3 data/expenses.db "SELECT COUNT(*) FROM incomeentry WHERE user_id IS NULL;"
sqlite3 data/expenses.db "SELECT COUNT(*) FROM budgetlimit WHERE user_id IS NULL;"
# expect: 0 for all — no orphaned rows
```

### V6 — indexes created
```bash
sqlite3 data/expenses.db ".indexes"
# expect: idx_expense_user_id, idx_incomeentry_user_id etc. all listed
```

### V7 — backend still starts after migration
```bash
uv run uvicorn backend.main:app --port 8000
# expect: Application startup complete — no errors
# test a protected endpoint:
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@spendsense.local","password":"changeme123"}'
# expect: {"access_token": "eyJ..."}
```

### V8 — re-running migration is safe
```bash
uv run python migrate_add_user_id.py
# expect: all 6 lines show ⏭️  already exists — skipping
# expect: no errors, no data corruption
```

---

## Files Created / Modified in This Commit

| File | Change |
|---|---|
| `backend/models.py` | `user_id` FK added to 6 models |
| `migrate_add_user_id.py` | New — one-time migration script |
| `README.md` | New `## Database Migrations` section added |

### Files NOT changed in this commit
- `backend/main.py` — query isolation is Commit 2.2
- `backend/auth.py` — no changes
- `backend/budget_rules.py` — query isolation is Commit 2.2
- `frontend/app.py` — no frontend changes in Sprint 2
- Any `.env` or config files

---

## Important Notes

**Why `Optional[int]` not `int`:**
SQLite does not support adding NOT NULL columns to existing tables via
`ALTER TABLE` unless a DEFAULT is provided. Using `Optional[int]` with
`default=None` in SQLModel, combined with the migration script updating
nulls to `user_id=1`, keeps the schema change safe for existing databases.

**Why existing data goes to admin (id=1):**
The original single-user data belongs to you — the person who built this.
You registered as the first user (admin). Assigning existing rows to id=1
preserves your full expense history under your account. Other users who
register later start with a clean slate.

**Why this commit does NOT filter queries yet:**
Adding `user_id` to the schema and migrating data is one atomic step.
Updating all queries is a separate step (Commit 2.2). This prevents a
partial state where some queries filter by `user_id` and others don't,
which would be harder to debug.

**SQLite ALTER TABLE limitation:**
SQLite does not support adding foreign key constraints to existing tables
via ALTER TABLE. The column is added as `INTEGER REFERENCES user(id)` which
SQLite treats as advisory only (FK enforcement requires `PRAGMA foreign_keys=ON`).
This is acceptable for our use case — the application code enforces the
constraint by always writing `user_id` on insert (Commit 2.2).

---

*Last updated: May 2026*
*Owner: Debashish*
*Status: Prompt ready — awaiting execution approval*
