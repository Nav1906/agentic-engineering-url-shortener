"""MTTR and reliability metrics (T040, T082; FR-603, FR-604, ADR-0008).

MTTR population: recovered events only (an audit_events row whose
recovery_of_event_id points at the failure it resolves). Unrecovered
failures are counted and reported separately, never blended into the MTTR
figure — per ADR-0008's explicit definition and the guide's MTTR rule.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime


def compute_mttr_seconds(conn: sqlite3.Connection) -> tuple[float | None, int]:
    """Returns (mttr_seconds_or_None, unrecovered_failure_count)."""
    failures = conn.execute(
        "SELECT id, timestamp FROM audit_events WHERE result IN ('failed', 'failed_transient', 'failed_permanent')"
    ).fetchall()
    recoveries = conn.execute(
        "SELECT id, timestamp, recovery_of_event_id FROM audit_events WHERE recovery_of_event_id IS NOT NULL"
    ).fetchall()
    recovery_by_failure = {r["recovery_of_event_id"]: r for r in recoveries}

    durations: list[float] = []
    unrecovered = 0
    for f in failures:
        rec = recovery_by_failure.get(f["id"])
        if rec is None:
            unrecovered += 1
            continue
        t0 = datetime.fromisoformat(f["timestamp"])
        t1 = datetime.fromisoformat(rec["timestamp"])
        durations.append((t1 - t0).total_seconds())

    if not durations:
        return None, unrecovered
    return sum(durations) / len(durations), unrecovered


def compute_reliability_metrics(conn: sqlite3.Connection) -> dict:
    total_instances = conn.execute(
        "SELECT COUNT(*) FROM orchestration_workflow_instance"
    ).fetchone()[0]
    completed = conn.execute(
        "SELECT COUNT(*) FROM orchestration_workflow_instance WHERE status='completed'"
    ).fetchone()[0]
    failed = conn.execute(
        "SELECT COUNT(*) FROM orchestration_workflow_instance WHERE status IN ('rejected', 'safe_stopped')"
    ).fetchone()[0]
    retries = conn.execute(
        "SELECT COALESCE(SUM(attempt_count), 0) FROM orchestration_workflow_stage"
    ).fetchone()[0]
    stage_count = conn.execute("SELECT COUNT(*) FROM orchestration_workflow_stage").fetchone()[0]

    mttr, unrecovered = compute_mttr_seconds(conn)

    success_rate = (completed / total_instances) if total_instances else 0.0
    failure_rate = (failed / total_instances) if total_instances else 0.0
    retry_frequency = (retries / stage_count) if stage_count else 0.0

    return {
        "demonstration_data": True,
        "success_rate": success_rate,
        "failure_rate": failure_rate,
        "retry_frequency": retry_frequency,
        "rollback_or_compensation_frequency": 0.0,
        "mttr_seconds": mttr,
        "unrecovered_failure_count": unrecovered,
    }
