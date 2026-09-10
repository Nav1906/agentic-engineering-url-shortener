"""DELETE /short-links/{shortCode} (FR-116: idempotency record retained)."""


def test_delete_then_404(client):
    create = client.post("/short-links", json={"destination_url": "https://example.com/del"})
    code = create.json()["short_code"]
    resp = client.delete(f"/short-links/{code}")
    assert resp.status_code == 204
    resolve = client.get(f"/{code}", follow_redirects=False)
    assert resolve.status_code == 404


def test_delete_unknown_404(client):
    resp = client.delete("/short-links/doesnotexist")
    assert resp.status_code == 404


def test_delete_retains_idempotency_record(client):
    key = "z" * 20
    body = {"destination_url": "https://example.com/keep-idem"}
    r1 = client.post("/short-links", json=body, headers={"Idempotency-Key": key})
    code = r1.json()["short_code"]
    client.delete(f"/short-links/{code}")
    r2 = client.post("/short-links", json=body, headers={"Idempotency-Key": key})
    assert r2.status_code == 201
    assert r2.json()["short_code"] == code
    assert r2.json()["idempotent_replay"] is True
