"""LR3 routes attached to the existing FastAPI application from laboratory work 1."""

from __future__ import annotations

import os

import httpx
from fastapi import HTTPException, status
from pydantic import BaseModel, HttpUrl

from app.main import app
from celery.result import AsyncResult
from celery_app import celery_app
from tasks import parse_url_task


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


class QueuedParserResponse(BaseModel):
    """Information returned immediately after a Celery task is queued."""

    task_id: str
    status: str


class ParserTaskStatus(BaseModel):
    """Current state and, once ready, result of a background parse."""

    task_id: str
    status: str
    result: dict[str, object] | None = None


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


@app.post("/parser/parse/async", response_model=QueuedParserResponse, status_code=status.HTTP_202_ACCEPTED, tags=["parser"])
def queue_parse(payload: ParserRequest) -> QueuedParserResponse:
    """Put a parsing task onto the Redis-backed Celery queue."""
    task = parse_url_task.delay(str(payload.url))
    return QueuedParserResponse(task_id=task.id, status=task.status)


@app.get("/parser/tasks/{task_id}", response_model=ParserTaskStatus, tags=["parser"])
def get_parse_task_status(task_id: str) -> ParserTaskStatus:
    """Return the current state of a queued parsing task."""
    task = AsyncResult(task_id, app=celery_app)
    result = task.result if task.successful() else None
    return ParserTaskStatus(task_id=task.id, status=task.status, result=result)
