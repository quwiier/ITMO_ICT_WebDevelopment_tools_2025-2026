"""PostgreSQL storage used by the standalone parser service."""

from __future__ import annotations

import os
from datetime import datetime

from sqlmodel import Field, SQLModel, Session, create_engine


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://finance_user:finance_password@db:5432/personal_finance",
)
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)


class ParsedPage(SQLModel, table=True):
    """One successful page parsing result."""

    __tablename__ = "parsed_page"

    id: int | None = Field(default=None, primary_key=True)
    url: str = Field(max_length=2048)
    title: str = Field(max_length=500)
    approach: str = Field(max_length=32)
    status_code: int
    parsed_at: datetime = Field(default_factory=datetime.utcnow)


def initialize_database() -> None:
    """Create the parser result table if it is absent."""
    SQLModel.metadata.create_all(engine)


def save_parsed_page(url: str, title: str, status_code: int) -> ParsedPage:
    """Persist one result through a short-lived database session."""
    page = ParsedPage(
        url=url,
        title=title,
        approach="lr3-parser-service",
        status_code=status_code,
    )
    with Session(engine) as session:
        session.add(page)
        session.commit()
        session.refresh(page)
    return page
