from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import Optional
from datetime import datetime, date as DateT
import os

DATABASE_URL = "sqlite:///./data/expenses.db"
engine = create_engine(DATABASE_URL, echo=False)


class Expense(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: DateT = Field(default_factory=DateT.today)
    vendor: str
    amount: float
    category: str
    note: Optional[str] = None
    is_fixed: bool = Field(default=False)
    month_key: str  # "2026-05" format
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
