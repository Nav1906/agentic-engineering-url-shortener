"""T031: expiresAt future-validation at creation (FR-114)."""
from datetime import UTC, datetime, timedelta


def test_future_validation(client):
    past = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    resp = client.post("/short-links", json={"destination_url": "https://example.com/x", "expires_at": past})
    assert resp.status_code == 400


def test_future_expires_at_accepted(client):
    future = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    resp = client.post("/short-links", json={"destination_url": "https://example.com/x", "expires_at": future})
    assert resp.status_code == 201
    assert resp.json()["expires_at"] is not None


def test_no_expires_at_means_no_default_expiration(client):
    resp = client.post("/short-links", json={"destination_url": "https://example.com/no-exp"})
    assert resp.status_code == 201
    assert resp.json()["expires_at"] is None
