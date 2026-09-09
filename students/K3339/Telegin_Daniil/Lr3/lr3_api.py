"""LR3 routes attached to the existing FastAPI application from laboratory work 1."""

from __future__ import annotations

import os

import httpx
from fastapi import HTTPException, status
from pydantic import BaseModel, HttpUrl

from app.main import app


PARSER_SERVICE_URL = os.getenv("PARSER_SERVICE_URL", "http://parser:8001")
PARSER_TIMEOUT_SECONDS = 20.0


class ParserRequest(BaseModel):
    """Payload accepted by the API gateway route."""

    url: HttpUrl


class ParserResponse(BaseModel):
    """Successful response returned by the parser service."""

    url: HttpUrl
    title: str
    status_code: int


def call_parser(url: str) -> ParserResponse:
    """Forward one URL to the dedicated parser service."""
    try:
        response = httpx.post(
            f"{PARSER_SERVICE_URL}/parse",
            json={"url": url},
            timeout=PARSER_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return ParserResponse.model_validate(response.json())
    except httpx.HTTPStatusError as error:
        detail = error.response.json().get("detail", error.response.text)
        raise HTTPException(status_code=error.response.status_code, detail=detail) from error
    except httpx.HTTPError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Parser service is unavailable: {error}",
        ) from error


@app.get("/parser/health", tags=["parser"])
def parser_health() -> dict[str, str]:
    """Confirm that the API extension has been loaded."""
    return {"status": "ok"}


@app.post("/parser/parse", response_model=ParserResponse, tags=["parser"])
def parse_via_service(payload: ParserRequest) -> ParserResponse:
    """Request a synchronous page parse from the dedicated parser container."""
    return call_parser(str(payload.url))
