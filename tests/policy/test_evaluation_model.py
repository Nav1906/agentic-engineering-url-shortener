"""T050: policy_evaluation schema."""
import pytest

import src.persistence.db as db_module
from src.policy.evaluator import evaluate_policy


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    yield c
    c.close()


def test_evaluation_recorded_with_version(conn):
    eval_id = evaluate_policy(conn, "dependency-secret-scan", "1.0.0", lambda: "PASS")
    row = conn.execute("SELECT * FROM policy_evaluation WHERE id=?", (eval_id,)).fetchone()
    assert row["policy_id"] == "dependency-secret-scan"
    assert row["policy_version"] == "1.0.0"
    assert row["outcome"] == "PASS"
