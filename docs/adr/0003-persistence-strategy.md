# ADR-0003: Persistence Strategy

## Status

**Accepted.** Approved by the human candidate at Human Gate 4, 2026-09-10.

## Context

The system needs durable storage for: short links, idempotency records,
analytics summaries + outbox, workflow instances/stages/dependency edges,
decision lineage, approval decisions, policy evaluations, and audit events —
all of which must survive a process restart (FR-116, FR-204, FR-205) and remain
correct under concurrent access (FR-110). Spec Constraints exclude a hosted/
cloud database and require the system to "run locally, demonstrable."

## Decision Drivers

- Durability across restarts (FR-116, FR-204, FR-205).
- Concurrency correctness without external coordination infrastructure
  (FR-110).
- Atomicity for the idempotency check-and-insert pattern (FR-112/113) and the
  analytics outbox pattern (ADR-0009).
- No hosted/cloud dependency (spec Constraints).
- Timebox: minimize setup/operational surface.

## Options Considered

**A. SQLite, single file, WAL (write-ahead log) mode.**
- Advantages: zero external process, true ACID transactions, UNIQUE
  constraints give idempotency and short-code uniqueness "for free" at the
  storage layer; WAL mode allows one writer + multiple concurrent readers
  without application-level locking for reads; a single file is trivial to
  inspect, back up, or reset for a reviewer.
- Disadvantages: a single writer at a time (WAL mode does not remove this);
  under high write concurrency this would eventually bottleneck — not a
  concern at prototype scale (spec explicitly excludes production-scale
  capacity planning).
- Risks: write-serialization could, in principle, interact with the
  orchestration engine's parallel-stage writes; mitigated by keeping
  individual transactions short and using `BEGIN IMMEDIATE` for
  writer-intent transactions to fail fast rather than deadlock.
- Implementation impact: low; standard library `sqlite3`, no new
  infrastructure.
- Assessment implications: a reviewer can open the `.db` file directly with
  any SQLite browser to verify claims — strong fit with Constitution
  Principle XI.

**B. PostgreSQL, run via a local Docker container.**
- Advantages: closer to a typical production choice; richer concurrency model.
- Disadvantages: requires Docker (or a local Postgres install) as a
  prerequisite, adding a setup step and a second process to the quickstart;
  disproportionate to a single-operator, 2–3 day prototype.
- Risks: adds a dependency-availability failure mode (FR-109-style) that
  doesn't need to exist for this prototype's scope.
- Implementation impact: moderate — connection pooling, migrations tooling.
- Assessment implications: raises the bar for a reviewer to run the system
  locally (needs Docker).

**C. Separate stores per concern (e.g., SQLite for domain data, a separate
file-based event log for audit events).**
- Disadvantages: splits transactional guarantees across stores, which
  directly undermines the outbox pattern's atomicity requirement (ADR-0009)
  and adds cross-store consistency problems with no offsetting benefit at
  this scale.
- Rejected without further analysis.

## Decision

**Option A** — a single SQLite database file (`data/app.db`, gitignored,
created on first run), WAL mode enabled, one connection pool shared across the
process (short-lived connections per request/stage, not one long-lived global
connection), with each package (per ADR-0001) owning a distinct table
namespace: `domain_*` (short links, idempotency records, analytics),
`orchestration_*` (workflow instances, stages, dependency edges, decision
lineage), `policy_*` (policy evaluations, exceptions), `audit_events`.

## Rationale

Satisfies every durability and concurrency-correctness requirement using only
the standard library, with zero setup cost for a reviewer, and makes the
idempotency and analytics-outbox atomicity guarantees (both required by the
approved spec) straightforward to implement correctly using ordinary SQL
transactions rather than a distributed-transaction protocol.

## Consequences

- **Positive**: no external dependency to install; a reviewer can inspect the
  entire persisted state with `sqlite3 data/app.db`.
- **Negative**: single-writer serialization is a real (if currently
  inconsequential) scalability ceiling — disclosed, not hidden.
- **Operational**: back up = copy one file; reset = delete one file.
- **Testing**: tests can use an ephemeral SQLite file (or `:memory:` for pure
  unit tests) with zero test-infrastructure setup.
- **Governance**: moving to a client-server database later is a material
  change requiring its own ADR, migration plan, and impact analysis (FR-306).

## Risks and Mitigations

- **Risk**: a long-running transaction (e.g., a slow orchestration stage)
  blocks other writers. **Mitigation**: keep each transaction scoped to a
  single logical operation (one stage transition, one idempotency check, one
  outbox drain batch), never spanning a network call or external I/O wait.
- **Risk**: WAL file growth / checkpoint behavior. **Mitigation**: documented
  as a known prototype-scope limitation, not addressed with production-grade
  tuning (Constitution Principle VII).

## Reversibility

**Moderate.** SQLite's SQL dialect is close enough to PostgreSQL's that a
future migration is a bounded, well-understood effort (schema translation +
connection-layer swap), not a rewrite — but it is real work, not free.

## Traceability

- Requirements: FR-102, FR-108–FR-116, FR-110, FR-204, FR-205, FR-601–FR-606.
- Specification sections: Constraints (no hosted DB), Assumptions
  (single-operator/local deployment).
- Plan sections: plan.md Technical Context (Storage).
- Expected tasks: engineering-baseline, persistence-abstraction task groups.

## Validation

**Planned, not yet executed** (corrected at Human Gate 4 review — no code
exists yet, so nothing here has actually run): persistence tests issuing
concurrent write *attempts* from multiple callers to confirm SQLite's
serialization is correctly surfaced to the application (each write completes
in isolation — atomically and durably — with no update silently lost to a
race), rather than tests that mistakenly assume SQLite executes writes in
parallel at the row level (it does not — **writes are serialized by SQLite's
single-writer lock; only readers run concurrently under WAL mode**, per this
ADR's own Decision). Also planned: a restart-recovery test that stops and
restarts the process mid-workflow and confirms state is unchanged (FR-204/
FR-205). When executed, actual output will be retained as evidence.
