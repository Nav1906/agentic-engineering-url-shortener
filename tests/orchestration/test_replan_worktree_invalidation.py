"""T079: in-progress execution invalidation on replan."""
import pytest

import src.persistence.db as db_module
from src.orchestration.models import add_stage, create_workflow_instance
from src.orchestration.replanning import invalidate_worktree
from src.orchestration.scheduler import claim_stage, mark_ready


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    yield c
    c.close()


def test_in_progress_execution_marked_abandoned_on_replan(conn):
    wf = create_workflow_instance(conn, "req")
    stage = add_stage(conn, wf, "A")
    mark_ready(conn, [stage])
    execution_id = claim_stage(conn, stage, "worker-1")
    assert execution_id is not None

    invalidated = invalidate_worktree(conn, stage)
    assert invalidated is True

    row = conn.execute("SELECT status FROM orchestration_stage_execution WHERE id=?", (execution_id,)).fetchone()
    assert row["status"] == "abandoned"

    # Fencing consequence: a late completion write for the abandoned
    # execution must now affect 0 rows (T046's fencing rule).
    from src.orchestration.scheduler import complete_stage

    completed = complete_stage(conn, execution_id, stage)
    assert completed is False


def test_no_in_progress_execution_returns_false(conn):
    wf = create_workflow_instance(conn, "req")
    stage = add_stage(conn, wf, "A")
    assert invalidate_worktree(conn, stage) is False
