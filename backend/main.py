from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional
from datetime import date
import yaml

from backend.models import Expense, BudgetLimit, IncomeEntry, create_db, get_session, engine
from backend.ai_parser import parse_expense_input
from backend.budget_rules import (
    get_month_key, check_budget_warnings, get_balance_summary,
    seed_fixed_expenses, get_monthly_spent_by_category, get_budget_limits
)

with open("config.yaml") as f:
    config = yaml.safe_load(f)

app = FastAPI(title="Expenditure Tracker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    create_db()
    # Seed budget limits from config on first run
    with Session(engine) as session:
        existing = session.exec(select(BudgetLimit)).first()
        if not existing:
            for cat, limit in config.get("budget_limits", {}).items():
                session.add(BudgetLimit(category=cat, limit_amount=limit))
            session.commit()
        # Seed current month fixed expenses
        seed_fixed_expenses(session, get_month_key())


# ── Request Models ──────────────────────────────────────────────────────────

class ExpenseInput(BaseModel):
    text: str
    date_override: Optional[str] = None  # "YYYY-MM-DD"

class ManualExpense(BaseModel):
    vendor: str
    amount: float
    category: str
    note: Optional[str] = None
    expense_date: Optional[str] = None

class BudgetUpdate(BaseModel):
    category: str
    limit_amount: float

class IncomeInput(BaseModel):
    source: str
    amount: float
    month_key: Optional[str] = None
    note: Optional[str] = None


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.post("/expenses/parse")
def parse_and_save(input: ExpenseInput, session: Session = Depends(get_session)):
    """Parse natural language expense input and save to DB."""
    try:
        parsed = parse_expense_input(input.text)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"AI parsing failed: {str(e)}")

    expense_date = date.today()
    if input.date_override:
        expense_date = date.fromisoformat(input.date_override)

    month_key = get_month_key(expense_date)
    saved = []

    for item in parsed:
        exp = Expense(
            date=expense_date,
            vendor=item["vendor"],
            amount=item["amount"],
            category=item["category"],
            note=item.get("note"),
            is_fixed=False,
            month_key=month_key,
        )
        session.add(exp)
        saved.append(item)

    session.commit()

    warnings = check_budget_warnings(session, month_key)
    balance = get_balance_summary(session, month_key)

    return {
        "saved": saved,
        "warnings": warnings,
        "balance": balance
    }


@app.post("/expenses/manual")
def add_manual_expense(exp: ManualExpense, session: Session = Depends(get_session)):
    expense_date = date.fromisoformat(exp.expense_date) if exp.expense_date else date.today()
    month_key = get_month_key(expense_date)

    new_exp = Expense(
        date=expense_date,
        vendor=exp.vendor,
        amount=exp.amount,
        category=exp.category,
        note=exp.note,
        is_fixed=False,
        month_key=month_key,
    )
    session.add(new_exp)
    session.commit()
    session.refresh(new_exp)

    warnings = check_budget_warnings(session, month_key)
    return {"expense": new_exp, "warnings": warnings}


@app.get("/expenses/{month_key}")
def get_expenses(month_key: str, session: Session = Depends(get_session)):
    expenses = session.exec(
        select(Expense).where(Expense.month_key == month_key)
        .order_by(Expense.date.desc())
    ).all()
    return expenses


@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int, session: Session = Depends(get_session)):
    exp = session.get(Expense, expense_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")
    session.delete(exp)
    session.commit()
    return {"deleted": expense_id}


@app.get("/summary/{month_key}")
def get_summary(month_key: str, session: Session = Depends(get_session)):
    seed_fixed_expenses(session, month_key)
    balance = get_balance_summary(session, month_key)
    warnings = check_budget_warnings(session, month_key)
    spent_by_cat = get_monthly_spent_by_category(session, month_key)
    limits = get_budget_limits(session)

    categories = []
    for cat, limit in limits.items():
        spent = spent_by_cat.get(cat, 0)
        categories.append({
            "category": cat,
            "spent": spent,
            "limit": limit,
            "pct": min((spent / limit * 100) if limit > 0 else 0, 100),
            "remaining": max(limit - spent, 0)
        })

    return {
        "balance": balance,
        "warnings": warnings,
        "categories": categories
    }


@app.get("/summary/current/now")
def get_current_summary(session: Session = Depends(get_session)):
    month_key = get_month_key()
    return get_summary(month_key, session)


@app.put("/budget")
def update_budget(update: BudgetUpdate, session: Session = Depends(get_session)):
    bl = session.exec(
        select(BudgetLimit).where(BudgetLimit.category == update.category)
    ).first()
    if bl:
        bl.limit_amount = update.limit_amount
    else:
        bl = BudgetLimit(category=update.category, limit_amount=update.limit_amount)
        session.add(bl)
    session.commit()
    return {"category": update.category, "limit": update.limit_amount}


@app.get("/budgets")
def list_budgets(session: Session = Depends(get_session)):
    return session.exec(select(BudgetLimit)).all()


@app.post("/income")
def add_income(income: IncomeInput, session: Session = Depends(get_session)):
    month_key = income.month_key or get_month_key()
    entry = IncomeEntry(
        source=income.source,
        amount=income.amount,
        month_key=month_key,
        note=income.note
    )
    session.add(entry)
    session.commit()
    return entry


@app.get("/months")
def list_months(session: Session = Depends(get_session)):
    expenses = session.exec(select(Expense.month_key).distinct()).all()
    return sorted(set(expenses), reverse=True)


@app.post("/seed/{month_key}")
def seed_month(month_key: str, session: Session = Depends(get_session)):
    seed_fixed_expenses(session, month_key)
    return {"seeded": month_key}
