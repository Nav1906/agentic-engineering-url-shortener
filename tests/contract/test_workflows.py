"""POST /workflows, GET /workflows/{id} (FR-201, FR-204, FR-206, FR-601)."""


def test_create_workflow_returns_correlation_id(client):
    resp = client.post("/workflows", json={"requirement": "add feature X"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"]
    assert body["status"] == "running"
    assert body["stages"] == []
    assert body["decision_lineage"] == []


def test_get_unknown_workflow_404(client):
    resp = client.get("/workflows/does-not-exist")
    assert resp.status_code == 404


def test_get_workflow_returns_persisted_state(client):
    create = client.post("/workflows", json={"requirement": "req", "scenario": "greenfield"})
    wf_id = create.json()["id"]
    resp = client.get(f"/workflows/{wf_id}")
    assert resp.status_code == 200
    assert resp.json()["scenario"] == "greenfield"
