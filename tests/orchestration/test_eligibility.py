"""T056: a stage becomes ready only when every dependency resolves to succeeded."""
import pytest

import src.persistence.db as db_module
from src.orchestration.models import add_stage, create_workflow_instance
from src.orchestration.scheduler import compute_ready_stages, mark_ready


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    yield c
    c.close()


def test_stage_with_no_dependencies_is_immediately_ready(conn):
    wf = create_workflow_instance(conn, "req")
    stage_a = add_stage(conn, wf, "A")
    ready = compute_ready_stages(conn, wf)
    assert ready == [stage_a]


def test_stage_not_ready_until_dependency_succeeds(conn):
    wf = create_workflow_instance(conn, "req")
    stage_a = add_stage(conn, wf, "A")
    stage_b = add_stage(conn, wf, "B", depends_on=[stage_a])

    ready = compute_ready_stages(conn, wf)
    assert ready == [stage_a]  # B not ready, A hasn't succeeded

    conn.execute("UPDATE orchestration_workflow_stage SET status='succeeded' WHERE id=?", (stage_a,))
    conn.commit()
    mark_ready(conn, [])  # noop, just ensure state settled
    ready = compute_ready_stages(conn, wf)
    assert stage_b in ready


def test_forward_progress_on_known_good_graph(conn):
    """A -> B -> C linear chain: forward progress test."""
    wf = create_workflow_instance(conn, "req")
    a = add_stage(conn, wf, "A")
    b = add_stage(conn, wf, "B", depends_on=[a])
    c = add_stage(conn, wf, "C", depends_on=[b])

    assert compute_ready_stages(conn, wf) == [a]
    conn.execute("UPDATE orchestration_workflow_stage SET status='succeeded' WHERE id=?", (a,))
    conn.commit()
    assert compute_ready_stages(conn, wf) == [b]
    conn.execute("UPDATE orchestration_workflow_stage SET status='succeeded' WHERE id=?", (b,))
    conn.commit()
    assert compute_ready_stages(conn, wf) == [c]
