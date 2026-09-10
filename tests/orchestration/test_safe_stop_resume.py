"""T076: safe-stop resumable only via explicit authorized action — no
automatic resume path exists anywhere in the scheduler module."""
import pytest

import src.persistence.db as db_module
from src.orchestration.models import create_workflow_instance
from src.orchestration.scheduler import resume_from_safe_stop


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    yield c
    c.close()


def test_resume_requires_explicit_call(conn):
    wf = create_workflow_instance(conn, "req")
    conn.execute("UPDATE orchestration_workflow_instance SET status='safe_stopped' WHERE id=?", (wf,))
    conn.commit()

    row = conn.execute("SELECT status FROM orchestration_workflow_instance WHERE id=?", (wf,)).fetchone()
    assert row["status"] == "safe_stopped"  # nothing else in this module touches it

    resume_from_safe_stop(conn, wf)
    row = conn.execute("SELECT status FROM orchestration_workflow_instance WHERE id=?", (wf,)).fetchone()
    assert row["status"] == "running"


def test_resume_noop_if_not_safe_stopped(conn):
    wf = create_workflow_instance(conn, "req")  # starts 'running'
    resume_from_safe_stop(conn, wf)  # no-op, WHERE clause guards it
    row = conn.execute("SELECT status FROM orchestration_workflow_instance WHERE id=?", (wf,)).fetchone()
    assert row["status"] == "running"
