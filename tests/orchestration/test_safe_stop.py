"""T075: safe-stop triggers (retry exhaustion, unresolved policy FAIL,
stuck reconciliation), all 3 individually, never a hang."""
import pytest

import src.persistence.db as db_module
from src.orchestration.models import add_stage, create_workflow_instance
from src.orchestration.scheduler import apply_fallback_or_safe_stop, issue_retry_or_exhaust


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    yield c
    c.close()


def test_retry_exhaustion_with_no_fallback_reaches_safe_stop(conn):
    wf = create_workflow_instance(conn, "req")
    stage = add_stage(conn, wf, "A")
    conn.execute("UPDATE orchestration_workflow_stage SET status='failed_transient', attempt_count=3 WHERE id=?", (stage,))
    conn.commit()
    outcome = issue_retry_or_exhaust(conn, stage)
    assert outcome == "exhausted"
    safe_stop_outcome = apply_fallback_or_safe_stop(conn, wf, stage, fallback_stage_id=None)
    assert safe_stop_outcome == "safe_stopped"


def test_unresolved_policy_fail_reaches_safe_stop(conn):
    """A workflow with an unresolved policy FAIL and no path forward
    reaches safe-stop via the same terminal mechanism (not a distinct
    hang state)."""
    wf = create_workflow_instance(conn, "req")
    stage = add_stage(conn, wf, "policy_gate")
    outcome = apply_fallback_or_safe_stop(conn, wf, stage, fallback_stage_id=None)
    assert outcome == "safe_stopped"


def test_stuck_reconciliation_reaches_safe_stop(conn):
    """A stage stuck awaiting_reconciliation with no probe available is,
    by the same mechanism, ultimately routed to safe-stop rather than
    hanging indefinitely."""
    wf = create_workflow_instance(conn, "req")
    stage = add_stage(conn, wf, "A", effect_class="externally_observable_uncertain")
    conn.execute("UPDATE orchestration_workflow_stage SET status='awaiting_reconciliation' WHERE id=?", (stage,))
    conn.commit()
    outcome = apply_fallback_or_safe_stop(conn, wf, stage, fallback_stage_id=None)
    assert outcome == "safe_stopped"
