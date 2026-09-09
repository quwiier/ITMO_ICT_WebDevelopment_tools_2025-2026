"""Storage for page titles in the PostgreSQL database from laboratory work 1."""

from __future__ import annotations

import os
from datetime import datetime

from dotenv import load_dotenv
from sqlmodel import Field, SQLModel, Session, create_engine


load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://finance_user:finance_password@localhost:5432/personal_finance",
)
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)


class ParsedPage(SQLModel, table=True):
    """A title obtained from a URL by one of the concurrent implementations."""

    __tablename__ = "parsed_page"

    id: int | None = Field(default=None, primary_key=True)
    url: str = Field(max_length=2048)
    title: str = Field(max_length=500)
    approach: str = Field(max_length=32)
    status_code: int
    parsed_at: datetime = Field(default_factory=datetime.utcnow)


def initialize_database() -> None:
    """Create the LR2 table in the existing PostgreSQL database when needed."""
    SQLModel.metadata.create_all(engine)


def save_parsed_page(
    *, url: str, title: str, approach: str, status_code: int
) -> ParsedPage:
    """Persist one successful parsing result using an independent DB session."""
    page = ParsedPage(
        url=url,
        title=title,
        approach=approach,
        status_code=status_code,
    )
    with Session(engine) as session:
        session.add(page)
        session.commit()
        session.refresh(page)
    return page
