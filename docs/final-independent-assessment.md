# Final Independent Assessment (Guide Section 23)

**Method**: run by a genuinely fresh Claude Code agent with no context from
the implementation session — briefed only with the guide's Section 23
prompt, this repository, and instructions to independently execute
(not just read) tests, linters, the OpenAPI validator, all three
demo scripts, and a live server session, then score and report candidly.
It was explicitly instructed not to modify files, not to generate
implementation code, and not to defend prior work.
**Run**: 2026-09-11, immediately after the `/speckit-converge` pass
recorded in [convergence-report.md](convergence-report.md).
**Verdict**: **BORDERLINE** (the agent's own words: "leaning PASS on
engineering substance, held to BORDERLINE by scope-narrowing that
materially changes what 'orchestration' means in this submission, plus
several small but real documentation-integrity slips"). **Mandatory
Blocking Gaps: none** — explicitly stated by the assessment itself.

## Disposition of findings (applied after this report, per instruction: fix
only mandatory blockers / factual errors / broken tests / security
defects; record everything else as backlog)

| Finding | Category | Action taken |
|---|---|---|
| `docs/traceability-matrix.md` cited a stale "184-test passing run" (actual: 241 at the time) | Factual error | **Fixed** — corrected to the current count, and the file's own header now discloses that `convergence-report.md`'s earlier claim of having already re-verified it was itself inaccurate |
| `docs/convergence-report.md` claimed the traceability matrix was "already current" without actually re-verifying it | Factual error | **Fixed** — claim corrected in place |
| `docs/reviewer-navigation-guide.md` §3 still said "Expected: `184 passed`" / "42 source files" | Factual error (missed by the convergence pass's own grep, which only searched for "237") | **Fixed** — updated to 241 (see below for why the final count is now 242) |
| `specs/.../checklists/requirements.md`'s "14/14" framing, repeated in `convergence-report.md`, undercounts the file's real 16-item scope (2 items are explicitly `[~]` partial) | Factual error (favorable framing) | **Fixed** — `convergence-report.md` now says "14/16, 2 explicitly partial" |
| `src/api/routers/approvals.py`'s module docstring still claimed "no credential-provisioning path is wired (T100/T101 blocked)" | Factual error (stale, contradicted by the file's own T100–T103 behavior) | **Fixed** — docstring corrected |
| `live_scheduler.py::_drive_workflow`'s already-checked guard did not scope by `artifact_revision`, so a workflow with any prior policy evaluation would never re-run mandatory checks after a (currently theoretical, single-revision-scope) revision bump | Correctness gap, latent | **Fixed** — guard now scoped to `(workflow_instance_id, artifact_revision)` |
| **Real, reproduced concurrency defect**: the assessment flagged the same guard's SELECT-then-insert as "a real TOCTOU shape" and reported (while suspecting its own environment) observing 6 `policy_evaluation` rows instead of 3 for one workflow. **A new regression test added to confirm or refute this (`tests/orchestration/test_no_duplicate_policy_evaluations_under_concurrent_ticks`, 8 real concurrent threads) failed intermittently on first run** — confirming this was a genuine, reproducible race, not an environment artifact as the assessment itself had speculated. | **Confirmed defect** | **Fixed**: added a `UNIQUE(workflow_instance_id, policy_id, artifact_revision)` constraint to `policy_evaluation` (`src/persistence/schema.py`) and made `evaluate_policy` race-safe (`INSERT OR IGNORE` + fallback lookup of the winning row's id, `src/policy/evaluator.py`). Re-ran the new regression test 8 consecutive times post-fix — 0 failures. Full suite, mypy, ruff all re-verified green afterward. |
| Compensation module (`src/orchestration/compensation.py`) is a thin classifier, not an executor of real compensating actions | Architecture concern, non-mandatory (no FR requires an executed compensating action, only correct classification) | **Logged as backlog** — see `docs/risk-register.md` |
| Replanning/invalidation cascade only ever exercised white-box (no live HTTP path bumps `artifact_revision`, hardcoded to `"v1"`) | Architecture concern, disclosed scope limit | **Logged as backlog** |
| `tests/e2e/test_ambiguous.py` / `test_brownfield.py` are thin subprocess+stdout wrappers | Testing concern, non-mandatory | **Logged as backlog** |
| Git history is one single-day session with several large commits, in tension with Constitution Principle X's "small and logically coherent" | Documentation/process concern | **Logged as backlog** — disclosed here rather than left for a reviewer to notice unassisted, per the assessment's own remediation recommendation |
| Parallel dispatch (`dispatch_ready_stages_parallel`) not exercised through the live HTTP `auto_execute` path (only via direct module test) | Testing concern, non-mandatory | **Logged as backlog** |

**Not fixed, and correctly so**: nothing in the "Mandatory Blocking Gaps"
section, because that section was empty. No accepted architecture was
reopened for subjective improvement, per instruction — the compensation
module, the single-revision replanning scope, and the thin e2e wrappers
are real, disclosed, non-mandatory limitations, not defects.

## Post-fix re-verification

`uv run pytest tests/` → **242 passed** (241 + 1 new regression test for
the concurrency fix). `uv run mypy src/` → success, 47 files. `uv run ruff
check src/ tests/ scripts/` → all checks passed. The new
`test_no_duplicate_policy_evaluations_under_concurrent_ticks` test was
additionally re-run 8 consecutive times standalone with 0 failures
(matching the number of times it was run to originally reproduce the
defect), to confirm the fix, not just a single lucky pass.

## Full assessment report (verbatim)

<details>
<summary>Click to expand the complete independent assessment</summary>

# Overall Verdict

**BORDERLINE** (leaning PASS on engineering substance, held to BORDERLINE by scope-narrowing that materially changes what "orchestration" means in this submission, plus several small but real documentation-integrity slips discovered during independent verification)

# Executive Rationale

This submission is unusually honest and unusually well-verified relative to what I could independently confirm. I ran the full test suite, mypy, ruff, the OpenAPI validator, all three demo scripts, and a live server session (redirect, analytics, idempotency, SSRF/scheme rejection, a real `auto_execute` workflow driven purely by the background scheduler with real conditional branching, and the full approval-credential pipeline including `bootstrap_credentials.py`/`approve.py` against a live server). Every quantitative claim I checked against reality — 241 tests (and its exact per-category breakdown: 32/38/2/66/46/5/24), mypy clean on 47 files, ruff clean, OpenAPI valid, 117 checklist items split 29/16/30/21/21 across five files with 104 checked — matched the repository's own documents precisely. That level of correspondence between claim and observation is rare and is the strongest single piece of evidence for genuine engineering discipline here.

The orchestration engine itself (`src/orchestration/scheduler.py`, `branching.py`, `reaper.py`, `replanning.py`, `workspace.py`) is real: an explicit dependency-graph table, atomic compare-and-swap claiming, genuine `asyncio.gather`-based parallel dispatch with an overlap-proving test, lease-based stale-worker detection, effect reconciliation gated on `effect_class`, an invalidation cascade for material changes, and a background scheduler that live-drives a workflow through HTTP alone (I watched this happen against a live server). This is not a linear chain dressed up as orchestration.

The central caveat, which the repository itself discloses at length in ADR-0006 Revision 5, is that this orchestration engine never executes a real external agent. `src/orchestration/adapters/launcher.py` unconditionally raises `ExternalAgentLaunchBlocked` for every call, by design, after three earlier ADR-0006 revisions failed a real macOS `sandbox-exec` feasibility spike (confirmed `SIGABRT`, documented with an honest failure record rather than glossed over). Consequently, what the orchestration engine actually coordinates in this release is a **workflow state machine** whose "stages" (design, implementation, testing, etc.) are symbolic status transitions — `_execute_stage_safely` in `live_scheduler.py` does nothing for any stage name except `classify`, which writes a hardcoded `{"decision": "proceed"}`. The three scenario demonstrations "re-enact" work that was actually done by the human-directed Claude Code session separately (this is stated explicitly in `scripts/demo_greenfield.py`'s docstring), not evidence of agents being orchestrated to do SDLC work autonomously. This is honestly disclosed, not hidden — but it is a substantial scope reduction from what "governed, stateful, non-linear agentic software engineering orchestration system" suggests on first read, and a reviewer should not come away thinking real coding agents were coordinated through dependency graphs, retried, and rolled back. They were not; a state machine that *could* coordinate them was built, tested, and then deliberately fenced off from ever doing so, for good, disclosed safety reasons.

I found several small, real integrity issues that a "fresh reviewer" is specifically supposed to catch: a stale docstring in `src/api/routers/approvals.py` that still claims no credential path is wired (contradicted by T100–T103, implemented two commits later and never updated); `docs/traceability-matrix.md` still says "part of the 184-test passing run" despite the convergence report explicitly asserting this document is "unchanged this pass — already current" (the real count is 241); and the built-in `requirements.md` checklist's "14/14" claim quietly excludes two items marked `[~]` (partial) from its own denominator rather than counting them as 14/16. None of these are fabrications of evidence — they are exactly the kind of small staleness that a genuinely single-day, high-velocity build produces — but they are real, and the convergence report's claim that the traceability matrix was independently re-verified as "current" is not accurate.

Git history is one continuous, single-day session (12:58–21:13 on 2026-09-10), with some very large single commits (e.g., 63 files / 2,302 insertions in a 10-minute gap). This is disclosed nowhere as a limitation and is in tension with Constitution Principle X's "commits MUST be small and logically coherent" — though it is consistent with, and expected of, an AI-paced build rather than a fabricated history (no evidence of squashed/rewritten history, no gaps suggesting hidden work, and the diff sizes are plausible for AI-generated code at that pace).

# Scoring Matrix

| # | Dimension | Score | Evidence |
|---|---|---|---|
| 1 | Requirement understanding | 4 | `specs/001-governed-url-shortener/spec.md` — 51 FRs (FR-101–606) traced in `docs/traceability-matrix.md`; constitution correctly identifies the orchestration system, not the shortener, as the evaluated subject (`.specify/memory/constitution.md` "Project Context"). |
| 2 | Ambiguity management | 4 | `scripts/demo_ambiguous.py` executed live: correctly detects `'faster'` as `vague_unmeasurable_adjective`, suspends to `awaiting_approval`, does not auto-resolve; explicitly labels its own clarification step "a demonstration substitute for a real approval." |
| 3 | Task decomposition | 4 | `specs/001-governed-url-shortener/tasks.md` — 106 tasks, all marked complete (`grep -c '\[X\]'` = 106, `\[ \]` = 0), grouped into 43 groups per `final-engineering-summary.md` §2. |
| 4 | Brownfield reasoning | 4 | `scripts/demo_brownfield.py` executed live: 7-dimension impact analysis recorded before any code change; implementation stage structurally blocked until impact-analysis stage succeeds; real, scoped regression run (`uv run pytest tests/security/test_health_exempt_from_rate_limit.py tests/unit/test_rate_limit.py`) observed passing live. |
| 5 | Orchestration effectiveness | 3 | Real dependency-graph engine (`src/orchestration/scheduler.py`, `models.py`) — but the engine's own stage-execution path (`live_scheduler.py::_execute_stage_safely`) does no real work beyond one hardcoded decision; ADR-0006 Rev.5 confirms no external agent is ever coordinated. Effective as a workflow engine, not as agent orchestration in the sense the guide implies. |
| 6 | Stateful and non-linear design | 5 | `orchestration_workflow_stage`/`orchestration_stage_dependency` tables are an explicit persisted graph; live-verified conditional branching (`branching.py`) produced `branch_selected`/`branch_not_selected` audit events in my own server session. |
| 7 | Parallel execution and synchronization | 4 | `scheduler.py::dispatch_ready_stages_parallel` uses `asyncio.gather`; `tests/orchestration/test_parallel_sync.py` asserts genuine window overlap (`a_start < b_end and b_start < a_end`), not sequential timing. Not exercised through the live HTTP path in my testing (only via direct module test), slightly narrower than the branching/scheduling live-verification. |
| 8 | Controlled autonomy | 4 | `src/orchestration/adapters/launcher.py` fail-closed by construction; live-verified: `launch_external_agent` raises unconditionally and audits every call; grep confirms no `subprocess`/`Popen`/`claude` invocation outside an explicit allowlist (git worktree mgmt, `uv run pytest`, `uvicorn`). |
| 9 | Human approval enforcement | 5 | Live-verified against a running server: unauthenticated → 401, wrong-role (bob on `requirements_approval`) → 403 `wrong_role_for_gate`, correct role (alice) → 200, `scripts/approve.py` end-to-end via real bootstrapped credentials → 200; agent-identity rejection tested in `tests/security/test_t103_security_verification.py::test_agent_identity_rejected`. |
| 10 | Retry, fallback, timeout, and safe-stop | 4 | `retry_policy.py`, `scheduler.py::issue_retry_or_exhaust`/`apply_fallback_or_safe_stop` — real bounded retry (`MAX_STAGE_ATTEMPTS`), tested backoff timing (`test_backoff_timing.py`), per-subprocess timeouts (`test_subprocess_timeouts.py`); safe-stop resumable only via explicit call, verified in `test_safe_stop_resume.py`. |
| 11 | Rollback or compensation | 3 | `src/orchestration/compensation.py::dispatch` is a real, constitutionally-compliant classifier (infeasible rollback structurally cannot return `rolled_back`), but the module is a 27-line two-branch function with correspondingly thin tests (`tests/orchestration/test_rollback_compensation.py`, 2 assertions) — no actual compensating action is executed against any real effect. |
| 12 | Resume and recovery | 4 | `scheduler.py::recover_on_startup` forces `running`→`failed_transient` on restart, wired into `src/api/main.py` lifespan; `tests/persistence/test_restart_recovery.py` exercises this. |
| 13 | Dynamic replanning | 3 | `replanning.py::invalidate_downstream`/`invalidate_worktree` are real and correctly scoped (invalidates exactly the affected stages/approvals); but `_current_artifact_revision` in `approvals.py` is hardcoded to `"v1"` always, so the replanning cascade is only ever exercised white-box (direct module calls in tests), never through a real HTTP-triggered revision bump — disclosed as "single-revision demonstration scope" but a real limitation. |
| 14 | Decision lineage | 4 | `src/orchestration/lineage.py`, append-only `orchestration_decision_lineage`; live-verified via `get_lineage` returning `requirement_quality_check`/`synchronization_point` entries in demo runs. |
| 15 | Traceability | 3 | `docs/traceability-matrix.md` maps FR→task→code→test for 51 FRs — but the document itself still cites a stale "184-test passing run" though the convergence report claims it was independently re-verified as "already current" this pass (contradiction, see Unsupported Claims). |
| 16 | Architecture quality | 4 | Clean package separation (domain/orchestration/policy/api/persistence/observability) per ADR-0001, enforced (mypy/ruff clean); `promote_or_reject` in `workspace.py` is the sole content-copy path from isolated worktree to main tree, by construction. |
| 17 | Code quality | 4 | `uv run mypy src/` → success, 47 files; `uv run ruff check src/ tests/ scripts/` → all checks passed (independently re-run, not reused from claims). |
| 18 | Test-driven development | 3 | Plausible and partially evidenced (`final-engineering-summary.md` §17 cites two real regressions caught by running code: a `mark_ready`/`compute_ready_stages` ordering bug and a nested-pytest deadlock) but TDD's red-green-refactor sequence is not independently verifiable from git history alone (bulk commits bundle tests+implementation together). |
| 19 | Test depth | 4 | Sampled `test_parallel_sync.py`, `test_t103_security_verification.py`, `test_external_agent_shutdown.py`, `test_live_workflow_execution.py` — genuine behavioral assertions (concurrency overlap, structural source-tree scans, real HTTP polling with no direct scheduler calls), not `assert True`-style padding. `tests/e2e/test_ambiguous.py`/`test_brownfield.py` are comparatively thin subprocess+stdout-string wrappers. |
| 20 | Security | 4 | Live-verified: scheme allow-list rejects `javascript:`, private/loopback/link-local address rejection (127.0.0.1, 169.254.169.254) both return 400 with honest "no DNS-rebinding protection at resolution time" disclosure; `pip-audit` clean per docs (not independently re-run by me); credential tests (`test_t103_security_verification.py`) check raw-token absence from API responses, DB rows, and git tracking. |
| 21 | Reliability | 4 | Idempotency-key replay verified live (identical response body on retry); analytics "degraded_since_unclean_shutdown_at" observed live on my own server start (real behavior, not just a test). |
| 22 | Observability | 4 | `/metrics/reliability` returns `"demonstration_data":true` live, matching Constitution Principle IX's non-production-statistics rule; correlation via `workflow_instance_id` verified live in audit-events output. |
| 23 | Auditability | 5 | Live-verified: rejected approval attempts (`rejected_unauthenticated`, `rejected_wrong_role`) appear in `/workflows/{id}/audit-events` with FR citations in the `reason` field, within seconds of the actual HTTP calls. |
| 24 | Greenfield scenario | 4 | `uv run python3 scripts/demo_greenfield.py` executed by me, passed; script's own docstring discloses it "re-enacts" already-implemented work rather than performing new implementation. |
| 25 | Brownfield scenario | 4 | `uv run python3 scripts/demo_brownfield.py` executed by me, passed, including a real nested `pytest` regression run with real pass output captured. |
| 26 | Ambiguous-requirement scenario | 4 | `uv run python3 scripts/demo_ambiguous.py` executed by me, passed; correctly refuses to fabricate an approval through the real endpoint, stating this limitation in its own printed output. |
| 27 | Documentation | 4 | Extensive, cross-referenced, mostly accurate (`docs/final-engineering-summary.md`, `docs/threat-model.md`, `docs/risk-register.md`) — but not perfectly synchronized (see stale docstring and stale traceability-matrix count above). |
| 28 | GitHub evidence | 3 | 24 commits, well-labeled messages describing real engineering intent, but the entire history is one ~8h15m session on a single calendar day with several very large commits (e.g. `f3242aa`: 63 files/2,302 insertions), in tension with Principle X's "small and logically coherent" commit rule. |
| 29 | Defensibility of decisions | 5 | ADR-0006's full revision history (1→5) is the standout artifact: documents a real failed feasibility spike (macOS `sandbox-exec` SIGABRT, five profile variants tried), an explicitly rejected Revision 3, and a narrower Revision 5 that states plainly what it does *not* solve. This is genuine engineering ownership, not hand-waving. |
| 30 | Engineering judgment | 5 | The decision to scope-exclude external-agent execution entirely rather than ship an unverified sandboxing claim, and to disclose that choice's exact boundary (`docs/threat-model.md`'s "Explicitly Out of Scope" section), is defensible, disclosed, and consistent with Constitution Principle VIII's prohibition on invalid rollback/safety claims. |

# Mandatory Blocking Gaps

None. Every mandatory FR I could check traces to real, tested, and (where I could verify live) actually-working code. The scope reduction around external-agent execution is a disclosed, governance-approved (Human Gate 4, 2026-09-11) design decision, not a silently-missing mandatory capability — no FR in `spec.md` required external-agent subprocess execution specifically, and ADR-0006 Revision 5's Constitution Check table honestly marks Principle V as "PASS, scope-limited" rather than claiming a broader PASS.

# Evidence Strengths

- **Numerical claims matched reality exactly on every check I ran**: 241 tests (32/38/2/66/46/5/24 per-category), mypy clean on 47 files, ruff clean, OpenAPI valid, 117 checklist items (29+16+30+21+21), 104 checked. This is unusual and meaningfully raises confidence in everything else in the documents.
- **Live server verification succeeded across the full governance surface**: create/redirect/analytics/idempotency/SSRF-rejection, a real `auto_execute:true` workflow driven entirely by the background scheduler with real conditional branching (`branch_selected`/`branch_not_selected` audit events observed), and the complete approval pipeline (401 unauthenticated → 403 wrong-role → 200 correct-role, `scripts/approve.py` working end-to-end against bootstrapped credentials).
- **ADR-0006's revision history** is the single strongest piece of evidence of genuine engineering ownership in the repository: a real platform-level failure was hit, honestly reported (not glossed over), and the team pivoted to a narrower, defensible, and *actually implemented* scope rather than claiming an unverified mitigation worked.
- **Structural, not just behavioral, security tests**: `test_external_agent_shutdown.py` and `test_t103_security_verification.py` scan the actual source tree for subprocess/Popen/`claude` invocations rather than merely asserting behavior of one code path — I independently reproduced the same grep and got the same allowlisted set of three sites.
- **Genuine concurrency test**, not simulated: `test_parallel_sync.py` proves overlap via wall-clock windows that are impossible under sequential execution.

# Unsupported Claims

- `docs/convergence-report.md` item 1 states the traceability matrix is "unchanged this pass — already current," but `docs/traceability-matrix.md` line 3 still references "the 184-test passing run," a figure superseded by the 241 total established earlier in the same convergence pass. The claim of independent re-verification for that specific document is not accurate.
- `src/api/routers/approvals.py`'s module docstring ("since no credential-provisioning path is wired (T100/T101 blocked), no real bearer token will ever resolve to an identity in a genuine deployment") is stale — contradicted by the same file's own behavior and by T100–T103, implemented in a later commit (`3cba7cf`) and verified live by me. Not a functional bug (the code works correctly), but a documentation claim that no longer matches the code it's attached to.
- `specs/001-governed-url-shortener/checklists/requirements.md`'s "14/14" framing (repeated in the convergence report) excludes two `[~]` (partial) items from its own denominator; the file itself actually contains 16 checklist items, 14 fully checked and 2 explicitly partial. Not fabricated (the partial items are visibly disclosed in the file), but the "14/14" headline is a more favorable framing than "14/16" would be.
- I observed, in one ad hoc live test before I isolated the database path correctly, 6 `policy_evaluation` rows for a single workflow instead of the expected 3 (matching `tests/e2e/test_live_workflow_execution.py::test_workflow_progresses_automatically_to_completion`'s explicit assertion of `len(policy_evals.json()) == 3`). A clean re-test with an isolated database produced exactly 3, matching the test suite. I could not conclusively reproduce the anomaly and attribute it most likely to my own initial environment misconfiguration (pointing at a pre-existing, non-empty `data/app.db` left over from a prior session) rather than a genuine duplicate-write defect in `live_scheduler.py::_drive_workflow`'s `already_checked` guard — but I flag it as unresolved rather than dismiss it, since the guard as written (`SELECT ... LIMIT 1` then three separate INSERTs) is a real TOCTOU shape.

# Architecture Concerns

- `src/orchestration/compensation.py` is architecturally correct but minimal — it is a pure classifier (`operation_class` string → outcome), not a compensating-action executor. There is no code path in this repository that actually performs a compensating write to reverse an externally-observed effect (e.g., decrementing an analytics counter that was already incremented). The distinction the constitution demands (rollback vs. compensation, never claiming the former where infeasible) is honored, but "compensation" here means "correctly labels an outcome as compensated," not "executes a compensating action."
- The replanning/invalidation cascade (`replanning.py`) is real but is never exercised through a live HTTP path — `_current_artifact_revision` in `approvals.py` is hardcoded to `"v1"`, so no request through the running API ever produces a revision bump that would trigger `invalidate_downstream` organically. All replanning evidence is white-box (tests calling the module directly).

# Orchestration Concerns

- The most important scope caveat for any reviewer: the orchestration engine, as shipped, never executes real agentic work. `live_scheduler.py::_execute_stage_safely` is a no-op for every stage name except `classify` (which writes one hardcoded decision). The three scenario scripts explicitly acknowledge they "re-enact" requirements already implemented by the human-directed development session, using the engine's primitives, rather than demonstrating the engine driving real agent-produced work end-to-end. This is honestly disclosed (not a fabrication under Principle X/XI), but a reader should not conclude that this system coordinates AI coding agents through a dependency graph with retries and rollback — it coordinates a state machine that is architected to be able to, with the actual agent-execution wire deliberately left unconnected for a disclosed, defensible safety reason.
- Genuine parallel dispatch (`dispatch_ready_stages_parallel`) is proven only via direct module test (`test_parallel_sync.py`), not exercised through the live HTTP `auto_execute` path in either my testing or, as far as I could find, the shipped e2e suite — the live demo pipeline (`intake → classify → {proceed_path | hold_path}`) is a branching DAG but not a fan-out/fan-in one.

# Governance Concerns

- None beyond what's already disclosed and accepted at Human Gate 4. The approval-enforcement mechanics I tested live (401/403/200 paths, agent-identity rejection, wrong-role rejection) all behaved exactly as documented.

# Testing Concerns

- `tests/e2e/test_ambiguous.py` and `tests/e2e/test_brownfield.py` are thin: each is a `subprocess.run` of the corresponding demo script plus a single stdout-string assertion. They add value only insofar as the demo scripts themselves contain real internal `assert` statements (they do), but they do not independently verify database state the way `test_live_workflow_execution.py` does via HTTP polling.
- `tests/orchestration/test_rollback_compensation.py` is two one-line assertions against a pure function — correctly scoped to what the module actually does, but it should not be read as deep coverage of a "rollback or compensation" capability in the sense of exercising real state reversal.

# Security and Reliability Concerns

- All disclosed and accepted, not hidden: same-OS-user compromise of `local-secrets/approval_tokens.raw.json` (Unix permissions don't stop a co-resident process running as the same user), operator macOS-account compromise, and no DNS-rebinding protection at redirect-resolution time (only at creation time — I confirmed the creation-time rejection works for `127.0.0.1` and `169.254.169.254`, but did not attempt to construct a DNS-rebinding bypass, which is out of scope for read-only review anyway).
- Audit log is append-only by code convention only, not a DB-level constraint (ADR-0008, checklist CHK079/CHK034, risk register R-007) — disclosed, not blocking, but worth flagging since it weakens the tamper-evidence of the audit trail this whole system's evidentiary claims lean on.

# Documentation and Traceability Concerns

- See Unsupported Claims above (stale `traceability-matrix.md` test count contradicting the convergence report's own "already current" claim; stale `approvals.py` docstring).
- Otherwise documentation is unusually extensive and cross-referenced (13 convergence outputs, a dedicated threat model scoped explicitly to one boundary, a risk register that consolidates rather than duplicates). The self-critical tone throughout (e.g., "this does NOT claim X," "disclosed, not glossed over") is consistent and appears genuinely applied, not just present in a few flagship documents.

# Git History Assessment

24 commits, all timestamped 2026-09-10 12:58:11 through 2026-09-10 21:13:51 — a single ~8h15m session, not the "2–3 days" framing the constitution and guide use for scope-sizing (that framing is about *effort budget*, not a literal calendar claim, so this is not itself a misrepresentation, but it is worth stating plainly for the record). Commit messages are consistently well-formed and describe real engineering intent (`feat(orchestration): reaper, reconciliation, retry-safety, fallback, safe-stop`, etc.), and diff sizes are plausible for AI-paced development — no evidence of fabricated or squashed history (`git log --all` shows a single linear branch, `confidential/` and `local-secrets/` are absent from `git ls-files` and from `git log --all -- confidential/ local-secrets/` with empty output, confirming they were never tracked, not merely deleted later). Several commits are very large for a single unit (`a0bf779`: 32 files/5,128 insertions at project init — expected; `f3242aa`: 63 files/2,302 insertions in a 10-minute gap — a full working URL shortener plus orchestration core in one commit). This is in tension with Constitution Principle X's "commits MUST be small and logically coherent," though it is more consistent with "one coherent task-group boundary per commit" (the constitution's own autonomous-execution bound) than with traditional small human commits — a defensible reading, but the tension is real and undisclosed anywhere in the repository's own documents.

# Likely Reviewer Questions

1. "Does the orchestration engine ever actually run a coding agent?" — No. Confirmed by reading `launcher.py`, running the grep tests myself, and reading ADR-0006 Revision 5's Human Gate 4 decision verbatim. Be prepared to explain this distinction plainly rather than let a reviewer infer more than what's built.
2. "Why does `docs/traceability-matrix.md` still say 184 tests when the suite has 241?" — Genuine staleness; the convergence pass's claim that this document is "already current" is not accurate for that line.
3. "Is the macOS `sandbox-exec` failure a workaround or a real platform finding?" — Real; I did not re-run the spike myself (it required `sudo`/account creation, out of scope for read-only review) but the failure mode described (custom profile `SIGABRT` on `(allow process-exec)`) is consistent with known Seatbelt/`sandbox-exec` deprecation behavior on recent macOS and is documented with specific reproducible commands across five profile variants.
4. "Why does the demo greenfield script call itself a 're-enactment' rather than a real implementation?" — Because it is one; the actual `workflow_evidence.py` endpoints were implemented via the normal git-commit development process, and the script replays that same requirement through the orchestration engine's primitives for inspectability, not as new implementation work.
5. "Is the compensation mechanism more than a label?" — No, and that should be acknowledged as a real, if minor, engineering thinness rather than defended as complete.

# Prioritized Remediation Plan

1. **Correct `docs/traceability-matrix.md`'s stale "184-test" reference** to 241, and correct the convergence report's claim that this document was independently re-verified as current this pass — either re-verify it for real or state plainly that it wasn't.
2. **Update or remove the stale docstring in `src/api/routers/approvals.py`** that claims no credential-provisioning path is wired — it directly contradicts the file's own T100–T103 behavior.
3. **Reframe the `requirements.md` checklist's "14/14"** as "14/16, 2 explicitly partial" wherever it's cited externally (convergence report, final engineering summary), since the underlying file already discloses the 2 partial items — the summary framing should match.
4. **Disclose the single-day, large-bulk-commit nature of the git history explicitly** in one of the engineering-summary documents, with a rationale (task-group-boundary commits per the constitution's own autonomous-execution rule) rather than leaving a reviewer to notice the tension with Principle X unassisted.
5. **If a future revision reintroduces real agent execution** (which the repository itself flags as its own natural next step, gated behind a new ADR/Human Gate per R-003), the compensation module and the replanning cascade should be exercised through a live HTTP path, not only white-box — this would close the two thinnest spots in an otherwise solid orchestration implementation.
6. **Investigate the `_drive_workflow` `already_checked`-then-multi-INSERT pattern in `live_scheduler.py`** for a possible TOCTOU duplicate-write path, even though I could not reproduce it under a controlled re-test — the shape of the guard (a SELECT followed by three separate, non-transactionally-grouped INSERTs) is worth a defensive rewrite (e.g., a unique constraint on `(workflow_instance_id, policy_id, artifact_revision)`) regardless of whether my one anomalous observation was a real bug or an environment artifact.

</details>
