"""Parse web-page titles concurrently with the multiprocessing module."""

from __future__ import annotations

import argparse
from multiprocessing import Pool
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
            approach="multiprocessing",
            status_code=response.status_code,
        )
        return ParseResult(url=url, title=title, status_code=response.status_code)
    except Exception as error:
        return ParseResult(url=url, title=None, status_code=None, error=str(error))


def _parse_chunk(urls: list[str]) -> list[ParseResult]:
    """Process a URL chunk in a child process."""
    return [parse_and_save(url) for url in urls]


def run(urls: tuple[str, ...] = URLS, workers: int = DEFAULT_WORKERS) -> tuple[list[ParseResult], float]:
    """Run the multiprocess parser and return outcomes with elapsed time."""
    chunks = split_urls(urls, workers)
    started_at = perf_counter()
    with Pool(processes=len(chunks)) as pool:
        result_chunks = pool.map(_parse_chunk, chunks)
    elapsed_seconds = perf_counter() - started_at
    return [result for chunk in result_chunks for result in chunk], elapsed_seconds


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
