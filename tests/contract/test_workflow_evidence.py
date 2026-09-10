"""GET /workflows/{id}/audit-events, GET /workflows/{id}/policy-evaluations
(FR-601, FR-602, FR-303). Greenfield scenario demonstration requirement."""


def test_audit_events_empty_for_fresh_workflow(client):
    wf = client.post("/workflows", json={"requirement": "req"}).json()["id"]
    resp = client.get(f"/workflows/{wf}/audit-events")
    assert resp.status_code == 200
    events = resp.json()
    # create_workflow itself records one audit event
    assert len(events) >= 1
    assert events[0]["action"] == "create_workflow"


def test_policy_evaluations_empty_for_fresh_workflow(client):
    wf = client.post("/workflows", json={"requirement": "req"}).json()["id"]
    resp = client.get(f"/workflows/{wf}/policy-evaluations")
    assert resp.status_code == 200
    assert resp.json() == []
