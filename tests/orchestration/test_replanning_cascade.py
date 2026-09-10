"""T078: exactly the affected stages/approvals invalidated, none broader."""
from datetime import UTC, datetime

import pytest

import src.persistence.db as db_module
from src.orchestration.models import add_stage, create_workflow_instance
from src.orchestration.replanning import invalidate_downstream


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    yield c
    c.close()


def _insert_approval(conn, wf, gate_id, revision):
    now = datetime.now(UTC).isoformat()
    conn.execute(
        "INSERT INTO orchestration_approval_decision "
        "(id, workflow_instance_id, gate_id, identity, role, decision, rationale, artifact_revision, created_at, invalidated_at) "
        "VALUES (?,?,?,?,?, 'approved', NULL, ?, ?, NULL)",
        (f"appr-{gate_id}", wf, gate_id, "alice", "reviewer_approver", revision, now),
    )
    conn.commit()


def test_only_affected_stages_and_approvals_invalidated(conn):
    wf = create_workflow_instance(conn, "req")
    affected = add_stage(conn, wf, "affected", artifact_revision="v1")
    unaffected = add_stage(conn, wf, "unaffected", artifact_revision="v1")
    conn.execute("UPDATE orchestration_workflow_stage SET status='succeeded' WHERE id IN (?,?)", (affected, unaffected))
    conn.commit()

    _insert_approval(conn, wf, "requirements_approval", "v1")

    result = invalidate_downstream(conn, wf, "v2", [affected])

    assert result["stages"] == [affected]
    assert len(result["approvals"]) == 1

    affected_row = conn.execute("SELECT status, artifact_revision FROM orchestration_workflow_stage WHERE id=?", (affected,)).fetchone()
    assert affected_row["status"] == "pending"
    assert affected_row["artifact_revision"] == "v2"

    unaffected_row = conn.execute("SELECT status, artifact_revision FROM orchestration_workflow_stage WHERE id=?", (unaffected,)).fetchone()
    assert unaffected_row["status"] == "succeeded"  # untouched
    assert unaffected_row["artifact_revision"] == "v1"  # untouched

    approval_row = conn.execute("SELECT invalidated_at FROM orchestration_approval_decision WHERE id='appr-requirements_approval'").fetchone()
    assert approval_row["invalidated_at"] is not None


def test_approval_already_on_new_revision_not_invalidated(conn):
    wf = create_workflow_instance(conn, "req")
    affected = add_stage(conn, wf, "affected", artifact_revision="v1")
    _insert_approval(conn, wf, "requirements_approval", "v2")  # already current

    invalidate_downstream(conn, wf, "v2", [affected])

    approval_row = conn.execute("SELECT invalidated_at FROM orchestration_approval_decision WHERE id='appr-requirements_approval'").fetchone()
    assert approval_row["invalidated_at"] is None  # not re-invalidated, already on v2
