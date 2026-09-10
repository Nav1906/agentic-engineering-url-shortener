"""T081: correlation-ID linkage — every event for one workflow shares its ID."""
import pytest

import src.persistence.db as db_module
from src.observability.audit import get_events_for_workflow, record_event
from src.orchestration.models import create_workflow_instance


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    yield c
    c.close()


def test_events_scoped_to_correct_workflow(conn):
    wf1 = create_workflow_instance(conn, "req1")
    wf2 = create_workflow_instance(conn, "req2")
    record_event(conn, "system", "a", "s", "r", "reason", workflow_instance_id=wf1)
    record_event(conn, "system", "b", "s", "r", "reason", workflow_instance_id=wf1)
    record_event(conn, "system", "c", "s", "r", "reason", workflow_instance_id=wf2)

    wf1_events = get_events_for_workflow(conn, wf1)
    assert len(wf1_events) == 2
    assert all(e["workflow_instance_id"] == wf1 for e in wf1_events)
