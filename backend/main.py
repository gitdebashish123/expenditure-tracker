from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional
from datetime import date
from dotenv import load_dotenv
import os
import yaml

# Load .env before anything else
load_dotenv()

from backend.models import (
    Expense, BudgetLimit, IncomeEntry, FixedExpenseTemplate, ExpenseTemplate, PoolEntry,
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
    allow_origins=[
        # HTTP direct — used by Streamlit when accessed from iPhone on local WiFi
        # and as a fallback during local development without nginx
        "http://localhost:8501",

        # HTTPS via nginx — used by Mac browser after Commit 1.2 HTTPS setup
        # nginx listens on 8443 and proxies to Streamlit on 8501
        "https://localhost:8443",

        # TODO Sprint 5 (API Hardening): replace with production URL once deployed
        # e.g. "https://spendsense.railway.app"
    ],
    allow_methods=["*"],   # tightened in Sprint 5 — API Hardening
    allow_headers=["*"],   # tightened in Sprint 5 — API Hardening
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
    template_type: Optional[str] = "fixed"

class FixedTemplateUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    amount: Optional[float] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    due_day: Optional[int] = None
    template_type: Optional[str] = None


class PoolEntryCreate(BaseModel):
    label: str
    amount: float
    note: Optional[str] = None


class PoolEntryUpdate(BaseModel):
    label: Optional[str] = None
    amount: Optional[float] = None
    paid: Optional[bool] = None
    note: Optional[str] = None
    due_day: Optional[int] = None


class ExpenseUpdate(BaseModel):
    vendor: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None
    note: Optional[str] = None
    expense_date: Optional[str] = None


class BulkDeleteRequest(BaseModel):
    ids: list[int]


class ExpenseTemplateCreate(BaseModel):
    name: str
    vendor: str
    category: str
    amount: float


class ExpenseTemplateUpdate(BaseModel):
    name: Optional[str] = None
    vendor: Optional[str] = None
    category: Optional[str] = None
    amount: Optional[float] = None
    is_active: Optional[bool] = None


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


@app.patch("/expenses/{expense_id}")
def edit_expense(expense_id: int, update: ExpenseUpdate, session: Session = Depends(get_session)):
    """Edit vendor, amount, category or note of a variable expense."""
    exp = session.get(Expense, expense_id)
    if not exp or exp.is_fixed:
        raise HTTPException(status_code=404, detail="Expense not found")
    if update.vendor is not None: exp.vendor = update.vendor
    if update.amount is not None: exp.amount = update.amount
    if update.category is not None: exp.category = update.category
    if update.note is not None: exp.note = update.note
    if update.expense_date is not None:
        exp.date = date.fromisoformat(update.expense_date)
        exp.month_key = get_month_key(exp.date)
    session.add(exp)
    session.commit()
    session.refresh(exp)
    return exp


@app.post("/expenses/bulk-delete")
def bulk_delete_expenses(req: BulkDeleteRequest, session: Session = Depends(get_session)):
    """Delete multiple variable expenses at once."""
    deleted = []
    for expense_id in req.ids:
        exp = session.get(Expense, expense_id)
        if exp and not exp.is_fixed:
            session.delete(exp)
            deleted.append(expense_id)
    session.commit()
    return {"deleted": deleted, "count": len(deleted)}


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


# ── Expense Templates (Favourites) ──────────────────────────────────────────

@app.get("/expense-templates")
def list_expense_templates(session: Session = Depends(get_session)):
    return session.exec(
        select(ExpenseTemplate).where(ExpenseTemplate.is_active == True)
        .order_by(ExpenseTemplate.use_count.desc())
    ).all()


@app.post("/expense-templates")
def create_expense_template(tmpl: ExpenseTemplateCreate, session: Session = Depends(get_session)):
    new = ExpenseTemplate(
        name=tmpl.name, vendor=tmpl.vendor,
        category=tmpl.category, amount=tmpl.amount
    )
    session.add(new)
    session.commit()
    session.refresh(new)
    return new


@app.put("/expense-templates/{tmpl_id}")
def update_expense_template(tmpl_id: int, update: ExpenseTemplateUpdate,
                            session: Session = Depends(get_session)):
    tmpl = session.get(ExpenseTemplate, tmpl_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(tmpl, field, value)
    session.add(tmpl)
    session.commit()
    session.refresh(tmpl)
    return tmpl


@app.delete("/expense-templates/{tmpl_id}")
def delete_expense_template(tmpl_id: int, session: Session = Depends(get_session)):
    tmpl = session.get(ExpenseTemplate, tmpl_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")
    tmpl.is_active = False
    session.add(tmpl)
    session.commit()
    return {"deleted": tmpl_id}


@app.post("/expense-templates/{tmpl_id}/log")
def log_from_template(tmpl_id: int, expense_date: Optional[str] = None,
                      session: Session = Depends(get_session)):
    """One-tap log: create an expense from a favourite template."""
    tmpl = session.get(ExpenseTemplate, tmpl_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")
    exp_date = date.fromisoformat(expense_date) if expense_date else date.today()
    month_key = get_month_key(exp_date)
    exp = Expense(
        date=exp_date, vendor=tmpl.vendor, amount=tmpl.amount,
        category=tmpl.category, note=f"Quick-add: {tmpl.name}",
        is_fixed=False, paid=True, month_key=month_key
    )
    session.add(exp)
    tmpl.use_count += 1
    session.add(tmpl)
    session.commit()
    session.refresh(exp)
    warnings = check_budget_warnings(session, month_key)
    balance = get_balance_summary(session, month_key)
    return {"expense": exp, "warnings": warnings, "balance": balance}


# ── Income Check ─────────────────────────────────────────────────────────────

@app.get("/income/check/{month_key}")
def check_income_set(month_key: str, session: Session = Depends(get_session)):
    """Check if income has been explicitly set for a month."""
    entry = session.exec(
        select(IncomeEntry).where(IncomeEntry.month_key == month_key)
    ).first()
    return {"is_set": entry is not None, "month_key": month_key}


# ── Fixed Due Day ─────────────────────────────────────────────────────────────

@app.get("/fixed/due-reminders/{month_key}")
def get_due_reminders(month_key: str, session: Session = Depends(get_session)):
    """Return unpaid fixed expenses whose due_day is today or has passed."""
    from datetime import date as dt
    today = dt.today()
    expenses = session.exec(
        select(Expense).where(
            Expense.month_key == month_key,
            Expense.is_fixed == True,
            Expense.paid == False,
        )
    ).all()
    reminders = []
    for exp in expenses:
        tmpl = session.get(FixedExpenseTemplate, exp.fixed_template_id) if exp.fixed_template_id else None
        if tmpl and tmpl.due_day:
            days_overdue = today.day - tmpl.due_day
            if days_overdue >= 0:
                reminders.append({
                    "expense_id": exp.id,
                    "vendor": exp.vendor,
                    "amount": exp.amount,
                    "category": exp.category,
                    "due_day": tmpl.due_day,
                    "days_overdue": days_overdue,
                })
    return sorted(reminders, key=lambda x: x["days_overdue"], reverse=True)


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
        template_type=tmpl.template_type or "fixed",
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
    # Fall back to DEFAULT_MONTHLY_INCOME env var, then 0
    default_income = int(os.getenv("DEFAULT_MONTHLY_INCOME", "0"))
    return {"source": "Salary", "amount": default_income, "note": None}


@app.get("/months")
def list_months(session: Session = Depends(get_session)):
    expenses = session.exec(select(Expense.month_key).distinct()).all()
    return sorted(set(expenses), reverse=True)


@app.post("/seed/{month_key}")
def seed_month(month_key: str, session: Session = Depends(get_session)):
    seed_fixed_expenses(session, month_key)
    return {"seeded": month_key}


@app.get("/insights/mom/{month_key}")
def month_over_month(month_key: str, session: Session = Depends(get_session)):
    """
    Return variable spend per category for the given month + 2 preceding months.
    Used for the month-over-month comparison table on the dashboard.
    """
    from datetime import date as dt
    import calendar

    # Build list of [month_key-2, month_key-1, month_key]
    year, month = map(int, month_key.split("-"))
    months = []
    for offset in range(2, -1, -1):
        m = month - offset
        y = year
        while m <= 0:
            m += 12
            y -= 1
        months.append(f"{y:04d}-{m:02d}")

    # All variable expenses across those 3 months
    expenses = session.exec(
        select(Expense).where(
            Expense.month_key.in_(months),
            Expense.is_fixed == False,
        )
    ).all()

    # Build category → {month_key: total}
    data: dict[str, dict[str, float]] = {}
    for e in expenses:
        data.setdefault(e.category, {})
        data[e.category][e.month_key] = data[e.category].get(e.month_key, 0) + e.amount

    # Also pull income for each month (for savings rate)
    incomes = session.exec(
        select(IncomeEntry).where(IncomeEntry.month_key.in_(months))
    ).all()
    income_map = {i.month_key: i.amount for i in incomes}

    return {
        "months": months,
        "categories": data,
        "income": income_map,
    }


@app.get("/insights/top-spends/{month_key}")
def top_spends(month_key: str, limit: int = 5, session: Session = Depends(get_session)):
    """
    Return top N individual variable expense transactions for the month.
    """
    expenses = session.exec(
        select(Expense).where(
            Expense.month_key == month_key,
            Expense.is_fixed == False,
        ).order_by(Expense.amount.desc())
    ).all()

    results = []
    for e in expenses[:limit]:
        results.append({
            "id": e.id,
            "vendor": e.vendor,
            "amount": e.amount,
            "category": e.category,
            "date": e.date.isoformat(),
            "note": e.note,
        })
    return results


@app.get("/insights/projection/{month_key}")
def budget_projection(month_key: str, session: Session = Depends(get_session)):
    """
    For each variable category, project end-of-month spend based on daily burn rate.
    """
    from datetime import date as dt
    import calendar

    year, month = map(int, month_key.split("-"))
    days_in_month = calendar.monthrange(year, month)[1]
    today = dt.today()

    # Days elapsed: if viewing a past month use full month, else use today
    if month_key < today.strftime("%Y-%m"):
        days_elapsed = days_in_month
    elif month_key == today.strftime("%Y-%m"):
        days_elapsed = max(today.day, 1)
    else:
        days_elapsed = 1

    expenses = session.exec(
        select(Expense).where(
            Expense.month_key == month_key,
            Expense.is_fixed == False,
        )
    ).all()

    limits_rows = session.exec(select(BudgetLimit)).all()
    limits = {bl.category: bl.limit_amount for bl in limits_rows}

    cat_spent: dict[str, float] = {}
    for e in expenses:
        cat_spent[e.category] = cat_spent.get(e.category, 0) + e.amount

    projections = []
    for cat, limit in limits.items():
        spent = cat_spent.get(cat, 0)
        daily_rate = spent / days_elapsed
        projected = daily_rate * days_in_month
        days_left = days_in_month - days_elapsed
        budget_left = max(limit - spent, 0)

        if limit > 0:
            projections.append({
                "category": cat,
                "spent": spent,
                "limit": limit,
                "projected": round(projected),
                "daily_rate": round(daily_rate, 1),
                "days_left": days_left,
                "budget_left": budget_left,
                "pct_spent": round(spent / limit * 100, 1),
                "pct_projected": round(projected / limit * 100, 1),
                "status": (
                    "over" if spent > limit else
                    "danger" if projected > limit else
                    "warning" if projected > limit * 0.85 else
                    "safe"
                ),
            })

    return sorted(projections, key=lambda x: x["pct_projected"], reverse=True)


# ── Pool Entries (Essential Pools) ───────────────────────────────────────────

@app.get("/pools/{month_key}")
def get_pools_for_month(month_key: str, session: Session = Depends(get_session)):
    """
    Return all active pool templates with their entries for the given month.
    Used to render the Essential Pools section in the Fixed tab.
    """
    pool_templates = session.exec(
        select(FixedExpenseTemplate).where(
            FixedExpenseTemplate.is_active == True,
            FixedExpenseTemplate.template_type == "pool",
        ).order_by(FixedExpenseTemplate.sort_order, FixedExpenseTemplate.id)
    ).all()

    result = []
    for tmpl in pool_templates:
        entries = session.exec(
            select(PoolEntry).where(
                PoolEntry.pool_template_id == tmpl.id,
                PoolEntry.month_key == month_key,
            ).order_by(PoolEntry.created_at)
        ).all()
        paid_total   = sum(e.amount for e in entries if e.paid)
        unpaid_total = sum(e.amount for e in entries if not e.paid)
        result.append({
            "id": tmpl.id,
            "name": tmpl.name,
            "category": tmpl.category,
            "entries": [
                {
                    "id": e.id,
                    "label": e.label,
                    "amount": e.amount,
                    "paid": e.paid,
                    "paid_date": e.paid_date.isoformat() if e.paid_date else None,
                    "note": e.note,
                }
                for e in entries
            ],
            "paid_total": paid_total,
            "unpaid_total": unpaid_total,
            "entry_count": len(entries),
        })
    return result


@app.post("/pools/{pool_template_id}/entries/{month_key}")
def add_pool_entry(
    pool_template_id: int,
    month_key: str,
    entry: PoolEntryCreate,
    session: Session = Depends(get_session)
):
    """Add a new payment entry to an essential pool for a month."""
    tmpl = session.get(FixedExpenseTemplate, pool_template_id)
    if not tmpl or tmpl.template_type != "pool":
        raise HTTPException(status_code=404, detail="Pool template not found")

    new_entry = PoolEntry(
        pool_template_id=pool_template_id,
        month_key=month_key,
        label=entry.label,
        amount=entry.amount,
        paid=True,                    # entering an amount = already paid
        paid_date=date.today(),
        note=entry.note,
    )
    session.add(new_entry)
    session.commit()
    session.refresh(new_entry)
    return new_entry


@app.patch("/pools/entries/{entry_id}")
def update_pool_entry(
    entry_id: int,
    update: PoolEntryUpdate,
    session: Session = Depends(get_session)
):
    """Update label, amount, paid status or note of a pool entry."""
    entry = session.get(PoolEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Pool entry not found")
    if update.label is not None:  entry.label  = update.label
    if update.amount is not None: entry.amount = update.amount
    if update.note is not None:   entry.note   = update.note
    if update.paid is not None:
        entry.paid = update.paid
        entry.paid_date = date.today() if update.paid else None
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@app.patch("/pools/entries/{entry_id}/toggle")
def toggle_pool_entry_paid(entry_id: int, session: Session = Depends(get_session)):
    """Toggle paid status of a pool entry."""
    entry = session.get(PoolEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Pool entry not found")
    entry.paid = not entry.paid
    entry.paid_date = date.today() if entry.paid else None
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@app.delete("/pools/entries/{entry_id}")
def delete_pool_entry(entry_id: int, session: Session = Depends(get_session)):
    """Delete a pool entry."""
    entry = session.get(PoolEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Pool entry not found")
    session.delete(entry)
    session.commit()
    return {"deleted": entry_id}
