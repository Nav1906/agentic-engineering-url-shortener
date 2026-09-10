"""T059: periodic-only trigger — the "zero other transitions occurring"
case Round 3 caught as missing. The sweep must detect a stale lease purely
from being called, not from riding along on some other event."""
from datetime import UTC, datetime, timedelta

import pytest

import src.persistence.db as db_module
from src.orchestration.models import add_stage, create_workflow_instance
from src.orchestration.reaper import sweep_stale_leases
from src.orchestration.scheduler import claim_stage, mark_ready


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    yield c
    c.close()


def test_sweep_with_no_other_activity_still_detects_stale_lease(conn):
    wf = create_workflow_instance(conn, "req")
    stage = add_stage(conn, wf, "A", timeout_seconds=1)
    mark_ready(conn, [stage])
    claim_stage(conn, stage, "worker-1")

    # Force the lease into the past directly — simulates real time passing
    # with absolutely no other event occurring in between.
    past = (datetime.now(UTC) - timedelta(seconds=60)).isoformat()
    conn.execute("UPDATE orchestration_stage_execution SET lease_expires_at=? WHERE stage_id=?", (past, stage))
    conn.commit()

    affected = sweep_stale_leases(conn)
    assert affected == [stage]

    row = conn.execute("SELECT status FROM orchestration_workflow_stage WHERE id=?", (stage,)).fetchone()
    assert row["status"] == "awaiting_reconciliation"


def test_sweep_ignores_leases_not_yet_expired(conn):
    wf = create_workflow_instance(conn, "req")
    stage = add_stage(conn, wf, "A", timeout_seconds=300)
    mark_ready(conn, [stage])
    claim_stage(conn, stage, "worker-1")

    affected = sweep_stale_leases(conn)
    assert affected == []
