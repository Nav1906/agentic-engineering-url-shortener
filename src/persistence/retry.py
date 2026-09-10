"""Bounded-retry wrapper for SQLITE_BUSY/SQLITE_LOCKED (T020, FR-402, ADR-0007).

3 attempts total, exactly 2 intervening waits (1s, 2s) per ADR-0007 Rev. 3 /
PVT-002. A caller-supplied sleep function lets tests avoid real sleeping.
"""
from __future__ import annotations

import sqlite3
import time
from typing import Callable, TypeVar

T = TypeVar("T")

MAX_ATTEMPTS = 3
BACKOFF_SECONDS = (1, 2)


class RetryExhausted(RuntimeError):
    """Raised when all MAX_ATTEMPTS attempts hit SQLITE_BUSY/SQLITE_LOCKED."""


def with_bounded_retry(
    fn: Callable[[], T],
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    last_exc: sqlite3.OperationalError | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return fn()
        except sqlite3.OperationalError as exc:
            if "locked" not in str(exc).lower() and "busy" not in str(exc).lower():
                raise
            last_exc = exc
            if attempt < MAX_ATTEMPTS:
                sleep(BACKOFF_SECONDS[attempt - 1])
    raise RetryExhausted(f"exhausted {MAX_ATTEMPTS} attempts") from last_exc
