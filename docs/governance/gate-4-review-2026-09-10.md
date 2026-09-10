# Human Gate 4 Review Record — 2026-09-10

**Status**: Human Gate 4 **partially closed** (2026-09-10) — 9 of 10 ADRs
Accepted ("accept all"); **ADR-0006 remains open**, Rejected, pending the
Option A spike and its own follow-up decision. This file persists the
decision inventory and unresolved issues per the guide's ADR-gate
requirement ("At the end provide... 1. ADR inventory 2. Decisions requiring human approval
3. Decisions safely deferrable 4. Conflicts with the current plan 5. Missing
information") so this record survives independent of any single
conversation turn. It will be updated, not replaced, as further review
rounds occur.

## Authorized Spike Scope (recorded per explicit instruction, 2026-09-10)

The human candidate authorized a **bounded architecture feasibility spike
only** — explicitly **not** production implementation and **not** blanket
ADR approval. Constraints as given, honored throughout: disposable
fixtures and test credentials only; no real human-approval credentials
used; no changes pushed; the approved specification (`spec.md`) was not
altered. All spike code and fixtures ran in the session scratchpad, outside
this repository, and were not committed — only this written record and
`gate-4-spike-results-2026-09-10.md` persist. Full results, including every
retained command/exit-code/output and every explicit PASS/FAIL/NOT RUN
verdict, are in that companion file — summarized in the "Round 3 → Spike"
section below.

## Round 1 → Round 2: Findings and Resolutions

The human candidate's first Human Gate 4 review pass identified eight
findings against the Round-1 plan and ADR set. All eight are addressed in
Round 2 (this revision). None were silently dropped; each resolution is
cited below with its governing artifact.

| # | Finding | Resolution | Governing artifact |
|---|---|---|---|
| 1 | ADR-0005/0007 crash-recovery rule could duplicate a non-idempotent effect on retry | Durable execution identities, atomic (CAS) claiming, lease-based stale-worker detection, per-effect-class reconciliation before retry, fencing against zombie workers | ADR-0005 Rev. 2 §Decision |
| 2 | No concrete execution model for "real engineering actions" — orchestration stages were an abstract graph with unspecified work inside | Named agent-adapter contract (12 SDLC-stage adapters, each with input/tool/output/validation), each invoking an installed SpecKit command, a human wait, or real executed/validated work; worked DAG example with real fan-out and a join | ADR-0005 Rev. 2 §Decision — Agent Adapters |
| 3 | Credential isolation relied on gitignore + package convention, not an enforceable boundary against an agent running as the same OS user | OS-sandboxed subprocess boundary (Linux `bwrap` / macOS `sandbox-exec`) denying filesystem access to the credentials path, plus Unix file-permission baseline; explicit in-process-vs-subprocess statement; network-permission scope disclosed; **not marked PASS** pending its own test | ADR-0006 Rev. 2 |
| 4 | SQLite shared-writer contention between analytics, workflow/audit, and domain writes was unaddressed; crash windows around the HTTP response were unanalyzed; deduplication was unaddressed; p95 was conflated with a hard timeout | Write-ahead-log file (not a SQLite table) decouples the hot redirect path from SQLite contention entirely; precise crash-window analysis; `event_id`-based deduplication for drain-worker crash-and-reprocess; explicit hard-timeout (`PVT-001a`, 20ms) vs. p95 target (`PVT-001b`, 50ms) distinction; SQLite contention for all *other* writers addressed via `busy_timeout` + bounded retry (ADR-0007 Rev. 2) | ADR-0009 Rev. 2, ADR-0007 Rev. 2 |
| 5 | "OpenAPI validated" overstated a YAML-parse check as contract validation | Corrected language in plan.md §2; real structural validation executed (`openapi-spec-validator`, exit 0, output retained); runtime conformance explicitly noted as still-future work | plan.md §2 |
| 6 | Release-readiness rule incorrectly implied `NOT READY` could only result from delivery-sequence items 1–7 being incomplete, which would let an accepted limitation waive a mandatory requirement | Rule corrected: any missing mandatory requirement/scenario/security control/approval/policy outcome/validation blocks `READY`, regardless of delivery-sequence bucket; accepted limitations restricted to genuinely non-mandatory items | plan.md § Planning Constraints |
| 7 | No concrete approval-timeout or rate-limit proposal; private-address validation implied DNS-rebinding protection it doesn't provide; idempotency-key unguessability was assumed; unauthenticated API scope was not stated plainly | Concrete proposed numbers (`PVT-006` timeout, `PVT-007` rate limit); DNS-rebinding gap explicitly disclosed as unresolved at resolution time; minimum idempotency-key length proposed, entropy explicitly disclosed as the caller's responsibility; unauthenticated scope (including unauthenticated `DELETE`) stated explicitly | plan.md §5, §8 |
| 8 | Gate 4 decision inventory existed only in chat, not the repository; "Constitution FR-312" mislabeled a specification requirement as a constitution citation, inside the already-approved, committed spec.md | This file persists the inventory; the citation error is identified precisely below as a **proposed, non-substantive amendment** — spec.md has **not** been silently altered | This file; see "Proposed Specification Amendment" below |

## Round 2 → Round 3: Findings and Resolutions

A further review round found that several Round-2 fixes were themselves
incomplete — not new problems, but gaps in how thoroughly Round 2 closed
the original findings. All are addressed in Round 3. Two of Round 2's ADRs
(0005, 0006, 0007, 0009) required a further revision each.

| # | Finding | Resolution | Governing artifact |
|---|---|---|---|
| 9 | Adapter DAG ran Task Decomposition before Architecture/Design and Human Architecture Approval — inverted relative to the guide's own Final Lifecycle (Section 2/27), which this project has itself followed turn-by-turn | Corrected stage order: Architecture/Design → Human Architecture Approval → Checklist → Task Decomposition → Analyze → Implementation; Checklist and Analyze stages added (were missing entirely) | ADR-0005 Rev. 3 §Decision — Corrected Lifecycle Order |
| 10 | "Invoke `/speckit-tasks`" was written as though it were a standalone shell command — it is not; SpecKit skills are Markdown instructions a Claude Code session follows | Corrected: adapters invoke the real `claude` CLI, headless, prompted with the skill name, so Claude Code's own skill loader resolves it; exact flags left as an implementation detail, not asserted | ADR-0005 Rev. 3 §Decision — Real Claude Invocation |
| 11 | An in-band exception raised *after* a side effect was treated as automatically safe to retry without reconciliation — a worker can act, then throw | Reconciliation via `check_effect()` now required after exception, timeout, **or** stale lease alike for `externally_observable_uncertain` stages; only `idempotent` stages skip it | ADR-0005 Rev. 3, ADR-0007 Rev. 3 |
| 12 | Fencing the `orchestration_stage_execution` database row does not stop a still-running "zombie" worker from continuing to write real files or produce other external effects | Isolated per-execution `git worktree`s; the controller alone promotes output into the main tree, gated on fencing + a passing postcondition validator + current artifact revision — a zombie's output is simply never promoted | ADR-0005 Rev. 3 §Decision — Isolated Execution Workspaces |
| 13 | The reaper only ran on scheduler ticks — a single hung stage with no other transitions occurring would never be re-checked | Reaper now also runs on a fixed wall-clock interval (`PVT-008`, proposed 10s), independent of transitions | ADR-0005 Rev. 3 |
| 14 | "3 attempts, backoff 1s/2s/4s" miscounted — 3 attempts have exactly 2 intervening waits, not 3 | Corrected to 3 attempts, waits of 1s then 2s | ADR-0007 Rev. 3 |
| 15 | Per-attempt timeouts (5s/10s) were unrealistic for an actual Claude Code invocation or a real `pytest` run | Split and revised: 5s internal, 300s `pytest`, 600s Claude Code — all proposed, requiring approval | ADR-0007 Rev. 3 |
| 16 | Credential isolation covered only the credentials file path — an agent that could modify the approval server, database, policy manifest, or launch scripts could defeat approval without ever reading a token; the macOS sandbox profile also default-allowed everything but one denied path | Explicit protected-asset list (database, policy manifest, launch scripts, orchestration engine's own source, main `.git/`); macOS profile corrected to default-deny; identical boundary applied to every agent subprocess including test execution; explicit statement that the interactive Claude Code session developing this repo is out of this ADR's scope | ADR-0006 Rev. 3 |
| 17 | Postconditions had no executable validator — dependency completion alone (a status flag) was treated as proof; a task checkbox or clean git status is not evidence | Stage `succeeded` now requires the controller to run a real postcondition validator and retain its exit code, output hash, and per-artifact SHA-256 hashes | ADR-0005 Rev. 3 §Decision — Executable Postconditions |
| 18 | Several ADRs' Validation sections claimed tests were "executed" and evidence "retained" when no code exists yet | Corrected to "Planned, not yet executed" across ADR-0003, 0004, 0005, 0007, 0008, 0009 | Each ADR's §Validation |
| 19 | "SQLite handles concurrent writes" language did not distinguish serialized writes from concurrent readers | Corrected: SQLite **serializes writes** under its single-writer lock; only readers run concurrently under WAL mode | ADR-0003 §Validation, ADR-0007 Rev. 3 |
| 20 | Analytics: the claimed "hard 20ms fsync-with-abandon" timeout cannot actually cancel a blocking syscall — a timed-out wait does not stop the write, which may complete later | Withdrawn. Durability write moved off any hard-timeout mechanism entirely (see #21) | ADR-0009 Rev. 3 |
| 21 | Analytics: recording the count *before* sending the response could durably record a redirect that a subsequent crash prevented from ever being sent — an overcount, contradicting FR-105's actual definition of the count | Durability write moved to **after** the response is sent, back onto plain SQLite (the separate WAL file is withdrawn — a net simplification); no count is ever recorded for a response not actually sent | ADR-0009 Rev. 3 |
| 22 | Analytics: how uncertainty survives a restart, and how "both event storage and loss-marker storage fail" is handled, was unanswered; "complete" could be inferred from an empty backlog alone | Single-store design (event storage and status tracking share one SQLite database, so they cannot fail independently); unclean-shutdown detection sets a sticky, system-wide `degraded_since_unclean_shutdown_at` signal; `complete` is never reported while it is set, regardless of backlog state — **proposed as a new contract element requiring your explicit specification approval**, not applied as decided | ADR-0009 Rev. 3 |

## Round 3 → Spike: Findings

A bounded feasibility spike (authorized scope above) directly executed the
three mechanisms most in question. Full evidence:
`gate-4-spike-results-2026-09-10.md`.

| # | Item | Verdict | Consequence |
|---|---|---|---|
| 23 | Real `claude` CLI headless invocation syntax | **PASS** | ADR-0005's illustrative `--cwd` syntax corrected to the real mechanism (process `cwd`, no such flag) — verified via `claude --help` and one real successful invocation (exit 0, real artifact produced, cost/duration retained) |
| 24 | Environment-variable secret scrubbing | **PASS** | Confirmed an explicit deny-list works; also found `env -i`-style full scrubbing breaks the CLI's own auth — ADR-0006 corrected from allow-list to deny-list |
| 25 | OS-sandbox isolation of agent subprocess (macOS `sandbox-exec`) | **FAIL** | Confirmed platform blocker: `(allow process-exec)` in any form aborts (`SIGABRT`) on macOS 26.6.2 — reproduced across 5 profile variants. **ADR-0006's primary mechanism does not currently work on the one platform it was tested against.** Not resolved by this spike — surfaced as an open architectural risk |
| 26 | OS-sandbox isolation (Linux `bwrap`) | **NOT RUN** | No Linux environment available this session |
| 27 | Git operations under the sandbox / controller-validator execution inside the sandbox | **NOT RUN** | Blocked by #25's root cause — no subprocess could be launched under any restrictive `sandbox-exec` profile to test either |
| 28 | Exception-after-effect reconciliation | **PASS** | Real file write, no success report, `check_effect()` correctly found the completed effect and promoted without a blind retry |
| 29 | Freeze/terminate worker before validate+promote | **PASS** | Real subprocess, real `SIGKILL` (`returncode=-9`), lease genuinely expired, effect correctly detected and promoted exactly once; fencing confirmed (0 rows affected on the zombie's late write) |
| 30 | Git-promotion-succeeds-DB-record-doesn't recovery | **PASS** | Real git commit with an execution-id trailer; DB update skipped (simulated crash); "restart" correctly found the existing commit via `git log --grep` and reconciled without duplicating it |
| 31 | Analytics: write fails, loss-marker succeeds | **PASS** | Forced failure, correctly marked the specific short code `incomplete` |
| 32 | Analytics: write **and** loss-marker write both fail | **PASS** | New scenario, explicitly requested this round — confirmed fallback to a plain-file sentinel, independent of SQLite's own availability |
| 33 | Restart/shutdown behavior (running marker, unclean-shutdown detection, clean-shutdown refusal while uncertainty pending) | **PASS** | All three behaviors confirmed with real DB state transitions |
| 34 | Operator acknowledgment does not restore historical completeness | **PASS** | The specific property most emphasized this round — confirmed the acknowledged short codes stayed `incomplete`/unfabricated after acknowledgment |
| 35 | FR-106 bounded-overhead requirement was incorrectly described as retired | **Corrected, not a spike PASS/FAIL** | Reverted: FR-106 remains in force, re-scoped to the background write's own duration (not response latency); real write measured at 0.276ms against a restored 50ms budget (`PVT-001`) |

## Option A (Separate OS User) — Preflight Evidence and Analysis (2026-09-10)

Per explicit instruction, **only read-only preflight commands were
executed** this round. Full command-by-command detail (sudo requirement,
exact path, expected exit code, PASS/FAIL meaning, macOS-version
dependency) is in `docs/adr/0006-human-approval-model.md`, "Revision 4 —
Option A Spike Design (Corrected, Pending Authorization, Not Executed)."
Summary:

- **Resolved proposed UID for the new account: `502`** — determined
  dynamically from the actual current UID listing (highest local-range UID
  found was `501`, the operator's own account), confirmed free via a
  second, independent read-only check.
- **`svcspikeagent` does not currently exist** — confirmed
  (`eDSRecordNotFound`).
- **`staff` group ID confirmed: `20`.**
- **Tool locations confirmed**: `sudo`, `dscl`, `claude`, `git`, `python3`
  all located, all present.
- **New finding, not previously examined**: the operator's home directory
  is `750` with group `staff`, and `.local`/`.local/bin`/`.claude` are all
  `755` (world-traversable/readable at the directory level). Since the
  proposed new account's `PrimaryGroupID` is also `staff` (the macOS
  default), Unix directory permissions alone — before any account-specific
  hardening — already grant it more traversal toward `~/.claude` than the
  isolation goal would ideally want. **No file contents under `~/.claude`
  were read, listed, or inspected** — this finding is from directory-mode
  bits only. Per your instruction not to touch home-directory or Claude
  configuration permissions, this is disclosed as a real constraint on what
  the spike can establish, not something this round proposes to fix.

**OS isolation vs. Claude execution — kept separate, as instructed**: the
designed test suite (§3 of ADR-0006 Revision 4) has 7 tests establishing
OS-level isolation (credential/database/policy/source/`.git` denial;
workspace-only read-write; git functioning under real ownership;
fail-closed detectability — the last one explicitly disclosed as a weaker,
design-level check since no controller code exists yet) and exactly 1 test
(3.7) for Claude CLI execution specifically, whose "PASS" is explicitly
**not** "authentication succeeds" (that's not achievable without a
provisioned credential, which is out of scope) but "fails cleanly with no
credential found, confirming no leak."

**Dedicated agent-only API credential — architectural analysis only, none
created**: `claude --help`'s own `--bare` flag documentation (already
captured this session) confirms `ANTHROPIC_API_KEY`/`apiKeyHelper` is a
real, CLI-supported auth path structurally separate from OAuth/keychain.
A dedicated, agent-scoped key would not weaken approval isolation (the two
credential systems — agent-to-Anthropic vs. human-to-approval-gate — are
already architecturally orthogonal). **Classification, per explicit
instruction**: since headless execution does not strictly require sharing
personal credentials, **Option A is not classified as categorically
unsuitable**. As currently scoped (no credential provisioned, none
authorized to be created), Test 3.7 is predicted to fail — a separate,
disclosed gap requiring its own future decision, not evidence against
Option A's OS-isolation mechanism itself.

## Human Gate 4 Decisions (2026-09-10, this round)

The human candidate made seven explicit decisions this round. Recorded
verbatim in effect, not paraphrased away:

1. **ADR-0006 Revision 3 REJECTED as written.** Credential isolation is
   **not** marked PASS. A final, bounded Option A spike (separate OS user)
   is **authorized to design**, not to execute — no privileged command may
   run until the human candidate has reviewed the exact commands. See
   ADR-0006 "Revision 4 — Option A Spike Design (Pending Authorization)."
2. **Option A spike scope**: must verify seven specific properties (agent
   cannot read test credentials; cannot read/modify database, policy
   manifest, controller source, approval scripts, or main `.git/`; can
   read/write only its assigned worktree; Claude CLI auth/headless
   execution functions under that user; git operations and controller
   validators work under real ownership/permissions; every
   application-spawned subprocess including tests uses the same boundary;
   the application fails closed when the boundary can't be established).
   If Claude CLI auth cannot be isolated cleanly, **report FAIL** — do not
   copy the operator's credentials into an agent-readable location.
3. **Spec.md citation fix APPLIED.** Exact diff:
   ```diff
   - candidate acting under the reviewer/approver role (Constitution FR-312). See
   + candidate acting under the reviewer/approver role (per spec.md FR-312). See
   ...
   - role (Constitution FR-312), on **2026-09-10**.
   + role (per spec.md FR-312), on **2026-09-10**.
   ```
   Applied to `spec.md` (currently lines 9 and 22 — shifted by two lines
   from the original Round 2 finding's "lines 8 and 20" because the Status
   line's own "Amended 2026-09-10" annotation, added as part of this same
   round, now precedes them). Recorded in spec.md's own new "Human Gate 4
   Amendment Record" section.
4. **`degraded_since_unclean_shutdown_at` contract addition APPROVED** as
   **FR-117**, with the exact semantics directed: sticky after an unclean
   shutdown; operator acknowledgment clears the forward-looking warning
   only; acknowledgment never restores or asserts historical completeness;
   historical uncertainty remains visible in analytics evidence. Applied
   consistently to `spec.md` (new FR-117 + Amendment Record),
   `contracts/openapi.yaml` (field description updated to APPROVED,
   re-validated — `openapi-spec-validator`: OK, exit 0), `plan.md` §7,
   `data-model.md` (`analytics_system_status` table), and
   `docs/adr/0009-analytics-consistency.md`.
5. **`PVT-001`, `PVT-002`, `PVT-003`, `PVT-006`, `PVT-007`, `PVT-008`
   provisionally approved as implementation targets** — explicitly labeled
   **unverified** until their own implementation-time tests pass. Per
   instruction: a single spike measurement (0.276ms for `PVT-001`) does not
   establish a performance percentile; this correction is applied in
   `plan.md` and `docs/adr/0009-analytics-consistency.md`.
6. **Private-address rejection and minimum Idempotency-Key length
   APPROVED as proposed**, including the documented DNS-rebinding and
   caller-entropy limitations — unchanged disclosures, now approved
   controls rather than open proposals. Applied in `plan.md` §8.
7. **No ADR accepted. Human Gate 4 remains open.** This section presents
   the requested five items (privileged commands, expected changes/
   cleanup, revised ADR-0006 decision, updated inventory, current git
   diff/status) for review — nothing here closes the gate.

## 1. ADR Inventory (Current — post-acceptance, 2026-09-10)

**Decision**: the human candidate reviewed the inventory below and said
"accept all," applied to every ADR presented for decision at that point
(0001–0005, 0007–0010) — **explicitly not including ADR-0006**, which had
already been ruled on separately (Rejected) earlier in this same review
and was not re-offered as part of this batch.

| ADR | Revision | Decision | Status |
|---|---|---|---|
| 0001 | 1 | Modular monolith | **Accepted** |
| 0002 | 1 | Python 3.12 + FastAPI + Pydantic v2 + pytest | **Accepted** |
| 0003 | 1 | SQLite, WAL mode, single file | **Accepted** |
| 0004 | 1 | Random base62 short codes | **Accepted** |
| 0005 | **3** | Durable execution identities, corrected lifecycle order, real `claude` CLI invocation (spike-verified), worktree isolation + controller-only promotion (spike-verified logic), executable postcondition validators | **Accepted** |
| 0006 | **3** | Broadened OS-sandboxed isolation | **REJECTED** by explicit Human Gate 4 decision — primary mechanism spike-FAILED on macOS, untested on Linux |
| 0006 | **4 (design only)** | Option A — separate OS user | Spike **designed**, awaiting authorization; **not executed** |
| 0007 | **3** | Corrected retry-safety semantics, corrected attempt/backoff count, realistic subprocess timeouts | **Accepted** |
| 0008 | 1 | Append-only audit + precise MTTR definition | **Accepted** |
| 0009 | **3** | Post-response SQLite-based analytics durability, sticky system-wide unclean-shutdown signal — spike-verified across 9 scenarios including the double-failure case; contract approved as FR-117 | **Accepted** |
| 0010 | 1 | Plain local process, no Docker | **Accepted** |

## 2. Decisions Requiring Human Approval

- **ADR-0006 alone** — the sole remaining unaccepted ADR, rejected as
  written, pending the Option A spike's outcome.
- **The exact Option A privileged commands** (setup/test/cleanup) — see
  ADR-0006 "Revision 4," still awaiting your explicit authorization before
  any `sudo` command runs. Not authorized by the "accept all" decision,
  which applied to ADRs, not to executing privileged commands.
- Whatever the Option A spike finds (PASS or FAIL) will itself require a
  follow-up decision: accept Option A, seek a different mechanism, or
  accept a disclosed, weaker interim posture.

## 3. Decisions Safely Deferrable

Unchanged: ADR-0004, 0008, 0010 do not block the walking skeleton.

## 4. Conflicts With the Current Plan

None among the design decisions themselves. ADR-0006 is a rejected
proposal awaiting a replacement design, not a conflict between artifacts.

## 5. Missing Information

- Egress network restriction for agent subprocesses (ADR-0006) — disclosed,
  unaddressed regardless of Option A's outcome.
- DNS-rebinding protection at redirect-resolution time (plan.md §8) —
  disclosed, accepted limitation (Decision 6 above).
- Concrete per-stage timeout overrides beyond the ADR-0007 default — a
  `/speckit-tasks` deliverable.
- **Linux `bwrap` isolation — still entirely untested.**
- Whether Option A actually works — the entire point of the next
  authorized spike; genuinely unknown until run.

## Specification Amendment — APPLIED (2026-09-10)

**Error identified**: `specs/001-governed-url-shortener/spec.md` (already
approved and committed at `e29f2d7`), lines 8 and 20, both cite
**"Constitution FR-312"** — this conflates two different governing
artifacts. `FR-312` is a **specification** requirement (this repository's
own `spec.md`, in the "Functional Requirements — Human Governance and
Policy Enforcement" section), not a Constitution principle. The
Constitution (`.specify/memory/constitution.md`) has no FR-numbered
identifiers at all — its structure is Roman-numeral Principles.

**Correction — APPLIED 2026-09-10, on your explicit approval** (citation
only — no change in meaning, no change to any requirement, role, or
behavior):
- `acting under the reviewer/approver role (Constitution FR-312)` →
  `acting under the reviewer/approver role (per spec.md FR-312)`
- `role (Constitution FR-312), on **2026-09-10**` → `role (per
  spec.md FR-312), on **2026-09-10**`

**Materiality assessment** (unchanged from the original finding): a
citation correction, not a change to any requirement's substance, scope, or
the approval that was actually granted — the human candidate genuinely did
act under the role FR-312 defines; only the artifact it was attributed to
was wrong. Classified as a **PATCH-level governance correction**, not a
FR-306 material change. Applied directly to the working tree alongside the
FR-117 amendment above; **not yet committed** — presented in the git diff
below for your review before any commit.

## Sequencing Decision — Timebox Prioritization (2026-09-10)

Given the assignment's 2–3 day timebox and that a **working prototype**
had not yet been started after the plan/ADR review, the human candidate
was presented with two options: (a) keep pursuing Option A (ADR-0006) to
a full PASS before writing any code, or (b) proceed to
`/speckit-checklist` → `/speckit-tasks` → implementation now, carrying
Option A forward as a documented, in-progress risk.

**Decision: (b).** ADR-0006 remains **Rejected**, not Accepted — this
sequencing decision does not change that. Its unresolved state is carried
forward explicitly as a disclosed, accepted risk, consistent with the
`READY WITH ACCEPTED LIMITATIONS` release-readiness outcome (plan.md §
Planning Constraints) — it is a candidate for that outcome specifically
because it is disclosed, not because it is resolved or waived. Also
practically necessary: this session cannot execute Option A's privileged
(`sudo`) commands itself (no interactive TTY/credential available), so
further progress on ADR-0006 requires the human candidate's own terminal
regardless of sequencing choice.
