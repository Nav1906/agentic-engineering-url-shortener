# Traceability Matrix: Requirement → Task → Code → Test

**Generated**: 2026-09-11. Spot-check method: for each row, the Code and Test paths are real files in this repository as of commit `21b3866` and later; the Test column's file, if present, was part of the 184-test passing run. `—` in Test means no dedicated test exists for that requirement specifically (see Status).

## Domain (FR-101–117)

| FR | Requirement (short) | Task(s) | Code | Test | Status |
|---|---|---|---|---|---|
| FR-101 | Scheme allow-list, malformed rejection | T011,T014,T022,T025,T026 | `src/domain/validation.py` | `tests/unit/test_domain_validation.py`, `tests/contract/test_create_short_link.py` | Implemented, tested |
| FR-102 | Unique short code among active links | T011,T023,T024 | `src/domain/short_link.py` | `tests/unit/test_short_link_model.py`, `test_short_code_collision.py` | Implemented, tested |
| FR-103 | Resolve; distinguish unknown/expired/success | T028–030 | `src/api/routers/redirect.py` | `tests/contract/test_resolve.py` | Implemented, tested |
| FR-104 | Optional `expiresAt`, no default expiration | T011,T032 | `src/domain/short_link.py`, `validation.py` | `tests/contract/test_expiration.py`, `test_resolve.py` | Implemented, tested |
| FR-105 | Accurate redirect counting, no duplicates | T034 | `src/domain/analytics.py` | `tests/analytics/test_ordering.py` | Implemented, tested |
| FR-106 | Bounded analytics latency budget | T034,T039 | `src/domain/analytics.py` (post-response `BackgroundTasks`) | `tests/analytics/test_budget.py` | Implemented; `PVT-001` sample measured, not a percentile claim |
| FR-107 | Aggregate analytics + completeness status | T035,T036 | `src/domain/analytics.py` | `tests/analytics/test_completeness_status.py` | Implemented, tested |
| FR-108 | Request-level idempotency (no key = always new) | T027 | `src/domain/idempotency.py` | `tests/contract/test_idempotency.py` | Implemented, tested |
| FR-109 | Persistence-layer failure observable, non-silent | T019 | `src/persistence/db.py`, `retry.py` | `tests/persistence/test_db.py`, `test_retry.py` | Implemented, tested |
| FR-110 | Correctness under concurrency | T019,T058 | `src/persistence/db.py` (WAL), `scheduler.py` (CAS) | `tests/orchestration/test_atomic_claim.py` (real threads) | Implemented, tested |
| FR-111 | Operational health indicator | T007,T083 | `src/api/routers/health.py` | `tests/contract/test_health.py` | Implemented, tested |
| FR-112 | Idempotent replay returns original, no re-validation of expiry | T027,T033 | `src/domain/idempotency.py` | `tests/contract/test_idempotency.py::test_replay_after_expiry` | Implemented, tested |
| FR-113 | Conflicting replay → 409 | T027 | `src/domain/idempotency.py` | `tests/contract/test_idempotency.py::test_same_key_different_payload_conflicts` | Implemented, tested |
| FR-114 | `expiresAt` must be valid + strictly future at creation | T014,T031 | `src/domain/validation.py` | `tests/unit/test_domain_validation.py`, `tests/contract/test_expiration.py` | Implemented, tested |
| FR-115 | Analytics degradation observable independent of any code | T083 | `src/api/routers/health.py` | `tests/contract/test_health.py::test_analytics_degradation` | Implemented, tested |
| FR-116 | Idempotency records retained indefinitely, independent of link lifecycle | T012 | `src/domain/idempotency.py` | `tests/contract/test_delete.py::test_delete_retains_idempotency_record` | Implemented, tested |
| FR-117 | Sticky unclean-shutdown flag; ack never restores history | T037,T038 | `src/observability/system_status.py` | `tests/analytics/test_unclean_shutdown.py` (5 tests), `test_running_marker.py` | Implemented, tested |

## Orchestration (FR-201–206)

| FR | Requirement | Task(s) | Code | Test | Status |
|---|---|---|---|---|---|
| FR-201 | Explicit dependency graph | T045,T056 | `src/orchestration/models.py`, `scheduler.py` | `tests/orchestration/test_eligibility.py` | Implemented, tested |
| FR-202 | Sequential/parallel/sync/conditional branching | T057,T104 | `scheduler.py`, `src/orchestration/branching.py` | `test_parallel_sync.py`, `test_conditional_branching.py` (6 tests) | **Implemented, tested** (2026-09-11 — was Partial; T104 closed the conditional-branching gap) |
| FR-203 | Per-stage inputs/outputs/entry/exit/actor/failure, inspectable before running | T045 | `src/orchestration/models.py` | `tests/orchestration/test_eligibility.py` (indirect) | Implemented; no dedicated pre-execution-inspection test |
| FR-204 | Persist state/context/provenance/lineage across interruption | T045,T063,T077 | `models.py`, `lineage.py`, `scheduler.recover_on_startup` | `tests/persistence/test_restart_recovery.py` | Implemented, tested |
| FR-205 | Controlled resumption from persisted state | T077 | `src/orchestration/scheduler.py` | `tests/persistence/test_restart_recovery.py` | Implemented, tested |
| FR-206 | Workflow creation + inspection as independent capabilities | T045,T106 | `src/api/routers/workflows.py`, `live_scheduler.py` | `tests/contract/test_workflows.py`, `tests/e2e/test_live_workflow_execution.py` | Implemented, tested — a workflow created via `auto_execute:true` now progresses to `completed` automatically, driven purely by the HTTP API |

## Human Governance (FR-301–313)

| FR | Requirement | Task(s) | Code | Test | Status |
|---|---|---|---|---|---|
| FR-301 | Mandatory gate list, never bypassed | T065–069 | `src/api/routers/approvals.py` | `tests/contract/test_approvals.py` | Implemented (fail-closed, §7 of summary), tested |
| FR-302 | Gate decision recorded as approved/rejected/timed-out, never inferred | T069 | `src/orchestration/scheduler.py` (timeout scaffolding) | `tests/orchestration/test_safe_stop.py` (adjacent) | Implemented; dedicated live timeout test not present |
| FR-303 | Policy outcome + version recorded, exactly one per check | T051,T105 | `evaluator.py`, `src/policy/live.py` | `test_evaluator.py`, `test_live_policy_evaluation.py` (13 tests) | Implemented, tested — now runs automatically per live workflow (2026-09-11), not just unit-tested |
| FR-304 | FAIL blocks downstream progression | T052 | `src/policy/evaluator.py` + `scheduler.py` eligibility | `tests/integration/test_cross_package_flow.py::test_policy_fail_blocks_downstream_across_packages` | Implemented, tested |
| FR-305 | Exception record, all required fields | T053 | `src/policy/exception.py` | `tests/policy/test_exception.py` | Implemented, tested |
| FR-306 | Material change → impact analysis + approval | T055,T105 | `replanning.py`, `src/policy/live.py::_check_change_control` | `test_change_detection.py`, `test_live_policy_evaluation.py` | Implemented, tested — live check now blocks a workflow automatically when a declared material change lacks a succeeded impact-analysis stage |
| FR-307 | Reject unauthenticated / wrong-role attempts | T065,T100 | `src/api/auth.py`, `approvals.py`, `credentials.py` | `tests/contract/test_approvals.py`, `tests/security/test_t103_security_verification.py` | Implemented, tested — real credential pipeline (2026-09-11) |
| FR-308 | Identity from verified credential, never caller-supplied name | T066,T100,T101 | `src/api/auth.py`, `src/api/credentials.py` | `test_approvals.py`, `test_credential_provisioning.py` (11), `test_t103_security_verification.py` | Implemented, tested — real end-to-end approval proven via `scripts/approve.py`'s exact pipeline (2026-09-11, was TEST-ONLY-credential-only before) |
| FR-309 | Agent identity unconditionally rejected | T067 | `src/api/auth.py::reject_if_agent` | `tests/contract/test_approvals.py::test_agent_identity_rejected_unconditionally` | Implemented, tested |
| FR-310 | Approval record: identity/role/decision/rationale/timestamp/gate/revision | T065 | `src/api/routers/approvals.py` | `tests/contract/test_approvals.py` (DB-row field check) | Implemented, tested |
| FR-311 | Approval bound to artifact revision, invalidated on material change | T064,T068,T078 | `models.py`, `replanning.py` | `tests/orchestration/test_replanning_cascade.py` | Implemented, tested |
| FR-312 | Distinct reviewer_approver / release_owner roles | T065 | `src/api/auth.py::GATE_REQUIRED_ROLE` | `tests/contract/test_approvals.py` | Implemented, tested |
| FR-313 | Approval under one role never satisfies a gate requiring the other | T065 | `src/api/auth.py::required_role_for_gate` | `tests/contract/test_approvals.py::test_fr313_*` (2 tests) | Implemented, tested |

## Reliability (FR-401–406)

| FR | Requirement | Task(s) | Code | Test | Status |
|---|---|---|---|---|---|
| FR-401 | Classify transient vs. permanent, retry only transient | T060 | `src/orchestration/reaper.py::reconcile_stage` | `tests/orchestration/test_reconciliation.py` | Implemented, tested |
| FR-402 | Bounded retries, explicit count + backoff/timeout | T020,T071,T072 | `retry.py`, `retry_policy.py` | `test_retry.py`, `test_backoff_timing.py`, `test_subprocess_timeouts.py` | Implemented, tested |
| FR-403 | Exhaustion → deterministic terminal outcome | T073,T075 | `scheduler.py::apply_fallback_or_safe_stop` | `test_fallback.py`, `test_safe_stop.py` | Implemented, tested |
| FR-404 | Rollback vs. compensation, infeasible-rollback never claimed | T074 | `src/orchestration/compensation.py` | `test_rollback_compensation.py` | Implemented, tested |
| FR-405 | Safe-stop when continuation unsafe, no auto-continue | T075,T076 | `scheduler.py` | `test_safe_stop.py`, `test_safe_stop_resume.py` | Implemented, tested |
| FR-406 | Repeatable operations idempotent | T027,T070 | `idempotency.py`, `scheduler.py::issue_retry_or_exhaust` | `test_idempotency_model.py`, `test_retry_safety.py` | Implemented, tested |

## Replanning & Lineage (FR-501–503)

| FR | Requirement | Task(s) | Code | Test | Status |
|---|---|---|---|---|---|
| FR-501 | Upstream change invalidates downstream, triggers replan | T078 | `src/orchestration/replanning.py` | `test_replanning_cascade.py` | Implemented, tested |
| FR-502 | Replanning re-requests approval, never carries forward | T078 | `replanning.py::invalidate_downstream` | `test_replanning_cascade.py` | Implemented, tested |
| FR-503 | Append-only decision lineage | T063 | `src/orchestration/lineage.py` | (exercised throughout `tests/orchestration/`) | Implemented, tested |

## Audit & Evidence (FR-601–606)

| FR | Requirement | Task(s) | Code | Test | Status |
|---|---|---|---|---|---|
| FR-601 | Correlation id on every execution | T045,T080 | `models.py`, `audit.py` | `test_correlation.py` | Implemented, tested |
| FR-602 | Audit event required fields | T080 | `src/observability/audit.py` | `test_audit.py` | Implemented, tested |
| FR-603 | Success/failure/retry/rollback rate + MTTR + unrecovered count | T040,T082 | `src/observability/metrics.py` | `test_mttr.py`, `tests/contract/test_metrics.py` | Implemented, tested |
| FR-604 | Demonstration data labeled, never presented as production stat | T082 | `metrics.py`, `schemas.py::ReliabilityMetrics` | `tests/contract/test_metrics.py` | Implemented, tested |
| FR-605 | Three scenarios, materially distinct, independently evidenced | T084–086 | `scripts/demo_*.py` | `tests/e2e/test_{greenfield,brownfield,ambiguous}.py` | Implemented, tested |
| FR-606 | Claimed execution backed by real artifact/command evidence | T062 | `src/orchestration/validators.py`, `workspace.py` | `test_postcondition_validators.py`, `test_worktree_promotion.py` | Implemented, tested |

## Success Criteria (SC-001–006)

| SC | Requirement | Demonstrated by | Status |
|---|---|---|---|
| SC-001 | Create/resolve/observe analytics via exposed interface | `scripts/smoke.sh`, `tests/e2e/test_golden_path.py` | Yes |
| SC-002 | Three scenarios, materially different paths | `scripts/demo_{greenfield,brownfield,ambiguous}.py` | Yes |
| SC-003 | Any audited claim traces to a real artifact/command | This matrix + `docs/final-engineering-summary.md` | Yes |
| SC-004 | Recovery duration measurable (no numeric target) | `tests/observability/test_mttr.py` | Yes (definitional only, as required) |
| SC-005 | Reject at gate → distinct non-approved terminal state | `tests/contract/test_approvals.py` | Yes |
| SC-006 | 100% mandatory policy checks recorded with version, live | `tests/e2e/test_live_workflow_execution.py` (confirms 3/3 policy evaluations via `GET /workflows/{id}/policy-evaluations`), `scripts/demo_greenfield.py` (`is_release_ready: True`) | **Yes** (2026-09-11 — was Partial; T105 wired policy evaluation into live workflow execution) |

**Spot-check**: 10 random FR IDs (FR-105, FR-202, FR-308, FR-402, FR-501, FR-602, FR-107, FR-313, FR-062→FR-606, FR-401) were traced end-to-end from this matrix to their cited code and test files during generation — all resolved to real, existing files; no orphans found. FR-202 was the one confirmed partial/incomplete row at that time, disclosed accurately rather than marked complete.

**Update (2026-09-11)**: FR-202 and SC-006 — the two rows honestly marked Partial above — are now closed. T104 (conditional workflow branching), T105 (live policy evaluation), and T106 (automatic background workflow execution from the HTTP API) were added and implemented specifically to close them; see `docs/final-engineering-summary.md` §21 for the updated release-readiness disposition. `tests/e2e/test_live_workflow_execution.py` is the single test that most directly demonstrates all three together: it creates a workflow purely via HTTP, observes real automatic progression (T106) through a conditional branch (T104) gated by live-evaluated mandatory policies (T105), reaching `completed` with zero direct scheduler calls.

**Update (2026-09-11, later same day)**: Human Gate 4 accepted a scope-limited ADR-0006 Revision 5 (external-agent subprocess execution permanently excluded from this prototype's trusted boundary). FR-307, FR-308, and the human-approval mechanism generally are now backed by a real, tested, end-to-end credential pipeline (T100–T103, 32 tests: `tests/security/test_credential_provisioning.py`, `test_external_agent_shutdown.py`, `test_t103_security_verification.py`), not merely role-logic tested against a fake test-only credential as before. See `docs/adr/0006-human-approval-model.md` Revision 5 and `docs/threat-model.md` for the exact, disclosed boundary this does and does not cover.
