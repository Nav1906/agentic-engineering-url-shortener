# Risk Register

**Purpose**: one of the 13 required `/speckit-converge` outputs (guide
Section 22) — consolidates residual risks already disclosed piecemeal in
[threat-model.md](threat-model.md), [security-summary.md](security-summary.md),
[reliability-summary.md](reliability-summary.md), and
[final-engineering-summary.md §19](final-engineering-summary.md) into a
single register with likelihood/impact framing. No new risk is introduced
here that isn't already disclosed elsewhere — this is a consolidation, not
new analysis.

| ID | Risk | Likelihood | Impact | Mitigation / Disposition | Status |
|---|---|---|---|---|---|
| R-001 | Same-OS-user process reads `local-secrets/approval_tokens.raw.json` directly | Low (requires local code execution as the same user) | High (full credential compromise) | Unix chmod 600 stops a different user, not the same one; accepted as out of scope per Human Gate 4 (ADR-0006 Revision 5) | **Accepted, disclosed** |
| R-002 | Compromise of the operator's macOS account | Low | High | Not addressed; standard limitation for any local dev tool; accepted per Human Gate 4 | **Accepted, disclosed** |
| R-003 | A future release reintroduces external-agent subprocess execution without redoing the credential-isolation analysis | Low (requires a deliberate future code change) | High if it happens without a new ADR | Requires its own new ADR revision + Human Gate decision; does not inherit Revision 5's acceptance | **Accepted, disclosed, structurally gated** |
| R-004 | DNS-rebinding attack against the private-address rejection control (address resolves differently at redirect time vs. creation time) | Low-Medium | Medium (SSRF-shaped) | Not implemented this release; disclosed explicitly adjacent to the control (`plan.md §8`) | **Deferred, non-mandatory, disclosed** |
| R-005 | Reaper (stale-worker detection) is periodic, not instantaneous | Low | Low-Medium (bounded delay in detecting a dead worker) | Sweep interval bounds the detection latency; not eliminated by design | **Accepted, bounded** |
| R-006 | SQLite as the sole datastore under concurrent write load at a scale beyond this prototype's demonstration scope | Low (out of scope — single local process, ADR-0002/0003) | Medium if scaled without redesign | `busy_timeout` + bounded retry on every writer path; explicitly not a production-scale claim (Constitution Principle VII) | **Accepted, scope-bounded** |
| R-007 | Audit log is append-only by code-review convention, not a DB-level constraint | Low | Medium (tamper risk if a future contributor adds an UPDATE/DELETE path) | Disclosed in ADR-0008 and `security-reliability-observability.md` checklist CHK079; a tamper-evident log is a deferred, non-mandatory item | **Deferred, non-mandatory, disclosed** |
| R-008 | No egress network restriction was ever implemented for agent subprocesses | N/A this release | N/A — moot | Moot: no agent subprocess exists in this release's trusted boundary at all (ADR-0006 Revision 5, T102) | **Moot by scope exclusion** |
| R-009 | Rate limiting (60 req/min/IP) does not specifically harden the approval endpoints against a targeted DoS beyond the general limit | Low | Low | General rate limit applies uniformly; a dedicated approval-endpoint limit was never a mandatory FR | **Accepted, disclosed** |
| R-010 | Independent Final Assessment (guide Section 23) has not yet run as of this register's creation | N/A (process risk, not a system risk) | Could surface additional findings | Scheduled as the next step in this convergence pass, using a fresh reviewer agent with no implementation-session context | **Open — tracked, in progress** |

## Risk disposition summary

- **9 of 10** risks are accepted, disclosed, bounded, or moot by design —
  none of them trace to a mandatory functional requirement (FR) left
  unsatisfied.
- **1** (R-010) is a process risk tracked for closure within this same
  convergence pass, not a system defect.
- No risk in this register is classified High-likelihood/High-impact.
