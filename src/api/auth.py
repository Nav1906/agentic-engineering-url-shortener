"""Verified-credential identity derivation — FAIL-CLOSED (T066, T067;
FR-308, FR-309).

ADR-0006's credential-isolation mechanism remains Rejected. T100
(scripts/bootstrap_credentials.py) and T101 (scripts/approve.py) are
explicitly BLOCKED pending an accepted replacement. Consequently there is
NO production credential-provisioning path wired into this build: the
credential store below is empty by default and stays empty in any real
deployment of this code, because nothing populates it. This is deliberate,
not an oversight — every approval attempt against a real deployment is
therefore rejected, which is the fail-closed behavior your instruction
requires, not a simulation of it.

`register_test_credential` exists ONLY for tests exercising the
role/revision-binding logic (T065) in isolation from the still-unresolved
credential question; it is never called by any application code path, only
by test fixtures.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Role = Literal["reviewer_approver", "release_owner"]


@dataclass(frozen=True)
class Identity:
    identity: str
    role: Role
    is_agent: bool = False


# Empty by default. Real deployment: stays empty forever until T100/T101 are
# unblocked by an accepted ADR-0006 replacement — this IS the fail-closed
# posture, not a placeholder for one.
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
    return _CREDENTIAL_STORE.get(bearer_token)


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
