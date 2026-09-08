"""PostgreSQL connection and SQLModel session dependency."""

import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlmodel import Session, create_engine


load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://finance_user:finance_password@localhost:5432/personal_finance",
)
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)


def get_session() -> Generator[Session, None, None]:
    """Yield one SQLModel session per request."""
    with Session(engine) as session:
        yield session
