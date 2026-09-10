"""T040: MTTR restricted to recovered events; unrecovered counted separately."""
import time

import pytest

import src.persistence.db as db_module
from src.observability.audit import record_event
from src.observability.metrics import compute_mttr_seconds


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    yield c
    c.close()


def test_no_failures_returns_none_and_zero(conn):
    mttr, unrecovered = compute_mttr_seconds(conn)
    assert mttr is None
    assert unrecovered == 0


def test_recovered_failure_produces_expected_mttr(conn):
    failure_id = record_event(conn, "system", "stage_failed", "stage1", "failed", "transient error")
    time.sleep(0.05)
    record_event(
        conn, "system", "stage_recovered", "stage1", "succeeded", "retry succeeded",
        recovery_of_event_id=failure_id,
    )
    mttr, unrecovered = compute_mttr_seconds(conn)
    assert mttr is not None
    assert mttr > 0
    assert unrecovered == 0


def test_unrecovered_failure_excluded_from_mttr_reported_separately(conn):
    record_event(conn, "system", "stage_failed", "stage1", "failed", "permanent error")
    mttr, unrecovered = compute_mttr_seconds(conn)
    assert mttr is None  # zero recovered events in the population
    assert unrecovered == 1


def test_mixed_recovered_and_unrecovered(conn):
    f1 = record_event(conn, "system", "stage_failed", "s1", "failed", "e1")
    record_event(conn, "system", "stage_recovered", "s1", "succeeded", "r1", recovery_of_event_id=f1)
    record_event(conn, "system", "stage_failed", "s2", "failed", "e2")  # never recovers
    mttr, unrecovered = compute_mttr_seconds(conn)
    assert mttr is not None
    assert unrecovered == 1
