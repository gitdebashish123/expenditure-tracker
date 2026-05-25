"""
migrate_add_user_id.py
──────────────────────
Sprint 2, Commit 2.1 — Schema Migration

Adds user_id FK column to all 6 data tables and assigns existing rows
to the default admin user (id=1).

Run once after Sprint 1 is deployed:
    uv run python migrate_add_user_id.py

Safe to re-run — skips columns that already exist.

Uses only Python stdlib sqlite3 — no SQLModel, no FastAPI, no venv needed.
"""

import sqlite3
import os
import sys

# ── Config ────────────────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "expenses.db")

# Tables that need user_id — in dependency order
MIGRATIONS = [
    ("fixedexpensetemplate", "user_id"),
    ("poolentry",            "user_id"),
    ("expensetemplate",      "user_id"),
    ("expense",              "user_id"),
    ("budgetlimit",          "user_id"),
    ("incomeentry",          "user_id"),
]


def column_exists(cursor, table: str, column: str) -> bool:
    """Return True if a column exists in the given table."""
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def table_exists(cursor, table: str) -> bool:
    """Return True if a table exists in the database."""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    )
    return cursor.fetchone() is not None


def main():
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  SpendSense — Schema Migration")
    print("  Sprint 2, Commit 2.1 — Add user_id FK")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    # ── Check DB exists ───────────────────────────────────────────────────────
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at: {DB_PATH}")
        print("   Start the backend first to create it:")
        print("   uv run uvicorn backend.main:app --port 8000")
        print("   Wait for startup, then Ctrl+C and re-run this script.")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF")   # required for ALTER TABLE on SQLite
    cursor = conn.cursor()

    # ── Verify user table exists ──────────────────────────────────────────────
    if not table_exists(cursor, "user"):
        print("❌ 'user' table not found in database.")
        print("   Start the backend first to auto-create tables and the default admin:")
        print("   uv run uvicorn backend.main:app --port 8000")
        sys.exit(1)

    # ── Find admin user ───────────────────────────────────────────────────────
    cursor.execute("SELECT id, email FROM user WHERE is_admin=1 LIMIT 1")
    admin = cursor.fetchone()

    if not admin:
        print("❌ No admin user found in the database.")
        print("   Start the backend first to auto-create the default admin:")
        print("   uv run uvicorn backend.main:app --port 8000")
        print("   Then re-run this script.")
        sys.exit(1)

    admin_id, admin_email = admin
    print(f"👤 Assigning existing rows to admin: {admin_email} (id={admin_id})")
    print()

    # ── Run migrations ────────────────────────────────────────────────────────
    migrated = 0
    skipped  = 0

    for table, column in MIGRATIONS:

        # Check table exists
        if not table_exists(cursor, table):
            print(f"⚠️  Table '{table}' not found — skipping")
            skipped += 1
            continue

        # Check if column already exists — idempotent
        if column_exists(cursor, table, column):
            print(f"⏭️  {table}.{column} already exists — skipping")
            skipped += 1
            continue

        # Add the column (SQLite advisory FK — enforcement is app-side)
        cursor.execute(
            f"ALTER TABLE {table} ADD COLUMN {column} INTEGER REFERENCES user(id)"
        )

        # Create index for fast per-user queries (Commit 2.2 will use this heavily)
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{table}_{column} ON {table}({column})"
        )

        # Assign all existing rows to the admin user
        cursor.execute(
            f"UPDATE {table} SET {column} = ? WHERE {column} IS NULL",
            (admin_id,)
        )
        affected = cursor.rowcount

        print(f"✅ Migrated {table:<28} — {affected} row(s) assigned to user_id={admin_id}")
        migrated += 1

    conn.commit()
    conn.close()

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    if migrated > 0:
        print(f"✅ Migration complete — {migrated} table(s) updated")
        print(f"   All existing data assigned to: {admin_email}")
    else:
        print("✅ Already up to date — no changes needed")
    print()
    print("   Next steps:")
    print("   1. Start the backend: uv run uvicorn backend.main:app --port 8000")
    print("   2. Verify endpoints still work:")
    print("      curl -X POST http://localhost:8000/auth/login \\")
    print('        -H "Content-Type: application/json" \\')
    print(f'        -d \'{{"email":"{admin_email}","password":"changeme123"}}\'')
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()


if __name__ == "__main__":
    main()
