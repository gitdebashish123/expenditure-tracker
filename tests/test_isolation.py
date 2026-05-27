"""
tests/test_isolation.py
────────────────────────
Sprint 2, Commit 2.3 — Data Isolation Test

Black-box integration test against the live API.
Proves that two users cannot see each other's data across all 20+ endpoints.

Prerequisites:
  - Backend running: uv run uvicorn backend.main:app --port 8000
  - Admin user exists (created on first backend startup)

Run:
  uv run python tests/test_isolation.py

Exit codes:
  0 — all tests passed
  1 — one or more tests failed
"""

import requests
import sys
import sqlite3
import os
from datetime import date

BASE_URL = "http://localhost:8000"
DB_PATH  = os.path.join(os.path.dirname(__file__), "..", "data", "expenses.db")
MONTH    = date.today().strftime("%Y-%m")

USER_A = {"email": "test_user_a@isolation.test", "password": "passwordA123"}
USER_B = {"email": "test_user_b@isolation.test", "password": "passwordB123"}

passed   = 0
failed   = 0
failures = []


# ── Helpers ───────────────────────────────────────────────────────────────────

def check(name: str, condition: bool, detail: str = ""):
    """Record a test result and print ✅ or ❌."""
    global passed, failed
    if condition:
        print(f"  ✅ {name}")
        passed += 1
    else:
        msg = f"  ❌ {name}" + (f": {detail}" if detail else "")
        print(msg)
        failures.append(name)
        failed += 1


def h(token: str) -> dict:
    """Return Authorization header dict for a token."""
    return {"Authorization": f"Bearer {token}"}


# ── Cleanup ───────────────────────────────────────────────────────────────────

def cleanup():
    """
    Remove test users and all their data directly from SQLite.
    Uses DB directly since DELETE /auth/account is not yet in Sprint 2
    (that is Sprint 4). Runs in try/finally — always executes.
    """
    print("\n── Cleanup ───────────────────────────────────────────")
    try:
        conn   = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Find test user IDs
        cursor.execute(
            "SELECT id, email FROM user WHERE email IN (?, ?)",
            (USER_A["email"], USER_B["email"])
        )
        users    = cursor.fetchall()
        user_ids = [u[0] for u in users]

        if not user_ids:
            print("  ℹ️  No test users found to clean up")
            conn.close()
            return

        for uid in user_ids:
            # Delete in FK-safe order: dependents first, then user row
            cursor.execute("DELETE FROM poolentry            WHERE user_id = ?", (uid,))
            cursor.execute("DELETE FROM expense              WHERE user_id = ?", (uid,))
            cursor.execute("DELETE FROM expensetemplate      WHERE user_id = ?", (uid,))
            cursor.execute("DELETE FROM fixedexpensetemplate WHERE user_id = ?", (uid,))
            cursor.execute("DELETE FROM incomeentry          WHERE user_id = ?", (uid,))
            cursor.execute("DELETE FROM budgetlimit          WHERE user_id = ?", (uid,))
            cursor.execute("DELETE FROM user                 WHERE id = ?",      (uid,))

        conn.commit()
        conn.close()

        emails = [u[1] for u in users]
        print(f"  ✅ Cleaned up {len(user_ids)} test user(s): {', '.join(emails)}")

    except Exception as e:
        print(f"  ⚠️  Cleanup error: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    global passed, failed

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  SpendSense — Data Isolation Test")
    print("  Sprint 2, Commit 2.3")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    # ── Step 1: Pre-flight check ──────────────────────────────────────────────
    try:
        r = requests.get(f"{BASE_URL}/docs", timeout=5)
        assert r.status_code == 200
    except Exception:
        print("❌ Backend not reachable at http://localhost:8000")
        print("   Start it with: uv run uvicorn backend.main:app --port 8000")
        sys.exit(1)
    print("✅ Backend reachable")

    # Wrap everything in try/finally so cleanup always runs
    try:

        # ── Step 2: Register and login both users ─────────────────────────────
        # Clean up stale test users from any previous failed run first
        cleanup()
        # Reset counters after cleanup-only run
        passed = 0
        failed = 0
        failures.clear()

        r = requests.post(f"{BASE_URL}/auth/register", json=USER_A)
        if r.status_code not in (201, 400):
            print(f"❌ Failed to register User A: {r.status_code} {r.text}")
            sys.exit(1)

        r = requests.post(f"{BASE_URL}/auth/register", json=USER_B)
        if r.status_code not in (201, 400):
            print(f"❌ Failed to register User B: {r.status_code} {r.text}")
            sys.exit(1)

        r = requests.post(f"{BASE_URL}/auth/login", json=USER_A)
        assert r.status_code == 200, f"Login A failed: {r.text}"
        token_a = r.json()["access_token"]

        r = requests.post(f"{BASE_URL}/auth/login", json=USER_B)
        assert r.status_code == 200, f"Login B failed: {r.text}"
        token_b = r.json()["access_token"]

        print("✅ Registered and logged in both test users")

        # ── Step 3: Seed distinct data for each user ──────────────────────────

        # ── User A ────────────────────────────────────────────────────────────
        r = requests.post(f"{BASE_URL}/expenses/manual",
            headers=h(token_a),
            json={"vendor": "UserA_Zomato", "amount": 500,
                  "category": "Food", "expense_date": str(date.today())})
        assert r.status_code == 200, f"User A expense failed: {r.text}"
        expense_a_id = r.json()["expense"]["id"]

        requests.post(f"{BASE_URL}/income",
            headers=h(token_a),
            json={"source": "UserA_Salary", "amount": 100000, "month_key": MONTH})

        requests.put(f"{BASE_URL}/budget",
            headers=h(token_a),
            json={"category": "Food", "limit_amount": 5000})

        r = requests.post(f"{BASE_URL}/fixed-templates",
            headers=h(token_a),
            json={"name": "UserA_Rent", "category": "Housing",
                  "amount": 15000, "template_type": "fixed"})
        assert r.status_code == 200, f"User A fixed template failed: {r.text}"
        template_a_id = r.json()["id"]

        r = requests.post(f"{BASE_URL}/fixed-templates",
            headers=h(token_a),
            json={"name": "UserA_Electric", "category": "Utilities",
                  "amount": 0, "template_type": "pool"})
        assert r.status_code == 200, f"User A pool template failed: {r.text}"
        pool_a_id = r.json()["id"]

        r = requests.post(f"{BASE_URL}/pools/{pool_a_id}/entries/{MONTH}",
            headers=h(token_a),
            json={"label": "UserA_Home", "amount": 800})
        assert r.status_code == 200, f"User A pool entry failed: {r.text}"
        pool_entry_a_id = r.json()["id"]

        r = requests.post(f"{BASE_URL}/expense-templates",
            headers=h(token_a),
            json={"name": "UserA_Petrol", "vendor": "UserA_Petrol",
                  "category": "Travel", "amount": 1000})
        assert r.status_code == 200, f"User A shortcut failed: {r.text}"
        shortcut_a_id = r.json()["id"]

        # ── User B ────────────────────────────────────────────────────────────
        r = requests.post(f"{BASE_URL}/expenses/manual",
            headers=h(token_b),
            json={"vendor": "UserB_Swiggy", "amount": 300,
                  "category": "Food", "expense_date": str(date.today())})
        assert r.status_code == 200, f"User B expense failed: {r.text}"
        expense_b_id = r.json()["expense"]["id"]

        requests.post(f"{BASE_URL}/income",
            headers=h(token_b),
            json={"source": "UserB_Salary", "amount": 80000, "month_key": MONTH})

        requests.put(f"{BASE_URL}/budget",
            headers=h(token_b),
            json={"category": "Food", "limit_amount": 3000})

        r = requests.post(f"{BASE_URL}/fixed-templates",
            headers=h(token_b),
            json={"name": "UserB_Rent", "category": "Housing",
                  "amount": 12000, "template_type": "fixed"})
        assert r.status_code == 200, f"User B fixed template failed: {r.text}"
        template_b_id = r.json()["id"]

        r = requests.post(f"{BASE_URL}/fixed-templates",
            headers=h(token_b),
            json={"name": "UserB_Electric", "category": "Utilities",
                  "amount": 0, "template_type": "pool"})
        assert r.status_code == 200, f"User B pool template failed: {r.text}"
        pool_b_id = r.json()["id"]

        r = requests.post(f"{BASE_URL}/pools/{pool_b_id}/entries/{MONTH}",
            headers=h(token_b),
            json={"label": "UserB_Home", "amount": 600})
        assert r.status_code == 200, f"User B pool entry failed: {r.text}"
        pool_entry_b_id = r.json()["id"]

        r = requests.post(f"{BASE_URL}/expense-templates",
            headers=h(token_b),
            json={"name": "UserB_Coffee", "vendor": "UserB_Coffee",
                  "category": "Food", "amount": 200})
        assert r.status_code == 200, f"User B shortcut failed: {r.text}"
        shortcut_b_id = r.json()["id"]

        print("✅ Seeded data for User A and User B")

        # ── Step 4: Isolation tests ───────────────────────────────────────────

        # 4.1 Expenses
        print("\n── Expenses ──────────────────────────────────────────")

        r = requests.get(f"{BASE_URL}/expenses/{MONTH}", headers=h(token_a))
        vendors_a = [e["vendor"] for e in r.json()]
        check("User A sees only own expenses",
              "UserA_Zomato" in vendors_a and "UserB_Swiggy" not in vendors_a)

        r = requests.get(f"{BASE_URL}/expenses/{MONTH}", headers=h(token_b))
        vendors_b = [e["vendor"] for e in r.json()]
        check("User B sees only own expenses",
              "UserB_Swiggy" in vendors_b and "UserA_Zomato" not in vendors_b)

        r = requests.delete(f"{BASE_URL}/expenses/{expense_a_id}", headers=h(token_b))
        check("User B cannot delete User A's expense",
              r.status_code == 404, f"got {r.status_code}")

        r = requests.patch(f"{BASE_URL}/expenses/{expense_a_id}",
            headers=h(token_b), json={"vendor": "Hacked"})
        check("User B cannot edit User A's expense",
              r.status_code == 404, f"got {r.status_code}")

        # 4.2 Income
        print("\n── Income ────────────────────────────────────────────")

        r = requests.get(f"{BASE_URL}/income/{MONTH}", headers=h(token_a))
        check("User A sees own income",
              r.json().get("source") == "UserA_Salary",
              f"got {r.json().get('source')}")

        r = requests.get(f"{BASE_URL}/income/{MONTH}", headers=h(token_b))
        check("User B sees own income",
              r.json().get("source") == "UserB_Salary",
              f"got {r.json().get('source')}")

        r = requests.get(f"{BASE_URL}/income/check/{MONTH}", headers=h(token_a))
        check("Income check scoped to User A",
              r.json().get("is_set") == True)

        # 4.3 Budgets
        print("\n── Budgets ───────────────────────────────────────────")

        r = requests.get(f"{BASE_URL}/budgets", headers=h(token_a))
        limits_a = {b["category"]: b["limit_amount"] for b in r.json()}
        check("User A's Food limit is 5000",
              limits_a.get("Food") == 5000,
              f"got {limits_a.get('Food')}")

        r = requests.get(f"{BASE_URL}/budgets", headers=h(token_b))
        limits_b = {b["category"]: b["limit_amount"] for b in r.json()}
        check("User B's Food limit is 3000",
              limits_b.get("Food") == 3000,
              f"got {limits_b.get('Food')}")

        check("User A's budgets not visible to User B",
              limits_b.get("Food") != 5000)

        # 4.4 Fixed Templates
        print("\n── Fixed Templates ───────────────────────────────────")

        r = requests.get(f"{BASE_URL}/fixed-templates", headers=h(token_a))
        names_a = [t["name"] for t in r.json()]
        check("User A sees own fixed templates",
              "UserA_Rent" in names_a and "UserB_Rent" not in names_a)

        r = requests.get(f"{BASE_URL}/fixed-templates", headers=h(token_b))
        names_b = [t["name"] for t in r.json()]
        check("User B sees own fixed templates",
              "UserB_Rent" in names_b and "UserA_Rent" not in names_b)

        r = requests.put(f"{BASE_URL}/fixed-templates/{template_a_id}",
            headers=h(token_b), json={"name": "Hacked"})
        check("User B cannot update User A's template",
              r.status_code == 404, f"got {r.status_code}")

        r = requests.delete(f"{BASE_URL}/fixed-templates/{template_a_id}",
            headers=h(token_b))
        check("User B cannot delete User A's template",
              r.status_code == 404, f"got {r.status_code}")

        # 4.5 Fixed Expenses (Seeded)
        print("\n── Fixed Expenses (Seeded) ───────────────────────────")

        r = requests.get(f"{BASE_URL}/fixed/{MONTH}", headers=h(token_a))
        fixed_vendors_a = [e["vendor"] for e in r.json()]
        check("User A's fixed expenses are seeded",
              "UserA_Rent" in fixed_vendors_a)

        r = requests.get(f"{BASE_URL}/fixed/{MONTH}", headers=h(token_b))
        fixed_vendors_b = [e["vendor"] for e in r.json()]
        check("User B's fixed expenses are seeded",
              "UserB_Rent" in fixed_vendors_b)

        check("User A's fixed expenses not in User B's list",
              "UserA_Rent" not in fixed_vendors_b)

        # 4.6 Pool Entries
        print("\n── Pool Entries ──────────────────────────────────────")

        r = requests.get(f"{BASE_URL}/pools/{MONTH}", headers=h(token_a))
        pool_names_a = [p["name"] for p in r.json()]
        check("User A sees own pool templates",
              "UserA_Electric" in pool_names_a and "UserB_Electric" not in pool_names_a)

        r = requests.get(f"{BASE_URL}/pools/{MONTH}", headers=h(token_b))
        pool_names_b = [p["name"] for p in r.json()]
        check("User B sees own pool templates",
              "UserB_Electric" in pool_names_b and "UserA_Electric" not in pool_names_b)

        r = requests.patch(f"{BASE_URL}/pools/entries/{pool_entry_a_id}/toggle",
            headers=h(token_b))
        check("User B cannot toggle User A's pool entry",
              r.status_code == 404, f"got {r.status_code}")

        r = requests.delete(f"{BASE_URL}/pools/entries/{pool_entry_a_id}",
            headers=h(token_b))
        check("User B cannot delete User A's pool entry",
              r.status_code == 404, f"got {r.status_code}")

        # 4.7 Expense Shortcuts
        print("\n── Expense Shortcuts ─────────────────────────────────")

        r = requests.get(f"{BASE_URL}/expense-templates", headers=h(token_a))
        shortcut_names_a = [t["name"] for t in r.json()]
        check("User A sees own shortcuts",
              "UserA_Petrol" in shortcut_names_a and "UserB_Coffee" not in shortcut_names_a)

        r = requests.get(f"{BASE_URL}/expense-templates", headers=h(token_b))
        shortcut_names_b = [t["name"] for t in r.json()]
        check("User B sees own shortcuts",
              "UserB_Coffee" in shortcut_names_b and "UserA_Petrol" not in shortcut_names_b)

        r = requests.post(f"{BASE_URL}/expense-templates/{shortcut_a_id}/log",
            headers=h(token_b))
        check("User B cannot log from User A's shortcut",
              r.status_code == 404, f"got {r.status_code}")

        r = requests.delete(f"{BASE_URL}/expense-templates/{shortcut_a_id}",
            headers=h(token_b))
        check("User B cannot delete User A's shortcut",
              r.status_code == 404, f"got {r.status_code}")

        # 4.8 Summary & Insights
        print("\n── Summary & Insights ────────────────────────────────")

        r = requests.get(f"{BASE_URL}/summary/{MONTH}", headers=h(token_a))
        bal_a = r.json()["balance"]
        check("User A's summary shows own income (100000)",
              bal_a["total_income"] == 100000,
              f"got {bal_a['total_income']}")

        r = requests.get(f"{BASE_URL}/summary/{MONTH}", headers=h(token_b))
        bal_b = r.json()["balance"]
        check("User B's summary shows own income (80000)",
              bal_b["total_income"] == 80000,
              f"got {bal_b['total_income']}")

        check("User B's summary does not include User A's income",
              bal_b["total_income"] != 100000)

        r = requests.get(f"{BASE_URL}/months", headers=h(token_a))
        check("User A's months list is non-empty",
              isinstance(r.json(), list) and len(r.json()) > 0)

        r = requests.get(f"{BASE_URL}/insights/top-spends/{MONTH}", headers=h(token_a))
        top_vendors_a = [t["vendor"] for t in r.json()]
        check("User A's top spends contains own data",
              "UserA_Zomato" in top_vendors_a)
        check("User A's top spends excludes User B's data",
              "UserB_Swiggy" not in top_vendors_a)

        r = requests.get(f"{BASE_URL}/insights/mom/{MONTH}", headers=h(token_a))
        check("MoM insights returns valid structure for User A",
              "months" in r.json() and "categories" in r.json())

    except AssertionError as e:
        print(f"\n❌ Unexpected assertion failure: {e}")
        failed += 1
        failures.append(str(e))

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        failed += 1
        failures.append(str(e))

    finally:
        # Always clean up — even on unexpected error
        cleanup()

    # ── Summary ───────────────────────────────────────────────────────────────
    total = passed + failed
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    if failed == 0:
        print(f"  ✅ ALL {total} TESTS PASSED — Data isolation is working correctly")
    else:
        print(f"  ❌ {failed}/{total} TESTS FAILED")
        for f in failures:
            print(f"     • {f}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
