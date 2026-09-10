"""T054: expired exception -> policy treated as FAIL again."""
from datetime import UTC, datetime, timedelta

import pytest

import src.persistence.db as db_module
from src.orchestration.models import create_workflow_instance
from src.policy.evaluator import evaluate_policy, has_unresolved_fail
from src.policy.exception import create_exception, is_expired


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    yield c
    c.close()


def test_unexpired_exception_resolves_the_fail(conn):
    wf = create_workflow_instance(conn, "req")
    eval_id = evaluate_policy(conn, "p1", "1.0", lambda: "FAIL", workflow_instance_id=wf)
    future = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    create_exception(conn, eval_id, "r", "s", "alice", "cc", future)
    assert has_unresolved_fail(conn, wf) is False


def test_expired_exception_treated_as_failure_again(conn):
    wf = create_workflow_instance(conn, "req")
    eval_id = evaluate_policy(conn, "p1", "1.0", lambda: "FAIL", workflow_instance_id=wf)
    past = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    exc_id = create_exception(conn, eval_id, "r", "s", "alice", "cc", past)
    assert is_expired(conn, exc_id) is True
    assert has_unresolved_fail(conn, wf) is True
