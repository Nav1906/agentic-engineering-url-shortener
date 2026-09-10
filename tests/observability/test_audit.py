"""T080: audit_events append-only writer, all required fields (FR-601,602)."""
import pytest

import src.persistence.db as db_module
from src.observability.audit import record_event


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    yield c
    c.close()


def test_all_required_fields_present(conn):
    event_id = record_event(
        conn, "system", "test_action", "some_state", "success", "because",
        workflow_instance_id=None,
    )
    row = conn.execute("SELECT * FROM audit_events WHERE id=?", (event_id,)).fetchone()
    for field in ("actor_type", "action", "timestamp", "affected_artifact_or_state", "result", "reason"):
        assert row[field] is not None


def test_demonstration_flag_default_true(conn):
    event_id = record_event(conn, "system", "a", "b", "c", "d")
    row = conn.execute("SELECT demonstration_flag FROM audit_events WHERE id=?", (event_id,)).fetchone()
    assert row["demonstration_flag"] == 1
