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
    # INSERT OR IGNORE + the schema's (workflow, policy, revision) UNIQUE
    # constraint make this race-safe under real concurrent callers (e.g.
    # two scheduler ticks hitting the same workflow at once): only the
    # first insert for a given triple ever lands, cur.rowcount tells us
    # which happened, and a lost race still returns the WINNING row's real
    # id rather than a stale/zero lastrowid.
    cur = conn.execute(
        "INSERT OR IGNORE INTO policy_evaluation "
        "(workflow_instance_id, policy_id, policy_version, artifact_revision, outcome, evaluated_at) "
        "VALUES (?,?,?,?,?,?)",
        (workflow_instance_id, policy_id, policy_version, artifact_revision, outcome, now),
    )
    conn.commit()
    if cur.rowcount == 1:
        return cur.lastrowid  # type: ignore[return-value]
    existing = conn.execute(
        "SELECT id FROM policy_evaluation "
        "WHERE workflow_instance_id IS ? AND policy_id = ? AND artifact_revision IS ?",
        (workflow_instance_id, policy_id, artifact_revision),
    ).fetchone()
    return existing["id"]


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
