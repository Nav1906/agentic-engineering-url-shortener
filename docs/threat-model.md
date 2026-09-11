# Threat Model: Human Approval Credentials (ADR-0006 Revision 5)

**Scope**: this document covers exactly one boundary — the human-approval
credential mechanism T100–T103 implement. It is not a full application
threat model; other security controls (URL scheme allow-list, private-
address rejection, rate limiting) are documented in
[plan.md §8](../specs/001-governed-url-shortener/plan.md) and
[final-engineering-summary.md §10](final-engineering-summary.md).

## What This Release Does

Excludes external-agent subprocess execution from its trusted boundary
entirely (`src/orchestration/adapters/launcher.py` always fails closed —
see ADR-0006 Revision 5). Role-specific, cryptographically random tokens
(256 bits of entropy) authenticate human approvers; only salted SHA-256
hashes are stored where the running application reads them; raw tokens
live in a chmod-600, gitignored local file, printed once at creation.

## In Scope (this release defends against)

| Threat | Mitigation | Evidence |
|---|---|---|
| An external agent subprocess reads the raw approval token | No external agent subprocess is ever launched (T102) | `tests/security/test_external_agent_shutdown.py` |
| A network attacker guesses or brute-forces a token | 256-bit random tokens, constant-time comparison | `src/api/credentials.py`, `tests/security/test_credential_provisioning.py` |
| A caller supplies a fabricated identity instead of a verified one | Identity is derived only from a verified token hash, never a request field | FR-308, `tests/security/test_t103_security_verification.py` |
| An agent identity attempts to approve its own work | Unconditionally rejected regardless of role | FR-309, `tests/contract/test_approvals.py` |
| A valid credential is used at the wrong gate (role/gate mismatch) | Explicit per-gate role requirement, tested as its own case (FR-313), not folded into a generic rejection | `tests/contract/test_approvals.py::test_fr313_*` |
| An approval is reused after the artifact it applied to changed | Revision-binding + invalidation cascade (FR-311) | `tests/security/test_t103_security_verification.py::test_stale_revision_approval_invalidated_on_replan` |
| A raw token leaks via an API response, database row, log line, or git history | Structural tests scan for the actual token value in each of those locations | `tests/security/test_t103_security_verification.py` (7 dedicated tests) |
| An internal workflow (including the fully-autonomous T106 background scheduler) manufactures its own approval record | Only `src/api/routers/approvals.py` writes `orchestration_approval_decision`; verified by source-tree scan, not convention alone | `tests/security/test_t103_security_verification.py::test_only_approvals_router_writes_approval_decisions`, `test_live_scheduler_never_writes_approval_decisions` |

## Explicitly Out of Scope

**None of the following are claimed to be solved. Stating this plainly,
per the Human Gate 4 decision, rather than leaving it to be inferred from
what isn't mentioned:**

- **Same-OS-user compromise.** Any other process running as the same
  macOS user as this prototype — a malicious local application, a
  compromised dependency executing arbitrary code, a second terminal
  session the operator opens — can read `local-secrets/` directly. Unix
  file permissions (chmod 600) stop a *different* OS user or a
  non-privileged remote attacker; they do not stop anything already
  running as the same account. No sandbox, container, or separate OS user
  was implemented in this release.
- **Compromise of the operator's macOS account itself.** If the account
  is compromised, everything on it — this prototype's credentials
  included — is compromised. This is true of essentially any local
  development tool and is not a risk this decision introduces or could
  reasonably eliminate within this prototype's scope.
- **A future release that reintroduces external-agent execution.**
  Revision 5's acceptance is scoped to "no external-agent subprocess in
  this release." Wiring a real adapter behind
  `src/orchestration/adapters/launcher.py` in a later release would
  reopen exactly the credential-isolation question Revisions 1–4
  attempted and failed to close, and would require its own new ADR
  revision and Human Gate decision — it does not inherit Revision 5's
  acceptance.
- **Physical access to the machine.** Not addressed; standard for a local
  development prototype.
- **Denial of service against the approval endpoints specifically**
  (beyond the general `PVT-007` rate limit already applied uniformly
  across the domain API).

## Why Excluding External-Agent Execution Is Sufficient For This Release's Claim

The credential-isolation problem Revisions 1–4 tried to solve has one
specific shape: *a subprocess this application itself launches, with
different trust than the human operator, must not be able to read a
secret meant only for that human.* Removing the launch removes the
differently-trusted subprocess. What remains — same-OS-user protections —
was never what those four revisions were trying to build in the first
place; conflating "no agent can read this" with "nothing on this machine
can ever read this" would be a stronger and false claim. This document
exists so that distinction is never blurred in release communication.
