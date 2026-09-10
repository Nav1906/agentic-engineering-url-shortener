"""T035: drain worker idempotent by event_id — kill mid-batch, no double-count."""
import pytest

import src.persistence.db as db_module
from src.domain.analytics import drain_outbox, enqueue_redirect_event, get_summary
from src.domain.short_link import create_short_link


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    yield c
    c.close()


def test_draining_twice_does_not_double_count(conn):
    link = create_short_link(conn, "https://example.com/twice")
    enqueue_redirect_event(conn, link.short_code)
    drain_outbox(conn)
    drain_outbox(conn)  # simulates a re-run after a mid-batch crash
    summary = get_summary(conn, link.short_code)
    assert summary["successful_redirect_count"] == 1


def test_multiple_events_all_counted_once_each(conn):
    link = create_short_link(conn, "https://example.com/multi")
    for _ in range(5):
        enqueue_redirect_event(conn, link.short_code)
    drain_outbox(conn)
    drain_outbox(conn)
    summary = get_summary(conn, link.short_code)
    assert summary["successful_redirect_count"] == 5
