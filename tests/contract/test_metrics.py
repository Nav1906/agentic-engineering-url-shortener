"""GET /metrics/reliability (FR-603, FR-604) -- the one endpoint T088's
sweep found missing a dedicated contract test."""


def test_metrics_always_demonstration_data(client):
    resp = client.get("/metrics/reliability")
    assert resp.status_code == 200
    body = resp.json()
    assert body["demonstration_data"] is True
    assert "success_rate" in body
    assert "failure_rate" in body
    assert "unrecovered_failure_count" in body


def test_metrics_mttr_null_when_no_recovered_events(client):
    resp = client.get("/metrics/reliability")
    assert resp.json()["mttr_seconds"] is None
