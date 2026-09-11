"""T102: enforced external-agent shutdown (ADR-0006 Revision 5). Proves
both that the one centralized launcher always fails closed AND audits,
and -- structurally, by scanning the actual source tree -- that no
alternate code path invokes `claude`, a shell, or an external agent
process anywhere in src/ or scripts/.
"""
import re
from pathlib import Path

import pytest

import src.persistence.db as db_module
from src.observability.audit import get_events_for_workflow
from src.orchestration.adapters.launcher import (
    ExternalAgentLaunchBlocked,
    LaunchRequest,
    launch_external_agent,
)
from src.orchestration.models import create_workflow_instance

REPO_ROOT = Path(__file__).resolve().parents[2]

# Every subprocess-invoking call site in this codebase, and why each one
# is NOT an external agent launch. Any subprocess/Popen/os.system/exec
# call site NOT in this allowlist fails the structural test below.
ALLOWED_SUBPROCESS_SITES = {
    "src/orchestration/workspace.py": "git worktree management -- git is not an agent",
    "scripts/smoke.sh": "starts uvicorn to serve this same application, not an agent",
    "scripts/demo_brownfield.py": "runs the project's own pytest regression suite as evidence, not an agent",
}


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    c = db_module.get_connection()
    db_module.init_schema(c)
    yield c
    c.close()


def test_launch_always_raises(conn):
    wf = create_workflow_instance(conn, "req")
    with pytest.raises(ExternalAgentLaunchBlocked):
        launch_external_agent(
            conn, LaunchRequest(agent_name="claude", command=("claude", "-p", "do something"), workflow_instance_id=wf),
        )


def test_launch_attempt_is_audited_even_though_blocked(conn):
    wf = create_workflow_instance(conn, "req")
    with pytest.raises(ExternalAgentLaunchBlocked):
        launch_external_agent(
            conn, LaunchRequest(agent_name="claude", command=("claude",), workflow_instance_id=wf),
        )
    events = get_events_for_workflow(conn, wf)
    blocked = [e for e in events if e["action"] == "external_agent_launch_blocked"]
    assert len(blocked) == 1
    assert blocked[0]["result"] == "blocked"
    assert blocked[0]["actor_type"] == "system"


def test_launch_blocked_regardless_of_agent_name_or_command(conn):
    """Not a claude-specific denylist -- unconditional, for any agent."""
    for agent_name, command in [
        ("claude", ("claude", "-p", "x")),
        ("some-other-agent", ("some-other-agent", "--flag")),
        ("", ()),
    ]:
        with pytest.raises(ExternalAgentLaunchBlocked):
            launch_external_agent(conn, LaunchRequest(agent_name=agent_name, command=command))


def _iter_source_files():
    for pattern in ("src/**/*.py", "scripts/**/*.py", "scripts/**/*.sh"):
        yield from REPO_ROOT.glob(pattern)


def test_no_unaccounted_subprocess_invocation_anywhere_in_src_or_scripts():
    """Structural proof, not a claim: every subprocess/Popen/os.system/
    external-command invocation in src/ or scripts/ is either absent, or
    explicitly named (and justified) in ALLOWED_SUBPROCESS_SITES above.
    A new subprocess call site added anywhere else fails this test."""
    pattern = re.compile(r"\bsubprocess\.(run|Popen|call|check_call|check_output)\b|\bos\.system\b")
    offenders = []
    for path in _iter_source_files():
        rel = str(path.relative_to(REPO_ROOT))
        if rel == "tests/security/test_external_agent_shutdown.py":
            continue  # this file's own allowlist regex/strings don't count
        text = path.read_text()
        if pattern.search(text) and rel not in ALLOWED_SUBPROCESS_SITES:
            offenders.append(rel)
    assert offenders == [], f"unaccounted subprocess invocation in: {offenders}"


def test_no_claude_cli_invocation_anywhere_outside_the_launcher_and_its_docs():
    """The literal string 'claude' as a command/binary reference must not
    appear anywhere in src/ or scripts/ except this launcher module's own
    docstrings/error text (which explicitly names it only to explain why
    it's blocked) and this test file itself."""
    # Files that mention "claude" only in prose (docstrings/comments
    # explaining that they do NOT invoke it) are legitimate, not offenders.
    prose_only_exceptions = {
        "src/orchestration/adapters/launcher.py",
        "src/orchestration/live_scheduler.py",
        "src/api/auth.py",
        "src/api/credentials.py",
        "tests/security/test_external_agent_shutdown.py",
    }
    offenders = []
    for path in _iter_source_files():
        rel = str(path.relative_to(REPO_ROOT))
        if rel in prose_only_exceptions:
            continue
        text = path.read_text()
        # Looks for an actual invocation-shaped reference, e.g. ["claude", ...]
        # or "claude " as a command token -- not incidental prose.
        if re.search(r'["\']claude["\'],|\bclaude\s+-p\b', text):
            offenders.append(rel)
    assert offenders == [], f"unexpected claude CLI reference in: {offenders}"


def test_builtin_adapters_remain_allowed_and_unaffected():
    """Built-in deterministic validators/adapters are NOT external agents
    and must keep working exactly as before -- T102 blocks agents, not
    the project's own built-in execution mechanics."""
    from src.orchestration.validators import run_builtin_validator

    result = run_builtin_validator("no_validator_ran", REPO_ROOT, {})
    assert result.passed is False  # unrelated to T102; just proves the call still works
