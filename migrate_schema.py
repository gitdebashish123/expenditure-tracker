"""
migrate_schema.py
─────────────────
Adds new columns to existing tables without wiping data.
Safe to run multiple times (idempotent).
In Docker: runs as db-init service before backend starts.
Locally: uv run python migrate_schema.py
"""
import sqlite3
import os

# Support both local (./data/) and Docker (/app/data/) paths
DB_PATH = os.getenv("DATABASE_URL", "sqlite:///./data/expenses.db")
# Strip the sqlite:/// prefix if present
DB_PATH = DB_PATH.replace("sqlite:///", "")

# Ensure the data directory exists (important in fresh Docker volumes)
os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# ── Step 1: Create all base tables if they don’t exist ────────────────────
# This makes the migration safe on a fresh Docker volume where
# tables haven’t been created yet by on_startup()
cur.executescript("""
CREATE TABLE IF NOT EXISTS user (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    email            TEXT NOT NULL UNIQUE,
    hashed_password  TEXT NOT NULL,
    is_active        INTEGER NOT NULL DEFAULT 1,
    is_admin         INTEGER NOT NULL DEFAULT 0,
    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
    last_login       TEXT
);

CREATE TABLE IF NOT EXISTS fixedexpensetemplate (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    category       TEXT NOT NULL,
    amount         REAL NOT NULL,
    is_active      INTEGER NOT NULL DEFAULT 1,
    sort_order     INTEGER DEFAULT 0,
    template_type  TEXT NOT NULL DEFAULT 'fixed',
    due_day        INTEGER,
    user_id        INTEGER REFERENCES user(id),
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS expense (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    date              TEXT NOT NULL,
    vendor            TEXT NOT NULL,
    amount            REAL NOT NULL,
    category          TEXT NOT NULL,
    note              TEXT,
    is_fixed          INTEGER NOT NULL DEFAULT 0,
    paid              INTEGER NOT NULL DEFAULT 1,
    month_key         TEXT NOT NULL,
    fixed_template_id INTEGER REFERENCES fixedexpensetemplate(id),
    user_id           INTEGER REFERENCES user(id),
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS budgetlimit (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    category      TEXT NOT NULL,
    limit_amount  REAL NOT NULL,
    user_id       INTEGER REFERENCES user(id)
);

CREATE TABLE IF NOT EXISTS incomeentry (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    source     TEXT NOT NULL,
    amount     REAL NOT NULL,
    month_key  TEXT NOT NULL,
    note       TEXT,
    date       TEXT NOT NULL DEFAULT (date('now')),
    user_id    INTEGER REFERENCES user(id)
);

CREATE TABLE IF NOT EXISTS expensetemplate (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    vendor     TEXT NOT NULL,
    category   TEXT NOT NULL,
    amount     REAL NOT NULL,
    is_active  INTEGER NOT NULL DEFAULT 1,
    use_count  INTEGER NOT NULL DEFAULT 0,
    user_id    INTEGER REFERENCES user(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS poolentry (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    pool_template_id  INTEGER NOT NULL REFERENCES fixedexpensetemplate(id),
    month_key         TEXT NOT NULL,
    label             TEXT NOT NULL,
    amount            REAL NOT NULL,
    paid              INTEGER NOT NULL DEFAULT 0,
    paid_date         TEXT,
    note              TEXT,
    created_at        TEXT NOT NULL DEFAULT (datetime('now')),
    user_id           INTEGER REFERENCES user(id)
);
""")
print("✅ Base tables ready")

# ── Step 2: Additive column migrations (safe on existing data) ─────────────
migrations = [
    # FixedExpenseTemplate — add columns if missing
    ("fixedexpensetemplate", "template_type", "TEXT NOT NULL DEFAULT 'fixed'"),
    ("fixedexpensetemplate", "due_day",        "INTEGER"),
    ("fixedexpensetemplate", "user_id",        "INTEGER REFERENCES user(id)"),
    ("fixedexpensetemplate", "created_at",     "TEXT NOT NULL DEFAULT (datetime('now'))"),
    # Expense — add columns if missing
    ("expense",              "user_id",        "INTEGER REFERENCES user(id)"),
    ("expense",              "created_at",     "TEXT NOT NULL DEFAULT (datetime('now'))"),
    # BudgetLimit — add user_id if missing
    ("budgetlimit",          "user_id",        "INTEGER REFERENCES user(id)"),
    # IncomeEntry — add columns if missing
    ("incomeentry",          "user_id",        "INTEGER REFERENCES user(id)"),
    ("incomeentry",          "date",           "TEXT NOT NULL DEFAULT (date('now'))"),
    # ExpenseTemplate — add columns if missing
    ("expensetemplate",      "user_id",        "INTEGER REFERENCES user(id)"),
    ("expensetemplate",      "created_at",     "TEXT NOT NULL DEFAULT (datetime('now'))"),
    # PoolEntry — add user_id if missing
    ("poolentry",            "user_id",        "INTEGER REFERENCES user(id)"),
]

for table, column, col_def in migrations:
    cur.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cur.fetchall()]
    if column not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")
        print(f"✅ Added {table}.{column}")
    else:
        print(f"⏭️  {table}.{column} already exists")

conn.commit()
conn.close()
print("\n✅ Migration complete")
