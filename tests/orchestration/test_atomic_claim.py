"""T058: concurrent claim attempts, exactly one wins (compare-and-swap)."""
import threading

import pytest

import src.persistence.db as db_module
from src.orchestration.models import add_stage, create_workflow_instance
from src.orchestration.scheduler import claim_stage, mark_ready


@pytest.fixture()
def db_path(tmp_path, monkeypatch):
    path = str(tmp_path / "app.db")
    monkeypatch.setattr(db_module, "DB_PATH", path)
    c = db_module.get_connection()
    db_module.init_schema(c)
    c.close()
    return path


def test_only_one_worker_wins_concurrent_claim(db_path):
    setup_conn = db_module.get_connection()
    wf = create_workflow_instance(setup_conn, "req")
    stage = add_stage(setup_conn, wf, "A")
    mark_ready(setup_conn, [stage])
    setup_conn.close()

    results: list[str | None] = []
    lock = threading.Lock()

    def worker(worker_id: str):
        conn = db_module.get_connection()
        try:
            execution_id = claim_stage(conn, stage, worker_id)
            with lock:
                results.append(execution_id)
        finally:
            conn.close()

    threads = [threading.Thread(target=worker, args=(f"worker-{i}",)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    winners = [r for r in results if r is not None]
    assert len(winners) == 1

    conn = db_module.get_connection()
    row = conn.execute("SELECT status, attempt_count FROM orchestration_workflow_stage WHERE id=?", (stage,)).fetchone()
    assert row["status"] == "running"
    assert row["attempt_count"] == 1
    conn.close()
