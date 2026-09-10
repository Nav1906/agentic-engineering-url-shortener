"""T071: exact timing assertions — 3 attempts, exactly 2 waits (1s, 2s)."""
from src.orchestration.retry_policy import (
    MAX_STAGE_ATTEMPTS,
    STAGE_BACKOFF_SECONDS,
    backoff_for_attempt,
)


def test_max_attempts_is_three():
    assert MAX_STAGE_ATTEMPTS == 3


def test_exactly_two_waits_one_then_two_seconds():
    assert STAGE_BACKOFF_SECONDS == (1, 2)


def test_first_attempt_has_no_wait():
    assert backoff_for_attempt(1) is None


def test_second_attempt_waits_one_second():
    assert backoff_for_attempt(2) == 1


def test_third_attempt_waits_two_seconds():
    assert backoff_for_attempt(3) == 2


def test_no_fourth_wait_defined():
    assert backoff_for_attempt(4) is None
