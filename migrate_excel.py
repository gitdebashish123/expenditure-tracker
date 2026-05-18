"""
Migration script: monthly_expenditure.xlsx → expenses.db
Reads all monthly sheets and inserts Expense + IncomeEntry rows.
Safe to re-run — skips months already present in the DB.
"""
import sqlite3
import pandas as pd
from datetime import date
from pathlib import Path

EXCEL_PATH = "/Users/debashish/Desktop/ai-projects/expenditure-tracker/monthly_expenditure.xlsx"
# DB path will be passed as argument or default
import sys
DB_PATH = sys.argv[1] if len(sys.argv) > 1 else "./data/expenses.db"

# ── Sheet → month_key mapping ─────────────────────────────────────────────
SHEET_MONTH_MAP = {
    "May25":    ("2025-05", 146709),
    "June25":   ("2025-06", 218826),   # two-month salary per sheet
    "July25":   ("2025-07", 145399),
    "Aug25":    ("2025-08", 145399),
    "Sept25":   ("2025-09", 145399),
    "Oct25":    ("2025-10", 145399),
    "Dec25":    ("2025-12", 145399),
    "Jan26":    ("2026-01", 145399),
    "Feb26":    ("2026-02", 145399),
    "April 26": ("2026-04", 145399),
}

# ── Category mapping from vendor/row name → our category system ───────────
def infer_category(name: str, is_fixed: bool) -> str:
    n = name.lower().strip()
    if any(x in n for x in ["rent"]):                          return "Housing"
    if any(x in n for x in ["rd", "iwish", "fd"]):             return "Savings"
    if any(x in n for x in ["car emi", "credit emi"]):         return "EMI"
    if any(x in n for x in ["groww", "sbi mf"]):               return "Investments"
    if any(x in n for x in ["term insurance", "insurance"]):   return "Insurance"
    if any(x in n for x in ["cook", "milk"]):                  return "Household"
    if any(x in n for x in ["fibre", "mobile recharge", "d2h"]): return "Utilities"
    if any(x in n for x in ["electric", "electic"]):           return "Utilities"
    if any(x in n for x in ["grocery", "groceries", "bigbasket", "blinkit", "zepto", "jiomart", "jio mart", "instamart", "grofers", "dmart"]): return "Groceries"
    if any(x in n for x in ["petrol", "fuel", "ola", "uber", "travel"]): return "Travel"
    if any(x in n for x in ["food", "zomato", "pizza", "sweets"]): return "Food"
    if any(x in n for x in ["medical", "doctor", "pharmacy", "medicine"]): return "Medical"
    if any(x in n for x in ["course", "udemy", "learning"]):  return "Course"
    if any(x in n for x in ["gift"]):                          return "Gifts"
    if any(x in n for x in ["entertainment", "movie", "netflix"]): return "Entertainment"
    if any(x in n for x in ["shopping", "amazon", "flipkart"]): return "Shopping"
    if is_fixed:                                                return "Household"
    return "Miscellaneous"

# Fixed expense row names (rows 2-21 in sheets, col 0)
FIXED_NAMES = {
    "rent", "rd1", "rd2", "rd3", "rd3 ( new )", "rd4 ( new )",
    "car emi", "credit emi",
    "cook", "milk",
    "term insurance", "insurance(platinum)",
    "groww mf1", "groww mf2", "groww mf3 ( new )", "groww mf4 ( new )",
    "sbi mf1", "sbi mf2",
    "fibre recharge", "fibre + mobile recharge",
    "d2h", "electic bill", "electric bill",
    "other1", "other2",
    "iwish",
}

def is_fixed_row(name: str) -> bool:
    return name.lower().strip() in FIXED_NAMES

# Rows to completely skip (summary/metadata rows)
SKIP_NAMES = {
    "expenditure calculator", "categories", "expected  expenditure",
    "actual  expenditure", "total salary", "remaining",
    "before rd & iwish break", "after rd and iWish withdrawal",
    "total medical expenditure", "rd + iwish", "send to sbi",
    "send to sbi", "send hdfc", "send sbi", "receive sbi",
    "sub total", "total", "", "nan",
}

def parse_sheet(df: pd.DataFrame, month_key: str):
    """Parse one monthly sheet → list of expense dicts."""
    expenses = []
    year, month = map(int, month_key.split("-"))
    exp_date = date(year, month, 1)

    for _, row in df.iterrows():
        name = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        actual = row.iloc[2] if len(row) > 2 else None
        comment = str(row.iloc[3]).strip() if len(row) > 3 and pd.notna(row.iloc[3]) else ""

        # Skip empty, summary, or metadata rows
        if not name or name.lower() in SKIP_NAMES or name.startswith("NaN"):
            continue
        # Skip rows with no actual amount or zero amount
        if pd.isna(actual) or actual == 0:
            continue
        try:
            amount = float(actual)
        except (ValueError, TypeError):
            continue
        if amount <= 0:
            continue

        fixed = is_fixed_row(name)
        paid = comment.lower() in ("completed", "inprogress") if comment else fixed

        # Clean up vendor name
        vendor = name.strip().title()
        vendor = vendor.replace("( New )", "").replace("(New)", "").strip()
        vendor = vendor.replace("Electic Bill", "Electric Bill")
        vendor = vendor.replace("Fibre + Mobile Recharge", "Fibre+Mobile")
        vendor = vendor.replace("Insurance(Platinum)", "Insurance Platinum")

        category = infer_category(name, fixed)

        expenses.append({
            "date": exp_date.isoformat(),
            "vendor": vendor,
            "amount": amount,
            "category": category,
            "is_fixed": fixed,
            "paid": paid,
            "month_key": month_key,
            "note": f"Imported from Excel ({comment})" if comment else "Imported from Excel",
        })

    return expenses


def migrate():
    xl = pd.ExcelFile(EXCEL_PATH)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    total_inserted = 0
    total_income = 0
    skipped_months = []

    for sheet_name, (month_key, salary) in SHEET_MONTH_MAP.items():
        # Check if month already has data
        cur.execute("SELECT COUNT(*) FROM expense WHERE month_key = ?", (month_key,))
        count = cur.fetchone()[0]
        if count > 0:
            print(f"⏭️  {month_key} already has {count} rows — skipping")
            skipped_months.append(month_key)
            continue

        print(f"\n📅 Processing {sheet_name} → {month_key}")
        df = pd.read_excel(xl, sheet_name=sheet_name, header=None)
        expenses = parse_sheet(df, month_key)

        inserted = 0
        for e in expenses:
            cur.execute("""
                INSERT INTO expense
                    (date, vendor, amount, category, note, is_fixed, paid, month_key, fixed_template_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, datetime('now'))
            """, (e["date"], e["vendor"], e["amount"], e["category"],
                  e["note"], e["is_fixed"], e["paid"], e["month_key"]))
            inserted += 1
            print(f"   {'🔒' if e['is_fixed'] else '💸'} {e['vendor']:30s} ₹{e['amount']:>8,.0f}  [{e['category']}]  {'✅' if e['paid'] else '⬜'}")

        # Insert income entry
        cur.execute("SELECT COUNT(*) FROM incomeentry WHERE month_key = ?", (month_key,))
        if cur.fetchone()[0] == 0:
            cur.execute("""
                INSERT INTO incomeentry (date, source, amount, month_key, note)
                VALUES (?, 'Infosys Salary', ?, ?, 'Imported from Excel')
            """, (f"{month_key}-01", salary, month_key))
            total_income += 1
            print(f"   💰 Income: ₹{salary:,}")

        conn.commit()
        total_inserted += inserted
        print(f"   ✅ {inserted} expenses inserted")

    conn.close()
    print(f"\n{'='*50}")
    print(f"✅ Migration complete!")
    print(f"   Months processed : {len(SHEET_MONTH_MAP) - len(skipped_months)}")
    print(f"   Months skipped   : {len(skipped_months)} {skipped_months}")
    print(f"   Expenses inserted: {total_inserted}")
    print(f"   Income entries   : {total_income}")

if __name__ == "__main__":
    migrate()
