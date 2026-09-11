"""In-process background scheduler, started/stopped via FastAPI's lifespan
(T106). Once a workflow is created through the HTTP API, this loop drives
its ready stages forward automatically -- no direct test-only scheduler
calls required.

External agent adapters remain fail-closed while ADR-0006 is unresolved:
`_execute_stage_safely` below is the ONLY stage-execution path this loop
uses, and it performs nothing beyond safe, built-in, in-process,
deterministic work -- no subprocess, no `claude` CLI invocation, no
credential access. This is a deliberate boundary, not an oversight: wiring
a real external adapter into an automatic loop would be exactly the kind
of unattended, credentialed execution T100-T103 stay blocked to prevent.
"""
from __future__ import annotations

import asyncio
import contextlib
import logging
import sqlite3
import uuid
from datetime import UTC, datetime

from src.observability.audit import record_event
from src.orchestration.branching import evaluate_branch_conditions, set_stage_outcome
from src.orchestration.reaper import sweep_stale_leases
from src.orchestration.scheduler import (
    claim_stage,
    complete_stage,
    compute_ready_stages,
    mark_ready,
)
from src.persistence.db import get_connection
from src.policy.live import run_mandatory_policy_checks

logger = logging.getLogger(__name__)

TICK_INTERVAL_SECONDS = 0.2
_WORKER_PREFIX = "bg-worker"
_DEMO_ARTIFACT_REVISION = "v1"  # single-revision demonstration scope, same
# precedent as src/api/routers/approvals.py::_current_artifact_revision


def _execute_stage_safely(conn: sqlite3.Connection, stage_id: str, stage_name: str) -> None:
    """The ONLY stage-execution path this loop uses. If this is the demo
    pipeline's classification point, writes a deterministic decision so
    downstream conditional branches (T104) have something real to
    evaluate -- disclosed as a built-in deterministic default, not a claim
    of real requirement-classification intelligence."""
    if stage_name == "classify":
        set_stage_outcome(conn, stage_id, {"decision": "proceed"})


def _drive_workflow(conn: sqlite3.Connection, workflow_instance_id: str, worker_id: str) -> None:
    already_checked = conn.execute(
        "SELECT 1 FROM policy_evaluation WHERE workflow_instance_id=? AND artifact_revision=? LIMIT 1",
        (workflow_instance_id, _DEMO_ARTIFACT_REVISION),
    ).fetchone()
    if already_checked is None:
        outcomes = run_mandatory_policy_checks(conn, workflow_instance_id, _DEMO_ARTIFACT_REVISION)
        if "FAIL" in outcomes.values():
            now = datetime.now(UTC).isoformat()
            conn.execute(
                "UPDATE orchestration_workflow_instance SET status='safe_stopped', updated_at=? WHERE id=?",
                (now, workflow_instance_id),
            )
            conn.commit()
            record_event(
                conn, "system", "policy_check_blocked_workflow", f"workflow:{workflow_instance_id}",
                "safe_stopped", f"mandatory policy FAIL: {outcomes}",
                workflow_instance_id=workflow_instance_id,
            )
            return

    newly_eligible = compute_ready_stages(conn, workflow_instance_id)
    mark_ready(conn, newly_eligible)

    # Also claim any stage already sitting in 'ready' status -- e.g. one a
    # branch decision (evaluate_branch_conditions) set directly to 'ready'
    # in a PRIOR tick, bypassing the pending->ready transition above.
    # compute_ready_stages() only ever looks at 'pending' rows, so without
    # this, an already-ready branch stage would never be picked up.
    already_ready_rows = conn.execute(
        "SELECT id FROM orchestration_workflow_stage WHERE workflow_instance_id=? AND status='ready'",
        (workflow_instance_id,),
    ).fetchall()
    to_claim = {row["id"] for row in already_ready_rows}

    for stage_id in to_claim:
        execution_id = claim_stage(conn, stage_id, worker_id)
        if execution_id is None:
            continue  # another worker/tick already claimed it -- no duplicate work
        stage_row = conn.execute(
            "SELECT name FROM orchestration_workflow_stage WHERE id=?", (stage_id,)
        ).fetchone()
        _execute_stage_safely(conn, stage_id, stage_row["name"])
        complete_stage(conn, execution_id, stage_id)
        evaluate_branch_conditions(conn, workflow_instance_id, stage_id)

    unfinished = conn.execute(
        "SELECT COUNT(*) AS c FROM orchestration_workflow_stage WHERE workflow_instance_id=? "
        "AND status IN ('pending','ready','running','awaiting_reconciliation')",
        (workflow_instance_id,),
    ).fetchone()["c"]
    if unfinished == 0:
        now = datetime.now(UTC).isoformat()
        conn.execute(
            "UPDATE orchestration_workflow_instance SET status='completed', updated_at=? "
            "WHERE id=? AND status='running'",
            (now, workflow_instance_id),
        )
        conn.commit()


def tick(worker_id: str) -> None:
    """One synchronous scheduling pass, real and directly testable without
    asyncio. `scheduler_loop` below is a thin async wrapper around this."""
    conn = get_connection()
    try:
        sweep_stale_leases(conn)
        running = conn.execute(
            "SELECT id FROM orchestration_workflow_instance WHERE status='running'"
        ).fetchall()
        for row in running:
            _drive_workflow(conn, row["id"], worker_id)
    finally:
        conn.close()


async def scheduler_loop() -> None:
    worker_id = f"{_WORKER_PREFIX}-{uuid.uuid4()}"
    logger.info("live scheduler started: worker_id=%s", worker_id)
    try:
        while True:
            tick(worker_id)
            await asyncio.sleep(TICK_INTERVAL_SECONDS)
    except asyncio.CancelledError:
        logger.info("live scheduler stopped: worker_id=%s", worker_id)
        raise


_task: asyncio.Task | None = None


def start() -> None:
    """Clean startup: called from the FastAPI lifespan, after schema init
    and crash recovery have already run."""
    global _task
    _task = asyncio.create_task(scheduler_loop())


async def stop() -> None:
    """Graceful shutdown: called from the FastAPI lifespan before the
    process exits."""
    global _task
    if _task is None:
        return
    _task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await _task
    _task = None
