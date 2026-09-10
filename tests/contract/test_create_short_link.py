"""T022, T025: POST /short-links (FR-101, FR-102)."""


def test_valid_url(client):
    resp = client.post("/short-links", json={"destination_url": "https://example.com/path"})
    assert resp.status_code == 201
    body = resp.json()
    assert len(body["short_code"]) > 0
    assert body["destination_url"] == "https://example.com/path"
    assert body["idempotent_replay"] is False


def test_invalid_scheme(client):
    resp = client.post("/short-links", json={"destination_url": "javascript:alert(1)"})
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"] == "validation_error"


def test_malformed_url_creates_nothing(client):
    resp = client.post("/short-links", json={"destination_url": "not a url"})
    assert resp.status_code == 400
