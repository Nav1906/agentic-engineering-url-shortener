# Feature Specification: Agentic Software Engineering System: URL Shortener

**Feature Branch**: `001-governed-url-shortener`

**Created**: 2026-09-10

**Status**: **APPROVED** (Human Requirements Approval, per the guide's Final
Lifecycle, satisfying Human Gates 2 and 3). Approved 2026-09-10 by the human
candidate acting under the reviewer/approver role (Constitution FR-312). See
"Approval Record" below.

**Input**: The confidential AI Native SDLC guide (`./confidential/AI Native SDLC - User Guide.docx`), Section 7 "Prompt 2: Feature Specification", combined with the human candidate's instruction to define testable requirements for URL-shortener domain behavior, stateful SDLC orchestration, human/policy governance, reliability and audit mechanisms, and three required scenarios (greenfield, brownfield, ambiguous requirement).

**Governing constitution**: `.specify/memory/constitution.md`, v1.0.0, ratified 2026-09-10.

## Approval Record

**Human Requirements Approval** (satisfying the guide's Human Gate 2 and Human
Gate 3) was granted by the human candidate, acting under the reviewer/approver
role (Constitution FR-312), on **2026-09-10**.

This approval covers the specification as clarified: the original draft (Human
Gate 2), the five-question clarification session and its integration (Human Gate
3, `## Clarifications` → `### Session 2026-09-10`), and the Human Gate 3
consistency-review corrections (`### Human Gate 3 Review (2026-09-10)`) — analytics
availability-over-accuracy trade-off (AMB-007), idempotency-replay rules and
retention (FR-112/113/114/116), the checklist's runtime-vs-specification-time
correction, and the MTTR target removal.

Explicitly acknowledged as part of this approval, not silently waived:
- The two disclosed checklist qualifications in `checklists/requirements.md`
  ("Written for non-technical stakeholders," "Feature meets measurable outcomes")
  remain `[~]` partial — neither is being claimed as fully passed.
- The explicitly deferred planning obligations (AMB-004; `PVT-001`'s numeric
  budget and recovery mechanism; `PVT-002`/`PVT-003`; the approver-authentication
  mechanism from AMB-005; and the MTTR definitional framework before any numeric
  target) are accepted as **open**, carried forward as obligations for
  `/speckit-plan`, not resolved by this approval.

**Revision binding** (per FR-311, applied reflexively to this governance
artifact): this approval is bound to the exact content of this file as committed
to git immediately following this record — the commit hash of that commit is the
authoritative revision identifier. A material change to this specification after
that commit invalidates this approval and requires re-approval, exactly as
FR-311/FR-501/FR-502 require for any other approved artifact.

## How to Read This Specification

Per the guide's Specification Rules, every requirement and assumption below is
explicitly classified so the human candidate can distinguish what is settled from
what still needs a decision:

| Tag | Meaning |
|---|---|
| **Confirmed** | Stated directly by the assignment or the governing guide. |
| **Derived** | A reasonable, disclosed inference from a confirmed requirement, not itself stated verbatim. |
| **Assumption** | A default chosen because no confirmed source specifies it; flagged for approval, not silently adopted. |
| **Constraint** | A boundary condition this feature must operate within (e.g., timebox, scope limits). |
| **Ambiguity (AMB-xxx)** | Genuinely unresolved; recorded here for `/speckit-clarify`, not guessed away. |
| **Exclusion** | Explicitly out of scope for this feature. |
| **Proposed Validation Target (PVT-xxx)** | A numeric or measurable target proposed by this specification because the assignment gave none. It is a **proposal requiring approval**, never a confirmed client requirement, per the guide's explicit rule. |

No framework, programming language, database, cloud provider, agent framework, or
deployment platform is chosen anywhere in this document, per the guide's
Specification Rules. Architecture and technology selection are deferred to
`/speckit-plan` and the ADR gate.

**Evidence integrity rule (Confirmed, from the current task instruction and
Constitution Principles X/XI)**: A workflow stage, test suite, or task report that
states "code generated" or "tests passed" without an artifact that was actually
produced and a validation command that was actually executed does not satisfy any
requirement in this specification. Every acceptance criterion below that requires
"evidence" means an artifact plus an executed, observable result — not a narrative
claim of one.

---

## Clarifications

### Session 2026-09-10

- Q: When an API consumer submits a URL that already has an active short link
  pointing to the same destination, should the system return the existing short
  code, or always mint a new one? (AMB-001) → A: Request-level idempotency, not
  URL-level. Without a caller-supplied Idempotency-Key: always mint a new short code,
  even for a previously-shortened destination. With an Idempotency-Key and an
  identical validated payload: return the original short link; no new short code is
  created. With the same Idempotency-Key but a different payload: reject with an
  explicit conflict outcome (illustrated by the human candidate as HTTP 409
  Conflict; the concrete transport/protocol realization is deferred to planning).
  Analytics are tracked separately per short code — never aggregated across
  multiple codes that happen to share a destination URL.
- Q: When a caller creates a short link without specifying an expiration, should
  the link expire automatically after a default period, or remain active
  indefinitely until explicitly deleted? (AMB-006, reclassified from the originally
  proposed PVT-005 — this is observable required behavior, not a tuning number) →
  A: No default expiration. If `expiresAt` is omitted, the link remains active until
  explicitly deleted. If supplied, `expiresAt` must be a valid timestamp strictly in
  the future; an invalid or past timestamp is rejected at creation time and no link
  is created. At or after `expiresAt`, the system stops redirecting and returns an
  explicit "Gone" outcome (illustrated by the human candidate as HTTP 410 Gone, now
  confirmed as part of the functional contract — see note below). An expired
  resolution attempt MUST NOT increment successful-redirect analytics. The human
  candidate additionally confirmed that HTTP 409 Conflict (AMB-001, above) is an
  explicit required API outcome, not merely an illustrative detail deferred to
  planning — see FR-113's revision.
- Q: Should redirect analytics capture only aggregate, per-short-code facts, or
  also per-resolution detail about the requester? (AMB-002) → A: Aggregate only,
  per short code: total count of successful redirects, and the timestamp of the
  last successful redirect (null if the link has never been successfully resolved;
  count starts at 0). Only redirect responses actually issued by this service count
  as "successful" — this does not prove the destination page loaded. Unknown,
  expired, rejected, or failed requests MUST NOT increment the count. No IP
  address, referrer, user agent, geography, or visitor identifier is collected or
  persisted for analytics. Per-event history (a list of individual past
  resolutions) is explicitly **not** a required user-facing feature — only the
  aggregate counter and last-timestamp are required.

- Q: Is authentication for who may act as a human approver in scope for this
  specification, or fully deferred to planning? (AMB-005) → A: Required behavior,
  mechanism deferred. Approval and rejection actions MUST require authentication
  and authorization: unauthenticated callers are rejected, and authenticated
  actors lacking the required approval role are rejected. The approver identity
  MUST be derived from verified credentials, never from a caller-supplied name.
  Agent identities (automated/AI actors) MUST NOT approve their own work and MUST
  NOT have access to human-approval credentials. Every approval decision MUST
  record: identity, role, decision, rationale, timestamp, workflow/gate ID, and the
  exact artifact revision approved — and that approval is bound to that revision; a
  material change to the approved artifact invalidates the approval and requires
  human review again (reinforcing FR-501/FR-502). The concrete authentication
  *mechanism* remains deferred to `/speckit-plan` and the ADR gate; a minimal local
  demonstration mechanism is acceptable there provided its trust boundary and
  limitations are made explicit and are tested. This decision does not add general
  URL-shortener end-user authentication — that stays excluded (see Exclusions).

- Q: Should Human Reviewer/Approver and Release Owner be modeled as genuinely
  distinct approval authorities, or is a single generic human role an acceptable
  simplification? (AMB-003) → A: Distinct roles, enforced. Requirements and
  architecture approval gates require the reviewer/approver role. Final release and
  submission approval gates require the release-owner role. For this single-operator
  prototype, the same authenticated human candidate may hold both roles — this is
  role *separation* (distinct, individually-checked role grants), not a claim of
  independent-person separation of duties. Each decision is recorded separately
  with verified identity, the specific authorizing role used, rationale, timestamp,
  gate ID, and artifact revision. An approval recorded under one role MUST NOT
  automatically satisfy a gate that requires a different role — a reviewer/approver
  identity is not thereby authorized for release. Agent identities cannot satisfy
  any human-approval gate at all (generalizing FR-309 beyond the self-approval
  case).

### Human Gate 3 Review (2026-09-10)

Raised and resolved during consistency review, before ratifying Human Gate 3 —
distinct from the five-question Session above:

- Q: FR-106's "MUST NOT block or measurably delay" wording was not a testable
  criterion, and it silently left open whether an analytics failure could block a
  redirect. Should redirect availability or analytics accuracy take priority under
  an analytics-subsystem failure? (AMB-007) → A: Redirect availability wins.
  Normal operation: count accurately, no duplicates. Under an analytics failure:
  the redirect still succeeds; counts may lag/undercount; degradation MUST be
  observable via operational metrics/logs (FR-115) and a per-short-code
  completeness status (FR-107) — the system MUST NOT claim an exact durable count
  while degraded. The numeric latency budget and recovery-after-failure behavior
  are deferred to an ADR at `/speckit-plan` (`PVT-001`). See FR-105/106/107/115.
- Q: How should an idempotent replay behave once the original link has expired or
  been deleted, and does the `expiresAt`-must-be-future check re-run on every
  replay (creating a contradiction with returning the original result)? → A: The
  future-timestamp check (FR-114) applies only to first-time creation, never to a
  replay of an existing key — but syntax validation and the payload comparison
  still run on every replay, to correctly distinguish a matching resubmission
  (FR-112) from a conflicting one (FR-113 → 409). A replay always returns the
  original creation result, never recreating or reactivating the link; whether the
  link currently resolves is answered independently by resolution (FR-103/FR-104).
  Idempotency records are retained indefinitely, surviving restarts, independent of
  the short link's own lifecycle (FR-116) — a disclosed prototype-scope choice, not
  a claim of universal idempotency-key convention. See FR-112/113/114/116.
- Q: Does the "5 minute" MTTR figure in `SC-004`/`PVT-004` represent an approved
  target? → A: No — removed. A numeric MTTR target requires the measurement
  population, start/end events, and exclusions (per FR-603 and Constitution
  Principle IX) to be defined at `/speckit-plan` *first*; no number is proposed in
  this specification until that definitional work exists. See Success Criteria.
- Checklist correction: the "Feature meets measurable outcomes" item was
  previously described as re-validated at `/speckit-analyze` — corrected: that
  command is a read-only, static cross-artifact consistency check and produces no
  execution evidence by itself. Only executed validation (real tests run) confirmed
  at `/speckit-converge` (which executes the applicable quality suite) constitutes
  runtime proof of an outcome. See `checklists/requirements.md`.

### Planning Obligations Recorded During Clarification

The following are not resolved here — they are explicit obligations for
`/speckit-plan` to address, surfaced while answering the clarification questions
above, so they are not lost between stages:

- (From AMB-007, narrowed at Human Gate 3 review — the trade-off itself is now
  resolved; only the calibration remains open) Propose, via an ADR, the specific
  analytics latency budget (`PVT-001`) and the mechanism and recovery behavior for
  restoring accurate counting after an analytics failure clears.
- (From AMB-005) Select and document the concrete approver-authentication
  mechanism, its trust boundary, and its explicit limitations for this local
  demonstration prototype; the mechanism must be tested, not merely described.
- (AMB-004, not asked this session — a design decision, not a behavioral
  ambiguity) Determine which workflow stages are safe to execute in parallel
  without concurrent-write conflicts on shared workflow state; this specification
  only requires that synchronization points be explicit and observable (FR-202),
  not which specific stages qualify.
- (PVT-002, PVT-003 — numeric/calibration parameters, not required behavior) Set
  the bounded-retry attempt ceiling and backoff, and the per-attempt timeout
  window. Remain proposals pending approval at planning; see Proposed Validation
  Targets below.
- (MTTR — corrected at Human Gate 3 review; no longer just "pending approval," the
  definitional prerequisites must exist *before* any number is proposed) Define
  the measurement population (recovered events only), failure-detected /
  recovery-start / recovery-complete timestamps, exclusions, and unrecovered-
  failure reporting (FR-603); only then propose a numeric MTTR target for
  approval.

**Note on interface-level confirmations**: Two clarifications above (AMB-001,
AMB-006) now bind this specification to specific HTTP status-code outcomes (409
Conflict for idempotency-key payload mismatch; 410 Gone for expired resolution).
This confirms the public interface is HTTP-based for at least these two observable
outcomes; the remainder of the API surface, framework, and language choice remain
deferred to `/speckit-plan` and the ADR gate, per the Specification Rules.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — API Consumer creates and resolves short links (Priority: P1)

An API consumer submits a long URL and receives a short link; a second party later
requests the short link and is redirected to the original destination.

**Why this priority**: This is the base capability the entire demonstration domain
exists to prove. Without it, no other capability (analytics, expiration,
orchestration) has anything to operate on.

**Independent Test**: Can be fully tested by submitting a valid URL for shortening and
then requesting the returned short code, independent of any orchestration, approval,
or scenario machinery.

**Acceptance Scenarios**:

1. **Given** a syntactically valid URL using an allowed scheme, **When** the API
   consumer submits it for shortening, **Then** the system returns a unique short
   code and a resolvable short link, and the mapping is durably persisted.
2. **Given** an existing short link that has not expired, **When** any party requests
   that short link, **Then** the system resolves it to the original URL and records a
   redirect analytics event.
3. **Given** a URL using a disallowed or malformed scheme (e.g., `javascript:`, a
   bare local/loopback address, or a malformed string), **When** the API consumer
   submits it for shortening, **Then** the system rejects the request with a
   specific, observable validation error and creates no short link.
4. **Given** an expired short link (its `expiresAt` has passed), **When** any party
   requests it, **Then** the system does not redirect, returns an explicit "Gone"
   outcome (HTTP 410 Gone) distinct from "not found", and does not increment
   successful-redirect analytics for that attempt. (Resolved via AMB-006,
   Clarifications: Session 2026-09-10.)
4a. **Given** a short link created without an `expiresAt`, **When** any party
    requests it at any later time, **Then** the system continues to resolve it
    normally — it never expires on its own. (AMB-006)
4b. **Given** a shortening request supplying an `expiresAt` that is invalid or not
    strictly in the future, **When** the API consumer submits it, **Then** the
    system rejects the request and creates no short link. (AMB-006)
5. **Given** a shortening request submitted without an Idempotency-Key, **When** the
   same destination URL is submitted again (also without a key), **Then** the system
   creates a new, distinct short code each time — no destination-level deduplication
   occurs. (Resolved via AMB-001, Clarifications: Session 2026-09-10.)
6. **Given** a shortening request submitted with an Idempotency-Key, **When** the
   identical key is resubmitted with an identical validated payload, **Then** the
   system returns the original short link and creates no new short code. (AMB-001)
7. **Given** a shortening request submitted with an Idempotency-Key, **When** the
   identical key is resubmitted with a different payload, **Then** the system
   rejects the request with an explicit, observable conflict outcome and creates no
   short link. (AMB-001)
8. **Given** a freshly created short link that has never been successfully
   resolved, **When** its analytics summary is inspected, **Then** the
   successful-redirect count is 0 and the last-successful-redirect timestamp is
   null. (AMB-002)
9. **Given** a request for an unknown, expired, or otherwise rejected short code,
   **When** that request is made, **Then** the short code's successful-redirect
   count and last-redirect timestamp (if the code exists) MUST NOT change. (AMB-002)
10. **Given** the analytics subsystem is failing, **When** a valid, non-expired
    short code is requested, **Then** the redirect still succeeds, and the short
    code's analytics completeness status becomes (or remains) `degraded` — the
    redirect is never blocked or failed on account of the analytics failure.
    (AMB-007, FR-105, FR-106)
11. **Given** an idempotency key whose original short link has since expired or
    been deleted, **When** the identical validated payload is resubmitted under
    that key, **Then** the system returns the original creation result (the
    original short code) without recreating or reactivating the link — a
    subsequent resolution request for that code still follows its own current
    lifecycle state (e.g., still returns 410 Gone if expired). (Human Gate 3
    review, FR-112)
12. **Given** a stored idempotency record, **When** the service restarts and the
    identical key and validated payload are resubmitted afterward, **Then** the
    system still returns the original creation result — the idempotency record
    survives the restart. (FR-116)

---

### User Story 2 — Software Engineer initiates and inspects an orchestration workflow (Priority: P1)

A software engineer (or an automated caller acting on their behalf) submits a
requirement-shaped input to the orchestration system and can inspect the resulting
workflow's state, dependency graph, and decision lineage at any point, including
mid-execution.

**Why this priority**: This is the capability the assessment's "central
differentiator" (per the constitution's Project Context) actually measures. It must
be demonstrable independently of which of the three required scenarios is running.

**Independent Test**: Can be fully tested by creating a workflow instance and
querying its state, without needing a human approval to occur first (approval is
exercised in User Story 3).

**Acceptance Scenarios**:

1. **Given** a submitted requirement, **When** the orchestration system ingests it,
   **Then** a workflow instance is created with a persisted, unique correlation
   identifier and an explicit initial state.
2. **Given** a running or completed workflow instance, **When** the software engineer
   inspects it, **Then** the system exposes its current state, its dependency graph
   (or equivalent explicit stateful model), the stages that ran sequentially, the
   stages that ran in parallel, all synchronization points, and the full decision
   lineage recorded so far — not merely a final status string.
3. **Given** a workflow with at least two independent stages, **When** those stages'
   preconditions are simultaneously satisfied, **Then** the system executes them in
   parallel and records an explicit synchronization event before any stage that
   depends on both.
4. **Given** a workflow instance that must be inspected after process interruption
   (e.g., the executing session ends), **When** the software engineer queries it
   later, **Then** the system returns the same persisted state that existed at
   interruption, not a reconstructed or approximated one.

---

### User Story 3 — Human Reviewer/Approver governs a high-impact workflow decision (Priority: P2)

A human reviewer is presented with a workflow paused at a mandatory approval gate and
can approve, reject, or (implicitly, via non-response) leave it pending — and the
system must never treat that non-response as approval.

**Why this priority**: This is the project's primary safety property (constitution
Principle III) and is what separates governed orchestration from unattended
automation. It depends on User Story 2's workflow model existing first.

**Independent Test**: Can be fully tested by driving a workflow to a known approval
gate (e.g., an architecture-sensitive or policy-exception decision) and exercising
approve, reject, and timeout/non-response paths independently.

**Acceptance Scenarios**:

1. **Given** a workflow reaches a stage requiring human approval (per the list in
   FR-201), **When** the stage is entered, **Then** the workflow transitions to an
   explicit "awaiting approval" state and does not proceed to any dependent stage.
2. **Given** a workflow awaiting approval, **When** the human reviewer explicitly
   approves it, **Then** the workflow resumes, and the approval (actor, timestamp,
   decision, rationale if provided) is recorded in the decision lineage.
3. **Given** a workflow awaiting approval, **When** the human reviewer explicitly
   rejects it, **Then** the workflow transitions to a defined rejected/blocked
   terminal or remediation state — never silently to "approved".
4. **Given** a workflow awaiting approval, **When** no response is received within
   the workflow's defined timeout window, **Then** the system does not proceed as if
   approved; it transitions to an explicit escalation or safe-stop state and records
   the timeout as its own audited event.
5. **Given** a workflow awaiting approval, **When** an unauthenticated caller
   attempts to approve or reject it, **Then** the system rejects the attempt, the
   workflow remains awaiting approval, and the rejected attempt is itself an
   audited event. (AMB-005)
6. **Given** a workflow awaiting approval, **When** an authenticated caller who
   lacks the required approval role attempts to approve or reject it, **Then** the
   system rejects the attempt on authorization grounds, distinct from the
   unauthenticated case. (AMB-005)
7. **Given** a workflow awaiting approval, **When** an agent (automated/AI) identity
   attempts to approve or reject at *any* gate, whether or not the work is its own,
   **Then** the system rejects the attempt unconditionally — no agent identity can
   satisfy a human-approval gate, under any role. (AMB-005, generalized by AMB-003)
8. **Given** a workflow stage was approved against a specific artifact revision,
   **When** that artifact is materially changed afterward, **Then** the prior
   approval is invalidated and the stage returns to awaiting-approval against the
   new revision — a stale approval MUST NOT be treated as still valid. (AMB-005,
   FR-311)

---

### User Story 4 — Release Owner determines release readiness (Priority: P3)

A release owner requests a release-readiness determination for the current state of
the repository and receives one of exactly three governed outcomes, each backed by
verifiable evidence.

**Why this priority**: This is the terminal governance outcome of the whole system,
but it is meaningless without Stories 1–3 already functioning, so it is correctly
lower priority for build sequencing even though it is high-stakes.

**Independent Test**: Can be fully tested by requesting a release-readiness
determination against a known repository state and verifying the outcome matches the
state of mandatory gates and policy checks.

**Acceptance Scenarios**:

1. **Given** all mandatory requirements, scenarios, security controls, and governance
   gates for the current scope are complete and evidenced, **When** the release owner
   requests a readiness determination, **Then** the system returns `READY` with a
   traceable evidence index.
2. **Given** all mandatory items are complete except for explicitly disclosed,
   human-accepted limitations, **When** requested, **Then** the system returns `READY
   WITH ACCEPTED LIMITATIONS` and lists each limitation with its disclosure record.
3. **Given** any mandatory compliance/change-control policy check has an unresolved
   `FAIL` or an unapproved/expired exception, **When** requested, **Then** the system
   returns `NOT READY` and MUST NOT return `READY` under any circumstance while that
   condition holds.
4. **Given** an identity holding only the reviewer/approver role (not the
   release-owner role), **When** that identity attempts to authorize a
   release-readiness or final-submission gate, **Then** the system rejects the
   attempt — an earlier requirements/architecture approval by that identity does
   not carry over into release authority. (AMB-003, FR-312, FR-313)

---

### User Story 5 — Assessment Reviewer verifies a specific claim end-to-end (Priority: P3)

An assessment reviewer picks any specific claim made by the system (e.g., "this
workflow retried twice then recovered") and can trace it to a concrete, reproducible
artifact and command, without trusting a generated summary.

**Why this priority**: Directly enforces constitution Principle XI ("a
Claude-generated summary...is not itself evidence"); it is the reviewer-facing
consequence of every other story and is naturally validated last, once evidence exists
to check.

**Independent Test**: Can be fully tested by selecting any single audited event and
confirming it resolves to a real, executed artifact rather than a narrative claim.

**Acceptance Scenarios**:

1. **Given** any entry in the audit trail, **When** the assessment reviewer inspects
   it, **Then** it includes actor type, action, timestamp, affected artifact or
   state, result, and reason — sufficient to independently reconstruct that step.
2. **Given** a claim of "demonstration metric" (e.g., a measured MTTR value), **When**
   the reviewer inspects it, **Then** it is visibly and unambiguously labeled as
   demonstration data, distinct from any production-style statistic, per Constitution
   Principle IX.

---

### Scenario A — Greenfield: well-defined new requirement (traces to FR-6xx)

A complete, consistent, testable requirement that is within approved policy and
architecture boundaries proceeds through decomposition, design, implementation,
testing, documentation, and validation to release-readiness *without* an artificial
clarification gate being forced merely to demonstrate one.

**Acceptance Scenarios**:

1. **Given** a requirement that passes an explicit requirement-quality check
   (complete, consistent, testable, within approved policy/architecture boundaries),
   **When** it enters the orchestration system, **Then** the system records that the
   check was performed, records why clarification was judged unnecessary, and
   proceeds directly to decomposition — the "why" record is itself required evidence,
   not an assumed pass.
2. **Given** a greenfield workflow already in flight, **When** material ambiguity is
   discovered mid-flight, **Then** only the affected path is suspended (not the whole
   workflow), governed clarification and downstream impact analysis are invoked, and
   the workflow resumes from the correct prior state only after explicit human
   approval.
3. **Given** a completed greenfield run, **When** inspected, **Then** it shows the
   full path Requirement → Decomposition → Design → Implementation → Testing →
   Documentation → Validation → Release Readiness with traceable evidence at each
   step.

### Scenario B — Brownfield: change against the existing system (traces to FR-6xx)

An enhancement, refactor, or defect correction against the already-built URL
shortener is preceded by a mandatory impact analysis before any code changes.

**Acceptance Scenarios**:

1. **Given** an approved brownfield change request, **When** the workflow begins,
   **Then** the system identifies and records impacted components, interfaces, data
   flows, tests, documentation, regression risks, and rollout/rollback
   considerations, *before* any code is modified.
2. **Given** the impact analysis is incomplete or not yet reviewed, **When**
   implementation is attempted, **Then** the system blocks the attempt — code changes
   for a brownfield scenario MUST NOT precede a recorded impact analysis.
3. **Given** a completed brownfield run, **When** inspected, **Then** the recorded
   regression risk assessment and the actual regression-test evidence produced are
   both present and consistent with each other.

### Scenario C — Ambiguous requirement: incomplete, unclear, or conflicting input (traces to FR-6xx)

An intentionally ambiguous input demonstrates that the system detects the ambiguity
and suspends rather than guessing.

**Acceptance Scenarios**:

1. **Given** an input with material ambiguity (as judged by the requirement-quality
   check in FR-601), **When** it enters the orchestration system, **Then** the system
   detects and classifies the ambiguity, and does not proceed to implementation.
2. **Given** a detected ambiguity, **When** the workflow suspends, **Then** the system
   requests human clarification, and the workflow remains in a blocked/clarification
   state until an explicit human decision is recorded — never auto-resolved and never
   inferred from elapsed time.
3. **Given** the human clarification is provided, **When** the decision is recorded,
   **Then** the system performs downstream impact analysis, updates affected
   artifacts, and resumes at the correct workflow state — not from the beginning and
   not from an arbitrary later point.

---

### Edge Cases

- What happens when two shortening requests for the identical destination URL arrive
  concurrently without an idempotency key? (Each creates its own short code per
  FR-108/AMB-001; FR-110 governs correctness of the concurrent creation itself.)
- What happens when two requests race using the *same* idempotency key with
  identical payloads? (Both MUST resolve to a single created short link — the
  system must not create two short codes for one key under concurrent submission;
  see FR-112, FR-110.)
- What happens when a redirect is requested for a short code that was never issued?
  (Distinguished from "expired" — see US1 Acceptance Scenario 4 and FR-103.)
- What happens when the persistence layer is unavailable at the moment of short-link
  creation or resolution? (See FR-109 — persistence-failure behavior must be an
  observable, non-silent failure mode, not a hang or a false success.)
- What happens when a bounded retry is exhausted without recovery? (See FR-403 — the
  system must reach a deterministic terminal outcome, not retry indefinitely.)
- What happens when rollback is requested for an action that is not technically
  reversible? (See FR-404 — compensation must be used instead, and claiming rollback
  where infeasible is itself a defect, not a simplification, per Constitution
  Principle VIII.)
- What happens when a policy check fails during an in-flight workflow that has
  already passed earlier gates? (See FR-301 — the failure blocks downstream
  progression regardless of earlier gate outcomes.)
- What happens when a dynamic replanning event is triggered by an upstream artifact
  change *after* a human has already approved a downstream stage? (See FR-501 — the
  affected approval must be invalidated and re-requested, not silently carried
  forward.)
- What happens when two workflow stages are marked parallel but actually write to the
  same underlying state? (See AMB-004 — this is a design-time hazard the plan stage
  must resolve; this specification only requires that synchronization points be
  explicit and observable.)
- What happens when an approval response arrives after the timeout window has already
  triggered escalation? (See FR-204 — the late response is recorded but does not
  retroactively unwind the escalation state.)

---

## Requirements *(mandatory)*

### Functional Requirements — URL Shortener Domain

- **FR-101** (Confirmed): The system MUST accept a URL for shortening only if it is
  syntactically valid and uses an explicitly allowed scheme; it MUST reject all
  others with a specific, observable error and MUST NOT create a short link for a
  rejected submission.
- **FR-102** (Confirmed): The system MUST generate a short code that is unique among
  all currently active (non-expired, non-deleted) short links at the moment of
  creation.
- **FR-103** (Confirmed): The system MUST resolve a request for a valid, active short
  code to its original URL, and MUST distinguish, as observably different outcomes,
  the cases of (a) unknown short code, (b) expired short code, and (c) successful
  resolution.
- **FR-104** (Confirmed — resolved via AMB-006, Clarifications: Session 2026-09-10):
  The system MUST support an optional `expiresAt` attribute on a short link. A short
  link created without `expiresAt` MUST remain active indefinitely (no default
  expiration) until explicitly deleted. A short link created with `expiresAt` MUST
  stop resolving successfully at or after that timestamp, returning an explicit
  "Gone" outcome (HTTP 410 Gone) distinct from "not found," and MUST NOT increment
  successful-redirect analytics for a resolution attempt made at or after
  `expiresAt`.
- **FR-114** (Confirmed — resolved via AMB-006, refined at Human Gate 3 review): The
  system MUST validate, at creation time, that a caller-supplied `expiresAt` is a
  valid timestamp strictly in the future; an invalid or non-future `expiresAt`
  MUST be rejected with no short link created. This check applies to any
  first-time creation (with or without an idempotency key). Per FR-112, it is
  **not** repeated for an identical replay of an existing idempotency key, since
  that check is time-dependent and would otherwise contradict returning the
  original result for an unchanged payload.
- **FR-105** (Confirmed — resolved via AMB-002 and AMB-007, Clarifications: Session
  2026-09-10 and Human Gate 3 review): During normal operation, the system MUST
  accurately increment a per-short-code successful-redirect counter and update a
  per-short-code last-successful-redirect timestamp exactly once for each
  resolution this service actually redirects, with no duplicate counting. An
  unknown, expired, rejected, or otherwise failed resolution attempt MUST NOT
  increment the counter or update the timestamp. A successful count reflects only
  that this service issued the redirect response — it is not proof the destination
  page loaded. **Redirect availability takes priority over analytics accuracy**: an
  analytics-subsystem failure MUST NOT prevent, block, or fail an otherwise-valid
  redirect. During such a failure, the counter and timestamp MAY lag or undercount;
  the system MUST NOT represent the count as an exact, durable figure while
  degraded (see FR-107's completeness status). This is a decided trade-off, not an
  open alternative.
- **FR-106** (Confirmed — resolved via AMB-007): Analytics capture MUST add no more
  than a bounded latency budget to the redirect response. The specific numeric
  budget and the capture mechanism are proposed at `/speckit-plan` as `PVT-001` and
  require an ADR (guide Section 10, item 16: "Analytics consistency"); that ADR
  MUST also propose recovery behavior for restoring accurate counting once an
  analytics failure clears.
- **FR-107** (Confirmed — resolved via AMB-001, AMB-002, and AMB-007): The system
  MUST expose, per short code, the total successful-redirect count, the last
  successful redirect timestamp (null if never successfully resolved), and an
  analytics completeness status of at least `complete` or `degraded`. While status
  is `degraded`, the system MUST NOT claim the count is exact or durable. Analytics
  MUST be scoped per short code and MUST NOT be aggregated across multiple short
  codes that happen to share a destination URL (AMB-001). Exposing a per-event
  history (a list of individual past resolutions) is explicitly **not** required
  (AMB-002); an implementation MAY retain per-event records internally for other
  purposes (e.g., the audit trail under FR-601–FR-606), but is not required to
  expose them as an analytics feature. The system MUST NOT collect or persist IP
  address, referrer, user agent, geography, or any visitor identifier for
  analytics purposes.
- **FR-115** (Confirmed — AMB-007): An analytics-subsystem failure MUST be
  observable through operational health/metrics or logs (see FR-111), independent
  of and in addition to the per-short-code completeness status (FR-107) — a
  reviewer must be able to detect degraded analytics without inspecting any
  specific short link.
- **FR-108** (Confirmed — resolved via AMB-001, Clarifications: Session 2026-09-10):
  The system MUST use request-level idempotency, not URL-level deduplication. A
  shortening request submitted without a caller-supplied idempotency signal MUST
  always create a new, distinct short code, even if an active short code already
  exists for the same destination URL.
- **FR-112** (Confirmed — resolved via AMB-001, refined at Human Gate 3 review,
  Clarifications: Session 2026-09-10): When a shortening request is submitted with
  a caller-supplied idempotency key that already has a stored record, the system
  MUST still validate the incoming request's syntax (per FR-101 and related
  time-independent validation rules) and compare the resulting validated payload
  against the stored original validated payload. If they match exactly, the system
  MUST return the original creation result (the original short code) and MUST NOT
  create a new short link. The system MUST NOT recreate or reactivate the link if
  it has since expired (FR-104) or been deleted — the replay returns the original
  *creation* result only; whether the link currently resolves follows its own
  present lifecycle state, evaluated independently at resolution time (FR-103,
  FR-104).
- **FR-113** (Confirmed — resolved via AMB-001 and reaffirmed via AMB-006,
  Clarifications: Session 2026-09-10): When a shortening request is submitted with
  a caller-supplied idempotency key and a validated payload that does *not* match
  the stored original is subsequently submitted under the same key, the system
  MUST reject the request with an explicit HTTP 409 Conflict outcome and MUST NOT
  create a short link. This is a confirmed functional requirement, not an
  illustrative detail — the human candidate explicitly elevated it from a deferred
  protocol detail to a required API outcome.
- **FR-109** (Confirmed): The system MUST handle a persistence-layer failure during
  creation or resolution as an observable, non-silent failure — never a false
  success and never an indefinite hang.
- **FR-110** (Confirmed): The system MUST remain correct under concurrent creation and
  concurrent resolution requests, including concurrent requests for the same
  destination URL and the same short code.
- **FR-111** (Confirmed): The system MUST expose an operational health indicator
  distinguishing at least "healthy", "degraded", and "unavailable" states for the URL
  shortener's own dependencies.
- **FR-116** (Confirmed — Human Gate 3 review, Clarifications: Session 2026-09-10):
  Idempotency records MUST be retained indefinitely for this prototype, surviving
  process restarts, and independently of the referenced short link's own
  lifecycle — deleting or expiring a short link MUST NOT erase its associated
  idempotency record. This is a deliberate prototype-scope choice consistent with
  the indefinite-retention pattern already adopted for short links (AMB-006), not
  a claim that indefinite retention is a universal idempotency-key convention; the
  resulting storage growth is an accepted, disclosed trade-off for this prototype
  (Constitution Principle VII), to be revisited if this were to move toward
  production scale.

### Functional Requirements — Orchestration and Workflow

- **FR-201** (Confirmed): The system MUST represent a workflow's structure as an
  explicit dependency graph or an equivalent stateful model that is inspectable, not
  merely an implicit sequence of function calls.
- **FR-202** (Confirmed): The system MUST support stages that execute sequentially,
  stages that execute in parallel, explicit synchronization points where parallel
  stages converge, and conditional branching based on workflow state.
- **FR-203** (Confirmed): Every workflow stage MUST have an explicit definition of
  its inputs, outputs, entry criteria, exit criteria, owning actor, and failure
  behavior, inspectable independent of that stage having run yet.
- **FR-204** (Confirmed): The system MUST persist workflow state, cross-stage
  context, artifact provenance, and decision lineage such that a workflow instance
  can be inspected accurately after an interruption, without reconstruction from
  external memory.
- **FR-205** (Confirmed): The system MUST support controlled resumption of an
  interrupted-but-recoverable workflow from its persisted state, not from the
  beginning.
- **FR-206** (Confirmed): The system MUST support workflow creation (triggering a new
  run) and workflow inspection (querying an existing run's state, graph, and lineage)
  as independently usable capabilities.

### Functional Requirements — Human Governance and Policy Enforcement

- **FR-301** (Confirmed): The system MUST enforce a defined list of mandatory human
  approval gates (at minimum: unresolved ambiguity, architecture approval,
  security-sensitive action, destructive/irreversible action, constitutional or
  policy exception, material risk acceptance, release readiness, and final
  submission) and MUST NOT allow a workflow to bypass an applicable gate.
- **FR-302** (Confirmed): The system MUST record every gate decision as one of:
  approved, rejected, or timed-out/escalated — and MUST NEVER interpret the absence
  of a response as approval.
- **FR-303** (Confirmed): The system MUST evaluate every applicable compliance or
  change-control policy check and record exactly one outcome per check: `PASS`,
  `FAIL`, `EXCEPTION-REQUESTED`, or `NOT-APPLICABLE`, together with the policy version
  evaluated.
- **FR-304** (Confirmed): A `FAIL` outcome on a mandatory policy check MUST block
  downstream workflow progression until resolved or superseded by an approved,
  unexpired exception.
- **FR-305** (Confirmed): An `EXCEPTION-REQUESTED` outcome MUST require an explicit,
  recorded human approval before the workflow may proceed, and that record MUST
  include the applicable policy, reason, scope, approving authority, compensating
  control, approval timestamp, and expiry/review condition.
- **FR-306** (Confirmed): A material change to approved requirements, architecture,
  schemas, workflow states, security controls, or release criteria MUST pass through
  a recorded impact analysis and change approval before it takes effect.
- **FR-307** (Confirmed — resolved via AMB-005, Clarifications: Session 2026-09-10):
  The system MUST reject an approval or rejection action from an unauthenticated
  caller, and MUST reject one from an authenticated caller who lacks the required
  approval role for that gate.
- **FR-308** (Confirmed — AMB-005): The system MUST derive the approver's recorded
  identity from verified credentials; it MUST NOT accept a caller-supplied name as
  the identity of record for an approval decision.
- **FR-309** (Confirmed — resolved via AMB-005 and generalized via AMB-003,
  Clarifications: Session 2026-09-10): No agent (automated/AI) identity may satisfy
  any mandatory human-approval gate, for any role — including but not limited to
  approving its own work — and no agent identity may have access to human-approval
  credentials.
- **FR-310** (Confirmed — AMB-005): Every recorded approval decision MUST include:
  identity, role, decision (approve/reject), rationale, timestamp, the workflow/gate
  identifier, and the exact artifact revision approved.
- **FR-311** (Confirmed — AMB-005): An approval MUST be bound to the specific
  artifact revision it approved. A material change to that artifact MUST invalidate
  the approval and require human re-approval before the workflow may proceed
  (reinforcing FR-501/FR-502's replanning-invalidation rule).
- **FR-312** (Confirmed — AMB-003): The system MUST enforce distinct, individually
  checked approval roles: the reviewer/approver role for requirements-approval and
  architecture-approval gates, and the release-owner role for release-readiness and
  final-submission gates. The same authenticated identity MAY hold both roles, but
  each gate MUST check for its own specifically required role.
- **FR-313** (Confirmed — AMB-003): An approval recorded under one role MUST NOT be
  treated as satisfying a gate that requires a different role. In particular, a
  reviewer/approver's earlier approval MUST NOT automatically authorize release.

### Functional Requirements — Reliability, Retry, and Recovery

- **FR-401** (Confirmed): The system MUST classify a failure as transient or
  permanent, and MUST apply retries only to failures classified as transient.
- **FR-402** (Confirmed): Retries MUST be bounded, with an explicit maximum attempt
  count and an explicit backoff/timeout behavior (see PVT-002, PVT-003 for proposed
  numeric defaults).
- **FR-403** (Confirmed): Exhausting the bounded retry limit without recovery MUST
  lead to a deterministic terminal outcome (fallback, safe-stop, or an equivalent
  defined state) — never an indefinite retry loop and never a silent hang.
- **FR-404** (Confirmed): The system MUST distinguish rollback (technically reversing
  an action) from compensation (offsetting an action that cannot be reversed), and
  MUST use compensation wherever rollback is not technically feasible for the
  specific action in question; claiming rollback for an infeasible case is a
  specification violation.
- **FR-405** (Confirmed): The system MUST define and enter a safe-stop state when
  continuing execution would be unsafe (e.g., irrecoverable failure, unresolved
  mandatory policy failure, exhausted retries with no valid fallback), and MUST NOT
  continue processing the affected workflow path past that point without explicit
  human direction.
- **FR-406** (Confirmed): Repeatable operations (e.g., short-link creation, workflow
  stage retries) MUST be idempotent with respect to at least one caller-supplied or
  system-generated idempotency signal.

### Functional Requirements — Dynamic Replanning and Decision Lineage

- **FR-501** (Confirmed): When an upstream artifact (requirement, architecture
  decision, contract, or schema) changes materially after downstream stages or
  approvals already occurred, the system MUST identify the affected downstream
  artifacts and approvals, invalidate them, and trigger a governed replanning event
  rather than silently continuing on stale approvals.
- **FR-502** (Confirmed): Replanning MUST preserve governance: any approval that
  applied to now-invalidated work MUST be re-requested, not carried forward
  automatically.
- **FR-503** (Confirmed): Every decision (human or system-classification) that
  affects workflow direction MUST be appended to a persisted decision lineage that
  is never overwritten, only extended.

### Functional Requirements — Audit, Evidence, and Reliability Metrics

- **FR-601** (Confirmed): Every orchestration execution MUST carry a unique
  correlation/run identifier, and every recorded event for that execution MUST be
  attributable to it.
- **FR-602** (Confirmed): Every audit event MUST record actor type, action,
  timestamp, affected artifact or state, result, and reason, sufficient for a
  reviewer to reconstruct the execution without additional context.
- **FR-603** (Confirmed): The system MUST support computing at least: workflow
  success rate, failure rate, retry frequency, rollback/compensation frequency, Mean
  Time to Recovery (MTTR) restricted to recovered failure events, and unrecovered
  failure count — reported separately from the MTTR figure, never blended into it.
- **FR-604** (Confirmed): Any reported metric derived from demonstration data MUST be
  visibly labeled as demonstration data and MUST NOT be presented as a production
  statistic.
- **FR-605** (Confirmed): The system MUST demonstrate Scenario A (greenfield),
  Scenario B (brownfield), and Scenario C (ambiguous requirement) as three materially
  distinct, independently evidenced executions, each producing its own audit trail,
  decision lineage, and terminal outcome.
- **FR-606** (Confirmed): A workflow stage or task report that claims execution
  (e.g., "code generated," "tests passed," "validation complete") MUST be backed by
  an artifact that exists in the repository and/or a validation command that was
  actually run, with its actual output retained as evidence; a narrative claim
  without both is not a satisfied requirement, and MUST be identified as simulated or
  illustrative if presented for demonstration purposes only.

### Key Entities

- **Short Link**: A mapping from a generated short code to a destination URL, with
  creation time, optional expiration, and status (active/expired/deleted). Owns no
  implementation detail (e.g., no storage engine implied).
- **Idempotency Record** (added via AMB-001, refined at Human Gate 3 review,
  Clarifications: Session 2026-09-10): An optional association between a
  caller-supplied idempotency key and the exact validated creation payload and
  short link it produced, used solely to detect an identical resubmission (return
  original) versus a conflicting resubmission (reject) under the same key. Not used
  for destination-URL-level deduplication. Retained indefinitely and independently
  of the referenced short link's own lifecycle (FR-116) — deleting or expiring the
  short link does not erase this record, and this record never recreates or
  reactivates the link.
- **Short Link Analytics Summary** (redefined via AMB-002 and AMB-007,
  Clarifications: Session 2026-09-10 and Human Gate 3 review; formerly "Redirect
  Analytics Event"): The required user-facing analytics surface per short code — a
  successful-redirect counter (starts at 0), a last-successful-redirect timestamp
  (null until first success), and a completeness status (`complete` or
  `degraded`). Carries no requester-identifying fields. Per-event history is not a
  required feature (an implementation may still log individual events internally
  for audit purposes under FR-601–FR-606, but that is a distinct concern from this
  analytics summary). The counter and timestamp are not claimed exact while status
  is `degraded` (FR-105, FR-107).
- **Workflow Instance (Orchestration Run)**: A single execution of the orchestration
  system against one ingested requirement, carrying a correlation identifier,
  current state, dependency graph, decision lineage, and terminal outcome once
  reached.
- **Workflow Stage**: A node in a workflow instance's dependency graph, with defined
  inputs, outputs, entry/exit criteria, owning actor, and failure behavior.
- **Approval Decision**: A recorded human response (approve/reject) or an
  escalation/timeout event at a specific gate, with (as resolved via AMB-005,
  Clarifications: Session 2026-09-10) verified identity, role, decision, rationale,
  timestamp, workflow/gate identifier, and the exact artifact revision approved;
  bound to that revision, and invalidated by a material change to it.
- **Policy Evaluation**: A recorded outcome (`PASS`/`FAIL`/`EXCEPTION-REQUESTED`/
  `NOT-APPLICABLE`) for one policy check against one policy version, for one
  workflow instance.
- **Policy Exception**: An approved, time-bounded deviation from a specific policy
  check, with its full required record (policy, reason, scope, authority,
  compensating control, timestamp, expiry).
- **Audit Event**: An individual, immutable record of a state transition, decision,
  retry, failure, or replanning event, attributable to a workflow instance.
- **Scenario Record**: The evidence bundle (input, decomposition, orchestration path,
  approvals, validation, terminal outcome) produced by running Scenario A, B, or C.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001** (Confirmed, qualitative): A reviewer can create a short link, resolve it,
  and observe a captured analytics event, entirely through the system's own exposed
  interface, without inspecting source code to understand the outcome.
- **SC-002** (Confirmed, qualitative): A reviewer can trigger all three required
  scenarios (greenfield, brownfield, ambiguous requirement) and observe three
  materially different, independently evidenced orchestration paths and terminal
  outcomes.
- **SC-003** (Confirmed, qualitative): A reviewer can locate, for any given audited
  claim, the exact repository artifact and command that produced it, without relying
  on a generated summary as the only evidence.
- **SC-004** (Deferred — no target yet, corrected at Human Gate 3 review): A
  bounded-retry workflow path that encounters a transient failure and
  subsequently recovers has a measurable recovery duration, reported as part of
  MTTR (FR-603). **No numeric target is proposed here.** Per Constitution
  Principle IX and the guide's MTTR definition, a target may only be proposed once
  `/speckit-plan` defines the measurement population (recovered events only),
  failure-detected / recovery-start / recovery-complete timestamps, and
  exclusions — see `PVT-004` below, which is intentionally left without a number.
- **SC-005** (Confirmed, qualitative): A human reviewer can reject a workflow at any
  mandatory approval gate and observe the workflow entering a distinct, non-approved
  terminal or remediation state — never silently proceeding.
- **SC-006** (Confirmed, qualitative): 100% of mandatory policy checks executed during
  a demonstration run produce a recorded outcome (`PASS`/`FAIL`/`EXCEPTION-REQUESTED`/
  `NOT-APPLICABLE`) with an identified policy version; none are silently skipped.

---

## Assumptions

- (Assumption) A single-operator/local demonstration deployment is sufficient; this
  specification does not assume multi-tenant isolation, horizontal auto-scaling, or a
  managed cloud environment (see Exclusions).
- ~~(Assumption)~~ **Confirmed via AMB-002** (Clarifications: Session 2026-09-10):
  "Analytics" means count- and timestamp-level aggregation per short code only, not
  user-level tracking, device fingerprinting, or geolocation. No longer an
  assumption — see FR-105/FR-107.
- ~~(Assumption)~~ **Confirmed via AMB-003** (Clarifications: Session 2026-09-10):
  The reviewer/approver and release-owner roles are enforced as distinct,
  individually-checked authorization roles (FR-312/FR-313), and the same
  authenticated human candidate may hold both for this single-operator prototype.
  This is deliberate role separation, not a claim of independent-person
  separation-of-duties — no longer an unstated assumption.
- (Assumption) "Operational health" (FR-111) refers to the URL shortener's own
  runtime and its direct dependencies (e.g., the persistence layer), not the
  orchestration system's health, which is covered separately by workflow-state
  inspection (FR-206).
- (Assumption) Short codes and destination URLs are not treated as containing
  regulated personal data for this demonstration; no data-residency or
  data-subject-rights handling is in scope. This assumption is revisited if the
  clarification stage surfaces a reason to change it.

## Constraints

- (Constraint, Confirmed) The assessment is timeboxed to 2–3 days; scope for this
  feature must fit a must-have/deferred-scope split established at planning, not
  everything enumerated here at maximal depth on day one.
- (Constraint, Confirmed) No framework, programming language, database, cloud
  provider, agent framework, or deployment platform may be chosen in this
  specification; that is deferred to `/speckit-plan` and the ADR gate.
- (Constraint, Confirmed) The system must run locally in a demonstrable, reviewable
  way; this specification does not assume a hosted, publicly reachable deployment.
- (Constraint, Derived from Constitution Principle VII) Complexity not justified by a
  requirement in this document or by demonstrability must be avoided — e.g., no
  distributed-systems machinery introduced merely because "orchestration" sounds like
  it warrants one.

## Exclusions

- (Exclusion) Custom/branded domains for short links.
- (Exclusion) User authentication/authorization for the URL-shortener's own end
  users (who may create or resolve short links) remains fully out of scope. This is
  distinct from approver authentication/authorization for the *orchestration and
  governance* surface, which — as resolved via AMB-005, Clarifications: Session
  2026-09-10 — **is** in scope as required behavior (FR-307–FR-311); only the
  concrete authentication *mechanism* for approvers is deferred to `/speckit-plan`
  and the ADR gate.
- (Exclusion) Horizontal scaling, multi-region deployment, or production-grade
  capacity planning; this is a production-oriented *prototype*, not
  production-*scale* infrastructure, per Constitution Principle VII.
- (Exclusion) Any competing orchestration or SDLC framework alongside SpecKit
  (explicitly forbidden by the constitution's Governing Methodology section).
- (Exclusion) Billing, quotas, or monetization of the URL-shortening capability.

---

## Ambiguities Requiring Clarification

These are intentionally **not resolved** by this specification, per the current task
instruction to keep material ambiguities visible. They are recorded here for
`/speckit-clarify` and MUST NOT be treated as decided until an explicit human decision
is recorded.

- **AMB-001** — **RESOLVED** (Clarifications: Session 2026-09-10). *Duplicate-request
  semantics (affected FR-108, FR-112, FR-113, FR-107)*: Resolved as request-level
  idempotency via an optional Idempotency-Key, not URL-level deduplication. See the
  Clarifications section above for the full decision and User Story 1 Acceptance
  Scenarios 5–7 for the resulting testable behavior.
- **AMB-002** — **RESOLVED** (Clarifications: Session 2026-09-10). *Analytics depth
  (affected FR-105, FR-107, Key Entities, Assumptions)*: Resolved as aggregate-only
  — per-short-code successful-redirect count and last-success timestamp, no
  requester-identifying data, no required per-event history. See the
  Clarifications section above and User Story 1 Acceptance Scenarios 8–9.
- **AMB-003** — **RESOLVED** (Clarifications: Session 2026-09-10). *Human-role
  separation (affected User Stories 3/4, Assumptions, added FR-312/FR-313)*:
  Resolved — reviewer/approver and release-owner are distinct, enforced roles; the
  same human candidate may hold both; an approval under one role never satisfies a
  gate requiring the other. See the Clarifications section above, User Story 4
  Acceptance Scenario 4, and User Story 3 Acceptance Scenario 7.
- **AMB-004** — *Parallel-path data-safety boundary (affects FR-202, Edge Cases)*:
  The specification requires explicit synchronization points for parallel stages but
  does not define which stages are safe to run in parallel without risking
  concurrent-write conflicts on shared workflow state. This is a design decision
  best resolved with plan-stage input, but the *requirement* that synchronization be
  explicit and observable is not itself ambiguous.
- **AMB-005** — **RESOLVED** (Clarifications: Session 2026-09-10). *Authentication
  assumption for the orchestration/approval surface (affected FR-301–FR-306, added
  FR-307–FR-311, Exclusions, Approval Decision entity)*: Resolved — approver
  authentication/authorization is required behavior (mechanism deferred to
  planning); agent self-approval and credential access are unconditionally
  forbidden; approvals are bound to a specific artifact revision. See the
  Clarifications section above and User Story 3 Acceptance Scenarios 5–8.
- **AMB-006** — **RESOLVED** (Clarifications: Session 2026-09-10; reclassified from
  the originally proposed `PVT-005`). *Default expiration behavior (affected
  FR-104, added FR-114)*: Resolved — no default expiration; an explicit
  `expiresAt`, if supplied, must be valid and strictly future or the request is
  rejected. See the Clarifications section above and User Story 1 Acceptance
  Scenarios 4/4a/4b.
- **AMB-007** — **RESOLVED** (Human Gate 3 review, 2026-09-10; raised during
  consistency review, not the original 5-question session). *Analytics durability
  vs. redirect availability trade-off (affected FR-105, FR-106, FR-107, added
  FR-115, Short Link Analytics Summary entity)*: Resolved — redirect availability
  takes priority; an analytics-subsystem failure never blocks or fails a valid
  redirect, counts may lag/undercount during that window with a visible
  `degraded` completeness status, and the exact numeric latency budget plus
  recovery behavior are deferred to an ADR at `/speckit-plan` (`PVT-001`). See
  User Story 1 Acceptance Scenario 10.

---

## Proposed Validation Targets

Numeric or measurable targets below are **proposals only**, per the guide's explicit
rule ("record a proposed validation target as an assumption requiring approval. Do
not represent it as a confirmed client requirement"). None are treated as approved
until you approve them, most likely alongside `/speckit-plan`.

- **PVT-001** (supports FR-106): Analytics capture adds no more than a small,
  documented fraction of overall redirect latency budget once a budget is set at
  planning; no specific millisecond figure is proposed here since that is a plan-
  stage decision informed by chosen technology.
- **PVT-002** (supports FR-402): Proposed default bounded-retry ceiling of 3 attempts
  for a transient failure, with exponential backoff, subject to change per stage.
- **PVT-003** (supports FR-402): Proposed default per-attempt timeout window
  sufficient to distinguish "slow" from "failed" for the operation in question; exact
  duration deferred to planning per operation type.
- **PVT-004** (supports SC-004) — **number removed at Human Gate 3 review**: The
  previously stated "under 5 minutes" figure was unsupported and has been struck.
  No MTTR target is proposed until `/speckit-plan` first defines: the measurement
  population (recovered events only, per FR-603), the failure-detected /
  recovery-start / recovery-complete timestamps, exclusions, and how unrecovered
  failures are counted and reported separately (never blended into the MTTR
  denominator). A numeric target may be proposed only after that definitional work
  exists, and will remain explicitly labeled demonstration data, never a
  production SLA, once proposed.
- ~~**PVT-005**~~ — **RESOLVED and reclassified as AMB-006** (Clarifications: Session
  2026-09-10): this turned out to be required behavior, not a tuning number. No
  default expiration applies; see FR-104, FR-114, and Clarifications above.
