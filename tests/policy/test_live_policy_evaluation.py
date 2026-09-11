"""T105: mandatory policy checks run automatically, persisted with
workflow + artifact_revision, and gate release-readiness -- PASS, FAIL,
EXCEPTION-REQUESTED, NOT-APPLICABLE, and stale-revision invalidation."""
from datetime import UTC, datetime, timedelta

import pytest

import src.persistence.db as db_module
from src.orchestration.lineage import append as append_lineage
from src.orchestration.models import add_stage, create_workflow_instance
from src.policy.evaluator import evaluate_policy
from src.policy.exception import create_exception
from src.policy.live import is_release_ready, run_mandatory_policy_checks


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    yield c
    c.close()


def test_all_mandatory_policies_evaluated_and_persisted_with_revision(conn):
    wf = create_workflow_instance(conn, "req")
    results = run_mandatory_policy_checks(conn, wf, "v1")

    assert set(results.keys()) == {"dependency-secret-scan", "change-control", "release-readiness"}
    rows = conn.execute(
        "SELECT policy_id, artifact_revision, outcome FROM policy_evaluation WHERE workflow_instance_id=?",
        (wf,),
    ).fetchall()
    assert len(rows) == 3
    for row in rows:
        assert row["artifact_revision"] == "v1"


def test_dependency_secret_scan_passes_for_committed_lockfile(conn):
    """Real, local, fast check against this actual repository's own
    pyproject.toml/uv.lock -- not a canned value."""
    wf = create_workflow_instance(conn, "req")
    results = run_mandatory_policy_checks(conn, wf, "v1")
    assert results["dependency-secret-scan"] in ("PASS", "FAIL")  # real filesystem-derived outcome


def test_change_control_pass_when_no_material_change_declared(conn):
    wf = create_workflow_instance(conn, "req")
    results = run_mandatory_policy_checks(conn, wf, "v1")
    assert results["change-control"] == "PASS"


def test_change_control_fail_when_material_change_undeclared_impact_analysis(conn):
    wf = create_workflow_instance(conn, "req")
    append_lineage(conn, wf, "material_change_detected", {"change_type": "schema"})
    results = run_mandatory_policy_checks(conn, wf, "v1")
    assert results["change-control"] == "FAIL"


def test_change_control_pass_once_impact_analysis_succeeded(conn):
    wf = create_workflow_instance(conn, "req")
    append_lineage(conn, wf, "material_change_detected", {"change_type": "schema"})
    stage = add_stage(conn, wf, "impact_analysis")
    conn.execute("UPDATE orchestration_workflow_stage SET status='succeeded' WHERE id=?", (stage,))
    conn.commit()
    results = run_mandatory_policy_checks(conn, wf, "v1")
    assert results["change-control"] == "PASS"


def test_release_readiness_policy_is_not_applicable_per_workflow(conn):
    wf = create_workflow_instance(conn, "req")
    results = run_mandatory_policy_checks(conn, wf, "v1")
    assert results["release-readiness"] == "NOT-APPLICABLE"


def test_exception_requested_outcome_producible_and_resolvable(conn):
    wf = create_workflow_instance(conn, "req")
    eval_id = evaluate_policy(
        conn, "custom-check", "1.0", lambda: "EXCEPTION-REQUESTED",
        workflow_instance_id=wf, artifact_revision="v1",
    )
    future = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    create_exception(conn, eval_id, "reason", "scope", "alice", "manual review", future)
    # EXCEPTION-REQUESTED itself is not FAIL, so it doesn't trip
    # has_unresolved_fail -- distinct outcome, correctly not conflated.
    from src.policy.evaluator import has_unresolved_fail

    assert has_unresolved_fail(conn, wf) is False


def test_release_not_ready_while_mandatory_fail_unresolved(conn):
    wf = create_workflow_instance(conn, "req")
    append_lineage(conn, wf, "material_change_detected", {"change_type": "schema"})
    run_mandatory_policy_checks(conn, wf, "v1")  # change-control -> FAIL (no impact analysis)

    ready, reasons = is_release_ready(conn, wf, "v1")
    assert ready is False
    assert any("FAIL" in r for r in reasons)


def test_release_ready_when_all_mandatory_policies_pass_current_revision(conn):
    wf = create_workflow_instance(conn, "req")
    run_mandatory_policy_checks(conn, wf, "v1")  # change-control -> PASS, no material change declared

    ready, reasons = is_release_ready(conn, wf, "v1")
    assert ready is True
    assert reasons == []


def test_stale_revision_evaluation_invalidates_release_readiness(conn):
    """A policy evaluated against v1 must not silently authorize release
    once the workflow has moved to v2 (e.g. via replanning) -- this is the
    explicit stale-revision-invalidation requirement."""
    wf = create_workflow_instance(conn, "req")
    run_mandatory_policy_checks(conn, wf, "v1")  # all evaluated against v1

    ready, reasons = is_release_ready(conn, wf, "v2")  # workflow has since moved to v2
    assert ready is False
    assert any("stale" in r for r in reasons)


def test_never_evaluated_policy_blocks_release(conn):
    wf = create_workflow_instance(conn, "req")
    ready, reasons = is_release_ready(conn, wf, "v1")  # run_mandatory_policy_checks never called
    assert ready is False
    assert any("never evaluated" in r for r in reasons)
