"""Dynamic replanning: material-change detection + invalidation cascade
(T055, T078, T079; FR-501, FR-502, FR-306).
"""
from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from typing import Literal

ChangeType = Literal[
    "requirements", "architecture", "schema", "workflow_states", "security_controls", "release_criteria"
]

MATERIAL_CHANGE_TYPES: set[ChangeType] = {
    "requirements", "architecture", "schema", "workflow_states", "security_controls", "release_criteria",
}


def classify_change(change_type: str) -> bool:
    """FR-306: is this change type one that requires impact analysis and
    change approval before it takes effect? All 6 listed types are
    material — none exempted."""
    return change_type in MATERIAL_CHANGE_TYPES


def invalidate_downstream(
    conn: sqlite3.Connection,
    workflow_instance_id: str,
    new_artifact_revision: str,
    affected_stage_ids: list[str],
) -> dict[str, list[str]]:
    """T078: invalidation cascade on material change. Invalidates EXACTLY
    the affected stages and their approvals — no broader, no narrower
    (FR-501, FR-502). Stages are forced back to 'pending' with the new
    revision; any approval bound to their old revision is invalidated
    (never silently carried forward)."""
    now = datetime.now(UTC).isoformat()
    invalidated_stages: list[str] = []
    invalidated_approvals: list[str] = []

    for stage_id in affected_stage_ids:
        conn.execute(
            "UPDATE orchestration_workflow_stage SET status='pending', artifact_revision=?, "
            "attempt_count=0, updated_at=? WHERE id=?",
            (new_artifact_revision, now, stage_id),
        )
        invalidated_stages.append(stage_id)

        approvals = conn.execute(
            "SELECT id FROM orchestration_approval_decision "
            "WHERE workflow_instance_id=? AND artifact_revision != ? AND invalidated_at IS NULL",
            (workflow_instance_id, new_artifact_revision),
        ).fetchall()
        for approval in approvals:
            conn.execute(
                "UPDATE orchestration_approval_decision SET invalidated_at=? WHERE id=?",
                (now, approval["id"]),
            )
            invalidated_approvals.append(approval["id"])

    conn.commit()
    return {"stages": invalidated_stages, "approvals": invalidated_approvals}


def invalidate_worktree(
    conn: sqlite3.Connection,
    stage_id: str,
) -> bool:
    """T079: any in-progress execution for a now-invalidated stage must
    never be promoted. Marks the latest claimed/running execution abandoned
    -- the same fencing rule T046/scheduler.complete_stage already relies
    on then guarantees a late completion write affects 0 rows."""
    row = conn.execute(
        "SELECT id FROM orchestration_stage_execution WHERE stage_id=? AND status IN ('claimed','running') "
        "ORDER BY claimed_at DESC LIMIT 1",
        (stage_id,),
    ).fetchone()
    if row is None:
        return False
    conn.execute("UPDATE orchestration_stage_execution SET status='abandoned' WHERE id=?", (row["id"],))
    conn.commit()
    return True
