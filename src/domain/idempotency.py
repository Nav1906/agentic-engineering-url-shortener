"""Request-level idempotency (T012, T027, T041; FR-108, FR-112, FR-113, FR-116).

AMB-001's full resolution: without a key, always mint a new code. With a key
and identical payload, return the original. With the same key and a
different payload, reject (409). Records retained indefinitely (FR-116).
"""
from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timezone

MIN_KEY_LENGTH = 16  # plan.md §8: caller's responsibility beyond this floor


class IdempotencyKeyTooShort(ValueError):
    pass


class IdempotencyConflict(ValueError):
    """FR-113: same key, different payload -> 409 Conflict."""


def _hash_payload(destination_url: str, expires_at: str | None) -> str:
    raw = f"{destination_url}|{expires_at or ''}"
    return hashlib.sha256(raw.encode()).hexdigest()


def validate_key_length(idempotency_key: str) -> None:
    if len(idempotency_key) < MIN_KEY_LENGTH:
        raise IdempotencyKeyTooShort(
            f"Idempotency-Key must be at least {MIN_KEY_LENGTH} characters"
        )


def find_existing(
    conn: sqlite3.Connection, idempotency_key: str
) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT idempotency_key, validated_payload_hash, short_code, created_at "
        "FROM domain_idempotency_record WHERE idempotency_key = ?",
        (idempotency_key,),
    ).fetchone()


def check_replay(
    conn: sqlite3.Connection,
    idempotency_key: str,
    destination_url: str,
    expires_at: str | None,
) -> str | None:
    """Returns the original short_code if this is a matching replay.
    Raises IdempotencyConflict if the key exists with a different payload.
    Returns None if the key has never been seen (caller should proceed to
    create a new short link and then call record())."""
    existing = find_existing(conn, idempotency_key)
    if existing is None:
        return None
    incoming_hash = _hash_payload(destination_url, expires_at)
    if existing["validated_payload_hash"] == incoming_hash:
        return existing["short_code"]
    raise IdempotencyConflict(
        f"Idempotency-Key {idempotency_key!r} already used with a different payload"
    )


def record(
    conn: sqlite3.Connection,
    idempotency_key: str,
    destination_url: str,
    expires_at: str | None,
    short_code: str,
) -> None:
    payload_hash = _hash_payload(destination_url, expires_at)
    created_at = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO domain_idempotency_record "
        "(idempotency_key, validated_payload_hash, short_code, created_at) "
        "VALUES (?, ?, ?, ?)",
        (idempotency_key, payload_hash, short_code, created_at),
    )
    conn.commit()
