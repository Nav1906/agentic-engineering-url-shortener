# Agentic Orchestration, Controlled Autonomy, Human Approvals & Compliance Checklist: Agentic Software Engineering System: URL Shortener

**Purpose**: Objectively verifiable quality/readiness checklist for guide
categories 4 (Agentic Orchestration), 5 (Controlled Autonomy), 6 (Human
Approvals), 8 (Compliance and Change-Control Policy Enforcement).
**Created**: 2026-09-10
**Feature**: [docs/adr/0005-orchestration-model.md](../../../docs/adr/0005-orchestration-model.md), [docs/adr/0006-human-approval-model.md](../../../docs/adr/0006-human-approval-model.md)

**Review Ownership**: Reviewer-owned. `[x]` = requirements-quality
satisfied, not implementation verified. IDs continue from
`requirements-architecture.md` (last used: CHK030).

## 4. Agentic Orchestration

- [ ] CHK031 Is the dependency graph representation specified as explicit, queryable data (table rows) rather than implicit control flow, such that "is this genuinely non-linear" is independently checkable? [Clarity, ADR-0005, avoids the guide's "linear chaining disguised as orchestration" trap]
- [ ] CHK032 Are parallel-execution and synchronization requirements specified with a concrete example (not just an abstract capability claim)? [Measurability, ADR-0005 DAG example]
- [ ] CHK033 Is persisted workflow state defined precisely enough that "was context preserved across an interruption" is a testable question, not a subjective one? [Measurability, FR-204]
- [ ] CHK034 [Gap] Is decision-lineage append-only behavior specified as an enforced constraint (e.g., no UPDATE/DELETE path exists) rather than merely a convention? [Constitution Principle II]
- [ ] CHK035 Is the retry-safety rule specified precisely enough to distinguish "safe to retry" from "requires reconciliation" for every failure path (exception, timeout, stale lease)? [Clarity, ADR-0005/0007, avoids "unlimited retries" and premature-retry traps]
- [ ] CHK036 Is a rollback claim, wherever made, backed by a stated technical-feasibility justification rather than asserted generically? [Measurability, avoids the guide's "invalid rollback claims" trap]
- [ ] CHK037 Is the safe-stop trigger set (retry exhaustion with no fallback, unresolved mandatory policy failure, stuck reconciliation) exhaustively enumerated rather than left open-ended? [Completeness, ADR-0007]
- [ ] CHK038 Is dynamic replanning specified to invalidate exactly the affected downstream artifacts/approvals — no broader, no narrower — with the invalidation rule stated explicitly? [Clarity, FR-501/502]
- [ ] CHK039 [Gap] Is a requirement established for detecting and reporting an "orphan" workflow stage (one with no path to any terminal outcome) before it is considered a completeness risk?

## 5. Controlled Autonomy

- [ ] CHK040 Is the boundary of autonomous execution defined as a bounded unit (one task group + its tests/docs/traceability), not an unbounded multi-task run? [Clarity, Constitution "Development Workflow and Human Gates"]
- [ ] CHK041 Is it specified that Claude Code may propose, compare, and recommend but never self-mark an ADR Accepted? [Completeness, Constitution Principle III, guide guardrail "Do Not Allow Claude to Approve Its Own Decisions"]
- [ ] CHK042 Is agent-adapter tool selection specified as invoking existing SpecKit commands rather than reimplementing lifecycle logic, with the rule for what happens on a detected gap made explicit (route upstream, never decide inline)? [Consistency, ADR-0005 "avoids becoming a competing lifecycle framework"]
- [ ] CHK043 [Gap] Is there a specified limit on how many task groups may execute without a human checkpoint, or is this left to the operator's judgment with no objective bound?
- [ ] CHK044 Is the distinction between an agent's own summary and actual evidence stated as an explicit rule (a generated statement is not itself proof)? [Evidence-integrity, Constitution Principle XI]
- [ ] CHK045 Are the seven categories of action requiring human approval (per FR-301) each individually named, with none left as an unenumerated "etc."? [Completeness]

## 6. Human Approvals

- [ ] CHK046 Is approver-identity derivation specified as coming from a verified credential, with the rejection of caller-supplied-name identity stated explicitly? [Clarity, FR-308]
- [ ] CHK047 Are the two approval roles (reviewer_approver, release_owner) mapped to their specific gates with no gate left unassigned to either role? [Completeness, FR-312]
- [ ] CHK048 Is it specified that an approval under one role must not satisfy a gate requiring the other role, with a negative test scenario named for this? [Coverage, FR-313, Spec User Story 4 Acceptance Scenario 4]
- [ ] CHK049 Is agent-originated approval explicitly and unconditionally prohibited (not merely "discouraged")? [Clarity, FR-309]
- [ ] CHK050 Is the timeout/escalation behavior for an unanswered approval specified as distinct from both "approved" and "rejected," with lack-of-response never interpreted as approval? [Completeness, FR-302, avoids "approval inferred from silence" trap]
- [ ] CHK051 Is revision-binding for approvals specified precisely (which exact artifact revision an approval applies to, and what invalidates it)? [Measurability, FR-311]
- [ ] CHK052 [Gap] Is the credential-isolation mechanism's current status (Rejected/spike-pending) reflected accurately everywhere it's referenced, so no document overstates its readiness?

## 8. Compliance and Change-Control Policy Enforcement

- [ ] CHK053 Is the versioned policy model specified with a concrete manifest location and format, not left as an abstract concept? [Clarity, research.md §8, `config/policies.yaml`]
- [ ] CHK054 Is every policy evaluation specified to record the policy version evaluated, with no path where a policy check runs without a recorded version? [Completeness, FR-303, avoids "policy execution without a recorded policy version" trap]
- [ ] CHK055 Is it specified that a `FAIL` outcome mechanically blocks downstream progression (a structural consequence of the graph model), rather than relying on a separately-enforced rule that could drift out of sync? [Consistency, plan.md §9]
- [ ] CHK056 Are the required fields for a policy exception record (policy, reason, scope, authority, compensating control, timestamp, expiry) each individually enumerated with none merged into a catch-all field? [Completeness, FR-305]
- [ ] CHK057 Is an expired, unreviewed policy exception specified to be treated as a policy failure rather than silently continuing to apply? [Coverage, avoids "expired policy exception" trap]
- [ ] CHK058 Is the impact-analysis requirement for a material change (to requirements, architecture, schemas, workflow states, security controls, release criteria) specified as unconditional — no listed change type exempted? [Completeness, FR-306, avoids "material change implemented without impact analysis" trap]
- [ ] CHK059 [Gap] Is a compensating control required and recorded for every approved policy exception, with no exception approvable without one?

## Notes

- Mark items `[x]` only after review confirms the requirement-quality criterion is satisfied.
- `/speckit-implement` reads checklist checkbox state as a gate and must not modify markers.
- Traceability self-check: of the 29 items above (CHK031–CHK059), 27 carry an explicit reference or `[Gap]` marker (93%).
