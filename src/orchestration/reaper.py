"""Lease-based stale-worker detection + effect reconciliation (T059, T060;
ADR-0005 Rev.3, ADR-0007). Periodic sweep — callable on its own, not only in
response to an event, closing the "zero other transitions occurring" gap
Round 3 caught as missing.
"""
from __future__ import annotations

import sqlite3
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Literal

ReconciliationResult = Literal["not_completed", "already_completed"]


def sweep_stale_leases(conn: sqlite3.Connection) -> list[str]:
    """T059: periodic reaper. Finds stage_execution rows still claimed/
    running whose lease has expired, marks them abandoned, and moves the
    owning stage to awaiting_reconciliation — regardless of whether this
    sweep was triggered by any other event. Returns the affected stage_ids.
    """
    now = datetime.now(UTC).isoformat()
    stale = conn.execute(
        "SELECT id, stage_id FROM orchestration_stage_execution "
        "WHERE status IN ('claimed','running') AND lease_expires_at < ?",
        (now,),
    ).fetchall()
    stage_ids: list[str] = []
    for row in stale:
        conn.execute(
            "UPDATE orchestration_stage_execution SET status='abandoned' WHERE id=?",
            (row["id"],),
        )
        conn.execute(
            "UPDATE orchestration_workflow_stage SET status='awaiting_reconciliation', updated_at=? "
            "WHERE id=? AND status='running'",
            (now, row["stage_id"]),
        )
        stage_ids.append(row["stage_id"])
    conn.commit()
    return stage_ids


def reconcile_stage(
    conn: sqlite3.Connection,
    stage_id: str,
    probe_effect: Callable[[str], bool] | None = None,
) -> ReconciliationResult:
    """T060: check_effect() dispatch, required after exception, timeout, OR
    stale lease alike (Round 3 correction — no path treats an in-band
    exception as automatically safe without this).

    idempotent stages: always safe to retry without a probe (re-running has
    no additional effect beyond what already happened).
    externally_observable_uncertain stages: MUST call probe_effect to learn
    whether the effect actually completed before any retry is issued.
    """
    stage = conn.execute(
        "SELECT effect_class FROM orchestration_workflow_stage WHERE id=?", (stage_id,)
    ).fetchone()
    now = datetime.now(UTC).isoformat()

    if stage["effect_class"] == "idempotent":
        result: ReconciliationResult = "not_completed"
    else:
        if probe_effect is None:
            raise ValueError(
                "externally_observable_uncertain stages require a probe_effect function"
            )
        completed = probe_effect(stage_id)
        result = "already_completed" if completed else "not_completed"

    if result == "already_completed":
        conn.execute(
            "UPDATE orchestration_workflow_stage SET status='succeeded', updated_at=? WHERE id=?",
            (now, stage_id),
        )
    else:
        conn.execute(
            "UPDATE orchestration_workflow_stage SET status='failed_transient', updated_at=? WHERE id=?",
            (now, stage_id),
        )
    conn.commit()
    return result
