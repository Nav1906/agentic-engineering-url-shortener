# Implementation Plan: Agentic Software Engineering System: URL Shortener

**Branch**: `001-governed-url-shortener` | **Date**: 2026-09-10 | **Spec**: [spec.md](./spec.md) (Approved, commit `e29f2d7`)

**Input**: Feature specification from `specs/001-governed-url-shortener/spec.md`

**Status**: **9 of 10 ADRs ACCEPTED** by the human candidate at Human Gate
4, 2026-09-10 ("accept all," applied to every ADR then presented for
decision — ADR-0006 excluded, ruled on separately, remains **Rejected**).
This plan itself, and ADRs 0005/0007/0009, went through three revision
rounds before acceptance; ADR-0006 went through a fourth (rejected) and is
tracked separately, still open.
Round 1 found a genuine crash/retry conflict, an unenforced credential-
isolation claim, an under-specified execution model, SQLite contention
coupling in the analytics design, an overstated contract-validation claim,
and an incorrect release-readiness rule. Round 2's fixes were themselves
found incomplete on a further review: the adapter DAG ran tasks before
architecture approval (inverted lifecycle order); reconciliation didn't
cover exceptions after a side effect, only stale leases; fencing a database
row didn't stop a still-running worker's real file effects; the reaper
missed a no-transitions-occurring case; the analytics "hard 20ms" timeout
couldn't actually cancel a blocking write, and recording a count before the
response was sent could overcount responses never issued; credential
isolation covered one file but not the approval server, database, or
verifier configuration; postconditions had no executable validator; several
Validation sections falsely claimed tests were "executed" when no code
exists yet. All of Round 2's findings are addressed in Round 3. Full
finding-by-finding resolution for both rounds is persisted at
[docs/governance/gate-4-review-2026-09-10.md](../../docs/governance/gate-4-review-2026-09-10.md).
Do not treat any technology choice or ADR below as final until you
explicitly accept it.

## Summary

Build a governed, stateful, non-linear agentic orchestration system (the
assessment's central differentiator) whose demonstration domain is a
production-oriented URL shortener. Primary technical approach (research.md):
a single Python/FastAPI process, a single SQLite database (WAL mode) shared
by clearly-separated packages (ADR-0001), a hand-rolled persisted
dependency-graph workflow engine with durable execution identities, atomic
claiming, and effect reconciliation before any retry (ADR-0005 Rev. 2), a
named agent-adapter execution layer that invokes SpecKit's own commands
rather than competing with them (ADR-0005 Rev. 2), role-enforced human
approvals with credentials isolated via an OS-sandboxed subprocess boundary
(ADR-0006 Rev. 2, not yet verified), a write-ahead-log analytics model
decoupled from SQLite contention that never reports permanently-lost counts
as complete (ADR-0009 Rev. 2), and a uniform bounded-retry/safe-stop/
write-contention reliability policy (ADR-0007 Rev. 2) — all within a 2–3 day
timebox (§ Planning Constraints, below).

## Technical Context

**Language/Version**: Python 3.12 (ADR-0002)

**Primary Dependencies**: FastAPI, Pydantic v2, `uvicorn`, standard-library
`sqlite3` (ADR-0002, ADR-0003)

**Storage**: SQLite, single file, WAL mode (ADR-0003) — see data-model.md

**Testing**: `pytest`, `pytest-asyncio`, FastAPI `TestClient` (ADR-0002)

**Target Platform**: Local process, any OS with Python 3.12 (ADR-0010) — no
cloud/hosted target

**Project Type**: Single-process web service with an in-process orchestration
engine (modular monolith, ADR-0001) — not a library, not a mobile app

**Performance Goals**: No hard production-scale target (spec Exclusions rule
out capacity planning). **`PVT-001` corrected, not retired (Human Gate 4
spike)**: an earlier Round 3 draft incorrectly concluded that moving the
analytics write after the redirect response retired FR-106's bounded-
overhead requirement. That was wrong and has been reverted — FR-106 is an
approved requirement and remains in force; moving the write off the
response-blocking path changes *what* the bound applies to (the background
write's own duration, not the response latency, which the write no longer
touches at all), not *whether* a bound applies. **`PVT-001`, restored:
the post-response analytics write completes within 50ms — provisionally
approved as an implementation target (Human Gate 4, 2026-09-10), labeled
unverified until implementation tests pass.** Spike evidence
(`docs/governance/gate-4-spike-results-2026-09-10.md`, Scenario 9): a
single real write against the actual schema measured 0.276ms under
uncontended, no-load conditions. **Per explicit instruction: a single
spike measurement does not establish a performance percentile** — this
supports "not obviously infeasible," not a p95 claim; real percentile
validation is implementation-time work. A write exceeding the budget is
treated as degraded proactively (background-task time-boxing), not
retried unboundedly. No other numeric performance target is proposed for
the redirect path itself; none was requested by the
assignment.

**Constraints**: Must run locally with no external infrastructure (ADR-0003,
ADR-0010); redirect availability must never depend on analytics durability
(FR-105/106, ADR-0009); retries bounded per ADR-0007's proposed numbers.

**Scale/Scope**: Single-operator local demonstration (spec Assumptions) — not
sized for concurrent multi-tenant load.

*All Technical Context fields above are resolved — none remain `NEEDS
CLARIFICATION`. See research.md for the comparative analysis behind each.*

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design
(below).*

| Principle | Check | Status |
|---|---|---|
| I. Specification Before Implementation | No code written this stage; every plan decision traces to an approved FR | **PASS** |
| II. Explicit Agentic Orchestration | ADR-0005 — persisted dependency graph, not implicit chaining | **PASS** (design-time; implementation-time re-verification required) |
| III. Human Governance | ADR-0006 — role-checked approvals, revision-bound (ADR-0005), mechanism sound. Credential-isolation sub-control: **Revision 3 REJECTED by explicit Human Gate 4 decision** — its OS-sandbox mechanism spike-FAILED on the tested platform; a final Option A (separate OS user) spike is designed, awaiting authorization, not yet executed | **PASS** (role/revision mechanism) / **FAILED → PENDING RE-SPIKE** (credential isolation) |
| IV. Test-Driven Engineering | ADR-0002 — pytest, TestClient enable red-green-refactor; plan §10 (Testing) below | **PASS** |
| V. Security and Privacy by Design | plan §8 (Security) below — scheme allow-list, no PII in analytics (already resolved, AMB-002) | **PASS** |
| VI. Compliance and Change-Control | research.md §8 — versioned policy manifest, PASS/FAIL/EXCEPTION-REQUESTED/NOT-APPLICABLE | **PASS** |
| VII. Architecture and Maintainability | ADR-0001 — explicit package separation; no unjustified complexity (rejected: microservices, external orchestration engine, OPA) | **PASS** |
| VIII. Reliability and Recovery | ADR-0007 — bounded retry, rollback-vs-compensation rule, safe-stop | **PASS** |
| IX. Observability and Auditability | ADR-0008 — append-only audit table, precise MTTR definition, demonstration-data labeling | **PASS** |
| X. Traceability and Repository Integrity | Every FR referenced by ID throughout this plan and its ADRs | **PASS** |
| XI. Evidence-Based Completion | quickstart.md and every ADR's Validation section require executed, retained output — no narrative-only claims | **PASS** |

No violation requires justification — **Complexity Tracking (below) is empty
by design**, not omitted.

**What "PASS" means at this gate, stated explicitly after Human Gate 4
review**: a design-level judgment that the proposed architecture, if
implemented as specified, satisfies the principle — it is **not** a claim
that the principle is already satisfied in a running system, since no code
exists yet. Every ADR's own Validation section states what must actually be
executed for its specific claims to be verified; ADR-0006's credential-
isolation control is called out above by name because the Human Gate 4
review specifically found it had been described in stronger terms than its
evidence supported — the same "design PASS ≠ verified PASS" distinction
applies to every row, but is stated once here rather than repeated eleven
times.

## 1. System Context

- **System boundary**: this single process (ADR-0001); no external system is
  called (no real third-party redirect targets are contacted — destination
  URLs are stored and returned, never fetched server-side).
- **Actors**: API consumer, software engineer, human reviewer/approver,
  release owner, assessment reviewer (spec User Types).
- **External dependencies**: none required to run (ADR-0003, ADR-0010) —
  intentionally, to keep the system locally demonstrable.
- **Trust boundaries**: the approval surface (authenticated, role-checked,
  ADR-0006) vs. the domain API (unauthenticated, per spec Exclusions) are
  distinct trust boundaries within the same process.
- **Major runtime components**: FastAPI HTTP layer; orchestration scheduler
  loop (ADR-0005); analytics drain worker (ADR-0009); SQLite (ADR-0003).
- **Data ownership**: each package owns its table namespace (data-model.md);
  no cross-package direct table access.
- **Application-plane vs. control-plane**: domain package = application
  plane; orchestration + policy + audit packages = control plane (ADR-0001).

## 2. URL Shortener Architecture

Full API/schema contract: [contracts/openapi.yaml](./contracts/openapi.yaml).
**Evidence, corrected at Human Gate 4 review**: an earlier report of this
contract as "validated" was overstated — the command actually run
(`python3 -c "import yaml; yaml.safe_load(...)"`) only confirms the file is
**syntactically well-formed YAML**, not that it is a structurally valid
OpenAPI document (schema types, `$ref` targets, required fields per the
OpenAPI 3.0 spec). That gap has since been closed: `uv run --with
openapi-spec-validator openapi-spec-validator
specs/001-governed-url-shortener/contracts/openapi.yaml` was executed this
session and returned `...openapi.yaml: OK` with exit code 0 — a real
structural OpenAPI validation (schema and `$ref` checks), not merely a YAML
parse. This confirms the contract is a structurally valid OpenAPI 3.0.3
document. **Runtime conformance** (does the eventual implementation actually
match these schemas at request/response time) remains future test work —
this validation covers document structure only, not implementation
behavior. Full
persistence schema: [data-model.md](./data-model.md). Versioning and
change-control rules for this contract are defined at the bottom of the
OpenAPI file itself (semantic versioning; FR-306 change-approval required for
any modification).

Components: API delivery (FastAPI routers) · domain logic (`domain` package)
· short-code generation (ADR-0004) · URL validation (allow-listed schemes,
§8 Security below) · redirect resolution (FR-103) · persistence (ADR-0003)
· analytics (ADR-0009) · expiration (FR-104/FR-114) · health/readiness
(`/health`, FR-111/FR-115) · telemetry (ADR-0008's audit table) ·
configuration (environment variables for credential hashes, ADR-0006; a
`config/policies.yaml` manifest, research.md §8).

## 3. Agentic Orchestration Architecture

Full design: **ADR-0005 (Revision 3)**. Summary of every required primitive
and where it lives:

| Primitive | Mechanism | Table(s) |
|---|---|---|
| Explicit nodes/stages | `orchestration_workflow_stage` rows | data-model.md |
| Explicit dependencies | `orchestration_stage_dependency` edges | data-model.md |
| Durable execution identity | `orchestration_stage_execution` rows, per-process `worker_id` | ADR-0005 §Decision |
| Atomic claiming | compare-and-swap `UPDATE ... WHERE status='ready'` | ADR-0005 §Decision |
| State transitions | `status` enum + transition rules | ADR-0005 |
| **Lifecycle order** (corrected Round 3) | Architecture/Design → Human Architecture Approval → Checklist → Task Decomposition → Analyze → Implementation — **never tasks before architecture approval** | ADR-0005 §Decision — Corrected Lifecycle Order |
| Sequential paths | dependency chain, one stage's `depends_on` another | ADR-0005 |
| Parallel paths / fan-out | multiple `ready` stages dispatched via `asyncio.gather`, **only across dependency-safe pairs** (e.g., checklist ∥ security static checks; testing ∥ documentation — never across a human gate) | ADR-0005 |
| Synchronization | eligibility query requires *all* dependencies `succeeded` | ADR-0005 |
| Conditional branches | scheduler eligibility query can incorporate stage-output conditions | ADR-0005 |
| Entry/exit gates | per-stage `preconditions`/`postconditions`, now backed by an **executable validator** whose result (exit code, output hash, artifact hashes) is required before `succeeded` — a clean git status or checked box is not accepted alone | ADR-0005 §Decision — Executable Postconditions |
| Approval / rejection states | `awaiting_approval` / `rejected` stage status + `orchestration_approval_decision` | ADR-0006 |
| Retry states | `failed_transient` → reconciliation-confirmed-safe bounded retry, **required after exception, timeout, or stale lease alike** (Round 3 correction — an in-band exception is no longer assumed safe on its own) | ADR-0005 + ADR-0007 |
| Effect reconciliation | `check_effect()` adapter probe, triggered by exception/timeout/stale-lease | ADR-0005 §Decision |
| Isolated execution & promotion (new, Round 3) | each file-producing stage runs in its own `git worktree`; only the controller promotes output into the main tree, gated on fencing + validator + revision match — closes the "fencing the DB row doesn't stop a zombie's real effects" gap | ADR-0005 §Decision — Isolated Execution Workspaces |
| Fallback states | defined per stage, invoked on `failed_permanent` | ADR-0007 |
| Rollback/compensation | per-operation classification | ADR-0007 |
| Safe-stop terminal state | `workflow_instance.status = safe_stopped`, incl. reconciliation exhaustion | ADR-0007 |
| Resume/recovery | lease-expiry detection on **both** an event-triggered tick and a periodic wall-clock sweep (Round 3 — closes the "no transitions occurring" gap), never a blind retry | ADR-0005 |
| Dynamic replanning | artifact-revision invalidation cascade, reconciled before reset; in-progress worktrees never promoted once invalidated | ADR-0005, FR-501/502 |
| Execution engine ("real work") | agent-adapter contract; SpecKit skills invoked via the real `claude` CLI, headless (Round 3 — corrected from "invoke `/speckit-tasks`" as if it were a standalone binary) | ADR-0005 §Decision — Real Claude Invocation |

Per-node definitions (purpose/inputs/outputs/pre-postconditions/actor/allowed
transitions/timeout/retry policy/failure classification/fallback/audit
events) are captured structurally in `orchestration_workflow_stage` +
ADR-0007's policy, not enumerated per concrete stage here — concrete stage
definitions are a `/speckit-tasks` deliverable once this plan is approved.
ADR-0005's adapter table (§Decision — Agent Adapters) names the twelve
concrete SDLC-stage adapters and a worked DAG example with real fan-out and
a join; that is the fundamental execution model, not deferred.

## 4. State and Decision Lineage

Preserved via: `orchestration_workflow_instance`/`_stage` (workflow state),
`decision_lineage` (append-only, FR-503), `orchestration_approval_decision`
(approvals/rejections, revision-bound), `audit_events` (everything else:
retries, replanning, terminal status). Normalized requirements/task
decomposition/artifact versions are tracked via `feature_ref` and
`artifact_revision` fields referencing this repository's own git history and
`specs/`/`docs/adr/` files — no separate requirements-tracking system is
introduced (Constitution: SpecKit is the sole lifecycle authority).

## 5. Human-in-the-Loop Controls

Mandatory gates (FR-301, unchanged from spec): unresolved ambiguity,
architecture approval, security-sensitive action, destructive/irreversible
action, constitutional exception, material risk acceptance, release
readiness, final submission. Approval-recording mechanism (roles,
revision-binding, audit fields): **ADR-0006**, sound and unaffected by the
credential-isolation finding below. Credential-isolation mechanism
specifically: **Revision 3 REJECTED (Human Gate 4, 2026-09-10)** — see
ADR-0006 "Revision 4 — Option A Spike Design," awaiting authorization. Role
mapping (FR-312/313): `reviewer_approver` — requirements/architecture;
`release_owner` — release-readiness/final-submission.

**Approval-timeout policy (`PVT-006`, proposed, added at Human Gate 4
review)**: a workflow awaiting approval escalates (FR-302 — never inferred
as approval) after **24 hours** of no recorded decision, for gates other
than a live, synchronous scenario demonstration (greenfield/brownfield/
ambiguous scripts, which use a much shorter, explicitly test-only timeout —
proposed **60 seconds** — so an automated demonstration run doesn't hang
indefinitely waiting on a human who is, by design, expected to respond
quickly during a live demo). Both numbers are **proposed, not approved.**
Escalation transitions the gate to a distinct `escalated_timeout` decision
record (already in the schema, data-model.md) — never silently proceeds.

## 6. Reliability

Full design and proposed numbers: **ADR-0007 (Revision 3)** — bounded retry
is now precisely 3 attempts with exactly 2 intervening waits (1s, 2s), and
per-attempt timeouts are split by realistic subprocess type: 5s (internal
DB/claim operations), 300s (`pytest`), 600s (a real Claude Code invocation)
— all still proposed, not approved. A retry for an
`externally_observable_uncertain` stage now always requires ADR-0005's
`check_effect()` reconciliation first, regardless of whether the failure
was an exception, a timeout, or a stale lease. Idempotency: **ADR-0003**
(SQLite UNIQUE constraint transactionally), **data-model.md**
(`domain_idempotency_record`). Duplicate-execution protection: the same
idempotency mechanism, plus orchestration-stage `attempt_count` tracking
retries at the workflow level (distinct from domain-level idempotency).
Partial failure / dependency unavailability: FR-109 (persistence-layer
failure is observable, non-silent) — implemented as the lease-expiry
detection rule in ADR-0005 plus ADR-0007's failure classification.

## 7. Observability

Full design and precise MTTR definition: **ADR-0008**. Logs: standard
application logs for operational signals (e.g., analytics degradation,
FR-115) distinct from the audit-event table (evidence-of-record). Metrics:
computed via SQL aggregate queries (`/metrics/reliability`, contracts/
openapi.yaml) — always `demonstration_data: true`, never presented as
production statistics (FR-604). `/health`'s analytics sub-object also
exposes `degraded_since_unclean_shutdown_at` (`analytics_system_status`,
ADR-0009) — a system-wide signal that a prior unclean shutdown may have
caused undetectable analytics loss. **Approved as spec.md FR-117 (Human
Gate 4 amendment, 2026-09-10)**, with the semantics as directed: sticky;
operator acknowledgment clears the forward-looking warning only, never
historical completeness; historical uncertainty stays visible in analytics
evidence. The contract is approved; the mechanism implementing it
(ADR-0009) remains Proposed, not Accepted. Traces: satisfied via
`correlation_id` (=`workflow_instance.id`) linkage across audit events
within a single process — full distributed tracing infrastructure is not
introduced, since there is only one process to trace within (ADR-0001).

## 8. Security

- **Input validation**: Pydantic schemas (contracts/openapi.yaml) validate
  every request body/parameter at the boundary.
- **Allowed URL schemes**: an explicit allow-list (`https`, `http` —
  proposed; final list requires your confirmation as it was not specified by
  the assignment) rejects everything else, including `javascript:`,
  `data:`, and other script-executing schemes (FR-101).
- **Malicious redirect / internal-address considerations — approved as
  proposed (Human Gate 4, 2026-09-10)**: destination URLs resolving to
  loopback/link-local/private-network addresses are checked **at creation
  time only**. This check is explicitly **not** a permanent guarantee: DNS is not pinned, so a
  destination hostname that resolves to a public address at creation time
  can later be repointed (DNS rebinding) to a private/internal address by
  the time a redirect is actually resolved — the creation-time check reduces
  the obvious/lazy attack (submitting an already-private-pointing URL) but
  does **not** prevent a determined rebinding attack at resolution time.
  Closing that gap would require resolving and re-checking the destination
  at *every* redirect (adding latency and complexity disproportionate to
  this timebox) or a proxying redirect model — both explicitly out of scope
  here and disclosed as a known, accepted limitation, not silently ignored.
- **Abuse cases**: short-code enumeration (mitigated by ADR-0004's random,
  non-sequential codes). **Idempotency-key guessing**: a caller-supplied key
  is **not automatically unguessable** — nothing in FR-108/112/113
  constrains how a caller generates it. **Approved as proposed (Human Gate
  4, 2026-09-10)**: an `Idempotency-Key` MUST be a string of at least 16
  characters; the system does not itself verify
  entropy/randomness beyond that length floor, since it cannot know how the
  caller generated the value. This is disclosed as the **caller's
  responsibility** — a short or predictable key is a caller-side risk (a
  guessed key could let a third party observe whether *a* request with that
  key was already processed, though not read its payload), not a system
  guarantee.
- **Rate limiting (`PVT-007`, proposed, added at Human Gate 4 review)**: no
  numeric target was given by the assignment; proposed limit is **60
  requests/minute per source IP** on the domain API (`/short-links`,
  `/{shortCode}`). **Not approved.**
- **Authentication assumptions, and the unauthenticated API's scope made
  explicit (Human Gate 4 review)**: the domain API is unauthenticated (spec
  Exclusions, explicit) — this means **any caller who can reach this
  process** can create, resolve, view analytics for, **and delete** any
  short link they can name or guess a code for (`DELETE
  /short-links/{shortCode}` carries no auth per contracts/openapi.yaml).
  This is a direct, accepted consequence of the spec's explicit exclusion of
  end-user authentication, not an implementation oversight — but it was not
  stated this plainly before, and is stated plainly now so it is not
  mistaken for an omission. The approval surface (`ADR-0006`) is the only
  authenticated part of this system.
- **Secrets management**: approver credential hashes only in the app
  process's environment (ADR-0006); raw credentials never in git (gitignored
  local file).
- **Dependency risk**: `uv`-pinned lockfile; a dependency-scan check is part
  of the compliance policy manifest (research.md §8).
- **Audit integrity**: append-only convention (ADR-0008), disclosed as not
  cryptographically tamper-evident at this scale.
- **Least privilege — Revision 3 REJECTED (Human Gate 4, 2026-09-10)**: the
  broadened protected-asset boundary (database, policy manifest, launch
  scripts, the orchestration engine's own source, main `.git/`) via an
  OS-level default-deny sandbox remains the right *design shape*, but its
  specified mechanism (macOS `sandbox-exec`) **failed a direct feasibility
  spike** on the actual target platform (confirmed `SIGABRT` on any custom
  profile allowing `process-exec`); Linux `bwrap` was never tested. This
  control was **rejected as written**, not accepted with caveats. A final,
  bounded spike for **Option A (a separate OS user)** is designed in
  ADR-0006 "Revision 4" and awaiting your authorization — no privileged
  command has been run. **Explicitly out of scope regardless of outcome**:
  this says nothing about, and provides no protection for, the interactive
  Claude Code session used to develop this repository. **This control
  remains "not yet PASS"** — now for a confirmed-failure reason, not merely
  an untested one.
- **Secure defaults**: no default expiration is *not* a security weakening —
  it was an explicit, approved behavioral decision (AMB-006), not a default
  chosen for convenience.
- **Threat modeling**: covered narratively above; a dedicated STRIDE-style
  pass is out of scope for this timebox and is disclosed as such.

## 9. Compliance and Change Control

Policy domains and model: **research.md §8**. Mandatory policies for this
prototype: dependency/secret scan (security), architecture change-control
(any material change requires an ADR or spec amendment, FR-306), release
readiness (all FR-301 gates non-`FAIL`). Policy evaluation is itself a
workflow stage (§3 above), producing `policy_evaluation` rows
(data-model.md) with the required `PASS`/`FAIL`/`EXCEPTION-REQUESTED`/
`NOT-APPLICABLE` outcome and policy version. A `FAIL` blocks downstream
progression by construction (the dependent stage's eligibility query in
ADR-0005 will never see the policy stage as `succeeded`) — this is a direct,
mechanical consequence of the orchestration model, not a separately
enforced rule that could drift out of sync with it.

## 10. Testing

| Test type | Tooling | Demonstrates |
|---|---|---|
| Domain unit | pytest | FR-101–FR-116 |
| API contract | FastAPI `TestClient` against contracts/openapi.yaml | Request/response schema conformance |
| Persistence | pytest + ephemeral SQLite file | FR-110 concurrency, FR-204 durability |
| Integration | pytest, full app boot | end-to-end domain + orchestration paths |
| Orchestration state-transition | pytest, direct table assertions | FR-201–FR-206, ADR-0005 |
| Approval/rejection | pytest + `TestClient` with test credentials | FR-301–FR-313, ADR-0006 |
| Retry / timeout / fallback / rollback-or-compensation / safe-stop | pytest with fault injection | FR-401–FR-406, ADR-0007 |
| Resumption | pytest, process-kill simulation | FR-204/205, ADR-0005 |
| Replanning | pytest, artifact-revision mutation | FR-501–FR-503 |
| Concurrency | pytest, concurrent async requests | FR-110 |
| Security | pytest, malicious-scheme/payload fixtures | §8 above |
| End-to-end | pytest + `TestClient`, full scenario scripts | Scenario A/B/C (§11) |
| Release-readiness | pytest, policy-manifest fixtures | FR-301–FR-306 |

Red-green-refactor applied wherever technically practical (Constitution
Principle IV) — task-level TDD sequencing is a `/speckit-tasks` deliverable.

## 11. Scenario Designs

| | Greenfield (A) | Brownfield (B) | Ambiguous (C) |
|---|---|---|---|
| Initial input | A complete, testable requirement | A change request against the running system | A deliberately incomplete/conflicting requirement |
| Requirement interpretation | Passes requirement-quality check (FR-601) | Impact analysis required before any code change | Ambiguity detected, classified |
| Decomposition | Direct to design stage | Impact map → design stage | Suspended pending clarification |
| Orchestration path | Requirement → Decomposition → Design → Implementation → Testing → Documentation → Validation → Release Readiness | Impact analysis gate → (approved) → implementation | Detection → awaiting_approval (clarification) → resume |
| Approvals | Requirements/architecture as normal | Same, plus explicit impact-analysis review | Clarification decision is itself the approval event |
| Failure paths | Standard ADR-0007 policy | Blocked implementation if impact analysis incomplete (FR-605 Scenario B) | Cannot proceed without recorded human decision |
| Validation | Full test suite for the new capability | Regression suite + new tests | Post-clarification: impact-analysis + new tests |
| Generated evidence | Full audit trail, decision lineage | Impact-analysis record + regression evidence | Ambiguity-detection + clarification + replanning events |
| Expected terminal outcome | `completed` | `completed` (or `safe_stopped` if regression risk unmitigated) | `completed` after resumption |

Scenario scripts (`scripts/demo_*.py`) are enumerated in quickstart.md; full
implementation is a `/speckit-tasks` deliverable.

## 12. Technology Decisions

Every material selection is a full ADR under `docs/adr/`, each with Decision
Drivers, Options Considered (with advantages/disadvantages/risks/
implementation-impact/assessment-implications per option), Decision,
Rationale, Consequences, Risks and Mitigations, Reversibility, Traceability,
and Validation:

| ADR | Decision | Status |
|---|---|---|
| 0001 | Modular monolith (not microservices / two-service split) | **Accepted** |
| 0002 | Python 3.12 + FastAPI + Pydantic v2 + pytest | **Accepted** |
| 0003 | SQLite, WAL mode, single file | **Accepted** |
| 0004 | Random base62 short codes, bounded retry-on-collision | **Accepted** |
| **0005 (Rev. 3)** | Hand-rolled persisted dependency-graph engine, corrected lifecycle order (architecture approval before tasks), real `claude` CLI invocation (not a fictitious standalone command), reconciliation on exception/timeout/stale-lease alike, isolated per-execution `git worktree`s with controller-only promotion, a periodic (not just event-triggered) reaper, and executable postcondition validators with retained artifact-hash evidence | **Accepted** |
| **0006 (Rev. 3 — REJECTED, 2026-09-10)** | Rejected as written: primary macOS sandbox mechanism spike-FAILED on the actual target platform; Linux untested. A final, bounded Option A spike (separate OS user) is designed and awaiting your authorization to execute any privileged command — see ADR-0006 "Revision 4 — Option A Spike Design" | **Rejected** — the sole remaining unaccepted ADR |
| **0007 (Rev. 3)** | Bounded retry — 3 attempts, exactly 2 waits (1s, 2s, corrected from a miscounted 1s/2s/4s) — no longer treats an in-band exception as automatically safe without reconciliation; realistic per-subprocess timeouts (5s internal / 300s pytest / 600s Claude); SQLite correctly described as serializing writes, not providing concurrent row-level writers | **Accepted** |
| 0008 | Append-only audit table + precise MTTR definition (no number proposed yet) | **Accepted** |
| **0009 (Rev. 3)** | Analytics durability write moved to **after** the response is sent (closing an overcount defect), back onto plain SQLite (the separate WAL file and its unworkable hard-timeout claim are withdrawn); restart uncertainty handled via a single-store unclean-shutdown detector and a sticky, system-wide degradation signal — contract approved as spec.md FR-117 | **Accepted** |
| 0010 | Plain local process via `uv run`, no Docker | **Accepted** |

**9 of 10 ADRs Accepted by the human candidate at Human Gate 4, 2026-09-10**
("accept all," applied to every ADR presented for decision at that point —
**not** including ADR-0006, which was ruled on separately and earlier, and
stays Rejected). **Numeric targets — provisionally approved as
implementation targets (Human Gate 4, 2026-09-10), all labeled unverified
until implementation tests pass**: `PVT-001` (50ms bounded-overhead
budget for the post-response analytics write, per FR-106 — **corrected: not
retired**, see Technical Context above; a single spike measurement of
0.276ms supports "not obviously infeasible," not a performance percentile
claim), `PVT-002`/`PVT-003` (retry: 3 attempts, 1s+2s waits; timeouts:
5s/300s/600s by subprocess type), `PVT-006` (24h approval-gate timeout / 60s
demo-script timeout), `PVT-007` (60 req/min/IP rate limit), `PVT-008` (10s
periodic reaper sweep interval). `PVT-001a`/`PVT-001b` (the Round-2 hard-
timeout split) remain retired — that specific split was withdrawn along with
the unworkable fsync-abandon mechanism, not the underlying FR-106 obligation.
**All six above (`PVT-001`, `PVT-002`, `PVT-003`, `PVT-006`, `PVT-007`,
`PVT-008`) are provisionally approved as implementation targets — not
final, not verified. Each stays labeled "unverified" until its own
implementation-time test actually passes; provisional approval authorizes
building toward these numbers, it does not certify them.**

## 13. Traceability

`Requirement → Scenario → Design → ADR → Task → Code → Test → Validation →
Documentation → Evidence`. Concretely: every FR in spec.md is referenced by
ID in this plan and/or its ADRs (§1–§9 above); every ADR references its
governing FR(s) in its own Traceability section; tasks (not yet generated)
will reference both FR IDs and ADR IDs per the `/speckit-tasks` skill's
required task format; code/tests (not yet written) will reference task IDs
in commit messages (guide's Suggested Commit Progression).

## 14. Delivery Sequence (maps to § Planning Constraints below)

1. Engineering baseline (repo scaffolding, lockfile, CI-equivalent local
   commands)
2. Walking skeleton (one endpoint, one test, one commit, end-to-end)
3. Core URL behavior (FR-101–FR-116)
4. Orchestration state model (FR-201–FR-206, ADR-0005)
5. Approval governance (FR-301–FR-313, ADR-0006)
6. Reliability controls (FR-401–FR-406, ADR-0007)
7. Observability (FR-601–FR-606, ADR-0008)
8. Three scenarios (FR-605, §11 above)
9. Release readiness (FR-301–FR-306, §9 above)

## Planning Constraints

**Timebox**: 2–3 days. **Must-have scope** (days 1–2, roughly): items 1–7
above — without a working orchestration engine, approval governance, and
reliability controls, the assessment's central differentiator cannot be
demonstrated at all, so these are not deferrable. **Day 3 (or scope-control
checkpoint if running behind)**: items 8–9 — the three scenarios and
release-readiness reporting. **Backlog (explicitly deferred, not silently
dropped)**: allow-listed-scheme final list confirmation, DNS-rebinding
protection at resolution time (disclosed limitation, §8), egress network
restriction for agent subprocesses (disclosed limitation, ADR-0006), a
cryptographically tamper-evident audit log, containerized deployment
(ADR-0010 Option B — none of these are mandatory FRs, so they are legitimate
`READY WITH ACCEPTED LIMITATIONS` candidates, unlike a missing mandatory
item),
multi-tenant/production-scale concerns (explicitly excluded by spec, not a
timebox casualty).

**Stop conditions**: if, by the end of day 2, orchestration state-transition
tests (§10) are not passing, stop adding scope and stabilize the engine
before touching scenario scripts — a broken orchestration core invalidates
the whole demonstration, while a missing scenario script is a disclosed,
bounded gap.

**Minimum defensible release-readiness outcome, corrected at Human Gate 4
review**: the prior wording here incorrectly implied `NOT READY` could only
result from delivery-sequence items 1–7 being incomplete. That is wrong and
is retracted — it would let an "accepted limitation" silently waive a
mandatory requirement, which Constitution Principle VI and spec FR-301/
FR-306 do not permit. The correct rule, unchanged from spec.md and
Constitution Principle VI: **`READY` MUST NOT be returned while any
mandatory requirement, required scenario (A/B/C), mandatory security
control, mandatory human-approval gate, mandatory policy-check outcome, or
mandatory validation step remains incomplete or unresolved — regardless of
which delivery-sequence item (1–9) it happens to belong to.** A backlog
item may become an *accepted limitation* under `READY WITH ACCEPTED
LIMITATIONS` **only if it was never mandatory in the first place** (e.g.,
containerized deployment, a cryptographically tamper-evident audit log —
neither is required by any FR) — never as a way to excuse an incomplete
mandatory item. Concretely: if, by day 3, any of the three required
scenarios cannot be demonstrated, or any FR-301 gate is unenforced, or any
mandatory policy check is unresolved, the honest outcome is `NOT READY`,
full stop — the 2–3 day timebox is a planning constraint on *scope*, not a
license to relax what "mandatory" means at release-readiness time.

## Project Structure

### Documentation (this feature)

```text
specs/001-governed-url-shortener/
├── spec.md               # Approved (commit e29f2d7)
├── plan.md                # This file
├── research.md             # Phase 0
├── data-model.md           # Phase 1
├── quickstart.md           # Phase 1
├── contracts/
│   └── openapi.yaml         # Phase 1, validated
├── checklists/
│   └── requirements.md
└── tasks.md                # Phase 2 (/speckit-tasks — not created by this plan)

docs/adr/
├── 0001-application-architecture.md         # Proposed
├── 0002-language-framework-testing.md       # Proposed
├── 0003-persistence-strategy.md             # Proposed
├── 0004-short-code-generation.md            # Proposed
├── 0005-orchestration-model.md              # Proposed
├── 0006-human-approval-model.md             # Proposed
├── 0007-reliability-recovery-policy.md      # Proposed
├── 0008-observability-audit-model.md        # Proposed
└── 0009-analytics-consistency.md            # Proposed
└── 0010-local-execution-deployment.md       # Proposed
```

### Source Code (repository root — planned, not yet created)

```text
src/
├── domain/          # short links, idempotency, analytics (ADR-0001, ADR-0003, ADR-0004, ADR-0009)
├── orchestration/    # workflow engine, dependency graph, state machine (ADR-0005)
├── policy/            # policy manifest evaluation (research.md §8)
├── api/                 # FastAPI routers, request/response schemas (contracts/openapi.yaml)
├── persistence/          # SQLite access layer, shared schema utilities (ADR-0003)
└── observability/          # audit event writer, metrics queries (ADR-0008)

tests/
├── unit/
├── contract/
├── integration/
├── orchestration/
├── reliability/
├── analytics/
└── security/

scripts/
├── bootstrap_credentials.py   # ADR-0006
├── approve.py                  # ADR-0006 — the only code path that reads raw approver credentials
├── demo_greenfield.py
├── demo_brownfield.py
└── demo_ambiguous.py

config/
└── policies.yaml            # research.md §8

data/                         # gitignored — data/app.db created on first run (ADR-0003, ADR-0010)
local-secrets/                 # gitignored — ADR-0006
```

**Structure Decision**: Single project (Option 1 in the plan-template's
generic menu), expanded into the concrete package layout above. This is
Option A from ADR-0001 (modular monolith) made concrete — not a placeholder,
the actual planned layout. No `backend/`/`frontend/` split (no frontend
exists or is required by the spec) and no mobile-platform structure.

## Complexity Tracking

*Empty — no Constitution Check violation requires justification. Every
architectural choice above (see §12/ADRs) explicitly rejected higher-
complexity alternatives (external orchestration engines, microservices, a
hosted database, OPA) in favor of the simplest option that still satisfies
every approved requirement, per Constitution Principle VII.*

---

## Constitution Check (Post-Design Re-evaluation)

Re-checked after Phase 1 design (data-model.md, contracts/openapi.yaml,
quickstart.md): no new violation was introduced by the detailed data model or
API contract beyond what the pre-design check above already covered. All
eleven principles remain **PASS**. No Complexity Tracking entry is added.

---

## Human Gate 4

**9 of 10 ADRs Accepted by explicit human-candidate decision, 2026-09-10**
("accept all," per the guide's ADR gate and Constitution `Development
Workflow and Human Gates` — none were marked Accepted except by that
explicit decision). **ADR-0006 remains Rejected**, ruled on separately and
earlier in the same review; its replacement (Option A) is designed, not
executed, and not yet decided. Full inventory, rationale, and history:
`docs/governance/gate-4-review-2026-09-10.md`.
