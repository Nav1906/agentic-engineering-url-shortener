"""T024: short-code collision + bounded-retry test (ADR-0004)."""
import pytest

import src.persistence.db as db_module
from src.domain.short_link import ShortCodeGenerationExhausted, create_short_link


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    yield c
    c.close()


def test_collision_retry_is_bounded_and_deterministic(conn):
    # Shrunk alphabet -> tiny code space -> forces collisions quickly.
    tiny_alphabet = "ab"
    seen = set()
    created = 0
    try:
        for _ in range(200):
            link = create_short_link(conn, "https://example.com/x", alphabet=tiny_alphabet)
            assert link.short_code not in seen
            seen.add(link.short_code)
            created += 1
    except ShortCodeGenerationExhausted:
        pass
    # With alphabet size 2 and length 7, the space is 2**7=128; exhaustion
    # must occur deterministically well before 200 unbounded attempts.
    assert created < 200
