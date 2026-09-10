"""Contract tests for GET /health (FR-111, FR-115, FR-117)."""
from fastapi.testclient import TestClient


def test_health_returns_200_with_status_field(tmp_path, monkeypatch):
    import src.persistence.db as db_module

    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    from src.api.main import app

    with TestClient(app) as client:  # triggers lifespan startup (schema init)
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] in ("healthy", "degraded", "unavailable")


def test_analytics_degradation(tmp_path, monkeypatch):
    """FR-115/FR-117: analytics degradation observable via /health independent
    of any specific short code."""
    import src.persistence.db as db_module

    db_path = tmp_path / "app.db"
    monkeypatch.setattr(db_module, "DB_PATH", str(db_path))
    from src.api.main import app

    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert "analytics" in body
        assert "degraded_since_unclean_shutdown_at" in body["analytics"]
