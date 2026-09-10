# ADR-0008: Observability and Audit Model, and MTTR Definition

## Status

**Accepted.** Approved by the human candidate at Human Gate 4, 2026-09-10.
**No numeric MTTR target is proposed in this ADR** — per the
Human Gate 3 correction, the definitional framework below must exist and be
implemented before any number is proposed. That number, when proposed, will
come in a future amendment, not here.

## Context

FR-601–FR-606 and Constitution Principle IX require: a correlation/run
identifier per execution, full state-transition/decision/approval/retry/
replanning audit events, actor/action/timestamp/artifact/result/reason on
every event, demonstration-vs-production labeling, and — per spec's removed
`SC-004`/`PVT-004` — a precisely defined MTTR metric (population, start/end
events, exclusions, unrecovered-failure reporting) *before* any target number.

## Decision Drivers

- Audit integrity: events must be tamper-evident enough for a reviewer to
  trust them as evidence (Constitution Principle XI), within prototype scope
  (not a cryptographic audit log — disclosed as a limitation, not solved).
- MTTR must be defined precisely enough to compute correctly and to exclude
  unrecovered failures from the denominator (guide's explicit MTTR formula
  and rule).
- No new infrastructure (no external tracing/metrics backend) — reuse the
  persistence layer (ADR-0003).

## Options Considered

**A. `audit_events` table in the same SQLite database, append-only (no
UPDATE/DELETE from application code), with structured columns
(`correlation_id`, `actor_type`, `action`, `timestamp`, `affected_artifact`,
`result`, `reason`) plus a JSON `detail` column for event-specific data;
metrics computed via SQL aggregate queries over this table and
`workflow_stage`/`workflow_instance`.**
- Advantages: reuses existing infrastructure (no new store); append-only
  discipline is enforceable by simply never issuing UPDATE/DELETE against
  this table in application code, and verifiable by a reviewer grepping for
  any such statement; SQL aggregation makes success-rate/failure-rate/retry-
  frequency/MTTR all straightforward, reviewer-runnable queries.
- Disadvantages: not cryptographically tamper-evident (no hash chaining) —
  disclosed as a prototype-scope limitation, not claimed as solved.
- Risks: none material beyond the disclosed limitation.
- Implementation impact: low.
- Assessment implications: a reviewer can run the actual SQL queries
  themselves to verify a reported metric, rather than trusting a generated
  summary — directly serving Constitution Principle XI.

**B. Structured JSON log lines to stdout/a log file, parsed for metrics.**
- Disadvantages: weaker queryability than SQL; correlating events across a
  workflow instance requires custom parsing rather than a `WHERE
  correlation_id = ?` query; duplicates data already needed in the database
  anyway (state transitions must be persisted regardless, per FR-204).
- Rejected as the primary mechanism, though ordinary application logs
  (distinct from audit events) are still emitted for operational
  observability (e.g., the analytics-degradation signal, FR-115) — logs and
  the audit table serve different purposes and both exist, but audit events
  are the evidence-of-record.

## Decision

**Option A**, plus the following precise MTTR definition (satisfying the
Human Gate 3 correction before any target number is proposed):

- **Failure-detected timestamp**: the timestamp of the audit event recording
  a stage's transition to `failed_transient` or `failed_permanent`.
- **Recovery-start timestamp**: the timestamp of the first retry attempt (or
  fallback invocation) following failure detection.
- **Recovery-complete timestamp**: the timestamp of the audit event recording
  that same stage reaching `succeeded` (or a defined fallback's own success),
  where the recovery is attributable to the same failure episode (tracked via
  a `recovery_of_event_id` foreign key on the recovering audit event — not
  inferred by proximity in time).
- **Individual recovery duration**: `recovery-complete − failure-detected`.
- **Recovery mechanism used**: recorded per event (`retry` / `fallback`).
- **Recovered vs. unrecovered status**: a failure is `recovered` only if a
  `recovery-complete` event with a matching `recovery_of_event_id` exists;
  otherwise `unrecovered` — including any failure whose workflow instance
  reached `safe_stopped` without resolution.
- **Measurement population**: only `recovered` failure events are included in
  the MTTR numerator/denominator, per the guide's explicit rule.
- **MTTR**: `(sum of individual recovery durations for recovered events) ÷
  (count of recovered events)`.
- **Exclusions**: `unrecovered` events are counted and reported separately
  (never blended into the MTTR denominator, per the guide's explicit rule);
  events from automated test/demonstration runs are labeled as such and never
  presented as production statistics (FR-604, Constitution Principle IX).
- **Demonstration-data limitation**: disclosed explicitly wherever MTTR is
  reported — this is measured from a local, single-operator prototype run,
  not production traffic.

Correlation identifiers: every `workflow_instance` row's primary key **is**
the correlation identifier (FR-601) — no separate ID scheme needed, since
every audit event carries `workflow_instance_id`.

## Rationale

Satisfies audit-event completeness (FR-602) and gives MTTR (and the other
required metrics: success rate, failure rate, retry frequency, rollback/
compensation frequency, unrecovered-failure count) a precise, SQL-computable,
reviewer-verifiable definition — directly resolving the Human Gate 3 finding
that a number without this definitional work is premature.

## Consequences

- **Positive**: every reported metric traces back to a runnable SQL query
  against real rows, not a narrative claim.
- **Negative**: append-only discipline is a code-review convention, not
  enforced by a database-level trigger in this prototype — disclosed as a
  limitation, not hidden.
- **Operational**: no new infrastructure.
- **Testing**: an MTTR test can construct a known failure-then-recovery
  sequence and assert the computed MTTR matches the expected value exactly.
- **Governance**: unrecovered-failure count is always reported alongside
  MTTR, never omitted, per the guide's explicit rule and FR-603.

## Risks and Mitigations

- **Risk**: `recovery_of_event_id` linkage is implemented incorrectly,
  silently mis-attributing a recovery to the wrong failure. **Mitigation**:
  a dedicated orchestration test constructs an overlapping-failure scenario
  (two failures close in time) and asserts correct attribution.

## Reversibility

**High.** Metric-computation queries are independent of the orchestration
engine's core logic; refining the MTTR definition later (e.g., adding a
tolerance window) does not require a data-model migration beyond adding
columns.

## Traceability

- Requirements: FR-601–FR-606, Constitution Principle IX.
- Specification sections: `PVT-004` (number removed at Human Gate 3, this ADR
  supplies the prerequisite definition), Success Criteria `SC-004`.
- Plan sections: plan.md §7 (Observability).
- Expected tasks: audit-trail, logs/metrics/traces, MTTR-instrumentation task
  groups.

## Validation

**Planned, not yet executed** (corrected at Human Gate 4 review): a test
asserting a constructed recovered-failure sequence produces the exact
expected MTTR value, and a second test asserting an unrecovered failure is
excluded from that calculation and reported separately. No code exists yet;
when these are executed, actual output will be retained as evidence — this
section describes what must pass, not what has passed.
