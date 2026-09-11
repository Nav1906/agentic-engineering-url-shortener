# GitHub Evidence, Release Readiness & Assessment Submission Checklist: Agentic Software Engineering System: URL Shortener

**Purpose**: Objectively verifiable quality/readiness checklist for guide
categories 17 (GitHub Evidence), 18 (Release Readiness), 19 (Assessment
Submission).
**Created**: 2026-09-10
**Feature**: [docs/governance/](../../../docs/governance/), [plan.md § Planning Constraints](../plan.md)

**Review Ownership**: Reviewer-owned. `[x]` = requirements-quality
satisfied, not implementation verified. IDs continue from
`testing-scenarios.md` (last used: CHK101).

## 17. GitHub Evidence

- [x] CHK102 Is a requirement specified that commit messages describe engineering intent (not just "wip" or "fix"), with this checked against the actual commit history to date? [Constitution Principle X]
- [x] CHK103 Is it specified that commits must reflect the actual execution sequence, with a prohibition on manufacturing commits to create the appearance of TDD after the fact? [Evidence-integrity, guide "Suggested Commit Progression"]
- [x] CHK104 [Gap] Is a requirement specified for how ADR-0006's Rejected status and the Option A spike's real (blocked) outcome remain visible in git history, rather than only in a document that could be overlooked? — **Self-check**: commit `a679708` records this; verify on each future commit that this remains true.
- [x] CHK105 Is it specified that no confidential material (the assignment guide) may ever appear in git history, with the current `.gitignore` rule verified against the actual tracked file list, not merely assumed correct? [Security]
- [ ] CHK106 [Gap] Is a final-tag requirement specified (e.g., `assessment-submission-v1.0`), to be applied only after a clean status and a validated fresh-clone run — per the guide's Section 28?

## 18. Release Readiness

- [x] CHK107 Is the release-readiness outcome set specified as exactly `READY` / `READY WITH ACCEPTED LIMITATIONS` / `NOT READY`, with no fourth, softer category available? [Clarity, spec.md User Story 4]
- [x] CHK108 Is it specified, without exception, that a missing mandatory scenario, security control, approval, policy outcome, or validation step blocks `READY` regardless of which delivery-sequence bucket it falls in — the specific rule corrected at this review after an earlier draft got it wrong? [Consistency, plan.md § Planning Constraints]
- [x] CHK109 Is the distinction between a legitimate "accepted limitation" (a genuinely non-mandatory item) and a disguised waiver of a mandatory requirement specified precisely, with examples of each? [Clarity, plan.md § Planning Constraints]
- [x] CHK110 Is ADR-0006's unresolved status specified as a named, disclosed accepted-limitation candidate — rather than something the readiness determination would need to silently work around? [Evidence-integrity, docs/governance/ Sequencing Decision]
- [x] CHK111 [Gap] Is a specific, minimum defensible release-readiness bar defined for *this* timebox (which of the mandatory items above absolutely must exist before any readiness claim is made)?
- [x] CHK112 Is it specified that a release-readiness determination must cite the exact repository artifacts and commands a reviewer can use to verify it, not only a narrative conclusion? [Evidence-integrity, Constitution Principle XI]

## 19. Assessment Submission

- [x] CHK113 Is the mandatory 21-section Final Engineering Summary schema (per the guide, Section 25) specified as the target structure, so its eventual generation isn't improvised? [Completeness]
- [x] CHK114 Is a Reviewer Navigation Guide specified as a required deliverable distinct from the Final Engineering Summary, with its own defined purpose (quick verification paths, not a restatement)? [Clarity, guide Section 26]
- [ ] CHK115 [Gap] Is it specified which claims in the eventual submission must be labeled "demonstration" versus presented as unqualified fact, consistent with the demonstration-data labeling rule already established for metrics (FR-604)?
- [x] CHK116 Is a final independent, adversarial review (the guide's "Principal Engineer Assessment") specified as a required step before submission, distinct from and in addition to this session's own iterative self-review? [Completeness, guide Section 23]
- [x] CHK117 [Gap] Is it specified how known, unresolved items at submission time (e.g., if ADR-0006 is still unresolved) will be disclosed in the submission itself, rather than only in an internal governance file a reviewer might not open?

## Notes

- Mark items `[x]` only after review confirms the requirement-quality criterion is satisfied.
- `/speckit-implement` reads checklist checkbox state as a gate and must not modify markers.
- This category is necessarily the most forward-looking of the five files — several items are `[Gap]` because the underlying artifacts (Final Engineering Summary, Reviewer Navigation Guide, final tag) don't exist yet by design; that is expected at this lifecycle stage, not an oversight.
- Traceability self-check: of the 16 items above (CHK102–CHK117), all 16 carry an explicit reference or `[Gap]` marker (100%).

---

## Cross-File Summary (all 19 guide-mandated categories)

| # | Category | File | Item range |
|---|---|---|---|
| 1 | Requirements | requirements-architecture.md | CHK001–CHK007 |
| 2 | Architecture | requirements-architecture.md | CHK008–CHK013 |
| 3 | Architecture Decision Records | requirements-architecture.md | CHK014–CHK019 |
| 4 | Agentic Orchestration | orchestration-governance.md | CHK031–CHK039 |
| 5 | Controlled Autonomy | orchestration-governance.md | CHK040–CHK045 |
| 6 | Human Approvals | orchestration-governance.md | CHK046–CHK052 |
| 7 | Security | security-reliability-observability.md | CHK060–CHK066 |
| 8 | Compliance and Change-Control | orchestration-governance.md | CHK053–CHK059 |
| 9 | Reliability and Recovery | security-reliability-observability.md | CHK067–CHK074 |
| 10 | Observability and Auditability | security-reliability-observability.md | CHK075–CHK080 |
| 11 | TDD and Testing | testing-scenarios.md | CHK081–CHK086 |
| 12 | Greenfield Scenario | testing-scenarios.md | CHK087–CHK091 |
| 13 | Brownfield Scenario | testing-scenarios.md | CHK092–CHK096 |
| 14 | Ambiguous-Requirement Scenario | testing-scenarios.md | CHK097–CHK101 |
| 15 | Documentation | requirements-architecture.md | CHK020–CHK024 |
| 16 | Traceability | requirements-architecture.md | CHK025–CHK030 |
| 17 | GitHub Evidence | release-evidence-submission.md | CHK102–CHK106 |
| 18 | Release Readiness | release-evidence-submission.md | CHK107–CHK112 |
| 19 | Assessment Submission | release-evidence-submission.md | CHK113–CHK117 |

**117 items total across 5 files, all 19 guide-mandated categories covered.**
