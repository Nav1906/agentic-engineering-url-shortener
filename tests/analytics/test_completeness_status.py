"""T036: three-state completeness_status, incomplete is sticky/one-way."""
import pytest

import src.persistence.db as db_module
from src.domain.analytics import get_summary, mark_incomplete
from src.domain.short_link import create_short_link


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    yield c
    c.close()


def test_default_is_complete(conn):
    link = create_short_link(conn, "https://example.com/x")
    assert get_summary(conn, link.short_code)["completeness_status"] == "complete"


def test_mark_incomplete_transitions(conn):
    link = create_short_link(conn, "https://example.com/x")
    mark_incomplete(conn, link.short_code)
    assert get_summary(conn, link.short_code)["completeness_status"] == "incomplete"


def test_incomplete_never_auto_reverts(conn):
    link = create_short_link(conn, "https://example.com/x")
    mark_incomplete(conn, link.short_code)
    # Any subsequent read must still show incomplete — nothing in this
    # module ever transitions incomplete -> complete/degraded.
    assert get_summary(conn, link.short_code)["completeness_status"] == "incomplete"
    assert get_summary(conn, link.short_code)["completeness_status"] == "incomplete"
