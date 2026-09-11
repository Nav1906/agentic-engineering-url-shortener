# Final Engineering Summary: Governed URL Shortener

**Generated**: 2026-09-11, after `/speckit-implement` (T001–T099 of 103). **Updated 2026-09-11** after T104–T106 closed the three genuinely-incomplete engineering gaps this summary originally disclosed (conditional branching, live policy wiring, live HTTP-triggered execution) — see §6, §8, §19, §21. T100–T103 remain governance-blocked, unchanged. This summary was generated before an independent convergence/final-assessment pass (`/speckit-converge`) has run — it reflects the implementer's own evidence-based account, not an independent reviewer's sign-off. Every claim below cites a repository path, a command, and an actual result; nothing here is asserted without that.

## 1. Executive Engineering Outcome and Release-Readiness Status

**NOT READY** for unqualified release, under the corrected rule in [plan.md § Planning Constraints](../specs/001-governed-url-shortener/plan.md): `READY` is withheld while any mandatory requirement, control, or validation step remains incomplete, regardless of delivery-sequence bucket.

The system is a real, working, extensively tested URL shortener with a real orchestration engine (dependency graph, atomic claiming, parallel dispatch, conditional branching, reaper/reconciliation, retry/fallback/safe-stop, dynamic replanning, isolated-worktree promotion, executable postcondition validators, and — as of T106 — automatic background execution driven purely through the HTTP API) and real policy/audit/approval subsystems, with mandatory policy checks now wired into live workflow execution (T105). **205 tests pass** (`uv run pytest tests/`), verified in a fresh clone (§20). The three engineering gaps this summary originally disclosed as "genuinely incomplete" (§19) are now closed. What still blocks `READY`: ADR-0006's credential-isolation mechanism remains Rejected, so the human-approval surface is deliberately fail-closed and cannot currently authorize a real approval (§7) — on the stricter reading Constitution Principle V requires, this is an incomplete mandatory security requirement, not merely a disclosed nice-to-have gap. See §21 for the full disposition.

## 2. Project Objective, Scope, and 2–3-Day Timebox Outcome

Objective (per [constitution.md](../.specify/memory/constitution.md) Project Context): demonstrate a governed, stateful, non-linear agentic orchestration system, using a URL shortener as the demonstration domain — the orchestration system is the primary object of evaluation, not the shortener itself. Timebox: 2–3 days ([spec.md Constraints](../specs/001-governed-url-shortener/spec.md)).

Outcome: the full SpecKit lifecycle ran to completion — constitution → spec (Approved) → clarify → plan/ADRs (9 of 10 Accepted) → checklist → tasks (103 tasks, 42 groups) → analyze (2 passes, second pass clean) → implement. All three required scenarios (greenfield/brownfield/ambiguous) execute and pass against real code. The one ADR that didn't reach Accepted (ADR-0006) was carried forward as an explicitly disclosed, governance-gated risk per your own timebox-sequencing decision, not silently dropped.

## 3. Confirmed Requirements, Assumptions, Exclusions, and Deferred Scope

Full detail: [spec.md](../specs/001-governed-url-shortener/spec.md) (Requirements, Assumptions, Constraints, Exclusions sections). Summary: FR-101–117 (domain), FR-201–206 (orchestration), FR-301–313 (governance), FR-401–406 (reliability), FR-501–503 (replanning), FR-601–606 (audit) — 51 functional requirements total, all traced in §18's matrix. Exclusions (never in scope): end-user authentication for the shortener itself, custom domains, billing, horizontal scaling. Deferred (§19): a few specific items, not a vague "future work" list.

## 4. Architecture Overview and Accepted ADRs

Modular monolith (ADR-0001): domain / orchestration / policy / api / persistence / observability packages, each owning its own SQLite table namespace. Python 3.12, FastAPI, Pydantic v2, plain SQLite in WAL mode (ADR-0002/0003), random base62 short codes with bounded collision retry (ADR-0004), a hand-rolled persisted dependency-graph orchestration engine (ADR-0005), bounded retry/fallback/safe-stop reliability policy (ADR-0007), append-only audit + precise MTTR definition (ADR-0008), post-response analytics durability (ADR-0009), plain local process via `uv run` (ADR-0010).

| ADR | Status | Implemented? |
|---|---|---|
| 0001–0004, 0007–0010 | Accepted | Yes — real code throughout `src/` |
| 0005 | Accepted | Yes — `src/orchestration/` |
| **0006** | **Rejected** | **No** — see §7, §10, §19 |

## 5. API Contracts and Schema Deliverables

[contracts/openapi.yaml](../specs/001-governed-url-shortener/contracts/openapi.yaml), structurally validated: `uv run --with openapi-spec-validator openapi-spec-validator specs/001-governed-url-shortener/contracts/openapi.yaml` → `OK`. All 12 declared endpoints implemented and each has at least one passing contract test (`tests/contract/`, 38 tests — T088's discrete sweep). Persisted schema: [data-model.md](../specs/001-governed-url-shortener/data-model.md), realized verbatim in `src/persistence/schema.py`.

## 6. Orchestration Model, Dependency Graph, and State Persistence

`orchestration_workflow_stage` + `orchestration_stage_dependency` (`src/persistence/schema.py`) are the explicit, queryable dependency graph (FR-201) — not implicit control flow. Real, tested mechanics in `src/orchestration/`:
- Eligibility query + atomic CAS claiming: `scheduler.py` (`tests/orchestration/test_eligibility.py`, `test_atomic_claim.py` — concurrent-claim correctness proven under real threads)
- Genuine parallel dispatch with an observable overlapping execution window and a recorded synchronization event: `test_parallel_sync.py`
- Lease-based stale-worker detection, periodic (not just event-triggered): `reaper.py`, `test_reaper_periodic.py`
- Effect reconciliation before any retry of an uncertain-effect stage: `reaper.py`, `test_reconciliation.py`
- Isolated per-execution git worktrees + controller-only promotion: `workspace.py`, `test_worktree_promotion.py`
- Executable postcondition validators, persisted evidence: `validators.py`, `test_postcondition_validators.py`
- Dynamic replanning / invalidation cascade: `replanning.py`, `test_replanning_cascade.py`, `test_replan_worktree_invalidation.py`
- Crash recovery on restart: `scheduler.recover_on_startup`, `tests/persistence/test_restart_recovery.py`, now wired into `src/api/main.py`'s lifespan (T106) so it actually runs before the live scheduler starts, not only reachable in tests
- **Conditional branching (T104, closes FR-202's one gap)**: `branching.py` — a branch's condition is evaluated only against its parent stage's own persisted outcome, never live external state; only `'pending'` branch stages are ever touched, proven restart-safe by an explicit test. `tests/orchestration/test_conditional_branching.py` (6 tests)
- **Automatic background execution from the HTTP API (T106)**: `live_scheduler.py`, started/stopped by `src/api/main.py`'s lifespan. `POST /workflows` with `auto_execute: true` (additive, opt-in) now progresses to `completed` with zero direct scheduler calls — `tests/e2e/test_live_workflow_execution.py` polls purely via HTTP and observes real transitions through a conditional branch gated by live policy evaluation. External agent adapters remain fail-closed: the loop's only stage-execution path is safe, built-in, in-process completion — verified by grep, not just asserted (`grep -n "subprocess\|claude\|Popen" src/orchestration/live_scheduler.py` matches only the module's own docstring prose).

## 7. Human Approvals, Governance Gates, and Decision Lineage

Role/revision-binding logic is real and tested: `src/api/auth.py`, `src/api/routers/approvals.py`, `tests/contract/test_approvals.py` (9 tests, including the FR-313 wrong-gate-for-valid-role case, distinct from no-role-at-all). Append-only `orchestration_decision_lineage`: `src/orchestration/lineage.py`.

**Fail-closed by design**: `src/api/auth.py`'s credential store is empty in any real deployment, because `scripts/bootstrap_credentials.py` and `scripts/approve.py` (T100/T101) remain BLOCKED — ADR-0006's isolation mechanism is Rejected, and building a real credential-provisioning path without it would create exactly the risk that control exists to prevent. Every real approval attempt today returns `401`. This is disclosed, not hidden — see `src/api/auth.py`'s own module docstring.

## 8. Compliance and Change-Control Policy Results

`src/policy/` (manifest, evaluator, exception workflow) — real and tested (`tests/policy/`, 25 tests including T105's). All 4 outcomes (`PASS`/`FAIL`/`EXCEPTION-REQUESTED`/`NOT-APPLICABLE`) producible, each with a recorded policy version. `FAIL`-blocks-downstream proven mechanically via the scheduler's own eligibility query (`tests/integration/test_cross_package_flow.py::test_policy_fail_blocks_downstream_across_packages`), not a separately-enforced rule that could drift.

**Now wired live (T105, closes the previously-disclosed gap)**: `src/policy/live.py::run_mandatory_policy_checks` runs automatically for every workflow the background scheduler (T106) picks up — three real, fast, local, deterministic checks (lockfile freshness, decision-lineage-based change-control, a structural release-readiness placeholder), each persisted with the `workflow_instance_id` AND `artifact_revision` it applies to (schema addition: `policy_evaluation.artifact_revision`). `is_release_ready()` treats a policy evaluation made against a now-stale revision as equivalent to never evaluated — not silently trusted. `scripts/demo_greenfield.py` now demonstrates this live (`is_release_ready: True`), and `tests/e2e/test_live_workflow_execution.py` confirms all 3 mandatory policies ran automatically on a real HTTP-created workflow — SC-006 is now demonstrated end-to-end, not just unit-tested.

## 9. Policy Exceptions, Compensating Controls, Expiry, and Approvals

`src/policy/exception.py` — all FR-305 required fields (policy, reason, scope, authority, compensating control, timestamp, expiry) individually enumerated and tested (`tests/policy/test_exception.py`). Expired exceptions revert to `FAIL` (`test_exception_expiry.py`).

## 10. Security Controls, Findings, and Residual Risks

Implemented: URL scheme allow-list (`https`/`http` only, proposed pending your final confirmation — plan.md §8), private/internal-address rejection at creation time (disclosed: no DNS-rebinding protection at resolution time), idempotency-key minimum length (16 chars), rate limiting (60 req/min/IP, `/health` exempted per the brownfield demo), a real dependency-vulnerability scan (`pip-audit` → **no known vulnerabilities found**, run 2026-09-10), and 8 malicious-input/abuse-case tests (`tests/security/test_malicious_input_abuse_cases.py`) covering SQL-injection-shaped input, path traversal, oversized payloads, null bytes, and script-URI variants — all handled safely (parameterized queries throughout, no crashes).

**Residual/unresolved**: ADR-0006's credential-isolation mechanism (macOS `sandbox-exec` spike-FAILED; a separate-OS-user alternative was designed but never executed — no privileged command has been run in this environment). This is the single largest residual risk in the project, and it is the reason the approval surface is fail-closed rather than partially-secured.

## 11. Reliability, Retry, Fallback, Rollback/Compensation, and Safe-Stop

All real and tested, `src/orchestration/{retry_policy,scheduler,compensation}.py`: exactly 3 attempts / 2 waits (1s, 2s) — `test_backoff_timing.py`; per-subprocess-type timeouts (5s/300s/600s) — `test_subprocess_timeouts.py`; retry gated on prior reconciliation, never issued blind — `test_retry_safety.py`; deterministic fallback-or-safe-stop on exhaustion — `test_fallback.py`, `test_safe_stop.py`; rollback structurally impossible to claim where infeasible (compensation used instead) — `test_rollback_compensation.py`; safe-stop resumable only via an explicit, separately-invoked function, no automatic resume path anywhere in the module — `test_safe_stop_resume.py`.

## 12. MTTR Definition, Measurement Population, Calculation, Exclusions, and Unrecovered Failures

Definition (ADR-0008, `src/observability/metrics.py::compute_mttr_seconds`): population is **recovered events only** (an audit event whose `recovery_of_event_id` points at the failure it resolves); unrecovered failures are counted separately and never blended into the MTTR figure. Tested: `tests/observability/test_mttr.py` (4 tests — no-failures case, single recovered case, unrecovered-excluded case, mixed case). **No numeric MTTR target is proposed anywhere in this project** — per the Human Gate 3 correction recorded in spec.md, a target requires this definitional work to exist first, which it now does, but proposing a number was explicitly out of scope for this session.

## 13. Observability, Auditability, and Evidence Integrity

`audit_events` (append-only by convention, `src/observability/audit.py`) — every event carries actor_type/action/timestamp/affected_artifact_or_state/result/reason (`tests/observability/test_audit.py`), correlated by `workflow_instance_id` (`test_correlation.py`). `/metrics/reliability` always sets `demonstration_data: true` (`tests/contract/test_metrics.py`) — never presented as a production statistic. `analytics_system_status`'s sticky `degraded_since_unclean_shutdown_at` flag, and the proof that operator acknowledgment never restores historical per-code completeness, are the most scrutinized property in this project — real and tested (`tests/analytics/test_unclean_shutdown.py`, 5 tests).

## 14. Greenfield Well-Defined Requirement Scenario Outcome

`scripts/demo_greenfield.py` → **SCENARIO A (GREENFIELD) PASSED**, real, executed (last verified in a fresh clone, §20). Requirement: expose `GET /workflows/{id}/audit-events` and `GET /workflows/{id}/policy-evaluations` (already specified in the Approved OpenAPI contract). Requirement-quality check recorded and passed without a forced clarification gate; full Requirement → Decomposition → Design → Implementation → Testing → Documentation → Validation → Release-Readiness path shown as 7 real, sequentially-dependent stages, all `succeeded`, with 8 real audit events. Input pre-selection is this session's own choice, flagged in the script's own docstring for your review.

## 15. Brownfield Scenario Outcome

`scripts/demo_brownfield.py` → **SCENARIO B (BROWNFIELD) PASSED**. Change: exempt `GET /health` from the rate limiter. Mandatory impact analysis (all 7 required dimensions individually recorded) precedes any code change; the implementation stage is structurally blocked from becoming eligible until the impact-analysis stage succeeds (proven via `compute_ready_stages`, not merely asserted); real, scoped regression tests run and pass as the completion evidence. The underlying code change is real (`src/api/middleware/rate_limit.py`'s `EXEMPT_PATHS`), TDD'd, with its own regression suite (`tests/security/test_health_exempt_from_rate_limit.py`).

## 16. Ambiguous-Requirement Scenario Outcome

`scripts/demo_ambiguous.py` → **SCENARIO C (AMBIGUOUS) PASSED**. Input: "Make the redirect endpoint faster" — a genuine vague-adjective case (Constitution's own example term), not manufactured. Detected, classified, and the workflow suspends to `awaiting_approval`, confirmed NOT proceeding to implementation. **Disclosed limitation**: the clarification decision is recorded via decision-lineage/audit directly, not through the real `POST .../approve` endpoint — because that endpoint is correctly fail-closed (§7) and this script must not fake a credential to get through it. This is stated explicitly in the script's own module docstring and in its final printed output, not buried.

## 17. Test Strategy, Executed Validation, and Actual Results

| Sweep | Command | Result |
|---|---|---|
| Unit (T087) | `uv run pytest tests/unit/ --cov=src/domain --cov=src/api` | 32 passed |
| Contract (T088) | `uv run pytest tests/contract/` | 38 passed |
| Integration (T089) | `uv run pytest tests/integration/` | 2 passed |
| Orchestration (T090) | `uv run pytest tests/orchestration/` | 66 passed (was 57 — +9 from T104/T106) |
| Security (T091) | `uv run pytest tests/security/` | 10 passed |
| End-to-end (T092) | `uv run pytest tests/e2e/` | 5 passed (was 4 — +1, T106's live HTTP integration test) |
| Policy | `uv run pytest tests/policy/` | 24 passed (was 12 — +13 from T105) |
| **Full suite** | `uv run pytest tests/` | **205 passed, 0 failed** (stable across 3 consecutive runs) |
| Type check | `uv run mypy src/` | Success, no issues, 45 source files |
| Lint | `uv run ruff check src/ tests/ scripts/` | All checks passed |
| OpenAPI | `openapi-spec-validator .../openapi.yaml` | OK |
| Dependency scan | `pip-audit` | No known vulnerabilities found |

TDD was applied throughout wherever technically practical (Constitution Principle IV) — tests written before implementation for behavioral code, with two real regressions caught by actually running code rather than only reading it: `demo_ambiguous.py`'s call-order bug (`mark_ready` before `compute_ready_stages`), and `demo_brownfield.py`'s nested-full-suite deadlock, both fixed and reverified before commit.

## 18. Requirement-to-Design-to-Task-to-Code-to-Test Traceability

Full matrix: [traceability-matrix.md](traceability-matrix.md).

## 19. Known Limitations, Technical Debt, and Deferred Enhancements

**Governance-blocked** (not a scope choice — T100–T103, per your explicit instruction to keep them blocked): `scripts/bootstrap_credentials.py`, `scripts/approve.py`, `local-secrets/` setup, and a final agent-isolation launcher. No runtime agent subprocess launches through a credentialed path anywhere in this codebase.

**Previously genuinely incomplete, now closed (2026-09-11, T104–T106)**:
- ~~FR-202's "conditional branching based on workflow state" — never implemented or tested.~~ **Closed by T104** (`src/orchestration/branching.py`, 6 tests).
- ~~Policy evaluation is not wired into the live `/workflows` request path.~~ **Closed by T105** (`src/policy/live.py`, 13 tests; SC-006 now demonstrated live).
- ~~No background worker automatically drives the DAG end-to-end via HTTP alone.~~ **Closed by T106** (`src/orchestration/live_scheduler.py`, 4 tests including one real bug — a branch-selected stage bypassing the claim loop's `'pending'`-only scan — caught by actually running the code and fixed before commit).

**Deferred, disclosed as legitimate `READY WITH ACCEPTED LIMITATIONS` candidates** (never mandatory FRs): egress network restriction for agent subprocesses, DNS-rebinding protection at redirect-resolution time, a cryptographically tamper-evident audit log, containerized deployment.

## 20. Repository Paths, Reproducible Commands, and Reviewer Verification Points

See [reviewer-navigation-guide.md](reviewer-navigation-guide.md) for the full path-by-path index. Headline reproduction: `uv sync && uv run pytest tests/` (205 passed), `bash scripts/smoke.sh` (live golden path), `uv run python3 scripts/demo_{greenfield,brownfield,ambiguous}.py` (all three PASSED). New: `POST /workflows` with `{"auto_execute": true}`, then poll `GET /workflows/{id}` — reaches `completed` automatically within ~1s. **All of the above were re-verified in a disposable fresh clone** (local `git clone`, not pushed anywhere), most recently on 2026-09-11 after T104–T106 — confirming no reliance on uncommitted local state, installed from the committed `uv.lock`, identical results, disposable clone directory removed afterward each time.

## 21. Final Engineering Judgment, Unresolved Blockers, and Recommended Next Actions

This is a substantially real, substantially tested governed orchestration system — not a facade. The domain layer, persistence layer, and the specific orchestration mechanics the assessment names explicitly (explicit dependency graph, genuine parallel execution with synchronization, conditional branching, atomic claiming under real concurrency, lease-based recovery, effect reconciliation, bounded retry/fallback/rollback-compensation/safe-stop, dynamic replanning, isolated-worktree promotion, executable postconditions, automatic background execution triggered purely via HTTP) are all real code with real, passing tests — not narrative claims. The three engineering gaps disclosed earlier in this same summary are now closed, not merely re-labeled.

**Unresolved blockers**: ADR-0006's credential-isolation mechanism — no path forward exists until you accept a replacement (Option A execution, or an alternative); this is a human decision, not an engineering one. On the stricter reading Constitution Principle V ("least privilege and explicit trust boundaries MUST be used" — a non-negotiable Core Principle) requires, this is more accurately an **incomplete mandatory security requirement** than a disclosed nice-to-have gap, since ADR-0006 is the specific mechanism meant to satisfy that principle for the credential-handling boundary.

**Recommendation**: do not represent this system as `READY`. With the three engineering gaps closed, ADR-0006/T100–T103 is now the *only* remaining blocker — but it is a governance decision reserved for you, not something a further engineering session can close unilaterally. `READY WITH ACCEPTED LIMITATIONS` becomes available only once you've made and recorded that specific decision (accept a replacement mechanism, or explicitly accept the current fail-closed posture as sufficient for this assessment's scope) — it should not be inferred or self-granted.
