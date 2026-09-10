"""Scheduler: eligibility query, atomic claiming, recovery (T056, T058, T077).

T056: a stage becomes eligible only when every dependency edge resolves to
'succeeded' — this single query is what separates real orchestration from
linear chaining disguised as orchestration.
"""
from __future__ import annotations

import asyncio
import sqlite3
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

from src.orchestration.models import get_dependencies


def compute_ready_stages(conn: sqlite3.Connection, workflow_instance_id: str) -> list[str]:
    """T056: pure read — returns pending stage IDs whose dependencies are
    ALL succeeded. Does not mutate state (mutation is mark_ready, separate,
    so this function stays trivially testable)."""
    pending = conn.execute(
        "SELECT id FROM orchestration_workflow_stage "
        "WHERE workflow_instance_id = ? AND status = 'pending'",
        (workflow_instance_id,),
    ).fetchall()
    ready: list[str] = []
    for row in pending:
        stage_id = row["id"]
        deps = get_dependencies(conn, stage_id)
        if not deps:
            ready.append(stage_id)
            continue
        placeholders = ",".join("?" for _ in deps)
        succeeded_count = conn.execute(
            f"SELECT COUNT(*) FROM orchestration_workflow_stage "
            f"WHERE id IN ({placeholders}) AND status = 'succeeded'",
            deps,
        ).fetchone()[0]
        if succeeded_count == len(deps):
            ready.append(stage_id)
    return ready


def mark_ready(conn: sqlite3.Connection, stage_ids: list[str]) -> None:
    for stage_id in stage_ids:
        conn.execute(
            "UPDATE orchestration_workflow_stage SET status='ready', updated_at=? "
            "WHERE id=? AND status='pending'",
            (datetime.now(UTC).isoformat(), stage_id),
        )
    conn.commit()


def claim_stage(conn: sqlite3.Connection, stage_id: str, worker_id: str) -> str | None:
    """T058: atomic compare-and-swap claim. Returns the new execution_id, or
    None if another worker already claimed it (0 rows affected)."""
    now = datetime.now(UTC)
    stage = conn.execute(
        "SELECT timeout_seconds, attempt_count FROM orchestration_workflow_stage WHERE id = ?",
        (stage_id,),
    ).fetchone()
    if stage is None:
        return None
    lease_expires = now + timedelta(seconds=max(stage["timeout_seconds"], 30))

    cur = conn.execute(
        "UPDATE orchestration_workflow_stage SET status='running', attempt_count=attempt_count+1, updated_at=? "
        "WHERE id=? AND status='ready'",
        (now.isoformat(), stage_id),
    )
    conn.commit()
    if cur.rowcount == 0:
        return None  # another worker already claimed it, or it wasn't ready

    execution_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO orchestration_stage_execution "
        "(id, stage_id, attempt_number, claimed_by_worker_id, claimed_at, lease_expires_at, "
        " workspace_path, status, outcome_detail) "
        "VALUES (?,?,?,?,?,?, NULL, 'claimed', NULL)",
        (execution_id, stage_id, stage["attempt_count"] + 1, worker_id, now.isoformat(), lease_expires.isoformat()),
    )
    conn.commit()
    return execution_id


def complete_stage(conn: sqlite3.Connection, execution_id: str, stage_id: str) -> bool:
    """Fencing: only affects rows still in claimed/running state (T046's
    fencing rule) — a stale/zombie worker's late write affects 0 rows once
    reconciled."""
    cur = conn.execute(
        "UPDATE orchestration_stage_execution SET status='completed' "
        "WHERE id=? AND status IN ('claimed','running')",
        (execution_id,),
    )
    if cur.rowcount == 0:
        conn.commit()
        return False
    conn.execute(
        "UPDATE orchestration_workflow_stage SET status='succeeded', updated_at=? WHERE id=?",
        (datetime.now(UTC).isoformat(), stage_id),
    )
    conn.commit()
    return True


async def dispatch_ready_stages_parallel(
    db_path: str,
    workflow_instance_id: str,
    stage_ids: list[str],
    worker_id: str,
    execute_fn: Callable[[str], Awaitable[None]],
) -> dict[str, float]:
    """T057: genuine concurrent dispatch of independent, already-ready
    stages via asyncio.gather (each on its own connection since sqlite3
    connections are not safely shared across concurrent async tasks), with
    an explicit synchronization event recorded once all complete — the
    guide's "fan-out and synchronization" requirement, not sequential
    chaining disguised as parallelism.

    Returns {stage_id: start_time_monotonic} so a test can observe overlap.
    """
    import time

    start_times: dict[str, float] = {}

    async def run_one(stage_id: str) -> None:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            execution_id = claim_stage(conn, stage_id, worker_id)
            if execution_id is None:
                return
            start_times[stage_id] = time.monotonic()
            await execute_fn(stage_id)
            complete_stage(conn, execution_id, stage_id)
        finally:
            conn.close()

    await asyncio.gather(*(run_one(sid) for sid in stage_ids))

    # Explicit synchronization event, recorded once all parallel stages
    # have converged — before any stage that depends on all of them.
    sync_conn = sqlite3.connect(db_path)
    sync_conn.row_factory = sqlite3.Row
    try:
        from src.orchestration.lineage import append

        append(
            sync_conn, workflow_instance_id, "synchronization_point",
            {"synchronized_stage_ids": stage_ids},
        )
    finally:
        sync_conn.close()

    return start_times


def recover_on_startup(conn: sqlite3.Connection) -> int:
    """T077 (satisfies T021's xfail test): a stage found 'running' at
    process start is forced to 'failed_transient' — crash recovery."""
    now = datetime.now(UTC).isoformat()
    cur = conn.execute(
        "UPDATE orchestration_workflow_stage SET status='failed_transient', updated_at=? "
        "WHERE status='running'",
        (now,),
    )
    conn.commit()
    return cur.rowcount
