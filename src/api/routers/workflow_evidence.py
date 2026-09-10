"""GET /workflows/{id}/audit-events, GET /workflows/{id}/policy-evaluations
(FR-601, FR-602, FR-303). Both already specified in contracts/openapi.yaml;
implemented here as real endpoints, not simulated."""
from __future__ import annotations

from fastapi import APIRouter

from src.api.schemas import AuditEventOut, PolicyEvaluationOut
from src.observability.audit import get_events_for_workflow
from src.persistence.db import get_connection

router = APIRouter()


@router.get("/workflows/{workflow_id}/audit-events", response_model=list[AuditEventOut])
def get_workflow_audit_events(workflow_id: str):
    conn = get_connection()
    try:
        events = get_events_for_workflow(conn, workflow_id)
        return [
            AuditEventOut(
                actor_type=e["actor_type"], action=e["action"], timestamp=e["timestamp"],
                affected_artifact_or_state=e["affected_artifact_or_state"], result=e["result"],
                reason=e["reason"], demonstration_flag=bool(e["demonstration_flag"]),
            )
            for e in events
        ]
    finally:
        conn.close()


@router.get("/workflows/{workflow_id}/policy-evaluations", response_model=list[PolicyEvaluationOut])
def get_workflow_policy_evaluations(workflow_id: str):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT policy_id, policy_version, outcome, evaluated_at FROM policy_evaluation "
            "WHERE workflow_instance_id = ? ORDER BY id",
            (workflow_id,),
        ).fetchall()
        return [
            PolicyEvaluationOut(
                policy_id=r["policy_id"], policy_version=r["policy_version"],
                outcome=r["outcome"], evaluated_at=r["evaluated_at"],
            )
            for r in rows
        ]
    finally:
        conn.close()
