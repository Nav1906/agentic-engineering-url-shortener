# ADR-0002: Programming Language, Web Framework, and Testing Strategy

## Status

**Accepted.** Approved by the human candidate at Human Gate 4, 2026-09-10.

## Context

Spec Constraints forbid choosing a language/framework before this stage. The
guide's ADR-candidate list separately names "Programming language and
framework" (#2) and "Testing strategy" (#13); they are combined here because
the testing-tool choice is materially derivative of the language choice, not
an independent architectural fork.

## Decision Drivers

- 2–3 day timebox: minimize setup/build-tooling overhead.
- FR requires versioned, executable API/schema contracts (spec §"Architecture");
  the language/framework choice should make schema-as-code natural, not bolted
  on.
- Constitution Principle IV: red-green-refactor TDD must be practical, not
  awkward, in the chosen stack.
- Reviewer familiarity: a mainstream, widely-readable stack lowers the bar for
  an assessor to verify claims independently (Constitution Principle XI).

## Options Considered

**A. Python 3.12 + FastAPI + Pydantic v2 + pytest.**
- Advantages: Pydantic models double as runtime validation and OpenAPI schema
  generation — directly satisfies the "versioned API and schema deliverables"
  requirement with no separate schema-authoring step to drift out of sync;
  `pytest` is a minimal, widely-known TDD-friendly test runner; FastAPI's
  `TestClient` supports fast in-process contract tests (no network needed).
- Disadvantages: Python's `asyncio` concurrency model has real but manageable
  sharp edges (e.g., blocking calls inside async handlers); dynamic typing
  requires discipline (mitigated by Pydantic + type hints + `mypy` in CI).
- Risks: none material at this scale.
- Implementation impact: low; extremely common stack, minimal boilerplate.
- Assessment implications: broadly readable by most reviewers.

**B. TypeScript + Node.js + Express/Fastify + Zod + Vitest.**
- Advantages: comparable schema-as-code story via Zod; native async I/O.
- Disadvantages: needs an explicit OpenAPI-generation step from Zod schemas
  (not as turnkey as FastAPI+Pydantic); slightly more build tooling
  (TypeScript compilation) for the same timebox.
- Risks: none material.
- Implementation impact: comparable to Option A, marginally higher setup cost.
- Assessment implications: equally readable to a broad reviewer audience.

**C. Java/Kotlin + Spring Boot + JUnit.**
- Disadvantages: materially heavier build tooling (Gradle/Maven), slower
  local iteration loop, disproportionate ceremony for a 2–3 day prototype.
- Rejected without further analysis.

## Decision

**Option A** — Python 3.12, FastAPI, Pydantic v2, `pytest` (+`pytest-asyncio`
for orchestration/async tests), `httpx`'s `TestClient` (via FastAPI) for
contract/integration tests, `mypy` for static typing as a lightweight quality
gate (not a hard CI blocker at prototype scale, but run and reported).

## Rationale

Minimizes the gap between "schema" and "code" (directly serves the spec's
explicit versioned-contract requirement), keeps the TDD loop fast (Constitution
Principle IV), and is broadly legible to reviewers (Constitution Principle XI).
Option B is a reasonable, only-marginally-worse alternative — recorded for
transparency, not because it was a close call driven by anything specific to
this project's requirements.

## Consequences

- **Positive**: contract tests can be written before any server is actually
  running (in-process `TestClient`), enabling genuine red-green-refactor for
  API behavior (FR-101–FR-116) from day one.
- **Negative**: ties the team (the human candidate + Claude Code) to Python's
  ecosystem conventions and its `asyncio` execution model for the orchestration
  engine (ADR-0005).
- **Operational**: single `pip`/`uv` environment; no separate build step.
- **Testing**: unit (domain), contract (API, via `TestClient`), orchestration
  state-transition, and security tests all run under `pytest`.
- **Governance**: any later language migration is a material architecture
  change requiring its own ADR and full impact analysis (FR-306).

## Risks and Mitigations

- **Risk**: dynamic typing hides a class of bugs static languages catch.
  **Mitigation**: `mypy` run as part of validation (FR-606 requires it be
  actually executed, not merely configured); Pydantic validates all I/O
  boundaries at runtime regardless of type-hint discipline.

## Reversibility

**Low-to-moderate.** A full language rewrite is expensive; however, because
ADR-0001's modular boundaries are enforced at the package/schema level, a
future rewrite of one package (e.g., just the orchestration engine) without
touching others is more tractable than a full-system rewrite would be.

## Traceability

- Requirements: spec Architecture section (API/schema deliverables),
  Constitution Principle IV (TDD), Principle VII.
- Specification sections: Specification Rules (no premature tech choice —
  honored by deferring this decision to this ADR).
- Plan sections: plan.md Technical Context.
- Expected tasks: engineering-baseline task group.

## Validation

**Planned, not yet executed** (corrected at Human Gate 4 review — no code
exists yet): a `pytest` run with contract tests for at least one domain
endpoint. When run, its actual output will be retained as evidence per
FR-606 — not merely described as passing.
