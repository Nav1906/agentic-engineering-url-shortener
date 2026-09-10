# Agentic Software Engineering System: URL Shortener Constitution

## Project Context

This repository is an engineering assessment submission. The URL shortener is the
demonstration domain; it is not the primary object of evaluation. The central
differentiator under review is a governed, stateful, non-linear agentic software
engineering orchestration system that transforms requirements into reviewable
engineering outcomes across the complete software development lifecycle. Reviewers
will assess working behavior, architecture, engineering decisions, the AI-assisted
development process itself, task decomposition, testing discipline, governance,
traceability, change history, documentation, and engineering judgment. Every
principle below is scoped to serve that evaluation honestly — evidence must be real,
gates must be real, and autonomy must be bounded and observable.

## Core Principles

### I. Specification Before Implementation

No production implementation may begin without an approved specification. Requirements
MUST be testable and traceable. Functional and non-functional requirements MUST remain
distinguishable from one another. Ambiguities MUST be resolved or recorded as explicit,
human-approved assumptions — never silently resolved. Material upstream changes
(requirements, architecture, contracts) MUST trigger downstream impact analysis before
implementation proceeds. Existing code MUST NOT become an undocumented substitute for
the specification: if behavior and spec diverge, the spec is corrected through the
proper SpecKit stage, not silently outrun by code.

**Rationale**: An assessment of engineering process is meaningless if implementation
can outrun or quietly override the requirements it is supposed to satisfy.

### II. Explicit Agentic Orchestration

The orchestration system MUST be more than sequential agent chaining. It MUST use an
explicit dependency graph or an equivalent stateful model — not an implicit or
inferred one. It MUST support sequential paths, parallel paths, synchronization,
branching, dynamic replanning, interruption, and resumption. Every orchestration stage
MUST define its inputs, outputs, entry criteria, exit criteria, owning actor, and
failure behavior. Workflow state, cross-stage context, artifact provenance, and
decision lineage MUST be preserved, not reconstructed after the fact. Agent autonomy
MUST be bounded, observable, and auditable at all times.

**Rationale**: A linear sequence of agent calls is not orchestration and does not meet
this project's evaluation bar; the guide is explicit that "a linear sequence of agents
is not sufficient evidence of orchestration."

### III. Human Governance

Humans retain ownership of requirements interpretation, architecture approval,
technology-selection approval, security-sensitive decisions, destructive or
irreversible changes, material exception approval, material risk acceptance, release
readiness, and final submission. High-impact actions MUST require explicit human
approval before proceeding. Approval, rejection, escalation, timeout, and safe-stop
behavior MUST be explicitly defined for every gate. Mandatory approval gates MUST NOT
be silently skipped. Lack of response MUST NOT be interpreted as approval, under any
circumstance.

**Rationale**: This is the project's core control against an AI assistant approving
its own decisions or manufacturing the appearance of oversight.

### IV. Test-Driven Engineering

Red-green-refactor TDD MUST be applied to domain and orchestration behavior wherever
technically practical. For applicable behavior: write an initially failing test before
the corresponding implementation; execute the test and verify it fails for the
expected reason; implement only the minimum behavior needed to pass; refactor only
while tests remain green. Test coverage MUST include unit, integration, API contract,
orchestration state-transition, reliability, security, and end-to-end tests as
applicable. Task completion requires executed validation, not merely generated code —
and implementation-first work MUST NOT be retrospectively described as TDD.

**Rationale**: "Wherever technically practical" is preserved deliberately from the
governing guide rather than stated as an absolute — some infrastructure and
scaffolding work has no meaningful failing-test precursor, and claiming otherwise
would itself be a fabrication under Principle X.

### V. Security and Privacy by Design

External input MUST be validated and normalized. Acceptable URL schemes MUST be
explicitly restricted. Malicious-redirect and abuse scenarios MUST be addressed.
Secrets and sensitive information MUST NOT be exposed in logs. Secure configuration
defaults MUST be applied. Least privilege and explicit trust boundaries MUST be used.
Authentication assumptions, rate limiting, threat scenarios, and security trade-offs
MUST be documented. Dependency and secret scanning MUST be included in release
readiness.

**Rationale**: A URL shortener is a classic open-redirect and abuse surface; security
posture must be a first-class, designed-in property, not an afterthought bolted onto a
working prototype.

### VI. Compliance and Change-Control Policy Enforcement

Versioned policy guardrails MUST be defined covering security, compliance, privacy,
audit retention, approved dependencies, software licensing, and change control. Every
orchestration run MUST identify the policy version it evaluated against. Every
applicable policy check MUST produce exactly one outcome: `PASS`, `FAIL`,
`EXCEPTION-REQUESTED`, or `NOT-APPLICABLE`. A failed mandatory policy check MUST block
downstream workflow progression. A policy exception MUST require explicit human
approval and MUST record: the applicable policy, reason, scope, approving authority,
compensating control, approval timestamp, and expiry or review condition. Changes to
approved requirements, architecture, schemas, workflow states, security controls, or
release criteria MUST pass through formal impact analysis and change approval. Release
readiness MUST fail while a mandatory compliance or change-control policy remains
violated or carries an unapproved (or expired) exception. Policy outcomes and
exceptions MUST be included in audit and traceability evidence.

**Rationale**: This principle is the only sanctioned mechanism for a bounded,
time-limited deviation from a specific policy check. It does not waive a Core
Principle (see Governance, "Waiver Policy").

### VII. Architecture and Maintainability

Domain logic, API delivery, persistence, orchestration, policy enforcement, telemetry,
and infrastructure concerns MUST be separated. External dependencies MUST be accessed
through explicit interfaces. Material architectural decisions and rejected
alternatives MUST be recorded (as Architecture Decision Records). Complexity that
cannot be justified by requirements or demonstrability MUST be avoided. Code MUST
remain modular, readable, testable, and replaceable.

**Rationale**: Distinguishes production-grade engineering discipline from
production-scale infrastructure the assessment's timebox does not warrant.

### VIII. Reliability and Recovery

Transient and permanent failures MUST be classified separately. Bounded retries MUST
be used where appropriate, with explicit backoff and timeout behavior. Idempotency
MUST be applied to repeatable operations. Fallback behavior MUST be defined. Rollback
MUST be distinguished from compensation, and each used only where it is actually
feasible — a rollback claim that is not technically feasible is a constitutional
violation, not a simplification. Safe-stop conditions MUST be defined for when
continuation is unsafe. Terminal outcomes MUST be deterministic. Controlled resumption
after interruption MUST be supported. Evidence of success, failure, retry,
compensation, recovery, and latency MUST be captured.

**Rationale**: These are the mechanisms the assessment specifically probes for
("retries, fallback, rollback, compensation, and safe-stop") and are easy to claim and
hard to actually implement — hence the explicit prohibition on invalid rollback claims.

### IX. Observability and Auditability

Every orchestration execution MUST carry a correlation or run identifier. State
transitions, decisions, approvals, retries, failures, replanning events, and terminal
outcomes MUST be recorded. Audit evidence MUST include actor type, action, timestamp,
affected artifact or state, result, and reason. Logs, metrics, traces, and workflow
history MUST together support full reconstruction of an execution. Demonstration
metrics MUST be clearly and visibly distinguished from production measurements — they
MUST NOT be presented as production statistics.

**Rationale**: Reconstructable executions are what let a reviewer verify a claim
instead of trusting it.

### X. Traceability and Repository Integrity

Traceability MUST be maintained across requirement, scenario, decision, design, task,
implementation, test, validation, documentation, and evidence. Commits MUST be small
and logically coherent, with messages that describe engineering intent. Approval,
test, execution, or operational evidence MUST NOT be fabricated, under any
circumstance — this prohibition admits no exception, including under the Principle VI
exception workflow. AI-generated artifacts require human review and human ownership.
Documentation MUST evolve alongside implementation, not trail it indefinitely.

**Rationale**: This principle, together with Principle III's approval-from-silence
prohibition, forms the non-waivable evidentiary floor of the whole system: no policy
exception, timebox pressure, or convenience justifies fabricated evidence or
self-approval.

### XI. Evidence-Based Completion

A feature or task is complete only when all of the following hold: applicable
requirements are identified; decisions and assumptions are recorded; acceptance
criteria are satisfied; required tests have been executed successfully; security and
reliability checks are complete; documentation is current; traceability is complete;
residual risks and limitations are disclosed; required approval is recorded; and
evidence is available for independent reviewer verification. A Claude-generated
summary asserting an outcome (e.g., "all workflows support rollback") is not itself
evidence of that outcome.

**Rationale**: Closes the loop opened by Principle X — completion is defined by
externally verifiable evidence, not by an agent's self-report.

## Governing Methodology and Authority Hierarchy

SpecKit is the sole lifecycle, specification, planning, task, and governance authority
for this repository. Claude Code acts only as the primary AI coding assistant and
execution runtime operating within that authority; it MUST NOT introduce or simulate a
competing planning, task, memory, or execution methodology (e.g., GSD, SuperPowers,
BMAD, or a self-invented roadmap, state file, task numbering scheme, or planning
document), and any such proposal MUST be rejected unless it is adopted through the
correct SpecKit stage (constitution amendment, specification, clarification, plan, or
ADR, as applicable).

When instructions conflict, the following precedence governs, highest first:

1. Official assessment requirements
2. This approved constitution
3. Approved feature specification and clarifications
4. Approved technical plan and contracts
5. Approved Architecture Decision Records
6. SpecKit-generated task plan
7. Current implementation
8. Informal conversation

Existing implementation behavior MUST NOT override approved requirements found higher
in this list. If Claude Code identifies a missing or incorrect requirement, the
correction is made by returning to the appropriate upstream SpecKit stage (typically
`/speckit-clarify` or `/speckit-specify`), revising downstream artifacts, re-running
`/speckit-analyze`, and only then resuming — never by editing code first and
explaining the deviation afterward.

## Development Workflow and Human Gates

The authoritative lifecycle for this repository is:

`/speckit-constitution` → `/speckit-specify` → `/speckit-clarify` →
**Human Requirements Approval** → `/speckit-plan` → Architecture Decision Records →
**Human Architecture Approval** → `/speckit-checklist` → `/speckit-tasks` →
`/speckit-analyze` → **Pre-Implementation Review** → `/speckit-implement` →
Incremental TDD Execution → Scenario Demonstrations → `/speckit-converge` →
**Independent Assessment Review** → **Release-Readiness Decision**.

Each bolded step is a mandatory human gate. A gate is satisfied only by an explicit,
recorded human decision (approve, reject, or request changes) — never by silence,
timeout, or inferred consent. Implementation-affecting work MUST NOT proceed past a
gate that has not been explicitly cleared. Architecture-sensitive implementation
specifically MUST be blocked until its governing ADR is marked Accepted by the human
candidate; Claude Code may propose, compare, and recommend an ADR decision, but MUST
NOT mark its own proposal Accepted.

Autonomous execution during `/speckit-implement` is bounded by task-group boundaries
(one coherent task group, its tests, its documentation, and its traceability update),
after which work stops for inspection and commit — not by an unbounded, multi-task
autonomous run.

## Governance

**Supremacy**: This constitution supersedes ad hoc practice for this repository.
Where a lower-precedence artifact (per the Authority Hierarchy above) conflicts with
this constitution, this constitution governs until the conflict is resolved through a
constitutional amendment.

**Compliance assessment during planning**: Constitutional compliance is assessed
continuously, not only at the end. `/speckit-plan` and the ADR generation gate must
show how each proposed design satisfies the applicable Core Principles.
`/speckit-analyze` performs a read-only cross-artifact consistency and constitutional-
compliance pass, classifying findings as CRITICAL, HIGH, MEDIUM, or LOW, and MUST be
re-run after corrections until no CRITICAL or HIGH constitutional finding remains open.
An independent, adversarial Principal Engineer review (a fresh reviewer role that does
not defend prior Claude-generated recommendations) is required before implementation
begins and again before convergence.

**Waiver policy — which principles cannot be waived**: All eleven Core Principles are
non-negotiable; none may be waived in whole. The only sanctioned, bounded deviation
mechanism is the Principle VI exception workflow (`EXCEPTION-REQUESTED`), which applies
solely to specific policy checks (security, compliance, privacy, audit retention,
dependency, licensing, change control) and requires the full exception record
(authority, reason, scope, compensating control, timestamp, expiry). It does not waive
a Core Principle itself, and it can never authorize what Principle X and Principle III
forbid outright: fabricated evidence, self-approval, or approval inferred from
silence — those admit no exception under any process.

**Exception proposal and approval**: Any exception is proposed by identifying the
specific policy check and rationale, is never self-approved by Claude Code, and
requires the human candidate's explicit, recorded approval before the exception takes
effect. An expired or unapproved exception is treated as a policy failure and blocks
release readiness under Principle VI.

**Amendment versioning**: Amendments follow semantic versioning:
- **MAJOR** — backward-incompatible removal or redefinition of a principle or
  governance rule.
- **MINOR** — a new principle added, or materially expanded guidance on an existing
  one.
- **PATCH** — clarification, wording, or other non-semantic refinement.

Every amendment updates `LAST_AMENDED_DATE` and produces a Sync Impact Report
documenting the version change, modified principles, added/removed sections, and any
deferred follow-up items, as scratch material for human review preceding the commit
that ratifies the amendment.

**Conflict resolution between principles**: Where two principles appear to conflict in
a specific situation, the more conservative, evidence-preserving, and
human-oversight-preserving reading governs by default, and the conflict itself is
disclosed rather than silently resolved. An irreducible conflict MUST stop the
affected work and escalate to the human candidate rather than be worked around;
Principle III's approval requirements and Principle X/XI's evidence-integrity
requirements are never the losing side of such a resolution. (This rule is not
verbatim from the governing guide, which does not itself rank the principles — it was
proposed at drafting and explicitly approved by the human candidate at ratification.)

**Non-compliance blocking release readiness**: `/speckit-converge` MUST resolve to
exactly one of `READY`, `READY WITH ACCEPTED LIMITATIONS`, or `NOT READY`, and MUST
NOT return `READY` while a critical requirement, scenario, security control,
governance gate, or validation step remains incomplete. Per Principle VI, release
readiness also fails outright while any mandatory compliance or change-control policy
check remains `FAIL`, or carries an `EXCEPTION-REQUESTED` outcome without recorded
human approval, or an approved exception has expired.

**Initial constitution version**: 1.0.0, ratified 2026-09-10.

**Ratification record**: This constitution (v1.0.0) was reviewed and explicitly
approved by the human candidate at Human Gate 1 on 2026-09-10, together with the four
decisions recorded in this ratification: dating this version's ratification and
last-amendment to the approval date; adopting the conservative, evidence-preserving
conflict-resolution default above, with escalation to the human candidate for
irreducible conflicts; retaining SpecKit's sole-lifecycle-authority framing and the
authority hierarchy at constitutional weight; and retaining the section names as
drafted. No principle content changed between proposal and ratification.

**Version**: 1.0.0 | **Ratified**: 2026-09-10 | **Last Amended**: 2026-09-10
