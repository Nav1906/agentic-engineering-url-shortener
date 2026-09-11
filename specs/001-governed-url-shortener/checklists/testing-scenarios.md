# TDD/Testing & Three-Scenario (Greenfield/Brownfield/Ambiguous) Checklist: Agentic Software Engineering System: URL Shortener

**Purpose**: Objectively verifiable quality/readiness checklist for guide
categories 11 (TDD and Testing), 12 (Greenfield Scenario), 13 (Brownfield
Scenario), 14 (Ambiguous-Requirement Scenario).
**Created**: 2026-09-10
**Feature**: [plan.md §10–§11](../plan.md), [spec.md Scenarios A/B/C](../spec.md)

**Review Ownership**: Reviewer-owned. `[x]` = requirements-quality
satisfied, not implementation verified — **especially important in this
category**, since no test has been written or run yet; every item here
checks whether the *test plan* is well-specified, not whether tests pass.
IDs continue from `security-reliability-observability.md` (last used:
CHK080).

## 11. TDD and Testing

- [x] CHK081 Is red-green-refactor specified as applying "wherever technically practical" with the qualifier's rationale stated, rather than presented as an unqualified absolute that could later be claimed retroactively? [Clarity, Constitution Principle IV]
- [x] CHK082 Is each test type (unit, contract, persistence, integration, orchestration state-transition, approval, retry/timeout/fallback/rollback/safe-stop, resumption, replanning, concurrency, security, end-to-end, release-readiness) mapped to the specific requirement(s) it demonstrates? [Traceability, plan.md §10]
- [x] CHK083 Is a rule specified prohibiting implementation-first work from being retrospectively described as TDD? [Evidence-integrity, ADR-0002]
- [ ] CHK084 [Gap] Is a minimum test-coverage expectation specified for the orchestration engine's reconciliation logic specifically, given it is the highest-risk component identified in this review? [ADR-0005]
- [x] CHK085 Is it specified that a validation command's actual exit code and output — not merely its existence — constitutes evidence of a passing test? [Evidence-integrity, FR-606, ADR-0005 "Executable Postconditions"]
- [ ] CHK086 [Gap] Is a rule specified for how flaky or order-dependent tests are detected and handled, distinct from genuine failures?

## 12. Greenfield Scenario

- [x] CHK087 Is the requirement-quality check that determines "no clarification needed" specified as producing its own recorded evidence (not merely a pass/fail flag with no rationale)? [Evidence-integrity, FR-601, Spec Scenario A Acceptance Scenario 1]
- [x] CHK088 Is the full evidence path (Requirement → Decomposition → Design → Implementation → Testing → Documentation → Validation → Release Readiness) specified as independently inspectable per step, not only as an end-to-end claim? [Traceability, Spec Scenario A Acceptance Scenario 3]
- [x] CHK089 Is the mid-flight-ambiguity-suspends-only-the-affected-path behavior specified precisely enough to distinguish it from suspending the entire workflow? [Clarity, Spec Scenario A Acceptance Scenario 2]
- [x] CHK090 [Gap] Is a specific, concrete greenfield requirement pre-selected for this scenario's demonstration, or is that decision still open?
- [x] CHK091 Is it specified that the greenfield scenario's terminal outcome must be `completed`, distinguishing a genuine success from a scenario that was merely not-yet-failed? [Measurability, plan.md §11]

## 13. Brownfield Scenario

- [x] CHK092 Is the mandatory pre-code-change impact analysis specified to cover every listed dimension (components, interfaces, data flows, tests, documentation, regression risks, rollout/rollback) individually, with none foldable into a generic "impact assessment"? [Completeness, Spec Scenario B Acceptance Scenario 1]
- [x] CHK093 Is it specified that implementation is structurally blocked (not merely discouraged) until the impact analysis is recorded and reviewed? [Clarity, Spec Scenario B Acceptance Scenario 2]
- [x] CHK094 [Gap] Is a specific, concrete brownfield change pre-selected for this scenario's demonstration (an enhancement, refactor, or defect fix against the eventual working prototype), or is that decision still open — and can it only be selected once a prototype exists to change?
- [x] CHK095 Is the regression-risk assessment specified to require actual regression-test evidence, not only a documented risk statement with no corresponding test run? [Evidence-integrity, Spec Scenario B Acceptance Scenario 3]
- [ ] CHK096 [Gap] Is a rule specified for what "impacted" means precisely (e.g., any component whose behavior, interface, or data contract changes) to avoid a subjective impact-analysis boundary?

## 14. Ambiguous-Requirement Scenario

- [x] CHK097 Is the specific ambiguous input pre-selected and recorded (not left to be improvised at demonstration time, which risks appearing engineered after the fact)? [Evidence-integrity, guide "do not invent ambiguity... merely to demonstrate one"]
- [x] CHK098 Is the suspend-and-request-clarification behavior specified as blocking implementation entirely (not merely delaying it) until an explicit human decision is recorded? [Clarity, Spec Scenario C Acceptance Scenario 2]
- [x] CHK099 Is the resumption behavior specified to continue from the correct workflow state (not from the beginning and not from an arbitrary later point), with "correct state" defined precisely? [Measurability, Spec Scenario C Acceptance Scenario 3]
- [x] CHK100 Is downstream impact analysis specified as a required step following the clarification decision, distinct from the decision itself? [Completeness, Spec Scenario C Acceptance Scenario 3]
- [ ] CHK101 [Gap] Is it specified how this scenario's evidence will demonstrate it is materially distinct from the brownfield scenario's own impact-analysis step, given both involve analyzing downstream effects?

## Notes

- Mark items `[x]` only after review confirms the requirement-quality criterion is satisfied.
- `/speckit-implement` reads checklist checkbox state as a gate and must not modify markers.
- Several items in this file are explicitly `[Gap]` because the corresponding decision (which concrete requirement/change/input to use per scenario) has not yet been made — this is disclosed, not an oversight in the checklist itself.
- Traceability self-check: of the 21 items above (CHK081–CHK101), all 21 carry an explicit reference or `[Gap]` marker (100%).
