"""Policy exception workflow (T053, T054; FR-305)."""
from __future__ import annotations

import sqlite3
import uuid
from datetime import UTC, datetime


def create_exception(
    conn: sqlite3.Connection,
    policy_evaluation_id: int,
    reason: str,
    scope: str,
    approving_identity: str,
    compensating_control: str,
    expires_at: str,
) -> str:
    """FR-305: every field required — policy (via policy_evaluation_id),
    reason, scope, approving authority, compensating control, timestamp,
    expiry/review condition. This function does not itself check the
    approver's role; callers (the approval-gate endpoint) are responsible
    for having already authorized the approving_identity."""
    exception_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    conn.execute(
        "INSERT INTO policy_exception "
        "(id, policy_evaluation_id, reason, scope, approving_identity, compensating_control, approved_at, expires_at) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (exception_id, policy_evaluation_id, reason, scope, approving_identity, compensating_control, now, expires_at),
    )
    conn.commit()
    return exception_id


def is_expired(conn: sqlite3.Connection, exception_id: str) -> bool:
    """T054: an expired, unreviewed exception is treated as a policy
    failure again, not silently still-applying."""
    row = conn.execute("SELECT expires_at FROM policy_exception WHERE id = ?", (exception_id,)).fetchone()
    if row is None:
        raise ValueError(f"unknown exception id {exception_id!r}")
    return row["expires_at"] <= datetime.now(UTC).isoformat()
