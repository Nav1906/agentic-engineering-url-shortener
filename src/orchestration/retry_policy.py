"""Corrected backoff + realistic per-subprocess timeouts (T071, T072;
FR-402, PVT-002, PVT-003). Exactly 3 attempts, exactly 2 waits (1s, 2s)."""
from __future__ import annotations

MAX_STAGE_ATTEMPTS = 3
STAGE_BACKOFF_SECONDS = (1, 2)

SUBPROCESS_TIMEOUTS_SECONDS = {
    "internal": 5,
    "pytest": 300,
    "claude": 600,
}


def timeout_for(subprocess_type: str) -> int:
    if subprocess_type not in SUBPROCESS_TIMEOUTS_SECONDS:
        raise ValueError(f"unknown subprocess type {subprocess_type!r}")
    return SUBPROCESS_TIMEOUTS_SECONDS[subprocess_type]


def backoff_for_attempt(attempt_number: int) -> int | None:
    """Returns the wait (seconds) BEFORE this attempt, or None if this is
    the first attempt (no wait) or attempt_number exceeds the schedule."""
    if attempt_number <= 1:
        return None
    index = attempt_number - 2
    if index >= len(STAGE_BACKOFF_SECONDS):
        return None
    return STAGE_BACKOFF_SECONDS[index]
