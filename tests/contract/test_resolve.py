"""T028, T030: GET /{shortCode} (FR-103)."""
import time
from datetime import UTC


def test_valid(client):
    create = client.post("/short-links", json={"destination_url": "https://example.com/resolve-me"})
    code = create.json()["short_code"]
    resp = client.get(f"/{code}", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"] == "https://example.com/resolve-me"


def test_unknown(client):
    resp = client.get("/doesnotexist", follow_redirects=False)
    assert resp.status_code == 404


def test_expired(client):
    from datetime import datetime, timedelta

    near_future = (datetime.now(UTC) + timedelta(seconds=1)).isoformat()
    create = client.post(
        "/short-links", json={"destination_url": "https://example.com/exp", "expires_at": near_future}
    )
    code = create.json()["short_code"]
    time.sleep(1.2)
    resp = client.get(f"/{code}", follow_redirects=False)
    assert resp.status_code == 410
    assert resp.json()["detail"]["error"] == "gone"
