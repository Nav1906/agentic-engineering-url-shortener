"""Append-only orchestration_decision_lineage writer (T063; FR-503).

No UPDATE/DELETE function exists in this module by design — enforcement is
code-review convention, not a DB constraint (disclosed limitation).
"""
from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import Any

from src.api.schemas import DecisionLineageEntry


def append(
    conn: sqlite3.Connection,
    workflow_instance_id: str,
    decision_type: str,
    detail: dict[str, Any],
) -> int:
    now = datetime.now(UTC).isoformat()
    cur = conn.execute(
        "INSERT INTO orchestration_decision_lineage "
        "(workflow_instance_id, decision_type, detail, created_at) VALUES (?,?,?,?)",
        (workflow_instance_id, decision_type, json.dumps(detail), now),
    )
    conn.commit()
    assert cur.lastrowid is not None  # AUTOINCREMENT PK always assigns one on INSERT
    return cur.lastrowid


def get_lineage(conn: sqlite3.Connection, workflow_instance_id: str) -> list[DecisionLineageEntry]:
    rows = conn.execute(
        "SELECT decision_type, detail, created_at FROM orchestration_decision_lineage "
        "WHERE workflow_instance_id = ? ORDER BY id",
        (workflow_instance_id,),
    ).fetchall()
    return [
        DecisionLineageEntry(
            decision_type=r["decision_type"], detail=json.loads(r["detail"]), created_at=r["created_at"]
        )
        for r in rows
    ]
