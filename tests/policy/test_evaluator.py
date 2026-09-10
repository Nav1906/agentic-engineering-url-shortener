"""T051: policy-evaluation stage produces all 4 outcomes; T052: FAIL blocks."""
import pytest

import src.persistence.db as db_module
from src.orchestration.models import create_workflow_instance
from src.policy.evaluator import evaluate_policy, has_unresolved_fail


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    yield c
    c.close()


@pytest.mark.parametrize("outcome", ["PASS", "FAIL", "EXCEPTION-REQUESTED", "NOT-APPLICABLE"])
def test_all_four_outcomes_producible(conn, outcome):
    eval_id = evaluate_policy(conn, "p1", "1.0", lambda: outcome)
    row = conn.execute("SELECT outcome FROM policy_evaluation WHERE id=?", (eval_id,)).fetchone()
    assert row["outcome"] == outcome


def test_fail_blocks_until_resolved(conn):
    wf = create_workflow_instance(conn, "req")
    evaluate_policy(conn, "p1", "1.0", lambda: "FAIL", workflow_instance_id=wf)
    assert has_unresolved_fail(conn, wf) is True


def test_pass_does_not_block(conn):
    wf = create_workflow_instance(conn, "req")
    evaluate_policy(conn, "p1", "1.0", lambda: "PASS", workflow_instance_id=wf)
    assert has_unresolved_fail(conn, wf) is False
