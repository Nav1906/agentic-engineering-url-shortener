"""POST /workflows, GET /workflows/{id} (FR-201, FR-204, FR-206, FR-503,
FR-601). Workflow creation + inspection as independently usable
capabilities (FR-206)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.api.schemas import ErrorResponse, WorkflowCreateRequest, WorkflowInstance, WorkflowStage
from src.observability.audit import record_event
from src.orchestration.lineage import get_lineage
from src.orchestration.models import (
    create_workflow_instance,
    get_dependencies,
    get_stages,
    get_workflow_instance,
)
from src.persistence.db import get_connection

router = APIRouter()


@router.post("/workflows", response_model=WorkflowInstance, status_code=201)
def create_workflow(body: WorkflowCreateRequest):
    conn = get_connection()
    try:
        scenario = body.scenario or "n/a"
        workflow_id = create_workflow_instance(conn, feature_ref=body.requirement, scenario=scenario)
        record_event(
            conn, "system", "create_workflow", f"workflow:{workflow_id}", "created",
            f"ingested requirement: {body.requirement!r}", workflow_instance_id=workflow_id,
        )
        return _serialize(conn, workflow_id)
    finally:
        conn.close()


@router.get("/workflows/{workflow_id}", response_model=WorkflowInstance)
def get_workflow(workflow_id: str):
    conn = get_connection()
    try:
        wf = get_workflow_instance(conn, workflow_id)
        if wf is None:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(error="not_found", message="unknown workflow").model_dump(),
            )
        return _serialize(conn, workflow_id)
    finally:
        conn.close()


def _serialize(conn, workflow_id: str) -> WorkflowInstance:
    wf = get_workflow_instance(conn, workflow_id)
    assert wf is not None  # caller (create_workflow/get_workflow) already confirmed existence
    stages = []
    for row in get_stages(conn, workflow_id):
        stages.append(
            WorkflowStage(
                id=row["id"], name=row["name"], status=row["status"],
                attempt_count=row["attempt_count"], artifact_revision=row["artifact_revision"],
                depends_on=get_dependencies(conn, row["id"]),
            )
        )
    lineage = get_lineage(conn, workflow_id)
    return WorkflowInstance(
        id=wf["id"], feature_ref=wf["feature_ref"], scenario=wf["scenario"], status=wf["status"],
        stages=stages, decision_lineage=lineage,
    )
