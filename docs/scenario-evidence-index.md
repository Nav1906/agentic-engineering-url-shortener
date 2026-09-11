# Scenario Evidence Index

**Purpose**: one of the 13 required `/speckit-converge` outputs (guide
Section 22). A single lookup table for the three mandatory scenarios —
narrative detail lives in
[final-engineering-summary.md §14–§16](final-engineering-summary.md); this
indexes exactly where the evidence for each required element lives.

| Scenario | Initial input | Normalized requirement | Decomposition/orchestration path | Governance evidence | Validation/audit evidence | Outcome | Reproduce |
|---|---|---|---|---|---|---|---|
| **A — Greenfield** | Pre-selected, well-defined: expose `GET /workflows/{id}/audit-events` and `GET /workflows/{id}/policy-evaluations` (already in the Approved OpenAPI contract) | Requirement-quality check recorded and passed without a forced clarification gate | 7 real, sequentially-dependent orchestration stages, all `succeeded` | Live policy evaluation (T105) runs automatically; `is_release_ready: True` | 8 real audit events; `orchestration_workflow_stage`/`orchestration_decision_lineage` rows | **SCENARIO A (GREENFIELD) PASSED** | `uv run python3 scripts/demo_greenfield.py` |
| **B — Brownfield** | Pre-selected: exempt `GET /health` from the rate limiter | Mandatory impact analysis, all 7 required dimensions individually recorded, precedes any code change | Implementation stage structurally blocked (not merely discouraged) until impact-analysis stage succeeds — proven via `compute_ready_stages`, not asserted | Impact-analysis stage is a real, persisted orchestration stage, not a document only | Real, scoped regression suite: `tests/security/test_health_exempt_from_rate_limit.py` | **SCENARIO B (BROWNFIELD) PASSED** | `uv run python3 scripts/demo_brownfield.py` |
| **C — Ambiguous** | Pre-selected genuine vague-adjective case: "Make the redirect endpoint faster" (Constitution's own example term, not invented for the demo) | Detected and classified as ambiguous — workflow suspends to `awaiting_approval`, confirmed NOT proceeding to implementation | Suspension recorded via decision lineage; resumption after a human decision continues from the correct suspended state, not from the beginning | Clarification decision recorded via decision-lineage/audit directly — **disclosed limitation**: not through the real fail-closed `POST .../approve` endpoint, to avoid faking a credential | Decision-lineage rows + audit events for the suspend/resume transition | **SCENARIO C (AMBIGUOUS) PASSED** | `uv run python3 scripts/demo_ambiguous.py` |

## Cross-scenario evidence integrity notes

- All three scripts run against real code, real persistence, and were
  re-verified in a disposable fresh clone (final-engineering-summary.md
  §20) — not only in this working checkout.
- Each script's own module docstring discloses its pre-selected
  input/change up front, so the demonstration cannot be read as improvised
  or engineered after the fact (guide's explicit requirement: "do not
  invent ambiguity... merely to demonstrate one").
- Scenario C's approval-substitution limitation is stated in the script's
  own printed output at runtime, not only in this document.
