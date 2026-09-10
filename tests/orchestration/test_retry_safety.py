"""T070: an externally_observable_uncertain stage never retries without a
not_completed reconciliation result first."""
import pytest

import src.persistence.db as db_module
from src.orchestration.models import add_stage, create_workflow_instance
from src.orchestration.reaper import reconcile_stage
from src.orchestration.retry_policy import MAX_STAGE_ATTEMPTS
from src.orchestration.scheduler import claim_stage, issue_retry_or_exhaust, mark_ready


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    yield c
    c.close()


def test_retry_requires_prior_reconciliation(conn):
    wf = create_workflow_instance(conn, "req")
    stage = add_stage(conn, wf, "A")
    mark_ready(conn, [stage])
    claim_stage(conn, stage, "worker-1")
    # Stage is 'running', not 'failed_transient' -- the gate must reject.
    with pytest.raises(ValueError):
        issue_retry_or_exhaust(conn, stage)


def test_retry_allowed_after_reconciliation_confirms_not_completed(conn):
    wf = create_workflow_instance(conn, "req")
    stage = add_stage(conn, wf, "A", effect_class="idempotent")
    mark_ready(conn, [stage])
    claim_stage(conn, stage, "worker-1")
    reconcile_stage(conn, stage)  # sets failed_transient
    outcome = issue_retry_or_exhaust(conn, stage)
    assert outcome == "retried"
    row = conn.execute("SELECT status FROM orchestration_workflow_stage WHERE id=?", (stage,)).fetchone()
    assert row["status"] == "ready"


def test_exhausted_after_max_attempts(conn):
    wf = create_workflow_instance(conn, "req")
    stage = add_stage(conn, wf, "A", effect_class="idempotent")
    mark_ready(conn, [stage])
    outcome = None
    for _ in range(MAX_STAGE_ATTEMPTS):
        # issue_retry_or_exhaust always leaves the stage 'ready' (on retry)
        # for the next claim, so no manual re-arming is needed between
        # iterations.
        claim_stage(conn, stage, "worker-1")
        reconcile_stage(conn, stage)
        outcome = issue_retry_or_exhaust(conn, stage)
    assert outcome == "exhausted"
    row = conn.execute("SELECT status FROM orchestration_workflow_stage WHERE id=?", (stage,)).fetchone()
    assert row["status"] == "failed_permanent"
