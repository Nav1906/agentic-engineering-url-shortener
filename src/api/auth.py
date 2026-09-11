"""Verified-credential identity derivation (T066, T067, T100/T101;
FR-308, FR-309).

Human Gate 4, 2026-09-11: ADR-0006 Revision 5 was adopted — a
scope-limited replacement that permanently excludes external-agent
subprocess execution from this prototype's trusted boundary (see
src/orchestration/adapters/launcher.py). That is what makes real
credential provisioning (T100, src/api/credentials.py) safe to wire in
here: there is no agent process for a same-OS-user credential-isolation
gap to matter to. This does NOT claim same-user macOS credential
isolation is solved — see docs/threat-model.md.

`resolve_identity` checks two sources, in order: the TEST-ONLY in-memory
store (register_test_credential, for unit/contract tests that want an
isolated fake identity without touching the filesystem), then the real
file-backed store (src/api/credentials.py, populated by
scripts/bootstrap_credentials.py). A real deployment where bootstrap was
never run has an empty file-backed store too, so this remains fail-closed
by default — the difference from before is that there is now a real,
intentional path out of that default, not merely an empty placeholder.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from src.api import credentials

Role = Literal["reviewer_approver", "release_owner"]


@dataclass(frozen=True)
class Identity:
    identity: str
    role: Role
    is_agent: bool = False


# TEST-ONLY in-memory store, checked before the real file-backed one.
_CREDENTIAL_STORE: dict[str, Identity] = {}


def register_test_credential(token: str, identity: Identity) -> None:
    """TEST-ONLY. Never invoked by scripts/ or src/api/ application code."""
    _CREDENTIAL_STORE[token] = identity


def clear_test_credentials() -> None:
    """TEST-ONLY, for fixture teardown."""
    _CREDENTIAL_STORE.clear()


def resolve_identity(bearer_token: str | None) -> Identity | None:
    """FR-308: identity is derived from a verified credential; a
    caller-supplied name is never accepted as identity of record. Returns
    None (fail-closed) for a missing or unrecognized token — there is no
    fallback that grants access."""
    if not bearer_token:
        return None
    test_identity = _CREDENTIAL_STORE.get(bearer_token)
    if test_identity is not None:
        return test_identity
    verified = credentials.verify_token(bearer_token)
    if verified is None:
        return None
    identity, role = verified
    return Identity(identity=identity, role=role, is_agent=False)


def reject_if_agent(identity: Identity) -> None:
    """FR-309: unconditional — no agent identity may satisfy any
    human-approval gate, for any role, including but not limited to
    approving its own work."""
    if identity.is_agent:
        raise PermissionError(
            f"agent identity {identity.identity!r} cannot satisfy a human-approval gate (FR-309)"
        )


GATE_REQUIRED_ROLE: dict[str, Role] = {
    "requirements_approval": "reviewer_approver",
    "architecture_approval": "reviewer_approver",
    "release_readiness": "release_owner",
    "final_submission": "release_owner",
}


def required_role_for_gate(gate_id: str) -> Role:
    """FR-312/FR-313: any gate not in the explicit release-owner list
    defaults to reviewer_approver — never the other way around, since
    release-owner gates are named exhaustively and deliberately narrow."""
    return GATE_REQUIRED_ROLE.get(gate_id, "reviewer_approver")
