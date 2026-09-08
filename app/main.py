"""FastAPI application entry point for practice 1."""

from fastapi import FastAPI, HTTPException, status

from app import storage
from app.schemas import TagCreate, TagRead, TransactionCreate, TransactionRead, TransactionUpdate


app = FastAPI(
    title="Personal Finance Service",
    description="API for managing personal income, expenses, budgets, and accounts.",
    version="0.1.0",
)


def get_transaction_or_404(transaction_id: int) -> TransactionRead:
    transaction = storage.transactions.get(transaction_id)
    if transaction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return transaction


def validate_references(account_id: int, category_id: int, tag_ids: list[int]) -> tuple[object, object, list[TagRead]]:
    account = storage.accounts.get(account_id)
    category = storage.categories.get(category_id)
    missing_tag_ids = [tag_id for tag_id in tag_ids if tag_id not in storage.tags]
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    if missing_tag_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tags not found: {missing_tag_ids}")
    return account, category, [storage.tags[tag_id] for tag_id in tag_ids]


@app.get("/", tags=["service"])
def read_root() -> dict[str, str]:
    """Return a small health message for the base application."""
    return {"message": "Personal Finance Service is running"}


@app.get("/transactions", response_model=list[TransactionRead], tags=["transactions"])
def list_transactions() -> list[TransactionRead]:
    """Return every operation from the temporary storage."""
    return list(storage.transactions.values())


@app.get("/transactions/{transaction_id}", response_model=TransactionRead, tags=["transactions"])
def get_transaction(transaction_id: int) -> TransactionRead:
    """Return one operation with its account, category, and tags."""
    return get_transaction_or_404(transaction_id)


@app.post("/transactions", response_model=TransactionRead, status_code=status.HTTP_201_CREATED, tags=["transactions"])
def create_transaction(transaction: TransactionCreate) -> TransactionRead:
    """Create a financial operation in the temporary storage."""
    account, category, transaction_tags = validate_references(transaction.account_id, transaction.category_id, transaction.tag_ids)
    new_id = max(storage.transactions, default=0) + 1
    created = TransactionRead(id=new_id, amount=transaction.amount, kind=transaction.kind, operation_date=transaction.operation_date, description=transaction.description, account=account, category=category, tags=transaction_tags)
    storage.transactions[new_id] = created
    return created


@app.patch("/transactions/{transaction_id}", response_model=TransactionRead, tags=["transactions"])
def update_transaction(transaction_id: int, transaction: TransactionUpdate) -> TransactionRead:
    """Partially update an operation in the temporary storage."""
    existing = get_transaction_or_404(transaction_id)
    changes = transaction.model_dump(exclude_unset=True)
    account = existing.account
    category = existing.category
    transaction_tags = existing.tags
    if "account_id" in changes or "category_id" in changes or "tag_ids" in changes:
        account, category, transaction_tags = validate_references(changes.get("account_id", account.id), changes.get("category_id", category.id), changes.get("tag_ids", [tag.id for tag in transaction_tags]))
    updated = TransactionRead(id=transaction_id, amount=changes.get("amount", existing.amount), kind=changes.get("kind", existing.kind), operation_date=changes.get("operation_date", existing.operation_date), description=changes.get("description", existing.description), account=account, category=category, tags=transaction_tags)
    storage.transactions[transaction_id] = updated
    return updated


@app.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["transactions"])
def delete_transaction(transaction_id: int) -> None:
    """Delete an operation from the temporary storage."""
    get_transaction_or_404(transaction_id)
    del storage.transactions[transaction_id]


@app.get("/tags", response_model=list[TagRead], tags=["tags"])
def list_tags() -> list[TagRead]:
    """Return tags available for attaching to operations."""
    return list(storage.tags.values())


@app.post("/tags", response_model=TagRead, status_code=status.HTTP_201_CREATED, tags=["tags"])
def create_tag(tag: TagCreate) -> TagRead:
    """Create a tag in the temporary storage."""
    new_id = max(storage.tags, default=0) + 1
    created = TagRead(id=new_id, **tag.model_dump())
    storage.tags[new_id] = created
    return created
