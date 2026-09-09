"""Run comparable benchmarks for all implementations of task 1."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from task1_sum import asyncio_sum, multiprocessing_sum, threading_sum
from task1_sum.common import DEFAULT_LIMIT, DEFAULT_WORKERS, RESULTS_FILE, save_result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=Path, default=RESULTS_FILE)
    args = parser.parse_args()

    if args.repeats < 1:
        parser.error("--repeats must be positive")

    implementations = (
        threading_sum.run,
        multiprocessing_sum.run,
    )
    for attempt in range(1, args.repeats + 1):
        print(f"Run {attempt}/{args.repeats}")
        for implementation in implementations:
            result = implementation(limit=args.limit, workers=args.workers)
            save_result(result, args.output)
            print(result)

        async_result = asyncio.run(
            asyncio_sum.run(limit=args.limit, workers=args.workers)
        )
        save_result(async_result, args.output)
        print(async_result)


if __name__ == "__main__":
    main()
