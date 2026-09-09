"""HTTP parser service used by the API and Celery worker in laboratory work 3."""

from __future__ import annotations

from contextlib import asynccontextmanager

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, HttpUrl

from services.parser.database import initialize_database, save_parsed_page


REQUEST_TIMEOUT_SECONDS = 15
REQUEST_HEADERS = {"User-Agent": "ITMO-LR3-Parser/1.0"}


class ParseRequest(BaseModel):
    """A URL accepted by the parser service."""

    url: HttpUrl


class ParseResponse(BaseModel):
    """Information obtained from one web page."""

    url: HttpUrl
    title: str
    status_code: int


def extract_title(html: str) -> str:
    """Return a normalized title or a readable marker for absent titles."""
    soup = BeautifulSoup(html, "html.parser")
    if soup.title is None or soup.title.string is None:
        return "(no title)"
    return " ".join(soup.title.string.split())[:500] or "(no title)"


def parse_url(url: str) -> ParseResponse:
    """Fetch, parse, and persist a single web page."""
    try:
        response = requests.get(
            url,
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to fetch URL: {error}",
        ) from error

    title = extract_title(response.text)
    save_parsed_page(url, title, response.status_code)
    return ParseResponse(url=url, title=title, status_code=response.status_code)


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="LR3 Parser Service",
    description="Fetches web pages and stores their titles in PostgreSQL.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["service"])
def health() -> dict[str, str]:
    """Return the service readiness state."""
    return {"status": "ok"}


@app.post("/parse", response_model=ParseResponse, tags=["parser"])
def parse(payload: ParseRequest) -> ParseResponse:
    """Parse one public web page and write its title to PostgreSQL."""
    return parse_url(str(payload.url))
