"""
migrate_schema.py
─────────────────
Adds new columns to existing tables without wiping data.
Run once from project root:
  uv run python migrate_schema.py
"""
import sqlite3

DB_PATH = "./data/expenses.db"
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

migrations = [
    # FixedExpenseTemplate — add template_type and due_day if missing
    ("fixedexpensetemplate", "template_type", "TEXT NOT NULL DEFAULT 'fixed'"),
    ("fixedexpensetemplate", "due_day",        "INTEGER"),
    # PoolEntry — create if not exists (new table)
]

for table, column, col_def in migrations:
    # Check if column already exists
    cur.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cur.fetchall()]
    if column not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")
        print(f"✅ Added {table}.{column}")
    else:
        print(f"⏭️  {table}.{column} already exists")

# Create PoolEntry table if it doesn't exist
cur.executescript("""
CREATE TABLE IF NOT EXISTS poolentry (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    pool_template_id  INTEGER NOT NULL REFERENCES fixedexpensetemplate(id),
    month_key         TEXT NOT NULL,
    label             TEXT NOT NULL,
    amount            REAL NOT NULL,
    paid              INTEGER NOT NULL DEFAULT 0,
    paid_date         TEXT,
    note              TEXT,
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);
""")
print("✅ poolentry table ready")

conn.commit()
conn.close()
print("\n✅ Migration complete — restart the backend now")
