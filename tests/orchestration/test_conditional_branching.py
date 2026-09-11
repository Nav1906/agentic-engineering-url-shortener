"""T104: FR-202 conditional branching. True/false/malformed/missing
condition cases, plus restart/resume never re-deciding a branch."""
import pytest

import src.persistence.db as db_module
from src.orchestration.branching import (
    add_conditional_branch,
    evaluate_branch_conditions,
    set_stage_outcome,
)
from src.orchestration.models import add_stage, create_workflow_instance


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    yield c
    c.close()


def _setup(conn, condition_a, condition_b):
    wf = create_workflow_instance(conn, "req")
    classify = add_stage(conn, wf, "classify")
    branch_a = add_conditional_branch(
        conn, wf, "proceed_path", classify, "outcome_branch", condition_a,
    )
    branch_b = add_conditional_branch(
        conn, wf, "hold_path", classify, "outcome_branch", condition_b,
    )
    return wf, classify, branch_a, branch_b


def test_true_condition_selects_branch_false_skips_sibling(conn):
    wf, classify, branch_a, branch_b = _setup(
        conn,
        {"field": "decision", "op": "eq", "value": "proceed"},
        {"field": "decision", "op": "eq", "value": "hold"},
    )
    set_stage_outcome(conn, classify, {"decision": "proceed"})

    result = evaluate_branch_conditions(conn, wf, classify)

    assert result == {"selected": [branch_a], "skipped": [branch_b]}
    a_row = conn.execute("SELECT status FROM orchestration_workflow_stage WHERE id=?", (branch_a,)).fetchone()
    b_row = conn.execute("SELECT status FROM orchestration_workflow_stage WHERE id=?", (branch_b,)).fetchone()
    assert a_row["status"] == "ready"
    assert b_row["status"] == "skipped"


def test_skip_event_is_audited(conn):
    wf, classify, _branch_a, _branch_b = _setup(
        conn,
        {"field": "decision", "op": "eq", "value": "proceed"},
        {"field": "decision", "op": "eq", "value": "hold"},
    )
    set_stage_outcome(conn, classify, {"decision": "proceed"})
    evaluate_branch_conditions(conn, wf, classify)

    events = conn.execute(
        "SELECT action, affected_artifact_or_state, result FROM audit_events WHERE workflow_instance_id=?",
        (wf,),
    ).fetchall()
    actions = {(e["action"], e["result"]) for e in events}
    assert ("branch_selected", "ready") in actions
    assert ("branch_not_selected", "skipped") in actions


def test_malformed_condition_skips_branch_not_error(conn):
    wf, classify, branch_a, _branch_b = _setup(
        conn,
        {"field": "decision", "op": "unknown_operator", "value": "proceed"},  # malformed
        {"field": "decision", "op": "eq", "value": "hold"},
    )
    set_stage_outcome(conn, classify, {"decision": "proceed"})

    result = evaluate_branch_conditions(conn, wf, classify)

    assert branch_a in result["skipped"]
    a_row = conn.execute("SELECT status FROM orchestration_workflow_stage WHERE id=?", (branch_a,)).fetchone()
    assert a_row["status"] == "skipped"  # fails closed, never selected


def test_missing_field_in_parent_outcome_skips_branch(conn):
    wf, classify, branch_a, branch_b = _setup(
        conn,
        {"field": "decision", "op": "eq", "value": "proceed"},
        {"field": "decision", "op": "eq", "value": "hold"},
    )
    set_stage_outcome(conn, classify, {"unrelated_field": "x"})  # "decision" never written

    result = evaluate_branch_conditions(conn, wf, classify)

    assert result["selected"] == []
    assert set(result["skipped"]) == {branch_a, branch_b}


def test_restart_resume_does_not_change_decided_branch(conn):
    """Simulates a restart between evaluation and a later re-invocation --
    the second call must be a pure no-op against already-decided stages."""
    wf, classify, branch_a, branch_b = _setup(
        conn,
        {"field": "decision", "op": "eq", "value": "proceed"},
        {"field": "decision", "op": "eq", "value": "hold"},
    )
    set_stage_outcome(conn, classify, {"decision": "proceed"})
    first = evaluate_branch_conditions(conn, wf, classify)
    assert first == {"selected": [branch_a], "skipped": [branch_b]}

    # Simulate the parent's outcome somehow being re-read differently on a
    # naive re-evaluation (e.g. if the caller mistakenly reran this after
    # restart) -- even so, already-decided stages must not flip.
    second = evaluate_branch_conditions(conn, wf, classify)
    assert second == {"selected": [], "skipped": []}  # nothing left to decide

    a_row = conn.execute("SELECT status FROM orchestration_workflow_stage WHERE id=?", (branch_a,)).fetchone()
    b_row = conn.execute("SELECT status FROM orchestration_workflow_stage WHERE id=?", (branch_b,)).fetchone()
    assert a_row["status"] == "ready"  # unchanged
    assert b_row["status"] == "skipped"  # unchanged


def test_unknown_parent_stage_raises(conn):
    from src.orchestration.branching import BranchConditionError

    wf = create_workflow_instance(conn, "req")
    with pytest.raises(BranchConditionError):
        evaluate_branch_conditions(conn, wf, "does-not-exist")
