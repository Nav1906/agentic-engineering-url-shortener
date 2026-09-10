# ADR-0001: Application Architecture

## Status

**Accepted.** Approved by the human candidate at Human Gate 4, 2026-09-10.

## Context

The spec requires two clearly separable concerns (Constitution Principle VII):
an **application plane** (URL shortener domain: create/resolve/expire/analytics)
and an **orchestration/control plane** (workflow engine, approvals, policy
enforcement, audit). Both must run "locally, demonstrable" within a 2–3 day
timebox (spec Constraints), without unjustified distributed-system complexity.

## Decision Drivers

- Constitution Principle VII: separate domain logic, API delivery, persistence,
  orchestration, policy enforcement, telemetry, infrastructure concerns.
- 2–3 day timebox; avoid multi-service deployment/ops overhead.
- Reviewer legibility: an assessor must be able to read and trace the system
  without standing up multiple processes.
- FR-201–FR-206 (explicit orchestration model) and FR-101–FR-116 (URL shortener
  domain) must not become entangled in one another's code paths.

## Options Considered

**A. Modular monolith — one process, one deployable, internally layered**
(domain / orchestration / policy / persistence / API / telemetry as separate
Python packages with explicit interfaces between them, no shared mutable state
except through the persistence layer).
- Advantages: single process to run and review; layering still gives the
  required separation of concerns; no network hop between app-plane and
  control-plane, so no distributed-consistency problem to solve.
- Disadvantages: a genuine architectural boundary must be enforced by
  discipline (module boundaries, not process boundaries) rather than the OS.
- Risks: without care, "monolith" drifts into "big ball of mud." Mitigated by
  the explicit package layout below and interface contracts in data-model.md.
- Implementation impact: low — matches Option 1 ("Single project") in the
  plan-template's Project Structure.
- Assessment implications: reviewer can read one codebase, one `git log`, one
  test run.

**B. Two separate services (app-plane API service + control-plane orchestration
service), communicating over HTTP/a local socket.**
- Advantages: closest to how a real production system might eventually split;
  process-level enforcement of the boundary.
- Disadvantages: two processes to start/stop/reason about for a local
  demonstration; introduces a real network boundary and its failure modes
  (partial failure, retries across the boundary) that add complexity not
  required by any specific requirement; doubles the deployment/quickstart
  surface within the timebox.
- Risks: distributed-system complexity the constitution and spec Constraints
  explicitly warn against introducing without justification.
- Implementation impact: high relative to the timebox.
- Assessment implications: harder for a reviewer to run end-to-end quickly.

**C. Full microservices (per-capability services) with a message broker.**
- Disadvantages: entirely disproportionate to a 2–3 day, single-operator
  prototype; explicitly excluded by spec Constraints and Constitution
  Principle VII.
- Rejected without further analysis.

## Decision

**Option A — modular monolith**, one Python process, with these top-level
packages under `src/`: `domain/` (URL shortener logic), `orchestration/`
(workflow engine, dependency graph, state machine), `policy/` (policy manifest
evaluation), `api/` (FastAPI routers, request/response schemas), `persistence/`
(SQLite access layer, shared by domain and orchestration but through distinct
schemas/tables), `observability/` (audit event writer, metrics queries).

## Rationale

Satisfies Constitution Principle VII's separation-of-concerns requirement
through module boundaries and distinct persistence schemas, without paying the
operational cost of a second process/service inside a 2–3 day timebox. The
app-plane/control-plane distinction (spec System Context) is real and enforced
at the code and data-schema level, just not at the process level — which is the
right level of rigor for a demonstrability-focused prototype (Constitution
Principle VII: "distinguish production-grade discipline from production-scale
infrastructure").

## Consequences

- **Positive**: single quickstart command; single test run; simpler crash-
  recovery story (one process, one persistence file); easier for a reviewer to
  trace a request end-to-end.
- **Negative**: the app-plane/control-plane boundary is enforced by code
  review discipline and module structure, not the OS — a future production
  evolution would need to re-verify no accidental coupling crept in.
- **Operational**: one process to run (`uvicorn`), one SQLite file to inspect.
- **Testing**: contract tests can run against the same in-process app (via
  FastAPI's `TestClient`) without spinning up a second service — faster CI/
  local test loop.
- **Governance**: any later split into real services would itself be a
  material architecture change requiring a new ADR and impact analysis per
  FR-306.

## Risks and Mitigations

- **Risk**: module boundaries erode over time. **Mitigation**: distinct
  SQLite table ownership per package (see data-model.md) and no direct
  cross-package SQL — only through each package's own persistence interface.

## Reversibility

**Moderate.** Splitting into two services later is a bounded, well-understood
refactor (the module boundaries already exist); it is not a rewrite. Recorded
here as the honest reversibility assessment, not a promise it will happen.

## Traceability

- Requirements: FR-201–FR-206 (orchestration), FR-101–FR-116 (domain),
  Constitution Principle VII.
- Specification sections: System Context (plan.md §1), Constraints.
- Plan sections: plan.md Project Structure.
- Expected tasks: engineering-baseline and walking-skeleton task groups
  (`/speckit-tasks`, not yet generated).

## Validation

Validated by: (a) the quickstart guide running end-to-end from a single
process; (b) a static check (task-stage validation, not yet implemented) that
no package imports another package's persistence internals directly; (c)
reviewer inspection of the package layout against this ADR.
