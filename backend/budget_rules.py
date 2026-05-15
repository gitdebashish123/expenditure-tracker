from sqlmodel import Session, select
from backend.models import Expense, BudgetLimit, IncomeEntry
from datetime import date
import yaml

with open("config.yaml") as f:
    config = yaml.safe_load(f)


def get_month_key(d: date = None) -> str:
    d = d or date.today()
    return d.strftime("%Y-%m")


def get_monthly_spent_by_category(session: Session, month_key: str) -> dict[str, float]:
    expenses = session.exec(
        select(Expense).where(Expense.month_key == month_key)
    ).all()
    totals = {}
    for e in expenses:
        totals[e.category] = totals.get(e.category, 0) + e.amount
    return totals


def get_budget_limits(session: Session) -> dict[str, float]:
    limits = session.exec(select(BudgetLimit)).all()
    if limits:
        return {bl.category: bl.limit_amount for bl in limits}
    # Fall back to config defaults
    return config.get("budget_limits", {})


def check_budget_warnings(session: Session, month_key: str) -> list[dict]:
    spent = get_monthly_spent_by_category(session, month_key)
    limits = get_budget_limits(session)
    warnings = []

    for category, limit in limits.items():
        cat_spent = spent.get(category, 0)
        if limit <= 0:
            continue
        pct = cat_spent / limit * 100
        if pct >= 100:
            warnings.append({
                "category": category,
                "spent": cat_spent,
                "limit": limit,
                "pct": pct,
                "level": "danger",
                "message": f"🚨 {category} limit exceeded! ₹{cat_spent:,.0f} / ₹{limit:,.0f}"
            })
        elif pct >= 80:
            warnings.append({
                "category": category,
                "spent": cat_spent,
                "limit": limit,
                "pct": pct,
                "level": "warning",
                "message": f"⚠️ {category} at {pct:.0f}%: ₹{cat_spent:,.0f} / ₹{limit:,.0f}"
            })
    return warnings


def get_balance_summary(session: Session, month_key: str) -> dict:
    # Total income for the month
    incomes = session.exec(
        select(IncomeEntry).where(IncomeEntry.month_key == month_key)
    ).all()
    total_income = sum(i.amount for i in incomes)
    if total_income == 0:
        total_income = config["salary"]["net_monthly"]

    # Fixed expenses
    fixed = session.exec(
        select(Expense).where(
            Expense.month_key == month_key,
            Expense.is_fixed == True
        )
    ).all()
    fixed_total = sum(e.amount for e in fixed)

    # Variable expenses
    variable = session.exec(
        select(Expense).where(
            Expense.month_key == month_key,
            Expense.is_fixed == False
        )
    ).all()
    variable_total = sum(e.amount for e in variable)

    total_spent = fixed_total + variable_total
    remaining = total_income - total_spent

    return {
        "month_key": month_key,
        "total_income": total_income,
        "fixed_total": fixed_total,
        "variable_total": variable_total,
        "total_spent": total_spent,
        "remaining": remaining,
        "savings_rate": ((total_income - total_spent) / total_income * 100) if total_income > 0 else 0
    }


def seed_fixed_expenses(session: Session, month_key: str):
    """Auto-seed fixed expenses for a month if not already done."""
    existing = session.exec(
        select(Expense).where(
            Expense.month_key == month_key,
            Expense.is_fixed == True
        )
    ).first()

    if existing:
        return  # Already seeded

    fixed_list = config.get("fixed_expenses", [])
    year, month = map(int, month_key.split("-"))
    expense_date = date(year, month, 1)

    for item in fixed_list:
        exp = Expense(
            date=expense_date,
            vendor=item["name"],
            amount=item["amount"],
            category=item["category"],
            is_fixed=True,
            month_key=month_key,
            note="Auto-seeded fixed expense"
        )
        session.add(exp)

    session.commit()
