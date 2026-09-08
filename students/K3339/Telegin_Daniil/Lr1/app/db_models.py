"""SQLModel tables for the personal finance service."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, text
from sqlmodel import Field, Relationship, SQLModel

from app.schemas import Currency, OperationKind


class TransactionTagLink(SQLModel, table=True):
    """Many-to-many link with the moment a tag was applied."""
    transaction_id: int | None = Field(default=None, foreign_key="transaction.id", primary_key=True)
    tag_id: int | None = Field(default=None, foreign_key="tag.id", primary_key=True)
    applied_at: datetime = Field(sa_column=Column(DateTime(timezone=False), nullable=False, server_default=text("CURRENT_TIMESTAMP")))


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, max_length=255)
    password_hash: str = Field(max_length=255)
    full_name: str = Field(max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    accounts: list["Account"] = Relationship(back_populates="user")
    categories: list["Category"] = Relationship(back_populates="user")
    budgets: list["Budget"] = Relationship(back_populates="user")
    tags: list["Tag"] = Relationship(back_populates="user")


class Account(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    name: str = Field(max_length=100)
    balance: Decimal = Field(max_digits=12, decimal_places=2)
    currency: Currency = Field(default=Currency.RUB)
    user: User = Relationship(back_populates="accounts")
    transactions: list["Transaction"] = Relationship(back_populates="account")


class Category(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    name: str = Field(max_length=100)
    kind: OperationKind
    color: str = Field(default="#4F46E5", max_length=7)
    user: User = Relationship(back_populates="categories")
    transactions: list["Transaction"] = Relationship(back_populates="category")
    budgets: list["Budget"] = Relationship(back_populates="category")


class Budget(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    category_id: int = Field(foreign_key="category.id", index=True)
    amount_limit: Decimal = Field(max_digits=12, decimal_places=2)
    period_start: date
    period_end: date
    user: User = Relationship(back_populates="budgets")
    category: Category = Relationship(back_populates="budgets")


class Tag(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    name: str = Field(max_length=50)
    color: str = Field(default="#64748B", max_length=7)
    user: User = Relationship(back_populates="tags")
    transactions: list["Transaction"] = Relationship(back_populates="tags", link_model=TransactionTagLink)


class Transaction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="account.id", index=True)
    category_id: int = Field(foreign_key="category.id", index=True)
    amount: Decimal = Field(max_digits=12, decimal_places=2)
    kind: OperationKind
    operation_date: date
    description: str = Field(default="", max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    account: Account = Relationship(back_populates="transactions")
    category: Category = Relationship(back_populates="transactions")
    tags: list[Tag] = Relationship(back_populates="transactions", link_model=TransactionTagLink)