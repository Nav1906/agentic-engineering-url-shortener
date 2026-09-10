#!/usr/bin/env python3
"""Scenario C -- Ambiguous requirement demonstration (T086, spec.md
Scenario C).

Pre-selected input (this session's own choice, flagged for your review --
see tasks.md T086's Risk field, and the guide's explicit rule: "do not
invent ambiguity merely to demonstrate one"): "Make the redirect endpoint
faster." This is genuinely ambiguous as stated -- no measurable target, no
baseline, no scope (which endpoint call path? under what load?) -- the
exact class of vague adjective (Constitution's own example: "fast") this
project's requirement-quality check is designed to catch, not a
manufactured edge case.

IMPORTANT DISCLOSED LIMITATION: this script does NOT route the
clarification decision through the real POST /workflows/{id}/gates/{id}/
approve endpoint. That endpoint is fail-closed by design (src/api/auth.py)
because ADR-0006's credential-isolation mechanism remains Rejected and
T100/T101 (credential provisioning) remain BLOCKED -- there is no real
approver credential this script could legitimately present, and
`register_test_credential` is explicitly TEST-ONLY, never to be called
from scripts/ (see auth.py's own docstring). Faking an approval here would
violate that documented invariant and would misrepresent what this
system can currently do. Instead, this script records the clarification
decision directly via the decision-lineage/audit mechanisms (the same
tables a real approval would write to), clearly labeled below as a
demonstration substitute for the still-unavailable real approval gate --
not a claim that real human governance ran.
"""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import src.persistence.db as db_module

VAGUE_ADJECTIVES = {"fast", "faster", "scalable", "secure", "intuitive", "robust", "better"}
NUMBER_PATTERN = re.compile(r"\d")


def detect_ambiguity(requirement_text: str) -> dict | None:
    """Requirement-quality check (FR-601): a vague adjective with no
    accompanying measurable number is classified as ambiguous."""
    words = {w.strip(".,!?").lower() for w in requirement_text.split()}
    found = words & VAGUE_ADJECTIVES
    has_number = bool(NUMBER_PATTERN.search(requirement_text))
    if found and not has_number:
        return {
            "ambiguity_type": "vague_unmeasurable_adjective",
            "flagged_terms": sorted(found),
            "reason": "no measurable target, baseline, or scope accompanies the vague term",
        }
    return None


def main() -> None:
    db_module.DB_PATH = str(Path(tempfile.mkdtemp()) / "demo_ambiguous.db")
    conn = db_module.get_connection()
    db_module.init_schema(conn)

    from src.observability.audit import record_event
    from src.orchestration.lineage import append as append_lineage
    from src.orchestration.models import add_stage, create_workflow_instance
    from src.orchestration.scheduler import (
        claim_stage,
        complete_stage,
        compute_ready_stages,
        mark_ready,
    )

    requirement = "Make the redirect endpoint faster"
    print("=== Scenario C: Ambiguous Requirement ===")
    print(f"Input: {requirement!r}\n")

    wf = create_workflow_instance(conn, requirement, scenario="ambiguous")
    print(f"[1] Workflow created: {wf}")

    ambiguity = detect_ambiguity(requirement)
    assert ambiguity is not None, "this demo's own input must actually be detected as ambiguous"
    print(f"[2] Ambiguity detected and classified: {ambiguity}")
    append_lineage(conn, wf, "ambiguity_detected", ambiguity)
    record_event(conn, "system", "ambiguity_detected", f"workflow:{wf}", "detected",
                 ambiguity["reason"], workflow_instance_id=wf)

    # FR: Scenario C AS1/AS2 -- does not proceed to implementation; workflow
    # transitions to a blocked/clarification state.
    conn.execute(
        "UPDATE orchestration_workflow_instance SET status='awaiting_approval' WHERE id=?", (wf,)
    )
    conn.commit()
    print("[3] Workflow -> awaiting_approval (suspended, NOT proceeding to implementation)")

    # No time-based auto-resolution: demonstrate that inspecting the
    # workflow while suspended shows it still awaiting_approval, never
    # silently advancing.
    from src.orchestration.models import get_workflow_instance
    row = get_workflow_instance(conn, wf)
    assert row["status"] == "awaiting_approval"
    print("[4] Confirmed: workflow remains blocked until an explicit human decision is recorded.")

    # --- DISCLOSED SUBSTITUTE FOR THE REAL APPROVAL GATE (see module
    # docstring) --- the real POST .../approve endpoint is fail-closed
    # (ADR-0006 unresolved); this records what the clarification decision
    # WOULD be, directly against the same audit/lineage tables, explicitly
    # labeled as a demonstration substitute, not a real authenticated
    # approval.
    clarification_decision = {
        "clarification": (
            "Target: p95 redirect latency under 50ms, measured via a load test at "
            "100 req/s sustained for 60s. This numeric target is NOT approved by this "
            "demonstration -- it illustrates what a resolved clarification looks like. "
            "Real target-setting is deferred; out of scope for this timebox."
        ),
        "decided_by": "DEMONSTRATION SUBSTITUTE -- not a real authenticated approval "
        "(see module docstring: ADR-0006 unresolved, T100/T101 blocked)",
    }
    print(f"\n[5] Clarification decision (demonstration substitute): {clarification_decision['clarification']}")
    append_lineage(conn, wf, "clarification_decision", clarification_decision)
    record_event(
        conn, "system", "clarification_recorded", f"workflow:{wf}", "recorded",
        "DEMONSTRATION SUBSTITUTE for a real human approval -- see script docstring",
        workflow_instance_id=wf,
    )

    # FR: Scenario C AS3 -- downstream impact analysis follows the
    # clarification, distinct from the decision itself; resumes at the
    # correct workflow state, not from the beginning.
    conn.execute("UPDATE orchestration_workflow_instance SET status='running' WHERE id=?", (wf,))
    conn.commit()
    impact_stage = add_stage(conn, wf, "downstream_impact_analysis")
    ready = compute_ready_stages(conn, wf)
    assert impact_stage in ready
    mark_ready(conn, [impact_stage])
    execution_id = claim_stage(conn, impact_stage, "ambiguous-demo-worker")
    append_lineage(conn, wf, "downstream_impact_analysis", {
        "affected": ["src/api/routers/redirect.py performance characteristics"],
        "note": "deferred -- no numeric target approved by this demonstration",
    })
    complete_stage(conn, execution_id, impact_stage)
    print("[6] Downstream impact analysis recorded, distinct from the clarification decision itself.")

    conn.execute("UPDATE orchestration_workflow_instance SET status='completed' WHERE id=?", (wf,))
    conn.commit()
    print(f"[7] Workflow {wf} -> completed (resumed from the correct suspended state, not restarted)")

    print("\nSCENARIO C (AMBIGUOUS) PASSED")
    print("NOTE: step [5]'s decision was a demonstration substitute for a real approval,")
    print("not evidence of real human governance -- see this script's module docstring.")
    conn.close()


if __name__ == "__main__":
    main()
