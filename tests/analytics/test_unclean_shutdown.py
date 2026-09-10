"""T037: unclean-shutdown detection, sticky flag, ack doesn't restore
historical completeness (FR-117 — the spike-verified headline finding)."""
import pytest

import src.persistence.db as db_module
from src.domain.analytics import get_summary, mark_incomplete
from src.domain.short_link import create_short_link
from src.observability import system_status


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    yield c
    c.close()


def test_first_ever_startup_is_not_flagged_unclean(conn):
    detected = system_status.on_startup(conn)
    assert detected is False


def test_clean_shutdown_then_restart_not_flagged(conn):
    system_status.on_startup(conn)
    system_status.on_clean_shutdown(conn)
    detected = system_status.on_startup(conn)
    assert detected is False


def test_crash_window_detected_on_next_startup(conn):
    """Simulates: process started (state='running') then crashed without
    calling on_clean_shutdown; the NEXT startup must detect this."""
    system_status.on_startup(conn)
    # No on_clean_shutdown call — simulates a crash.
    detected = system_status.on_startup(conn)
    assert detected is True
    status = system_status.get_status(conn)
    assert status["degraded_since_unclean_shutdown_at"] is not None


def test_double_failure_flag_stays_sticky_across_multiple_crashes(conn):
    system_status.on_startup(conn)
    system_status.on_startup(conn)  # first crash detected here
    first_flag = system_status.get_status(conn)["degraded_since_unclean_shutdown_at"]
    system_status.on_startup(conn)  # second crash in a row
    second_flag = system_status.get_status(conn)["degraded_since_unclean_shutdown_at"]
    assert first_flag == second_flag  # sticky: not overwritten by the second detection


def test_acknowledge_does_not_restore_historical_completeness(conn):
    link = create_short_link(conn, "https://example.com/x")
    mark_incomplete(conn, link.short_code)
    system_status.on_startup(conn)
    system_status.on_startup(conn)  # detect unclean shutdown

    system_status.acknowledge(conn)

    status = system_status.get_status(conn)
    assert status["degraded_since_unclean_shutdown_at"] is None  # forward-looking warning cleared
    # But historical per-code completeness is untouched — it stays incomplete forever.
    assert get_summary(conn, link.short_code)["completeness_status"] == "incomplete"
