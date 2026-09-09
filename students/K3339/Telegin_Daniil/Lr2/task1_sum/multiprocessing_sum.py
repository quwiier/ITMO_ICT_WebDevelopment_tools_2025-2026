"""Calculate a large integer sum by coordinating several processes."""

from __future__ import annotations

import argparse
from multiprocessing import Pool
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


def run(limit: int = DEFAULT_LIMIT, workers: int = DEFAULT_WORKERS) -> BenchmarkResult:
    """Run the multiprocess implementation and return its benchmark result."""
    ranges = split_inclusive_range(1, limit, workers)

    started_at = perf_counter()
    with Pool(processes=len(ranges)) as pool:
        partial_sums = pool.starmap(calculate_sum, ranges)
    elapsed_seconds = perf_counter() - started_at

    total = sum(partial_sums)
    return BenchmarkResult(
        approach="multiprocessing",
        workers=len(ranges),
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
