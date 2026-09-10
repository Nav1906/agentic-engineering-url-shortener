"""T060: the three real spike scenarios — exception-after-effect,
killed-worker, git-succeeds-DB-doesn't — generalized to: idempotent stages
never need a probe; externally_observable_uncertain stages always do, and
the probe result alone decides succeeded vs. failed_transient."""
import pytest

import src.persistence.db as db_module
from src.orchestration.models import add_stage, create_workflow_instance
from src.orchestration.reaper import reconcile_stage


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    yield c
    c.close()


def test_idempotent_stage_reconciles_without_probe(conn):
    wf = create_workflow_instance(conn, "req")
    stage = add_stage(conn, wf, "A", effect_class="idempotent")
    result = reconcile_stage(conn, stage)
    assert result == "not_completed"
    row = conn.execute("SELECT status FROM orchestration_workflow_stage WHERE id=?", (stage,)).fetchone()
    assert row["status"] == "failed_transient"


def test_uncertain_stage_requires_probe(conn):
    wf = create_workflow_instance(conn, "req")
    stage = add_stage(conn, wf, "A", effect_class="externally_observable_uncertain")
    with pytest.raises(ValueError):
        reconcile_stage(conn, stage)


def test_uncertain_stage_effect_actually_completed(conn):
    """Simulates: exception raised after the effect actually landed (e.g.
    git succeeded, DB commit didn't) — reconciliation must NOT retry."""
    wf = create_workflow_instance(conn, "req")
    stage = add_stage(conn, wf, "A", effect_class="externally_observable_uncertain")
    result = reconcile_stage(conn, stage, probe_effect=lambda sid: True)
    assert result == "already_completed"
    row = conn.execute("SELECT status FROM orchestration_workflow_stage WHERE id=?", (stage,)).fetchone()
    assert row["status"] == "succeeded"


def test_uncertain_stage_effect_never_happened(conn):
    """Simulates: a killed worker before any effect landed — reconciliation
    confirms not_completed, safe to retry."""
    wf = create_workflow_instance(conn, "req")
    stage = add_stage(conn, wf, "A", effect_class="externally_observable_uncertain")
    result = reconcile_stage(conn, stage, probe_effect=lambda sid: False)
    assert result == "not_completed"
    row = conn.execute("SELECT status FROM orchestration_workflow_stage WHERE id=?", (stage,)).fetchone()
    assert row["status"] == "failed_transient"
