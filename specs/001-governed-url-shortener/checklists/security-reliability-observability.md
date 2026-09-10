# Security, Reliability & Recovery, Observability & Auditability Checklist: Agentic Software Engineering System: URL Shortener

**Purpose**: Objectively verifiable quality/readiness checklist for guide
categories 7 (Security), 9 (Reliability and Recovery), 10 (Observability
and Auditability).
**Created**: 2026-09-10
**Feature**: [plan.md §8](../plan.md), [docs/adr/0007-reliability-recovery-policy.md](../../../docs/adr/0007-reliability-recovery-policy.md), [docs/adr/0008-observability-audit-model.md](../../../docs/adr/0008-observability-audit-model.md), [docs/adr/0009-analytics-consistency.md](../../../docs/adr/0009-analytics-consistency.md)

**Review Ownership**: Reviewer-owned. `[x]` = requirements-quality
satisfied, not implementation verified. IDs continue from
`orchestration-governance.md` (last used: CHK059).

## 7. Security

- [ ] CHK060 Is the allowed-URL-scheme list specified as an explicit allow-list with the specific rejected schemes enumerated (not just "malicious schemes")? [Clarity, FR-101, plan.md §8]
- [ ] CHK061 Is the private/internal-address rejection control's actual limitation (no DNS-rebinding protection at resolution time) stated adjacent to the control itself, not only in a separate risk register? [Evidence-integrity, plan.md §8]
- [ ] CHK062 Is the minimum idempotency-key-length control specified together with the explicit disclosure that entropy beyond that floor is the caller's responsibility? [Clarity, plan.md §8]
- [ ] CHK063 Is the rate-limiting target specified as a concrete, proposed number rather than left unquantified? [Measurability, `PVT-007`]
- [ ] CHK064 Is the unauthenticated scope of the domain API (including `DELETE`) stated explicitly, rather than left to be inferred from the absence of an auth requirement? [Clarity, plan.md §8]
- [ ] CHK065 Is the credential-isolation control's current verification status (Rejected mechanism / spike-pending replacement) reflected accurately, with no document implying it is production-ready? [Evidence-integrity, ADR-0006]
- [ ] CHK066 [Gap] Is a dependency/secret-scanning requirement specified as part of release readiness, with a pass/fail outcome defined, not merely "run a scan"?

## 9. Reliability and Recovery

- [ ] CHK067 Are transient and permanent failure classes each defined with concrete example triggers, not left as an abstract distinction? [Clarity, ADR-0007]
- [ ] CHK068 Is the retry ceiling and backoff schedule specified as exact numbers (attempts, wait durations) rather than "a reasonable number of retries"? [Measurability, `PVT-002`]
- [ ] CHK069 Is idempotency required for every repeatable operation named individually (short-link creation, workflow stage retries), with none left unaddressed? [Completeness, FR-406]
- [ ] CHK070 Is the rollback-vs-compensation decision rule specified per operation class (uncommitted-transaction vs. externally-observed), not as a blanket policy? [Clarity, ADR-0007]
- [ ] CHK071 Is safe-stop specified as resumable only via an explicit, authorized human/operator action — never an automatic retry — with this distinction stated unambiguously? [Clarity, Constitution Principle VIII]
- [ ] CHK072 Is the SQLite write-contention response (busy_timeout + bounded retry) specified for every writer path individually (domain, orchestration, audit, analytics drain), with none silently assumed to be exempt? [Coverage, ADR-0007]
- [ ] CHK073 Is the per-subprocess-type timeout set specified with a distinct value per type (internal/pytest/Claude), rather than one blanket number applied regardless of realism? [Measurability, `PVT-003`]
- [ ] CHK074 [Gap] Is a requirement established for what evidence constitutes "resumption correctly worked" (e.g., specific state fields compared pre/post-interruption), rather than a general claim?

## 10. Observability and Auditability

- [ ] CHK075 Is the correlation identifier specified as the workflow instance's own primary key (not a separately-generated, potentially-divergent ID)? [Consistency, FR-601]
- [ ] CHK076 Are the required audit-event fields (actor type, action, timestamp, affected artifact/state, result, reason) each individually named as mandatory, with none optional? [Completeness, FR-602]
- [ ] CHK077 Is the MTTR calculation specified with a precise definition of its measurement population (recovered events only), excluding unrecovered failures from the denominator, before any target number is proposed? [Measurability, ADR-0008, avoids presenting an undefined metric as if it were rigorous]
- [ ] CHK078 Is a rule specified for labeling demonstration-derived metrics as such, with an explicit prohibition on presenting them as production statistics? [Clarity, FR-604]
- [ ] CHK079 Is the append-only discipline for audit events specified as a stated constraint (no UPDATE/DELETE path), with its current enforcement level (code-review convention, not a DB-level constraint) disclosed rather than overstated? [Evidence-integrity, ADR-0008]
- [ ] CHK080 [Gap] Is a specified minimum retention period established for audit evidence, or is this explicitly left open pending a future decision?

## Notes

- Mark items `[x]` only after review confirms the requirement-quality criterion is satisfied.
- `/speckit-implement` reads checklist checkbox state as a gate and must not modify markers.
- Traceability self-check: of the 21 items above (CHK060–CHK080), 19 carry an explicit reference or `[Gap]` marker (90%).
