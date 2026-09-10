"""Analytics: post-response outbox write, drain worker, completeness status.

T034-T036; FR-105, FR-106, FR-107, ADR-0009 Rev. 3. The write happens AFTER
the HTTP response is sent (never before) — this ordering is the corrected
fix for the overcount defect Human Gate 4 caught; it must never move back to
before-send.
"""
from __future__ import annotations

import sqlite3
import uuid
from datetime import UTC, datetime


def enqueue_redirect_event(conn: sqlite3.Connection, short_code: str) -> str:
    """Called strictly AFTER the redirect response has been sent (e.g. via
    FastAPI BackgroundTasks). Returns the event_id."""
    event_id = str(uuid.uuid4())
    redirected_at = datetime.now(UTC).isoformat()
    conn.execute(
        "INSERT INTO domain_analytics_outbox (event_id, short_code, redirected_at, drain_status) "
        "VALUES (?, ?, ?, 'pending')",
        (event_id, short_code, redirected_at),
    )
    conn.commit()
    return event_id


def drain_outbox(conn: sqlite3.Connection) -> int:
    """T035: idempotent by event_id via a check-and-insert against
    applied_events in the same transaction as the summary-count increment —
    a crash mid-batch cannot double-count. Returns count of events applied."""
    pending = conn.execute(
        "SELECT event_id, short_code FROM domain_analytics_outbox WHERE drain_status = 'pending'"
    ).fetchall()
    applied = 0
    for row in pending:
        event_id, short_code = row["event_id"], row["short_code"]
        already = conn.execute(
            "SELECT 1 FROM applied_events WHERE event_id = ?", (event_id,)
        ).fetchone()
        if already is not None:
            conn.execute(
                "UPDATE domain_analytics_outbox SET drain_status='applied' WHERE event_id=?",
                (event_id,),
            )
            conn.commit()
            continue
        now = datetime.now(UTC).isoformat()
        conn.execute("INSERT INTO applied_events (event_id, applied_at) VALUES (?, ?)", (event_id, now))
        conn.execute(
            "UPDATE domain_short_link_analytics_summary "
            "SET successful_redirect_count = successful_redirect_count + 1, "
            "    last_successful_redirect_at = ? "
            "WHERE short_code = ?",
            (now, short_code),
        )
        conn.execute(
            "UPDATE domain_analytics_outbox SET drain_status='applied' WHERE event_id=?",
            (event_id,),
        )
        conn.commit()
        applied += 1
    return applied


def mark_incomplete(conn: sqlite3.Connection, short_code: str) -> None:
    """T036: one-way transition, set when the post-send outbox write itself
    observably fails after exhausting ADR-0007's bounded retries."""
    conn.execute(
        "UPDATE domain_short_link_analytics_summary SET completeness_status='incomplete' "
        "WHERE short_code = ?",
        (short_code,),
    )
    conn.commit()


def get_summary(conn: sqlite3.Connection, short_code: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT short_code, successful_redirect_count, last_successful_redirect_at, completeness_status "
        "FROM domain_short_link_analytics_summary WHERE short_code = ?",
        (short_code,),
    ).fetchone()


def effective_completeness_status(conn: sqlite3.Connection, short_code: str) -> str:
    """FR-117: `complete` MUST NOT be reported while the system-wide
    degraded_since_unclean_shutdown_at flag is set, regardless of this row's
    own backlog state."""
    row = get_summary(conn, short_code)
    if row is None:
        return "complete"
    status_row = conn.execute(
        "SELECT degraded_since_unclean_shutdown_at FROM analytics_system_status WHERE id=1"
    ).fetchone()
    if (
        status_row is not None
        and status_row["degraded_since_unclean_shutdown_at"] is not None
        and row["completeness_status"] == "complete"
    ):
        return "degraded"
    return row["completeness_status"]
