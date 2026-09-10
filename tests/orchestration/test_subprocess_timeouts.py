"""T072: distinct realistic timeout per subprocess type (5s/300s/600s)."""
import pytest

from src.orchestration.retry_policy import timeout_for


def test_internal_timeout_is_5s():
    assert timeout_for("internal") == 5


def test_pytest_timeout_is_300s():
    assert timeout_for("pytest") == 300


def test_claude_timeout_is_600s():
    assert timeout_for("claude") == 600


def test_unknown_type_rejected():
    with pytest.raises(ValueError):
        timeout_for("made_up_type")
