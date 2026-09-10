"""Pydantic models generated from contracts/openapi.yaml (T015)."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error: str
    message: str
    requirement_ref: str | None = None


class ShortLinkCreateRequest(BaseModel):
    destination_url: str
    expires_at: str | None = None


class ShortLinkCreateResponse(BaseModel):
    short_code: str
    destination_url: str
    created_at: str
    expires_at: str | None = None
    idempotent_replay: bool = False


class ShortLinkAnalyticsSummary(BaseModel):
    short_code: str
    successful_redirect_count: int = Field(ge=0)
    last_successful_redirect_at: str | None = None
    completeness_status: Literal["complete", "degraded", "incomplete"]


class AnalyticsHealth(BaseModel):
    status: Literal["healthy", "degraded"]
    degraded_since_unclean_shutdown_at: str | None = None


class HealthStatus(BaseModel):
    status: Literal["healthy", "degraded", "unavailable"]
    analytics: AnalyticsHealth


class WorkflowCreateRequest(BaseModel):
    requirement: str
    scenario: Literal["greenfield", "brownfield", "ambiguous"] | None = None


class WorkflowStage(BaseModel):
    id: str
    name: str
    status: str
    attempt_count: int = 0
    artifact_revision: str
    depends_on: list[str] = Field(default_factory=list)


class DecisionLineageEntry(BaseModel):
    decision_type: str
    detail: dict[str, Any]
    created_at: str


class WorkflowInstance(BaseModel):
    id: str
    feature_ref: str | None = None
    scenario: str
    status: str
    stages: list[WorkflowStage] = Field(default_factory=list)
    decision_lineage: list[DecisionLineageEntry] = Field(default_factory=list)


class ApprovalRequest(BaseModel):
    rationale: str | None = None


class ApprovalDecision(BaseModel):
    id: str
    gate_id: str
    identity: str
    role: Literal["reviewer_approver", "release_owner"]
    decision: Literal["approved", "rejected", "escalated_timeout"]
    rationale: str | None = None
    artifact_revision: str
    created_at: str
    invalidated_at: str | None = None


class PolicyEvaluationOut(BaseModel):
    policy_id: str
    policy_version: str
    outcome: Literal["PASS", "FAIL", "EXCEPTION-REQUESTED", "NOT-APPLICABLE"]
    evaluated_at: str


class AuditEventOut(BaseModel):
    actor_type: Literal["human", "agent", "system"]
    action: str
    timestamp: str
    affected_artifact_or_state: str
    result: str
    reason: str
    demonstration_flag: bool = True


class ReliabilityMetrics(BaseModel):
    demonstration_data: bool = True
    success_rate: float
    failure_rate: float
    retry_frequency: float
    rollback_or_compensation_frequency: float = 0.0
    mttr_seconds: float | None = None
    unrecovered_failure_count: int
