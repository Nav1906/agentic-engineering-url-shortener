"""SQLite schema for the governed URL shortener (data-model.md is authoritative).

Every CREATE TABLE below traces to a table defined in
specs/001-governed-url-shortener/data-model.md. No ORM is used (ADR-0002/0003).
"""
from __future__ import annotations

import sqlite3

DDL = """
-- Domain package (domain_*, ADR-0001) -------------------------------------

CREATE TABLE IF NOT EXISTS domain_short_link (
    short_code TEXT PRIMARY KEY,
    destination_url TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT,
    status TEXT NOT NULL CHECK (status IN ('active', 'deleted')),
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS domain_idempotency_record (
    idempotency_key TEXT PRIMARY KEY,
    validated_payload_hash TEXT NOT NULL,
    short_code TEXT NOT NULL REFERENCES domain_short_link(short_code),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS domain_analytics_outbox (
    event_id TEXT PRIMARY KEY,
    short_code TEXT NOT NULL REFERENCES domain_short_link(short_code),
    redirected_at TEXT NOT NULL,
    drain_status TEXT NOT NULL CHECK (drain_status IN ('pending', 'applied'))
);

CREATE TABLE IF NOT EXISTS applied_events (
    event_id TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics_system_status (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    state TEXT NOT NULL CHECK (state IN ('running', 'stopped_clean')),
    started_at TEXT NOT NULL,
    clean_shutdown_at TEXT,
    degraded_since_unclean_shutdown_at TEXT
);

CREATE TABLE IF NOT EXISTS domain_short_link_analytics_summary (
    short_code TEXT PRIMARY KEY REFERENCES domain_short_link(short_code),
    successful_redirect_count INTEGER NOT NULL DEFAULT 0,
    last_successful_redirect_at TEXT,
    completeness_status TEXT NOT NULL DEFAULT 'complete'
        CHECK (completeness_status IN ('complete', 'degraded', 'incomplete'))
);

-- Orchestration package (orchestration_*, ADR-0005) ------------------------

CREATE TABLE IF NOT EXISTS orchestration_workflow_instance (
    id TEXT PRIMARY KEY,
    feature_ref TEXT NOT NULL,
    scenario TEXT NOT NULL CHECK (scenario IN ('greenfield', 'brownfield', 'ambiguous', 'n/a')),
    status TEXT NOT NULL CHECK (
        status IN ('running', 'awaiting_approval', 'safe_stopped', 'completed', 'rejected')
    ),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orchestration_workflow_stage (
    id TEXT PRIMARY KEY,
    workflow_instance_id TEXT NOT NULL REFERENCES orchestration_workflow_instance(id),
    name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN (
            'pending', 'ready', 'running', 'succeeded', 'failed_transient',
            'failed_permanent', 'awaiting_approval', 'awaiting_reconciliation',
            'rejected', 'skipped'
        )
    ),
    attempt_count INTEGER NOT NULL DEFAULT 0,
    effect_class TEXT NOT NULL CHECK (effect_class IN ('idempotent', 'externally_observable_uncertain')),
    artifact_revision TEXT NOT NULL,
    preconditions TEXT,
    postconditions TEXT,
    timeout_seconds INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orchestration_stage_execution (
    id TEXT PRIMARY KEY,
    stage_id TEXT NOT NULL REFERENCES orchestration_workflow_stage(id),
    attempt_number INTEGER NOT NULL,
    claimed_by_worker_id TEXT NOT NULL,
    claimed_at TEXT NOT NULL,
    lease_expires_at TEXT NOT NULL,
    workspace_path TEXT,
    status TEXT NOT NULL CHECK (status IN ('claimed', 'running', 'completed', 'failed', 'abandoned')),
    outcome_detail TEXT
);

CREATE TABLE IF NOT EXISTS orchestration_stage_dependency (
    workflow_instance_id TEXT NOT NULL,
    stage_id TEXT NOT NULL REFERENCES orchestration_workflow_stage(id),
    depends_on_stage_id TEXT NOT NULL REFERENCES orchestration_workflow_stage(id),
    PRIMARY KEY (stage_id, depends_on_stage_id)
);

CREATE TABLE IF NOT EXISTS orchestration_decision_lineage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_instance_id TEXT NOT NULL REFERENCES orchestration_workflow_instance(id),
    decision_type TEXT NOT NULL,
    detail TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orchestration_approval_decision (
    id TEXT PRIMARY KEY,
    workflow_instance_id TEXT NOT NULL REFERENCES orchestration_workflow_instance(id),
    gate_id TEXT NOT NULL,
    identity TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('reviewer_approver', 'release_owner')),
    decision TEXT NOT NULL CHECK (decision IN ('approved', 'rejected', 'escalated_timeout')),
    rationale TEXT,
    artifact_revision TEXT NOT NULL,
    created_at TEXT NOT NULL,
    invalidated_at TEXT
);

-- Policy package (policy_*) -------------------------------------------------

CREATE TABLE IF NOT EXISTS policy_evaluation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_instance_id TEXT REFERENCES orchestration_workflow_instance(id),
    policy_id TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('PASS', 'FAIL', 'EXCEPTION-REQUESTED', 'NOT-APPLICABLE')),
    evaluated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS policy_exception (
    id TEXT PRIMARY KEY,
    policy_evaluation_id INTEGER NOT NULL REFERENCES policy_evaluation(id),
    reason TEXT NOT NULL,
    scope TEXT NOT NULL,
    approving_identity TEXT NOT NULL,
    compensating_control TEXT NOT NULL,
    approved_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

-- Audit package ---------------------------------------------------------

CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_instance_id TEXT,
    actor_type TEXT NOT NULL CHECK (actor_type IN ('human', 'agent', 'system')),
    action TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    affected_artifact_or_state TEXT NOT NULL,
    result TEXT NOT NULL,
    reason TEXT NOT NULL,
    recovery_of_event_id INTEGER REFERENCES audit_events(id),
    demonstration_flag INTEGER NOT NULL DEFAULT 1,
    detail TEXT
);
"""


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(DDL)
    conn.commit()
