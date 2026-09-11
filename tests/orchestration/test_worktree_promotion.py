"""T061: isolated git worktree per execution + controller-only promotion.
Tests stale-output rejection, revision mismatch, cleanup, and that a
worker cannot directly promote into the main tree (structural: the fixture
worker function never receives repo_path -- there is no parameter through
which it could reach the main tree).

Uses a throwaway git repository per test, never the actual project repo.
Fixture workers below are plain in-process file writes -- never a
subprocess, never Claude, never anything that touches ADR-0006's still-
unresolved isolation question.
"""
import subprocess
from pathlib import Path

import pytest

import src.persistence.db as db_module
from src.orchestration.models import add_stage, create_workflow_instance
from src.orchestration.scheduler import claim_stage, mark_ready
from src.orchestration.workspace import create_worktree, promote_or_reject, remove_worktree


def harmless_fixture_worker(worktree_path: Path) -> None:
    """Structurally cannot touch the main tree: this is the only parameter
    it receives. Never launches a subprocess."""
    (worktree_path / "output.txt").write_text("fixture output")


@pytest.fixture()
def isolated_repo(tmp_path):
    repo_path = tmp_path / "fixture-repo"
    repo_path.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, check=True)
    (repo_path / "README.md").write_text("fixture repo\n")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=repo_path, check=True)
    return repo_path


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    yield c
    c.close()


def _new_worktree(isolated_repo, execution_id, tmp_path):
    worktrees_root = tmp_path / "worktrees"
    worktrees_root.mkdir(exist_ok=True)
    return create_worktree(isolated_repo, execution_id, worktrees_root)


def test_valid_execution_is_promoted(conn, isolated_repo, tmp_path):
    wf = create_workflow_instance(conn, "req")
    stage = add_stage(conn, wf, "file_producing", artifact_revision="v1")
    mark_ready(conn, [stage])
    execution_id = claim_stage(conn, stage, "worker-1")
    worktree_path = _new_worktree(isolated_repo, execution_id, tmp_path)

    harmless_fixture_worker(worktree_path)

    promoted = promote_or_reject(
        conn, isolated_repo, execution_id, stage, worktree_path, expected_revision="v1",
        validator_name="file_exists", validator_args={"filename": "output.txt"},
    )
    assert promoted is True
    assert (isolated_repo / "output.txt").read_text() == "fixture output"

    row = conn.execute("SELECT status FROM orchestration_workflow_stage WHERE id=?", (stage,)).fetchone()
    assert row["status"] == "succeeded"

    exec_row = conn.execute(
        "SELECT outcome_detail FROM orchestration_stage_execution WHERE id=?", (execution_id,)
    ).fetchone()
    import json

    detail = json.loads(exec_row["outcome_detail"])
    assert detail["validator_exit_code"] == 0
    assert "output.txt" in detail["artifact_hashes"]

    remove_worktree(isolated_repo, execution_id, worktree_path)
    assert not worktree_path.exists()


def test_stale_abandoned_execution_never_promoted(conn, isolated_repo, tmp_path):
    wf = create_workflow_instance(conn, "req")
    stage = add_stage(conn, wf, "file_producing", artifact_revision="v1")
    mark_ready(conn, [stage])
    execution_id = claim_stage(conn, stage, "worker-1")
    worktree_path = _new_worktree(isolated_repo, execution_id, tmp_path)
    harmless_fixture_worker(worktree_path)

    # Simulate the reaper (T059) having already abandoned this execution
    # before the worker's (late) promotion attempt arrives.
    conn.execute("UPDATE orchestration_stage_execution SET status='abandoned' WHERE id=?", (execution_id,))
    conn.commit()

    promoted = promote_or_reject(conn, isolated_repo, execution_id, stage, worktree_path, expected_revision="v1")
    assert promoted is False
    assert not (isolated_repo / "output.txt").exists()

    row = conn.execute("SELECT status FROM orchestration_workflow_stage WHERE id=?", (stage,)).fetchone()
    assert row["status"] != "succeeded"

    remove_worktree(isolated_repo, execution_id, worktree_path)


def test_revision_mismatch_never_promoted(conn, isolated_repo, tmp_path):
    wf = create_workflow_instance(conn, "req")
    stage = add_stage(conn, wf, "file_producing", artifact_revision="v1")
    mark_ready(conn, [stage])
    execution_id = claim_stage(conn, stage, "worker-1")
    worktree_path = _new_worktree(isolated_repo, execution_id, tmp_path)
    harmless_fixture_worker(worktree_path)

    # A replan bumped the stage's artifact_revision to v2 while this
    # execution was still working against v1 -- classic stale-output case.
    conn.execute("UPDATE orchestration_workflow_stage SET artifact_revision='v2' WHERE id=?", (stage,))
    conn.commit()

    promoted = promote_or_reject(conn, isolated_repo, execution_id, stage, worktree_path, expected_revision="v1")
    assert promoted is False
    assert not (isolated_repo / "output.txt").exists()

    remove_worktree(isolated_repo, execution_id, worktree_path)


def test_failed_validator_never_promotes(conn, isolated_repo, tmp_path):
    """Proves no path to `succeeded` bypasses the validator -- here the
    worker never wrote the expected artifact at all."""
    wf = create_workflow_instance(conn, "req")
    stage = add_stage(conn, wf, "file_producing", artifact_revision="v1")
    mark_ready(conn, [stage])
    execution_id = claim_stage(conn, stage, "worker-1")
    worktree_path = _new_worktree(isolated_repo, execution_id, tmp_path)
    # No harmless_fixture_worker() call -- worktree stays empty.

    promoted = promote_or_reject(
        conn, isolated_repo, execution_id, stage, worktree_path, expected_revision="v1",
        validator_name="file_exists", validator_args={"filename": "output.txt"},
    )
    assert promoted is False
    row = conn.execute("SELECT status FROM orchestration_workflow_stage WHERE id=?", (stage,)).fetchone()
    assert row["status"] == "failed_transient"
    assert not (isolated_repo / "output.txt").exists()

    remove_worktree(isolated_repo, execution_id, worktree_path)


def test_no_validator_ran_case_never_promotes(conn, isolated_repo, tmp_path):
    """The explicit 'validation has not run' representation must also
    never reach succeeded -- omission is not evidence either."""
    wf = create_workflow_instance(conn, "req")
    stage = add_stage(conn, wf, "file_producing", artifact_revision="v1")
    mark_ready(conn, [stage])
    execution_id = claim_stage(conn, stage, "worker-1")
    worktree_path = _new_worktree(isolated_repo, execution_id, tmp_path)
    harmless_fixture_worker(worktree_path)  # even with real output present

    promoted = promote_or_reject(
        conn, isolated_repo, execution_id, stage, worktree_path, expected_revision="v1",
        validator_name="no_validator_ran",
    )
    assert promoted is False
    row = conn.execute("SELECT status FROM orchestration_workflow_stage WHERE id=?", (stage,)).fetchone()
    assert row["status"] != "succeeded"

    remove_worktree(isolated_repo, execution_id, worktree_path)


def test_cleanup_removes_worktree_and_branch(conn, isolated_repo, tmp_path):
    wf = create_workflow_instance(conn, "req")
    stage = add_stage(conn, wf, "file_producing", artifact_revision="v1")
    mark_ready(conn, [stage])
    execution_id = claim_stage(conn, stage, "worker-1")
    worktree_path = _new_worktree(isolated_repo, execution_id, tmp_path)
    harmless_fixture_worker(worktree_path)
    promote_or_reject(
        conn, isolated_repo, execution_id, stage, worktree_path, expected_revision="v1",
        validator_name="file_exists", validator_args={"filename": "output.txt"},
    )

    remove_worktree(isolated_repo, execution_id, worktree_path)

    assert not worktree_path.exists()
    result = subprocess.run(["git", "worktree", "list"], cwd=isolated_repo, capture_output=True, text=True, check=False)
    assert str(worktree_path) not in result.stdout
    branches = subprocess.run(["git", "branch"], cwd=isolated_repo, capture_output=True, text=True, check=False)
    assert f"exec-{execution_id}" not in branches.stdout


def test_worker_function_has_no_access_to_repo_path():
    """Structural guarantee, not a convention: the fixture worker's
    signature takes only a worktree_path."""
    import inspect

    sig = inspect.signature(harmless_fixture_worker)
    assert list(sig.parameters.keys()) == ["worktree_path"]
