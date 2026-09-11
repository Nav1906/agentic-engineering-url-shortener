# Tasks: Agentic Software Engineering System: URL Shortener

**Input**: [spec.md](./spec.md) (Approved), [plan.md](./plan.md) (9/10 ADRs
Accepted, ADR-0006 Rejected), [data-model.md](./data-model.md),
[contracts/openapi.yaml](./contracts/openapi.yaml) (structurally validated),
[research.md](./research.md), [docs/adr/](../../docs/adr/)

**Status**: Draft — not yet reviewed/approved. Per the guide's Prompt 6: no
code is implemented by this document; it is the dependency-aware task plan
`/speckit-implement` will execute against, once reviewed.

**Format per task** (per the guide's Prompt 6 Task Format, all 15 fields):
`ID` · `Title` · **Req**(uirement IDs) · **Scn**(ario/User-Story IDs) ·
**ADR** · **Path** · **Prereq**(uisites) · **Dep**(endencies) · **P**(arallel?)
· **Artifact** · **TDD** · **Validation** (exact command) · **Docs** (impact)
· **Trace** (ability update) · **Risk**/guardrail · **Done** (completion
criteria) · **Human** (approval requirement)

**16th field, added during the `/speckit-analyze` remediation pass (2026-09-10,
fixing finding E3)**: **SC**(uccess Criteria IDs, spec.md SC-001–SC-006) —
added only to the specific tasks that most directly produce or demonstrate a
given Success Criterion, not to all 99 tasks. Absence of an SC field on a
task does not mean it contributes nothing to a Success Criterion — it means
no single Success Criterion is *most* directly demonstrated by that specific
task; broader coverage still flows through the FR-level traceability chain.

`[P]` marks a task with no shared-file conflict against its concurrently-
eligible siblings — reused from the standard SpecKit convention, carrying the
same meaning as the guide's "parallelization status" field.

**Status markers, added 2026-09-11 after `/speckit-implement` ran T001–T099**
(`/speckit-implement`'s own "Done When" step: mark completed tasks `[X]`):
`- [x] **Txxx**` = this task's own Done criterion has genuinely passed, with
real retained evidence (a command, its output, and — where applicable — a
commit) cited in that task's own entry or in
`docs/final-engineering-summary.md`. `- [ ] **Txxx**` = not done; currently
only T100–T103 (governance-blocked per explicit instruction, never
attempted). No task is marked `[x]` on the strength of a written plan alone.

---

## Phase 0: Timebox and Scope Control

**Purpose**: the guide's explicitly required task group — establishes
must-have scope, deferred scope, day-level milestones, critical path,
checkpoint decisions, and stop conditions for the 2–3 day timebox, before
any other task begins.

- [x] **T001** — Ratify must-have vs. deferred scope for this timebox
  **Req**: all FR groups **Scn**: — **ADR**: — **Path**: this file (below)
  **Prereq**: none **Dep**: none **P**: no
  **Artifact**: the "Must-Have / Deferred" table below
  **TDD**: n/a (planning task) **Validation**: reviewer inspection, not a command
  **Docs**: this file **Trace**: plan.md § Planning Constraints
  **Risk**: scope inflation displacing mandatory validation — guarded by the stop condition in T003
  **Done**: table below exists and is unambiguous **Human**: implicit via this task list's review, no separate gate

**Must-Have** (blocks any `READY`/`READY WITH ACCEPTED LIMITATIONS` claim):
domain URL-shortener behavior (Groups 6–10), orchestration engine core
(Groups 11, 16–24), at least one authenticated approval path demonstrable
even if ADR-0006's isolation mechanism stays an accepted limitation (Group
19), audit/observability (Groups 25–27), all three scenarios (Groups 28–30)
at least minimally executed, release-readiness check (Group 39).

**Deferred** (explicitly labeled backlog, never silently dropped): full
compliance policy engine sophistication beyond a minimal manifest (Groups
12–15 kept minimal), Final Engineering Summary / Reviewer Navigation Guide
full generation (Groups 40–41 — stubbed now, completed at convergence),
egress network restriction for agent subprocesses, DNS-rebinding protection,
containerized deployment.

**Blocked** (distinct from deferred — not a scope choice, a governance gate;
added during `/speckit-analyze` remediation, 2026-09-10, finding F2): T100
(`scripts/bootstrap_credentials.py`), T101 (`scripts/approve.py`), T102
(`local-secrets/` setup), and T103 (the final agent-isolation launcher and
its security tests) — all in Group 19 — cannot start until you accept a
replacement mechanism for ADR-0006. This is not a timebox trade-off; it is
the project's core human-governance control (Constitution Principle III)
refusing to let a credential-handling code path get built without an
accepted isolation boundary around it.

- [x] **T002** — Define day-level milestones and critical path
  **Req**: — **Scn**: — **ADR**: — **Path**: this file **Prereq**: T001 **Dep**: T001 **P**: no
  **Artifact**: milestone table below **TDD**: n/a **Validation**: reviewer inspection
  **Docs**: this file **Trace**: plan.md §14 Delivery Sequence
  **Risk**: none material **Done**: table exists **Human**: no

| Day | Milestone | Critical path? |
|---|---|---|
| 1 | Engineering baseline + walking skeleton + domain model + API contracts + persistence (Groups 1–5) | Yes — nothing else can start without it |
| 1–2 | Core domain behavior (Groups 6–10) in parallel with orchestration engine core (Groups 11, 16–18) | Yes |
| 2 | Approval gates, reliability controls, audit (Groups 19–27) | Yes |
| 2–3 | Three scenarios (Groups 28–30), tests (Groups 31–36) | Yes |
| 3 | Documentation, setup, release-readiness, checkpoint decisions (Groups 37–39) | Yes |

- [x] **T003** — Define stop conditions and checkpoint decisions
  **Req**: — **Scn**: — **ADR**: — **Path**: this file **Prereq**: T001 **Dep**: T001 **P**: no
  **Artifact**: stop-condition list below **TDD**: n/a **Validation**: reviewer inspection
  **Docs**: this file **Trace**: plan.md § Planning Constraints
  **Risk**: without an explicit stop rule, optional work could displace mandatory validation — this task exists specifically to prevent that
  **Done**: list exists, referenced by later phase checkpoints **Human**: no

**Stop conditions**: if orchestration state-transition tests (Group 34) are
not passing by end of Day 2, halt new scope and stabilize the engine before
touching scenario scripts (a broken orchestration core invalidates the whole
demonstration; a narrower scenario is a disclosed, bounded gap).
**Checkpoint decisions** (require explicit human confirmation before
proceeding, not silent continuation): after Group 18 (workflow state
machine) — confirm the engine demonstrably supports parallel+sync before
building approval gates on top of it; after Group 30 (three scenarios) —
confirm minimum defensible release-readiness bar (plan.md) is realistically
reachable before continuing to exhaustive test-suite breadth.

---

## Phase 1: Group 1 — Engineering Baseline

- [x] **T004** — Scaffold package layout per ADR-0001
  **Req**: — **Scn**: — **ADR**: ADR-0001 **Path**: `src/{domain,orchestration,policy,api,persistence,observability}/__init__.py`
  **Prereq**: none **Dep**: none **P**: no
  **Artifact**: package skeleton **TDD**: n/a (structural) **Validation**: `python3 -c "import src.domain, src.orchestration, src.policy, src.api, src.persistence, src.observability"`
  **Docs**: plan.md Project Structure (already documents target — this task realizes it) **Trace**: ADR-0001
  **Risk**: package boundary drift — mitigated by no cross-package persistence imports (checked in T005)
  **Done**: all six packages importable **Human**: no

- [x] **T005** [P] — Pin dependencies per ADR-0002
  **Req**: — **Scn**: — **ADR**: ADR-0002 **Path**: `pyproject.toml`, lockfile
  **Prereq**: T004 **Dep**: T004 **P**: yes (independent of T006)
  **Artifact**: `pyproject.toml` + lock **TDD**: n/a **Validation**: `uv sync && uv run python3 --version` (expect 3.12.x)
  **Docs**: ADR-0002 (already records the decision) **Trace**: ADR-0002
  **Risk**: version drift from ADR-0002's pinned choice **Done**: `uv sync` succeeds, exit 0 **Human**: no

- [x] **T006** [P] — Configure lint/type-check tooling
  **Req**: — **Scn**: — **ADR**: ADR-0002 **Path**: `pyproject.toml` (`[tool.mypy]`, `[tool.ruff]` or equivalent)
  **Prereq**: T004 **Dep**: T004 **P**: yes (independent of T005)
  **Artifact**: lint/type config **TDD**: n/a **Validation**: `uv run mypy src/ ; uv run ruff check src/` (or chosen linter) — exit code retained regardless of pass/fail
  **Docs**: none beyond config itself **Trace**: ADR-0002
  **Risk**: none material **Done**: tooling runs (even if findings exist) **Human**: no

**Checkpoint**: baseline importable, dependencies pinned, tooling runs — Group 2 may begin.

---

## Phase 2: Group 2 — Walking Skeleton

- [x] **T007** — Minimal FastAPI app + `/health` stub
  **Req**: FR-111 **Scn**: — **ADR**: ADR-0002 **Path**: `src/api/main.py`
  **Prereq**: T004–T006 **Dep**: T004 **P**: no
  **Artifact**: running app **TDD**: test-first (T008 before this) **Validation**: `uv run uvicorn src.api.main:app --port 8000 &`; `curl -sf http://localhost:8000/health`
  **Docs**: quickstart.md (already describes target command) **Trace**: FR-111
  **Risk**: none material **Done**: `/health` returns 200 **Human**: no

- [x] **T008** — Failing contract test for `/health`
  **Req**: FR-111 **Scn**: — **ADR**: — **Path**: `tests/contract/test_health.py`
  **Prereq**: T004 **Dep**: none (written before T007's implementation) **P**: no
  **Artifact**: failing test **TDD**: this IS the "write failing test" TDD step for T007
  **Validation**: `uv run pytest tests/contract/test_health.py` — MUST fail before T007, MUST pass after
  **Docs**: none **Trace**: FR-111
  **Risk**: none **Done**: fails for the expected reason (no app yet), then passes after T007 **Human**: no

- [x] **T009** [P] — End-to-end quickstart smoke script
  **Req**: — **Scn**: — **ADR**: ADR-0010 **Path**: `scripts/smoke.sh`
  **Prereq**: T007 **Dep**: T007 **P**: yes (independent of T010)
  **Artifact**: smoke script **TDD**: n/a **Validation**: `bash scripts/smoke.sh` — exit 0
  **Docs**: quickstart.md **Trace**: ADR-0010
  **Risk**: none **Done**: script runs clean from a fresh clone **Human**: no

- [x] **T010** [P] — First coherent commit checkpoint
  **Req**: — **Scn**: — **ADR**: — **Path**: n/a (git)
  **Prereq**: T007–T009 **Dep**: T007 **P**: yes
  **Artifact**: git commit **TDD**: n/a **Validation**: `git log -1 --stat`
  **Docs**: n/a **Trace**: Constitution Principle X (small, coherent commits)
  **Risk**: bundling unrelated changes — guarded by reviewing `git status` before commit
  **Done**: committed, working tree clean **Human**: no

**Checkpoint**: app runs, one real test passes, one real commit exists — Groups 3–5 may begin, in parallel with each other where noted.

---

## Phase 3: Group 3 — Domain Model

- [x] **T011** [P] — `domain_short_link` table + model
  **Req**: FR-101–FR-104, FR-114 **Scn**: US1 **ADR**: ADR-0003 **Path**: `src/persistence/schema.py`, `src/domain/short_link.py`
  **Prereq**: T004 **Dep**: T004 **P**: yes (independent file from T012–T014)
  **Artifact**: table + model **TDD**: test-first **Validation**: `uv run pytest tests/unit/test_short_link_model.py`
  **Docs**: data-model.md (already specifies this table) **Trace**: FR-101–FR-104
  **Risk**: schema drift from data-model.md — mitigated by this task's own Done
  criterion (field-for-field match) and spot-checked again by T098's
  traceability-matrix pass; **corrected during `/speckit-analyze` remediation
  (2026-09-10)** — the prior text cited a task "T124" that does not exist in
  this 99-task plan (a stray reference caught by the analyze rerun)
  **Done**: model matches data-model.md field-for-field **Human**: no

- [x] **T012** [P] — `domain_idempotency_record` table + model
  **Req**: FR-112, FR-113, FR-116 **Scn**: US1 **ADR**: ADR-0003 **Path**: `src/persistence/schema.py`, `src/domain/idempotency.py`
  **Prereq**: T004 **Dep**: T004 **P**: yes
  **Artifact**: table + model **TDD**: test-first **Validation**: `uv run pytest tests/unit/test_idempotency_model.py`
  **Docs**: data-model.md **Trace**: FR-112, FR-113, FR-116
  **Risk**: none beyond T011's **Done**: matches data-model.md **Human**: no

- [x] **T013** [P] — Analytics tables (`domain_analytics_outbox`, `applied_events`, `analytics_system_status`, `domain_short_link_analytics_summary`)
  **Req**: FR-105–FR-107, FR-115, FR-117 **Scn**: US1 **ADR**: ADR-0009 **Path**: `src/persistence/schema.py`, `src/domain/analytics.py`
  **Prereq**: T011 **Dep**: T011 (FK to short_link) **P**: no (shares `schema.py` with T011/T012 — sequential, not parallel, per the "don't parallelize same-file edits" rule)
  **Artifact**: 4 tables + model **TDD**: test-first **Validation**: `uv run pytest tests/unit/test_analytics_model.py`
  **Docs**: data-model.md, spec.md FR-117 **Trace**: FR-117 (Human Gate 4 amendment)
  **Risk**: this is the ADR-0009 Accepted design's core schema — a schema bug here undermines every analytics guarantee **Done**: matches data-model.md **Human**: no

- [x] **T014** — Domain validation rules (destination URL scheme allow-list, expiry validation)
  **Req**: FR-101, FR-114 **Scn**: US1 **ADR**: — **Path**: `src/domain/validation.py`
  **Prereq**: T011 **Dep**: T011 **P**: no
  **Artifact**: validator module **TDD**: test-first **Validation**: `uv run pytest tests/unit/test_domain_validation.py`
  **Docs**: plan.md §8 (scheme allow-list still needs your final-list confirmation — flagged, not silently assumed) **Trace**: FR-101, FR-114
  **Risk**: **BLOCKED pending your confirmation of the final allowed-scheme list** (plan.md §8) — implement against the proposed `https`/`http` list, but do not treat it as final
  **Done**: rejects disallowed schemes, accepts allowed ones, per FR-101 negative/positive paths **Human**: yes — final scheme list confirmation, not yet given

**Checkpoint**: domain schema complete and test-covered — Groups 4–5 may proceed.

---

## Phase 4: Group 4 — API Contracts

- [x] **T015** — Generate Pydantic models from `contracts/openapi.yaml`
  **Req**: — **Scn**: — **ADR**: ADR-0002 **Path**: `src/api/schemas.py`
  **Prereq**: T011–T013 **Dep**: T011 **P**: no
  **Artifact**: schema module **TDD**: n/a (derived from already-validated contract) **Validation**: `uv run python3 -c "from src.api.schemas import ShortLinkCreateRequest"`
  **Docs**: contracts/openapi.yaml (source of truth) **Trace**: contracts/openapi.yaml
  **Risk**: contract drift if hand-edited out of sync with `openapi.yaml` **Done**: schema fields match contract 1:1 **Human**: no

- [x] **T016** [P] — Contract-version and compatibility-review note
  **Req**: FR-306 **Scn**: — **ADR**: — **Path**: `contracts/openapi.yaml` (versioning section, already present)
  **Prereq**: T015 **Dep**: T015 **P**: yes
  **Artifact**: no change needed yet (v0.1.0-proposed stands until first breaking need) **TDD**: n/a
  **Validation**: `uv run openapi-spec-validator contracts/openapi.yaml` (already run this session — re-run here as the implementation-time check)
  **Docs**: contracts/openapi.yaml **Trace**: FR-306
  **Risk**: none yet — no change has occurred **Done**: validator exits 0 **Human**: no (no change yet to approve)

- [x] **T017** [P] — Representative request/response examples
  **Req**: — **Scn**: — **ADR**: — **Path**: `contracts/examples/`
  **Prereq**: T015 **Dep**: T015 **P**: yes
  **Artifact**: example JSON files per endpoint **TDD**: n/a **Validation**: examples validate against their schema (`uv run python3 scripts/validate_examples.py`, to be written)
  **Docs**: contracts/ **Trace**: guide §9.2 "representative examples"
  **Risk**: none **Done**: one example per endpoint, schema-valid **Human**: no

- [x] **T018** — Contract tests (endpoint-schema conformance)
  **Req**: — **Scn**: — **ADR**: — **Path**: `tests/contract/`
  **Prereq**: T015, T017 **Dep**: T015 **P**: no
  **Artifact**: contract test suite **TDD**: test-first relative to each endpoint's implementation (Groups 6–9)
  **Validation**: `uv run pytest tests/contract/`
  **Docs**: none beyond the tests themselves **Trace**: contracts/openapi.yaml
  **Risk**: contract tests written before endpoints exist will fail until Groups 6–9 land — expected, tracked
  **Done**: one contract test per endpoint **Human**: no

**Checkpoint**: API surface locked to the validated contract — domain-behavior implementation (Groups 6–9) may begin.

---

## Phase 5: Group 5 — Persistence Abstraction

- [x] **T019** — SQLite connection/transaction helper, WAL mode, `busy_timeout`
  **Req**: FR-109, FR-110 **Scn**: — **ADR**: ADR-0003, ADR-0007 **Path**: `src/persistence/db.py`
  **Prereq**: T004 **Dep**: T004 **P**: no
  **Artifact**: connection helper **TDD**: test-first **Validation**: `uv run pytest tests/persistence/test_db.py`
  **Docs**: ADR-0003 (already documents the design) **Trace**: ADR-0003, ADR-0007's contention policy
  **Risk**: incorrect transaction scoping could reintroduce the contention issues ADR-0007 exists to prevent **Done**: WAL mode confirmed active (`PRAGMA journal_mode`), `busy_timeout=2000` confirmed set **Human**: no

- [x] **T020** [P] — Bounded-retry wrapper for `SQLITE_BUSY`/`SQLITE_LOCKED`
  **Req**: FR-402 (narrowed from a broad FR-401–FR-406 citation during
  `/speckit-analyze` remediation, 2026-09-10, finding E1 — this task's bounded
  attempt count and backoff is FR-402's specific subject; it does not itself
  perform transient/permanent classification (FR-401), fallback (FR-403),
  rollback/compensation (FR-404), or safe-stop (FR-405))
  **Scn**: — **ADR**: ADR-0007 **Path**: `src/persistence/retry.py`
  **Prereq**: T019 **Dep**: T019 **P**: yes (independent of T021)
  **Artifact**: retry decorator/helper **TDD**: test-first — force contention, assert bounded retry then observable failure
  **Validation**: `uv run pytest tests/persistence/test_retry.py`
  **Docs**: ADR-0007 **Trace**: `PVT-002` (3 attempts, 1s+2s waits — provisionally approved, unverified)
  **Risk**: this is the mechanism the whole "no hang, ever" guarantee rests on — under-test here is high-impact
  **Done**: forced contention produces exactly 3 attempts then a clean failure, never a hang **Human**: no

- [x] **T021** [P] — Restart-recovery integration test (kill mid-workflow, confirm state intact)
  **Req**: FR-204, FR-205 **Scn**: — **ADR**: ADR-0003 **Path**: `tests/persistence/test_restart_recovery.py`
  **Prereq**: T019 **Dep**: T019 **P**: yes
  **Artifact**: test **TDD**: test-first (written before any orchestration state exists to test against — will initially skip/xfail until Group 17 lands)
  **Validation**: `uv run pytest tests/persistence/test_restart_recovery.py`
  **Docs**: none **Trace**: FR-204/205
  **Risk**: depends on Group 17 existing — tracked as a cross-group dependency, not silently ignored
  **Done**: passes once Group 17 lands **Human**: no

**Checkpoint**: persistence layer real and contention-tested — Groups 6–9 (domain endpoints) may proceed in parallel with Group 11 onward (orchestration engine), since they touch disjoint packages.

---

## Phase 6: Group 6 — URL Shortening

- [x] **T022** — Failing test: create short link (valid URL) → 201
  **Req**: FR-101, FR-102 **Scn**: US1 AS1 **ADR**: — **Path**: `tests/contract/test_create_short_link.py`
  **Prereq**: T018 **Dep**: T018 **P**: no
  **Artifact**: failing test **TDD**: step 1–3 of TDD sequence **Validation**: `uv run pytest tests/contract/test_create_short_link.py::test_valid_url -x`
  **Docs**: none **Trace**: FR-101, FR-102 **Risk**: none **Done**: fails for "no endpoint" reason **Human**: no

- [x] **T023** — Implement `POST /short-links` (happy path)
  **Req**: FR-101, FR-102 **Scn**: US1 AS1 **SC**: SC-001 **ADR**: ADR-0004 **Path**: `src/api/routers/short_links.py`, `src/domain/short_link.py`
  **Prereq**: T022 **Dep**: T022, T014 **P**: no
  **Artifact**: working endpoint **TDD**: step 4–7 **Validation**: `uv run pytest tests/contract/test_create_short_link.py::test_valid_url`
  **Docs**: quickstart.md (golden-path command already documented) **Trace**: FR-101, FR-102
  **Risk**: short-code generation collision handling (ADR-0004) must be exercised, not just the happy path — covered by T024
  **Done**: T022's test passes **Human**: no

- [x] **T024** [P] — Short-code collision + bounded-retry test
  **Req**: FR-102 **Scn**: — **ADR**: ADR-0004 **Path**: `tests/unit/test_short_code_collision.py`
  **Prereq**: T023 **Dep**: T023 **P**: yes (independent of T025)
  **Artifact**: test forcing a collision (shrunk alphabet in test config) **TDD**: test-first for this specific behavior
  **Validation**: `uv run pytest tests/unit/test_short_code_collision.py`
  **Docs**: ADR-0004 **Trace**: ADR-0004's bounded-retry design
  **Risk**: none beyond what ADR-0004 already discloses **Done**: retry bounded, deterministic failure on exhaustion **Human**: no

- [x] **T025** — Failing test: invalid scheme → 400, no link created
  **Req**: FR-101 **Scn**: US1 AS3 **ADR**: — **Path**: `tests/contract/test_create_short_link.py`
  **Prereq**: T023 **Dep**: T023 **P**: no
  **Artifact**: failing test **TDD**: step 1–3 **Validation**: `uv run pytest tests/contract/test_create_short_link.py::test_invalid_scheme -x`
  **Docs**: none **Trace**: FR-101 negative path **Risk**: none **Done**: fails for expected reason **Human**: no

- [x] **T026** — Implement scheme validation rejection path
  **Req**: FR-101 **Scn**: US1 AS3 **ADR**: — **Path**: `src/api/routers/short_links.py`
  **Prereq**: T025, T014 **Dep**: T025, T014 **P**: no
  **Artifact**: rejection path **TDD**: step 4–7 **Validation**: `uv run pytest tests/contract/test_create_short_link.py::test_invalid_scheme`
  **Docs**: none **Trace**: FR-101
  **Risk**: **carries T014's open item** — final allowed-scheme list still needs your confirmation
  **Done**: T025's test passes **Human**: yes (inherits T014's open scheme-list confirmation)

- [x] **T027** [P] — Idempotency-Key request-level idempotency (FR-108, FR-112, FR-113)
  **Req**: FR-108, FR-112, FR-113 **Scn**: US1 AS5–7 **ADR**: ADR-0003 **Path**: `src/api/routers/short_links.py`, `src/domain/idempotency.py`
  **Prereq**: T012, T023 **Dep**: T012, T023 **P**: yes (independent file focus from T028)
  **Artifact**: idempotency logic **TDD**: test-first, 3 cases (no key/new code, same key+payload/return original, same key+different payload/409)
  **Validation**: `uv run pytest tests/contract/test_idempotency.py`
  **Docs**: none **Trace**: AMB-001 resolution (spec.md Clarifications)
  **Risk**: this is the most subtle domain logic in the project (AMB-001's full resolution) — under-testing here directly risks a spec violation
  **Done**: all 3 cases pass, matching spec.md exactly **Human**: no

**Checkpoint**: domain creation path complete, idempotency correct — Group 7 may proceed.

---

## Phase 7: Group 7 — Redirect Resolution

- [x] **T028** — Failing test: resolve valid code → 302 + destination
  **Req**: FR-103 **Scn**: US1 AS2 **ADR**: — **Path**: `tests/contract/test_resolve.py`
  **Prereq**: T023 **Dep**: T023 **P**: no
  **Artifact**: failing test **TDD**: step 1–3 **Validation**: `uv run pytest tests/contract/test_resolve.py::test_valid -x`
  **Docs**: none **Trace**: FR-103 **Risk**: none **Done**: fails for expected reason **Human**: no

- [x] **T029** — Implement `GET /{shortCode}` resolution
  **Req**: FR-103 **Scn**: US1 AS2 **SC**: SC-001 **ADR**: — **Path**: `src/api/routers/redirect.py`
  **Prereq**: T028 **Dep**: T028 **P**: no
  **Artifact**: working redirect **TDD**: step 4–7 **Validation**: `uv run pytest tests/contract/test_resolve.py::test_valid`
  **Docs**: quickstart.md **Trace**: FR-103 **Risk**: none **Done**: T028's test passes **Human**: no

- [x] **T030** [P] — Unknown vs. expired distinction (404 vs. 410)
  **Req**: FR-103 **Scn**: US1 AS4 **ADR**: — **Path**: `src/api/routers/redirect.py`
  **Prereq**: T029 **Dep**: T029 **P**: yes (depends on Group 8 for expiry, tracked as cross-group)
  **Artifact**: distinguished error paths **TDD**: test-first, both negative cases
  **Validation**: `uv run pytest tests/contract/test_resolve.py::test_unknown tests/contract/test_resolve.py::test_expired`
  **Docs**: none **Trace**: FR-103, FR-104
  **Risk**: conflating "unknown" and "expired" would violate FR-103's explicit distinction requirement
  **Done**: both negative tests pass, distinctly **Human**: no

**Checkpoint**: redirect resolution complete — Group 8 (expiration) can complete T030's dependency.

---

## Phase 8: Group 8 — Expiration

- [x] **T031** — Failing test: `expiresAt` future-validation at creation
  **Req**: FR-114 **Scn**: US1 AS4b **ADR**: — **Path**: `tests/contract/test_expiration.py`
  **Prereq**: T023 **Dep**: T023 **P**: no
  **Artifact**: failing test **TDD**: step 1–3 **Validation**: `uv run pytest tests/contract/test_expiration.py::test_future_validation -x`
  **Docs**: none **Trace**: FR-114 **Risk**: none **Done**: fails for expected reason **Human**: no

- [x] **T032** — Implement `expiresAt` validation + no-default-expiration behavior
  **Req**: FR-104, FR-114 **Scn**: US1 AS4/4a/4b **ADR**: — **Path**: `src/domain/validation.py`, `src/api/routers/short_links.py`
  **Prereq**: T031 **Dep**: T031 **P**: no
  **Artifact**: expiry logic **TDD**: step 4–7 **Validation**: `uv run pytest tests/contract/test_expiration.py`
  **Docs**: none **Trace**: AMB-006 resolution
  **Risk**: FR-112's "no re-run of the time-dependent future-check on idempotent replay" rule (Human Gate 3 correction) — must not regress here; covered by T033
  **Done**: no-expiration-by-default, future-only validation, both pass **Human**: no

- [x] **T033** [P] — Idempotent-replay-does-not-re-validate-expiresAt regression test
  **Req**: FR-112, FR-114 **Scn**: US1 AS11 **ADR**: — **Path**: `tests/contract/test_idempotency.py`
  **Prereq**: T027, T032 **Dep**: T027, T032 **P**: yes
  **Artifact**: regression test **TDD**: test-first for this exact corrected rule
  **Validation**: `uv run pytest tests/contract/test_idempotency.py::test_replay_after_expiry`
  **Docs**: none **Trace**: Human Gate 3 review correction (spec.md Clarifications)
  **Risk**: this is exactly the contradiction the Human Gate 3 review caught and fixed at the design level — this test is what proves the fix holds in real code
  **Done**: replay after expiry returns the original result, doesn't re-validate, doesn't reactivate **Human**: no

**Checkpoint**: full URL-shortener domain behavior (Groups 6–8) complete — Group 9 (analytics) may proceed, depending on T013.

---

## Phase 9: Group 9 — Analytics

- [x] **T034** — Post-response outbox write (ADR-0009's corrected ordering)
  **Req**: FR-105, FR-106 **Scn**: US1 AS10 **ADR**: ADR-0009 **Path**: `src/domain/analytics.py`, `src/api/routers/redirect.py`
  **Prereq**: T013, T029 **Dep**: T013, T029 **P**: no
  **Artifact**: post-send write, `BackgroundTasks`-based **TDD**: test-first — assert no count for an unsent response (the specific overcount defect this design exists to prevent)
  **Validation**: `uv run pytest tests/analytics/test_ordering.py`
  **Docs**: ADR-0009 (already documents the corrected design) **Trace**: ADR-0009 Rev. 3, Human Gate 4 spike finding #21
  **Risk**: **highest-risk task in this group** — a regression here reintroduces the exact overcount bug Human Gate 4 caught; the ordering (write strictly after send) must never be "optimized" back to before-send
  **Done**: overcount test passes, `PVT-001` budget measured **Human**: no

- [x] **T035** — Drain worker (outbox → summary, idempotent by `event_id`)
  **Req**: FR-107 **Scn**: — **ADR**: ADR-0009 **Path**: `src/domain/analytics.py`
  **Prereq**: T034 **Dep**: T034 **P**: no
  **Artifact**: background drain task **TDD**: test-first — kill mid-batch, assert no double-count
  **Validation**: `uv run pytest tests/analytics/test_drain_dedup.py`
  **Docs**: none **Trace**: ADR-0009's `applied_events` uniqueness design
  **Risk**: none beyond what's already disclosed **Done**: dedup test passes **Human**: no

- [x] **T036** [P] — Three-state `completeness_status` (`complete`/`degraded`/`incomplete`)
  **Req**: FR-107 **Scn**: — **SC**: SC-001 **ADR**: ADR-0009 **Path**: `src/domain/analytics.py`
  **Prereq**: T035 **Dep**: T035 **P**: yes (independent of T037)
  **Artifact**: status transitions **TDD**: test-first, all 3 states + the one-way `incomplete` transition
  **Validation**: `uv run pytest tests/analytics/test_completeness_status.py`
  **Docs**: none **Trace**: ADR-0009
  **Risk**: `incomplete` must never auto-revert — guarded explicitly in the test **Done**: all transitions match ADR-0009 **Human**: no

- [x] **T037** [P] — `analytics_system_status`: unclean-shutdown detection, sticky flag, operator acknowledgment
  **Req**: FR-117 **Scn**: — **ADR**: ADR-0009 **Path**: `src/observability/system_status.py`
  **Prereq**: T013 **Dep**: T013 **P**: yes (independent of T036)
  **Artifact**: startup/shutdown lifecycle hooks **TDD**: test-first — the exact spike-verified scenarios (crash-window, double-failure, ack-doesn't-restore)
  **Validation**: `uv run pytest tests/analytics/test_unclean_shutdown.py`
  **Docs**: spec.md FR-117 (already documents the exact semantics) **Trace**: FR-117, Human Gate 4 spike results (docs/governance/gate-4-spike-results-2026-09-10.md)
  **Risk**: **the single most spec-scrutinized behavior in this project** — acknowledgment MUST NOT restore historical completeness; this exact property was the spike's headline finding and must not regress
  **Done**: all spike scenarios reproduce as real, passing tests **Human**: no

- [x] **T038** — Durable running-marker gate on request-serving
  **Req**: FR-117 **Scn**: — **ADR**: ADR-0009 **Path**: `src/api/main.py`, `src/observability/system_status.py`
  **Prereq**: T037 **Dep**: T037 **P**: no
  **Artifact**: startup gate **TDD**: test-first — marker-write failure must prevent request-serving, not just log a warning
  **Validation**: `uv run pytest tests/analytics/test_running_marker.py`
  **Docs**: none **Trace**: Human Gate 4 spike Scenario 4
  **Risk**: none beyond what's already disclosed **Done**: test passes **Human**: no

- [x] **T039** [P] — `PVT-001` bounded-overhead measurement (background task, not response-blocking)
  **Req**: FR-106 **Scn**: — **ADR**: ADR-0009 **Path**: `tests/analytics/test_budget.py`
  **Prereq**: T034 **Dep**: T034 **P**: yes
  **Artifact**: timing test **TDD**: n/a (measurement, not correctness) **Validation**: `uv run pytest tests/analytics/test_budget.py -v`
  **Docs**: plan.md (already notes the single-measurement caveat) **Trace**: `PVT-001`, provisionally approved, **explicitly unverified until this test exists and passes under representative load** — per the instruction that one spike sample is not a percentile
  **Risk**: do not overclaim this single test as p95 evidence — report it as one more sample, same caveat as the spike
  **Done**: measured and logged, still labeled unverified as a percentile claim **Human**: no

- [x] **T040** — MTTR instrumentation: timestamps, recovered-event population, exclusions
  **Req**: — **Scn**: — **SC**: SC-004 **ADR**: ADR-0008 **Path**: `src/observability/metrics.py`
  **Prereq**: T080 (audit_events table, Group 26) **Dep**: T080 **P**: no
  **Artifact**: MTTR calculation function **TDD**: test-first — constructed recovered-failure sequence produces exact expected MTTR; unrecovered failures excluded from the denominator, reported separately
  **Validation**: `uv run pytest tests/observability/test_mttr.py`
  **Docs**: ADR-0008 (already specifies the precise definition) **Trace**: ADR-0008, guide's explicit MTTR rule
  **Risk**: **no numeric MTTR target exists or should be proposed until this task's tests pass** — per ADR-0008, the definitional work must precede any target.
  **Corrected during `/speckit-analyze` remediation (2026-09-10)**: this task's
  Prereq/Dep previously cited a nonexistent task ("T106"); the real
  `audit_events` table is built by T080 (Group 26). This is a genuine
  **disclosed cross-phase dependency**, matching the precedent already set by
  T021/T077: T040 is written here in Group 9 because MTTR instrumentation is
  conceptually an analytics/observability concern, but it cannot actually
  pass until T080 lands in Group 26, sixteen phases later. Phase 9's own
  checkpoint below is qualified accordingly — it does not claim T040 is fully
  closed out.
  **Done**: exact-match test passes, unrecovered count reported separately **Human**: no

**Checkpoint**: analytics durability and uncertainty-handling (T034–T039) are
real and tested here. MTTR definition (T040) is **written** here but cannot
**pass** until T080 (Group 26) lands — a disclosed cross-phase dependency,
not a silent gap (see T040's Risk field, corrected during `/speckit-analyze`
remediation, 2026-09-10). Group 10 may proceed regardless, since it does not
depend on T040.

---

## Phase 10: Group 10 — Validation and Security

- [x] **T041** — Idempotency-Key minimum-length enforcement
  **Req**: — **Scn**: — **ADR**: — **Path**: `src/domain/idempotency.py`
  **Prereq**: T027 **Dep**: T027 **P**: no
  **Artifact**: length check **TDD**: test-first **Validation**: `uv run pytest tests/unit/test_idempotency_key_length.py`
  **Docs**: plan.md §8 (approved control) **Trace**: plan.md §8, approved 2026-09-10
  **Risk**: disclosed limitation — no entropy check beyond length, caller's responsibility, stated in code comment near the check
  **Done**: rejects <16 chars **Human**: no

- [x] **T042** [P] — Private/internal-address rejection at creation time
  **Req**: — **Scn**: — **ADR**: — **Path**: `src/domain/validation.py`
  **Prereq**: T014 **Dep**: T014 **P**: yes
  **Artifact**: address-check **TDD**: test-first, including a positive test that a public address is accepted
  **Validation**: `uv run pytest tests/unit/test_private_address_rejection.py`
  **Docs**: plan.md §8 (already documents the DNS-rebinding limitation — must be repeated in code comment, not silently dropped) **Trace**: plan.md §8, approved 2026-09-10
  **Risk**: **DNS-rebinding is explicitly NOT covered by this check** — code comment must state this, not just the plan doc
  **Done**: rejects loopback/private literals; comment discloses the rebinding gap **Human**: no

- [x] **T043** [P] — Rate limiting (`PVT-007`, 60 req/min/IP)
  **Req**: — **Scn**: — **ADR**: — **Path**: `src/api/middleware/rate_limit.py`
  **Prereq**: T007 **Dep**: T007 **P**: yes
  **Artifact**: middleware **TDD**: test-first **Validation**: `uv run pytest tests/unit/test_rate_limit.py`
  **Docs**: plan.md §8 **Trace**: `PVT-007`, provisionally approved, unverified until this test passes
  **Risk**: none beyond standard rate-limiter false-positive risk at burst traffic — disclosed, not solved here
  **Done**: 61st request in a minute from one IP is rejected **Human**: no

- [x] **T044** — Dependency/secret scan (release-readiness input)
  **Req**: — **Scn**: — **ADR**: — **Path**: CI-equivalent local command, no new source file
  **Prereq**: T005 **Dep**: T005 **P**: no
  **Artifact**: scan report **TDD**: n/a **Validation**: `uv run pip-audit` (or equivalent) — exit code retained regardless of findings
  **Docs**: Group 39 (release readiness) consumes this **Trace**: Constitution Principle V, plan.md §8
  **Risk**: none **Done**: scan runs, output retained as evidence **Human**: no

**Checkpoint**: security controls real and tested — domain-side work (Groups 1–10) is now complete. Orchestration-side work (Groups 11+) was eligible to run in parallel throughout; its own checkpoint gating is tracked within Groups 11–27 below.

---

## Phase 11: Group 11 — Orchestration Domain

- [x] **T045** — `orchestration_workflow_instance`/`_stage`/`stage_dependency` schema
  **Req**: FR-201–FR-206 **Scn**: — **ADR**: ADR-0005 **Path**: `src/persistence/schema.py`, `src/orchestration/models.py`
  **Prereq**: T004 **Dep**: T004 **P**: yes (independent package from Groups 3–10)
  **Artifact**: 3 tables + models **TDD**: test-first **Validation**: `uv run pytest tests/unit/test_orchestration_models.py`
  **Docs**: data-model.md **Trace**: FR-201, ADR-0005
  **Risk**: this schema IS the "explicit dependency graph" the whole assessment measures — get it wrong and the central differentiator fails **Done**: matches data-model.md **Human**: no

- [x] **T046** — `orchestration_stage_execution` schema (durable execution identity)
  **Req**: FR-606 **Scn**: — **ADR**: ADR-0005 **Path**: `src/persistence/schema.py`, `src/orchestration/models.py`
  **Prereq**: T045 **Dep**: T045 **P**: no
  **Artifact**: execution-identity table **TDD**: test-first **Validation**: `uv run pytest tests/unit/test_stage_execution_model.py`
  **Docs**: data-model.md **Trace**: ADR-0005 Rev. 3, Human Gate 4 spike (Scenario 2, all PASS)
  **Risk**: this is the exact mechanism the real subprocess-kill spike verified in isolation — the real implementation must match that verified logic, not diverge from it **Done**: matches data-model.md and the spike's verified schema **Human**: no

- [x] **T047** [P] — Agent-adapter `Protocol` interface (`effect_class`, `execute`, `check_effect`)
  **Req**: — **Scn**: — **ADR**: ADR-0005 **Path**: `src/orchestration/adapters/base.py`
  **Prereq**: T046 **Dep**: T046 **P**: yes (independent of T048)
  **Artifact**: interface **TDD**: n/a (interface definition) **Validation**: `uv run mypy src/orchestration/adapters/base.py`
  **Docs**: ADR-0005 (already specifies this exact interface) **Trace**: ADR-0005 §Decision — Agent Adapters
  **Risk**: none **Done**: interface matches ADR-0005 verbatim **Human**: no

- [x] **T048** — Real `claude` CLI invocation wrapper (corrected mechanism)
  **Req**: — **Scn**: — **ADR**: ADR-0005 **Path**: `src/orchestration/adapters/claude_invoke.py`
  **Prereq**: T047 **Dep**: T047 **P**: no
  **Artifact**: subprocess wrapper **TDD**: test-first, using the **exact syntax the spike verified** (`cwd`-based, `--output-format json --permission-mode bypassPermissions`, no `--cwd` flag)
  **Validation**: `uv run pytest tests/orchestration/test_claude_invoke.py` (mocked) + one real smoke invocation, cost-bounded
  **Docs**: ADR-0005 (already corrected from the wrong illustrative syntax) **Trace**: Human Gate 4 spike 1a (PASS, real invocation, real artifact)
  **Risk**: reintroducing the wrong `--cwd`-flag syntax would be a regression
  of an already-caught, already-fixed defect. **Clarification added during
  `/speckit-analyze` remediation (2026-09-10)**: distinct from T103's
  blocked isolation launcher (Group 19) — this task invokes the `claude` CLI
  using the developer's own already-authenticated session for orchestration
  subprocess execution; it does not read or provision human-approver
  credentials (that is T101's blocked scope, ADR-0006). No ADR-0006
  replacement is required to build T048 itself.
  **Done**: real invocation succeeds, matches spike evidence **Human**: no

**Checkpoint**: orchestration schema + adapter interface real — Groups 16–18 (dependency graph, state machine, decision lineage) may proceed.

---

## Phase 12: Group 12 — Compliance Policy Model and Policy Versioning

- [x] **T049** — `config/policies.yaml` manifest + loader
  **Req**: — **Scn**: — **ADR**: — **Path**: `config/policies.yaml`, `src/policy/manifest.py`
  **Prereq**: T004 **Dep**: T004 **P**: yes (independent package)
  **Artifact**: manifest + loader **TDD**: test-first **Validation**: `uv run pytest tests/policy/test_manifest.py`
  **Docs**: research.md §8 (already specifies this design) **Trace**: Constitution Principle VI
  **Risk**: none **Done**: manifest parses, version field required **Human**: no

- [x] **T050** [P] — `policy_evaluation` schema
  **Req**: FR-303 **Scn**: — **ADR**: — **Path**: `src/persistence/schema.py`, `src/policy/models.py`
  **Prereq**: T049 **Dep**: T049 **P**: yes
  **Artifact**: table + model **TDD**: test-first **Validation**: `uv run pytest tests/policy/test_evaluation_model.py`
  **Docs**: data-model.md **Trace**: FR-303 **Risk**: none **Done**: matches data-model.md **Human**: no

**Checkpoint**: policy model real — Group 13 may proceed.

---

## Phase 13: Group 13 — Compliance Evaluation and Enforcement

- [x] **T051** — Policy-evaluation stage (produces `PASS`/`FAIL`/`EXCEPTION-REQUESTED`/`NOT-APPLICABLE`)
  **Req**: FR-303, FR-304 **Scn**: — **SC**: SC-006 **ADR**: — **Path**: `src/policy/evaluator.py`
  **Prereq**: T050 **Dep**: T050 **P**: no
  **Artifact**: evaluator **TDD**: test-first, all 4 outcomes **Validation**: `uv run pytest tests/policy/test_evaluator.py`
  **Docs**: none **Trace**: FR-303 **Risk**: none **Done**: all 4 outcomes producible **Human**: no

- [x] **T052** — `FAIL` mechanically blocks downstream progression
  **Req**: FR-304 **Scn**: — **ADR**: — **Path**: `src/orchestration/scheduler.py` (integration point)
  **Prereq**: T051, T056 (scheduler eligibility query, Group 16) **Dep**: T051, T056 **P**: no
  **Artifact**: integration **TDD**: test-first — a `FAIL` policy stage's dependents never become `ready`
  **Validation**: `uv run pytest tests/orchestration/test_policy_blocking.py`
  **Docs**: plan.md §9 (already specifies this as a structural, not separately-enforced, consequence) **Trace**: FR-304, plan.md §9
  **Risk**: if implemented as a separate enforced rule rather than a structural graph consequence, it could drift out of sync — must reuse the scheduler's own eligibility query, not a parallel check.
  **Corrected during `/speckit-analyze` remediation (2026-09-10)**: this
  task's Prereq previously cited "T054 (scheduler)" — T054 is actually the
  policy-exception-expiry test (Group 14), unrelated to the scheduler. The
  real scheduler eligibility query is T056 (Group 16). This is a genuine
  **disclosed cross-phase dependency**: T052 sits in Group 13, three phases
  before the scheduler it must integrate with is built in Group 16. The test
  can be written here, but a real pass requires T056 to exist first.
  **Done**: test passes **Human**: no

**Checkpoint**: policy evaluation (T051) is real and tested here. T052's
blocking test is written here but — per its corrected Risk field
(`/speckit-analyze` remediation, 2026-09-10) — cannot fully pass until T056
(Group 16) lands; a disclosed cross-phase dependency, not a silent gap.
Group 14 may proceed regardless, since it does not depend on T052 passing.

---

## Phase 14: Group 14 — Policy Exception and Compensating-Control Workflow

- [x] **T053** — `policy_exception` schema + approval-gated creation
  **Req**: FR-305 **Scn**: — **ADR**: ADR-0006 **Path**: `src/persistence/schema.py`, `src/policy/exception.py`
  **Prereq**: T050, T065 (approval mechanism, Group 19) **Dep**: T050 **P**: no
  **Artifact**: table + workflow **TDD**: test-first, all required fields (policy, reason, scope, authority, compensating control, timestamp, expiry)
  **Validation**: `uv run pytest tests/policy/test_exception.py`
  **Docs**: data-model.md **Trace**: FR-305
  **Risk**: depends on Group 19's approval mechanism, which carries ADR-0006's
  unresolved isolation — an accepted, disclosed limitation, not silently
  ignored. **Corrected during `/speckit-analyze` remediation (2026-09-10)**:
  this task's Prereq previously cited "T086", which is actually the
  Ambiguous-Scenario demo script (Group 30), not the approval mechanism. The
  real approval-mechanism task is T065 (Group 19). This is a genuine
  **disclosed cross-phase dependency**: T053 sits in Group 14, five phases
  before Group 19 builds the approval endpoints its "approval-gated" schema
  needs. The schema itself (fields, constraints) can be built and tested
  here; the gating behavior cannot be exercised end-to-end until T065 lands.
  **Done**: all fields required, expiry enforced **Human**: yes — exception creation requires the approval mechanism from Group 19

- [x] **T054** [P] — Expired-exception-treated-as-failure test
  **Req**: FR-305 **Scn**: — **ADR**: — **Path**: `tests/policy/test_exception_expiry.py`
  **Prereq**: T053 **Dep**: T053 **P**: yes
  **Artifact**: test **TDD**: test-first **Validation**: `uv run pytest tests/policy/test_exception_expiry.py`
  **Docs**: none **Trace**: Constitution Principle VI **Risk**: none **Done**: expired exception → policy treated as FAIL again **Human**: no

**Checkpoint**: exception workflow real — Group 15 may proceed.

---

## Phase 15: Group 15 — Change-Control and Downstream Impact Analysis

- [x] **T055** — Material-change detector (requirements/architecture/schema/workflow/security/release-criteria)
  **Req**: FR-306 **Scn**: Scenario B **ADR**: — **Path**: `src/orchestration/replanning.py`
  **Prereq**: T045, T051 **Dep**: T045 **P**: no
  **Artifact**: change-classification function **TDD**: test-first, each of the 6 listed change types
  **Validation**: `uv run pytest tests/orchestration/test_change_detection.py`
  **Docs**: none **Trace**: FR-306 **Risk**: none beyond correctness **Done**: all 6 types correctly classified as material **Human**: no

**Checkpoint**: change-control detection real — Group 16 (dependency graph, already schema-complete from Group 11) proceeds to its behavioral layer.

---

## Phase 16: Group 16 — Dependency Graph

- [x] **T056** — Scheduler eligibility query (the actual "is this stage ready" logic)
  **Req**: FR-201, FR-202 **Scn**: — **ADR**: ADR-0005 **Path**: `src/orchestration/scheduler.py`
  **Prereq**: T045 **Dep**: T045 **P**: no
  **Artifact**: eligibility query **TDD**: test-first — a stage becomes `ready` only when every dependency edge resolves to `succeeded`
  **Validation**: `uv run pytest tests/orchestration/test_eligibility.py`
  **Docs**: ADR-0005 (already specifies this exact query pattern) **Trace**: ADR-0005 §Decision
  **Risk**: **this single query is what separates real orchestration from linear chaining disguised as orchestration** — the guide's explicit failure trap
  **Done**: forward-progress test passes for a known-good graph **Human**: no

- [x] **T057** [P] — Real parallel dispatch + synchronization event (the concrete DAG example)
  **Req**: FR-202 **Scn**: US2 AS3 **ADR**: ADR-0005 **Path**: `src/orchestration/scheduler.py`
  **Prereq**: T056 **Dep**: T056 **P**: yes (independent test file from T058)
  **Artifact**: `asyncio.gather`-based dispatch **TDD**: test-first — two independent stages actually run concurrently (observable via overlapping timestamps), synchronization event recorded
  **Validation**: `uv run pytest tests/orchestration/test_parallel_sync.py`
  **Docs**: ADR-0005's worked DAG example (already documents the target shape) **Trace**: ADR-0005 §Decision — concrete DAG example
  **Risk**: this is the guide's explicit "fan-out and synchronization" requirement — a sequential-only implementation would fail this test by design
  **Done**: overlap + sync event both observed in the test **Human**: no

**Checkpoint**: real non-linear execution demonstrated in code, not just design — Group 17 may proceed.

---

## Phase 17: Group 17 — Workflow State Machine

- [x] **T058** — Atomic claiming (compare-and-swap `UPDATE ... WHERE status='ready'`)
  **Req**: FR-201 **Scn**: — **ADR**: ADR-0005 **Path**: `src/orchestration/scheduler.py`
  **Prereq**: T046, T056 **Dep**: T046, T056 **P**: no
  **Artifact**: CAS claim statement **TDD**: test-first — concurrent claim attempts, exactly one wins
  **Validation**: `uv run pytest tests/orchestration/test_atomic_claim.py`
  **Docs**: ADR-0005 (exact SQL already specified) **Trace**: ADR-0005 §Decision, Human Gate 4 spike (real reconciliation logic verified)
  **Risk**: none beyond what the spike already verified in isolation — this task is "make the spike's proven logic real"
  **Done**: concurrent-claim test passes **Human**: no

- [x] **T059** — Lease + dual-trigger reaper (event-triggered AND periodic)
  **Req**: — **Scn**: — **ADR**: ADR-0005 **Path**: `src/orchestration/reaper.py`
  **Prereq**: T058 **Dep**: T058 **P**: no
  **Artifact**: reaper routine **TDD**: test-first — **specifically the "zero other transitions occurring" case Round 3 caught as missing**
  **Validation**: `uv run pytest tests/orchestration/test_reaper_periodic.py`
  **Docs**: ADR-0005 (`PVT-008`, 10s interval, provisionally approved) **Trace**: ADR-0005 Rev. 3 finding #13
  **Risk**: this is a previously-identified gap (Round 2 missed it) — the test must specifically construct the no-other-transitions scenario, not just a generic reaper test
  **Done**: periodic-only trigger test passes **Human**: no

- [x] **T060** — Effect reconciliation (`check_effect()` on exception/timeout/stale-lease)
  **Req**: FR-401 (added during `/speckit-analyze` rerun, 2026-09-10 —
  narrowing T070/T020 away from a broad FR-401–406 citation left FR-401
  itself uncited by any task, a gap the rerun caught. This reconciliation
  dispatch is FR-401's actual real owner: its `not_completed` vs.
  otherwise result *is* the transient-vs-permanent classification decision
  for an `externally_observable_uncertain` stage — the output this task
  produces is what T070 then reads to decide retry eligibility)
  **Scn**: — **ADR**: ADR-0005, ADR-0007 **Path**: `src/orchestration/reaper.py`
  **Prereq**: T047, T059 **Dep**: T047, T059 **P**: no
  **Artifact**: reconciliation dispatch **TDD**: test-first — **the exact three real spike scenarios**: exception-after-effect, killed-worker, git-succeeds-DB-doesn't
  **Validation**: `uv run pytest tests/orchestration/test_reconciliation.py`
  **Docs**: Human Gate 4 spike results (already retains the real command/exit-code evidence for the isolated logic) **Trace**: ADR-0005 Rev. 3, Human Gate 4 spike (Scenarios A/B/C, all real PASS), FR-401
  **Risk**: **this is the corrected core of the whole recovery model** — the Round 2→3 finding that an in-band exception was wrongly assumed safe must not silently regress back into the codebase
  **Done**: all 3 spike-equivalent scenarios pass as real integration tests against real code, not the isolated simulation **Human**: no

- [x] **T061** [P] — Isolated `git worktree` per execution + controller-only promotion
  **Req**: — **Scn**: — **ADR**: ADR-0005 **Path**: `src/orchestration/workspace.py`
  **Prereq**: T060 **Dep**: T060 **P**: yes (independent of T062)
  **Artifact**: worktree lifecycle + promotion gate **TDD**: test-first — a stale execution's output is never promoted (fencing + validator + revision match all required)
  **Validation**: `uv run pytest tests/orchestration/test_worktree_promotion.py`
  **Docs**: ADR-0005 (mechanism shared with ADR-0006's isolation design) **Trace**: ADR-0005 §Decision — Isolated Execution Workspaces
  **Risk**: this is the actual fix for "fencing a DB row doesn't stop a zombie's real file effects" — the promotion gate is the load-bearing control here, not the DB fence alone
  **Done**: stale-execution non-promotion test passes **Human**: no

- [x] **T062** [P] — Executable postcondition validators + retained artifact-hash evidence
  **Req**: FR-606 **Scn**: — **ADR**: ADR-0005 **Path**: `src/orchestration/validators.py`
  **Prereq**: T046 **Dep**: T046 **P**: yes
  **Artifact**: validator-run + evidence-recording logic **TDD**: test-first — `succeeded` unreachable without an actually-run, actually-passing validator
  **Validation**: `uv run pytest tests/orchestration/test_postcondition_validators.py`
  **Docs**: data-model.md (`outcome_detail` schema already specified) **Trace**: ADR-0005 §Decision — Executable Postconditions, FR-606
  **Risk**: a clean `git status` or checked box must NOT be accepted as evidence on its own — the test must specifically assert this
  **Done**: no path to `succeeded` bypasses the validator **Human**: no

**Checkpoint**: the corrected, spike-verified recovery/reconciliation model is now real code, not an isolated simulation — Group 18 may proceed.

---

## Phase 18: Group 18 — Context and Decision Lineage

- [x] **T063** — Append-only `orchestration_decision_lineage` writer
  **Req**: FR-503 **Scn**: — **ADR**: — **Path**: `src/orchestration/lineage.py`
  **Prereq**: T045 **Dep**: T045 **P**: no
  **Artifact**: append-only writer (no UPDATE/DELETE code path) **TDD**: test-first **Validation**: `uv run pytest tests/orchestration/test_lineage.py`
  **Docs**: none **Trace**: FR-503
  **Risk**: enforcement is currently code-review convention, not a DB
  constraint — disclosed, not solved here. **Corrected during
  `/speckit-analyze` remediation (2026-09-10, finding F1)**: this task
  previously used the short name `decision_lineage`; the authoritative table
  name in data-model.md is `orchestration_decision_lineage` — the same drift
  existed in plan.md §4 and has been corrected there too.
  **Done**: append works, no update/delete function exists **Human**: no

- [x] **T064** [P] — Artifact-revision tracking on every stage/approval
  **Req**: FR-311, FR-501 **Scn**: — **ADR**: — **Path**: `src/orchestration/models.py`
  **Prereq**: T063 **Dep**: T063 **P**: yes
  **Artifact**: revision field wiring **TDD**: test-first **Validation**: `uv run pytest tests/orchestration/test_revision_tracking.py`
  **Docs**: none **Trace**: FR-311, FR-501 **Risk**: none **Done**: every stage/approval carries its governing revision **Human**: no

**Checkpoint**: decision lineage real — Group 19 (approval gates) may proceed.

---

## Phase 19: Group 19 — Approval Gates

- [x] **T065** — Role-checked approval endpoints (`reviewer_approver`/`release_owner`)
  **Req**: FR-307, FR-310, FR-312, FR-313 **Scn**: US3, US4 **SC**: SC-005 **ADR**: ADR-0006 **Path**: `src/api/routers/approvals.py`
  **Prereq**: T064 **Dep**: T064 **P**: no
  **Artifact**: approval endpoints **TDD**: test-first — both roles, both gate
  types, **plus a dedicated FR-313 case** (a `reviewer_approver` identity
  attempting a `release_readiness`/`final_submission` gate; a `release_owner`
  identity attempting a `requirements_approval`/`architecture_approval` gate
  — each rejected specifically *because* the role doesn't match that gate,
  distinct from having no valid role at all)
  **Validation**: `uv run pytest tests/contract/test_approvals.py`
  **Docs**: contracts/openapi.yaml (already specifies these endpoints) **Trace**: FR-307, FR-310, FR-312, FR-313
  **Risk**: **the credential-isolation mechanism underneath this endpoint is ADR-0006 Rejected, not Accepted** — this task implements the role/revision-binding logic, which IS Accepted, separately from the still-unresolved credential-storage isolation.
  **Expanded during `/speckit-analyze` remediation (2026-09-10, finding E2)**:
  FR-310 and FR-313 are now explicitly cited and tested here rather than only
  implicitly covered.
  **Done**: (1) unauthenticated and no-valid-role cases rejected; (2) the
  **FR-313 wrong-gate-for-role case** rejected as its own distinct assertion
  (not merely folded into "role-mismatch"); (3) revision-mismatch rejected;
  (4) every recorded `orchestration_approval_decision` row — verified by a
  direct DB read, not just the HTTP response — carries all **FR-310**
  mandatory fields: `identity`, `role`, `decision`, `rationale` (nullable but
  present as a column), `created_at` (timestamp), `gate_id`, and
  `artifact_revision`.
  **Human**: no (the endpoint itself doesn't need a human gate to *build*)

- [x] **T066** — Verified-credential identity derivation (not caller-supplied name)
  **Req**: FR-308 **Scn**: — **ADR**: ADR-0006 **Path**: `src/api/auth.py`
  **Prereq**: T065 **Dep**: T065 **P**: no
  **Artifact**: auth dependency **TDD**: test-first **Validation**: `uv run pytest tests/contract/test_auth.py`
  **Docs**: ADR-0006 **Trace**: FR-308
  **Risk**: **BLOCKED-adjacent**: the specific credential-*storage* isolation mechanism (separate OS user, sandbox, etc.) is unresolved (ADR-0006 Rejected). This task implements verified-credential-derivation using whatever mechanism is available now (e.g., static hashed tokens per ADR-0006 Revision 3's baseline layer), explicitly **not** claiming the rejected OS-isolation guarantee. Documented as an accepted limitation, not silently upgraded.
  **Done**: derives identity from a verified token, never a request field named "name" **Human**: yes — accepting this interim posture (token-based, without OS-level agent isolation) as the demonstrable mechanism for now is itself worth your explicit sign-off before Group 19 is considered "done enough" for a scenario demo

- [x] **T067** [P] — Agent-originated approval unconditional rejection
  **Req**: FR-309 **Scn**: US3 AS7 **ADR**: ADR-0006 **Path**: `src/api/auth.py`
  **Prereq**: T066 **Dep**: T066 **P**: yes (independent of T068)
  **Artifact**: agent-identity block **TDD**: test-first **Validation**: `uv run pytest tests/contract/test_approvals.py::test_agent_rejected`
  **Docs**: none **Trace**: FR-309 **Risk**: none beyond T066's disclosed limitation **Done**: any agent-flagged identity rejected at any gate **Human**: no

- [x] **T068** [P] — Revision-binding + invalidation on replan
  **Req**: FR-311, FR-501 **Scn**: US4 **ADR**: — **Path**: `src/api/routers/approvals.py`
  **Prereq**: T064, T055 **Dep**: T064 **P**: yes
  **Artifact**: binding + invalidation logic **TDD**: test-first — replanning invalidates exactly the affected approvals **Validation**: `uv run pytest tests/orchestration/test_approval_invalidation.py`
  **Docs**: none **Trace**: FR-311, FR-501 **Risk**: none **Done**: test passes **Human**: no

- [x] **T069** — Approval-timeout/escalation (`PVT-006`: 24h gate / 60s demo)
  **Req**: FR-302 **Scn**: — **ADR**: — **Path**: `src/orchestration/scheduler.py`
  **Prereq**: T065 **Dep**: T065 **P**: no
  **Artifact**: timeout handling **TDD**: test-first — timeout never treated as approval **Validation**: `uv run pytest tests/orchestration/test_approval_timeout.py`
  **Docs**: plan.md §5 **Trace**: `PVT-006`, provisionally approved, unverified until this test passes **Risk**: none beyond the provisional-number caveat **Done**: escalation state distinct from approved/rejected **Human**: no

### Blocked — pending an accepted replacement for ADR-0006

**Added during `/speckit-analyze` remediation (2026-09-10, finding F2)**: the
four tasks below are the concrete implementation of ADR-0006's still-Rejected
credential-isolation mechanism and plan.md's Project Structure entries for
it. They are listed here — not deleted, not silently dropped from plan.md —
but explicitly **BLOCKED**: none may be started under any bounded
autonomous task-group execution until you accept a replacement mechanism for
ADR-0006 (Option A's separate-OS-user execution, or an alternative). T066
remains the only implementable piece of this area, and only in its
documented fail-closed interim posture (token-based verified-identity
derivation, explicitly not claiming OS-level isolation). **No runtime agent
subprocess may launch without an accepted and verified isolation boundary.**

- [ ] **T100** — [BLOCKED] `scripts/bootstrap_credentials.py` (approver credential provisioning)
  **Req**: FR-308 **Scn**: — **ADR**: ADR-0006 **Path**: `scripts/bootstrap_credentials.py`
  **Prereq**: an accepted replacement mechanism for ADR-0006 (not yet decided) **Dep**: none **P**: no
  **Artifact**: none yet — blocked **TDD**: n/a — blocked
  **Validation**: n/a — no command to run until unblocked
  **Docs**: plan.md Project Structure (already lists this planned file, kept — not deleted, per your explicit instruction); ADR-0006 "Revision 4 — Option A Spike Design" (designed, not executed) **Trace**: ADR-0006 (Rejected), FR-308
  **Risk**: **BLOCKED — do not implement.** ADR-0006's credential-isolation mechanism remains Rejected (macOS `sandbox-exec` spike-FAILED; Option A spike designed but never executed, no privileged command run). Building this script now would create a real code path that provisions approver credentials with no accepted isolation boundary protecting them — exactly the risk ADR-0006 exists to prevent.
  **Done**: N/A while blocked — completion criteria to be defined alongside the accepted replacement mechanism **Human**: yes — blocked pending your ADR-0006 replacement decision; must not be started by an agent under any autonomous-execution authorization

- [ ] **T101** — [BLOCKED] `scripts/approve.py` (the sole code path that reads raw approver credentials)
  **Req**: FR-308, FR-309 **Scn**: — **ADR**: ADR-0006 **Path**: `scripts/approve.py`
  **Prereq**: an accepted replacement mechanism for ADR-0006 (not yet decided) **Dep**: none **P**: no
  **Artifact**: none yet — blocked **TDD**: n/a — blocked
  **Validation**: n/a — no command to run until unblocked
  **Docs**: plan.md Project Structure (already lists this planned file, kept — not deleted) **Trace**: ADR-0006 (Rejected), FR-308, FR-309
  **Risk**: **BLOCKED — do not implement.** Same posture as T100, and higher-stakes: plan.md names this specifically as "the only code path that reads raw approver credentials." Building it without an accepted isolation boundary is the single highest-risk file this project could produce; must not be attempted under any bounded autonomous task-group execution.
  **Done**: N/A while blocked **Human**: yes — blocked pending your ADR-0006 replacement decision; must not be started by an agent under any autonomous-execution authorization

- [ ] **T102** — [BLOCKED] `local-secrets/` directory setup and file permissions
  **Req**: — **Scn**: — **ADR**: ADR-0006 **Path**: `local-secrets/`
  **Prereq**: an accepted replacement mechanism for ADR-0006 (not yet decided) **Dep**: none **P**: no
  **Artifact**: none yet — blocked **TDD**: n/a — blocked
  **Validation**: n/a — no command to run until unblocked
  **Docs**: plan.md Project Structure (already lists this planned directory, kept — not deleted) **Trace**: ADR-0006 (Rejected)
  **Risk**: **BLOCKED — do not implement.** Even setting file/directory permission bits here would be meaningless (and could create a false sense of security) without the OS-level isolation boundary ADR-0006 was supposed to provide around whatever this directory holds.
  **Done**: N/A while blocked **Human**: yes — blocked pending your ADR-0006 replacement decision; must not be started by an agent under any autonomous-execution authorization

- [ ] **T103** — [BLOCKED] Final agent-isolation launcher + its security tests
  **Req**: — **Scn**: — **ADR**: ADR-0006 **Path**: TBD — depends on which replacement mechanism you eventually accept (Option A separate-OS-user, or an alternative)
  **Prereq**: an accepted replacement mechanism for ADR-0006 (not yet decided) **Dep**: none **P**: no
  **Artifact**: none yet — blocked **TDD**: n/a — blocked
  **Validation**: n/a — no command to run until unblocked; once unblocked, this task's own Validation must include real, executed security tests proving the isolation boundary holds (not a design-only claim)
  **Docs**: ADR-0006 "Revision 4 — Option A Spike Design" **Trace**: ADR-0006 (Rejected)
  **Risk**: **BLOCKED — do not implement. No runtime agent subprocess may launch through this path without an accepted and verified isolation boundary.** This is distinct from T048 (already implementable — see T048's own clarification note) and T072 (subprocess timeout *durations*, also already implementable): T048 invokes the `claude` CLI using the developer's own already-authenticated session; T103 is specifically the isolated-launch boundary that would stand between an orchestration stage and any credential this project would rather not expose to it.
  **Done**: N/A while blocked — completion criteria to be defined alongside the accepted replacement mechanism, and must include executed (not merely designed) security tests **Human**: yes — the last mandatory item before any orchestration stage that invokes a real subprocess may be considered safe to run against non-disposable credentials; must not be started by an agent under any autonomous-execution authorization

**Checkpoint — carries an explicit disclosed limitation forward, not a silent gap**: approval-gate *logic* (roles, revision-binding, timeout) is real and tested. Approval-gate *credential isolation* (ADR-0006) remains an accepted, documented risk, and its four concrete implementation tasks (T100–T103) are explicitly blocked, not silently dropped. Group 20 may proceed.

---

## Phase 20: Group 20 — Retry and Timeout

- [x] **T070** — Retry-safety gate (idempotent-vs-uncertain, reconciliation-required)
  **Req**: FR-406 (added during `/speckit-analyze` remediation, 2026-09-10,
  finding E1 — narrowly, not a broad FR-401–406 citation: this gate exists to
  make "workflow stage retries" — FR-406's own named example of a repeatable
  operation — safe with respect to an idempotency/reconciliation signal
  before reissuing, which is precisely FR-406's subject; it does not itself
  classify transient-vs-permanent (FR-401), which is `effect_class`'s
  adapter-declared concern)
  **Scn**: — **ADR**: ADR-0007 **Path**: `src/orchestration/scheduler.py`
  **Prereq**: T060 **Dep**: T060 **P**: no
  **Artifact**: retry-issuance gate **TDD**: test-first — an `externally_observable_uncertain` stage never retries without a `not_completed` reconciliation result **Validation**: `uv run pytest tests/orchestration/test_retry_safety.py`
  **Docs**: ADR-0007 (already corrected from the withdrawn "in-band exception is automatically safe" claim) **Trace**: ADR-0007 Rev. 3 finding #11, FR-406 **Risk**: this is the exact defect Round 3 fixed — a regression here reopens it **Done**: gate enforced for every retry path **Human**: no

- [x] **T071** [P] — Corrected backoff (3 attempts, 1s+2s waits)
  **Req**: FR-402 (added during `/speckit-analyze` remediation, 2026-09-10,
  finding E1 — FR-402's own text is "explicit maximum attempt count and
  explicit backoff/timeout behavior," which is exactly this task's subject)
  **Scn**: — **ADR**: ADR-0007 **Path**: `src/orchestration/retry_policy.py`
  **Prereq**: T070 **Dep**: T070 **P**: yes
  **Artifact**: backoff schedule **TDD**: test-first, exact timing assertions **Validation**: `uv run pytest tests/orchestration/test_backoff_timing.py`
  **Docs**: ADR-0007 (already corrected from the miscounted "1s/2s/4s") **Trace**: `PVT-002`, provisionally approved, unverified, FR-402 **Risk**: none beyond the miscounting Round 3 already caught **Done**: exactly 2 waits observed across 3 attempts **Human**: no

- [x] **T072** [P] — Realistic per-subprocess timeouts (5s/300s/600s)
  **Req**: FR-402 (added during `/speckit-analyze` remediation, 2026-09-10,
  finding E1 — the "timeout" half of FR-402's shared attempt-count/timeout
  requirement, split from T071's "attempt-count/backoff" half; both
  legitimately cite the same FR since FR-402 names both in one sentence)
  **Scn**: — **ADR**: ADR-0007 **Path**: `src/orchestration/retry_policy.py`
  **Prereq**: T048 **Dep**: T048 **P**: yes
  **Artifact**: timeout config per subprocess type **TDD**: test-first (mocked long-running subprocess) **Validation**: `uv run pytest tests/orchestration/test_subprocess_timeouts.py`
  **Docs**: ADR-0007 **Trace**: `PVT-003`, provisionally approved, unverified, FR-402
  **Risk**: none beyond the provisional-number caveat. Distinct from T103's
  blocked isolation launcher (Group 19): this task configures timeout
  *durations* for subprocess classes (internal/pytest/Claude), it does not
  build or launch an isolated subprocess boundary — no ADR-0006 replacement
  is required to build T072 itself.
  **Done**: each type's timeout independently configurable and enforced **Human**: no

**Checkpoint**: retry/timeout real — Group 21 may proceed.

---

## Phase 21: Group 21 — Fallback

- [x] **T073** — Fallback-on-`failed_permanent` (defined per stage or safe-stop)
  **Req**: FR-403 (added during `/speckit-analyze` remediation, 2026-09-10,
  finding E1 — FR-403 names exactly this: "exhausting the bounded retry limit
  without recovery MUST lead to a deterministic terminal outcome (fallback,
  safe-stop, or an equivalent defined state)")
  **Scn**: — **ADR**: ADR-0007 **Path**: `src/orchestration/scheduler.py`
  **Prereq**: T070 **Dep**: T070 **P**: no
  **Artifact**: fallback dispatch **TDD**: test-first, both branches (fallback defined / not defined) **Validation**: `uv run pytest tests/orchestration/test_fallback.py`
  **Docs**: none **Trace**: ADR-0007, FR-403 **Risk**: none **Done**: both branches tested **Human**: no

**Checkpoint**: Group 22 may proceed.

---

## Phase 22: Group 22 — Rollback or Compensation

- [x] **T074** — Per-operation-class rollback/compensation dispatch
  **Req**: FR-404 (added during `/speckit-analyze` remediation, 2026-09-10,
  finding E1 — FR-404 is precisely this task's subject: distinguishing
  rollback from compensation and using compensation wherever rollback is not
  technically feasible)
  **Scn**: — **ADR**: ADR-0007 **Path**: `src/orchestration/compensation.py`
  **Prereq**: T073 **Dep**: T073 **P**: no
  **Artifact**: dispatch logic **TDD**: test-first — an infeasible-rollback case must use compensation, never claim rollback
  **Validation**: `uv run pytest tests/orchestration/test_rollback_compensation.py`
  **Docs**: ADR-0007 (already states this rule) **Trace**: ADR-0007, Constitution Principle VIII, FR-404 **Risk**: "invalid rollback claims" is an explicit guide failure trap — the test must specifically assert no rollback is attempted where infeasible **Done**: test passes for both classes **Human**: no

**Checkpoint**: Group 23 may proceed.

---

## Phase 23: Group 23 — Safe-Stop

- [x] **T075** — Safe-stop triggers (retry exhaustion, unresolved policy FAIL, stuck reconciliation)
  **Req**: FR-403, FR-405 (added during `/speckit-analyze` remediation,
  2026-09-10, finding E1 — FR-405 defines the safe-stop state itself
  ["continuing execution would be unsafe... exhausted retries with no valid
  fallback"]; FR-403 is cited alongside it because "retry exhaustion" is
  literally FR-403's named terminal-outcome trigger — this is a legitimate
  2-FR citation, not the broad 6-FR label the finding flagged)
  **Scn**: — **ADR**: ADR-0007 **Path**: `src/orchestration/scheduler.py`
  **Prereq**: T074, T052 **Dep**: T074, T052 **P**: no
  **Artifact**: safe-stop transition logic **TDD**: test-first, all 3 triggers individually **Validation**: `uv run pytest tests/orchestration/test_safe_stop.py`
  **Docs**: ADR-0007 **Trace**: ADR-0007, FR-403, FR-405 **Risk**: none **Done**: all 3 triggers correctly reach `safe_stopped`, never a hang **Human**: no

- [x] **T076** [P] — Safe-stop resumable only via explicit authorized action
  **Req**: FR-405 (added during `/speckit-analyze` remediation, 2026-09-10,
  finding E1 — FR-405's own text: "MUST NOT continue processing the affected
  workflow path past that point without explicit human direction," which is
  precisely this task's no-automatic-resume behavior)
  **Scn**: — **ADR**: — **Path**: `src/orchestration/scheduler.py`
  **Prereq**: T075 **Dep**: T075 **P**: yes
  **Artifact**: resume gate **TDD**: test-first — no automatic resume path exists **Validation**: `uv run pytest tests/orchestration/test_safe_stop_resume.py`
  **Docs**: none **Trace**: Constitution Principle VIII, FR-405 **Risk**: none **Done**: test passes **Human**: no

**Checkpoint**: Group 24 may proceed.

---

## Phase 24: Group 24 — Resume and Recovery

- [x] **T077** — Restart-recovery (unblocks T021)
  **Req**: FR-204, FR-205 **Scn**: — **ADR**: ADR-0005 **Path**: `src/orchestration/scheduler.py` (startup routine)
  **Prereq**: T059 **Dep**: T059 **P**: no
  **Artifact**: startup recovery routine **TDD**: satisfies T021's previously-xfail test **Validation**: `uv run pytest tests/persistence/test_restart_recovery.py`
  **Docs**: none **Trace**: FR-204/205 **Risk**: none beyond what Groups 16–18 already covered **Done**: T021 passes for real **Human**: no

**Checkpoint**: Group 25 may proceed.

---

## Phase 25: Group 25 — Dynamic Replanning

- [x] **T078** — Invalidation cascade on material change (uses T055's detector)
  **Req**: FR-501, FR-502 **Scn**: — **ADR**: ADR-0005 **Path**: `src/orchestration/replanning.py`
  **Prereq**: T055, T068 **Dep**: T055, T068 **P**: no
  **Artifact**: cascade logic **TDD**: test-first — exactly the affected stages/approvals invalidated, none broader **Validation**: `uv run pytest tests/orchestration/test_replanning_cascade.py`
  **Docs**: none **Trace**: FR-501/502 **Risk**: none **Done**: test passes **Human**: no

- [x] **T079** [P] — In-progress worktree invalidation on replan
  **Req**: — **Scn**: — **ADR**: ADR-0005 **Path**: `src/orchestration/workspace.py`
  **Prereq**: T061, T078 **Dep**: T061, T078 **P**: yes
  **Artifact**: invalidation hook into T061's promotion gate **TDD**: test-first **Validation**: `uv run pytest tests/orchestration/test_replan_worktree_invalidation.py`
  **Docs**: none **Trace**: ADR-0005 §Decision — Dynamic Replanning **Risk**: none **Done**: test passes **Human**: no

**Checkpoint**: Group 26 may proceed.

---

## Phase 26: Group 26 — Audit Trail

- [x] **T080** — `audit_events` append-only writer, all required fields
  **Req**: FR-601, FR-602 **Scn**: — **SC**: SC-003 **ADR**: ADR-0008 **Path**: `src/observability/audit.py`
  **Prereq**: T045 **Dep**: T045 **P**: no
  **Artifact**: audit writer **TDD**: test-first, all 6 required fields present on every event **Validation**: `uv run pytest tests/observability/test_audit.py`
  **Docs**: data-model.md **Trace**: FR-601/602 **Risk**: none beyond convention-level append-only enforcement, disclosed **Done**: fields complete on every write path **Human**: no

- [x] **T081** [P] — Correlation-ID linkage (`workflow_instance.id` reused, not a separate scheme)
  **Req**: FR-601 **Scn**: — **ADR**: — **Path**: `src/observability/audit.py`
  **Prereq**: T080 **Dep**: T080 **P**: yes
  **Artifact**: linkage **TDD**: test-first **Validation**: `uv run pytest tests/observability/test_correlation.py`
  **Docs**: none **Trace**: FR-601 **Risk**: none **Done**: every event for one workflow instance shares its ID **Human**: no

**Checkpoint**: Group 27 may proceed.

---

## Phase 27: Group 27 — Logs, Metrics, and Traces

- [x] **T082** — `/metrics/reliability` endpoint (success/failure rate, retry frequency, rollback frequency)
  **Req**: FR-603 **Scn**: — **ADR**: ADR-0008 **Path**: `src/api/routers/metrics.py`
  **Prereq**: T080, T040 **Dep**: T080, T040 **P**: no
  **Artifact**: endpoint **TDD**: test-first **Validation**: `uv run pytest tests/contract/test_metrics.py`
  **Docs**: contracts/openapi.yaml (already specifies the schema, `demonstration_data: true` required) **Trace**: FR-603, FR-604
  **Risk**: must always set `demonstration_data: true` — a missing flag would violate FR-604's explicit prohibition on presenting demo metrics as production stats
  **Done**: all listed metrics computable, flag always true **Human**: no

- [x] **T083** [P] — Operational health signal for analytics degradation (independent of per-code status)
  **Req**: FR-115 **Scn**: — **ADR**: — **Path**: `src/api/routers/health.py`
  **Prereq**: T037 **Dep**: T037 **P**: yes
  **Artifact**: `/health` analytics sub-object, including `degraded_since_unclean_shutdown_at` **TDD**: test-first **Validation**: `uv run pytest tests/contract/test_health.py::test_analytics_degradation`
  **Docs**: contracts/openapi.yaml (already specifies this field as Approved, FR-117) **Trace**: FR-115, FR-117 **Risk**: none **Done**: reviewer can detect degradation without inspecting any specific short code **Human**: no

**Checkpoint**: observability complete — this closes Groups 11–27 (the full orchestration engine). Groups 28–30 (scenarios) may now proceed, since they exercise both the domain (Groups 1–10) and orchestration (Groups 11–27) work together.

---

## Phase 28: Group 28 — Greenfield Scenario

- [x] **T084** — `scripts/demo_greenfield.py`
  **Req**: FR-601, FR-605 **Scn**: Scenario A **SC**: SC-002 **ADR**: — **Path**: `scripts/demo_greenfield.py`
  **Prereq**: all of Groups 1–27 **Dep**: T056, T065 **P**: no
  **Artifact**: runnable demo script **TDD**: end-to-end test wrapping the script **Validation**: `uv run python3 scripts/demo_greenfield.py && uv run pytest tests/e2e/test_greenfield.py`
  **Docs**: quickstart.md (already lists this script as planned) **Trace**: spec.md Scenario A, FR-605
  **Risk**: **CHK090's open item**: the specific greenfield requirement to demonstrate still needs to be selected — flagged, not silently chosen
  **Done**: full path Requirement→...→Release Readiness shows real, inspectable evidence **Human**: yes — confirm the specific greenfield requirement used for the demo

**Checkpoint**: Group 29 may proceed.

---

## Phase 29: Group 29 — Brownfield Scenario

- [x] **T085** — `scripts/demo_brownfield.py` + mandatory pre-change impact analysis
  **Req**: FR-605 **Scn**: Scenario B **SC**: SC-002 **ADR**: — **Path**: `scripts/demo_brownfield.py`
  **Prereq**: Group 28 **Dep**: T078 **P**: no
  **Artifact**: runnable demo + impact-analysis record **TDD**: end-to-end test **Validation**: `uv run python3 scripts/demo_brownfield.py && uv run pytest tests/e2e/test_brownfield.py`
  **Docs**: quickstart.md **Trace**: spec.md Scenario B
  **Risk**: **CHK094's open item**: the specific brownfield change (enhancement/refactor/fix against the now-existing prototype) still needs to be selected — this can only happen once Groups 1–27 actually exist, which is why this scenario is sequenced after them, not before
  **Done**: impact analysis recorded before any code change, regression evidence real **Human**: yes — confirm the specific brownfield change used for the demo

**Checkpoint**: Group 30 may proceed.

---

## Phase 30: Group 30 — Ambiguous Requirement Scenario

- [x] **T086** — `scripts/demo_ambiguous.py`
  **Req**: FR-605 **Scn**: Scenario C **SC**: SC-002 **ADR**: — **Path**: `scripts/demo_ambiguous.py`
  **Prereq**: Group 29 **Dep**: T069 **P**: no
  **Artifact**: runnable demo **TDD**: end-to-end test, including the real approval-gate pause (never auto-approved) **Validation**: `uv run pytest tests/e2e/test_ambiguous.py`
  **Docs**: quickstart.md **Trace**: spec.md Scenario C
  **Risk**: **CHK097's open item** — per the guide's explicit rule, "do not invent ambiguity merely to demonstrate one"; the input must be pre-selected and recorded, not improvised at demo time
  **Done**: detection → suspend → real human decision → resume, all evidenced **Human**: yes — confirm the specific ambiguous input, and provide the real clarification decision at demo time (not auto-approved)

**Checkpoint**: all three required scenarios (spec.md's central requirement) demonstrable — Groups 31–36 (test-suite breadth) and Groups 37–39 (docs/release) may proceed in parallel.

---

## Phase 31: Group 31 — Unit Tests

- [x] **T087** [P] — Domain unit-test coverage sweep (fills gaps beyond the TDD-paired tests already written in Groups 6–10)
  **Req**: FR-101–FR-117 **Scn**: — **ADR**: — **Path**: `tests/unit/`
  **Prereq**: Groups 6–10 **Dep**: T044 **P**: yes
  **Artifact**: coverage report **TDD**: n/a (gap-filling, not new TDD cycles) **Validation**: `uv run pytest tests/unit/ --cov=src/domain`
  **Docs**: none **Trace**: all domain FRs **Risk**: none **Done**: coverage report retained as evidence **Human**: no

**Checkpoint**: Group 32 may proceed (independent of T087's completion).

---

## Phase 32: Group 32 — Contract Tests

- [x] **T088** [P] — Full contract-test sweep against `contracts/openapi.yaml`
  **Req**: — **Scn**: — **ADR**: — **Path**: `tests/contract/`
  **Prereq**: T018 **Dep**: T018 **P**: yes
  **Artifact**: full suite run **TDD**: n/a (sweep) **Validation**: `uv run pytest tests/contract/`
  **Docs**: none **Trace**: contracts/openapi.yaml **Risk**: none **Done**: every endpoint has at least one passing + one failing-path test **Human**: no

---

## Phase 33: Group 33 — Integration Tests

- [x] **T089** [P] — Cross-package integration sweep (domain + orchestration + policy + observability together)
  **Req**: — **Scn**: — **ADR**: — **Path**: `tests/integration/`
  **Prereq**: Groups 1–27 **Dep**: T084 **P**: yes
  **Artifact**: integration suite **TDD**: n/a **Validation**: `uv run pytest tests/integration/`
  **Docs**: none **Trace**: plan.md §10 **Risk**: none **Done**: suite passes **Human**: no

---

## Phase 34: Group 34 — Orchestration Tests

- [x] **T090** — Full orchestration state-transition sweep (this is the Phase 0 stop-condition gate)
  **Req**: FR-201–FR-606 **Scn**: — **ADR**: ADR-0005 **Path**: `tests/orchestration/`
  **Prereq**: Groups 11–27 **Dep**: T060, T083 **P**: no
  **Artifact**: full sweep **TDD**: n/a (sweep of already-TDD'd pieces) **Validation**: `uv run pytest tests/orchestration/`
  **Docs**: none **Trace**: Constitution Principle II
  **Risk**: **per T003's stop condition — if this suite is not passing by end of Day 2, halt new scope and stabilize before touching scenario scripts.** This is the single most consequential validation gate in the whole task plan.
  **Corrected during `/speckit-analyze` remediation (2026-09-10)**: Dep
  previously listed "T090 (self, see Risk)" — a task cannot depend on
  itself; that was a bug, not a deliberate device. Dep now cites T060
  (reconciliation, the deepest single mechanism this sweep validates) and
  T083 (the last task chronologically closing Groups 11–27), representing
  the full Groups 11–27 span already named in Prereq.
  **Done**: full suite green **Human**: no (but a red suite here triggers the human-visible stop-condition checkpoint from T003)

---

## Phase 35: Group 35 — Security Tests

- [x] **T091** [P] — Malicious-input/abuse-case sweep
  **Req**: — **Scn**: — **ADR**: — **Path**: `tests/security/`
  **Prereq**: T041–T044 **Dep**: T042 **P**: yes
  **Artifact**: security test suite **TDD**: n/a (sweep) **Validation**: `uv run pytest tests/security/`
  **Docs**: none **Trace**: Constitution Principle V **Risk**: none beyond already-disclosed limitations (DNS-rebinding, key entropy) **Done**: suite passes **Human**: no

---

## Phase 36: Group 36 — End-to-End Tests

- [x] **T092** — Full golden-path + three-scenario end-to-end sweep
  **Req**: — **Scn**: US1–US5, Scenarios A/B/C **ADR**: — **Path**: `tests/e2e/`
  **Prereq**: Groups 28–30 **Dep**: T084, T085, T086 **P**: no
  **Artifact**: e2e suite **TDD**: n/a **Validation**: `uv run pytest tests/e2e/`
  **Docs**: none **Trace**: quickstart.md's own golden-path section **Risk**: none **Done**: suite passes **Human**: no

**Checkpoint**: Group 37 may proceed.

---

## Phase 37: Group 37 — Documentation

- [x] **T093** — Reconcile `quickstart.md` from "planned" to real, executed commands
  **Req**: — **Scn**: — **ADR**: — **Path**: `specs/001-governed-url-shortener/quickstart.md`
  **Prereq**: T092 **Dep**: T092 **P**: no
  **Artifact**: updated quickstart **TDD**: n/a **Validation**: fresh-clone run of every documented command, output retained
  **Docs**: this task IS the doc update **Trace**: Constitution Principle X (docs evolve with implementation)
  **Risk**: none **Done**: no command in quickstart.md is still labeled "planned" **Human**: no

- [x] **T094** [P] — README (repository-root reviewer entry point)
  **Req**: — **Scn**: — **ADR**: — **Path**: `README.md`
  **Prereq**: T093 **Dep**: T093 **P**: yes
  **Artifact**: README **TDD**: n/a **Validation**: reviewer inspection
  **Docs**: this task **Trace**: guide's repository-structure recommendation **Risk**: none **Done**: exists, links to quickstart/architecture/ADRs **Human**: no

---

## Phase 38: Group 38 — Setup and Quick Start

- [x] **T095** — Fresh-clone verification (guide Section 27, step 61)
  **Req**: — **Scn**: — **ADR**: ADR-0010 **Path**: n/a (procedure)
  **Prereq**: T093 **Dep**: T093 **P**: no
  **Artifact**: verification log **TDD**: n/a **Validation**: clone into a clean directory, run quickstart.md verbatim, retain output
  **Docs**: quickstart.md **Trace**: ADR-0010 §Validation **Risk**: none **Done**: clean run succeeds **Human**: no

---

## Phase 39: Group 39 — Release-Readiness Validation

- [x] **T096** — Run the corrected release-readiness rule against actual state
  **Req**: FR-301–FR-306 **Scn**: — **SC**: SC-006 **ADR**: — **Path**: n/a (procedure, `/speckit-analyze`/`/speckit-converge` territory)
  **Prereq**: Groups 1–38 **Dep**: T090, T092 **P**: no
  **Artifact**: readiness determination **TDD**: n/a **Validation**: every mandatory gate/scenario/control checked against the plan.md-corrected rule (no delivery-bucket exemption)
  **Docs**: this feeds Group 40 **Trace**: plan.md § Planning Constraints (the specific rule corrected at Human Gate 4)
  **Risk**: ADR-0006's unresolved isolation is a live candidate for `READY WITH ACCEPTED LIMITATIONS` — but only if every *other* mandatory item is actually complete; it cannot be used to excuse a different, unrelated gap
  **Done**: exactly one of `READY`/`READY WITH ACCEPTED LIMITATIONS`/`NOT READY` determined, with cited evidence **Human**: yes — release-readiness determination itself requires your sign-off, per FR-301

---

## Phase 40: Group 40 — Final Engineering Summary

- [x] **T097** — Draft the mandatory 21-section summary (guide Section 25)
  **Req**: — **Scn**: — **ADR**: — **Path**: `docs/final-engineering-summary.md` (not yet created)
  **Prereq**: T096 **Dep**: T096 **P**: no
  **Artifact**: 21-section document **TDD**: n/a **Validation**: reviewer inspection against the guide's exact section list
  **Docs**: this task **Trace**: guide Section 25 **Risk**: must not make unsupported claims or omit incomplete outcomes, per the guide's explicit rule **Done**: all 21 sections present, evidence-cited **Human**: yes — this is the assessment submission's centerpiece

## Phase 41: Group 41 — Traceability Matrix

- [x] **T098** [P] — Requirement→Scenario→Design→ADR→Task→Code→Test→Evidence matrix
  **Req**: — **Scn**: — **SC**: SC-003 **ADR**: — **Path**: `docs/traceability-matrix.md` (not yet created)
  **Prereq**: T097 **Dep**: T090 **P**: yes
  **Artifact**: matrix **TDD**: n/a **Validation**: spot-check 10 random FR IDs trace end-to-end
  **Docs**: this task **Trace**: plan.md §13 **Risk**: none **Done**: no orphan requirement/task/test found in the spot-check **Human**: no

## Phase 42: Group 42 — Reviewer Navigation Guide

- [x] **T099** [P] — Reviewer navigation guide (guide Section 26)
  **Req**: — **Scn**: — **ADR**: — **Path**: `docs/reviewer-navigation-guide.md` (not yet created)
  **Prereq**: T097, T098 **Dep**: T097 **P**: yes
  **Artifact**: navigation guide **TDD**: n/a **Validation**: a reviewer following it can locate every required artifact within the guide's own checklist
  **Docs**: this task **Trace**: guide Section 26 **Risk**: none **Done**: every item in guide Section 26's list has a cited path/command **Human**: no

---

## Evidence Tasks (cross-cutting, satisfied by the tasks above — indexed here per the guide's explicit requirement)

| Evidence type (guide's list) | Satisfied by |
|---|---|
| Requirement-to-test traceability | T098 |
| Architecture-decision evidence | docs/adr/ (already committed, `a679708`) |
| Approval evidence | T065, T066, data-model.md `orchestration_approval_decision` |
| Policy-version evidence | T051 |
| Compliance evaluation evidence | T051, T052 |
| Failed-policy blocking evidence | T052 |
| Approved exception evidence | T053 |
| Compensating-control evidence | T053, T074 |
| Change-request and impact-analysis evidence | T055, T085 |
| State-transition evidence | T080 |
| Sequential-path evidence | T056 |
| Parallel-path and synchronization evidence | T057 |
| Retry evidence | T070, T071 |
| Compensation or rollback evidence | T074 |
| Safe-stop evidence | T075 |
| Resume evidence | T077 |
| Replanning evidence | T078, T079 |
| Measured demonstration metrics | T082, T039 (both explicitly labeled `demonstration_data: true`) |
| Limitations | ADR "Risks and Mitigations" sections (already committed) + T097 |
| Residual risks | same |
| Reviewer navigation | T099 |

---

## Notes

- **Not implemented by this document** — per the guide's explicit rule, no code is written here; this is the plan `/speckit-implement` executes against.
- **Human approval markers** above are not exhaustive of every constitutional gate — they flag tasks with a *specific, named* open decision (scheme allow-list, scenario-input selection, release-readiness sign-off, ADR-0006's interim posture, and — new since the remediation pass below — the ADR-0006 replacement decision gating T100–T103). Ordinary implementation work proceeds under the already-accepted plan/ADRs without a fresh gate per task, consistent with the constitution's task-group autonomy boundary.
- **103 tasks total** (T001–T103; no ID gaps or duplicates — verified by the
  `/speckit-analyze` remediation rerun below), organized into 42 groups
  matching the guide's required list exactly (including both items the guide
  numbered "11"), plus four explicitly BLOCKED tasks (T100–T103) added
  within Group 19 during remediation — the guide's group numbering (1–42) is
  unchanged; only the task count within Group 19 grew.
- Before any of this executes, per the constitution's task-group boundary: one coherent group + its tests + its documentation + its traceability update, then stop, inspect, and commit — not an unbounded run across this whole file.

## Phase 43: Group 43 — Post-Implementation Gap Closure

**Added 2026-09-11**, after the Final Engineering Summary (T097) honestly
disclosed three genuinely-incomplete items rather than inflating the
release determination — these three tasks close them. (Note: an EARLIER,
unrelated "T106" was mentioned once in the Remediation Record below, as a
stray/incorrect reference in a task that no longer exists at that number —
that was fixed by pointing to the real T080 back on 2026-09-10. The T106
below is a new, real task, unrelated to that historical note.)

- [x] **T104** — FR-202 conditional workflow branching
  **Req**: FR-202 **Scn**: — **ADR**: ADR-0005 **Path**: `src/orchestration/branching.py`
  **Prereq**: T056 (eligibility query), T063 (lineage) **Dep**: T056 **P**: no
  **Artifact**: `set_stage_outcome`, `add_conditional_branch`, `evaluate_branch_conditions`
  **TDD**: test-first — true/false/malformed/missing-condition cases, plus restart/resume non-reversal
  **Validation**: `uv run pytest tests/orchestration/test_conditional_branching.py` — 6 passed
  **Docs**: docs/final-engineering-summary.md §6, §19 (updated) **Trace**: FR-202, this fixes the one previously-disclosed gap in an otherwise-real sequential/parallel/sync implementation (T056–T058)
  **Risk**: a condition is evaluated against the PARENT stage's persisted outcome only — never live external state — so evaluation is deterministic and idempotent; only 'pending' branch stages are ever touched, which is what makes restart/resume safe by construction, not by a separate resume-specific code path
  **Done**: all 6 tests pass, including the explicit restart/resume non-reversal test **Human**: no

- [x] **T105** — Live policy evaluation in workflow execution
  **Req**: FR-303, FR-304, FR-306 **Scn**: — **SC**: SC-006 **ADR**: — **Path**: `src/policy/live.py`
  **Prereq**: T051 (evaluator), T053 (exception) **Dep**: T051 **P**: no
  **Artifact**: `run_mandatory_policy_checks`, `is_release_ready`; `policy_evaluation.artifact_revision` column added to schema
  **TDD**: test-first — PASS/FAIL/EXCEPTION-REQUESTED/NOT-APPLICABLE + stale-revision invalidation
  **Validation**: `uv run pytest tests/policy/test_live_policy_evaluation.py` — 13 passed
  **Docs**: docs/final-engineering-summary.md §8 (updated); scripts/demo_greenfield.py updated to call `run_mandatory_policy_checks` instead of one manual check, so SC-006 is now demonstrated live, not just unit-tested **Trace**: FR-303, FR-304, FR-306, SC-006
  **Risk**: the 3 automatic per-workflow checks are real, fast, local, and deterministic (lockfile mtime, decision-lineage inspection) — deliberately NOT re-running the slow, network-based `pip-audit` scan per workflow; that remains the separate T044 release-readiness-time check
  **Done**: all 13 tests pass; `scripts/demo_greenfield.py` shows `is_release_ready: True` for a live workflow **Human**: no

- [x] **T106** — Automatic background workflow execution from the HTTP API
  **Req**: FR-201–206 **Scn**: US2 **ADR**: ADR-0005 **Path**: `src/orchestration/live_scheduler.py`
  **Prereq**: T104, T105, T058 (atomic claim), T059 (reaper) **Dep**: T104, T105 **P**: no
  **Artifact**: an asyncio background tick loop started/stopped by `src/api/main.py`'s lifespan; `WorkflowCreateRequest.auto_execute` (additive, opt-in — existing callers unaffected, `stages=[]` behavior preserved for ordinary creation)
  **TDD**: test-first — HTTP-only integration test creating a workflow and observing real transitions with zero direct scheduler calls
  **Validation**: `uv run pytest tests/e2e/test_live_workflow_execution.py tests/orchestration/test_live_scheduler.py` — 4 passed
  **Docs**: docs/final-engineering-summary.md §6, §19 (updated); contracts/openapi.yaml `WorkflowCreateRequest.auto_execute` added (MINOR, additive) **Trace**: FR-201–206, this fixes the "no live HTTP-triggered execution" gap disclosed in the Final Engineering Summary
  **Risk**: **external agent adapters remain fail-closed** — verified by grep, not just asserted: `grep -n "subprocess\|claude\|Popen" src/orchestration/live_scheduler.py` matches only the module's own docstring prose, no executable reference. The default stage executor performs only safe, built-in, in-process completion (no subprocess, no `claude` CLI invocation, no credential access); T048's real CLI wrapper and any future real adapter are deliberately NOT wired into this automatic loop while ADR-0006 remains Rejected, consistent with T100–T103 staying blocked. A real bug was caught by actually running this code (not just reading it): `evaluate_branch_conditions` sets a selected branch directly to `'ready'`, bypassing the `pending`→`ready` scan the claim loop was originally using — fixed by also claiming any already-`'ready'` stage each tick, not just newly-eligible `'pending'` ones.
  **Done**: `tests/orchestration/test_live_scheduler.py` (3 tests: full pipeline → `completed` over several ticks with the correct branch selected/skipped; policy-FAIL auto-`safe_stopped`; no duplicate claims under 8 concurrent threads) + `tests/e2e/test_live_workflow_execution.py` (1 test: `POST /workflows` with `auto_execute:true`, polled purely via `GET /workflows/{id}` — zero direct scheduler calls — reaches `completed` in <1s; audit trail and all 3 policy evaluations confirmed present) — all pass; full suite `205 passed`, stable across 3 consecutive runs **Human**: no

### Remediation Record (`/speckit-analyze` rerun, 2026-09-10)

This document was revised once, after an initial `/speckit-analyze` pass
found six findings (E1–E3, F1–F3) plus three task-ID reference bugs the
analyze skill's own "verify IDs" step would have caught on a second look
(T011→"T124", T040→"T106", and two mislabeled-not-missing references:
T052→"T054 (scheduler)", T053→"T086 (approval mechanism)"). All nine are
fixed in place above, each marked inline at its exact location rather than
summarized only here. New tasks T100–T103 were added (not silently — see
Phase 19 above and Phase 0's "Blocked" note); no existing task was deleted;
task count grew from 99 to 103. See the chat-facing analyze rerun report for
the full before/after finding table and updated coverage metrics.

**Commit** (per guide Section 12): staged for your review before committing, consistent with this project's practice of not committing a major artifact without a chance to review it first.
