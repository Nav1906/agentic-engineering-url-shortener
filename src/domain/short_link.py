"""Short-link domain logic (T011, T023, T024; FR-101-104, ADR-0004)."""
from __future__ import annotations

import secrets
import sqlite3
import string
from dataclasses import dataclass
from datetime import datetime, timezone

from src.domain.validation import validate_destination_url, validate_expires_at

_ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 7
MAX_COLLISION_RETRIES = 5


class ShortCodeGenerationExhausted(RuntimeError):
    """ADR-0004: bounded retry on collision, exhausted without a free code."""


@dataclass
class ShortLink:
    short_code: str
    destination_url: str
    created_at: str
    expires_at: str | None
    status: str
    deleted_at: str | None

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        expires = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) >= expires


def _generate_code(alphabet: str = _ALPHABET, length: int = CODE_LENGTH) -> str:
    return "".join(secrets.choice(alphabet) for _ in range(length))


def create_short_link(
    conn: sqlite3.Connection,
    destination_url: str,
    expires_at: str | None = None,
    alphabet: str = _ALPHABET,
) -> ShortLink:
    """FR-101/102/104/114. Raises ValidationError on invalid input (no link
    created), ShortCodeGenerationExhausted if the bounded collision-retry is
    exhausted (ADR-0004)."""
    validate_destination_url(destination_url)
    validate_expires_at(expires_at)

    created_at = datetime.now(timezone.utc).isoformat()
    for _ in range(MAX_COLLISION_RETRIES):
        code = _generate_code(alphabet=alphabet)
        try:
            conn.execute(
                "INSERT INTO domain_short_link "
                "(short_code, destination_url, created_at, expires_at, status, deleted_at) "
                "VALUES (?, ?, ?, ?, 'active', NULL)",
                (code, destination_url, created_at, expires_at),
            )
            conn.execute(
                "INSERT INTO domain_short_link_analytics_summary (short_code) VALUES (?)",
                (code,),
            )
            conn.commit()
            return ShortLink(code, destination_url, created_at, expires_at, "active", None)
        except sqlite3.IntegrityError:
            continue
    raise ShortCodeGenerationExhausted(
        f"exhausted {MAX_COLLISION_RETRIES} collision retries for a {length_desc(alphabet)}-space code"
    )


def length_desc(alphabet: str) -> str:
    return f"{len(alphabet)}^{CODE_LENGTH}"


def get_short_link(conn: sqlite3.Connection, short_code: str) -> ShortLink | None:
    row = conn.execute(
        "SELECT short_code, destination_url, created_at, expires_at, status, deleted_at "
        "FROM domain_short_link WHERE short_code = ?",
        (short_code,),
    ).fetchone()
    if row is None:
        return None
    return ShortLink(*row)


def delete_short_link(conn: sqlite3.Connection, short_code: str) -> bool:
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        "UPDATE domain_short_link SET status='deleted', deleted_at=? "
        "WHERE short_code=? AND status='active'",
        (now, short_code),
    )
    conn.commit()
    return cur.rowcount > 0
