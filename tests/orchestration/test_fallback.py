"""T073: fallback-on-failed_permanent, both branches (fallback defined /
not defined)."""
import pytest

import src.persistence.db as db_module
from src.orchestration.models import add_stage, create_workflow_instance
from src.orchestration.scheduler import apply_fallback_or_safe_stop


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    yield c
    c.close()


def test_fallback_defined_activates_fallback_stage(conn):
    wf = create_workflow_instance(conn, "req")
    primary = add_stage(conn, wf, "primary")
    fallback = add_stage(conn, wf, "fallback")
    outcome = apply_fallback_or_safe_stop(conn, wf, primary, fallback_stage_id=fallback)
    assert outcome == "fallback"
    row = conn.execute("SELECT status FROM orchestration_workflow_stage WHERE id=?", (fallback,)).fetchone()
    assert row["status"] == "ready"


def test_no_fallback_defined_reaches_safe_stop(conn):
    wf = create_workflow_instance(conn, "req")
    primary = add_stage(conn, wf, "primary")
    outcome = apply_fallback_or_safe_stop(conn, wf, primary, fallback_stage_id=None)
    assert outcome == "safe_stopped"
    row = conn.execute("SELECT status FROM orchestration_workflow_instance WHERE id=?", (wf,)).fetchone()
    assert row["status"] == "safe_stopped"
