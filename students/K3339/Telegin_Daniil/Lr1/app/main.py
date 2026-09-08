"""FastAPI application backed by PostgreSQL through SQLModel."""

from decimal import Decimal
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from app.database import get_session
from app.db_models import Account, Budget, Category, Tag, Transaction, User
from app.security import create_access_token, decode_access_token, hash_password, verify_password
from app.schemas import (
    AccountDbCreate,
    AccountRead,
    AccountUpdate,
    BudgetCreate,
    BudgetRead,
    BudgetUpdate,
    ChangePasswordRequest,
    CategoryDbCreate,
    CategoryRead,
    CategoryUpdate,
    AccessToken,
    LoginRequest,
    TagDbCreate,
    TagRead,
    TagUpdate,
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
    OperationKind,
    RegisterRequest,
    UserCreate,
    UserRead,
)


app = FastAPI(
    title="Personal Finance Service",
    description="API for managing personal income, expenses, budgets, and accounts.",
    version="0.2.0",
)
SessionDep = Annotated[Session, Depends(get_session)]
bearer_scheme = HTTPBearer()


def not_found(resource: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{resource} not found")


def get_user(session: Session, user_id: int) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise not_found("User")
    return user


def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)], session: SessionDep) -> User:
    """Return the user encoded in a valid Bearer JWT."""
    try:
        user_id = decode_access_token(credentials.credentials)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error)) from error
    return get_user(session, user_id)


CurrentUserDep = Annotated[User, Depends(get_current_user)]

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


def update_account_balance(account: Account, amount: Decimal, kind: OperationKind, reverse: bool = False) -> None:
    """Apply or reverse a transaction effect on an account balance."""
    change = amount if kind == OperationKind.INCOME else -amount
    account.balance += -change if reverse else change

@app.get("/", tags=["service"])
def read_root() -> dict[str, str]:
    return {"message": "Personal Finance Service is running"}


@app.post("/auth/register", response_model=UserRead, status_code=status.HTTP_201_CREATED, tags=["authentication"])
def register(payload: RegisterRequest, session: SessionDep) -> User:
    """Register a user and store only a bcrypt password hash."""
    existing = session.exec(select(User).where(User.email == payload.email)).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")
    user = User(email=payload.email, full_name=payload.full_name, password_hash=hash_password(payload.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@app.post("/auth/login", response_model=AccessToken, tags=["authentication"])
def login(payload: LoginRequest, session: SessionDep) -> AccessToken:
    """Authenticate with a password and issue a manually created HS256 JWT."""
    user = session.exec(select(User).where(User.email == payload.email)).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    return AccessToken(access_token=create_access_token(user.id))


@app.get("/auth/me", response_model=UserRead, tags=["authentication"])
def read_current_user(current_user: CurrentUserDep) -> User:
    """Return the authenticated user profile."""
    return current_user


@app.post("/auth/change-password", tags=["authentication"])
def change_password(payload: ChangePasswordRequest, current_user: CurrentUserDep, session: SessionDep) -> dict[str, str]:
    """Verify the current password and replace its bcrypt hash."""
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    current_user.password_hash = hash_password(payload.new_password)
    session.add(current_user)
    session.commit()
    return {"message": "Password updated"}

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
    update_account_balance(account, transaction.amount, transaction.kind)
    session.add(account)
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return serialize_transaction(transaction)


@app.patch("/transactions/{transaction_id}", response_model=TransactionRead, tags=["transactions"])
def update_transaction(transaction_id: int, payload: TransactionUpdate, session: SessionDep) -> TransactionRead:
    transaction = session.get(Transaction, transaction_id)
    if transaction is None:
        raise not_found("Transaction")
    previous_account = transaction.account
    update_account_balance(previous_account, transaction.amount, transaction.kind, reverse=True)
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
    update_account_balance(transaction.account, transaction.amount, transaction.kind)
    session.add(previous_account)
    session.add(transaction.account)
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return serialize_transaction(transaction)


@app.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["transactions"])
def delete_transaction(transaction_id: int, session: SessionDep) -> None:
    transaction = session.get(Transaction, transaction_id)
    if transaction is None:
        raise not_found("Transaction")
    update_account_balance(transaction.account, transaction.amount, transaction.kind, reverse=True)
    session.add(transaction.account)
    session.delete(transaction)
    session.commit()


def apply_changes(model: object, changes: dict[str, object]) -> None:
    for field, value in changes.items():
        setattr(model, field, value)


@app.get("/accounts/{account_id}", response_model=AccountRead, tags=["accounts"])
def get_account(account_id: int, session: SessionDep) -> Account:
    account = session.get(Account, account_id)
    if account is None:
        raise not_found("Account")
    return account


@app.patch("/accounts/{account_id}", response_model=AccountRead, tags=["accounts"])
def update_account(account_id: int, payload: AccountUpdate, session: SessionDep) -> Account:
    account = get_account(account_id, session)
    apply_changes(account, payload.model_dump(exclude_unset=True))
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


@app.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["accounts"])
def delete_account(account_id: int, session: SessionDep) -> None:
    account = get_account(account_id, session)
    session.delete(account)
    session.commit()


@app.get("/categories/{category_id}", response_model=CategoryRead, tags=["categories"])
def get_category(category_id: int, session: SessionDep) -> Category:
    category = session.get(Category, category_id)
    if category is None:
        raise not_found("Category")
    return category


@app.patch("/categories/{category_id}", response_model=CategoryRead, tags=["categories"])
def update_category(category_id: int, payload: CategoryUpdate, session: SessionDep) -> Category:
    category = get_category(category_id, session)
    apply_changes(category, payload.model_dump(exclude_unset=True))
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@app.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["categories"])
def delete_category(category_id: int, session: SessionDep) -> None:
    category = get_category(category_id, session)
    session.delete(category)
    session.commit()


@app.get("/tags/{tag_id}", response_model=TagRead, tags=["tags"])
def get_tag(tag_id: int, session: SessionDep) -> Tag:
    tag = session.get(Tag, tag_id)
    if tag is None:
        raise not_found("Tag")
    return tag


@app.patch("/tags/{tag_id}", response_model=TagRead, tags=["tags"])
def update_tag(tag_id: int, payload: TagUpdate, session: SessionDep) -> Tag:
    tag = get_tag(tag_id, session)
    apply_changes(tag, payload.model_dump(exclude_unset=True))
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


@app.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["tags"])
def delete_tag(tag_id: int, session: SessionDep) -> None:
    tag = get_tag(tag_id, session)
    session.delete(tag)
    session.commit()


@app.get("/budgets/{budget_id}", response_model=BudgetRead, tags=["budgets"])
def get_budget(budget_id: int, session: SessionDep) -> Budget:
    budget = session.get(Budget, budget_id)
    if budget is None:
        raise not_found("Budget")
    return budget


@app.patch("/budgets/{budget_id}", response_model=BudgetRead, tags=["budgets"])
def update_budget(budget_id: int, payload: BudgetUpdate, session: SessionDep) -> Budget:
    budget = get_budget(budget_id, session)
    apply_changes(budget, payload.model_dump(exclude_unset=True))
    session.add(budget)
    session.commit()
    session.refresh(budget)
    return budget


@app.delete("/budgets/{budget_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["budgets"])
def delete_budget(budget_id: int, session: SessionDep) -> None:
    budget = get_budget(budget_id, session)
    session.delete(budget)
    session.commit()