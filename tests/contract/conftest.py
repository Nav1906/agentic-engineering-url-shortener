import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    import src.persistence.db as db_module

    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    from src.api.main import app

    with TestClient(app) as c:
        yield c
