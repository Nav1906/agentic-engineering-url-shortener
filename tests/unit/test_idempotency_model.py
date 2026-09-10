"""T012: domain_idempotency_record table + model (FR-112, FR-113, FR-116)."""
import pytest

import src.persistence.db as db_module
from src.domain.idempotency import (
    IdempotencyConflict,
    IdempotencyKeyTooShort,
    check_replay,
    record,
    validate_key_length,
)


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    c.execute(
        "INSERT INTO domain_short_link (short_code, destination_url, created_at, expires_at, status, deleted_at) "
        "VALUES ('code0001', 'https://example.com', '2026-01-01T00:00:00Z', NULL, 'active', NULL)"
    )
    c.commit()
    yield c
    c.close()


def test_new_key_returns_none(conn):
    assert check_replay(conn, "a" * 20, "https://example.com", None) is None


def test_matching_replay_returns_original_code(conn):
    record(conn, "b" * 20, "https://example.com", None, "code0001")
    result = check_replay(conn, "b" * 20, "https://example.com", None)
    assert result == "code0001"


def test_conflicting_replay_raises(conn):
    record(conn, "c" * 20, "https://example.com", None, "code0001")
    with pytest.raises(IdempotencyConflict):
        check_replay(conn, "c" * 20, "https://different.com", None)


def test_key_length_floor_enforced():
    with pytest.raises(IdempotencyKeyTooShort):
        validate_key_length("short")
    validate_key_length("a" * 16)  # does not raise
