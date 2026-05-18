from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional
from datetime import date
import yaml

from backend.models import (
    Expense, BudgetLimit, IncomeEntry, FixedExpenseTemplate,
    create_db, get_session, engine
)
from backend.ai_parser import parse_expense_input
from backend.budget_rules import (
    get_month_key, check_budget_warnings, get_balance_summary,
    seed_fixed_expenses, get_monthly_spent_by_category, get_budget_limits
)

with open("config.yaml") as f:
    config = yaml.safe_load(f)

app = FastAPI(title="Expenditure Tracker API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    create_db()
    with Session(engine) as session:
        # Seed budget limits
        existing = session.exec(select(BudgetLimit)).first()
        if not existing:
            for cat, limit in config.get("budget_limits", {}).items():
                session.add(BudgetLimit(category=cat, limit_amount=limit))
            session.commit()
        # Seed current month fixed expenses (also migrates config → DB templates on first run)
        seed_fixed_expenses(session, get_month_key())


# ── Request Models ───────────────────────────────────────────────────────────

class ExpenseInput(BaseModel):
    text: str
    date_override: Optional[str] = None

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

class FixedTemplateCreate(BaseModel):
    name: str
    category: str
    amount: float
    sort_order: Optional[int] = 0

class FixedTemplateUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    amount: Optional[float] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


# ── Variable Expense Endpoints ───────────────────────────────────────────────

@app.post("/expenses/parse")
def parse_and_save(input: ExpenseInput, session: Session = Depends(get_session)):
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
            paid=True,   # variable expenses are immediately "paid"
            month_key=month_key,
        )
        session.add(exp)
        saved.append(item)

    session.commit()
    warnings = check_budget_warnings(session, month_key)
    balance = get_balance_summary(session, month_key)
    return {"saved": saved, "warnings": warnings, "balance": balance}


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
        paid=True,
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


# ── Fixed Expense: Monthly Tick ──────────────────────────────────────────────

@app.get("/fixed/{month_key}")
def get_fixed_expenses(month_key: str, session: Session = Depends(get_session)):
    """Return all fixed expense rows for a month with paid status."""
    seed_fixed_expenses(session, month_key)
    expenses = session.exec(
        select(Expense).where(Expense.month_key == month_key, Expense.is_fixed == True)
        .order_by(Expense.category, Expense.vendor)
    ).all()
    return expenses


@app.patch("/fixed/{expense_id}/toggle")
def toggle_paid(expense_id: int, session: Session = Depends(get_session)):
    """Toggle the paid/unpaid tick for a fixed expense."""
    exp = session.get(Expense, expense_id)
    if not exp or not exp.is_fixed:
        raise HTTPException(status_code=404, detail="Fixed expense not found")
    exp.paid = not exp.paid
    session.add(exp)
    session.commit()
    session.refresh(exp)
    return exp


@app.patch("/fixed/{expense_id}/amount")
def update_fixed_amount(expense_id: int, amount: float, session: Session = Depends(get_session)):
    """Override amount for a specific month's fixed expense."""
    exp = session.get(Expense, expense_id)
    if not exp or not exp.is_fixed:
        raise HTTPException(status_code=404, detail="Fixed expense not found")
    exp.amount = amount
    session.add(exp)
    session.commit()
    session.refresh(exp)
    return exp


# ── Fixed Expense Templates (CRUD) ───────────────────────────────────────────

@app.get("/fixed-templates")
def list_templates(session: Session = Depends(get_session)):
    return session.exec(
        select(FixedExpenseTemplate)
        .order_by(FixedExpenseTemplate.sort_order, FixedExpenseTemplate.id)
    ).all()


@app.post("/fixed-templates")
def create_template(tmpl: FixedTemplateCreate, session: Session = Depends(get_session)):
    new = FixedExpenseTemplate(
        name=tmpl.name,
        category=tmpl.category,
        amount=tmpl.amount,
        sort_order=tmpl.sort_order or 0,
    )
    session.add(new)
    session.commit()
    session.refresh(new)
    return new


@app.put("/fixed-templates/{template_id}")
def update_template(
    template_id: int,
    update: FixedTemplateUpdate,
    session: Session = Depends(get_session)
):
    tmpl = session.get(FixedExpenseTemplate, template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(tmpl, field, value)
    session.add(tmpl)
    session.commit()
    session.refresh(tmpl)
    return tmpl


@app.delete("/fixed-templates/{template_id}")
def delete_template(template_id: int, session: Session = Depends(get_session)):
    tmpl = session.get(FixedExpenseTemplate, template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")

    # Soft delete the template
    tmpl.is_active = False
    session.add(tmpl)

    # Remove seeded expense rows for current month onwards (preserve past history)
    current_month = get_month_key()
    rows_to_delete = session.exec(
        select(Expense).where(
            Expense.fixed_template_id == template_id,
            Expense.month_key >= current_month,
        )
    ).all()
    for row in rows_to_delete:
        session.delete(row)

    session.commit()
    return {"deleted": template_id, "expense_rows_removed": len(rows_to_delete)}


# ── Summary & Budget ─────────────────────────────────────────────────────────

@app.get("/summary/{month_key}")
def get_summary(month_key: str, session: Session = Depends(get_session)):
    seed_fixed_expenses(session, month_key)
    balance = get_balance_summary(session, month_key)
    warnings = check_budget_warnings(session, month_key)
    spent_by_cat = get_monthly_spent_by_category(session, month_key)
    limits = get_budget_limits(session)

    # Fixed checklist progress
    fixed_exps = session.exec(
        select(Expense).where(Expense.month_key == month_key, Expense.is_fixed == True)
    ).all()
    fixed_paid = sum(1 for e in fixed_exps if e.paid)

    categories = []
    for cat, limit in limits.items():
        spent = spent_by_cat.get(cat, 0)
        categories.append({
            "category": cat,
            "spent": spent,
            "limit": limit,
            "pct": min((spent / limit * 100) if limit > 0 else 0, 100),
            "remaining": max(limit - spent, 0),
        })

    return {
        "balance": balance,
        "warnings": warnings,
        "categories": categories,
        "fixed_progress": {"paid": fixed_paid, "total": len(fixed_exps)},
    }


@app.get("/summary/current/now")
def get_current_summary(session: Session = Depends(get_session)):
    return get_summary(get_month_key(), session)


@app.put("/budget")
def update_budget(update: BudgetUpdate, session: Session = Depends(get_session)):
    bl = session.exec(select(BudgetLimit).where(BudgetLimit.category == update.category)).first()
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
def upsert_income(income: IncomeInput, session: Session = Depends(get_session)):
    """Upsert income for a month — updates existing entry rather than stacking duplicates."""
    month_key = income.month_key or get_month_key()
    existing = session.exec(
        select(IncomeEntry).where(IncomeEntry.month_key == month_key)
    ).first()
    if existing:
        existing.source = income.source
        existing.amount = income.amount
        existing.note = income.note
        session.add(existing)
    else:
        entry = IncomeEntry(source=income.source, amount=income.amount,
                            month_key=month_key, note=income.note)
        session.add(entry)
    session.commit()
    return {"month_key": month_key, "source": income.source, "amount": income.amount}


@app.get("/income/{month_key}")
def get_income(month_key: str, session: Session = Depends(get_session)):
    """Get income entry for a specific month."""
    entry = session.exec(
        select(IncomeEntry).where(IncomeEntry.month_key == month_key)
    ).first()
    if entry:
        return {"source": entry.source, "amount": entry.amount, "note": entry.note}
    # Return config default if no entry exists
    return {"source": "Infosys Salary", "amount": config["salary"]["net_monthly"], "note": None}


@app.get("/months")
def list_months(session: Session = Depends(get_session)):
    expenses = session.exec(select(Expense.month_key).distinct()).all()
    return sorted(set(expenses), reverse=True)


@app.post("/seed/{month_key}")
def seed_month(month_key: str, session: Session = Depends(get_session)):
    seed_fixed_expenses(session, month_key)
    return {"seeded": month_key}
