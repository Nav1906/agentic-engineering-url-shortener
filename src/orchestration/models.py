"""Orchestration domain models: workflow instance/stage/dependency (T045).

FR-201: this table IS the explicit dependency graph — not implicit control
flow. FR-203: every stage carries its own inputs/outputs/entry/exit/actor/
failure-behavior definition, inspectable before it has run.
"""
from __future__ import annotations

import sqlite3
import uuid
from datetime import UTC, datetime
from typing import Literal

EffectClass = Literal["idempotent", "externally_observable_uncertain"]


def create_workflow_instance(
    conn: sqlite3.Connection,
    feature_ref: str,
    scenario: str = "n/a",
) -> str:
    """FR-601: id IS the correlation identifier."""
    workflow_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    conn.execute(
        "INSERT INTO orchestration_workflow_instance "
        "(id, feature_ref, scenario, status, created_at, updated_at) "
        "VALUES (?, ?, ?, 'running', ?, ?)",
        (workflow_id, feature_ref, scenario, now, now),
    )
    conn.commit()
    return workflow_id


def add_stage(
    conn: sqlite3.Connection,
    workflow_instance_id: str,
    name: str,
    effect_class: EffectClass = "idempotent",
    artifact_revision: str = "v1",
    timeout_seconds: int = 5,
    depends_on: list[str] | None = None,
) -> str:
    """FR-203: inputs/outputs/entry/exit/actor/failure-behavior are captured
    via preconditions/postconditions (JSON, documentation fields) + the
    dependency edges below (the actual enforcement mechanism)."""
    stage_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    conn.execute(
        "INSERT INTO orchestration_workflow_stage "
        "(id, workflow_instance_id, name, status, attempt_count, effect_class, "
        " artifact_revision, preconditions, postconditions, timeout_seconds, created_at, updated_at) "
        "VALUES (?,?,?, 'pending', 0, ?, ?, NULL, NULL, ?, ?, ?)",
        (stage_id, workflow_instance_id, name, effect_class, artifact_revision, timeout_seconds, now, now),
    )
    for dep_stage_id in depends_on or []:
        conn.execute(
            "INSERT INTO orchestration_stage_dependency "
            "(workflow_instance_id, stage_id, depends_on_stage_id) VALUES (?,?,?)",
            (workflow_instance_id, stage_id, dep_stage_id),
        )
    conn.commit()
    return stage_id


def get_workflow_instance(conn: sqlite3.Connection, workflow_id: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM orchestration_workflow_instance WHERE id = ?", (workflow_id,)
    ).fetchone()


def get_stages(conn: sqlite3.Connection, workflow_id: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM orchestration_workflow_stage WHERE workflow_instance_id = ? ORDER BY created_at",
        (workflow_id,),
    ).fetchall()


def get_dependencies(conn: sqlite3.Connection, stage_id: str) -> list[str]:
    rows = conn.execute(
        "SELECT depends_on_stage_id FROM orchestration_stage_dependency WHERE stage_id = ?",
        (stage_id,),
    ).fetchall()
    return [r["depends_on_stage_id"] for r in rows]
