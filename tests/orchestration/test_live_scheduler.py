"""T106: in-process background scheduler -- direct tick() tests (the
asyncio wrapper is exercised end-to-end via
tests/e2e/test_live_workflow_execution.py). Covers periodic scheduling
mechanics, no-duplicate-claims under concurrent ticks, and policy-FAIL
blocking."""
import threading

import pytest

import src.persistence.db as db_module
from src.orchestration.branching import add_conditional_branch
from src.orchestration.lineage import append as append_lineage
from src.orchestration.live_scheduler import tick
from src.orchestration.models import add_stage, create_workflow_instance


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    yield c
    c.close()


def _seed_demo_pipeline(conn, wf):
    intake = add_stage(conn, wf, "intake")
    classify = add_stage(conn, wf, "classify", depends_on=[intake])
    proceed = add_conditional_branch(
        conn, wf, "proceed_path", classify, "outcome_branch",
        {"field": "decision", "op": "eq", "value": "proceed"},
    )
    hold = add_conditional_branch(
        conn, wf, "hold_path", classify, "outcome_branch",
        {"field": "decision", "op": "eq", "value": "hold"},
    )
    return intake, classify, proceed, hold


def test_full_pipeline_drives_to_completion_over_several_ticks(conn, tmp_path, monkeypatch):
    db_path = str(tmp_path / "app.db")
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    wf = create_workflow_instance(conn, "demo requirement")
    _seed_demo_pipeline(conn, wf)

    for _ in range(6):  # intake, classify, branch-eval, proceed_path, terminal check
        tick("test-worker")

    row = conn.execute("SELECT status FROM orchestration_workflow_instance WHERE id=?", (wf,)).fetchone()
    assert row["status"] == "completed"

    stages = {
        r["name"]: r["status"]
        for r in conn.execute(
            "SELECT name, status FROM orchestration_workflow_stage WHERE workflow_instance_id=?", (wf,)
        ).fetchall()
    }
    assert stages["intake"] == "succeeded"
    assert stages["classify"] == "succeeded"
    assert stages["proceed_path"] == "succeeded"
    assert stages["hold_path"] == "skipped"  # T104 branch correctly not selected


def test_policy_fail_stops_workflow_automatically(conn, tmp_path, monkeypatch):
    db_path = str(tmp_path / "app.db")
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    wf = create_workflow_instance(conn, "req with an undeclared material change")
    append_lineage(conn, wf, "material_change_detected", {"change_type": "schema"})
    add_stage(conn, wf, "intake")

    tick("test-worker")  # first tick: policy checks run automatically, change-control -> FAIL

    row = conn.execute("SELECT status FROM orchestration_workflow_instance WHERE id=?", (wf,)).fetchone()
    assert row["status"] == "safe_stopped"

    policy_rows = conn.execute(
        "SELECT policy_id, outcome FROM policy_evaluation WHERE workflow_instance_id=?", (wf,)
    ).fetchall()
    assert any(r["policy_id"] == "change-control" and r["outcome"] == "FAIL" for r in policy_rows)


def test_no_duplicate_claims_under_concurrent_ticks(tmp_path, monkeypatch):
    """Same guarantee T058 already proves for claim_stage() directly,
    reused here through the live loop's own code path."""
    db_path = str(tmp_path / "app.db")
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    setup_conn = db_module.get_connection()
    db_module.init_schema(setup_conn)
    wf = create_workflow_instance(setup_conn, "req")
    add_stage(setup_conn, wf, "intake")
    setup_conn.close()

    results = []
    lock = threading.Lock()

    def run_tick(worker_id: str):
        tick(worker_id)
        with lock:
            results.append(worker_id)

    threads = [threading.Thread(target=run_tick, args=(f"worker-{i}",)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    conn = db_module.get_connection()
    execs = conn.execute("SELECT claimed_by_worker_id, status FROM orchestration_stage_execution").fetchall()
    completed = [e for e in execs if e["status"] == "completed"]
    assert len(completed) == 1  # exactly one worker's claim was ever promoted to completed
    conn.close()


def test_no_duplicate_policy_evaluations_under_concurrent_ticks(tmp_path, monkeypatch):
    """Regression test added after the independent assessment flagged
    _drive_workflow's SELECT-then-run_mandatory_policy_checks() guard as a
    plausible TOCTOU shape (real concern: two ticks for the same workflow
    both observing "no policy_evaluation rows yet" would each insert all 3
    mandatory-policy rows, producing 6 instead of 3). Reuses the same
    real-thread concurrency harness as
    test_no_duplicate_claims_under_concurrent_ticks above to prove the
    guard is actually safe under real concurrent access, not merely
    reasoned about."""
    db_path = str(tmp_path / "app.db")
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    setup_conn = db_module.get_connection()
    db_module.init_schema(setup_conn)
    wf = create_workflow_instance(setup_conn, "req")
    add_stage(setup_conn, wf, "intake")
    setup_conn.close()

    def run_tick(worker_id: str):
        tick(worker_id)

    threads = [threading.Thread(target=run_tick, args=(f"worker-{i}",)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    conn = db_module.get_connection()
    rows = conn.execute(
        "SELECT policy_id FROM policy_evaluation WHERE workflow_instance_id=?", (wf,)
    ).fetchall()
    assert len(rows) == 3  # exactly one row per mandatory policy, never duplicated
    conn.close()
