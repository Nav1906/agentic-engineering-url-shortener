# Reviewer Navigation Guide

Concise index — every item cites an exact path, an exact command where applicable, the expected observable result, and the related requirement/scenario ID. Extended detail lives in the referenced documents, not here.

## 1. Project objective
[.specify/memory/constitution.md](../.specify/memory/constitution.md) § Project Context. The orchestration system, not the URL shortener, is the primary object of evaluation.

## 2. How to run the application
```bash
uv sync && uv run uvicorn src.api.main:app --reload
```
Expected: server starts on `http://localhost:8000`. [quickstart.md](../specs/001-governed-url-shortener/quickstart.md).

## 3. How to run tests
```bash
uv run pytest tests/ -v
```
Expected: `184 passed`. Also: `uv run mypy src/` → `Success: no issues found in 42 source files`; `uv run ruff check src/ tests/` → `All checks passed`.

## 4. How to exercise the URL shortener
```bash
bash scripts/smoke.sh
```
Expected: `SMOKE TEST PASSED`, exercising create → resolve → analytics → delete → 404. Related: FR-101–117, SC-001.

## 5. How to initiate an orchestration workflow
```bash
curl -s -X POST http://localhost:8000/workflows -H "Content-Type: application/json" -d '{"requirement": "demo"}'
```
Expected: `201`, a workflow `id`. Related: FR-201, FR-601. Code: `src/api/routers/workflows.py`.

## 6. How to inspect workflow state
```bash
curl -s http://localhost:8000/workflows/<id>
```
Expected: stages, `depends_on` edges, `decision_lineage`. Related: FR-204, FR-206. Also `GET /workflows/<id>/audit-events`, `GET /workflows/<id>/policy-evaluations`.

## 7. How to perform a human approval
`tests/contract/test_approvals.py` — real role/revision-binding logic, tested via a TEST-ONLY credential-registration helper (`src/api/auth.py::register_test_credential`, never called by application code). **A real approval cannot currently be performed against a live deployment** — the endpoint is fail-closed because ADR-0006 remains Rejected and T100/T101 (credential provisioning) are BLOCKED. See `src/api/auth.py`'s module docstring. Related: FR-301–313.

## 8. How to demonstrate retry
```bash
uv run pytest tests/orchestration/test_retry_safety.py tests/orchestration/test_backoff_timing.py -v
```
Expected: all pass; exactly 3 attempts, exactly 2 waits (1s, 2s). Code: `src/orchestration/retry_policy.py`, `scheduler.py::issue_retry_or_exhaust`. Related: FR-401, FR-402, FR-406.

## 9. How to demonstrate compensation or rollback
```bash
uv run pytest tests/orchestration/test_rollback_compensation.py -v
```
Code: `src/orchestration/compensation.py`. Related: FR-404.

## 10. How to demonstrate safe-stop
```bash
uv run pytest tests/orchestration/test_safe_stop.py tests/orchestration/test_safe_stop_resume.py -v
```
Related: FR-403, FR-405.

## 11. How to demonstrate dynamic replanning
```bash
uv run pytest tests/orchestration/test_replanning_cascade.py tests/orchestration/test_replan_worktree_invalidation.py -v
```
Code: `src/orchestration/replanning.py`. Related: FR-501, FR-502.

## 12. Greenfield scenario
```bash
uv run python3 scripts/demo_greenfield.py
```
Expected: `SCENARIO A (GREENFIELD) PASSED`. Related: spec.md Scenario A, FR-605.

## 13. Brownfield scenario
```bash
uv run python3 scripts/demo_brownfield.py
```
Expected: `SCENARIO B (BROWNFIELD) PASSED`. Related: spec.md Scenario B, FR-605.

## 14. Ambiguous-requirement scenario
```bash
uv run python3 scripts/demo_ambiguous.py
```
Expected: `SCENARIO C (AMBIGUOUS) PASSED`. Note the script's own printed disclosure about the clarification-decision substitute. Related: spec.md Scenario C, FR-605.

## 15. Architecture
[plan.md](../specs/001-governed-url-shortener/plan.md) §1–§12. Package layout: `src/{domain,orchestration,policy,api,persistence,observability}/`.

## 16. ADRs
[docs/adr/](adr/) — 9 of 10 Accepted; `0006-human-approval-model.md` is Rejected (see its Revision 3/4 for the full spike history).

## 17. Requirement traceability
[traceability-matrix.md](traceability-matrix.md) — every FR mapped to task, code, test.

## 18. Audit evidence
`audit_events` table, written by `src/observability/audit.py`. Inspect via `GET /workflows/<id>/audit-events` or directly: any test in `tests/observability/`.

## 19. Reliability measurements
```bash
curl -s http://localhost:8000/metrics/reliability
```
Always `demonstration_data: true`. `mttr_seconds` is `null` until a recovered-failure event exists in this deployment's own audit trail — by design, not a bug. Related: FR-603, FR-604, ADR-0008.

## 20. Security controls
[final-engineering-summary.md](final-engineering-summary.md) §10. Code: `src/domain/validation.py` (scheme/private-address), `src/domain/idempotency.py` (key-length floor), `src/api/middleware/rate_limit.py`. Scan evidence: `pip-audit` → no known vulnerabilities (run 2026-09-10).

## 21. Known limitations
[final-engineering-summary.md](final-engineering-summary.md) §19 — split explicitly into governance-blocked (T100–T103) vs. genuinely incomplete (FR-202 conditional branching, live policy wiring, live DAG-execution trigger) vs. deferred-and-legitimately-acceptable (egress restriction, DNS-rebinding protection, tamper-evident audit log, containerization).

## 22. Final engineering summary
[final-engineering-summary.md](final-engineering-summary.md) — the full 21-section account.

## 23. API contracts, schemas, versions, compatibility/migration rules, examples, and contract-test evidence
[contracts/openapi.yaml](../specs/001-governed-url-shortener/contracts/openapi.yaml) (versioning/change-control rules at the file's own bottom). Contract tests: `tests/contract/` (38 tests, one per endpoint minimum — T088).

## 24. Compliance/change-control results and approved exceptions
`src/policy/` — real, tested (`tests/policy/`, 12 tests). No policy exception has been approved in this codebase's own history (none was ever requested); the mechanism itself is tested via `tests/policy/test_exception.py` and `test_exception_expiry.py`.

## 25. MTTR calculation inputs, recovered-event population, exclusions, unrecovered failures, and demonstration-data limitations
See item 19 above and [final-engineering-summary.md](final-engineering-summary.md) §12. Definition lives in `src/observability/metrics.py::compute_mttr_seconds`'s own docstring, not duplicated here.
