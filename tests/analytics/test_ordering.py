"""T034: no count for an unsent response — the overcount defect this
design exists to prevent."""
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


def test_no_enqueue_means_no_count(conn):
    link = create_short_link(conn, "https://example.com/unsent")
    # No enqueue_redirect_event call -> simulates "response never actually sent".
    drain_outbox(conn)
    summary = get_summary(conn, link.short_code)
    assert summary["successful_redirect_count"] == 0


def test_enqueue_then_drain_increments_exactly_once(conn):
    link = create_short_link(conn, "https://example.com/sent")
    enqueue_redirect_event(conn, link.short_code)
    applied = drain_outbox(conn)
    assert applied == 1
    summary = get_summary(conn, link.short_code)
    assert summary["successful_redirect_count"] == 1
