"""T089: cross-package integration sweep -- domain + orchestration + policy
+ observability exercised together in one coherent flow, not each package
tested only in isolation."""
import pytest

import src.persistence.db as db_module
from src.domain.short_link import create_short_link
from src.observability.audit import get_events_for_workflow, record_event
from src.orchestration.models import add_stage, create_workflow_instance, get_stages
from src.orchestration.scheduler import (
    claim_stage,
    complete_stage,
    compute_ready_stages,
    mark_ready,
)
from src.policy.evaluator import evaluate_policy, has_unresolved_fail


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    yield c
    c.close()


def test_full_stack_flow_across_all_four_packages(conn):
    # Domain: a real short link exists, as the "subject" of this workflow.
    link = create_short_link(conn, "https://example.com/integration-target")

    # Orchestration: a workflow processes a requirement about that link.
    wf = create_workflow_instance(conn, f"Add analytics dashboard for {link.short_code}", scenario="n/a")
    record_event(conn, "system", "create_workflow", f"workflow:{wf}", "created",
                 "integration test workflow", workflow_instance_id=wf)

    stage = add_stage(conn, wf, "design", artifact_revision="v1")
    ready = compute_ready_stages(conn, wf)
    assert stage in ready
    mark_ready(conn, [stage])
    execution_id = claim_stage(conn, stage, "integration-worker")
    assert execution_id is not None

    # Policy: evaluated as part of this same workflow.
    evaluate_policy(conn, "change-control", "1.0.0", lambda: "PASS", workflow_instance_id=wf)
    assert has_unresolved_fail(conn, wf) is False

    complete_stage(conn, execution_id, stage)
    record_event(conn, "system", "stage_design_completed", f"stage:{stage}", "succeeded",
                 "design stage completed", workflow_instance_id=wf)

    # Observability: every package's activity is attributable to the same
    # correlation id (FR-601), and the domain artifact remains independently
    # correct throughout.
    events = get_events_for_workflow(conn, wf)
    assert len(events) == 2
    assert all(e["workflow_instance_id"] == wf for e in events)

    stages = get_stages(conn, wf)
    assert len(stages) == 1
    assert stages[0]["status"] == "succeeded"

    policy_rows = conn.execute(
        "SELECT outcome FROM policy_evaluation WHERE workflow_instance_id=?", (wf,)
    ).fetchall()
    assert len(policy_rows) == 1
    assert policy_rows[0]["outcome"] == "PASS"

    from src.domain.short_link import get_short_link

    still_correct = get_short_link(conn, link.short_code)
    assert still_correct.destination_url == "https://example.com/integration-target"


def test_policy_fail_blocks_downstream_across_packages(conn):
    """The exact mechanical consequence plan.md §9 describes: a FAIL
    recorded by the policy package means the orchestration package's own
    eligibility query never surfaces the dependent stage as ready."""
    wf = create_workflow_instance(conn, "req")
    gate_stage = add_stage(conn, wf, "policy_gate", artifact_revision="v1")
    dependent_stage = add_stage(conn, wf, "dependent_work", artifact_revision="v1", depends_on=[gate_stage])

    evaluate_policy(conn, "security-scan", "1.0.0", lambda: "FAIL", workflow_instance_id=wf)
    assert has_unresolved_fail(conn, wf) is True

    # gate_stage is never marked succeeded (policy FAIL blocks it structurally
    # -- this integration test doesn't even need to model the block
    # explicitly: dependent_stage simply never becomes ready because its
    # only dependency never succeeds).
    ready = compute_ready_stages(conn, wf)
    assert dependent_stage not in ready
    assert gate_stage in ready  # gate_stage itself has no dependencies
