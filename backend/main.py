from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, func
from pydantic import BaseModel, field_validator
import bleach
from typing import Optional
from datetime import date, datetime
from dotenv import load_dotenv
import os
import yaml
import csv
import io

# Load .env before anything else
load_dotenv()

from backend.models import (
    Expense, BudgetLimit, IncomeEntry, FixedExpenseTemplate, ExpenseTemplate, PoolEntry,
    User, create_db, get_session, engine
)
from backend.ai_parser import parse_expense_input
from backend.budget_rules import (
    get_month_key, check_budget_warnings, get_balance_summary,
    seed_fixed_expenses, get_monthly_spent_by_category, get_budget_limits
)
from backend.auth import (
    hash_password, verify_password,
    create_access_token, get_current_user
)

with open("config.yaml") as f:
    config = yaml.safe_load(f)

# -- Rate Limiter ----------------------------------------------------------------
def get_rate_limit_key(request: Request):
    """Use JWT email as rate limit key if available, else fall back to IP address."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            from backend.auth import decode_token
            payload = decode_token(auth[7:])
            return payload.get("sub", get_remote_address(request))
        except Exception:
            pass
    return get_remote_address(request)

limiter = Limiter(key_func=get_rate_limit_key)

app = FastAPI(
    title="Wallet Mantra API",
    version="2.0.0",
    description="Personal expenditure tracker - JWT authenticated, per-user data isolation",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
# TODO Sprint 6: Add /api/v1 prefix via APIRouter(prefix="/api/v1")
# Requires updating API_BASE in frontend and Railway env vars

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",                              # Streamlit — keep throughout migration
        "https://localhost:8443",
        "http://localhost:5173",                              # Vite dev server (T2.1)
        #"https://frontend-production-9697.up.railway.app",  # Railway Streamlit + React frontend
        "https://app.wallet-mantra.com",  # cloudflare domain
    ],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=False,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    """Reject requests larger than 10KB to prevent payload abuse."""
    max_size = 10 * 1024  # 10KB
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > max_size:
        return JSONResponse(
            status_code=413,
            content={"detail": "Request payload too large. Maximum size is 10KB."},
        )
    return await call_next(request)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Add security headers to every response.
    X-Content-Type-Options: prevents MIME-type sniffing
    X-Frame-Options: prevents clickjacking
    X-XSS-Protection: legacy browser XSS filter
    Strict-Transport-Security: force HTTPS for 1 year
    Referrer-Policy: control referrer on cross-origin requests
    """
    response = await call_next(request)
    response.headers["X-Content-Type-Options"]    = "nosniff"
    response.headers["X-Frame-Options"]           = "DENY"
    response.headers["X-XSS-Protection"]          = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"]           = "strict-origin-when-cross-origin"
    if "server" in response.headers:
        del response.headers["server"]
    if "x-powered-by" in response.headers:
        del response.headers["x-powered-by"]
    return response


@app.on_event("startup")
def on_startup():
    create_db()

    # ── Auto-migrate: ensure onboarding_complete column exists ───────────────
    # Handles the case where the backend restarts after a model change
    # but migrate_schema.py hasn't been run yet.
    import sqlite3 as _sqlite3
    _db_path = os.getenv("DATABASE_URL", "sqlite:///./data/expenses.db").replace("sqlite:///", "")
    try:
        _conn = _sqlite3.connect(_db_path)
        _cur  = _conn.cursor()
        _cur.execute("PRAGMA table_info(user)")
        _cols = [row[1] for row in _cur.fetchall()]
        if "onboarding_complete" not in _cols:
            _cur.execute("ALTER TABLE user ADD COLUMN onboarding_complete INTEGER NOT NULL DEFAULT 0")
            _conn.commit()
            print("✅ Auto-migrated: user.onboarding_complete")
        _conn.close()
    except Exception as _e:
        print(f"⚠️  Auto-migration check failed: {_e}")

    with Session(engine) as session:
        # Find admin user for seeding
        admin = session.exec(select(User).where(User.is_admin == True)).first()
        admin_id = admin.id if admin else None

        # Seed budget limits for admin only if none exist yet
        if admin_id:
            existing = session.exec(
                select(BudgetLimit).where(BudgetLimit.user_id == admin_id)
            ).first()
            if not existing:
                for cat, limit in config.get("budget_limits", {}).items():
                    session.add(BudgetLimit(
                        category=cat, limit_amount=limit, user_id=admin_id
                    ))
                session.commit()

            # Seed current month fixed expenses for admin
            seed_fixed_expenses(session, get_month_key(), user_id=admin_id)

        # ── Default admin user ────────────────────────────────────────────────
        # Created only if no users exist — prevents lockout on first run
        existing_user = session.exec(select(User)).first()
        if not existing_user:
            admin_email    = os.getenv("ADMIN_EMAIL", "admin@spendsense.local")
            admin_password = os.getenv("ADMIN_PASSWORD", "changeme123")
            admin = User(
                email=admin_email,
                hashed_password=hash_password(admin_password),
                is_active=True,
                is_admin=True,
            )
            session.add(admin)
            session.commit()
            print(f"\n✅ Default admin created: {admin_email}")
            print("⚠️  Change the default password immediately — update ADMIN_PASSWORD in .env\n")


# ── Health Check ─────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    """
    Public health check — no authentication required.
    Called by Railway/Render to verify the container is running.
    Called by docker-compose HEALTHCHECK directive.
    """
    return {
        "status": "ok",
        "app": "Wallet Mantra",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


# ── Request Models ────────────────────────────────────────────────────────────

class ExpenseInput(BaseModel):
    text: str
    date_override: Optional[str] = None

    @field_validator("text")
    @classmethod
    def sanitise_text(cls, v):
        if len(v) > 500:
            raise ValueError("Input text must be under 500 characters")
        return bleach.clean(v, tags=[], strip=True).strip()

class ManualExpense(BaseModel):
    vendor: str
    amount: float
    category: str
    note: Optional[str] = None
    expense_date: Optional[str] = None

    @field_validator("vendor")
    @classmethod
    def sanitise_vendor(cls, v):
        if len(v) > 100:
            raise ValueError("Vendor name must be under 100 characters")
        return bleach.clean(v, tags=[], strip=True).strip()

    @field_validator("amount")
    @classmethod
    def positive_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        if v > 10_000_000:
            raise ValueError("Amount exceeds maximum allowed value")
        return round(v, 2)

    @field_validator("note")
    @classmethod
    def sanitise_note(cls, v):
        if v and len(v) > 300:
            raise ValueError("Note must be under 300 characters")
        return bleach.clean(v, tags=[], strip=True).strip() if v else v

class BudgetUpdate(BaseModel):
    category: str
    limit_amount: float

class IncomeInput(BaseModel):
    source: str
    amount: float
    month_key: Optional[str] = None
    note: Optional[str] = None

    @field_validator("source")
    @classmethod
    def sanitise_source(cls, v):
        if len(v) > 100:
            raise ValueError("Source name must be under 100 characters")
        return bleach.clean(v, tags=[], strip=True).strip()

    @field_validator("amount")
    @classmethod
    def positive_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        if v > 100_000_000:
            raise ValueError("Amount exceeds maximum allowed value")
        return round(v, 2)

class FixedTemplateCreate(BaseModel):
    name: str
    category: str
    amount: float
    sort_order: Optional[int] = 0
    template_type: Optional[str] = "fixed"

    @field_validator("name")
    @classmethod
    def sanitise_name(cls, v):
        if len(v) > 100:
            raise ValueError("Name must be under 100 characters")
        return bleach.clean(v, tags=[], strip=True).strip()

    @field_validator("amount")
    @classmethod
    def positive_amount(cls, v):
        # Pool templates may have amount=0 (typical amount unknown until paid)
        if v < 0:
            raise ValueError("Amount cannot be negative")
        return round(v, 2)

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

# ── Auth Request / Response Models ───────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def valid_email(cls, v):
        v = v.strip().lower()
        if len(v) > 255:
            raise ValueError("Email too long")
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format")
        return v

    @field_validator("password")
    @classmethod
    def strong_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(v) > 128:
            raise ValueError("Password too long")
        return v

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime]
    onboarding_complete: bool = False


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class DeleteAccountRequest(BaseModel):
    confirmation: str   # must equal "DELETE" to proceed


# ── Auth Endpoints (PUBLIC — no token required) ───────────────────────────────

@app.post("/auth/register", response_model=UserResponse, status_code=201)
@limiter.limit("5/hour", key_func=get_remote_address)
def register(request: Request, req: RegisterRequest, session: Session = Depends(get_session)):
    """Register a new user. Does not return a token — user must log in explicitly."""
    existing = session.exec(select(User).where(User.email == req.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        is_active=True,
        is_admin=False,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserResponse(
        id=user.id, email=user.email, is_active=user.is_active,
        is_admin=user.is_admin, created_at=user.created_at, last_login=user.last_login,
        onboarding_complete=getattr(user, "onboarding_complete", False),
    )


@app.post("/auth/login", response_model=TokenResponse)
@limiter.limit("10/hour", key_func=get_remote_address)
def login(request: Request, req: LoginRequest, session: Session = Depends(get_session)):
    """Authenticate and return a signed JWT. Same 401 for wrong email or wrong password."""
    user = session.exec(select(User).where(User.email == req.email)).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=401, detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled — contact administrator")
    user.last_login = datetime.utcnow()
    session.add(user)
    session.commit()
    return TokenResponse(access_token=create_access_token(data={"sub": user.email}))


@app.get("/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return UserResponse(
        id=current_user.id, email=current_user.email, is_active=current_user.is_active,
        is_admin=current_user.is_admin, created_at=current_user.created_at,
        last_login=current_user.last_login,
        onboarding_complete=getattr(current_user, "onboarding_complete", False),
    )


@app.post("/auth/complete-onboarding")
def complete_onboarding(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Mark onboarding as complete for the authenticated user."""
    current_user.onboarding_complete = True
    session.add(current_user)
    session.commit()
    return {"message": "Onboarding complete"}


@app.put("/auth/password")
def change_password(
    req: ChangePasswordRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Change the authenticated user's password.
    Returns 400 (not 401) for wrong current password — user IS authenticated,
    just the old password is wrong. 401 would trigger frontend session expiry.
    Existing JWT tokens remain valid after password change (no blacklist yet).
    """
    # Verify current password
    if not verify_password(req.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    # Validate new password length
    if len(req.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")

    # Reject if new password is same as current
    if verify_password(req.new_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="New password must be different from current password")

    # Hash and save
    current_user.hashed_password = hash_password(req.new_password)
    session.add(current_user)
    session.commit()
    return {"message": "Password updated successfully"}


# -- Admin dependency ---------------------------------------------------------
def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Requires is_admin=True. Returns 403 for non-admin users."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@app.delete("/auth/account")
def delete_account(
    req: DeleteAccountRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Permanently delete the authenticated user's account and ALL their data.
    Requires confirmation string "DELETE" as a UX guard.
    Deletes in FK dependency order to avoid constraint violations.
    Single commit after all deletes — atomic: if anything fails, nothing is deleted.
    """
    if req.confirmation != "DELETE":
        raise HTTPException(
            status_code=400,
            detail='Type DELETE to confirm account deletion'
        )

    user_id = current_user.id
    email   = current_user.email

    # Delete in FK dependency order
    # 1. PoolEntry (references FixedExpenseTemplate)
    pool_entries = session.exec(select(PoolEntry).where(PoolEntry.user_id == user_id)).all()
    for row in pool_entries:
        session.delete(row)

    # 2. Expense (may reference FixedExpenseTemplate)
    expenses = session.exec(select(Expense).where(Expense.user_id == user_id)).all()
    for row in expenses:
        session.delete(row)

    # 3. IncomeEntry
    incomes = session.exec(select(IncomeEntry).where(IncomeEntry.user_id == user_id)).all()
    for row in incomes:
        session.delete(row)

    # 4. BudgetLimit
    budgets = session.exec(select(BudgetLimit).where(BudgetLimit.user_id == user_id)).all()
    for row in budgets:
        session.delete(row)

    # 5. ExpenseTemplate
    templates = session.exec(select(ExpenseTemplate).where(ExpenseTemplate.user_id == user_id)).all()
    for row in templates:
        session.delete(row)

    # 6. FixedExpenseTemplate
    fixed_tmpls = session.exec(select(FixedExpenseTemplate).where(FixedExpenseTemplate.user_id == user_id)).all()
    for row in fixed_tmpls:
        session.delete(row)

    # 7. User record itself
    session.delete(current_user)

    # Single commit — atomic: all or nothing
    session.commit()

    return {"message": "Account deleted", "email": email}


# ── Variable Expense Endpoints ────────────────────────────────────────────────

@app.post("/expenses/parse")
@limiter.limit("30/hour")
def parse_and_save(request: Request, input: ExpenseInput, session: Session = Depends(get_session),
                   current_user: User = Depends(get_current_user)):
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
            paid=True,
            month_key=month_key,
            user_id=current_user.id,
        )
        session.add(exp)
        saved.append(item)

    session.commit()
    warnings = check_budget_warnings(session, month_key, user_id=current_user.id)
    balance  = get_balance_summary(session, month_key, user_id=current_user.id)
    return {"saved": saved, "warnings": warnings, "balance": balance}


@app.post("/expenses/manual")
@limiter.limit("300/hour")
def add_manual_expense(request: Request, exp: ManualExpense, session: Session = Depends(get_session),
                       current_user: User = Depends(get_current_user)):
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
        user_id=current_user.id,
    )
    session.add(new_exp)
    session.commit()
    session.refresh(new_exp)
    warnings = check_budget_warnings(session, month_key, user_id=current_user.id)
    return {"expense": new_exp, "warnings": warnings}


@app.get("/expenses/{month_key}")
@limiter.limit("300/hour")
def get_expenses(request: Request, month_key: str, session: Session = Depends(get_session),
                 current_user: User = Depends(get_current_user)):
    return session.exec(
        select(Expense).where(
            Expense.month_key == month_key,
            Expense.user_id == current_user.id,
        ).order_by(Expense.date.desc(), Expense.id.desc())
    ).all()


@app.patch("/expenses/{expense_id}")
def edit_expense(expense_id: int, update: ExpenseUpdate, session: Session = Depends(get_session),
                 current_user: User = Depends(get_current_user)):
    exp = session.get(Expense, expense_id)
    if not exp or exp.is_fixed or exp.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Expense not found")
    if update.vendor is not None:       exp.vendor   = update.vendor
    if update.amount is not None:       exp.amount   = update.amount
    if update.category is not None:     exp.category = update.category
    if update.note is not None:         exp.note     = update.note
    if update.expense_date is not None:
        exp.date      = date.fromisoformat(update.expense_date)
        exp.month_key = get_month_key(exp.date)
    session.add(exp)
    session.commit()
    session.refresh(exp)
    return exp


@app.post("/expenses/bulk-delete")
def bulk_delete_expenses(req: BulkDeleteRequest, session: Session = Depends(get_session),
                         current_user: User = Depends(get_current_user)):
    deleted = []
    for expense_id in req.ids:
        exp = session.get(Expense, expense_id)
        if exp and not exp.is_fixed and exp.user_id == current_user.id:
            session.delete(exp)
            deleted.append(expense_id)
    session.commit()
    return {"deleted": deleted, "count": len(deleted)}


@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int, session: Session = Depends(get_session),
                   current_user: User = Depends(get_current_user)):
    exp = session.get(Expense, expense_id)
    if not exp or exp.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Expense not found")
    session.delete(exp)
    session.commit()
    return {"deleted": expense_id}


# ── Fixed Expense: Monthly Tick ───────────────────────────────────────────────

@app.get("/fixed/{month_key}")
def get_fixed_expenses(month_key: str, session: Session = Depends(get_session),
                       current_user: User = Depends(get_current_user)):
    seed_fixed_expenses(session, month_key, user_id=current_user.id)
    return session.exec(
        select(Expense).where(
            Expense.month_key == month_key,
            Expense.is_fixed == True,
            Expense.user_id == current_user.id,
        ).order_by(Expense.category, Expense.vendor)
    ).all()


@app.patch("/fixed/{expense_id}/toggle")
def toggle_paid(expense_id: int, session: Session = Depends(get_session),
                current_user: User = Depends(get_current_user)):
    exp = session.get(Expense, expense_id)
    if not exp or not exp.is_fixed or exp.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Fixed expense not found")
    exp.paid = not exp.paid
    session.add(exp)
    session.commit()
    session.refresh(exp)
    return exp


@app.patch("/fixed/{expense_id}/amount")
def update_fixed_amount(expense_id: int, amount: float, session: Session = Depends(get_session),
                        current_user: User = Depends(get_current_user)):
    exp = session.get(Expense, expense_id)
    if not exp or not exp.is_fixed or exp.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Fixed expense not found")
    exp.amount = amount
    session.add(exp)
    session.commit()
    session.refresh(exp)
    return exp


# ── Expense Templates (Favourites) ────────────────────────────────────────────

@app.get("/expense-templates")
def list_expense_templates(session: Session = Depends(get_session),
                           current_user: User = Depends(get_current_user)):
    return session.exec(
        select(ExpenseTemplate).where(
            ExpenseTemplate.is_active == True,
            ExpenseTemplate.user_id == current_user.id,
        ).order_by(ExpenseTemplate.use_count.desc())
    ).all()


@app.post("/expense-templates")
def create_expense_template(tmpl: ExpenseTemplateCreate, session: Session = Depends(get_session),
                            current_user: User = Depends(get_current_user)):
    new = ExpenseTemplate(
        name=tmpl.name, vendor=tmpl.vendor,
        category=tmpl.category, amount=tmpl.amount,
        user_id=current_user.id,
    )
    session.add(new)
    session.commit()
    session.refresh(new)
    return new


@app.put("/expense-templates/{tmpl_id}")
def update_expense_template(tmpl_id: int, update: ExpenseTemplateUpdate,
                            session: Session = Depends(get_session),
                            current_user: User = Depends(get_current_user)):
    tmpl = session.get(ExpenseTemplate, tmpl_id)
    if not tmpl or tmpl.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Template not found")
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(tmpl, field, value)
    session.add(tmpl)
    session.commit()
    session.refresh(tmpl)
    return tmpl


@app.delete("/expense-templates/{tmpl_id}")
def delete_expense_template(tmpl_id: int, session: Session = Depends(get_session),
                            current_user: User = Depends(get_current_user)):
    tmpl = session.get(ExpenseTemplate, tmpl_id)
    if not tmpl or tmpl.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Template not found")
    tmpl.is_active = False
    session.add(tmpl)
    session.commit()
    return {"deleted": tmpl_id}


@app.post("/expense-templates/{tmpl_id}/log")
def log_from_template(tmpl_id: int, expense_date: Optional[str] = None,
                      session: Session = Depends(get_session),
                      current_user: User = Depends(get_current_user)):
    tmpl = session.get(ExpenseTemplate, tmpl_id)
    if not tmpl or tmpl.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Template not found")
    exp_date  = date.fromisoformat(expense_date) if expense_date else date.today()
    month_key = get_month_key(exp_date)
    exp = Expense(
        date=exp_date, vendor=tmpl.vendor, amount=tmpl.amount,
        category=tmpl.category, note=f"Quick-add: {tmpl.name}",
        is_fixed=False, paid=True, month_key=month_key,
        user_id=current_user.id,
    )
    session.add(exp)
    tmpl.use_count += 1
    session.add(tmpl)
    session.commit()
    session.refresh(exp)
    warnings = check_budget_warnings(session, month_key, user_id=current_user.id)
    balance  = get_balance_summary(session, month_key, user_id=current_user.id)
    return {"expense": exp, "warnings": warnings, "balance": balance}


# ── Income Check ──────────────────────────────────────────────────────────────

@app.get("/income/check/{month_key}")
def check_income_set(month_key: str, session: Session = Depends(get_session),
                     current_user: User = Depends(get_current_user)):
    entry = session.exec(
        select(IncomeEntry).where(
            IncomeEntry.month_key == month_key,
            IncomeEntry.user_id == current_user.id,
        )
    ).first()
    return {"is_set": entry is not None, "month_key": month_key}


# ── Fixed Due Reminders ───────────────────────────────────────────────────────

@app.get("/fixed/due-reminders/{month_key}")
def get_due_reminders(month_key: str, session: Session = Depends(get_session),
                      current_user: User = Depends(get_current_user)):
    from datetime import date as dt
    today = dt.today()
    expenses = session.exec(
        select(Expense).where(
            Expense.month_key == month_key,
            Expense.is_fixed == True,
            Expense.paid == False,
            Expense.user_id == current_user.id,
        )
    ).all()
    reminders = []
    for exp in expenses:
        tmpl = session.get(FixedExpenseTemplate, exp.fixed_template_id) \
               if exp.fixed_template_id else None
        if tmpl and tmpl.user_id != current_user.id:
            continue
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


# ── Fixed Expense Templates (CRUD) ────────────────────────────────────────────

@app.get("/fixed-templates")
def list_templates(session: Session = Depends(get_session),
                   current_user: User = Depends(get_current_user)):
    return session.exec(
        select(FixedExpenseTemplate).where(
            FixedExpenseTemplate.user_id == current_user.id,
        ).order_by(FixedExpenseTemplate.sort_order, FixedExpenseTemplate.id)
    ).all()


@app.post("/fixed-templates")
def create_template(tmpl: FixedTemplateCreate, session: Session = Depends(get_session),
                    current_user: User = Depends(get_current_user)):
    new = FixedExpenseTemplate(
        name=tmpl.name,
        category=tmpl.category,
        amount=tmpl.amount,
        sort_order=tmpl.sort_order or 0,
        template_type=tmpl.template_type or "fixed",
        user_id=current_user.id,
    )
    session.add(new)
    session.commit()
    session.refresh(new)
    return new


@app.put("/fixed-templates/{template_id}")
def update_template(
    template_id: int,
    update: FixedTemplateUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    tmpl = session.get(FixedExpenseTemplate, template_id)
    if not tmpl or tmpl.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Template not found")
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(tmpl, field, value)
    session.add(tmpl)
    session.commit()
    session.refresh(tmpl)

    # Sync name/amount changes to already-seeded Expense rows for current+future months.
    # Without this, the Fixed tab keeps showing the old values until next month's seed.
    if update.name is not None or update.amount is not None:
        current_month = get_month_key()
        seeded_rows = session.exec(
            select(Expense).where(
                Expense.fixed_template_id == template_id,
                Expense.month_key >= current_month,
                Expense.user_id == current_user.id,
            )
        ).all()
        for row in seeded_rows:
            if update.name is not None:
                row.vendor = tmpl.name
            if update.amount is not None:
                row.amount = tmpl.amount
            session.add(row)
        if seeded_rows:
            session.commit()

    return tmpl


@app.delete("/fixed-templates/{template_id}")
def delete_template(template_id: int, session: Session = Depends(get_session),
                    current_user: User = Depends(get_current_user)):
    tmpl = session.get(FixedExpenseTemplate, template_id)
    if not tmpl or tmpl.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Template not found")
    tmpl.is_active = False
    session.add(tmpl)
    current_month = get_month_key()
    rows_to_delete = session.exec(
        select(Expense).where(
            Expense.fixed_template_id == template_id,
            Expense.month_key >= current_month,
            Expense.user_id == current_user.id,
        )
    ).all()
    for row in rows_to_delete:
        session.delete(row)
    session.commit()
    return {"deleted": template_id, "expense_rows_removed": len(rows_to_delete)}


# ── Summary & Budget ──────────────────────────────────────────────────────────

@app.get("/summary/{month_key}")
@limiter.limit("300/hour")
def get_summary(request: Request, month_key: str, session: Session = Depends(get_session),
                current_user: User = Depends(get_current_user)):
    seed_fixed_expenses(session, month_key, user_id=current_user.id)
    balance      = get_balance_summary(session, month_key, user_id=current_user.id)
    warnings     = check_budget_warnings(session, month_key, user_id=current_user.id)
    spent_by_cat = get_monthly_spent_by_category(session, month_key, user_id=current_user.id)
    limits       = get_budget_limits(session, user_id=current_user.id)

    fixed_exps = session.exec(
        select(Expense).where(
            Expense.month_key == month_key,
            Expense.is_fixed == True,
            Expense.user_id == current_user.id,
        )
    ).all()
    fixed_paid = sum(1 for e in fixed_exps if e.paid)

    all_cats = set(spent_by_cat.keys()) | set(limits.keys())
    categories = []
    for cat in sorted(all_cats):
        spent = spent_by_cat.get(cat, 0)
        limit = limits.get(cat, 0)
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
def get_current_summary(session: Session = Depends(get_session),
                        current_user: User = Depends(get_current_user)):
    return get_summary(get_month_key(), session, current_user)


@app.put("/budget")
def update_budget(update: BudgetUpdate, session: Session = Depends(get_session),
                  current_user: User = Depends(get_current_user)):
    bl = session.exec(
        select(BudgetLimit).where(
            BudgetLimit.category == update.category,
            BudgetLimit.user_id == current_user.id,
        )
    ).first()
    if bl:
        bl.limit_amount = update.limit_amount
    else:
        bl = BudgetLimit(
            category=update.category,
            limit_amount=update.limit_amount,
            user_id=current_user.id,
        )
        session.add(bl)
    session.commit()
    return {"category": update.category, "limit": update.limit_amount}


@app.get("/budgets")
def list_budgets(session: Session = Depends(get_session),
                 current_user: User = Depends(get_current_user)):
    return session.exec(
        select(BudgetLimit).where(BudgetLimit.user_id == current_user.id)
    ).all()


@app.post("/income")
def upsert_income(income: IncomeInput, session: Session = Depends(get_session),
                  current_user: User = Depends(get_current_user)):
    month_key = income.month_key or get_month_key()
    # Upsert by (month_key, user_id, source) so each source is independent
    existing = session.exec(
        select(IncomeEntry).where(
            IncomeEntry.month_key == month_key,
            IncomeEntry.user_id == current_user.id,
            IncomeEntry.source == income.source,
        )
    ).first()
    if existing:
        existing.amount = income.amount
        existing.note   = income.note
        session.add(existing)
    else:
        entry = IncomeEntry(
            source=income.source, amount=income.amount,
            month_key=month_key, note=income.note,
            user_id=current_user.id,
        )
        session.add(entry)
    session.commit()
    return {"month_key": month_key, "source": income.source, "amount": income.amount}


@app.get("/income/{month_key}/all")
def get_all_income(month_key: str, session: Session = Depends(get_session),
                   current_user: User = Depends(get_current_user)):
    """Return all income entries for the month as a list."""
    entries = session.exec(
        select(IncomeEntry).where(
            IncomeEntry.month_key == month_key,
            IncomeEntry.user_id == current_user.id,
        )
    ).all()
    return [{"id": e.id, "source": e.source, "amount": e.amount, "note": e.note} for e in entries]


@app.delete("/income/{income_id}")
def delete_income(income_id: int, session: Session = Depends(get_session),
                  current_user: User = Depends(get_current_user)):
    entry = session.exec(
        select(IncomeEntry).where(
            IncomeEntry.id == income_id,
            IncomeEntry.user_id == current_user.id,
        )
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Income entry not found")
    session.delete(entry)
    session.commit()
    return {"deleted": income_id}


@app.get("/income/{month_key}")
def get_income(month_key: str, session: Session = Depends(get_session),
               current_user: User = Depends(get_current_user)):
    entry = session.exec(
        select(IncomeEntry).where(
            IncomeEntry.month_key == month_key,
            IncomeEntry.user_id == current_user.id,
        )
    ).first()
    if entry:
        return {"source": entry.source, "amount": entry.amount, "note": entry.note}
    default_income = int(os.getenv("DEFAULT_MONTHLY_INCOME", "0"))
    return {"source": "Salary", "amount": default_income, "note": None}


@app.get("/months")
def list_months(session: Session = Depends(get_session),
                current_user: User = Depends(get_current_user)):
    expenses = session.exec(
        select(Expense.month_key).where(
            Expense.user_id == current_user.id
        ).distinct()
    ).all()
    return sorted(set(expenses), reverse=True)


@app.post("/seed/{month_key}")
def seed_month(month_key: str, session: Session = Depends(get_session),
               current_user: User = Depends(get_current_user)):
    seed_fixed_expenses(session, month_key, user_id=current_user.id)
    return {"seeded": month_key}


# ── Insights ──────────────────────────────────────────────────────────────────

@app.get("/insights/mom/{month_key}")
def month_over_month(month_key: str, session: Session = Depends(get_session),
                     current_user: User = Depends(get_current_user)):
    import calendar
    year, month = map(int, month_key.split("-"))
    months = []
    for offset in range(2, -1, -1):
        m = month - offset
        y = year
        while m <= 0:
            m += 12
            y -= 1
        months.append(f"{y:04d}-{m:02d}")

    expenses = session.exec(
        select(Expense).where(
            Expense.month_key.in_(months),
            Expense.is_fixed == False,
            Expense.user_id == current_user.id,
        )
    ).all()

    data: dict[str, dict[str, float]] = {}
    for e in expenses:
        data.setdefault(e.category, {})
        data[e.category][e.month_key] = data[e.category].get(e.month_key, 0) + e.amount

    incomes = session.exec(
        select(IncomeEntry).where(
            IncomeEntry.month_key.in_(months),
            IncomeEntry.user_id == current_user.id,
        )
    ).all()
    income_map = {i.month_key: i.amount for i in incomes}

    return {"months": months, "categories": data, "income": income_map}


@app.get("/insights/top-spends/{month_key}")
def top_spends(month_key: str, limit: int = 5, session: Session = Depends(get_session),
               current_user: User = Depends(get_current_user)):
    expenses = session.exec(
        select(Expense).where(
            Expense.month_key == month_key,
            Expense.is_fixed == False,
            Expense.user_id == current_user.id,
        ).order_by(Expense.amount.desc())
    ).all()
    return [
        {"id": e.id, "vendor": e.vendor, "amount": e.amount,
         "category": e.category, "date": e.date.isoformat(), "note": e.note}
        for e in expenses[:limit]
    ]


@app.get("/insights/projection/{month_key}")
def budget_projection(month_key: str, session: Session = Depends(get_session),
                      current_user: User = Depends(get_current_user)):
    import calendar
    from datetime import date as dt
    year, month = map(int, month_key.split("-"))
    days_in_month = calendar.monthrange(year, month)[1]
    today = dt.today()

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
            Expense.user_id == current_user.id,
        )
    ).all()

    limits_rows = session.exec(
        select(BudgetLimit).where(BudgetLimit.user_id == current_user.id)
    ).all()
    limits = {bl.category: bl.limit_amount for bl in limits_rows}

    cat_spent: dict[str, float] = {}
    for e in expenses:
        cat_spent[e.category] = cat_spent.get(e.category, 0) + e.amount

    projections = []
    for cat, limit in limits.items():
        spent      = cat_spent.get(cat, 0)
        daily_rate = spent / days_elapsed
        projected  = daily_rate * days_in_month
        days_left  = days_in_month - days_elapsed
        if limit > 0:
            projections.append({
                "category": cat,
                "spent": spent,
                "limit": limit,
                "projected": round(projected),
                "daily_rate": round(daily_rate, 1),
                "days_left": days_left,
                "budget_left": max(limit - spent, 0),
                "pct_spent": round(spent / limit * 100, 1),
                "pct_projected": round(projected / limit * 100, 1),
                "status": (
                    "over"    if spent > limit else
                    "danger"  if projected > limit else
                    "warning" if projected > limit * 0.85 else
                    "safe"
                ),
            })
    return sorted(projections, key=lambda x: x["pct_projected"], reverse=True)


# ── Data Export ─────────────────────────────────────────────────────────────
# NOTE: /export/csv/all MUST be defined before /export/csv/{month_key}
# to prevent FastAPI treating the literal string "all" as a month_key value.

@app.get("/export/csv/all")
@limiter.limit("20/hour")
def export_all_csv(
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Export all expenses for the authenticated user as a CSV file.
    Defence in depth: user_id filter applied even though endpoint is JWT-protected.
    """
    expenses = session.exec(
        select(Expense)
        .where(Expense.user_id == current_user.id)
        .order_by(Expense.date)
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header row — month column first, then standard columns
    writer.writerow(["month", "date", "vendor", "category", "amount", "note", "type", "paid"])

    for e in expenses:
        writer.writerow([
            e.month_key,
            e.date.isoformat() if e.date else "",
            e.vendor,
            e.category,
            e.amount,
            e.note or "",
            "fixed" if e.is_fixed else "variable",
            "yes" if e.paid else "no",
        ])

    output.seek(0)
    today = date.today().isoformat()
    filename = f"walletMantra_all_{today}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/export/csv/{month_key}")
@limiter.limit("20/hour")
def export_month_csv(
    request: Request,
    month_key: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Export expenses for a specific month as a CSV file.
    Defence in depth: user_id filter applied even though endpoint is JWT-protected.
    Returns a header-only CSV if no expenses exist for the month.
    """
    expenses = session.exec(
        select(Expense)
        .where(
            Expense.month_key == month_key,
            Expense.user_id == current_user.id,
        )
        .order_by(Expense.date)
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow(["date", "vendor", "category", "amount", "note", "type", "paid"])

    for e in expenses:
        writer.writerow([
            e.date.isoformat() if e.date else "",
            e.vendor,
            e.category,
            e.amount,
            e.note or "",
            "fixed" if e.is_fixed else "variable",
            "yes" if e.paid else "no",
        ])

    output.seek(0)
    filename = f"walletMantra_{month_key}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ── Pool Entries (Essential Pools) ────────────────────────────────────────────

@app.get("/pools/{month_key}")
def get_pools_for_month(month_key: str, session: Session = Depends(get_session),
                        current_user: User = Depends(get_current_user)):
    pool_templates = session.exec(
        select(FixedExpenseTemplate).where(
            FixedExpenseTemplate.is_active == True,
            FixedExpenseTemplate.template_type == "pool",
            FixedExpenseTemplate.user_id == current_user.id,
        ).order_by(FixedExpenseTemplate.sort_order, FixedExpenseTemplate.id)
    ).all()

    result = []
    for tmpl in pool_templates:
        entries = session.exec(
            select(PoolEntry).where(
                PoolEntry.pool_template_id == tmpl.id,
                PoolEntry.month_key == month_key,
                PoolEntry.user_id == current_user.id,
            ).order_by(PoolEntry.created_at)
        ).all()
        paid_total   = sum(e.amount for e in entries if e.paid)
        unpaid_total = sum(e.amount for e in entries if not e.paid)
        result.append({
            "id": tmpl.id,
            "name": tmpl.name,
            "category": tmpl.category,
            "entries": [
                {"id": e.id, "label": e.label, "amount": e.amount,
                 "paid": e.paid, "paid_date": e.paid_date.isoformat() if e.paid_date else None,
                 "note": e.note}
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
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    tmpl = session.get(FixedExpenseTemplate, pool_template_id)
    if not tmpl or tmpl.template_type != "pool" or tmpl.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Pool template not found")
    new_entry = PoolEntry(
        pool_template_id=pool_template_id,
        month_key=month_key,
        label=entry.label,
        amount=entry.amount,
        paid=True,
        paid_date=date.today(),
        note=entry.note,
        user_id=current_user.id,
    )
    session.add(new_entry)
    session.commit()
    session.refresh(new_entry)
    return new_entry


@app.patch("/pools/entries/{entry_id}")
def update_pool_entry(
    entry_id: int,
    update: PoolEntryUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    entry = session.get(PoolEntry, entry_id)
    if not entry or entry.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Pool entry not found")
    if update.label is not None:  entry.label  = update.label
    if update.amount is not None: entry.amount = update.amount
    if update.note is not None:   entry.note   = update.note
    if update.paid is not None:
        entry.paid      = update.paid
        entry.paid_date = date.today() if update.paid else None
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@app.patch("/pools/entries/{entry_id}/toggle")
def toggle_pool_entry_paid(entry_id: int, session: Session = Depends(get_session),
                           current_user: User = Depends(get_current_user)):
    entry = session.get(PoolEntry, entry_id)
    if not entry or entry.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Pool entry not found")
    entry.paid      = not entry.paid
    entry.paid_date = date.today() if entry.paid else None
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@app.delete("/pools/entries/{entry_id}")
def delete_pool_entry(entry_id: int, session: Session = Depends(get_session),
                      current_user: User = Depends(get_current_user)):
    entry = session.get(PoolEntry, entry_id)
    if not entry or entry.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Pool entry not found")
    session.delete(entry)
    session.commit()
    return {"deleted": entry_id}


# -- Admin Endpoints ----------------------------------------------------------

@app.get("/admin/stats")
def admin_stats(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_admin_user),
):
    """Overall system stats. Admin only."""
    total_users    = session.exec(select(func.count(User.id))).one()
    active_users   = session.exec(
        select(func.count(User.id)).where(User.is_active == True)
    ).one()
    total_expenses = session.exec(select(func.count(Expense.id))).one()
    return {"total_users": total_users, "active_users": active_users,
            "total_expenses": total_expenses}


@app.get("/admin/users")
def admin_list_users(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_admin_user),
):
    """List all users with stats. Admin only."""
    users = session.exec(select(User).order_by(User.created_at.desc())).all()
    result = []
    for user in users:
        expense_count = session.exec(
            select(func.count(Expense.id)).where(Expense.user_id == user.id)
        ).one()
        result.append({
            "id": user.id, "email": user.email,
            "is_active": user.is_active, "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "onboarding_complete": user.onboarding_complete,
            "expense_count": expense_count,
        })
    return result


@app.patch("/admin/users/{user_id}/toggle-active")
def admin_toggle_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_admin_user),
):
    """Enable or disable a user account. Admin only. Cannot disable own account."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot disable your own account")
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = not user.is_active
    session.add(user)
    session.commit()
    return {"id": user.id, "email": user.email, "is_active": user.is_active}
