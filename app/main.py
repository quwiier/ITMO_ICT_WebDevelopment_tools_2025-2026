"""FastAPI application entry point."""

from fastapi import FastAPI


app = FastAPI(
    title="Personal Finance Service",
    description="API for managing personal income, expenses, budgets, and accounts.",
    version="0.1.0",
)


@app.get("/", tags=["service"])
def read_root() -> dict[str, str]:
    """Return a small health message for the base application."""
    return {"message": "Personal Finance Service is running"}
