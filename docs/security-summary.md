# Security Summary

**Purpose**: one of the 13 required `/speckit-converge` outputs (guide
Section 22). Consolidates the security posture already documented in
[final-engineering-summary.md §10](final-engineering-summary.md) and
[threat-model.md](threat-model.md) into a single reviewable artifact —
content is cross-referenced, not duplicated.
**Generated**: 2026-09-11, during the convergence pass.

## Controls implemented and verified

| Control | Mechanism | Evidence |
|---|---|---|
| Malicious-scheme rejection | Explicit allow-list (`https`/`http` only) | `plan.md §8`, `tests/security/test_malicious_input_abuse_cases.py` |
| Private/internal-address rejection | Rejected at short-link creation time | `plan.md §8` (DNS-rebinding-at-resolution-time explicitly **not** covered — disclosed, not silent) |
| Idempotency-key minimum length | 16-char floor enforced | `plan.md §8` |
| Rate limiting | 60 req/min/IP, `/health` exempted | `tests/security/test_health_exempt_from_rate_limit.py` |
| Malicious-input / abuse-case handling | Parameterized queries throughout; SQLi-shaped input, path traversal, oversized payloads, null bytes, script-URI variants all handled safely | `tests/security/test_malicious_input_abuse_cases.py` (8+ tests) |
| Dependency vulnerability scan | `pip-audit` | **No known vulnerabilities found** (final-engineering-summary.md §17) |
| Credential provisioning | 256-bit `secrets.token_urlsafe(32)` tokens, salted SHA-256 hash storage, `hmac.compare_digest` constant-time verification, chmod 600, gitignored | `src/api/credentials.py`, `tests/security/test_credential_provisioning.py` |
| Server-side identity derivation | Identity/role derived only from the verified token hash — never a client-supplied field; `--identity` on the CLI is a local raw-token lookup key only, never transmitted | `src/api/auth.py::resolve_identity`, `tests/security/test_identity_impersonation_resistance.py` (4 tests, added during this convergence pass) |
| Agent-originated approval rejection | Unconditionally rejected regardless of role | FR-309, `tests/contract/test_approvals.py` |
| Wrong-role-for-gate rejection | Explicit per-gate role requirement, its own tested negative case (FR-313) | `tests/contract/test_approvals.py::test_fr313_*` |
| Revision-binding on approvals | An approval is invalidated by a downstream replan that changes the artifact it applied to (FR-311) | `tests/security/test_t103_security_verification.py::test_stale_revision_approval_invalidated_on_replan` |
| External-agent subprocess execution | Permanently excluded from the trusted boundary (ADR-0006 Revision 5); `src/orchestration/adapters/launcher.py` is the sole entry point and always fails closed, audited | `tests/security/test_external_agent_shutdown.py` (structural source-tree scan, not just an assertion) |
| No internal code path manufactures its own approval | Only `src/api/routers/approvals.py` writes `orchestration_approval_decision`, including from the autonomous T106 background scheduler | `tests/security/test_t103_security_verification.py::test_only_approvals_router_writes_approval_decisions`, `test_live_scheduler_never_writes_approval_decisions` |
| Raw-token leak surfaces (API response, DB row, log line, git history) | Structural tests scan each surface for the actual token value | `tests/security/test_t103_security_verification.py` (7 dedicated tests) |

## Security test inventory

`uv run pytest tests/security/` — 46 passed (42 as of the last
final-engineering-summary.md count + 4 new impersonation-resistance tests
added this pass; see `git log` for the exact commit).

## What is explicitly NOT claimed (residual, out of scope this release)

See [threat-model.md](threat-model.md) for the full, disclosed boundary.
Summary — none of the following are solved by this release:

- **Same-OS-user compromise**: another process running as the same macOS
  user can read `local-secrets/approval_tokens.raw.json` directly. Unix
  file permissions (chmod 600) stop a different OS user, not the same one.
- **Compromise of the operator's macOS account itself.**
- **A future release reintroducing external-agent execution** — would
  require its own new ADR revision and Human Gate decision; does not
  inherit Revision 5's acceptance.
- **Physical access to the machine.**
- **Denial of service specifically against approval endpoints** (beyond
  the general rate limit already applied uniformly, PVT-007).
- **DNS-rebinding protection at redirect-resolution time** — the
  private-address check runs at creation time only.

This system is **not** sandboxed and does **not** protect against
operator-account compromise. `docs/threat-model.md` exists specifically so
neither claim is made by accident.

## Deferred, non-mandatory security items (legitimate accepted limitations)

Egress network restriction for agent subprocesses (now largely moot — no
agent subprocess exists in this release at all), DNS-rebinding protection
at redirect-resolution time, a cryptographically tamper-evident audit log,
containerized deployment. None of these were ever a mandatory FR.
