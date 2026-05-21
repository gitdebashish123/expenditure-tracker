"""
seed_dummy_data.py
──────────────────
Wipes expenses.db and inserts realistic dummy data for
Jan 2024 → Apr 2026 (28 months).

Run from project root:
  uv run python seed_dummy_data.py
"""

import sqlite3, random, calendar
from datetime import date, timedelta
from pathlib import Path

DB_PATH = "./data/expenses.db"
random.seed(42)   # reproducible

# ── Salary by period ──────────────────────────────────────────────────────
def salary_for(month_key: str) -> float:
    if month_key < "2025-05":
        return 135000.0   # pre-May25 (approximate earlier salary)
    elif month_key == "2025-06":
        return 218826.0   # two-month credit
    else:
        return 145399.0

# ── Fixed expense templates ───────────────────────────────────────────────
FIXED_TEMPLATES = [
    # (name, category, amount_fn)  — amount_fn takes month_key → float
    ("Rent",                  "Housing",     lambda m: 16500),
    ("RD1",                   "Savings",     lambda m: 2000),
    ("RD2",                   "Savings",     lambda m: 5000),
    ("RD3",                   "Savings",     lambda m: 5000),
    ("iWish",                 "Savings",     lambda m: 2100),
    ("Car EMI",               "EMI",         lambda m: 16392),
    ("Cook",                  "Household",   lambda m: 4000),
    ("Milk",                  "Household",   lambda m: 945),
    ("Term Insurance",        "Insurance",   lambda m: 2062),
    ("Insurance Platinum",    "Insurance",   lambda m: 7000 if m >= "2025-01" else 0),
    ("Groww MF1",             "Investments", lambda m: 3000),
    ("Groww MF2",             "Investments", lambda m: 5000),
    ("Groww MF3",             "Investments", lambda m: 5000 if m >= "2024-06" else 0),
    ("SBI MF1",               "Investments", lambda m: 2000),
    ("SBI MF2",               "Investments", lambda m: 2000),
    ("Fibre+Mobile",          "Utilities",   lambda m: 2318),
    ("D2H",                   "Utilities",   lambda m: 372),
    ("Electric Bill",         "Utilities",   lambda m: random.randint(800, 1800)),
]

# ── Variable expense pools ────────────────────────────────────────────────
# (vendor, category, min, max, frequency_per_month)
VARIABLE_POOL = [
    # Food
    ("Zomato",        "Food",         200,  900,  5),
    ("Swiggy",        "Food",         150,  700,  3),
    ("Restaurant",    "Food",         300, 1200,  2),
    ("Cafe Coffee",   "Food",         100,  400,  2),
    # Groceries
    ("BigBasket",     "Groceries",    800, 2500,  3),
    ("Blinkit",       "Groceries",    200,  900,  4),
    ("DMart",         "Groceries",    500, 2000,  2),
    ("Zepto",         "Groceries",    150,  600,  3),
    ("JioMart",       "Groceries",    300, 1200,  1),
    # Travel
    ("Ola",           "Travel",       100,  500,  6),
    ("Uber",          "Travel",       120,  600,  4),
    ("Petrol",        "Travel",       500, 1500,  3),
    ("Rapido",        "Travel",        60,  250,  4),
    # Shopping
    ("Amazon",        "Shopping",     300, 3000,  2),
    ("Flipkart",      "Shopping",     200, 2500,  1),
    ("Myntra",        "Shopping",     500, 2000,  1),
    # Medical
    ("Apollo",        "Medical",      200,  800,  1),
    ("Netmeds",       "Medical",      100,  600,  1),
    ("Doctor",        "Medical",      300,  800,  1),
    # Entertainment
    ("Netflix",       "Entertainment",649,  649,  1),
    ("Hotstar",       "Entertainment",299,  299,  1),
    ("PVR",           "Entertainment",300,  900,  1),
    # Gifts
    ("Gift",          "Gifts",        300, 2000,  1),
    # Misc
    ("Haircut",       "Miscellaneous",150,  400,  1),
    ("Laundry",       "Miscellaneous", 80,  300,  2),
]

# ── Months to generate ────────────────────────────────────────────────────
def all_months():
    months = []
    y, m = 2024, 1
    while True:
        months.append(f"{y:04d}-{m:02d}")
        if y == 2026 and m == 4:
            break
        m += 1
        if m > 12:
            m = 1
            y += 1
    return months

# ── Random date within month ──────────────────────────────────────────────
def rand_date(month_key: str) -> str:
    y, m = map(int, month_key.split("-"))
    days = calendar.monthrange(y, m)[1]
    return date(y, m, random.randint(1, days)).isoformat()

# ── Main ──────────────────────────────────────────────────────────────────
def seed():
    Path("data").mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    # ── Wipe all data ──────────────────────────────────────────────────
    print("🗑️  Wiping existing data...")
    cur.executescript("""
        DELETE FROM expense;
        DELETE FROM incomeentry;
        DELETE FROM fixedexpensetemplate;
        DELETE FROM budgetlimit;
    """)
    # Reset autoincrement counters if the table exists
    try:
        cur.executescript("""
            DELETE FROM sqlite_sequence WHERE name IN
                ('expense','incomeentry','fixedexpensetemplate','budgetlimit');
        """)
    except sqlite3.OperationalError:
        pass  # sqlite_sequence doesn't exist yet — fine
    conn.commit()

    # ── Re-seed budget limits ──────────────────────────────────────────
    print("💰 Seeding budget limits...")
    limits = [
        ("Food", 2000), ("Travel", 4000), ("Groceries", 5000),
        ("Shopping", 3000), ("Medical", 5000), ("Entertainment", 2000),
        ("Gifts", 2000), ("Miscellaneous", 5000), ("Course", 3000),
    ]
    cur.executemany(
        "INSERT INTO budgetlimit (category, limit_amount) VALUES (?,?)", limits
    )
    conn.commit()

    # ── Seed fixed templates ───────────────────────────────────────────
    print("🔒 Seeding fixed templates...")
    tmpl_ids = {}
    for i, (name, cat, _) in enumerate(FIXED_TEMPLATES):
        cur.execute(
            "INSERT INTO fixedexpensetemplate (name, category, amount, is_active, sort_order, created_at) "
            "VALUES (?,?,?,1,?,datetime('now'))",
            (name, cat, 0, i)   # amount=0 placeholder; actual per-month amount set on expense row
        )
        tmpl_ids[name] = cur.lastrowid
    conn.commit()

    # ── Generate monthly data ──────────────────────────────────────────
    months = all_months()
    total_exp = 0
    total_inc = 0

    for month_key in months:
        y, m = map(int, month_key.split("-"))
        first_day = date(y, m, 1).isoformat()
        print(f"\n📅 {month_key}", end=" ")

        # Income
        sal = salary_for(month_key)
        cur.execute(
            "INSERT INTO incomeentry (date, source, amount, month_key, note) "
            "VALUES (?,?,?,?,?)",
            (first_day, "Infosys Salary", sal, month_key, "Monthly salary")
        )
        total_inc += 1

        # Fixed expenses
        for name, cat, amt_fn in FIXED_TEMPLATES:
            amt = amt_fn(month_key)
            if amt <= 0:
                continue
            tmpl_id = tmpl_ids[name]
            # Update template amount to latest value
            cur.execute("UPDATE fixedexpensetemplate SET amount=? WHERE id=?", (amt, tmpl_id))
            cur.execute(
                "INSERT INTO expense (date, vendor, amount, category, note, is_fixed, paid, month_key, fixed_template_id, created_at) "
                "VALUES (?,?,?,?,?,1,1,?,?,datetime('now'))",
                (first_day, name, amt, cat, "Fixed expense", month_key, tmpl_id)
            )

        # Variable expenses — pick a random subset each month
        month_variable = []
        for vendor, cat, lo, hi, freq in VARIABLE_POOL:
            # Vary frequency slightly for realism
            actual_freq = max(0, freq + random.randint(-1, 1))
            for _ in range(actual_freq):
                if random.random() < 0.75:  # 75% chance each occurrence happens
                    amt = round(random.randint(lo, hi) / 10) * 10
                    exp_date = rand_date(month_key)
                    month_variable.append((exp_date, vendor, amt, cat, month_key))

        # Insert variable expenses
        for exp_date, vendor, amt, cat, mk in month_variable:
            cur.execute(
                "INSERT INTO expense (date, vendor, amount, category, note, is_fixed, paid, month_key, fixed_template_id, created_at) "
                "VALUES (?,?,?,?,?,0,1,?,NULL,datetime('now'))",
                (exp_date, vendor, amt, cat, "Dummy data", mk)
            )
            total_exp += 1

        conn.commit()
        print(f"✅ {len(month_variable)} variable + {sum(1 for _,_,f in FIXED_TEMPLATES if f(month_key)>0)} fixed")

    conn.close()
    print(f"\n{'='*50}")
    print(f"✅ Seed complete!")
    print(f"   Months     : {len(months)} ({months[0]} → {months[-1]})")
    print(f"   Income rows: {total_inc}")
    print(f"   Var expenses: {total_exp}")

if __name__ == "__main__":
    seed()
