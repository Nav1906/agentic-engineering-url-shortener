"""Approval gate endpoints (T065, T067, T069; FR-301,302,307-313).

Role/revision-binding logic here is real and tested. It is fail-closed with
respect to ADR-0006: since no credential-provisioning path is wired (T100/
T101 blocked), no real bearer token will ever resolve to an identity in a
genuine deployment of this code — see src/api/auth.py's module docstring.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Header, HTTPException

from src.api.auth import reject_if_agent, required_role_for_gate, resolve_identity
from src.api.schemas import ApprovalDecision, ApprovalRequest, ErrorResponse
from src.observability.audit import record_event
from src.orchestration.models import get_workflow_instance
from src.persistence.db import get_connection

router = APIRouter()


def _authenticate_and_authorize(conn, workflow_id: str, gate_id: str, bearer_token: str | None):
    identity = resolve_identity(bearer_token)
    if identity is None:
        record_event(
            conn, "system", "approval_attempt_rejected", f"gate:{gate_id}",
            "rejected_unauthenticated", "no verified credential presented (FR-307)",
            workflow_instance_id=workflow_id,
        )
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse(error="unauthenticated", message="no verified credential", requirement_ref="FR-307").model_dump(),
        )
    try:
        reject_if_agent(identity)
    except PermissionError as exc:
        record_event(
            conn, "agent", "approval_attempt_rejected", f"gate:{gate_id}",
            "rejected_agent_identity", str(exc), workflow_instance_id=workflow_id,
        )
        raise HTTPException(
            status_code=403,
            detail=ErrorResponse(error="agent_identity_forbidden", message=str(exc), requirement_ref="FR-309").model_dump(),
        ) from exc

    required_role = required_role_for_gate(gate_id)
    if identity.role != required_role:
        record_event(
            conn, "human", "approval_attempt_rejected", f"gate:{gate_id}",
            "rejected_wrong_role",
            f"identity {identity.identity!r} holds role {identity.role!r}, gate requires {required_role!r} (FR-313)",
            workflow_instance_id=workflow_id,
        )
        raise HTTPException(
            status_code=403,
            detail=ErrorResponse(
                error="wrong_role_for_gate",
                message=f"role {identity.role!r} cannot satisfy a gate requiring {required_role!r}",
                requirement_ref="FR-312/FR-313",
            ).model_dump(),
        )
    return identity


def _current_artifact_revision(conn, workflow_id: str) -> str:
    wf = get_workflow_instance(conn, workflow_id)
    if wf is None:
        raise HTTPException(status_code=404, detail=ErrorResponse(error="not_found", message="unknown workflow").model_dump())
    return "v1"  # single-revision demonstration scope; see FR-311 note in models.py


@router.post("/workflows/{workflow_id}/gates/{gate_id}/approve", response_model=ApprovalDecision)
def approve_gate(
    workflow_id: str,
    gate_id: str,
    body: ApprovalRequest,
    authorization: str | None = Header(default=None),
):
    conn = get_connection()
    try:
        bearer = _extract_bearer(authorization)
        identity = _authenticate_and_authorize(conn, workflow_id, gate_id, bearer)
        revision = _current_artifact_revision(conn, workflow_id)
        decision_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        conn.execute(
            "INSERT INTO orchestration_approval_decision "
            "(id, workflow_instance_id, gate_id, identity, role, decision, rationale, "
            " artifact_revision, created_at, invalidated_at) "
            "VALUES (?,?,?,?,?, 'approved', ?, ?, ?, NULL)",
            (decision_id, workflow_id, gate_id, identity.identity, identity.role, body.rationale, revision, now),
        )
        conn.commit()
        record_event(
            conn, "human", "approve_gate", f"gate:{gate_id}", "approved",
            body.rationale or "approved, no rationale given", workflow_instance_id=workflow_id,
        )
        return ApprovalDecision(
            id=decision_id, gate_id=gate_id, identity=identity.identity, role=identity.role,
            decision="approved", rationale=body.rationale, artifact_revision=revision,
            created_at=now, invalidated_at=None,
        )
    finally:
        conn.close()


@router.post("/workflows/{workflow_id}/gates/{gate_id}/reject", response_model=ApprovalDecision)
def reject_gate(
    workflow_id: str,
    gate_id: str,
    body: ApprovalRequest,
    authorization: str | None = Header(default=None),
):
    conn = get_connection()
    try:
        bearer = _extract_bearer(authorization)
        identity = _authenticate_and_authorize(conn, workflow_id, gate_id, bearer)
        revision = _current_artifact_revision(conn, workflow_id)
        decision_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        conn.execute(
            "INSERT INTO orchestration_approval_decision "
            "(id, workflow_instance_id, gate_id, identity, role, decision, rationale, "
            " artifact_revision, created_at, invalidated_at) "
            "VALUES (?,?,?,?,?, 'rejected', ?, ?, ?, NULL)",
            (decision_id, workflow_id, gate_id, identity.identity, identity.role, body.rationale, revision, now),
        )
        conn.commit()
        record_event(
            conn, "human", "reject_gate", f"gate:{gate_id}", "rejected",
            body.rationale or "rejected, no rationale given", workflow_instance_id=workflow_id,
        )
        return ApprovalDecision(
            id=decision_id, gate_id=gate_id, identity=identity.identity, role=identity.role,
            decision="rejected", rationale=body.rationale, artifact_revision=revision,
            created_at=now, invalidated_at=None,
        )
    finally:
        conn.close()


def _extract_bearer(authorization: str | None) -> str | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    return authorization.split(" ", 1)[1].strip()
