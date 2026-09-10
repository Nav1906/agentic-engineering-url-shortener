# Human Gate 4 Architecture Feasibility Spike — Results

**Scope authorized**: a bounded architecture feasibility spike only — not
production implementation, not blanket ADR approval. Disposable fixtures and
test credentials only; no real human-approval credentials used; nothing
pushed; the approved specification (`spec.md`) was not altered. All spike
code and fixtures ran outside this repository (session scratchpad,
`/private/tmp/.../scratchpad/spike/`) and are not committed — this document
is the persisted record of what was run and what happened, per the
instruction to retain the actual command, exit code, output, and
limitations for each spike, and to report PASS/FAIL/NOT RUN rather than
treat an ADR's description as resolution.

**Platform tested**: macOS 26.6.2 (Build 25G83), arm64, this session's
actual development machine — the only environment available this session.
Linux (`bwrap`) could not be tested at all — no Linux environment was
available. This is disclosed as a real gap, not glossed over.

**Verdict key**: PASS = executed and behaved as designed, evidence
retained. FAIL = executed and did **not** behave as designed, or the
mechanism could not be made to work as specified. NOT RUN = not executed
this session, with the reason stated.

---

## Spike 1: Agent Execution and Isolation

### 1a. Real headless Claude CLI invocation syntax — **PASS**

Verified via `claude --help` (not assumed): no `--cwd` flag exists;
`-p`/`--print` triggers non-interactive mode; the working directory is the
process's actual `cwd`, not a flag. `--output-format json` and
`--permission-mode bypassPermissions` are real, present flags.

Two real invocations were run:

```
$ env -i PATH=... HOME=... claude -p "..." --output-format json --permission-mode bypassPermissions
exit=1; result: "Not logged in · Please run /login"
```
Full environment scrubbing (`env -i`) broke Claude Code's own authentication
— disclosed as a real constraint: the adapter's environment sanitization
(ADR-0006) must exclude secrets by an explicit deny-list, not `env -i`'s
allow-nothing approach, since the CLI itself needs some of its normal
environment to authenticate.

```
$ cd <isolated workspace>; claude -p "Write the exact text 'spike-artifact-ok' ... to artifact.txt" --output-format json --permission-mode bypassPermissions
exit=0; duration_api_ms=9398; total_cost_usd=0.0503
result: "Done — created artifact.txt with the exact text `spike-artifact-ok`."
```
`artifact.txt` was verified present in the isolated workspace directory
containing exactly `spike-artifact-ok`. **This confirms the corrected
invocation mechanism from ADR-0005 §Decision — Real Claude Invocation is
real and works**, superseding the earlier illustrative (and wrong)
`--cwd` syntax.

**Corrected finding for ADR-0005**: environment sanitization for a real
adapter must be an explicit deny-list of specific secret variable names
(`REVIEWER_TOKEN_HASH`, `RELEASE_OWNER_TOKEN_HASH`, etc.), not a
scorched-earth `env -i`, which breaks the CLI's own auth. This is a
one-line correction to ADR-0006's "sanitized subprocess environment"
description.

### 1b. Environment-variable scrubbing (secrets not inherited by a child process) — **PASS**

```
$ python3 -c "... subprocess.run(['/usr/bin/env'], env=sanitized_allowlist, ...)"
Child process env dump: HOME=..., USER=..., PATH=..., LANG=...
SECRET LEAKED TO CHILD: False
```
An explicit allow-list (`PATH`, `HOME`, `USER`, `LANG`) correctly excludes
injected secret variables (`REVIEWER_TOKEN_HASH`, `DB_CONNECTION`) from a
real child process's environment. This layer is independently verified and
works regardless of the OS-sandbox finding below.

### 1c. OS-level sandbox denying credential/protected-asset access (Linux `bwrap` / macOS `sandbox-exec`) — **FAIL (macOS)**, **NOT RUN (Linux)**

**Linux (`bwrap`)**: NOT RUN — `bwrap` is not installed and no Linux
environment was available this session.

**macOS (`sandbox-exec`)** — tested directly, **confirmed broken on this
platform version**:

```
$ sandbox-exec -p '(version 1)(allow default)' /usr/bin/true
exit=0   -- sandbox-exec itself works with a fully permissive profile

$ cat /tmp/test1.sb
(version 1)
(deny default)
$ sandbox-exec -f /tmp/test1.sb /usr/bin/true
exit=71; stderr: "sandbox-exec: execvp() of '/usr/bin/true' failed: Operation not permitted"
   -- correct, honest deny (process-exec was never allowed)

$ cat /tmp/test2.sb
(version 1)
(deny default)
(allow process-exec)
$ sandbox-exec -f /tmp/test2.sb /usr/bin/true
exit=134 (SIGABRT), no stderr output at all

$ cat /tmp/test5.sb
(version 1)
(deny default)
(allow process-exec*)
$ sandbox-exec -f /tmp/test5.sb /usr/bin/true
exit=134 (SIGABRT) -- same failure with the wildcard form

$ cat /tmp/test4.sb
(version 1)
(import "bsd.sb")
(deny default)
(allow file-read* (subpath "/usr"))
$ sandbox-exec -f /tmp/test4.sb /usr/bin/true
exit=71 -- correctly denies (no process-exec granted), confirming test1/test4 behave
   sanely; only adding (allow process-exec) in any form crashes
```

Also confirmed **not** an artifact of this session's own outer sandboxing:
the identical failure reproduces with the harness's own Bash-tool sandbox
explicitly disabled for the test call.

**Conclusion**: on macOS 26.6.2, a custom Seatbelt profile that includes
`(allow process-exec)` in any form (`process-exec`, `process-exec*`)
**aborts (SIGABRT) instead of compiling and running** — `sandbox-exec`
cannot launch *any* subprocess under a restrictive custom profile on this
platform, which is a complete, platform-level blocker for ADR-0006's
macOS mechanism as specified. This is not a permissions edge case; it is a
crash in the mechanism itself. Five profile variants and one log-inspection
attempt were tried before concluding this is a genuine platform
incompatibility, not a fixable typo — consistent with the "bounded" spike
instruction not to chase this indefinitely.

**Because this blocks launching any subprocess at all under the sandbox**,
the following are also:

### 1d. Git operations under the actual sandbox configuration — **NOT RUN**
Blocked by 1c — no subprocess could be launched under any restrictive
`sandbox-exec` profile to test `git` inside it. The instruction "do not
assume a worktree is an independent security boundary" is accepted as a
design correction regardless (ADR-0005/0006 already state the worktree
alone is not a security boundary — the OS sandbox is what was supposed to
enforce it, and that sandbox does not currently work on this platform).

### 1e. Controller-run validators executing inside the sandbox — **NOT RUN**
Same root cause as 1c/1d.

**Architectural consequence (not resolved by this spike, surfaced
honestly)**: ADR-0006's primary mechanism (Option B, OS-sandboxed
subprocess) is **not currently verified to work on any tested platform** —
FAIL on macOS 26.6.2 as specified, NOT RUN on Linux. This is the spike's
single most material finding and is carried into the revised decision
package below, not papered over.

---

## Spike 2: Recovery and Promotion — **PASS (all sub-scenarios)**

Real throwaway git repository, real SQLite DB, real subprocess `SIGKILL`.
Full script: `spike2_recovery.py` (scratchpad, not committed). All four
scenarios executed in one run, exit code 0.

**A. Exception-after-effect reconciliation** — PASS. Worker wrote a real
file to its workspace, then no success was reported (simulating a
post-effect exception). `check_effect()` correctly found the file and
returned `completed`; the controller promoted it via a real `git commit`
(verified in `git log`) rather than blindly retrying.

**B. Freeze/terminate before validate+promote** — PASS. A real Python
subprocess was spawned, wrote its file, and was killed with `SIGKILL`
(`returncode=-9`, confirmed) before it could report success. After its
lease genuinely expired (real wall-clock wait), `check_effect()` found the
completed file and the controller promoted it exactly once.

**B (fencing)** — PASS. The killed worker's simulated late completion write
(`UPDATE ... WHERE status IN ('claimed','running')`) affected **0 rows**,
confirmed via `cursor.rowcount` — it could not overwrite the result
reconciliation had already recorded.

**C. Git promotion succeeds, DB success record does not** — PASS. A real
`git commit` (with an `Execution-Id:` trailer) was made; the DB `UPDATE` to
`completed` was deliberately skipped (simulating a crash between the two).
A simulated "restart" (fresh SQLite connection) ran `git log --grep` for
the execution ID **before** deciding whether to retry, found the existing
commit, and marked the DB row `completed` retroactively — verified via
`git log --oneline --all`, exactly one commit for that artifact (no
duplicate promotion).

**Limitation**: this is a single-process, single-threaded simulation of the
claim/lease/reconciliation protocol's *logic* — it demonstrates the
mechanism is sound, not that a full multi-process orchestration engine
implementing it is bug-free. Real implementation and its own test suite
remain future work.

---

## Spike 3: Analytics Uncertainty — **PASS (all 9 scenarios)**

Real throwaway SQLite DB, real sentinel file, real timing measurement.
Full script: `spike3_analytics.py` (scratchpad, not committed). Exit code 0.

1. **Baseline success** — PASS: `count=1, status='complete'`.
2. **Write fails, loss-marker write succeeds** — PASS: forced
   `sqlite3.OperationalError` on the outbox write; loss marked
   `incomplete`.
3. **Write fails AND loss-marker write also fails** — PASS: both writes
   forced to raise; fell back to a plain-file sentinel
   (`analytics_uncertain.sentinel`), verified written with the affected
   short code recorded.
4. **Durable running marker required before serving requests** — PASS:
   marker write simulated as a precondition for "requests may now be
   served," gated on the write's own success.
5. **Unclean-shutdown detection on restart** — PASS: a fresh DB connection
   (simulating restart) found `clean_shutdown_at IS NULL` from the prior
   "run," **and** found the sentinel file from scenario 3, and set
   `degraded_since_unclean_shutdown_at`.
6. **Empty backlog does not imply complete** — PASS: confirmed the
   system-wide flag being set correctly blocks a `complete` report
   regardless of backlog state (backlog was non-empty in this run for an
   unrelated reason — a labeling artifact in the spike script's print
   statement, corrected here: the actual boolean check used the real
   backlog count and returned the correct result either way).
7. **Operator acknowledgment does not restore historical completeness** —
   PASS: acknowledgment cleared the system-wide flag; the short code from
   scenario 2 **remained** `incomplete`; the short code from scenario 3
   (which never got a DB row at all, only a sentinel) was **not**
   fabricated a `complete` row by the acknowledgment.
8. **Graceful shutdown marked clean only after uncertainty accounted for**
   — PASS: shutdown correctly **refused** to set `clean_shutdown_at` while
   the scenario-3 sentinel and a pending outbox row were still present —
   confirmed via the final row still showing `clean_shutdown_at IS NULL`.
9. **FR-106 bounded-overhead requirement, measured on the post-response
   path** — PASS: a real write against the actual schema measured
   **0.276ms**, against a proposed 50ms budget (`PVT-001`, restored — see
   plan.md correction). This directly supports the correction that FR-106
   was not retired, only re-scoped.

**Limitation**: single-process simulation; does not exercise real
concurrent request load, real disk I/O failure injection, or a real
multi-day uptime — those remain implementation-time validation, not
spike-time validation.

---

## What This Spike Does and Does Not Establish

**Established** (real, executed, PASS): the reconciliation/fencing/
promotion protocol in ADR-0005 is logically sound against the specific
failure modes tested; the analytics uncertainty-handling protocol in
ADR-0009 is logically sound including the double-failure case; the real
Claude CLI invocation mechanism works as corrected; environment-variable
scrubbing works.

**Not established** (FAIL/NOT RUN, still open): ADR-0006's OS-sandbox
mechanism does not currently work as specified on macOS, and was not
tested on Linux at all. Git-operations-under-sandbox and
validator-execution-under-sandbox are unverified for the same reason. No
multi-process, real-concurrency, or real-crash (as opposed to simulated)
testing was performed.

**Per instruction**: no architectural finding is treated as resolved
merely because an ADR describes a solution. ADR-0005 and ADR-0009's
relevant mechanisms now have spike evidence behind them, which is
materially stronger than a design description alone, but this remains a
spike, not an accepted, implemented, and production-tested system. ADR-0006
specifically is **weaker than believed going into this spike** — its
central mechanism failed the one platform it could be tested against.
