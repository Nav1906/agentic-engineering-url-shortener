"""T103: security verification for ADR-0006 Revision 5. Covers every item
the Human Gate 4 decision enumerated, in order. Uses an isolated
LOCAL_SECRETS_DIR throughout -- never touches this checkout's own
local-secrets/ directory.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api import credentials

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture()
def client(tmp_path, monkeypatch):
    import src.persistence.db as db_module
    from src.api.middleware.rate_limit import reset_all

    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    monkeypatch.setattr(credentials, "LOCAL_SECRETS_DIR", tmp_path / "local-secrets")
    reset_all()
    from src.api.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def bootstrapped(client):
    """Real T100 credentials, isolated to this test's tmp_path."""
    raw_tokens = credentials.bootstrap()
    return raw_tokens


# 1. Unauthenticated approval rejection -------------------------------------

def test_unauthenticated_approval_rejected(client):
    wf = client.post("/workflows", json={"requirement": "req"}).json()["id"]
    resp = client.post(f"/workflows/{wf}/gates/requirements_approval/approve", json={})
    assert resp.status_code == 401


# 2. Wrong-role rejection ----------------------------------------------------

def test_wrong_role_rejected(client, bootstrapped):
    wf = client.post("/workflows", json={"requirement": "req"}).json()["id"]
    # alice is reviewer_approver; release_readiness requires release_owner.
    resp = client.post(
        f"/workflows/{wf}/gates/release_readiness/approve", json={},
        headers={"Authorization": f"Bearer {bootstrapped['alice']}"},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"]["error"] == "wrong_role_for_gate"


# 3. Agent-identity rejection -------------------------------------------------

def test_agent_identity_rejected(client):
    from src.api.auth import Identity, clear_test_credentials, register_test_credential

    register_test_credential("agenttoken", Identity("agent-1", "reviewer_approver", is_agent=True))
    try:
        wf = client.post("/workflows", json={"requirement": "req"}).json()["id"]
        resp = client.post(
            f"/workflows/{wf}/gates/requirements_approval/approve", json={},
            headers={"Authorization": "Bearer agenttoken"},
        )
        assert resp.status_code == 403
        assert resp.json()["detail"]["error"] == "agent_identity_forbidden"
    finally:
        clear_test_credentials()


# 4. Stale-revision rejection -------------------------------------------------

def test_stale_revision_approval_invalidated_on_replan(client, bootstrapped):
    """FR-311: an approval bound to a revision is invalidated when that
    revision changes. This exercises the real HTTP approval path plus the
    existing replanning invalidation mechanism (T078) -- there is no
    separate HTTP endpoint for triggering a replan in this build, so the
    replan step itself uses the module directly (legitimate white-box
    verification of a server-side mechanism, not a claim that replanning
    is itself HTTP-triggered in this release)."""
    import src.persistence.db as db_module
    from src.orchestration.models import add_stage
    from src.orchestration.replanning import invalidate_downstream

    wf = client.post("/workflows", json={"requirement": "req"}).json()["id"]
    resp = client.post(
        f"/workflows/{wf}/gates/requirements_approval/approve", json={"rationale": "ok"},
        headers={"Authorization": f"Bearer {bootstrapped['alice']}"},
    )
    assert resp.status_code == 200
    approval_id = resp.json()["id"]
    assert resp.json()["artifact_revision"] == "v1"

    conn = db_module.get_connection()
    try:
        stage = add_stage(conn, wf, "some_stage", artifact_revision="v1")
        result = invalidate_downstream(conn, wf, "v2", [stage])
        assert len(result["approvals"]) == 1

        row = conn.execute(
            "SELECT invalidated_at FROM orchestration_approval_decision WHERE id=?", (approval_id,)
        ).fetchone()
        assert row["invalidated_at"] is not None  # stale, no longer valid
    finally:
        conn.close()


# 5 & 6. Valid reviewer / release-owner approval, via the REAL T100/T101 pipeline --

def test_valid_reviewer_approval_via_real_credentials(client, bootstrapped):
    wf = client.post("/workflows", json={"requirement": "req"}).json()["id"]
    resp = client.post(
        f"/workflows/{wf}/gates/requirements_approval/approve", json={"rationale": "complete"},
        headers={"Authorization": f"Bearer {bootstrapped['alice']}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["identity"] == "alice"
    assert body["role"] == "reviewer_approver"
    assert body["decision"] == "approved"


def test_valid_release_owner_approval_via_real_credentials(client, bootstrapped):
    wf = client.post("/workflows", json={"requirement": "req"}).json()["id"]
    resp = client.post(
        f"/workflows/{wf}/gates/release_readiness/approve", json={"rationale": "shipping"},
        headers={"Authorization": f"Bearer {bootstrapped['bob']}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["identity"] == "bob"
    assert body["role"] == "release_owner"


# 7. Raw credentials absent from logs, API responses, DB rows, git-tracked files, subprocess envs --

def test_raw_token_never_in_api_response(client, bootstrapped):
    wf = client.post("/workflows", json={"requirement": "req"}).json()["id"]
    resp = client.post(
        f"/workflows/{wf}/gates/requirements_approval/approve", json={"rationale": "x"},
        headers={"Authorization": f"Bearer {bootstrapped['alice']}"},
    )
    serialized = json.dumps(resp.json())
    assert bootstrapped["alice"] not in serialized
    assert bootstrapped["bob"] not in serialized


def test_raw_token_never_in_database_rows(client, bootstrapped):
    import src.persistence.db as db_module

    wf = client.post("/workflows", json={"requirement": "req"}).json()["id"]
    client.post(
        f"/workflows/{wf}/gates/requirements_approval/approve", json={"rationale": "x"},
        headers={"Authorization": f"Bearer {bootstrapped['alice']}"},
    )
    conn = db_module.get_connection()
    try:
        tables = [r["name"] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
        for table in tables:
            rows = conn.execute(f"SELECT * FROM {table}").fetchall()
            for row in rows:
                row_text = " ".join(str(v) for v in tuple(row))
                assert bootstrapped["alice"] not in row_text, f"raw token found in table {table!r}"
                assert bootstrapped["bob"] not in row_text, f"raw token found in table {table!r}"
    finally:
        conn.close()


def test_local_secrets_directory_is_gitignored():
    """Real, repo-relative check (not the isolated tmp_path fixture) --
    confirms the actual project's own local-secrets/ path is ignored."""
    result = subprocess.run(
        ["git", "check-ignore", "local-secrets/approval_tokens.raw.json"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, "local-secrets/ must be gitignored"


def test_local_secrets_never_git_tracked():
    result = subprocess.run(
        ["git", "ls-files", "local-secrets/"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    assert result.stdout.strip() == "", "no file under local-secrets/ may ever be git-tracked"


def test_no_token_logging_anywhere_in_src():
    """Structural: src/ never logs, prints, or records a raw token value.
    The ONE intentional print is in scripts/bootstrap_credentials.py,
    explicitly excluded here since that's the documented, one-time,
    operator-facing disclosure this whole design exists to allow."""
    token_var_pattern = re.compile(r"\b(print|log(?:ger)?\.\w+)\([^)]*\btoken\b", re.IGNORECASE)
    offenders = []
    for path in REPO_ROOT.glob("src/**/*.py"):
        text = path.read_text()
        if token_var_pattern.search(text):
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert offenders == [], f"possible token logging in: {offenders}"


def test_no_raw_token_reaches_a_subprocess_environment():
    """Since T102 ensures no subprocess ever launches carrying any
    externally-supplied environment/argument in this release, this is a
    structural corollary: credentials.py and auth.py never construct an
    environment dict or subprocess argument list at all."""
    for rel in ("src/api/credentials.py", "src/api/auth.py"):
        text = (REPO_ROOT / rel).read_text()
        assert "import subprocess" not in text
        assert "subprocess." not in text
        assert "os.environ" not in text


# 8. External-agent launch always fails closed and is audited ----------------
# (Full coverage in tests/security/test_external_agent_shutdown.py; this
# file adds one more confirmation as part of the T103 checklist.)

def test_external_agent_launch_fails_closed_and_audited():
    import tempfile

    import src.persistence.db as db_module2
    from src.observability.audit import get_events_for_workflow
    from src.orchestration.adapters.launcher import (
        ExternalAgentLaunchBlocked,
        LaunchRequest,
        launch_external_agent,
    )
    from src.orchestration.models import create_workflow_instance

    with tempfile.TemporaryDirectory() as tmp:
        db_module2.DB_PATH = str(Path(tmp) / "app.db")
        conn = db_module2.get_connection()
        db_module2.init_schema(conn)
        wf = create_workflow_instance(conn, "req")
        with pytest.raises(ExternalAgentLaunchBlocked):
            launch_external_agent(conn, LaunchRequest(agent_name="claude", command=("claude",), workflow_instance_id=wf))
        events = get_events_for_workflow(conn, wf)
        assert any(e["action"] == "external_agent_launch_blocked" for e in events)
        conn.close()


# 9. Application workflows cannot manufacture human approval records internally --

def test_only_approvals_router_writes_approval_decisions():
    """Structural: the only INSERT into orchestration_approval_decision
    anywhere in src/ is in src/api/routers/approvals.py -- no internal
    workflow/scheduler code path can manufacture a human approval record
    for itself."""
    offenders = []
    for path in REPO_ROOT.glob("src/**/*.py"):
        rel = str(path.relative_to(REPO_ROOT))
        if rel == "src/api/routers/approvals.py":
            continue
        text = path.read_text()
        if "INSERT INTO orchestration_approval_decision" in text:
            offenders.append(rel)
    assert offenders == [], f"unauthorized approval-record write in: {offenders}"


def test_live_scheduler_never_writes_approval_decisions():
    """live_scheduler.py (T106, fully automatic, no human in the loop)
    must never be able to write an approval record -- it drives stage
    execution, never gate decisions."""
    text = (REPO_ROOT / "src/orchestration/live_scheduler.py").read_text()
    assert "orchestration_approval_decision" not in text
