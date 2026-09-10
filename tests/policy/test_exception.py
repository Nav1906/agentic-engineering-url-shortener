"""T053: policy_exception, all required fields."""
from datetime import UTC, datetime, timedelta

import pytest

import src.persistence.db as db_module
from src.policy.evaluator import evaluate_policy
from src.policy.exception import create_exception


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    yield c
    c.close()


def test_exception_has_all_required_fields(conn):
    eval_id = evaluate_policy(conn, "p1", "1.0", lambda: "EXCEPTION-REQUESTED")
    future = (datetime.now(UTC) + timedelta(days=7)).isoformat()
    exc_id = create_exception(conn, eval_id, "reason", "scope", "alice", "manual review", future)
    row = conn.execute("SELECT * FROM policy_exception WHERE id=?", (exc_id,)).fetchone()
    for field in ("reason", "scope", "approving_identity", "compensating_control", "approved_at", "expires_at"):
        assert row[field] is not None
