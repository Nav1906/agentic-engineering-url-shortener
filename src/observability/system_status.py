"""Unclean-shutdown detection, sticky degradation flag, operator ack (T037,
T038; FR-117). Same SQLite database as everything else (ADR-0009) so there
is no second store that could fail independently of what it tracks.
"""
from __future__ import annotations

import sqlite3
from datetime import UTC, datetime


def ensure_status_row(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO analytics_system_status (id, state, started_at, clean_shutdown_at, "
        "degraded_since_unclean_shutdown_at) VALUES (1, 'stopped_clean', ?, ?, NULL)",
        (datetime.now(UTC).isoformat(), datetime.now(UTC).isoformat()),
    )
    conn.commit()


def on_startup(conn: sqlite3.Connection) -> bool:
    """Returns True if an unclean prior shutdown was just detected. Sets the
    sticky degraded_since_unclean_shutdown_at flag (only if not already set)
    when the persisted state was 'running' at the moment this process
    started — i.e. the prior process never reached a clean shutdown."""
    ensure_status_row(conn)
    row = conn.execute(
        "SELECT state, degraded_since_unclean_shutdown_at FROM analytics_system_status WHERE id=1"
    ).fetchone()
    now = datetime.now(UTC).isoformat()
    detected_unclean = row["state"] == "running"
    if detected_unclean and row["degraded_since_unclean_shutdown_at"] is None:
        conn.execute(
            "UPDATE analytics_system_status SET degraded_since_unclean_shutdown_at = ? WHERE id=1",
            (now,),
        )
    conn.execute(
        "UPDATE analytics_system_status SET state='running', started_at=?, clean_shutdown_at=NULL WHERE id=1",
        (now,),
    )
    conn.commit()
    return detected_unclean


def on_clean_shutdown(conn: sqlite3.Connection) -> None:
    now = datetime.now(UTC).isoformat()
    conn.execute(
        "UPDATE analytics_system_status SET state='stopped_clean', clean_shutdown_at=? WHERE id=1",
        (now,),
    )
    conn.commit()


def acknowledge(conn: sqlite3.Connection) -> None:
    """FR-117: clears ONLY the forward-looking warning. MUST NOT touch any
    per-code completeness_status row already 'incomplete' — those remain
    incomplete forever, by design."""
    conn.execute(
        "UPDATE analytics_system_status SET degraded_since_unclean_shutdown_at = NULL WHERE id=1"
    )
    conn.commit()


def get_status(conn: sqlite3.Connection) -> sqlite3.Row:
    ensure_status_row(conn)
    return conn.execute("SELECT * FROM analytics_system_status WHERE id=1").fetchone()
