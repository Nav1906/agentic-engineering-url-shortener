"""T020: force contention, assert bounded retry then observable failure."""
import sqlite3

import pytest

from src.persistence.retry import MAX_ATTEMPTS, BACKOFF_SECONDS, RetryExhausted, with_bounded_retry


def test_succeeds_on_first_attempt_without_sleeping():
    calls = []
    result = with_bounded_retry(lambda: 42, sleep=lambda s: calls.append(s))
    assert result == 42
    assert calls == []


def test_exhausts_after_exactly_three_attempts_two_waits():
    attempts = {"n": 0}
    sleeps = []

    def flaky():
        attempts["n"] += 1
        raise sqlite3.OperationalError("database is locked")

    with pytest.raises(RetryExhausted):
        with_bounded_retry(flaky, sleep=lambda s: sleeps.append(s))

    assert attempts["n"] == MAX_ATTEMPTS == 3
    assert sleeps == list(BACKOFF_SECONDS) == [1, 2]


def test_non_contention_errors_are_not_retried():
    def broken():
        raise sqlite3.OperationalError("no such table: foo")

    with pytest.raises(sqlite3.OperationalError, match="no such table"):
        with_bounded_retry(broken, sleep=lambda s: pytest.fail("should not sleep"))


def test_recovers_after_transient_contention():
    attempts = {"n": 0}

    def recovers_on_second_try():
        attempts["n"] += 1
        if attempts["n"] < 2:
            raise sqlite3.OperationalError("database is locked")
        return "ok"

    result = with_bounded_retry(recovers_on_second_try, sleep=lambda s: None)
    assert result == "ok"
    assert attempts["n"] == 2
