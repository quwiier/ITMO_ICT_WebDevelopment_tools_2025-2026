"""FastAPI application backed by PostgreSQL through SQLModel."""

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.db_models import Account, Budget, Category, Tag, Transaction, User
from app.schemas import (
    AccountDbCreate,
    AccountRead,
    BudgetCreate,
    BudgetRead,
    CategoryDbCreate,
    CategoryRead,
    TagDbCreate,
    TagRead,
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
    UserCreate,
    UserRead,
)


app = FastAPI(
    title="Personal Finance Service",
    description="API for managing personal income, expenses, budgets, and accounts.",
    version="0.2.0",
)
SessionDep = Annotated[Session, Depends(get_session)]


def not_found(resource: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{resource} not found")


def get_user(session: Session, user_id: int) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise not_found("User")
    return user


def serialize_transaction(transaction: Transaction) -> TransactionRead:
    return TransactionRead(
        id=transaction.id,
        amount=transaction.amount,
        kind=transaction.kind,
        operation_date=transaction.operation_date,
        description=transaction.description,
        account=AccountRead.model_validate(transaction.account),
        category=CategoryRead.model_validate(transaction.category),
        tags=[TagRead.model_validate(tag) for tag in transaction.tags],
    )


def validate_transaction_references(session: Session, account_id: int, category_id: int, tag_ids: list[int]) -> tuple[Account, Category, list[Tag]]:
    account = session.get(Account, account_id)
    category = session.get(Category, category_id)
    tags = [session.get(Tag, tag_id) for tag_id in tag_ids]
    if account is None:
        raise not_found("Account")
    if category is None:
        raise not_found("Category")
    if any(tag is None for tag in tags):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more tags not found")
    return account, category, [tag for tag in tags if tag is not None]


@app.get("/", tags=["service"])
def read_root() -> dict[str, str]:
    return {"message": "Personal Finance Service is running"}


@app.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED, tags=["users"])
def create_user(payload: UserCreate, session: SessionDep) -> User:
    user = User(email=payload.email, full_name=payload.full_name, password_hash="not-configured")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@app.get("/users", response_model=list[UserRead], tags=["users"])
def list_users(session: SessionDep) -> list[User]:
    return list(session.exec(select(User)))


@app.post("/accounts", response_model=AccountRead, status_code=status.HTTP_201_CREATED, tags=["accounts"])
def create_account(payload: AccountDbCreate, session: SessionDep) -> Account:
    get_user(session, payload.user_id)
    account = Account.model_validate(payload)
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


@app.get("/accounts", response_model=list[AccountRead], tags=["accounts"])
def list_accounts(session: SessionDep) -> list[Account]:
    return list(session.exec(select(Account)))


@app.post("/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED, tags=["categories"])
def create_category(payload: CategoryDbCreate, session: SessionDep) -> Category:
    get_user(session, payload.user_id)
    category = Category.model_validate(payload)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@app.get("/categories", response_model=list[CategoryRead], tags=["categories"])
def list_categories(session: SessionDep) -> list[Category]:
    return list(session.exec(select(Category)))


@app.post("/tags", response_model=TagRead, status_code=status.HTTP_201_CREATED, tags=["tags"])
def create_tag(payload: TagDbCreate, session: SessionDep) -> Tag:
    get_user(session, payload.user_id)
    tag = Tag.model_validate(payload)
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


@app.get("/tags", response_model=list[TagRead], tags=["tags"])
def list_tags(session: SessionDep) -> list[Tag]:
    return list(session.exec(select(Tag)))


@app.post("/budgets", response_model=BudgetRead, status_code=status.HTTP_201_CREATED, tags=["budgets"])
def create_budget(payload: BudgetCreate, session: SessionDep) -> Budget:
    get_user(session, payload.user_id)
    if session.get(Category, payload.category_id) is None:
        raise not_found("Category")
    budget = Budget.model_validate(payload)
    session.add(budget)
    session.commit()
    session.refresh(budget)
    return budget


@app.get("/budgets", response_model=list[BudgetRead], tags=["budgets"])
def list_budgets(session: SessionDep) -> list[Budget]:
    return list(session.exec(select(Budget)))


@app.get("/transactions", response_model=list[TransactionRead], tags=["transactions"])
def list_transactions(session: SessionDep) -> list[TransactionRead]:
    return [serialize_transaction(transaction) for transaction in session.exec(select(Transaction))]


@app.get("/transactions/{transaction_id}", response_model=TransactionRead, tags=["transactions"])
def get_transaction(transaction_id: int, session: SessionDep) -> TransactionRead:
    transaction = session.get(Transaction, transaction_id)
    if transaction is None:
        raise not_found("Transaction")
    return serialize_transaction(transaction)


@app.post("/transactions", response_model=TransactionRead, status_code=status.HTTP_201_CREATED, tags=["transactions"])
def create_transaction(payload: TransactionCreate, session: SessionDep) -> TransactionRead:
    account, category, tags = validate_transaction_references(session, payload.account_id, payload.category_id, payload.tag_ids)
    transaction = Transaction(amount=payload.amount, kind=payload.kind, operation_date=payload.operation_date, description=payload.description, account=account, category=category, tags=tags)
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return serialize_transaction(transaction)


@app.patch("/transactions/{transaction_id}", response_model=TransactionRead, tags=["transactions"])
def update_transaction(transaction_id: int, payload: TransactionUpdate, session: SessionDep) -> TransactionRead:
    transaction = session.get(Transaction, transaction_id)
    if transaction is None:
        raise not_found("Transaction")
    changes = payload.model_dump(exclude_unset=True)
    if "account_id" in changes or "category_id" in changes or "tag_ids" in changes:
        account_id = changes.pop("account_id", transaction.account_id)
        category_id = changes.pop("category_id", transaction.category_id)
        tag_ids = changes.pop("tag_ids", [tag.id for tag in transaction.tags])
        account, category, tags = validate_transaction_references(session, account_id, category_id, tag_ids)
        transaction.account = account
        transaction.category = category
        transaction.tags = tags
    for field, value in changes.items():
        setattr(transaction, field, value)
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return serialize_transaction(transaction)


@app.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["transactions"])
def delete_transaction(transaction_id: int, session: SessionDep) -> None:
    transaction = session.get(Transaction, transaction_id)
    if transaction is None:
        raise not_found("Transaction")
    session.delete(transaction)
    session.commit()