"""In-memory data storage for practice 1."""

from datetime import date
from decimal import Decimal

from app.schemas import AccountRead, CategoryRead, Currency, OperationKind, TagRead, TransactionRead


accounts: dict[int, AccountRead] = {
    1: AccountRead(id=1, name="Основная карта", balance=Decimal("45000.00"), currency=Currency.RUB),
    2: AccountRead(id=2, name="Наличные", balance=Decimal("3200.00"), currency=Currency.RUB),
}
categories: dict[int, CategoryRead] = {
    1: CategoryRead(id=1, name="Продукты", kind=OperationKind.EXPENSE, color="#EF4444"),
    2: CategoryRead(id=2, name="Зарплата", kind=OperationKind.INCOME, color="#22C55E"),
    3: CategoryRead(id=3, name="Транспорт", kind=OperationKind.EXPENSE, color="#F59E0B"),
}
tags: dict[int, TagRead] = {
    1: TagRead(id=1, name="Дом", color="#8B5CF6"),
    2: TagRead(id=2, name="Работа", color="#0EA5E9"),
    3: TagRead(id=3, name="Регулярное", color="#64748B"),
}
transactions: dict[int, TransactionRead] = {
    1: TransactionRead(id=1, amount=Decimal("1520.50"), kind=OperationKind.EXPENSE, operation_date=date(2026, 9, 1), description="Покупки в супермаркете", account=accounts[1], category=categories[1], tags=[tags[1]]),
    2: TransactionRead(id=2, amount=Decimal("85000.00"), kind=OperationKind.INCOME, operation_date=date(2026, 9, 5), description="Зарплата за август", account=accounts[1], category=categories[2], tags=[tags[2], tags[3]]),
    3: TransactionRead(id=3, amount=Decimal("70.00"), kind=OperationKind.EXPENSE, operation_date=date(2026, 9, 7), description="Поездка в метро", account=accounts[2], category=categories[3], tags=[]),
}
