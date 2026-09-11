"""Isolated per-execution git worktrees + controller-only promotion
(T061; ADR-0005 "Isolated Execution Workspaces").

Never operates against this project's own repository from library code --
every function here takes an explicit repo_path, so this module cannot
accidentally mutate the assessment repository's own git state; callers
(tests, and any future real wiring) must supply a throwaway repo.

promote_or_reject() is the ONLY function in this codebase that copies
content from an isolated worktree into a main working tree. A worker
function is never given repo_path at all (see the fixture workers in
tests/orchestration/test_worktree_promotion.py) -- it has no parameter
through which it could reach the main tree, which is what makes promotion
controller-only by construction, not merely by convention.
"""
from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from src.orchestration.validators import run_builtin_validator


class WorkspaceError(RuntimeError):
    pass


def _run_git(repo_path: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo_path), *args],
        capture_output=True, text=True, check=False, timeout=10,
    )


def create_worktree(repo_path: Path, execution_id: str, worktrees_root: Path) -> Path:
    """Creates an isolated git worktree on its own disposable branch."""
    worktree_path = worktrees_root / execution_id
    branch = f"exec-{execution_id}"
    result = _run_git(repo_path, "worktree", "add", "-b", branch, str(worktree_path), "HEAD")
    if result.returncode != 0:
        raise WorkspaceError(f"git worktree add failed: {result.stderr}")
    return worktree_path


def remove_worktree(repo_path: Path, execution_id: str, worktree_path: Path) -> None:
    """Cleanup -- removes the worktree and its disposable branch,
    regardless of whether promotion succeeded or was rejected."""
    _run_git(repo_path, "worktree", "remove", "--force", str(worktree_path))
    _run_git(repo_path, "branch", "-D", f"exec-{execution_id}")
    _run_git(repo_path, "worktree", "prune")
    if worktree_path.exists():
        shutil.rmtree(worktree_path, ignore_errors=True)


def promote_or_reject(
    conn: sqlite3.Connection,
    repo_path: Path,
    execution_id: str,
    stage_id: str,
    worktree_path: Path,
    expected_revision: str,
    validator_name: str = "file_exists",
    validator_args: dict | None = None,
) -> bool:
    """Fencing + revision-match + validator, in that order, all required.
    Returns True if promoted, False for any legitimate rejection (stale
    execution, revision mismatch, failed validator) -- rejection is an
    expected, tested outcome, not an error."""
    execution = conn.execute(
        "SELECT status FROM orchestration_stage_execution WHERE id=?", (execution_id,)
    ).fetchone()
    stage = conn.execute(
        "SELECT artifact_revision FROM orchestration_workflow_stage WHERE id=?", (stage_id,)
    ).fetchone()

    fenced_ok = execution is not None and execution["status"] in ("claimed", "running")
    revision_ok = stage is not None and stage["artifact_revision"] == expected_revision

    validator_result = run_builtin_validator(validator_name, worktree_path, validator_args or {})
    outcome_detail = {
        "validator_command": validator_result.command,
        "validator_exit_code": validator_result.exit_code,
        "validator_output_hash": validator_result.output_hash,
        "artifact_hashes": validator_result.artifact_hashes,
    }
    conn.execute(
        "UPDATE orchestration_stage_execution SET outcome_detail=? WHERE id=?",
        (json.dumps(outcome_detail), execution_id),
    )

    now = datetime.now(UTC).isoformat()

    if not fenced_ok:
        conn.execute(
            "UPDATE orchestration_stage_execution SET status='abandoned' WHERE id=? AND status != 'abandoned'",
            (execution_id,),
        )
        conn.commit()
        return False

    if not revision_ok:
        conn.execute("UPDATE orchestration_stage_execution SET status='failed' WHERE id=?", (execution_id,))
        conn.commit()
        return False

    if not validator_result.passed:
        conn.execute("UPDATE orchestration_stage_execution SET status='failed' WHERE id=?", (execution_id,))
        conn.execute(
            "UPDATE orchestration_workflow_stage SET status='failed_transient', updated_at=? WHERE id=?",
            (now, stage_id),
        )
        conn.commit()
        return False

    # Fencing-gated completion write -- same CAS pattern as T046's
    # scheduler.complete_stage: a late/duplicate call affects 0 rows.
    cur = conn.execute(
        "UPDATE orchestration_stage_execution SET status='completed' WHERE id=? AND status IN ('claimed','running')",
        (execution_id,),
    )
    if cur.rowcount == 0:
        conn.commit()
        return False

    # Only now, after every gate has passed, copy from the isolated
    # worktree into the main working tree. Nothing before this line ever
    # touches repo_path's files.
    for item in worktree_path.iterdir():
        if item.name == ".git":
            continue
        dest = repo_path / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)

    conn.execute(
        "UPDATE orchestration_workflow_stage SET status='succeeded', updated_at=? WHERE id=?",
        (now, stage_id),
    )
    conn.commit()
    return True
