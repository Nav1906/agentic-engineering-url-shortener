# ADR-0005: Orchestration Model, Durable Execution, Agent Adapters, and Dynamic Replanning

## Status

**Accepted** (Revision 3). Approved by the human candidate at Human Gate 4,
2026-09-10. Revision 3 (2026-09-10) superseded
Revision 2 in response to a further Human Gate 4 review round that found:
(a) the adapter DAG ran task decomposition before architecture/design and
human architecture approval — inverted relative to the guide's own Final
Lifecycle; (b) "invoke `/speckit-tasks`" was written as if it were a
standalone shell command, which it is not; (c) an in-band exception raised
*after* a side effect (not just a stale lease) is equally uncertain and was
incorrectly treated as automatically safe to retry; (d) fencing the
execution-status database row does nothing to stop a still-running "zombie"
worker from continuing to write real files or produce other external
effects; (e) the reaper only ran on scheduler ticks, so a hang with no other
transitions in flight would never be detected; (f) postconditions and
promoted "success" were not actually tied to executed validators or
retained evidence. All six are addressed below. Revision 2's core
claim/lease/reconciliation model is retained and generalized, not discarded.

## Context

Same governing requirements as Revision 2 (FR-201–FR-206, FR-501–FR-503,
FR-606, Constitution Principle II). This revision additionally must respect
the guide's own authoritative lifecycle ordering (Section 2, "Final
Lifecycle," and Section 27, "Final Step-by-Step Execution Sequence"):
constitution → specify → clarify → **Human Requirements Approval** → plan
→ ADRs → **Human Architecture Approval** → checklist → tasks → analyze →
**Pre-Implementation Review** → implement → ... — which this project has
itself been following turn-by-turn throughout this conversation. Revision
2's DAG example instead followed the guide Section 7 "Primary Capability"
enumeration, which lists task decomposition before architecture/design —
those two guide passages conflict, and the authoritative one is the Final
Lifecycle, since it is the one this repository's own SpecKit skill
invocations have actually followed.

## Decision Drivers (Revision 2's drivers, plus)

- The adapter DAG must match the guide's actual authoritative lifecycle
  order, not a topical enumeration from an earlier guide section.
- "Invoking a SpecKit command" must describe a real, executable mechanism —
  there is no `speckit-tasks` binary on `PATH`; SpecKit skills exist only as
  Markdown instructions a Claude Code (or compatible) session reads and
  follows, invoked via that agent's own CLI/SDK.
- Reconciliation must cover *every* path by which an
  `externally_observable_uncertain` stage's true outcome becomes uncertain —
  exception, timeout, and stale lease alike — not just the stale-lease case.
- Fencing a database row is necessary but not sufficient: a still-running
  process can keep acting on the real filesystem/repository regardless of
  what any row says. The actual side effects themselves must be contained.
- The reaper must run on a wall-clock cadence, independent of whether any
  other stage transition happens to occur.
- "Succeeded" must mean an executable validator actually ran and passed
  against retained evidence — not merely that `execute()` returned without
  raising.

## Decision — Corrected Lifecycle Order

The adapter sequence is corrected to match the guide's Final Lifecycle,
inserting the two stages Revision 2 omitted (**Checklist**, **Analyze**) and
moving task decomposition to its correct position *after* architecture,
ADRs, and Human Architecture Approval — never before:

| # | Stage | Guide correspondence |
|---|---|---|
| 1 | Requirement Ingestion | — |
| 2 | Requirement Normalization / Ambiguity Detection | `/speckit-clarify`-equivalent |
| 3 | Human Clarification | Human Requirements Approval |
| 4 | Architecture and Design | `/speckit-plan` + ADR gate |
| 5 | **Human Architecture Approval** (new, explicit stage — was implicit in Rev. 2) | Human Architecture Approval |
| 6 | **Checklist** (new — was missing in Rev. 2) | `/speckit-checklist` |
| 7 | Task Decomposition | `/speckit-tasks` — **now correctly after architecture approval, not before** |
| 8 | **Analyze / Pre-Implementation Review** (new — was missing in Rev. 2) | `/speckit-analyze` + independent reviewer gate |
| 9 | Implementation | `/speckit-implement` |
| 10 | Testing | — |
| 11 | Documentation | — |
| 12 | Security and Risk Validation | — |
| 13 | Release-Readiness Determination | `/speckit-converge`-equivalent |
| 14 | Final Engineering Summary | — |

**Concrete DAG, corrected**:

```
[1 Requirement Ingestion]
        |
[2 Ambiguity Detection] --(ambiguous)--> [3 Human Clarification] --> back to [2]
        | (clear)
[4 Architecture/Design]
        |
[5 Human Architecture Approval]   <-- explicit human gate; nothing below is eligible until this clears
        |
  +-----+---------------------------+
  |                                 |
[6 Checklist]              [12 Security & Risk Validation: static checks]   <- independent, dispatched together
  |                                 |
  +-----+---------------------------+
        | (JOIN)
[7 Task Decomposition]
        |
[8 Analyze / Pre-Implementation Review]
        |
[9 Implementation]
        |
  +-----+---------------------------+
  |                                 |
[10 Testing]                 [11 Documentation]        <- independent, dispatched together
  |                                 |
  +-----+---------------------------+
        | (JOIN)
[13 Release-Readiness Determination]
        |
[14 Final Engineering Summary]
```

Parallelism is applied **only** to genuinely dependency-safe pairs (checklist
∥ security-static-checks; testing ∥ documentation) — never across a human
approval gate, and never between stages that read/write the same artifact
(task decomposition and architecture/design are sequential, not parallel,
precisely because tasks are derived *from* the approved design).

## Decision — Real Claude Invocation (Corrected)

A SpecKit skill (e.g., `/speckit-tasks`) is Markdown instructions under
`.claude/skills/`, resolved and followed by a Claude Code session — it is
**not** a standalone executable. The Task Decomposition, Architecture/
Design, and any other adapter whose "tool" is a SpecKit skill invokes it by
running the **Claude Code CLI itself, non-interactively** (headless/print
mode), from the repository root, with a prompt naming the skill.

**Corrected by spike evidence (Human Gate 4, 2026-09-10;
`docs/governance/gate-4-spike-results-2026-09-10.md`, Spike 1a)**: the
illustrative `--cwd` flag used in an earlier draft of this ADR does not
exist — verified directly against `claude --help`. The real mechanism,
confirmed by an actual successful invocation: run the process with its
**working directory set to the target path** (there is no directory flag;
Claude Code uses the process's actual `cwd`), e.g. `subprocess.run(["claude",
"-p", "<prompt>", "--output-format", "json", "--permission-mode",
"bypassPermissions"], cwd=<workspace-path>)`. `--permission-mode
bypassPermissions` was required in the spike for the CLI to perform a file
write non-interactively without prompting — an adapter running unattended
needs an equivalent explicit permission mode, not silence-implies-approval.
This was run for real: exit 0, a real file was written with the exact
requested content, `total_cost_usd` and `duration_api_ms` were retained as
evidence. The orchestration engine does not reimplement the skill's logic
and does not shell out to a nonexistent binary; it shells out to the real,
now-verified `claude` CLI invocation above.

## Decision — Durable Execution and Recovery (generalizing Revision 2)

Schema unchanged from Revision 2 (`orchestration_stage_execution`,
`worker_id`, atomic CAS claiming — see data-model.md), with one correction:

**Reconciliation now applies to every path to uncertainty, not just stale
leases**: for an `externally_observable_uncertain` stage, a retry is safe
**only** after `check_effect()` returns `not_completed` — this check now
runs after **any** non-success outcome: an exception raised during
`execute()`, a timeout, **or** a stale/expired lease. Revision 2's claim that
an in-band exception was automatically safe to retry (because "the worker
that raised the exception is still the one reporting the outcome") is
**withdrawn** — a worker can perform a real side effect and *then* raise
(e.g., a file write succeeds, then a subsequent step throws), and an
exception alone reveals nothing about which side of that boundary the
failure occurred on. Only `idempotent`-class stages skip reconciliation on
exception/timeout, because their effect is safe regardless of exactly when
it occurred.

**Reaper cadence, corrected**: the reaper now runs on **both** triggers —
after any stage transition (as in Revision 2) **and** on a fixed wall-clock
interval (proposed: every **10 seconds**, `PVT-008`, requires your
approval) regardless of whether any transition has occurred — closing the
gap where a single hung stage with nothing else happening would never be
re-checked.

## Decision — Isolated Execution Workspaces and Controller-Only Promotion (new)

**This is the actual fix for "fencing the database row doesn't stop a
zombie worker's real effects,"** and is deliberately the simplest mechanism
that closes the gap — reusing `git worktree` (already part of the toolchain,
not new infrastructure) rather than inventing a bespoke sandbox subsystem:

- Every stage execution that performs file-producing work (any
  `externally_observable_uncertain` adapter — Task Decomposition,
  Architecture/Design, Implementation, Documentation, Final Engineering
  Summary) is launched with its **own isolated workspace**: a dedicated
  `git worktree` at `agent-workspaces/<execution_id>/`, checked out from the
  `artifact_revision` the stage claim recorded. The subprocess doing the
  actual work (Claude Code, `pytest`, etc.) reads and writes **only** inside
  that worktree — never the main repository working tree.
- The subprocess's own completion (success or failure) is **not** itself
  authoritative. The **controller** (this orchestration engine's own
  trusted, unsandboxed process — never the agent subprocess) is the **only**
  code path permitted to promote a worktree's output into the real
  repository (`git add` / `git commit` in the main tree, or an equivalent
  file copy for non-git artifacts), and it does so **only if all of the
  following hold**, checked atomically at promotion time:
  1. `execution_id` is still the currently-claimed, non-stale execution for
     its stage (the same fencing check from Revision 2, now gating a real
     action instead of only a database write).
  2. The stage's postcondition validator (below) passes when run against the
     worktree's actual content.
  3. `artifact_revision` still matches the workflow's current revision (no
     invalidating replan occurred while the worktree was being built).
- If a stale/zombie worker keeps running after being declared stale and
  eventually finishes, its worktree's output is simply **never promoted** —
  the controller's promotion gate rejects it (fails condition 1), and the
  abandoned worktree is later garbage-collected. The zombie can waste
  compute, but it cannot alter the real repository, the real database, or
  any protected controller asset (§ ADR-0006 defines that boundary in full;
  this mechanism is the one both ADRs share, not duplicated between them).

## Decision — Executable Postconditions and Retained Evidence (new)

A stage's `postconditions` field (data-model.md) is no longer documentation
only. Each stage's adapter supplies a **postcondition validator** — a real,
runnable check (a function, or a subprocess like `pytest`/`mypy`/a hash
comparison) — and a stage is marked `succeeded` **only after** that
validator is run by the controller against the worktree (or, for non-file
stages, against the relevant persisted state) and returns true. The
controller records, in `orchestration_stage_execution.outcome_detail`:
`validator_command`, `validator_exit_code`, `validator_output_hash` (a
SHA-256 of the validator's actual output), and `artifact_hashes` (a
SHA-256 per artifact file the stage claims to have produced). A clean `git
status` or an unchecked task-list box is explicitly **not** accepted as
evidence of success on its own — only a validator's actual retained result
is.

## Decision — Agent Adapters (table retained from Revision 2, corrected
ordering and invocation mechanism per above)

| # | Adapter | Tool invoked (corrected) | `effect_class` |
|---|---|---|---|
| 1 | Requirement Ingestion | none (pure capture) | `idempotent` |
| 2 | Ambiguity Detection | the requirement-quality check already specified in spec.md FR-601 | `idempotent` |
| 3 | Human Clarification | human-interaction gate (no tool) | `idempotent` |
| 4 | Architecture/Design | `claude` CLI, headless, prompted with `/speckit-plan` + the ADR gate | `externally_observable_uncertain` |
| *(5 omitted — Human Architecture Approval is a gate, not an adapter; its mechanism is ADR-0006, not a tool invocation)* | | | |
| 6 | Checklist | `claude` CLI, headless, prompted with `/speckit-checklist` | `externally_observable_uncertain` |
| 7 | Task Decomposition | `claude` CLI, headless, prompted with `/speckit-tasks` — **now after stage 5, not before stage 4** | `externally_observable_uncertain` |
| 8 | Analyze / Pre-Implementation Review | `claude` CLI, headless, prompted with `/speckit-analyze` + the independent-reviewer prompt | `idempotent` (read-only per the guide's own rule for `/speckit-analyze`) |
| 9 | Implementation | Claude Code, sandboxed subprocess (ADR-0006), operating inside its isolated worktree | `externally_observable_uncertain` — `check_effect()` probes the worktree's git history + the specific task's completion marker |
| 10 | Testing | `pytest`, sandboxed subprocess (ADR-0006), same worktree | `idempotent` |
| 11 | Documentation | sandboxed subprocess, same worktree | `externally_observable_uncertain` |
| 12 | Security and Risk Validation | policy-manifest evaluator + dependency/secret-scan subprocess | `idempotent` |
| 13 | Release-Readiness Determination | aggregation + policy check | `idempotent` |
| 14 | Final Engineering Summary | template-driven aggregation | `externally_observable_uncertain` |

Unchanged from Revision 2: every adapter either invokes an installed
SpecKit command, is a human-wait, or executes/validates real work — none
re-derive or override a SpecKit artifact's content; a detected gap routes
back upstream via replanning, never an inline decision.

## Decision — Dynamic Replanning (unchanged mechanism)

Unchanged from Revision 2, now also invalidating any in-progress worktree
whose `artifact_revision` no longer matches — an invalidated worktree is
simply never promoted (same gate as above), then discarded.

## Rationale

Every fix in this revision closes a gap between an assertion ("this stage
executes real work," "a stale worker can't cause harm," "the lifecycle
order is correct") and an actual mechanism that makes the assertion true.
None of the six findings required new infrastructure beyond what the
toolchain already has (`git worktree`, the `claude` CLI, a wall-clock
timer) — consistent with keeping this a bounded correction, not a redesign.

## Consequences

- **Positive**: a zombie worker's real side effects are contained to a
  disposable worktree; "succeeded" now means a validator actually ran; the
  lifecycle order matches what a reviewer can literally observe this
  project having followed.
- **Negative**: worktree lifecycle management (creation, promotion,
  garbage-collection) is real additional implementation surface — disclosed
  as necessary work, not optional polish.
- **Operational**: `agent-workspaces/` (gitignored) holds transient
  worktrees; the reaper's periodic sweep is one more scheduled routine in
  the same process.
- **Testing**: a test can now assert the exact property Human Gate 4 asked
  for — spawn a stage, let it write files in its worktree, declare it
  stale mid-write, and assert those files never reach the main tree.
- **Governance**: promotion decisions are themselves audit events (actor
  `system`, action `artifact_promoted` / `artifact_promotion_rejected`).

## Risks and Mitigations

- **Risk**: worktree disk usage grows with abandoned executions.
  **Mitigation**: garbage-collection of worktrees whose execution is
  `abandoned`/`failed` and older than a short retention window — an
  implementation detail, not a new architectural decision.
- **Risk**: the exact `claude` CLI invocation syntax/flags may differ from
  what's illustrated here. **Mitigation**: explicitly left open as an
  implementation detail, not asserted as fixed syntax in this ADR.

## Reversibility

**Low** for the core graph/execution-identity model (unchanged from
Revision 2). **Moderate** for the worktree-isolation addition — it is
additive and could be removed in a lower-rigor future revision, but doing
so would reopen the exact gap this revision closes.

## Traceability

- Requirements: FR-201–FR-206, FR-311, FR-501–FR-503, FR-606, Constitution
  Principle II, Principle XI.
- Specification sections: "Primary Capability: Agentic SDLC Orchestration."
- Plan sections: plan.md §3.
- Prior review: Human Gate 4 findings, Rounds 1–2 (2026-09-10), recorded in
  `docs/governance/gate-4-review-2026-09-10.md`.
- Expected tasks: orchestration-domain, dependency-graph, agent-workspace,
  workflow-state-machine, dynamic-replanning task groups.

## Validation

**Spike-verified (Human Gate 4, 2026-09-10;
`docs/governance/gate-4-spike-results-2026-09-10.md`, Spike 2 — real code,
real git repo, real SQLite, a real `SIGKILL`'d subprocess; PASS on all
sub-scenarios)**: (b) exception-after-effect reconciliation — confirmed the
controller detects a completed effect after a simulated post-effect
exception and promotes without a blind retry; (c, partial) worktree/
promotion containment — confirmed via the git-commit-and-DB-fencing
mechanism that a killed worker's real side effect is promoted exactly once,
and that its simulated late completion write is fenced (0 rows affected);
also newly confirmed, beyond what was originally planned: a
git-promotion-succeeds-but-DB-record-doesn't crash window is correctly
reconciled from git history on "restart," without a duplicate promotion.
**This is a logic-level simulation** (single process, no real Claude
subprocess spawned inside the worktree, no real OS sandbox involved) — it
establishes the protocol is sound, not that a full implementation is bug-
free.

**Still planned, not yet executed** (genuinely not run this session): (a)
the Revision 2 broader concurrency/replanning tests; (d) a periodic-reaper
test with zero other transitions occurring, asserting the wall-clock sweep
still detects a stale lease — **not covered by the spike**, still open; (e)
a postcondition-validator test asserting a stage cannot reach `succeeded`
without its validator actually running — the spike's git-log-grep check is
a simple instance of this idea but not a full test of the
`outcome_detail`/artifact-hash schema. Per instruction, none of this is
treated as resolved merely because this ADR describes it.
