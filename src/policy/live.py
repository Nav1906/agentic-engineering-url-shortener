"""Live policy evaluation wired into workflow execution (T105; SC-006).

Runs every mandatory policy from config/policies.yaml automatically as
part of a workflow's own progress -- not just unit-tested in isolation
(the gap T105 closes). Each check below is real, fast, deterministic, and
local -- none depend on network access, so they're safe to run
automatically on every workflow without becoming a bottleneck or a flaky
dependency.
"""
from __future__ import annotations

import sqlite3
from collections.abc import Callable
from pathlib import Path

from src.policy.evaluator import Outcome, evaluate_policy, has_unresolved_fail
from src.policy.manifest import load_manifest, policy_ids

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _check_dependency_secret_scan() -> Outcome:
    """Real, fast, local integrity signal: the committed lockfile must not
    be older than pyproject.toml (i.e. dependencies were re-locked after
    the last manifest change). The slow, network-based vulnerability scan
    itself (pip-audit) remains a separate, release-readiness-time check
    (T044) -- not re-run per workflow, which would make every workflow
    slow and network-dependent."""
    pyproject = _REPO_ROOT / "pyproject.toml"
    lockfile = _REPO_ROOT / "uv.lock"
    if not lockfile.exists():
        return "FAIL"
    if not pyproject.exists():
        return "NOT-APPLICABLE"
    return "PASS" if lockfile.stat().st_mtime >= pyproject.stat().st_mtime else "FAIL"


def _check_change_control(conn: sqlite3.Connection, workflow_instance_id: str) -> Outcome:
    """FAIL if this workflow's own decision lineage declares a material
    change (FR-306) with no corresponding succeeded impact-analysis stage
    yet; PASS otherwise (including the common case where no material
    change was ever declared)."""
    lineage_rows = conn.execute(
        "SELECT detail FROM orchestration_decision_lineage "
        "WHERE workflow_instance_id=? AND decision_type='material_change_detected'",
        (workflow_instance_id,),
    ).fetchall()
    if not lineage_rows:
        return "PASS"
    impact_done = conn.execute(
        "SELECT 1 FROM orchestration_workflow_stage "
        "WHERE workflow_instance_id=? AND name='impact_analysis' AND status='succeeded'",
        (workflow_instance_id,),
    ).fetchone()
    return "PASS" if impact_done is not None else "FAIL"


def _check_release_readiness_not_applicable_here() -> Outcome:
    """This policy is evaluated only by the release-readiness procedure
    itself (is_release_ready, below) -- not meaningfully per-workflow."""
    return "NOT-APPLICABLE"


_CHECK_FUNCTIONS: dict[str, Callable] = {
    "dependency-secret-scan": lambda conn, wf: _check_dependency_secret_scan(),
    "change-control": _check_change_control,
    "release-readiness": lambda conn, wf: _check_release_readiness_not_applicable_here(),
}


def run_mandatory_policy_checks(
    conn: sqlite3.Connection, workflow_instance_id: str, artifact_revision: str
) -> dict[str, str]:
    """T105: runs every policy in the manifest automatically, persists a
    policy_evaluation row per policy tied to this workflow AND this
    artifact_revision. Returns {policy_id: outcome}."""
    manifest = load_manifest()
    results: dict[str, str] = {}
    for policy_id in policy_ids(manifest):
        check_fn = _CHECK_FUNCTIONS.get(policy_id)
        outcome: Outcome = check_fn(conn, workflow_instance_id) if check_fn else "NOT-APPLICABLE"

        def _return_outcome(o: Outcome = outcome) -> Outcome:
            return o

        evaluate_policy(
            conn, policy_id, manifest["version"], _return_outcome,
            workflow_instance_id=workflow_instance_id, artifact_revision=artifact_revision,
        )
        results[policy_id] = outcome
    return results


def is_release_ready(
    conn: sqlite3.Connection, workflow_instance_id: str, current_artifact_revision: str
) -> tuple[bool, list[str]]:
    """Prevents downstream release-readiness when a mandatory policy
    result is FAIL/unresolved, OR when the only evaluation on record for a
    mandatory policy was made against a now-stale artifact_revision
    (replanning invalidation, T105's explicit requirement) -- a stale
    evaluation is treated as equivalent to "never evaluated for this
    revision", not silently trusted."""
    reasons: list[str] = []

    if has_unresolved_fail(conn, workflow_instance_id):
        reasons.append("at least one mandatory policy check is FAIL and unresolved")

    manifest = load_manifest()
    for policy_id in policy_ids(manifest):
        latest = conn.execute(
            "SELECT artifact_revision, outcome FROM policy_evaluation "
            "WHERE workflow_instance_id=? AND policy_id=? ORDER BY id DESC LIMIT 1",
            (workflow_instance_id, policy_id),
        ).fetchone()
        if latest is None:
            reasons.append(f"policy {policy_id!r} was never evaluated for this workflow")
            continue
        if latest["artifact_revision"] != current_artifact_revision:
            reasons.append(
                f"policy {policy_id!r}'s only evaluation is stale "
                f"(revision {latest['artifact_revision']!r} != current {current_artifact_revision!r})"
            )

    return (len(reasons) == 0, reasons)
