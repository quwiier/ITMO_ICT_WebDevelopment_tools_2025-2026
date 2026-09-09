"""Parse web-page titles concurrently with asyncio and aiohttp."""

from __future__ import annotations

import argparse
import asyncio
from time import perf_counter

import aiohttp

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


async def parse_and_save(url: str, session: aiohttp.ClientSession) -> ParseResult:
    """Download one page asynchronously, extract its title, and save it to DB."""
    try:
        async with session.get(url, headers=REQUEST_HEADERS) as response:
            response.raise_for_status()
            title = extract_title(await response.text())
            await asyncio.to_thread(
                save_parsed_page,
                url=url,
                title=title,
                approach="asyncio",
                status_code=response.status,
            )
            return ParseResult(url=url, title=title, status_code=response.status)
    except Exception as error:
        return ParseResult(url=url, title=None, status_code=None, error=str(error))


async def _parse_chunk(
    urls: list[str], session: aiohttp.ClientSession
) -> list[ParseResult]:
    return [await parse_and_save(url, session) for url in urls]


async def run(
    urls: tuple[str, ...] = URLS, workers: int = DEFAULT_WORKERS
) -> tuple[list[ParseResult], float]:
    """Run the asynchronous parser and return outcomes with elapsed time."""
    chunks = split_urls(urls, workers)
    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)
    connector = aiohttp.TCPConnector(limit=len(chunks))

    started_at = perf_counter()
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        result_chunks = await asyncio.gather(
            *(_parse_chunk(chunk, session) for chunk in chunks)
        )
    elapsed_seconds = perf_counter() - started_at
    return [result for chunk in result_chunks for result in chunk], elapsed_seconds


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", action="append", help="URL to parse; repeat as needed.")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    args = parser.parse_args()
    urls = tuple(args.url) if args.url else URLS

    initialize_database()
    results, elapsed_seconds = asyncio.run(run(urls=urls, workers=args.workers))
    for result in results:
        display_result(result)
    print(f"Elapsed time: {elapsed_seconds:.3f} seconds")


if __name__ == "__main__":
    main()
