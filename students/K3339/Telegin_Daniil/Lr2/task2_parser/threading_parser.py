"""Parse web-page titles concurrently with the threading module."""

from __future__ import annotations

import argparse
from queue import Queue
from threading import Thread
from time import perf_counter

import requests

from task2_parser.common import (
    URLS,
    ParseResult,
    display_result,
    extract_title,
    split_urls,
)
from task2_parser.database import initialize_database, save_parsed_page


DEFAULT_WORKERS = 4
REQUEST_TIMEOUT_SECONDS = 15
REQUEST_HEADERS = {"User-Agent": "ITMO-LR2-Parser/1.0"}


def parse_and_save(url: str) -> ParseResult:
    """Download one page, extract its title, and save it to the LR1 database."""
    try:
        response = requests.get(
            url, timeout=REQUEST_TIMEOUT_SECONDS, headers=REQUEST_HEADERS
        )
        response.raise_for_status()
        title = extract_title(response.text)
        save_parsed_page(
            url=url,
            title=title,
            approach="threading",
            status_code=response.status_code,
        )
        return ParseResult(url=url, title=title, status_code=response.status_code)
    except Exception as error:
        return ParseResult(url=url, title=None, status_code=None, error=str(error))


def _parse_chunk(urls: list[str], results: Queue[ParseResult]) -> None:
    for url in urls:
        results.put(parse_and_save(url))


def run(urls: tuple[str, ...] = URLS, workers: int = DEFAULT_WORKERS) -> tuple[list[ParseResult], float]:
    """Run the threaded parser and return page outcomes with elapsed time."""
    chunks = split_urls(urls, workers)
    results: Queue[ParseResult] = Queue()
    threads = [Thread(target=_parse_chunk, args=(chunk, results)) for chunk in chunks]

    started_at = perf_counter()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    elapsed_seconds = perf_counter() - started_at
    return [results.get() for _ in urls], elapsed_seconds


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", action="append", help="URL to parse; repeat as needed.")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    args = parser.parse_args()
    urls = tuple(args.url) if args.url else URLS

    initialize_database()
    results, elapsed_seconds = run(urls=urls, workers=args.workers)
    for result in results:
        display_result(result)
    print(f"Elapsed time: {elapsed_seconds:.3f} seconds")


if __name__ == "__main__":
    main()
