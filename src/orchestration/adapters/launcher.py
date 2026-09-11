"""Centralized external-agent launcher interface (T102; ADR-0006
Revision 5, Human Gate 4 decision 2026-09-11).

This is the ONE sanctioned entry point for launching an external agent
(Claude Code or any other subprocess-based agent) anywhere in this
codebase. For THIS release, it always fails closed: no external agent is
ever actually launched, by design, regardless of caller or arguments. The
Human Gate 4 decision was explicit: "The released prototype MUST NOT
launch Claude Code or any external agent subprocess." This function is
what makes that a single, auditable, structurally-enforced choke point
rather than a policy someone has to remember to honor at every call site.

Built-in, deterministic adapters (src/orchestration/validators.py's
built-in validators, src/orchestration/live_scheduler.py's
_execute_stage_safely) are NOT external agents and do not go through this
module — they never did, and still don't.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime

from src.observability.audit import record_event


class ExternalAgentLaunchBlocked(RuntimeError):
    """Raised by every call to launch_external_agent() in this release.
    Not a bug, not a missing feature -- the Human Gate 4 scope decision
    for ADR-0006 Revision 5."""


@dataclass(frozen=True)
class LaunchRequest:
    agent_name: str
    command: tuple[str, ...]
    stage_id: str | None = None
    workflow_instance_id: str | None = None


def launch_external_agent(conn: sqlite3.Connection, request: LaunchRequest) -> None:
    """The ONE function that would launch an external agent subprocess, if
    this release permitted it. It doesn't. Every call — regardless of
    agent_name, command, or caller — raises ExternalAgentLaunchBlocked and
    records an audit event first, so the attempt itself is never silent.
    """
    now = datetime.now(UTC).isoformat()
    reason = (
        f"external-agent launch blocked by design (ADR-0006 Revision 5, Human Gate 4, "
        f"{now[:10]}): this release excludes external-agent subprocess execution from its "
        f"trusted boundary entirely. agent_name={request.agent_name!r} command={request.command!r}"
    )
    record_event(
        conn, "system", "external_agent_launch_blocked",
        f"agent:{request.agent_name}", "blocked", reason,
        workflow_instance_id=request.workflow_instance_id,
    )
    raise ExternalAgentLaunchBlocked(reason)
