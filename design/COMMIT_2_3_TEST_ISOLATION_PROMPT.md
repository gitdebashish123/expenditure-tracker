# SpendSense — Commit 2.3 Implementation Prompt
## Sprint 2 — Data Isolation: Test Data Isolation

Reference: `design/MULTI_USER_ROADMAP.md` → Sprint 2, Commit 2.3

---

## Context

Commits 2.1 and 2.2 added `user_id` to all tables and scoped every query.
Commit 2.3 proves it works — with a standalone test script that:

1. Creates two test users via the live API
2. Adds distinct data for each user (expenses, income, budgets, fixed
   templates, pool templates, expense shortcuts)
3. Verifies each user sees only their own data across all 20+ endpoints
4. Verifies cross-user access attempts return 404, not the other user's data
5. Cleans up all test data after completion
6. Prints a clear PASS / FAIL summary

This is a **black-box integration test** — it calls the live HTTP API, not
internal Python functions. No pytest, no unittest, no mocking. Just
`requests` against a running backend.

**Project root:** `/Users/debashish/Desktop/ai-projects/expenditure-tracker`  
**File to create:** `tests/test_isolation.py`  
**Run with:** `uv run python tests/test_isolation.py`  
**Requires:** Backend running on `http://localhost:8000`

---

## Setup Requirements

Create the `tests/` directory at the project root.
Add a `tests/__init__.py` (empty) so it is a proper package.

The test script must:
- Use only `requests` (already in dependencies) and Python stdlib
- Not import from `backend/` — it tests the API as a black box
- Be runnable with a single command
- Print clear output for each test: `✅ PASS` or `❌ FAIL: <reason>`
- Exit with code 0 if all tests pass, code 1 if any fail
- Clean up all created test data even if tests fail (use try/finally)

---

## Test Users

```python
USER_A = {"email": "test_user_a@isolation.test", "password": "passwordA123"}
USER_B = {"email": "test_user_b@isolation.test", "password": "passwordB123"}
BASE_URL = "http://localhost:8000"
```

These are throwaway test accounts. The cleanup step deletes all data
associated with them directly in the SQLite DB after the test run,
since there is no `DELETE /auth/account` endpoint yet (Sprint 4).

---

## Script Structure

```python
"""
tests/test_isolation.py
────────────────────────
Sprint 2, Commit 2.3 — Data Isolation Test

Black-box integration test against the live API.
Proves that two users cannot see each other's data.

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

BASE_URL  = "http://localhost:8000"
DB_PATH   = os.path.join(os.path.dirname(__file__), "..", "data", "expenses.db")
MONTH     = date.today().strftime("%Y-%m")

USER_A = {"email": "test_user_a@isolation.test", "password": "passwordA123"}
USER_B = {"email": "test_user_b@isolation.test", "password": "passwordB123"}

passed = 0
failed = 0
failures = []


def check(name: str, condition: bool, detail: str = ""):
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


def cleanup():
    """Remove test users and all their data directly from SQLite."""
    ...


def main():
    ...


if __name__ == "__main__":
    main()
```

---

## Step 1 — Pre-flight Check

Before creating users, verify the backend is reachable:

```python
try:
    r = requests.get(f"{BASE_URL}/docs", timeout=5)
    assert r.status_code == 200
except Exception:
    print("❌ Backend not reachable at http://localhost:8000")
    print("   Start it with: uv run uvicorn backend.main:app --port 8000")
    sys.exit(1)
print("✅ Backend reachable")
```

---

## Step 2 — Register and Login Both Users

```python
# Register User A
r = requests.post(f"{BASE_URL}/auth/register", json=USER_A)
# Handle case where test user already exists from a previous failed run
if r.status_code not in (201, 400):
    print(f"❌ Failed to register User A: {r.status_code} {r.text}")
    sys.exit(1)

# Register User B
r = requests.post(f"{BASE_URL}/auth/register", json=USER_B)
if r.status_code not in (201, 400):
    print(f"❌ Failed to register User B: {r.status_code} {r.text}")
    sys.exit(1)

# Login User A
r = requests.post(f"{BASE_URL}/auth/login", json=USER_A)
assert r.status_code == 200, f"Login A failed: {r.text}"
token_a = r.json()["access_token"]

# Login User B
r = requests.post(f"{BASE_URL}/auth/login", json=USER_B)
assert r.status_code == 200, f"Login B failed: {r.text}"
token_b = r.json()["access_token"]

print(f"✅ Registered and logged in both test users")
```

---

## Step 3 — Seed Distinct Data for Each User

Seed enough data to test every category of endpoint.

### User A data:
```python
# Variable expense
r = requests.post(f"{BASE_URL}/expenses/manual",
    headers=h(token_a),
    json={"vendor": "UserA_Zomato", "amount": 500,
          "category": "Food", "expense_date": str(date.today())})
expense_a_id = r.json()["expense"]["id"]

# Income
requests.post(f"{BASE_URL}/income",
    headers=h(token_a),
    json={"source": "UserA_Salary", "amount": 100000, "month_key": MONTH})

# Budget limit
requests.put(f"{BASE_URL}/budget",
    headers=h(token_a),
    json={"category": "Food", "limit_amount": 5000})

# Fixed template
r = requests.post(f"{BASE_URL}/fixed-templates",
    headers=h(token_a),
    json={"name": "UserA_Rent", "category": "Housing",
          "amount": 15000, "template_type": "fixed"})
template_a_id = r.json()["id"]

# Pool template
r = requests.post(f"{BASE_URL}/fixed-templates",
    headers=h(token_a),
    json={"name": "UserA_Electric", "category": "Utilities",
          "amount": 0, "template_type": "pool"})
pool_a_id = r.json()["id"]

# Pool entry
r = requests.post(f"{BASE_URL}/pools/{pool_a_id}/entries/{MONTH}",
    headers=h(token_a),
    json={"label": "UserA_Home", "amount": 800})
pool_entry_a_id = r.json()["id"]

# Expense shortcut (template)
r = requests.post(f"{BASE_URL}/expense-templates",
    headers=h(token_a),
    json={"name": "UserA_Petrol", "vendor": "UserA_Petrol",
          "category": "Travel", "amount": 1000})
shortcut_a_id = r.json()["id"]
```

### User B data (same structure, different values):
```python
# Variable expense
r = requests.post(f"{BASE_URL}/expenses/manual",
    headers=h(token_b),
    json={"vendor": "UserB_Swiggy", "amount": 300,
          "category": "Food", "expense_date": str(date.today())})
expense_b_id = r.json()["expense"]["id"]

# Income
requests.post(f"{BASE_URL}/income",
    headers=h(token_b),
    json={"source": "UserB_Salary", "amount": 80000, "month_key": MONTH})

# Budget limit
requests.put(f"{BASE_URL}/budget",
    headers=h(token_b),
    json={"category": "Food", "limit_amount": 3000})

# Fixed template
r = requests.post(f"{BASE_URL}/fixed-templates",
    headers=h(token_b),
    json={"name": "UserB_Rent", "category": "Housing",
          "amount": 12000, "template_type": "fixed"})
template_b_id = r.json()["id"]

# Pool template
r = requests.post(f"{BASE_URL}/fixed-templates",
    headers=h(token_b),
    json={"name": "UserB_Electric", "category": "Utilities",
          "amount": 0, "template_type": "pool"})
pool_b_id = r.json()["id"]

# Pool entry
r = requests.post(f"{BASE_URL}/pools/{pool_b_id}/entries/{MONTH}",
    headers=h(token_b),
    json={"label": "UserB_Home", "amount": 600})
pool_entry_b_id = r.json()["id"]

# Expense shortcut
r = requests.post(f"{BASE_URL}/expense-templates",
    headers=h(token_b),
    json={"name": "UserB_Coffee", "vendor": "UserB_Coffee",
          "category": "Food", "amount": 200})
shortcut_b_id = r.json()["id"]
```

---

## Step 4 — Isolation Tests

Run all checks grouped by endpoint category. Each check uses one user's
token to access or attempt to access the other user's data.

### 4.1 Expense Isolation
```python
print("\n── Expenses ──────────────────────────────────────────")

# User A's expense list contains only UserA_Zomato
r = requests.get(f"{BASE_URL}/expenses/{MONTH}", headers=h(token_a))
vendors_a = [e["vendor"] for e in r.json()]
check("User A sees only own expenses",
      "UserA_Zomato" in vendors_a and "UserB_Swiggy" not in vendors_a)

# User B's expense list contains only UserB_Swiggy
r = requests.get(f"{BASE_URL}/expenses/{MONTH}", headers=h(token_b))
vendors_b = [e["vendor"] for e in r.json()]
check("User B sees only own expenses",
      "UserB_Swiggy" in vendors_b and "UserA_Zomato" not in vendors_b)

# User B cannot delete User A's expense
r = requests.delete(f"{BASE_URL}/expenses/{expense_a_id}", headers=h(token_b))
check("User B cannot delete User A's expense",
      r.status_code == 404, f"got {r.status_code}")

# User B cannot edit User A's expense
r = requests.patch(f"{BASE_URL}/expenses/{expense_a_id}",
    headers=h(token_b), json={"vendor": "Hacked"})
check("User B cannot edit User A's expense",
      r.status_code == 404, f"got {r.status_code}")
```

### 4.2 Income Isolation
```python
print("\n── Income ────────────────────────────────────────────")

r = requests.get(f"{BASE_URL}/income/{MONTH}", headers=h(token_a))
check("User A sees own income",
      r.json()["source"] == "UserA_Salary")

r = requests.get(f"{BASE_URL}/income/{MONTH}", headers=h(token_b))
check("User B sees own income",
      r.json()["source"] == "UserB_Salary")

r = requests.get(f"{BASE_URL}/income/check/{MONTH}", headers=h(token_a))
check("Income check scoped to User A", r.json()["is_set"] == True)
```

### 4.3 Budget Isolation
```python
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
```

### 4.4 Fixed Templates Isolation
```python
print("\n── Fixed Templates ───────────────────────────────────")

r = requests.get(f"{BASE_URL}/fixed-templates", headers=h(token_a))
names_a = [t["name"] for t in r.json()]
check("User A sees own fixed templates",
      "UserA_Rent" in names_a and "UserB_Rent" not in names_a)

r = requests.get(f"{BASE_URL}/fixed-templates", headers=h(token_b))
names_b = [t["name"] for t in r.json()]
check("User B sees own fixed templates",
      "UserB_Rent" in names_b and "UserA_Rent" not in names_b)

# User B cannot update User A's template
r = requests.put(f"{BASE_URL}/fixed-templates/{template_a_id}",
    headers=h(token_b), json={"name": "Hacked"})
check("User B cannot update User A's template",
      r.status_code == 404, f"got {r.status_code}")

# User B cannot delete User A's template
r = requests.delete(f"{BASE_URL}/fixed-templates/{template_a_id}",
    headers=h(token_b))
check("User B cannot delete User A's template",
      r.status_code == 404, f"got {r.status_code}")
```

### 4.5 Fixed Expenses (Seeded) Isolation
```python
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
```

### 4.6 Pool Entries Isolation
```python
print("\n── Pool Entries ──────────────────────────────────────")

r = requests.get(f"{BASE_URL}/pools/{MONTH}", headers=h(token_a))
pool_names_a = [p["name"] for p in r.json()]
check("User A sees own pool templates",
      "UserA_Electric" in pool_names_a and "UserB_Electric" not in pool_names_a)

r = requests.get(f"{BASE_URL}/pools/{MONTH}", headers=h(token_b))
pool_names_b = [p["name"] for p in r.json()]
check("User B sees own pool templates",
      "UserB_Electric" in pool_names_b and "UserA_Electric" not in pool_names_b)

# User B cannot toggle User A's pool entry
r = requests.patch(f"{BASE_URL}/pools/entries/{pool_entry_a_id}/toggle",
    headers=h(token_b))
check("User B cannot toggle User A's pool entry",
      r.status_code == 404, f"got {r.status_code}")

# User B cannot delete User A's pool entry
r = requests.delete(f"{BASE_URL}/pools/entries/{pool_entry_a_id}",
    headers=h(token_b))
check("User B cannot delete User A's pool entry",
      r.status_code == 404, f"got {r.status_code}")
```

### 4.7 Expense Shortcuts Isolation
```python
print("\n── Expense Shortcuts ─────────────────────────────────")

r = requests.get(f"{BASE_URL}/expense-templates", headers=h(token_a))
shortcut_names_a = [t["name"] for t in r.json()]
check("User A sees own shortcuts",
      "UserA_Petrol" in shortcut_names_a and "UserB_Coffee" not in shortcut_names_a)

r = requests.get(f"{BASE_URL}/expense-templates", headers=h(token_b))
shortcut_names_b = [t["name"] for t in r.json()]
check("User B sees own shortcuts",
      "UserB_Coffee" in shortcut_names_b and "UserA_Petrol" not in shortcut_names_b)

# User B cannot log from User A's shortcut
r = requests.post(f"{BASE_URL}/expense-templates/{shortcut_a_id}/log",
    headers=h(token_b))
check("User B cannot log from User A's shortcut",
      r.status_code == 404, f"got {r.status_code}")

# User B cannot delete User A's shortcut
r = requests.delete(f"{BASE_URL}/expense-templates/{shortcut_a_id}",
    headers=h(token_b))
check("User B cannot delete User A's shortcut",
      r.status_code == 404, f"got {r.status_code}")
```

### 4.8 Summary & Insights Isolation
```python
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

# Months list is scoped
r = requests.get(f"{BASE_URL}/months", headers=h(token_a))
check("User A's months list is non-empty",
      isinstance(r.json(), list) and len(r.json()) > 0)

# Top spends isolation
r = requests.get(f"{BASE_URL}/insights/top-spends/{MONTH}", headers=h(token_a))
top_vendors_a = [t["vendor"] for t in r.json()]
check("User A's top spends contains own data",
      "UserA_Zomato" in top_vendors_a)
check("User A's top spends excludes User B's data",
      "UserB_Swiggy" not in top_vendors_a)

# MoM insights isolation
r = requests.get(f"{BASE_URL}/insights/mom/{MONTH}", headers=h(token_a))
check("MoM insights returns valid structure for User A",
      "months" in r.json() and "categories" in r.json())
```

---

## Step 5 — Cleanup Function

```python
def cleanup(token_a: str, token_b: str):
    """
    Remove all test data. Uses SQLite directly since DELETE /auth/account
    is not yet implemented (Sprint 4).
    Runs in try/finally so it always executes even if tests fail.
    """
    print("\n── Cleanup ───────────────────────────────────────────")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get test user IDs
        cursor.execute(
            "SELECT id, email FROM user WHERE email IN (?, ?)",
            (USER_A["email"], USER_B["email"])
        )
        users = cursor.fetchall()
        user_ids = [u[0] for u in users]

        if not user_ids:
            print("  ℹ️  No test users found to clean up")
            conn.close()
            return

        for uid in user_ids:
            # Delete all data tables in FK-safe order
            cursor.execute("DELETE FROM poolentry WHERE user_id = ?",        (uid,))
            cursor.execute("DELETE FROM expense WHERE user_id = ?",           (uid,))
            cursor.execute("DELETE FROM expensetemplate WHERE user_id = ?",   (uid,))
            cursor.execute("DELETE FROM fixedexpensetemplate WHERE user_id = ?", (uid,))
            cursor.execute("DELETE FROM incomeentry WHERE user_id = ?",       (uid,))
            cursor.execute("DELETE FROM budgetlimit WHERE user_id = ?",       (uid,))
            cursor.execute("DELETE FROM user WHERE id = ?",                   (uid,))

        conn.commit()
        conn.close()

        emails = [u[1] for u in users]
        print(f"  ✅ Cleaned up {len(user_ids)} test user(s): {', '.join(emails)}")

    except Exception as e:
        print(f"  ⚠️  Cleanup error: {e}")
```

---

## Step 6 — Main Function and Summary

```python
def main():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  SpendSense — Data Isolation Test")
    print("  Sprint 2, Commit 2.3")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    token_a = None
    token_b = None

    try:
        # pre-flight, register, login, seed, test (Steps 1–4)
        ...

    finally:
        # Always clean up, even on unexpected failure
        if token_a or token_b:
            cleanup(token_a, token_b)
        else:
            # tokens never obtained — clean up by email directly
            cleanup("", "")

    # Summary
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
```

---

## Files Created in This Commit

| File | Description |
|---|---|
| `tests/__init__.py` | Empty — makes `tests/` a Python package |
| `tests/test_isolation.py` | Full isolation test script (~250 lines) |

### Files NOT changed
- `backend/main.py` — no changes
- `backend/models.py` — no changes
- `backend/budget_rules.py` — no changes
- `frontend/app.py` — no changes
- Any `.env` or config files

---

## Expected Output When All Tests Pass

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  SpendSense — Data Isolation Test
  Sprint 2, Commit 2.3
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Backend reachable
✅ Registered and logged in both test users
✅ Seeded data for User A and User B

── Expenses ──────────────────────────────────────────
  ✅ User A sees only own expenses
  ✅ User B sees only own expenses
  ✅ User B cannot delete User A's expense
  ✅ User B cannot edit User A's expense

── Income ────────────────────────────────────────────
  ✅ User A sees own income
  ✅ User B sees own income
  ✅ Income check scoped to User A

── Budgets ───────────────────────────────────────────
  ✅ User A's Food limit is 5000
  ✅ User B's Food limit is 3000
  ✅ User A's budgets not visible to User B

── Fixed Templates ───────────────────────────────────
  ✅ User A sees own fixed templates
  ✅ User B sees own fixed templates
  ✅ User B cannot update User A's template
  ✅ User B cannot delete User A's template

── Fixed Expenses (Seeded) ───────────────────────────
  ✅ User A's fixed expenses are seeded
  ✅ User B's fixed expenses are seeded
  ✅ User A's fixed expenses not in User B's list

── Pool Entries ──────────────────────────────────────
  ✅ User A sees own pool templates
  ✅ User B sees own pool templates
  ✅ User B cannot toggle User A's pool entry
  ✅ User B cannot delete User A's pool entry

── Expense Shortcuts ─────────────────────────────────
  ✅ User A sees own shortcuts
  ✅ User B sees own shortcuts
  ✅ User B cannot log from User A's shortcut
  ✅ User B cannot delete User A's shortcut

── Summary & Insights ────────────────────────────────
  ✅ User A's summary shows own income (100000)
  ✅ User B's summary shows own income (80000)
  ✅ User B's summary does not include User A's income
  ✅ User A's months list is non-empty
  ✅ User A's top spends contains own data
  ✅ User A's top spends excludes User B's data
  ✅ MoM insights returns valid structure for User A

── Cleanup ───────────────────────────────────────────
  ✅ Cleaned up 2 test user(s): test_user_a@isolation.test, test_user_b@isolation.test

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅ ALL 30 TESTS PASSED — Data isolation is working correctly
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## How to Run

```bash
cd /Users/debashish/Desktop/ai-projects/expenditure-tracker

# Ensure backend is running
uv run uvicorn backend.main:app --port 8000 &

# Run the test
uv run python tests/test_isolation.py

# Stop the background backend when done
pkill -f "uvicorn backend.main:app"
```

---

## Re-run Safety

The script is safe to re-run multiple times:
- If test users already exist from a previous run, registration returns 400
  (email already registered) which the script handles gracefully
- The cleanup step removes test users by email, so stale data from a
  previous failed run is always cleared before new data is seeded

---

*Last updated: May 2026*
*Owner: Debashish*
*Status: Prompt ready — awaiting execution approval*
