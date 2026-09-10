"""SQLite connection helper: WAL mode, busy_timeout (ADR-0003, FR-109, FR-110).

DB_PATH is a module attribute (not a constant baked into functions) so tests
can monkeypatch it to point at an isolated tmp_path database per test.
"""
from __future__ import annotations

import os
import sqlite3

DB_PATH = os.environ.get("APP_DB_PATH", "data/app.db")
BUSY_TIMEOUT_MS = 2000


def get_connection() -> sqlite3.Connection:
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    from src.persistence.schema import init_schema as _init_schema

    _init_schema(conn)
