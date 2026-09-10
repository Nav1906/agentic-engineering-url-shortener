"""T014: scheme allow-list + expiry validation (FR-101, FR-114)."""
from datetime import datetime, timedelta, timezone

import pytest

from src.domain.validation import (
    ValidationError,
    validate_destination_url,
    validate_expires_at,
)


def test_accepts_https_url():
    validate_destination_url("https://example.com/path")


def test_accepts_http_url():
    validate_destination_url("http://example.com/path")


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "data:text/html,<script>alert(1)</script>",
        "file:///etc/passwd",
        "not a url",
        "",
        "ftp://example.com/file",
    ],
)
def test_rejects_disallowed_or_malformed_schemes(url):
    with pytest.raises(ValidationError):
        validate_destination_url(url)


def test_validate_expires_at_accepts_future_timestamp():
    future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    validate_expires_at(future)


def test_validate_expires_at_accepts_none():
    validate_expires_at(None)


def test_validate_expires_at_rejects_past_timestamp():
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    with pytest.raises(ValidationError):
        validate_expires_at(past)


def test_validate_expires_at_rejects_invalid_timestamp():
    with pytest.raises(ValidationError):
        validate_expires_at("not-a-timestamp")
