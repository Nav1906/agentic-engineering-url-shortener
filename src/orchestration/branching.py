"""Conditional workflow branching (T104; FR-202's "conditional branching
based on workflow state" -- the one previously-undelivered clause of
FR-202, sequential/parallel/sync having already been real since T056-T058).

A branch condition is evaluated against the PRECEDING stage's persisted
outcome (its `postconditions` JSON, written via `set_stage_outcome` once
that stage succeeds) -- never against live external state, so evaluation
is deterministic and replay-safe (restart/resume never re-decides a branch
already decided).
"""
from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import Any, Literal

from src.observability.audit import record_event
from src.orchestration.models import add_stage

Operator = Literal["eq", "ne"]


class BranchConditionError(ValueError):
    """Raised only for a programming error in how a branch was constructed
    (never for a malformed/missing condition at evaluation time -- those
    are expected, handled outcomes: the branch is simply not selected)."""


def set_stage_outcome(conn: sqlite3.Connection, stage_id: str, outcome: dict[str, Any]) -> None:
    """Persists the structured outcome a downstream conditional branch will
    evaluate against. Distinct from T062's `outcome_detail` (validator
    evidence) -- this is the stage's own decision/result payload."""
    conn.execute(
        "UPDATE orchestration_workflow_stage SET postconditions=? WHERE id=?",
        (json.dumps(outcome), stage_id),
    )
    conn.commit()


def add_conditional_branch(
    conn: sqlite3.Connection,
    workflow_instance_id: str,
    name: str,
    depends_on_stage_id: str,
    branch_group: str,
    condition: dict[str, Any],
    artifact_revision: str = "v1",
) -> str:
    """Creates a stage that only becomes eligible if `condition` evaluates
    true against depends_on_stage_id's persisted outcome. `branch_group`
    marks this stage as mutually exclusive with its siblings sharing the
    same group -- exactly one is selected (or none, if the condition data
    is malformed/missing; see evaluate_branch_conditions)."""
    stage_id = add_stage(
        conn, workflow_instance_id, name, artifact_revision=artifact_revision,
        depends_on=[depends_on_stage_id],
    )
    conn.execute(
        "UPDATE orchestration_workflow_stage SET preconditions=? WHERE id=?",
        (json.dumps({"branch_group": branch_group, "condition": condition}), stage_id),
    )
    conn.commit()
    return stage_id


def _evaluate_condition(condition: dict[str, Any], outcome: dict[str, Any]) -> bool:
    field = condition["field"]
    op = condition["op"]
    expected = condition["value"]
    if field not in outcome:
        raise KeyError(field)
    actual = outcome[field]
    if op == "eq":
        return actual == expected
    if op == "ne":
        return actual != expected
    raise ValueError(f"unknown operator {op!r}")


def evaluate_branch_conditions(
    conn: sqlite3.Connection,
    workflow_instance_id: str,
    parent_stage_id: str,
) -> dict[str, list[str]]:
    """Call once, after parent_stage_id succeeds with a persisted outcome
    (set_stage_outcome). Idempotent by construction: only stages still
    'pending' are touched, so calling this again after a restart never
    changes a branch decision already made (T104's restart/resume
    requirement) -- a decided branch (ready/succeeded/skipped) is left
    exactly as it was.

    Returns {"selected": [...], "skipped": [...]}."""
    now = datetime.now(UTC).isoformat()

    parent = conn.execute(
        "SELECT postconditions FROM orchestration_workflow_stage WHERE id=?", (parent_stage_id,)
    ).fetchone()
    if parent is None:
        raise BranchConditionError(f"unknown parent stage {parent_stage_id!r}")
    try:
        parent_outcome = json.loads(parent["postconditions"]) if parent["postconditions"] else {}
    except json.JSONDecodeError:
        parent_outcome = {}

    dependents = conn.execute(
        "SELECT stage_id FROM orchestration_stage_dependency WHERE depends_on_stage_id=?",
        (parent_stage_id,),
    ).fetchall()

    selected: list[str] = []
    skipped: list[str] = []

    for row in dependents:
        stage_id = row["stage_id"]
        stage = conn.execute(
            "SELECT status, preconditions FROM orchestration_workflow_stage WHERE id=?", (stage_id,)
        ).fetchone()
        if stage is None or stage["status"] != "pending":
            continue  # already decided (or gone) -- never re-decide

        try:
            precond = json.loads(stage["preconditions"]) if stage["preconditions"] else None
        except json.JSONDecodeError:
            precond = None

        if not precond or "condition" not in precond:
            continue  # not a conditional branch at all -- leave to normal eligibility

        condition = precond["condition"]
        try:
            is_true = _evaluate_condition(condition, parent_outcome)
        except (KeyError, TypeError):
            # Missing-condition case: the field this condition needs was
            # never written into the parent's outcome.
            conn.execute(
                "UPDATE orchestration_workflow_stage SET status='skipped', updated_at=? WHERE id=?",
                (now, stage_id),
            )
            record_event(
                conn, "system", "branch_not_selected", f"stage:{stage_id}", "skipped",
                f"condition references a field missing from parent outcome: {condition!r}",
                workflow_instance_id=workflow_instance_id,
            )
            skipped.append(stage_id)
            continue
        except ValueError:
            # Malformed condition (bad/unknown operator, or structurally
            # invalid) -- fails closed, same as missing.
            conn.execute(
                "UPDATE orchestration_workflow_stage SET status='skipped', updated_at=? WHERE id=?",
                (now, stage_id),
            )
            record_event(
                conn, "system", "branch_not_selected", f"stage:{stage_id}", "skipped",
                f"malformed branch condition: {condition!r}",
                workflow_instance_id=workflow_instance_id,
            )
            skipped.append(stage_id)
            continue

        if is_true:
            conn.execute(
                "UPDATE orchestration_workflow_stage SET status='ready', updated_at=? WHERE id=?",
                (now, stage_id),
            )
            record_event(
                conn, "system", "branch_selected", f"stage:{stage_id}", "ready",
                f"condition {condition!r} evaluated true against parent outcome",
                workflow_instance_id=workflow_instance_id,
            )
            selected.append(stage_id)
        else:
            conn.execute(
                "UPDATE orchestration_workflow_stage SET status='skipped', updated_at=? WHERE id=?",
                (now, stage_id),
            )
            record_event(
                conn, "system", "branch_not_selected", f"stage:{stage_id}", "skipped",
                f"condition {condition!r} evaluated false against parent outcome",
                workflow_instance_id=workflow_instance_id,
            )
            skipped.append(stage_id)

    conn.commit()
    return {"selected": selected, "skipped": skipped}
