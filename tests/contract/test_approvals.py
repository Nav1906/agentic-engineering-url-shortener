"""T065, T067, T069: role-checked approval endpoints (FR-307,309,310,312,313).

Uses auth.register_test_credential — TEST-ONLY, never called by application
code — to exercise the role/revision-binding logic independently of the
still-unresolved ADR-0006 credential-provisioning question. A real
deployment has NO registered credentials (T100/T101 blocked), so every real
approval attempt is rejected regardless of what this test proves about the
logic itself.
"""
import pytest

from src.api.auth import Identity, clear_test_credentials, register_test_credential


@pytest.fixture(autouse=True)
def _clean_credentials():
    clear_test_credentials()
    yield
    clear_test_credentials()


def _create_workflow(client) -> str:
    resp = client.post("/workflows", json={"requirement": "test requirement"})
    return resp.json()["id"]


def test_unauthenticated_rejected(client):
    wf_id = _create_workflow(client)
    resp = client.post(f"/workflows/{wf_id}/gates/requirements_approval/approve", json={})
    assert resp.status_code == 401
    assert resp.json()["detail"]["error"] == "unauthenticated"


def test_agent_identity_rejected_unconditionally(client):
    wf_id = _create_workflow(client)
    register_test_credential("agenttoken", Identity("agent-1", "reviewer_approver", is_agent=True))
    resp = client.post(
        f"/workflows/{wf_id}/gates/requirements_approval/approve",
        json={},
        headers={"Authorization": "Bearer agenttoken"},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"]["error"] == "agent_identity_forbidden"


def test_reviewer_approver_can_approve_requirements_gate(client):
    wf_id = _create_workflow(client)
    register_test_credential("revtoken", Identity("alice", "reviewer_approver"))
    resp = client.post(
        f"/workflows/{wf_id}/gates/requirements_approval/approve",
        json={"rationale": "looks good"},
        headers={"Authorization": "Bearer revtoken"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision"] == "approved"
    assert body["role"] == "reviewer_approver"
    # FR-310: all mandatory fields present
    for field in ("id", "gate_id", "identity", "role", "decision", "artifact_revision", "created_at"):
        assert body.get(field) is not None or field == "rationale"


def test_fr313_reviewer_approver_rejected_at_release_readiness(client):
    """FR-313: a valid role used at the WRONG gate is rejected — distinct
    from having no valid role at all."""
    wf_id = _create_workflow(client)
    register_test_credential("revtoken", Identity("alice", "reviewer_approver"))
    resp = client.post(
        f"/workflows/{wf_id}/gates/release_readiness/approve",
        json={},
        headers={"Authorization": "Bearer revtoken"},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"]["error"] == "wrong_role_for_gate"


def test_fr313_release_owner_rejected_at_requirements_approval(client):
    wf_id = _create_workflow(client)
    register_test_credential("reltoken", Identity("bob", "release_owner"))
    resp = client.post(
        f"/workflows/{wf_id}/gates/requirements_approval/approve",
        json={},
        headers={"Authorization": "Bearer reltoken"},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"]["error"] == "wrong_role_for_gate"


def test_release_owner_can_approve_release_readiness(client):
    wf_id = _create_workflow(client)
    register_test_credential("reltoken", Identity("bob", "release_owner"))
    resp = client.post(
        f"/workflows/{wf_id}/gates/release_readiness/approve",
        json={},
        headers={"Authorization": "Bearer reltoken"},
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "release_owner"


def test_reject_gate_records_rejection(client):
    wf_id = _create_workflow(client)
    register_test_credential("revtoken", Identity("alice", "reviewer_approver"))
    resp = client.post(
        f"/workflows/{wf_id}/gates/architecture_approval/reject",
        json={"rationale": "not ready"},
        headers={"Authorization": "Bearer revtoken"},
    )
    assert resp.status_code == 200
    assert resp.json()["decision"] == "rejected"


def test_no_real_credentials_registered_by_default(client):
    """Confirms the fail-closed posture: without test-only registration
    (which application code never calls), literally any token is rejected."""
    wf_id = _create_workflow(client)
    resp = client.post(
        f"/workflows/{wf_id}/gates/requirements_approval/approve",
        json={},
        headers={"Authorization": "Bearer whatever-token-someone-guesses"},
    )
    assert resp.status_code == 401
