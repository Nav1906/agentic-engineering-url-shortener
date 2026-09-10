"""T057: two independent stages actually run concurrently (observable via
overlapping execution windows), synchronization event recorded."""
import asyncio

import pytest

import src.persistence.db as db_module
from src.orchestration.lineage import get_lineage
from src.orchestration.models import add_stage, create_workflow_instance
from src.orchestration.scheduler import dispatch_ready_stages_parallel, mark_ready


@pytest.fixture()
def db_path(tmp_path, monkeypatch):
    path = str(tmp_path / "app.db")
    monkeypatch.setattr(db_module, "DB_PATH", path)
    c = db_module.get_connection()
    db_module.init_schema(c)
    c.close()
    return path


@pytest.mark.asyncio
async def test_two_independent_stages_run_concurrently_with_sync_event(db_path):
    conn = db_module.get_connection()
    wf = create_workflow_instance(conn, "req")
    stage_a = add_stage(conn, wf, "A")
    stage_b = add_stage(conn, wf, "B")
    mark_ready(conn, [stage_a, stage_b])
    conn.close()

    windows: dict[str, tuple[float, float]] = {}

    async def slow_execute(stage_id: str) -> None:
        import time

        start = time.monotonic()
        await asyncio.sleep(0.1)
        windows[stage_id] = (start, time.monotonic())

    start_times = await dispatch_ready_stages_parallel(
        db_path, wf, [stage_a, stage_b], "worker-1", slow_execute
    )

    assert set(start_times) == {stage_a, stage_b}
    a_start, a_end = windows[stage_a]
    b_start, b_end = windows[stage_b]
    # Genuine concurrency: each stage's window overlaps the other's, which
    # is impossible if they ran sequentially (0.1s each -> would be >=0.2s
    # apart). This assertion is what a sequential-only implementation fails.
    assert a_start < b_end and b_start < a_end

    conn = db_module.get_connection()
    for sid in (stage_a, stage_b):
        row = conn.execute("SELECT status FROM orchestration_workflow_stage WHERE id=?", (sid,)).fetchone()
        assert row["status"] == "succeeded"
    lineage = get_lineage(conn, wf)
    sync_events = [e for e in lineage if e.decision_type == "synchronization_point"]
    assert len(sync_events) == 1
    assert set(sync_events[0].detail["synchronized_stage_ids"]) == {stage_a, stage_b}
    conn.close()
