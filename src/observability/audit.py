"""Append-only audit_events writer (T080, T081; FR-601, FR-602, ADR-0008)."""
from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import Any, Literal


def record_event(
    conn: sqlite3.Connection,
    actor_type: Literal["human", "agent", "system"],
    action: str,
    affected_artifact_or_state: str,
    result: str,
    reason: str,
    workflow_instance_id: str | None = None,
    recovery_of_event_id: int | None = None,
    demonstration_flag: bool = True,
    detail: dict[str, Any] | None = None,
) -> int:
    """FR-602: every event carries actor_type, action, timestamp, affected
    artifact/state, result, reason. FR-601: attributable to a correlation
    (workflow_instance) id when one applies."""
    timestamp = datetime.now(UTC).isoformat()
    cur = conn.execute(
        "INSERT INTO audit_events "
        "(workflow_instance_id, actor_type, action, timestamp, "
        " affected_artifact_or_state, result, reason, recovery_of_event_id, "
        " demonstration_flag, detail) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            workflow_instance_id,
            actor_type,
            action,
            timestamp,
            affected_artifact_or_state,
            result,
            reason,
            recovery_of_event_id,
            1 if demonstration_flag else 0,
            json.dumps(detail) if detail is not None else None,
        ),
    )
    conn.commit()
    assert cur.lastrowid is not None  # AUTOINCREMENT PK always assigns one on INSERT
    return cur.lastrowid


def get_events_for_workflow(conn: sqlite3.Connection, workflow_instance_id: str) -> list[sqlite3.Row]:
    """FR-601: every event for one workflow instance shares its correlation ID."""
    return conn.execute(
        "SELECT * FROM audit_events WHERE workflow_instance_id = ? ORDER BY id",
        (workflow_instance_id,),
    ).fetchall()
