"""T027, T033: Idempotency-Key request-level idempotency (FR-108,112,113)."""
from datetime import UTC, datetime, timedelta

KEY = "a" * 20


def test_no_key_always_creates_new(client):
    r1 = client.post("/short-links", json={"destination_url": "https://example.com/dup"})
    r2 = client.post("/short-links", json={"destination_url": "https://example.com/dup"})
    assert r1.json()["short_code"] != r2.json()["short_code"]


def test_same_key_same_payload_returns_original(client):
    body = {"destination_url": "https://example.com/idem"}
    r1 = client.post("/short-links", json=body, headers={"Idempotency-Key": KEY})
    r2 = client.post("/short-links", json=body, headers={"Idempotency-Key": KEY})
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["short_code"] == r2.json()["short_code"]
    assert r2.json()["idempotent_replay"] is True


def test_same_key_different_payload_conflicts(client):
    r1 = client.post(
        "/short-links", json={"destination_url": "https://example.com/a"}, headers={"Idempotency-Key": KEY}
    )
    assert r1.status_code == 201
    r2 = client.post(
        "/short-links", json={"destination_url": "https://example.com/b"}, headers={"Idempotency-Key": KEY}
    )
    assert r2.status_code == 409


def test_key_too_short_rejected(client):
    resp = client.post(
        "/short-links", json={"destination_url": "https://example.com/x"}, headers={"Idempotency-Key": "short"}
    )
    assert resp.status_code == 400


def test_replay_after_expiry(client):
    """Human Gate 3 review correction: replay after expiry returns the
    original creation result; does not re-validate expiresAt, does not
    reactivate the link."""
    near_future = (datetime.now(UTC) + timedelta(seconds=1)).isoformat()
    body = {"destination_url": "https://example.com/expiring", "expires_at": near_future}
    r1 = client.post("/short-links", json=body, headers={"Idempotency-Key": KEY})
    assert r1.status_code == 201
    code = r1.json()["short_code"]

    import time

    time.sleep(1.2)

    r2 = client.post("/short-links", json=body, headers={"Idempotency-Key": KEY})
    assert r2.status_code == 201
    assert r2.json()["short_code"] == code
    assert r2.json()["idempotent_replay"] is True

    # Resolution still independently reflects the current (now-expired) state.
    resolve = client.get(f"/{code}", follow_redirects=False)
    assert resolve.status_code == 410
