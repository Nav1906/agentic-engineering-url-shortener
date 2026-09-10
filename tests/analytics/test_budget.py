"""T039: PVT-001 bounded-overhead measurement (background task duration,
not response-blocking). One more sample — NOT a percentile claim, same
caveat as the Human Gate 4 spike."""
import time

import pytest

import src.persistence.db as db_module
from src.domain.analytics import drain_outbox, enqueue_redirect_event
from src.domain.short_link import create_short_link

PVT_001_BUDGET_SECONDS = 0.050  # 50ms, provisionally approved, unverified until this test


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    yield c
    c.close()


def test_background_write_completes_within_budget(conn):
    link = create_short_link(conn, "https://example.com/budget")
    start = time.perf_counter()
    enqueue_redirect_event(conn, link.short_code)
    drain_outbox(conn)
    elapsed = time.perf_counter() - start
    # One sample, logged — not asserted as a p95/percentile claim.
    print(f"PVT-001 sample: {elapsed * 1000:.3f}ms (budget {PVT_001_BUDGET_SECONDS * 1000:.0f}ms)")
    assert elapsed < PVT_001_BUDGET_SECONDS
