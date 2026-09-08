"""Pydantic schemas used by the temporary API."""

from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class Currency(str, Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class OperationKind(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class AccountBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    balance: Decimal
    currency: Currency = Currency.RUB


class AccountCreate(AccountBase):
    pass


class AccountRead(AccountBase):
    id: int


class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    kind: OperationKind
    color: str = Field(default="#4F46E5", pattern=r"^#[0-9A-Fa-f]{6}$")


class CategoryRead(CategoryBase):
    id: int


class TagBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    color: str = Field(default="#64748B", pattern=r"^#[0-9A-Fa-f]{6}$")


class TagCreate(TagBase):
    pass


class TagRead(TagBase):
    id: int


class TransactionCreate(BaseModel):
    account_id: int
    category_id: int
    tag_ids: list[int] = Field(default_factory=list)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    kind: OperationKind
    operation_date: date
    description: str = Field(default="", max_length=500)


class TransactionUpdate(BaseModel):
    account_id: int | None = None
    category_id: int | None = None
    tag_ids: list[int] | None = None
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    kind: OperationKind | None = None
    operation_date: date | None = None
    description: str | None = Field(default=None, max_length=500)


class TransactionRead(BaseModel):
    id: int
    amount: Decimal
    kind: OperationKind
    operation_date: date
    description: str
    account: AccountRead
    category: CategoryRead
    tags: list[TagRead]
