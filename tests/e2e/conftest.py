import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    import src.persistence.db as db_module
    from src.api.middleware.rate_limit import reset_all

    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    reset_all()
    from src.api.main import app

    with TestClient(app) as c:
        yield c
