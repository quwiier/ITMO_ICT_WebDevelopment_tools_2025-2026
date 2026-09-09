"""Shared helpers for the first task of laboratory work 2."""

from __future__ import annotations

import csv
import os
from dataclasses import asdict, dataclass
from pathlib import Path


DEFAULT_LIMIT = 10_000_000_000_000
DEFAULT_WORKERS = min(4, os.cpu_count() or 1)
RESULTS_FILE = Path(__file__).resolve().parents[1] / "results" / "task1_results.csv"


@dataclass(frozen=True)
class BenchmarkResult:
    """One reproducible execution of a summation implementation."""

    approach: str
    workers: int
    upper_limit: int
    elapsed_seconds: float
    total: int
    is_correct: bool


def split_inclusive_range(start: int, end: int, parts: int) -> list[tuple[int, int]]:
    """Split an inclusive range into balanced non-empty subranges."""
    if start > end:
        raise ValueError("start must not be greater than end")
    if parts < 1:
        raise ValueError("parts must be positive")

    length = end - start + 1
    actual_parts = min(parts, length)
    base_size, remainder = divmod(length, actual_parts)
    ranges: list[tuple[int, int]] = []
    current = start

    for index in range(actual_parts):
        size = base_size + (1 if index < remainder else 0)
        ranges.append((current, current + size - 1))
        current += size

    return ranges


def arithmetic_sum(start: int, end: int) -> int:
    """Return the sum of all integers in an inclusive range in constant time."""
    count = end - start + 1
    return count * (start + end) // 2


def expected_sum(upper_limit: int) -> int:
    """Return the reference sum for the interval from 1 through upper_limit."""
    if upper_limit < 1:
        raise ValueError("upper_limit must be positive")
    return arithmetic_sum(1, upper_limit)


def save_result(result: BenchmarkResult, file_path: Path = RESULTS_FILE) -> None:
    """Append a benchmark result to CSV, creating its header when needed."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    needs_header = not file_path.exists() or file_path.stat().st_size == 0

    with file_path.open("a", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=BenchmarkResult.__annotations__)
        if needs_header:
            writer.writeheader()
        writer.writerow(asdict(result))
