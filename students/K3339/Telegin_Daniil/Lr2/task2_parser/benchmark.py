"""Run comparable benchmarks for all implementations of task 2."""

from __future__ import annotations

import argparse
import asyncio
import csv
from dataclasses import asdict, dataclass
from pathlib import Path

from task2_parser import asyncio_parser, multiprocessing_parser, threading_parser
from task2_parser.common import URLS, ParseResult
from task2_parser.database import initialize_database


RESULTS_FILE = Path(__file__).resolve().parents[1] / "results" / "task2_results.csv"


@dataclass(frozen=True)
class ParserBenchmarkResult:
    """One reproducible run of a web parsing implementation."""

    approach: str
    workers: int
    url_count: int
    successful: int
    failed: int
    elapsed_seconds: float


def save_result(result: ParserBenchmarkResult, file_path: Path) -> None:
    """Append a parsing benchmark result to CSV."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    needs_header = not file_path.exists() or file_path.stat().st_size == 0
    with file_path.open("a", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=ParserBenchmarkResult.__annotations__)
        if needs_header:
            writer.writeheader()
        writer.writerow(asdict(result))


def make_result(
    approach: str, workers: int, results: list[ParseResult], elapsed_seconds: float
) -> ParserBenchmarkResult:
    """Convert individual page outcomes to one compact benchmark row."""
    successful = sum(result.error is None for result in results)
    return ParserBenchmarkResult(
        approach=approach,
        workers=workers,
        url_count=len(results),
        successful=successful,
        failed=len(results) - successful,
        elapsed_seconds=elapsed_seconds,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", action="append", help="URL to parse; repeat as needed.")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=Path, default=RESULTS_FILE)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be positive")

    urls = tuple(args.url) if args.url else URLS
    initialize_database()
    for attempt in range(1, args.repeats + 1):
        print(f"Run {attempt}/{args.repeats}")
        for approach, implementation in (
            ("threading", threading_parser.run),
            ("multiprocessing", multiprocessing_parser.run),
        ):
            results, elapsed_seconds = implementation(urls, args.workers)
            result = make_result(approach, args.workers, results, elapsed_seconds)
            save_result(result, args.output)
            print(result)

        results, elapsed_seconds = asyncio.run(asyncio_parser.run(urls, args.workers))
        result = make_result("asyncio", args.workers, results, elapsed_seconds)
        save_result(result, args.output)
        print(result)


if __name__ == "__main__":
    main()
