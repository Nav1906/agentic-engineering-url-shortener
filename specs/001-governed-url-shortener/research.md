# Phase 0 Research: Agentic Software Engineering System: URL Shortener

**Feature**: [spec.md](./spec.md) | **Constitution**: `.specify/memory/constitution.md` v1.0.0
**Date**: 2026-09-10 | **Status**: Feeds `docs/adr/` (all ADRs Proposed, not Accepted)

This resolves every `NEEDS CLARIFICATION` in plan.md's Technical Context and the
cross-cutting research questions behind the ADRs. Each material technology
decision's full options/rationale/consequences live in its own ADR — this file
holds the comparative groundwork and the topics that don't rise to their own ADR.

## Format

Each entry: **Decision** / **Rationale** / **Alternatives considered**.

---

## 1. Overall technology stack (feeds ADR-0002, ADR-0003, ADR-0010)

**Decision**: Python 3.12, FastAPI (ASGI web framework), Pydantic v2 (schema
validation, doubling as the OpenAPI schema source), SQLite (via the standard
`sqlite3` module in WAL mode, no ORM), `pytest` + `pytest-asyncio` for testing,
`uvicorn` as the local ASGI server.

**Rationale**: The 2–3 day timebox and Constitution Principle VII ("avoid
complexity not justified by requirements or demonstrability") rule out anything
requiring external infrastructure (a separate database server, a message broker,
a workflow-engine cluster). FastAPI + Pydantic gets the guide's required
"versioned API and schema deliverables" (Section 9.2) essentially for free — the
same Pydantic models are both the runtime validation and the generated OpenAPI
schema, which keeps the contract from drifting out of sync with the
implementation. SQLite in WAL mode gives real ACID transactions, a UNIQUE
constraint for durable idempotency (Constitution Principle VIII), and a single
on-disk file that satisfies "must run locally, demonstrable" (spec Constraints)
without any setup step beyond running the app.

**Alternatives considered**: Node.js/TypeScript + Express/Fastify + a
JSON-Schema library — comparable fit, rejected only because Python's standard
library `sqlite3` + Pydantic combination needs less glue code for the
schema-is-the-contract property. A JVM stack (Spring Boot) — much heavier
startup/build tooling for a 2–3 day timebox, rejected. Full detail and the
Decision Drivers/Consequences table are in **ADR-0002**.

## 2. Orchestration engine build-vs-buy (feeds ADR-0005)

**Decision**: Hand-rolled, in-process, SQLite-persisted workflow engine — not an
external orchestration product (Temporal, Airflow, Prefect, Camunda, AWS Step
Functions).

**Rationale**: External orchestration engines are built for production-scale,
multi-tenant, distributed workloads; standing one up (even "locally") means a
second runtime, a second data store, and a learning-curve tax that does not fit
a 2–3 day timebox and directly contradicts Constitution Principle VII and the
spec's Constraint against "unjustified distributed-system complexity." A
hand-rolled engine is also **more legible to an assessment reviewer** — the
dependency graph, state transitions, retry/backoff, and safe-stop logic are
plain, readable application code instead of hidden behind a third-party engine's
internals, which directly serves Constitution Principle IX (auditability) and
Principle XI (evidence must be independently verifiable). Full options/consequences
in **ADR-0005**.

**Alternatives considered**: Temporal (rejected: requires a server process +
its own persistence store, days of ramp-up); a Python DAG library like
`prefect`/`dagster` in local-only mode (rejected: still designed around a
scheduler service model that's overkill for one workflow type at prototype
scale); a pure in-memory state machine with no persistence (rejected outright —
directly violates FR-204's persisted-state requirement and the constitution's
crash-recovery expectations).

## 3. Short-code generation strategy (feeds ADR-0004)

**Decision**: Random base62 string, 7 characters, generated client-side-of-the-
persistence-layer and inserted with a UNIQUE constraint; on a collision (`sqlite3.
IntegrityError`), regenerate and retry, bounded to 5 attempts before surfacing a
`503`-class "temporarily unable to allocate a short code" error.

**Rationale**: At 62^7 (~3.5 trillion) possible codes, collision probability at
prototype-scale volumes is negligible (birthday-bound collision risk stays well
under 0.01% even at hundreds of thousands of active codes), so a bounded
retry-on-conflict loop is simpler and more honest than pre-reserving code ranges
or adding a coordination service. This satisfies FR-102 (uniqueness among active
codes) without introducing a single point of coordination beyond SQLite's own
UNIQUE index, which is already required for other reasons (idempotency records).

**Alternatives considered**: Sequential integer ID encoded as base62 (rejected:
reveals creation order/volume, and — more importantly — is harder to reconcile
with FR-108's requirement that resubmitting the same destination URL without a
key MUST always mint a *new* code, since a purely sequential+encode scheme adds
no value over random here and couples code allocation to a single monotonic
counter that becomes a minor contention point under concurrent writes). A
deterministic hash of the destination URL (rejected outright: this would make
the same URL always produce the same code, directly contradicting FR-108's
resolved behavior from AMB-001 — same URL, no key, submitted twice, must yield
two different codes).

## 4. Idempotency mechanism (feeds ADR-0003, applies FR-112–FR-116)

**Decision**: A dedicated `idempotency_records` table keyed by
`(idempotency_key)` UNIQUE, storing a hash of the validated request payload and
the resulting `short_code`. On a request carrying a key: `SELECT` first; if
found, compare the stored payload hash to the incoming validated payload's hash
— match → return the stored result (FR-112); mismatch → `409 Conflict` (FR-113);
not found → proceed to normal creation inside the same transaction that inserts
the new `idempotency_records` row, so the create-and-record-key step is atomic
(no window where a concurrent duplicate request could both "miss" the lookup and
both succeed in creating — see ADR-0003 for the exact transaction/locking design
satisfying FR-110's concurrency-correctness requirement).

**Rationale**: This is the standard, well-understood pattern for idempotency
keys (used by Stripe and similar APIs) and maps directly onto SQLite's
transactional guarantees without needing an external lock service. Retention is
indefinite per FR-116 (a disclosed prototype-scope choice) — no TTL/cleanup job
is in scope.

**Alternatives considered**: An in-memory (process-local) idempotency cache —
rejected outright, does not survive a restart, directly violates FR-116's
"retained... surviving process restarts" requirement.

## 5. Async execution and synchronization within a single process (feeds ADR-0005)

**Decision**: Python `asyncio`, using `asyncio.gather()` for fan-out of
independent, ready-to-run stages, with a synchronization barrier implemented as
"a stage's preconditions are satisfied only when every stage it depends on has
reached a terminal per-stage status" (checked via a SQL query against the
persisted stage table, not in-memory state) before that stage is scheduled.

**Rationale**: `asyncio` is already implied by FastAPI's async request handling,
so no second concurrency model needs to be introduced. Because the
synchronization check is a SQL query against durable state rather than an
in-memory flag, a process restart mid-workflow does not lose track of which
stages were actually complete — the next scheduler tick simply re-derives
"what's ready to run" from the database, which is what makes resumption after a
crash (a required capability) tractable without extra bookkeeping.

**Alternatives considered**: OS-level multiprocessing/threading for true
parallelism — rejected: the actual "stages" here are I/O-bound (database calls,
simulated external steps), not CPU-bound, so `asyncio` concurrency is sufficient
and avoids the complexity of cross-process shared state.

## 6. Authentication mechanism for the approval surface (feeds ADR-0006, resolves
   AMB-005's deferred mechanism)

**Decision**: Static, locally-generated bearer credentials per role
(`reviewer_approver`, `release_owner`), stored in a file outside the
orchestration/agent process's own read path (see ADR-0006 for the exact
isolation mechanism), presented as an `Authorization: Bearer <token>` header by
a small, separate, human-invoked CLI (`scripts/approve.py`) — never by any
automated/agent code path.

**Rationale**: A real OAuth2/OIDC provider is disproportionate for a local,
single-operator, 2–3 day prototype and would itself become the majority of the
implementation effort. A static, per-role credential *is* still a verified
credential (FR-308) rather than a caller-supplied name, and — critically — the
isolation mechanism (below, ADR-0006) is what actually satisfies "credentials
isolated from agent access," not the choice of token format.

**Alternatives considered**: HTTP Basic Auth against an in-memory user table —
materially equivalent to bearer tokens for this purpose, no meaningful
difference; rejected only for being a less idiomatic fit with FastAPI's
dependency-injection auth patterns. A full OIDC provider (e.g., Keycloak) —
rejected as disproportionate to the timebox.

## 7. Analytics durability pattern (feeds ADR-0009, resolves AMB-007's deferred
   mechanism)

**Decision**: A durable outbox: every successful redirect appends a row to an
`analytics_outbox` table **in the same SQLite transaction that reads the short
link for resolution** (so the redirect and the durable intent-to-count share
one atomic commit), then a background task drains the outbox into the
`short_link_analytics_summary` table asynchronously. See ADR-0009 for the full
completeness-status state machine (including the `incomplete` sticky state for
genuinely unrecoverable loss).

**Rationale**: This is the one place a naive "just increment async and hope"
design would violate the explicit instruction that "lost historical counts must
not become 'complete' merely because storage recovers" — the outbox pattern
makes durability of the *intent* to count atomic with the redirect decision
itself, so the only way a count is ever truly and permanently lost is if the
outbox write itself fails (extremely rare, and detectable), not merely because
the *summary table* update lags.

**Alternatives considered**: Fire-and-forget in-memory increment with no
durability at all — rejected, this is exactly the naive design the trade-off
decision (AMB-007, FR-105) was written to rule out, since a crash before the
increment is applied would silently and permanently lose it with no trace.
Fully synchronous increment in the same request path — rejected, this is the
option AMB-007 explicitly rejected in favor of redirect availability.

## 8. Compliance/change-control policy model scope for this prototype

**Decision**: A small, versioned, in-repository policy manifest
(`config/policies.yaml`), evaluated by a policy-check stage inside the
orchestration workflow (not an external policy engine like OPA), covering only
the policy domains this prototype can meaningfully demonstrate: security
(dependency/secret-scan gate), architecture/change-control (material-change
requires an approved ADR or spec amendment), and release-readiness (mandatory
gates from FR-301 must all be non-`FAIL`).

**Rationale**: Constitution Principle VI requires a versioned policy model and
`PASS`/`FAIL`/`EXCEPTION-REQUESTED`/`NOT-APPLICABLE` outcomes, but does not
require an external policy-engine product — a small versioned manifest plus a
policy-evaluation stage in the workflow is sufficient to demonstrate the
required mechanics (blocking on `FAIL`, requiring approval for
`EXCEPTION-REQUESTED`) without importing a general-purpose policy DSL that would
be disproportionate to this prototype's scope.

**Alternatives considered**: Open Policy Agent (OPA)/Rego — rejected as
disproportionate infrastructure for a single-workflow-type prototype; the
manifest-plus-evaluator approach demonstrates the same governance mechanics at a
fraction of the setup cost.

---

## Outstanding NEEDS CLARIFICATION

None remain unresolved by this research — all Technical Context fields in
`plan.md` are filled. Where a *number* rather than a *mechanism* is still open
(e.g., the exact analytics latency budget, retry ceiling/backoff, MTTR
population), that is intentionally deferred to the corresponding ADR's Decision
section as a **proposed, human-approvable number** — consistent with the
specification's Proposed Validation Target handling, not left as a research gap.
