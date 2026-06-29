from sqlmodel import Session, select
from backend.models import Expense, BudgetLimit, IncomeEntry, FixedExpenseTemplate, PoolEntry
from datetime import date
from dotenv import load_dotenv
import os
import yaml

load_dotenv()

with open("config.yaml") as f:
    config = yaml.safe_load(f)


def get_month_key(d: date = None) -> str:
    d = d or date.today()
    return d.strftime("%Y-%m")


def get_monthly_spent_by_category(session: Session, month_key: str,
                                   user_id: int) -> dict[str, float]:
    """Return total spend per category for a month, scoped to user."""
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


def get_budget_limits(session: Session, user_id: int) -> dict[str, float]:
    """Return budget limits for a user. Falls back to config.yaml if none set."""
    limits = session.exec(
        select(BudgetLimit).where(BudgetLimit.user_id == user_id)
    ).all()
    if limits:
        return {bl.category: bl.limit_amount for bl in limits}
    return config.get("budget_limits", {})


def check_budget_warnings(session: Session, month_key: str,
                           user_id: int) -> list[dict]:
    """Return warning dicts for categories over 80% or 100% of limit."""
    spent  = get_monthly_spent_by_category(session, month_key, user_id=user_id)
    limits = get_budget_limits(session, user_id=user_id)
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


def get_balance_summary(session: Session, month_key: str, user_id: int) -> dict:
    """Compute full balance summary scoped to a single user."""

    # Income: only count explicitly saved entries — 0 if none saved yet
    incomes = session.exec(
        select(IncomeEntry).where(
            IncomeEntry.month_key == month_key,
            IncomeEntry.user_id == user_id,
        )
    ).all()
    total_income = sum(i.amount for i in incomes)
    if total_income == 0:
        total_income = int(os.getenv("DEFAULT_MONTHLY_INCOME", "0"))

    # Fixed: only count PAID (ticked) rows
    fixed_all = session.exec(
        select(Expense).where(
            Expense.month_key == month_key,
            Expense.is_fixed == True,
            Expense.user_id == user_id,
        )
    ).all()
    fixed_paid_total   = sum(e.amount for e in fixed_all if e.paid)
    fixed_unpaid_total = sum(e.amount for e in fixed_all if not e.paid)

    # Pool entries: paid pool entries reduce balance
    pool_all = session.exec(
        select(PoolEntry).where(
            PoolEntry.month_key == month_key,
            PoolEntry.user_id == user_id,
        )
    ).all()
    pool_paid_total   = sum(p.amount for p in pool_all if p.paid)
    pool_unpaid_total = sum(p.amount for p in pool_all if not p.paid)

    # Variable expenses are always counted (already spent)
    variable = session.exec(
        select(Expense).where(
            Expense.month_key == month_key,
            Expense.is_fixed == False,
            Expense.user_id == user_id,
        )
    ).all()
    variable_total = sum(e.amount for e in variable)
    savings_total  = sum(e.amount for e in variable
                         if e.category in ("Savings", "Investments"))

    total_spent = fixed_paid_total + pool_paid_total + variable_total
    remaining   = total_income - total_spent

    return {
        "month_key": month_key,
        "total_income": total_income,
        "fixed_paid_total": fixed_paid_total + pool_paid_total,
        "fixed_unpaid_total": fixed_unpaid_total + pool_unpaid_total,
        "fixed_total": fixed_paid_total + fixed_unpaid_total + pool_paid_total + pool_unpaid_total,
        "pool_paid_total": pool_paid_total,
        "pool_unpaid_total": pool_unpaid_total,
        "variable_total": variable_total,
        "savings_total":  savings_total,
        "total_spent": total_spent,
        "remaining": remaining,
        "savings_rate": ((total_income - total_spent) / total_income * 100) if total_income > 0 else 0,
    }


def has_prior_activity(session: Session, month_key: str, user_id: int) -> bool:
    """True if the user has any Expense or IncomeEntry in a month before month_key.

    Month keys are "YYYY-MM" strings, so lexicographic `<` is the correct ordering.
    """
    exp = session.exec(
        select(Expense.id).where(
            Expense.user_id == user_id, Expense.month_key < month_key
        ).limit(1)
    ).first()
    if exp:
        return True
    inc = session.exec(
        select(IncomeEntry.id).where(
            IncomeEntry.user_id == user_id, IncomeEntry.month_key < month_key
        ).limit(1)
    ).first()
    return inc is not None


def compute_peace_of_mind(balance: dict) -> dict:
    """
    Compute Peace of Mind Score (0–100) from a get_balance_summary() dict.
    Formula weights confirmed by user on 2026-06-25.

    Sub-signals:
        bills    (35 pts) — fixed bills completion ratio
        buffer   (30 pts) — remaining / total_income ratio
        pace     (20 pts) — variable spend vs 40% of income threshold
        tracking (15 pts) — placeholder; always 15 until streak tracking built
    """
    fixed_paid   = balance["fixed_paid_total"]
    fixed_unpaid = balance["fixed_unpaid_total"]
    fixed_total  = fixed_paid + fixed_unpaid
    total_income = balance["total_income"]
    remaining    = balance["remaining"]
    variable_total = balance["variable_total"]

    # Bills sub-signal (35 pts)
    if fixed_total == 0 or fixed_unpaid == 0:
        bills_pts = 35
    else:
        bills_pts = round(35 * (fixed_paid / fixed_total))

    # Remaining buffer sub-signal (30 pts)
    if total_income > 0:
        buf = remaining / total_income
        if buf >= 0.20:
            buffer_pts = 30
        elif buf >= 0.10:
            buffer_pts = 20
        elif buf >= 0.05:
            buffer_pts = 10
        else:
            buffer_pts = 0
    else:
        buffer_pts = 0

    # Spending pace sub-signal (20 pts) — 40% of income is the variable budget threshold
    variable_budget = total_income * 0.4
    if variable_budget > 0:
        pace = variable_total / variable_budget
        if pace <= 0.80:
            pace_pts = 20
        elif pace <= 1.00:
            pace_pts = 10
        else:
            pace_pts = 0
    else:
        pace_pts = 0

    # Tracking consistency (15 pts) — placeholder until streak tracking is built
    tracking_pts = 15

    score = bills_pts + buffer_pts + pace_pts + tracking_pts

    if score >= 80:
        label = "Great going!"
    elif score >= 60:
        label = "On track, keep it up."
    elif score >= 40:
        label = "A few areas need attention."
    else:
        label = "Let's get back on track."

    return {
        "score": score,
        "label": label,
        "breakdown": {
            "bills":    bills_pts,
            "buffer":   buffer_pts,
            "pace":     pace_pts,
            "tracking": tracking_pts,
        },
    }


def seed_fixed_expenses(session: Session, month_key: str, user_id: int):
    """
    Seed fixed expense rows for a month from FixedExpenseTemplate, scoped to user.
    Falls back to config.yaml if no templates exist for this user yet.
    Idempotent — already-seeded templates are skipped.
    """
    year, month = map(int, month_key.split("-"))
    expense_date = date(year, month, 1)

    templates = session.exec(
        select(FixedExpenseTemplate).where(
            FixedExpenseTemplate.is_active == True,
            FixedExpenseTemplate.user_id == user_id,
        ).order_by(FixedExpenseTemplate.sort_order, FixedExpenseTemplate.id)
    ).all()

    # New users start with a clean slate — the onboarding wizard is their
    # setup path. Config seeding is intentionally skipped for non-admin users.
    if not templates:
        return

    for tmpl in templates:
        # Pool templates are not auto-seeded — entries added manually each month
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
            user_id=user_id,
        )
        session.add(exp)

    session.commit()


def _seed_from_config(session: Session, month_key: str,
                      expense_date: date, user_id: int):
    """One-time bootstrap from config.yaml into FixedExpenseTemplate table for a user."""
    fixed_list = config.get("fixed_expenses", [])

    for i, item in enumerate(fixed_list):
        tmpl = FixedExpenseTemplate(
            name=item["name"],
            category=item["category"],
            amount=item["amount"],
            is_active=True,
            sort_order=i,
            user_id=user_id,
        )
        session.add(tmpl)
        session.flush()  # get tmpl.id

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
                user_id=user_id,
            )
            session.add(exp)

    session.commit()
