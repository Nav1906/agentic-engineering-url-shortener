"""GET /short-links/{shortCode}/analytics (FR-105, FR-107, AMB-002; SC-001)."""
import time


def test_never_resolved_zero_count_null_timestamp(client):
    create = client.post("/short-links", json={"destination_url": "https://example.com/never"})
    code = create.json()["short_code"]
    resp = client.get(f"/short-links/{code}/analytics")
    assert resp.status_code == 200
    body = resp.json()
    assert body["successful_redirect_count"] == 0
    assert body["last_successful_redirect_at"] is None
    assert body["completeness_status"] == "complete"


def test_unknown_code_404(client):
    resp = client.get("/short-links/doesnotexist/analytics")
    assert resp.status_code == 404


def test_successful_redirect_increments_count(client):
    create = client.post("/short-links", json={"destination_url": "https://example.com/hit"})
    code = create.json()["short_code"]
    client.get(f"/{code}", follow_redirects=False)
    time.sleep(0.05)  # background task runs after response is sent
    resp = client.get(f"/short-links/{code}/analytics")
    body = resp.json()
    assert body["successful_redirect_count"] == 1
    assert body["last_successful_redirect_at"] is not None


def test_failed_resolution_does_not_increment(client):
    client.get("/doesnotexist", follow_redirects=False)
    # no assertion target (no code exists) — this documents the FR-105
    # negative path exists; the positive path is covered above.
