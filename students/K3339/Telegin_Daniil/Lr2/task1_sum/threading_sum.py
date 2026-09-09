"""Calculate a large integer sum by coordinating several threads."""

from __future__ import annotations

import argparse
from queue import Queue
from threading import Thread
from time import perf_counter

from task1_sum.common import (
    DEFAULT_LIMIT,
    DEFAULT_WORKERS,
    BenchmarkResult,
    arithmetic_sum,
    expected_sum,
    save_result,
    split_inclusive_range,
)


def calculate_sum(start: int, end: int) -> int:
    """Calculate the sum for one assigned inclusive subrange."""
    return arithmetic_sum(start, end)


def _sum_subrange(start: int, end: int, results: Queue[int]) -> None:
    """Put the sum for a subrange into a thread-safe queue."""
    results.put(calculate_sum(start, end))


def run(limit: int = DEFAULT_LIMIT, workers: int = DEFAULT_WORKERS) -> BenchmarkResult:
    """Run the threaded implementation and return its benchmark result."""
    ranges = split_inclusive_range(1, limit, workers)
    results: Queue[int] = Queue()
    threads = [
        Thread(target=_sum_subrange, args=(start, end, results))
        for start, end in ranges
    ]

    started_at = perf_counter()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    elapsed_seconds = perf_counter() - started_at

    total = sum(results.get() for _ in threads)
    return BenchmarkResult(
        approach="threading",
        workers=len(threads),
        upper_limit=limit,
        elapsed_seconds=elapsed_seconds,
        total=total,
        is_correct=total == expected_sum(limit),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--save", action="store_true", help="Append the result to CSV.")
    args = parser.parse_args()

    result = run(limit=args.limit, workers=args.workers)
    if args.save:
        save_result(result)
    print(result)


if __name__ == "__main__":
    main()
