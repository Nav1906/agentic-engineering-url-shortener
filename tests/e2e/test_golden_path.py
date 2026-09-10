"""T092 (partial): full golden-path end-to-end sweep via the real HTTP
surface, matching quickstart.md's own golden path. Complements the smoke
script (T009) as a pytest-collected regression check."""


def test_full_golden_path(client):
    create = client.post("/short-links", json={"destination_url": "https://example.com/golden"})
    assert create.status_code == 201
    code = create.json()["short_code"]

    resolve = client.get(f"/{code}", follow_redirects=False)
    assert resolve.status_code == 302

    import time

    time.sleep(0.1)

    analytics = client.get(f"/short-links/{code}/analytics")
    assert analytics.json()["successful_redirect_count"] == 1

    health = client.get("/health")
    assert health.status_code == 200

    delete = client.delete(f"/short-links/{code}")
    assert delete.status_code == 204

    gone = client.get(f"/{code}", follow_redirects=False)
    assert gone.status_code == 404
