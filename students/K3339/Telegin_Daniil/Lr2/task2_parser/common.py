"""Shared data and HTML helpers for the second task of laboratory work 2."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from bs4 import BeautifulSoup


URLS = (
    "https://example.com/",
    "https://www.iana.org/domains/reserved",
    "https://www.python.org/",
    "https://docs.python.org/3/",
    "https://fastapi.tiangolo.com/",
    "https://www.postgresql.org/",
)


@dataclass(frozen=True)
class ParseResult:
    """The outcome of downloading and parsing a single web page."""

    url: str
    title: str | None
    status_code: int | None
    error: str | None = None


def extract_title(html: str) -> str:
    """Extract and normalize a document title, including a missing-title marker."""
    soup = BeautifulSoup(html, "html.parser")
    if soup.title is None or soup.title.string is None:
        return "(no title)"
    return " ".join(soup.title.string.split())[:500] or "(no title)"


def display_result(result: ParseResult) -> None:
    """Print a concise parsing outcome for the laboratory demonstration."""
    if result.error:
        print(f"ERROR {result.url}: {result.error}")
        return
    print(f"{result.status_code} | {result.title} | {result.url}")


def split_urls(urls: Sequence[str], parts: int) -> list[list[str]]:
    """Divide URLs into balanced non-empty chunks for concurrent workers."""
    if parts < 1:
        raise ValueError("parts must be positive")
    if not urls:
        return []

    actual_parts = min(parts, len(urls))
    base_size, remainder = divmod(len(urls), actual_parts)
    chunks: list[list[str]] = []
    start = 0
    for index in range(actual_parts):
        size = base_size + (1 if index < remainder else 0)
        chunks.append(list(urls[start : start + size]))
        start += size
    return chunks
