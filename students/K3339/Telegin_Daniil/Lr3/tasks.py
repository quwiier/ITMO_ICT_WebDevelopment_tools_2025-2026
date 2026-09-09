"""Background tasks executed by the Celery worker."""

from __future__ import annotations

import os

import httpx

from celery_app import celery_app


PARSER_SERVICE_URL = os.getenv("PARSER_SERVICE_URL", "http://parser:8001")
PARSER_TIMEOUT_SECONDS = 20.0


@celery_app.task(
    bind=True,
    autoretry_for=(httpx.HTTPError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def parse_url_task(self, url: str) -> dict[str, object]:
    """Send a URL to the parser service from a Celery worker."""
    response = httpx.post(
        f"{PARSER_SERVICE_URL}/parse",
        json={"url": url},
        timeout=PARSER_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return dict(response.json())
