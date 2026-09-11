# Convergence Report

**Purpose**: this document is the top-level index for the 13 outputs
required by `/speckit-converge` (guide Section 22). It does not duplicate
content that already lives in dedicated artifacts — it states where each
required output lives and, for the two outputs with no prior standalone
home (checklist status, release-readiness restatement), gives the content
directly.

**Generated**: 2026-09-11, as the single convergence pass requested (no
repeated review cycles). **Convergence method**: the codebase, tests, and
documentation were assessed against `spec.md`, `plan.md`, `tasks.md`, and
the constitution per the guide's Prompt 9 categories (Requirements,
Architecture, Orchestration, Three Scenarios, Testing, Documentation,
Compliance and Change Control, Evidence Integrity). **Outcome: no new
`tasks.md` convergence-phase tasks were appended** — no actionable gap was
found that traces to a `missing`/`partial`/`contradicts` finding against a
mandatory requirement, architecture decision, or existing task. The 13
findings below are documentation consolidation and correction, not
application-code or architecture gaps.

## The 13 required outputs

1. **Requirement traceability matrix** → [traceability-matrix.md](traceability-matrix.md) (FR-101 through SC-006 mapped to task/code/test; **corrected during this pass** — its header cited a stale "184-test passing run"; this document was not actually independently re-verified when this report first claimed it was "already current," and is now corrected along with that claim, per the independent assessment's finding)
2. **Final checklist status** → see below
3. **Test and validation summary** → see below (full detail: [final-engineering-summary.md §17](final-engineering-summary.md))
4. **Security summary** → [security-summary.md](security-summary.md) (new this pass)
5. **Reliability summary** → [reliability-summary.md](reliability-summary.md) (new this pass)
6. **Risk register** → [risk-register.md](risk-register.md) (new this pass)
7. **Known limitations** → [final-engineering-summary.md §19](final-engineering-summary.md) (unchanged — already current)
8. **Residual risks** → folded into [risk-register.md](risk-register.md) (R-001–R-003; also [threat-model.md](threat-model.md))
9. **Assumption status** → [assumption-status.md](assumption-status.md) (new this pass)
10. **Scenario evidence index** → [scenario-evidence-index.md](scenario-evidence-index.md) (new this pass)
11. **Reviewer navigation guide** → [reviewer-navigation-guide.md](reviewer-navigation-guide.md) (corrected this pass — stale ADR-0006 "Rejected" reference fixed)
12. **Final engineering summary** → [final-engineering-summary.md](final-engineering-summary.md) (corrected this pass — stale ADR-0006 status table row and test count fixed)
13. **Release-readiness decision** → see below

## 2. Final checklist status

117 objectively-verifiable checklist items across 5 custom files (19
guide-mandated categories) plus the built-in 16-item `requirements.md`
(14 fully checked, 2 explicitly `[~]` partial — disclosed in that file's
own Notes section, not silently dropped from the count; "14/14" undercounts
the file's actual scope and was corrected to "14/16, 2 partial" here after
the independent assessment flagged the more favorable framing). Reviewed
against actual current
evidence during this pass — items were **not** mechanically bulk-marked;
each was individually evaluated against real spec/plan/ADR/code/test
content, and several `[Gap]`-tagged items that were open at spec-quality
time were re-verified as since-resolved (e.g., CHK052 — ADR-0006's status
is now accurately reflected everywhere post-Revision-5; CHK090/CHK094 —
the greenfield/brownfield demo inputs, unselected at checklist-creation
time, are now concretely pre-selected in `scripts/demo_*.py`).

| File | Checked | Total | % |
|---|---|---|---|
| `requirements-architecture.md` | 28 | 30 | 93% |
| `orchestration-governance.md` | 26 | 29 | 90% |
| `security-reliability-observability.md` | 19 | 21 | 90% |
| `testing-scenarios.md` | 17 | 21 | 81% |
| `release-evidence-submission.md` | 14 | 16 | 88% |
| **Total** | **104** | **117** | **89%** |

**All 13 items left unchecked are `[Gap]`-tagged items** (a category the
checklists themselves define as disclosed, known-open items, not
oversights) — none traces to a mandatory FR, ADR, or task left
unsatisfied. Each is a legitimate, minor, non-blocking specification gap:

| ID | Gap | Why non-blocking |
|---|---|---|
| CHK019 | No general rule for when a rejected ADR may be reconsidered (only this project's specific ADR-0006 instance exists) | Not required by any FR; ADR-0006 itself demonstrates the pattern worked in practice |
| CHK030 | No automated architecture-drift detection (code vs. ADR-0001 package boundaries) | Manual review sufficed for this timebox; not a mandatory FR |
| CHK034 | Decision-lineage append-only is convention, not a DB-level constraint | Same disclosed limitation pattern as the audit log (ADR-0008); no code path writes UPDATE/DELETE to it today |
| CHK039 | No orphan-workflow-stage detection | Never observed in practice; not a mandatory FR |
| CHK043 | No numeric limit on task groups executed without a human checkpoint | Operator judgment was used throughout this session and is disclosed as such, not hidden |
| CHK074 | "Resumption correctly worked" evidence criteria not formally specified (tests do compare specific state, but no spec-level definition exists) | Tests (`test_safe_stop_resume.py`, `test_restart_recovery.py`) do this in practice |
| CHK080 | No minimum audit-evidence retention period specified | Explicitly left open, not silently assumed |
| CHK084 | No numeric test-coverage target for reconciliation logic specifically | Reconciliation is tested (`test_reconciliation.py`) without a stated numeric floor |
| CHK086 | No formal flaky/order-dependent test detection rule | None observed in 242 real test runs this session |
| CHK096 | No precise spec-level definition of "impacted" for brownfield impact analysis | The brownfield demo's own impact-analysis stage enumerates concrete dimensions in practice |
| CHK101 | No explicit statement distinguishing the ambiguous scenario's impact analysis from the brownfield scenario's | Conceptually distinct (post-clarification vs. pre-change) but left to reviewer inference |
| CHK106 | The final-tag requirement (`assessment-submission-v1.0`) is not yet written into any repository document | By design — tagging is Phase 5 of this convergence pass, not yet reached; **do not tag yet**, per explicit instruction |
| CHK115 | No general "label as demonstration vs. fact" rule beyond the existing metrics-specific rule (FR-604) | Demonstration labeling was applied consistently in practice throughout (scenario scripts, this report) without a codified general rule |

## 3. Test and validation summary

Re-run in full during this convergence pass (not reused from a stale
prior run):

| Check | Command | Result |
|---|---|---|
| Full test suite | `uv run pytest tests/` | **242 passed, 0 failed** (241 at convergence-pass time, +1 new regression test added post-independent-assessment for the concurrency fix -- see final-independent-assessment.md) |
| Type check | `uv run mypy src/` | Success, no issues found in 47 source files |
| Lint | `uv run ruff check src/ tests/ scripts/` | All checks passed |

Full per-sweep breakdown (unit/contract/integration/orchestration/security/
e2e/policy) and the live-server credential demonstration: see
[final-engineering-summary.md §17](final-engineering-summary.md) — reused,
not duplicated, since those per-sweep numbers did not change this pass
(only the security suite grew, from 42 to 46 tests, by the 4 new identity-
impersonation-resistance tests added as part of this convergence pass's
pre-push checks; verified above via the full-suite total, 237→241→242, the last +1 from the post-assessment concurrency-fix regression test).

## 13. Release-readiness decision

**READY WITH ACCEPTED LIMITATIONS.**

Restated from [final-engineering-summary.md §1](final-engineering-summary.md)
and unchanged by this convergence pass: every mandatory requirement,
scenario, security control, human-approval gate, policy-check outcome, and
validation step is complete, real, and tested (242 passing tests,
re-verified in a fresh clone). The accepted limitations — same-OS-user
credential-file compromise, operator-macOS-account compromise, and any
future release reintroducing external-agent execution — are fully
disclosed ([threat-model.md](threat-model.md),
[security-summary.md](security-summary.md),
[risk-register.md](risk-register.md)) and were never mandatory FRs.

**Confirmed final, post-independent-assessment.** This decision has now
been through the guide's Section 23 Final Independent Assessment
([final-independent-assessment.md](final-independent-assessment.md)),
run by a fresh reviewer agent with no implementation-session context.
Verdict: **BORDERLINE, no mandatory blocking gaps** (the assessment's own
explicit finding). The one confirmed real defect it surfaced (a
`policy_evaluation` duplicate-row race under concurrent scheduler ticks)
has been fixed and regression-tested; the remaining findings were
documentation staleness (fixed) or disclosed, non-mandatory limitations
(logged as backlog, not fixed, per instruction not to reopen accepted
architecture for subjective improvement). The release-readiness decision
is therefore **unchanged and confirmed**: `READY WITH ACCEPTED
LIMITATIONS` — not tightened, because no mandatory gap was found, and not
loosened, because the accepted limitations remain exactly as disclosed
before this review.
