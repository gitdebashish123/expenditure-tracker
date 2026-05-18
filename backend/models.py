from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import Optional
from datetime import datetime, date as DateT
import os

DATABASE_URL = "sqlite:///./data/expenses.db"
engine = create_engine(DATABASE_URL, echo=False)


class FixedExpenseTemplate(SQLModel, table=True):
    """Master list of fixed expenses — managed by the user, persists across months."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str                        # e.g. "Rent", "Car EMI", "Groww MF1"
    category: str                    # e.g. "Housing", "EMI", "Investments"
    amount: float
    is_active: bool = Field(default=True)   # soft delete / disable
    sort_order: int = Field(default=0)      # for display ordering
    created_at: datetime = Field(default_factory=datetime.now)


class Expense(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: DateT = Field(default_factory=DateT.today)
    vendor: str
    amount: float
    category: str
    note: Optional[str] = None
    is_fixed: bool = Field(default=False)
    paid: bool = Field(default=False)       # tick = paid/done for the month
    month_key: str                          # "2026-05" format
    fixed_template_id: Optional[int] = Field(default=None, foreign_key="fixedexpensetemplate.id")
    created_at: datetime = Field(default_factory=datetime.now)


class BudgetLimit(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    category: str = Field(unique=True)
    limit_amount: float


class IncomeEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: DateT = Field(default_factory=DateT.today)
    source: str
    amount: float
    month_key: str
    note: Optional[str] = None


def create_db():
    os.makedirs("data", exist_ok=True)
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
