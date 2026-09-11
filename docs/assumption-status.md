# Assumption Status

**Purpose**: one of the 13 required `/speckit-converge` outputs (guide
Section 22). Tracks every assumption recorded in
[spec.md § Assumptions](../specs/001-governed-url-shortener/spec.md) through
to its current, post-implementation status. No assumption is silently
dropped or left unresolved without disposition.

| ID | Assumption (from spec.md) | Original status | Current status | Disposition |
|---|---|---|---|---|
| A-001 | A single-operator/local demonstration deployment is sufficient; no multi-tenant isolation, horizontal auto-scaling, or managed cloud environment | Assumption | **Held, confirmed by implementation** | ADR-0002/0003/0010 (SQLite local process, `uv run`, no Docker/cloud) implement exactly this scope; never contradicted during implementation |
| A-002 (AMB-002) | "Analytics" means count/timestamp aggregation per short code only, not user-level tracking, device fingerprinting, or geolocation | Assumption | **Confirmed via clarification, no longer an assumption** | Resolved during `/speckit-clarify` (Session 2026-09-10); now FR-105/FR-107, implemented in `src/domain/analytics.py`-equivalent and tested (`tests/analytics/`) |
| A-003 (AMB-003) | Reviewer/approver and release-owner roles are enforced as distinct authorization roles; the same human may hold both in this single-operator prototype (role separation, not person separation) | Assumption | **Confirmed via clarification, no longer an assumption** | Resolved during `/speckit-clarify`; now FR-312/FR-313, implemented in `src/api/auth.py` and `src/api/routers/approvals.py`, tested including the negative wrong-role case (`tests/contract/test_approvals.py::test_fr313_*`) |
| A-004 | "Operational health" (FR-111) refers to the URL shortener's own runtime and direct dependencies, not orchestration-system health (covered separately by FR-206) | Assumption | **Held, confirmed by implementation** | `/health` covers the domain runtime only; `GET /workflows/{id}` covers workflow-state inspection separately — the two were never merged, matching the assumption |
| A-005 | Short codes and destination URLs are not treated as containing regulated personal data; no data-residency or data-subject-rights handling in scope | Assumption | **Held, never revisited** | No implementation work touched data-residency or subject-rights handling; the assumption's own stated revisit trigger ("if the clarification stage surfaces a reason to change it") never fired during `/speckit-clarify` |

## Cross-cutting assumption introduced during implementation (not in original spec.md list)

| ID | Assumption | Status | Disposition |
|---|---|---|---|
| A-006 | Excluding external-agent subprocess execution from the trusted boundary entirely (rather than solving same-OS-user credential isolation) is an acceptable scope-limitation for this release | **Confirmed via explicit Human Gate 4 decision (2026-09-11)** | This was not silently assumed — it required its own explicit human decision, recorded in `docs/adr/0006-human-approval-model.md` "Revision 5" and `docs/governance/`. Distinguished from a spec-time assumption because it was a mid-implementation governance decision, not a pre-implementation guess. |

## Summary

- **5 of 5** original spec.md assumptions have an explicit, evidence-backed
  disposition — none remain silently unresolved.
- **2 of 5** (A-002, A-003) were formally confirmed during `/speckit-clarify`
  and are no longer assumptions at all — they are requirements.
- **3 of 5** (A-001, A-004, A-005) remain assumptions by design (never
  contradicted, never required revisiting) and are still accurately
  labeled as assumptions rather than promoted to unstated fact.
- **1 additional** assumption (A-006) arose during implementation and was
  resolved through an explicit human governance decision, not silently.
