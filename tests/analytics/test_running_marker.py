"""T038: marker-write failure MUST prevent request-serving, not just log."""
import sqlite3

import pytest
from fastapi.testclient import TestClient


def test_startup_marker_write_failure_prevents_serving(tmp_path, monkeypatch):
    import src.persistence.db as db_module

    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))

    from src.observability import system_status as status_module

    def _broken_on_startup(conn):
        raise sqlite3.OperationalError("simulated marker-write failure")

    monkeypatch.setattr(status_module, "on_startup", _broken_on_startup)

    from src.api.main import app

    with pytest.raises(sqlite3.OperationalError), TestClient(app):
        pytest.fail("request-serving must not begin if the startup marker write fails")
