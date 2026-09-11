"""Policy-evaluation stage (T051, T052; FR-303, FR-304)."""
from __future__ import annotations

import sqlite3
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Literal

Outcome = Literal["PASS", "FAIL", "EXCEPTION-REQUESTED", "NOT-APPLICABLE"]


def evaluate_policy(
    conn: sqlite3.Connection,
    policy_id: str,
    policy_version: str,
    check_fn: Callable[[], Outcome],
    workflow_instance_id: str | None = None,
    artifact_revision: str | None = None,
) -> int:
    """FR-303: every applicable check records exactly one outcome together
    with the policy version evaluated — no path runs a policy check without
    a recorded version. T105: also records the artifact_revision this
    evaluation applies to, so a later revision bump (replanning) can be
    detected as making the evaluation stale — see
    src/policy/live.py::is_release_ready."""
    outcome = check_fn()
    now = datetime.now(UTC).isoformat()
    cur = conn.execute(
        "INSERT INTO policy_evaluation "
        "(workflow_instance_id, policy_id, policy_version, artifact_revision, outcome, evaluated_at) "
        "VALUES (?,?,?,?,?,?)",
        (workflow_instance_id, policy_id, policy_version, artifact_revision, outcome, now),
    )
    conn.commit()
    return cur.lastrowid  # type: ignore[return-value]


def has_unresolved_fail(conn: sqlite3.Connection, workflow_instance_id: str) -> bool:
    """T052: FAIL mechanically blocks downstream progression. A FAIL is
    "resolved" only if superseded by a non-expired policy_exception row for
    the same evaluation."""
    now = datetime.now(UTC).isoformat()
    rows = conn.execute(
        "SELECT id FROM policy_evaluation WHERE workflow_instance_id = ? AND outcome = 'FAIL'",
        (workflow_instance_id,),
    ).fetchall()
    for row in rows:
        exception = conn.execute(
            "SELECT expires_at FROM policy_exception WHERE policy_evaluation_id = ? AND expires_at > ?",
            (row["id"], now),
        ).fetchone()
        if exception is None:
            return True
    return False
