"""T011: domain_short_link table + model."""
from datetime import UTC, datetime, timedelta

import pytest

import src.persistence.db as db_module
from src.domain.short_link import create_short_link, delete_short_link, get_short_link
from src.domain.validation import ValidationError


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    yield c
    c.close()


def test_create_and_get_short_link(conn):
    link = create_short_link(conn, "https://example.com/path")
    assert link.status == "active"
    assert link.expires_at is None
    fetched = get_short_link(conn, link.short_code)
    assert fetched.destination_url == "https://example.com/path"


def test_create_rejects_invalid_scheme_and_creates_nothing(conn):
    with pytest.raises(ValidationError):
        create_short_link(conn, "javascript:alert(1)")
    count = conn.execute("SELECT COUNT(*) FROM domain_short_link").fetchone()[0]
    assert count == 0


def test_two_requests_same_destination_no_key_create_distinct_codes(conn):
    link1 = create_short_link(conn, "https://example.com/same")
    link2 = create_short_link(conn, "https://example.com/same")
    assert link1.short_code != link2.short_code


def test_unique_short_code_among_active_links(conn):
    codes = {create_short_link(conn, f"https://example.com/{i}").short_code for i in range(20)}
    assert len(codes) == 20


def test_delete_short_link(conn):
    link = create_short_link(conn, "https://example.com/x")
    assert delete_short_link(conn, link.short_code) is True
    fetched = get_short_link(conn, link.short_code)
    assert fetched.status == "deleted"
    assert fetched.deleted_at is not None


def test_delete_nonexistent_returns_false(conn):
    assert delete_short_link(conn, "doesnotexist") is False


def test_expired_link_is_expired_property(conn):
    past = (datetime.now(UTC) - timedelta(seconds=1)).isoformat()
    # Bypass validate_expires_at (which requires future) by inserting directly,
    # simulating a link that has since passed its expiry.
    conn.execute(
        "INSERT INTO domain_short_link (short_code, destination_url, created_at, expires_at, status, deleted_at) "
        "VALUES ('abc1234', 'https://example.com', ?, ?, 'active', NULL)",
        (past, past),
    )
    conn.commit()
    link = get_short_link(conn, "abc1234")
    assert link.is_expired is True


def test_no_expiresat_never_expires(conn):
    link = create_short_link(conn, "https://example.com/no-exp")
    assert link.is_expired is False
