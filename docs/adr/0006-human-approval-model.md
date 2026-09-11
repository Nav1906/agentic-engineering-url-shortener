# ADR-0006: Human Approval Model and Enforceable Credential Isolation

## Status

**Revision 5 ACCEPTED by explicit Human Gate 4 decision (2026-09-11).** See
"Revision 5 — Scope-Limited Acceptance (Accepted, 2026-09-11)" near the end
of this file for the full decision, its exact boundary, and the real,
implemented, tested mechanism (T100–T103). Revisions 1–4 below are
preserved for the record — they document the credential-*isolation*
mechanism this project spent three rounds trying and failing to make safe
for an *external agent subprocess*, and the honest platform-level failure
(macOS `sandbox-exec`) that made Revision 3 unacceptable. Revision 5 does
**not** resolve that failure — it makes it moot for this release by
removing external-agent subprocess execution from the trusted boundary
entirely, a different and narrower claim. Read Revision 5's own Context
section before assuming anything below still describes the shipped system.

---

**Revision 3 REJECTED by explicit Human Gate 4 decision (2026-09-10).** The
human candidate rejected Revision 3 as written: its primary mechanism
(macOS `sandbox-exec`) failed a direct feasibility spike on the actual
target platform, and Revision 3's Linux `bwrap` alternative was never
tested at all. Credential isolation is **not** marked PASS. A further,
final bounded spike for **Option A (a separate OS user)** has been
authorized — design only at this point; no privileged command has been
executed. See "Revision 4 — Option A Spike Design (Pending Authorization)"
at the end of this file for the exact commands awaiting review, and
`docs/governance/gate-4-review-2026-09-10.md` for the full decision record.
The remainder of this document below is Revision 3's content, preserved
for reference — **it is superseded/rejected, not currently the proposed
decision**, pending the Option A spike's outcome.


**Proposed** — not Accepted. **Revision 3** (2026-09-10), correcting a
further Human Gate 4 finding: Revision 2 sandboxed only the credentials
**file path**, but an agent subprocess with broader write access could still
modify the approval server's own code, the database, the policy/verifier
configuration, or the launch scripts themselves — any of which could
subvert the approval system without ever touching the credentials file
directly. This revision defines the full protected-asset boundary, a
sanitized subprocess environment, and applies the identical boundary to
**every** subprocess the orchestration engine spawns, including test runs —
not credentials-adjacent adapters alone. It also states plainly what this
ADR does **not** cover: the interactive Claude Code session used to develop
this repository is not itself sandboxed by any mechanism described here.

**Spike finding (Human Gate 4, 2026-09-10) — confirmed platform blocker,
not resolved by this ADR**: a bounded feasibility spike
(`docs/governance/gate-4-spike-results-2026-09-10.md`) directly tested the
macOS `sandbox-exec` mechanism this ADR specifies, on the actual
development platform (macOS 26.6.2). **It does not work as specified**: a
custom Seatbelt profile containing `(allow process-exec)` in any form
aborts (`SIGABRT`) instead of compiling and running, meaning
`sandbox-exec` cannot launch any subprocess at all under a restrictive
custom profile on this OS version — not a permission edge case, a crash in
the mechanism itself, reproduced across five profile variants. Linux
`bwrap` was not tested (no Linux environment available this session). **This
finding is not resolved here** — it is surfaced honestly per the explicit
instruction not to mark an architectural finding resolved merely because an
ADR describes a solution. Option A (a separate OS user) does not depend on
this broken mechanism and remains analytically available, but **was not
itself tested** by this spike (creating a real OS-level user account was
outside the spike's authorized scope). Until either Option B is confirmed
working on a real target platform or Option A is validated, **this ADR's
credential/protected-asset isolation claim is unverified on every platform
tested**, and remains explicitly "Proposed / not yet PASS" — now for a
stronger reason than "the test hasn't been written yet."

## Context

FR-307–FR-313 require agent identities to have no access to human-approval
credentials. Revision 2 correctly identified that gitignore/package
convention is not enforcement and moved to an OS-sandboxed subprocess
boundary — but scoped that sandbox's *deny* rule to one file path. An agent
subprocess that can still **write** to the approval server's source, the
SQLite database file, `config/policies.yaml`, or `scripts/approve.py` could
achieve the same outcome (a compromised or malicious agent approving its
own work) through a different door — modifying the verifier instead of
reading the secret it checks against. This revision closes that door by
defining what must be protected, not just what must be denied.

## Decision Drivers

- The boundary must cover every asset whose modification could subvert
  approval integrity, not only the credentials file.
- The boundary must apply uniformly to every subprocess the orchestration
  engine spawns — including test execution, which touches the same
  filesystem and could be a vector if treated as a special, less-guarded
  case.
- The subprocess environment must be sanitized, not merely the filesystem.
- This ADR must not be read as claiming protection for the interactive
  Claude Code session used to build this repository — that session is
  unrestricted by design and is not in this ADR's scope.
- Reuse ADR-0005's isolated-worktree/controller-promotion mechanism rather
  than inventing a second, overlapping isolation scheme.

## Options Considered

Revision 2's Option A (separate OS user) and Option B (sandbox tooling)
remain the two live choices; **Option B remains the decision**, now scoped
correctly:

**B (revised). OS-level sandbox (Linux `bwrap` / macOS `sandbox-exec`)
applied to a broader, explicitly enumerated protected-asset set, as a
default-deny-write policy — not a single deny rule.**
- Advantages: closes the "modify the verifier instead of reading the
  secret" gap directly; reuses the same tooling decision from Revision 2
  (no new sandbox technology, just a corrected policy).
- Disadvantages: the macOS `sandbox-exec` profile must now be written as
  **default-deny** with explicit allows (Revision 2's profile only added
  one `deny` rule, which — because `sandbox-exec` profiles default-allow
  unless `(deny default)` is set — left every other path readable *and
  writable* by default; this was an actual gap in Revision 2's macOS
  profile specifically, now corrected).
- Risks: a default-deny profile is more work to get right (must explicitly
  allow everything legitimately needed) than a single deny rule — accepted
  as necessary, not optional, given what Revision 2's narrower rule missed.
- Implementation impact: moderate — one corrected profile, one explicit
  asset list.

## Decision

**Protected controller assets (explicit list, default-deny-write for every
agent subprocess)**:
- `local-secrets/` — approver credentials (unchanged from Revision 2).
- `data/app.db*` — the SQLite database file(s), including WAL/SHM
  sidecar files.
- `config/policies.yaml` — the compliance/change-control policy manifest
  (research.md §8) — an agent that could edit this could make its own work
  pass a policy check it should fail.
- `scripts/approve.py`, `scripts/bootstrap_credentials.py` — the approval
  and credential-bootstrap launch scripts.
- `src/orchestration/`, `src/api/`, `src/persistence/`,
  `src/observability/` — the orchestration engine's own source, including
  the postcondition-validator and promotion logic from ADR-0005. An agent
  that could modify its own verifier could make any outcome "pass."
- `.git/` at the **main** repository (not the agent's own isolated
  worktree, ADR-0005) — direct manipulation of the main repository's git
  state bypasses the controller-only-promotion gate entirely.

**Narrowly writable workspace**: the **only** writable path for any agent
subprocess is its own isolated worktree
(`agent-workspaces/<execution_id>/`, ADR-0005) — this is the same
mechanism ADR-0005 defines for effect-reconciliation, reused here rather
than duplicated, per the instruction to avoid parallel infrastructure for
the same underlying concern.

**Sanitized subprocess environment, corrected by spike evidence**: the
agent subprocess's environment excludes `REVIEWER_TOKEN_HASH`,
`RELEASE_OWNER_TOKEN_HASH`, any database connection detail, and any other
controller-only variable, via an **explicit deny-list** applied to the
inherited environment — **not** a from-scratch allow-list (`env -i`
style). The spike confirmed a fully-scrubbed environment breaks the
`claude` CLI's own authentication (`"Not logged in · Please run
/login"`), so the real mechanism must be "inherit, then remove named
secrets," not "start empty." The deny-list approach was verified to
correctly prevent injected secrets from reaching a child process (spike
1b, PASS). It receives what its adapter contract (ADR-0005) declares it
needs (e.g., its `execution_id`, its worktree path, and whatever the task
itself requires) plus whatever the CLI itself needs to authenticate. The
agent has **no legitimate reason** to hold a database credential or
handle at all — per ADR-0005, it never talks to SQLite directly; only the
controller does, at promotion time.

**Uniform application — including tests**: **every** subprocess the
orchestration engine spawns runs inside the identical sandbox boundary
described here, with no exception for the Testing adapter. A test run is
real code execution with real filesystem access and is exactly as capable
of reading a credential or modifying a protected asset as any other
subprocess — treating it as a lower-risk special case would be the same
error Revision 2 made in scoping the boundary too narrowly.

**Sandbox mechanism, corrected**:
- **Linux**: `bwrap --unshare-all --share-net --ro-bind / / --bind
  agent-workspaces/<execution_id> agent-workspaces/<execution_id> --tmpfs
  local-secrets --tmpfs data --tmpfs config --tmpfs scripts --tmpfs
  src/orchestration --tmpfs src/api --tmpfs src/persistence --tmpfs
  src/observability --tmpfs .git -- <sanitized-env> python3
  agent_adapter_entrypoint.py ...` — every protected path is
  `--tmpfs`-overlaid (replaced with an empty, isolated filesystem inside
  the subprocess's mount namespace) **in addition to** the general
  `--ro-bind / /` from Revision 2, so protected assets are neither
  readable nor writable, not merely non-writable.
- **macOS**: `sandbox-exec -f agent.sb`, profile **corrected to
  default-deny**: `(deny default) (allow process-exec) (allow
  file-read* (subpath "/usr") (subpath "<python-install>")) (allow
  file-read* file-write* (subpath "<repo>/agent-workspaces/<execution_id>"))
  (allow network*)` plus explicit reads for whatever the Python
  interpreter and Claude Code CLI themselves require to start — with
  **no** rule granting access to any path in the protected-asset list
  above, by omission (default-deny), not by an explicit deny that could be
  incomplete. Disclosed limitation, unchanged from Revision 2:
  `sandbox-exec` is a deprecated (if still functional) Apple API.
- **Pre-flight self-check (defense in depth, unchanged mechanism, broadened
  scope)**: before real work, the entrypoint attempts to `open()` **each**
  protected-asset path (not just the credentials file); any successful open
  is a hard configuration failure, logged as an audit event, refusing to
  proceed.

**What this ADR does not cover, stated explicitly**: the interactive Claude
Code session used throughout this project's own development (this
conversation) is **not** sandboxed by anything described here and is
outside this ADR's scope entirely — it runs with the access the operator
granted it directly. This ADR governs only the **built application's own**
agent-adapter subprocesses (ADR-0005), spawned by the orchestration engine
at a future implementation's runtime. Describing the outer session as
"protected by its child sandbox" would be false and is not claimed here.

**Roles, revision-binding, and audit fields**: unchanged from Revision 2.

## Rationale

Protecting one file while leaving the verifier, the database, and the
launch scripts writable does not achieve "agent identities MUST NOT have
access to human-approval credentials" in any meaningful sense — an agent
that can rewrite `scripts/approve.py` or `config/policies.yaml` has
defeated the approval system without ever reading a token. Enumerating the
actual protected-asset set, applying default-deny rather than point-denies,
and treating every subprocess (tests included) identically closes that
gap using the same sandbox tooling already decided in Revision 2 — no new
technology, a corrected policy.

## Consequences

- **Positive**: the isolation claim now covers the actual threat model
  (a compromised or malicious agent process), not just the credentials
  file specifically.
- **Negative**: the macOS profile is materially more work to write
  correctly (default-deny with explicit allows) than Revision 2's
  single-rule version — necessary, not optional.
- **Operational**: unchanged process model (agent subprocess, sandboxed,
  per-execution); the protected-asset list is configuration, reviewed
  alongside any future change to the repository layout.
- **Testing**: `tests/security/test_agent_credential_isolation.py`
  (planned) is broadened to attempt a read/write against **every**
  protected asset, not the credentials file alone; a parallel test
  confirms the Testing adapter itself runs under the identical sandbox.
- **Governance**: unchanged — still explicitly "Proposed / not yet PASS"
  until these tests exist and pass.

## Risks and Mitigations

- **Risk**: the protected-asset list could go stale as the repository
  layout evolves (a new controller-only directory added without updating
  this list). **Mitigation**: flagged as an ongoing maintenance
  obligation, not solved by this ADR alone — the pre-flight self-check is
  the defense-in-depth layer that catches a missed path if the *sandbox*
  configuration lags, though it cannot catch a path missing from *both*
  lists simultaneously; disclosed, not hidden.
- **Risks carried over from Revision 2, unchanged**: `sandbox-exec`
  deprecation; unrestricted agent-subprocess network egress; human error
  pasting a raw token into an agent-visible context.

## Reversibility

**Moderate**, unchanged from Revision 2.

## Traceability

- Requirements: FR-307–FR-313, AMB-005.
- Specification sections: Planning Obligations.
- Plan sections: plan.md §5, §8.
- Related: ADR-0005 Revision 3 (the shared isolated-worktree mechanism this
  ADR's sandbox wraps around).
- Prior review: Human Gate 4 findings, Rounds 1–2 (2026-09-10),
  `docs/governance/gate-4-review-2026-09-10.md`.
- Expected tasks: approval-gates, agent-sandbox-launcher task groups.

## Validation

**Planned, not yet executed** (no code exists yet): the broadened
credential/protected-asset isolation test above, applied identically to
every adapter subprocess including Testing; the four negative approval
tests from Revision 1 (unauthenticated, wrong-role, agent-originated,
stale-revision), unchanged. **None of this is yet executed** — this ADR's
Validation section describes what must pass for this control to be marked
PASS; it is not marked PASS now.

---

## Revision 4 — Option A Spike Design (Corrected, Pending Authorization, Not Executed)

**Status of this section**: design only, revised per explicit safety
corrections requested at this review round. **Read-only preflight commands
listed in §0 below have been executed** (non-mutating, evidence retained).
**No command in §2 onward has been run.** Absolute paths are used
throughout per instruction; the scratchpad base path referenced below is:

```
/private/tmp/claude-501/-Users-moraboinanaveenkumar-Projects-agentic-engineering-url-shortener/bc89be00-752a-4657-97a9-3286e49c7a8b/scratchpad/spike-option-a
```

— entirely outside this repository (`/Users/moraboinanaveenkumar/Projects/agentic-engineering-url-shortener`) and outside the operator's home directory tree in the sense that matters (it is under `/private/tmp`, not `/Users/moraboinanaveenkumar`).

---

### 0. Read-only preflight — EXECUTED, evidence retained

| # | Command | sudo? | Path touched | Exit | Result |
|---|---|---|---|---|---|
| 0.1 | `/usr/bin/sw_vers` | No | none (read-only system query) | 0 | `ProductVersion: 26.6.2`, `BuildVersion: 25G83` |
| 0.2 | `/usr/bin/dscl . -read /Users/svcspikeagent` | No | reads DS record `/Users/svcspikeagent` | 56 | `eDSRecordNotFound` — **confirmed: does not exist** |
| 0.3 | `/usr/bin/dscl . -list /Users UniqueID` | No | reads all DS user records | 0 | Full listing captured; only one real local user, `moraboinanaveenkumar` at UID 501 — all others are system/service accounts |
| 0.4 | `awk '$2+0>=501 {print $2}' \| sort -n \| tail -1` (on 0.3's output) | No | none (pure computation on already-retrieved data) | 0 | Highest local-range UID found: **501** |
| 0.5 | Computed: `NEXT_UID = 501 + 1` | No | none | — | **Resolved proposed UID: `502`** |
| 0.6 | `/usr/bin/dscl . -search /Users UniqueID 502` | No | reads DS records | 0 | Empty result — **confirmed 502 is free** |
| 0.7 | `/usr/bin/dscl . -read /Groups/staff PrimaryGroupID` | No | reads DS record `/Groups/staff` | 0 | `PrimaryGroupID: 20` |
| 0.8 | `command -v sudo dscl claude git python3` | No | none | 0 (each) | `sudo`→`/usr/bin/sudo`, `dscl`→`/usr/bin/dscl`, `claude`→`/Users/moraboinanaveenkumar/.local/bin/claude`, `git`→`/usr/bin/git`, `python3`→`/usr/bin/python3` |
| 0.9 | `/bin/ls -ld /Users/moraboinanaveenkumar` | No | reads directory metadata only | 0 | `drwxr-x---+  ... staff ... /Users/moraboinanaveenkumar` |
| 0.10 | `/bin/ls -ld /Users/moraboinanaveenkumar/.local /Users/moraboinanaveenkumar/.local/bin` | No | reads directory metadata only | 0 | Both `drwxr-xr-x` (world-readable/traversable) |
| 0.11 | `/bin/ls -l /Users/moraboinanaveenkumar/.local/bin/claude` | No | reads metadata (symlink target) only | 0 | Symlink → `/Users/moraboinanaveenkumar/.local/share/claude/versions/2.1.267` |
| 0.12 | `/bin/ls -ld /Users/moraboinanaveenkumar/.claude` | No | reads directory metadata only | 0 | `drwxr-xr-x` (world-readable/traversable) |

**Important finding from 0.9–0.12, disclosed now, not glossed over**: the
operator's home directory is `750` (owner full access, **group `staff`
gets read+traverse**, other gets nothing) — and `svcspikeagent`'s proposed
`PrimaryGroupID` (0.7) is `20`, i.e. `staff`, the same group. `.local`,
`.local/bin`, and `.claude` are all `755` (**world**-readable and
traversable, not just group). This means: **before any account is even
created**, ordinary Unix permission bits already grant fairly broad
directory-level traversal toward `~/.claude` to any local user in `staff`
— which every default local macOS user, including a newly created one, is
in by default. This is a real, disclosed constraint feeding directly into
the "Claude execution" analysis below. **No file *contents* under
`~/.claude` were read, listed, or inspected** — only directory-level
permission bits, which reveals no authentication data itself.

---

### 1. Account-creation commands (NOT executed)

| # | Command | sudo? | Exact path/record | Expected exit | PASS means | FAIL means | macOS-version dependent? |
|---|---|---|---|---|---|---|---|
| 1.1 | `sudo /usr/bin/dscl . -create /Users/svcspikeagent` | **Yes** | DS record `/Users/svcspikeagent` (created) | 0 | Record created | Nonzero (e.g., already exists, permission denied) | No — `dscl` is a decades-stable, standard macOS directory-service tool |
| 1.2 | `sudo /usr/bin/dscl . -create /Users/svcspikeagent UserShell /usr/bin/false` | **Yes** | same record, `UserShell` attribute | 0 | Attribute set | Nonzero | No |
| 1.3 | `sudo /usr/bin/dscl . -create /Users/svcspikeagent RealName "Spike Agent (temporary, disposable, Gate 4 Option A spike)"` | **Yes** | same record, `RealName` attribute | 0 | Attribute set | Nonzero | No |
| 1.4 | `sudo /usr/bin/dscl . -create /Users/svcspikeagent UniqueID 502` | **Yes** | same record, `UniqueID` attribute — uses the **resolved value from §0.5**, not recomputed here | 0 | Attribute set to `502` | Nonzero, or set to an unexpected value | No |
| 1.5 | `sudo /usr/bin/dscl . -create /Users/svcspikeagent PrimaryGroupID 20` | **Yes** | same record, `PrimaryGroupID` attribute (`staff`, per §0.7) | 0 | Attribute set | Nonzero | No |
| 1.6 | `sudo /usr/bin/dscl . -create /Users/svcspikeagent NFSHomeDirectory /private/var/svcspikeagent` | **Yes** | same record, `NFSHomeDirectory` attribute | 0 | Attribute set | Nonzero | No |
| 1.7 | `sudo /usr/bin/dscl . -create /Users/svcspikeagent AuthenticationAuthority ";DisabledUser;"` | **Yes** | same record, `AuthenticationAuthority` attribute — **disables all interactive authentication for this account** | 0 | Attribute set | Nonzero | No |
| 1.8 | `sudo /usr/bin/dscl . -passwd /Users/svcspikeagent "*"` | **Yes** | same record, password hash set to the literal locked-password sentinel `*` (belt-and-suspenders alongside 1.7 — never a usable password) | 0 | Set | Nonzero | No |
| 1.9 | `sudo /bin/mkdir -p /private/var/svcspikeagent` | **Yes** (`/private/var` is root-owned) | filesystem path `/private/var/svcspikeagent` — created | 0 | Directory created | Nonzero | No |
| 1.10 | `sudo /usr/sbin/chown svcspikeagent:staff /private/var/svcspikeagent` | **Yes** | ownership of `/private/var/svcspikeagent` changed to the new user | 0 | Ownership changed | Nonzero | No |
| 1.11 | `sudo /bin/chmod 700 /private/var/svcspikeagent` | **Yes** | permissions of `/private/var/svcspikeagent` set to owner-only | 0 | Mode set | Nonzero | No |
| 1.12 | `/usr/bin/dscl . -read /Groups/admin GroupMembership` | No | reads DS record `/Groups/admin` | 0 | `svcspikeagent` **absent** from the list | `svcspikeagent` present (must never happen — would mean a scripting error, not intended by this design) | No |
| 1.13 | `/usr/bin/id svcspikeagent` | No | reads the now-created account's identity | 0 | `uid=502(svcspikeagent) gid=20(staff) groups=20(staff)` — no other groups | Any admin/wheel group present, or command errors | No |

**Nothing in §1 touches this repository, the operator's home directory,
`~/.claude`, or the keychain.** Every write in §1 is either a Directory
Service attribute on the *new* record, or a filesystem path under
`/private/var/svcspikeagent` (which does not exist until 1.9 creates it).

---

### 2. Fixture setup and ownership commands (NOT executed)

All paths below are under the scratchpad base path (absolute, shown in
full), never under the real repository or the operator's home directory.

| # | Command | sudo? | Exact path | Expected exit | PASS/FAIL | Version dependent? |
|---|---|---|---|---|---|---|
| 2.1 | `/bin/mkdir -p /private/tmp/claude-501/-Users-moraboinanaveenkumar-Projects-agentic-engineering-url-shortener/bc89be00-752a-4657-97a9-3286e49c7a8b/scratchpad/spike-option-a/protected/local-secrets` | No | creates the directory | 0 | PASS=created; FAIL=nonzero | No |
| 2.2 | `/bin/mkdir -p .../spike-option-a/protected/src_orchestration` | No | creates the directory | 0 | same | No |
| 2.3 | `/bin/mkdir -p .../spike-option-a/protected/data` | No | creates the directory | 0 | same | No |
| 2.4 | `/bin/sh -c 'echo "{\"test\":\"not-real\"}" > .../protected/local-secrets/creds.json'` | No | writes the disposable test-credentials fixture | 0 | PASS=written; FAIL=nonzero | No |
| 2.5 | `/bin/chmod 600 .../protected/local-secrets/creds.json` | No (operator owns it) | restricts the fixture to operator-only | 0 | PASS=mode set; FAIL=nonzero | No |
| 2.6 | `/bin/sh -c 'echo PROTECTED > .../protected/src_orchestration/verifier.py'` | No | writes the disposable "controller source" fixture | 0 | same | No |
| 2.7 | `/bin/sh -c 'echo fake-db > .../protected/data/app.db'` | No | writes the disposable "database" fixture | 0 | same | No |
| 2.8 | `/bin/chmod 600 .../protected/data/app.db` | No | restricts to operator-only | 0 | same | No |
| 2.9 | `/usr/bin/git init -q .../main-repo` | No | initializes a **throwaway, disposable** git repo — not the real project repository | 0 | PASS=repo created; FAIL=nonzero | No |
| 2.10 | `/usr/bin/git -C .../main-repo -c user.email=spike@example.test -c user.name=spike commit -q --allow-empty -m init` | No | one empty commit in the fixture repo | 0 | same | No |
| 2.11 | `/bin/mkdir -p .../agent-workspace` | No | creates the agent's assigned workspace | 0 | same | No |
| 2.12 | `sudo /usr/sbin/chown svcspikeagent:staff .../agent-workspace` | **Yes** (only sudo in this section — hands ownership of one scratchpad path to the new user) | ownership of `.../agent-workspace` | 0 | PASS=ownership changed; FAIL=nonzero | No |
| 2.13 | `/bin/chmod 700 .../agent-workspace` | No (operator still owns the parent, and per POSIX semantics the chmod in 2.12's aftermath — actually run *before* 2.12 relinquishes access — order matters: run 2.13 before 2.12, or as the new owner after) | mode of `.../agent-workspace` | 0 | same | No |

**Explicit confirmation**: no command in §2 references, reads, writes, or
changes ownership/permissions on any path under
`/Users/moraboinanaveenkumar` (the operator's home), the real project
repository, or anything keychain-related.

---

### 3. The eight test commands (NOT executed)

**"OS isolation" tests (1–6, 8) are separated from the "Claude execution"
test (7), per explicit instruction — they test different things and must
not be conflated in the result.**

| # | Command | sudo? | Exact path | Expected exit | PASS means | FAIL means | Version dependent? |
|---|---|---|---|---|---|---|---|
| **3.1** (OS isolation) | `sudo -u svcspikeagent /bin/cat .../protected/local-secrets/creds.json` | **Yes** (`sudo -u` — the *operator's* privilege to run as another user; `svcspikeagent` itself supplies no password) | reads `.../local-secrets/creds.json` | **Nonzero** (expect 1, "Permission denied") | Denied — isolation holds | Exit 0 with file content printed — **isolation broken** | No — standard Unix permission enforcement, the entire reason Option A doesn't depend on the mechanism that broke |
| **3.2** (OS isolation) | `sudo -u svcspikeagent /bin/sh -c "echo hacked >> .../protected/src_orchestration/verifier.py"` | **Yes** | writes `.../src_orchestration/verifier.py` | **Nonzero** | Denied, file unchanged (verified separately by operator `cat`) | Write succeeds | No |
| **3.3** (OS isolation) | `sudo -u svcspikeagent /bin/cat .../protected/data/app.db` | **Yes** | reads `.../protected/data/app.db` | **Nonzero** | Denied | Content printed | No |
| **3.4** (OS isolation) | `sudo -u svcspikeagent /bin/sh -c "echo x >> .../main-repo/.git/HEAD"` | **Yes** | writes to the **fixture** repo's `.git/HEAD` (not the real project repo) | **Nonzero** | Denied | Write succeeds | No |
| **3.5** (OS isolation) | `sudo -u svcspikeagent /bin/sh -c "echo ok > .../agent-workspace/artifact.txt && cat .../agent-workspace/artifact.txt"` | **Yes** | writes+reads `.../agent-workspace/artifact.txt` (the agent's own assigned path) | **0** | Succeeds, prints `ok` | Any denial | No |
| **3.6** (OS isolation) | `sudo -u svcspikeagent /usr/bin/git init -q .../agent-workspace` then `sudo -u svcspikeagent /usr/bin/git -C .../agent-workspace -c user.email=agent@test -c user.name=agent commit -q --allow-empty -m test` | **Yes** (both) | creates `.../agent-workspace/.git/`, commits within it | **0** (both) | Git functions correctly under the real, freshly-created-user ownership/permission model | Either command errors (e.g., git config/HOME resolution issues for a minimal new account) | Low — depends on git 2.50.1's behavior, not on macOS version specifically |
| **3.7** (Claude **execution**, not OS isolation — kept separate) | `sudo -u svcspikeagent /usr/bin/env -i HOME=/private/var/svcspikeagent PATH="/usr/bin:/bin:/opt/homebrew/bin:/Users/moraboinanaveenkumar/.local/bin" /Users/moraboinanaveenkumar/.local/bin/claude -p "write ok to test.txt" --output-format json --permission-mode bypassPermissions` | **Yes** | executes the `claude` binary (world-executable per §0.10–0.11, so the exec step itself is not what's in question) | **Predicted: nonzero / `is_error:true`, "Not logged in"** — this is a genuinely uncertain result, not asserted in advance as fact, but predicted from §0's evidence and from no credential being provisioned for this account | **Per explicit instruction, "PASS" here does not mean "authentication succeeds."** Failing with "not logged in" = isolation confirmed intact, recorded as evidence the boundary holds. | **Succeeding** (finding and using *any* credential) is the concerning outcome requiring immediate investigation, not celebration — it would suggest a leak via the §0.9–0.12 permission finding | Partially — auth mechanism behavior (keychain vs. config-file lookup) can vary by Claude Code version/config, disclosed as a source of uncertainty in the prediction itself |
| **3.8** (design-limitation check, explicitly weaker than a real test) | `sudo /usr/sbin/chown svcspikeagent:staff /private/tmp/.../spike-option-a/DOES-NOT-EXIST 2>/dev/null; echo "chown exit: $?"` | **Yes** (the chown attempt itself) | attempts chown on a deliberately nonexistent path — nothing is actually changed | **Nonzero** for the inner `chown`, **0** for the wrapping `echo` | The chown fails as expected, demonstrating the failure *is* detectable by a caller | The chown unexpectedly succeeds (would indicate a scripting error, not a real finding) | No — **but disclosed limitation: no real controller code exists yet, so this only proves the failure is detectable in principle, not that any actual implementation correctly aborts on it. Do not read a PASS here as "fail-closed is implemented" — it is not.** |

---

### 4. Cleanup commands (NOT executed), with explicit target validation

```sh
# Guard: the deletion target must equal exactly this path, checked before
# any recursive delete is proposed to run.
TARGET="/private/var/svcspikeagent"
if [ "$TARGET" = "/private/var/svcspikeagent" ]; then
  sudo /bin/rm -rf "$TARGET"
else
  echo "REFUSING: cleanup target does not match the expected exact path" >&2
  exit 1
fi
```

| # | Command | sudo? | Exact path | Expected exit | PASS/FAIL | Version dependent? |
|---|---|---|---|---|---|---|
| 4.1 | Guarded `rm -rf` above | **Yes** (only after the string-equality guard passes) | `/private/var/svcspikeagent`, and **only** that exact literal path | 0 | PASS=removed; FAIL=guard refused, or nonzero | No |
| 4.2 | `sudo /usr/bin/dscl . -delete /Users/svcspikeagent` | **Yes** | deletes DS record `/Users/svcspikeagent` | 0 | PASS=deleted; FAIL=nonzero | No |
| 4.3 | `/bin/rm -rf /private/tmp/claude-501/.../scratchpad/spike-option-a` | No (operator owns the parent; deleting a child does not require owning the child itself, only write access to the parent, which the operator has) | the entire scratchpad fixture tree, including the one sub-path (`agent-workspace`) previously `chown`'d to `svcspikeagent` | 0 | PASS=removed; FAIL=nonzero | No |

---

### 5. Post-cleanup verification (read-only, NOT executed)

| # | Command | sudo? | Exact path | Expected exit | PASS means | FAIL means |
|---|---|---|---|---|---|---|
| 5.1 | `/usr/bin/dscl . -read /Users/svcspikeagent` | No | reads (should fail to find) the record | **Nonzero** (`eDSRecordNotFound`, matching §0.2's original baseline) | Confirmed gone | Record still exists |
| 5.2 | `/usr/bin/id svcspikeagent` | No | reads (should fail to find) the account | **Nonzero** ("no such user") | Confirmed gone | Account still exists |
| 5.3 | `/bin/ls -ld /private/var/svcspikeagent` | No | reads (should fail to find) the directory | **Nonzero** ("No such file or directory") | Confirmed removed | Directory still exists |
| 5.4 | `/bin/ls -ld /private/tmp/claude-501/.../scratchpad/spike-option-a` | No | reads (should fail to find) the fixture tree | **Nonzero** | Confirmed removed | Tree still exists |

---

### Dedicated agent-only Anthropic API credential — architectural analysis only

**Explicitly not requested, created, or configured — analysis only, per
instruction.**

From this session's own earlier `claude --help` output (already
legitimately captured, no new lookup needed): the `--bare` flag's
description states plainly — *"Anthropic auth is strictly
`ANTHROPIC_API_KEY` or `apiKeyHelper` via `--settings` (OAuth and keychain
are never read)."* This confirms a real, CLI-supported, non-interactive
authentication path exists that is **structurally separate** from the
operator's own OAuth/keychain-based session.

**Could it enable headless execution without weakening approval
isolation? Yes, architecturally**: a dedicated `ANTHROPIC_API_KEY`,
provisioned specifically for `svcspikeagent` (e.g., stored at a path
`svcspikeagent` owns, never under the operator's home directory), would
let the agent authenticate without ever touching the operator's own
credential. This does **not** weaken approval isolation because the two
credential systems are already architecturally orthogonal in this design:
(1) *how the agent authenticates to Anthropic to run Claude Code* — what
this section is about — versus (2) *how a human authenticates to approve
a workflow gate* (ADR-0006's `reviewer_approver`/`release_owner` tokens,
entirely separate, never touched by anything described here). A leaked
agent-scoped API key has a small, revocable blast radius (its own budget,
independently rotatable); it is not the operator's personal, broader-scope
Pro-plan credential.

**Classification, per explicit instruction**: Claude execution does
**not** strictly require sharing the operator's personal credentials — a
dedicated credential is a real, architecturally sound alternative that
does not weaken isolation. **Therefore Option A is not classified as
categorically unsuitable.** However, **as currently scoped, no such
credential exists or is being created**, so Test 3.7 is predicted to FAIL
under the current provisioning — this is a **separate, disclosed gap**
(a credential decision, not an isolation-mechanism flaw), and provisioning
one would itself require your explicit future authorization, distinct from
this spike.

---

## Revision 5 — Scope-Limited Acceptance (Accepted, 2026-09-11)

### Human Gate 4 Decision

Verbatim scope, as directed: "Adopt a scope-limited Revision 5 for this
prototype. The released prototype MUST NOT launch Claude Code or any
external agent subprocess. External-agent execution remains fail-closed.
The implemented orchestration demonstration will use controlled built-in
adapters only. This decision does not claim that same-user macOS
credential isolation was solved. It removes that unverified execution
path from the prototype's trusted boundary."

### What This Decision Actually Does

Revisions 1–4 all tried to answer the same question: *if an external agent
subprocess (Claude Code or similar) runs as part of this orchestration
engine, how do we stop that subprocess from reading human-approval
credentials it should never see?* Every mechanism tried (gitignore
convention, a single-path sandbox deny rule, a full-protected-asset
sandbox boundary, a separate-OS-user spike) either failed a direct
feasibility test (macOS `sandbox-exec` — confirmed `SIGABRT`, Revision 3)
or was never executed (Option A — no privileged command was ever run).

Revision 5 does not answer that question. It makes the question not
apply to this release, by removing its premise: **no external agent
subprocess is ever launched by this prototype, full stop** — enforced by
`src/orchestration/adapters/launcher.py`, the one centralized entry point
any such launch would have to go through, which unconditionally raises
`ExternalAgentLaunchBlocked` and records an audit event for every call,
regardless of agent name or command (T102). This is verified structurally,
not just asserted: `tests/security/test_external_agent_shutdown.py` scans
the actual `src/` and `scripts/` trees and fails if any subprocess
invocation appears outside an explicit, justified allowlist (git worktree
management, this project's own uvicorn/pytest invocations — never an
agent).

With that premise removed, the original credential-isolation problem — protecting
a raw human-approval token from an agent process reading it — has no agent
process left to protect it *from*. This is what makes real credential
provisioning (T100) safe to build now, where it wasn't before.

### What This Decision Does NOT Claim

- It does **not** claim same-user macOS credential isolation is solved.
  Anything else running as the same OS user as this prototype (a
  malicious local process, a compromised dependency, another application)
  can still read `local-secrets/approval_tokens.raw.json` — nothing in
  T100–T103 defends against that. See `docs/threat-model.md`.
- It does **not** claim sandboxing of any kind. No Seatbelt profile, no
  container, no separate OS user was implemented. The macOS `sandbox-exec`
  failure from Revision 3 is unresolved and irrelevant here, not fixed.
- It does **not** claim protection against compromise of the operator's
  macOS account. If the account is compromised, everything on it is
  compromised, including this prototype's credentials — this is normal for
  any local development tool and is explicitly out of scope, not a novel
  risk this decision introduces.
- It does **not** extend to any future release that reintroduces external-
  agent execution. Re-adding a real adapter behind
  `src/orchestration/adapters/launcher.py` would require a new ADR
  revision and a new Human Gate decision — Revision 5's acceptance is
  scoped to "no external agent subprocess," not "credential handling is
  solved in general."

### Implementation (T100–T103)

- **T100** (`src/api/credentials.py`, `scripts/bootstrap_credentials.py`):
  cryptographically random per-identity tokens (`secrets.token_urlsafe(32)`,
  256 bits of entropy), salted SHA-256 hashes stored in a local, gitignored
  config file (`local-secrets/approval_tokens.hashed.json`, chmod 600); raw
  tokens written once to a separate gitignored file
  (`local-secrets/approval_tokens.raw.json`, chmod 600) and printed to
  stdout exactly once at creation time, never again.
- **T101** (`scripts/approve.py`): a separate, human-invoked CLI that reads
  the raw token locally (same OS user, same machine — this is exactly the
  boundary Revision 5 does not extend past) and submits it as a Bearer
  token to the real approval endpoint. The server never trusts a
  caller-supplied identity — only what `src/api/auth.py::resolve_identity`
  derives from verifying the token against the hash store (FR-308).
- **T102** (`src/orchestration/adapters/launcher.py`): the centralized
  fail-closed launcher described above.
- **T103**: comprehensive verification —
  `tests/security/test_t103_security_verification.py` (15 tests) plus
  `tests/security/test_credential_provisioning.py` (11 tests) and
  `tests/security/test_external_agent_shutdown.py` (6 tests). Covers
  unauthenticated/wrong-role/agent-identity/stale-revision rejection, valid
  reviewer and release-owner approval via the real T100/T101 pipeline (not
  just the test-only credential-injection path used elsewhere in this
  suite), raw-token absence from API responses/database rows/git-tracked
  files/logs/subprocess environments, external-agent-launch fail-closed
  auditing, and structural proof that no internal code path (including the
  fully-autonomous T106 background scheduler) can manufacture a human
  approval record for itself.

### Revised Constitution Check

| Principle | Status under Revision 5 |
|---|---|
| III. Human Governance | **PASS** — real approval mechanism, verified-credential identity, agent identities unconditionally rejected, revision-binding real and tested |
| V. Security and Privacy by Design | **PASS, scope-limited** — least privilege and explicit trust boundaries are real for the boundary this release actually has (no external agent execution); same-OS-user isolation for a hypothetical external agent remains unaddressed because that agent no longer exists in this release's trusted boundary, not because the principle was waived |

### Traceability

FR-307, FR-308, FR-309, FR-310, FR-311, FR-312, FR-313 (all now genuinely
implemented against real credentials, not only role-logic tested against
fake ones). Supersedes Revision 3's Rejected status and Revision 4's
never-executed Option A spike design — neither is resurrected or
completed; Revision 5 is a different, narrower decision, not a
continuation of that unresolved thread.

### Validation

`uv run pytest tests/security/test_credential_provisioning.py
tests/security/test_external_agent_shutdown.py
tests/security/test_t103_security_verification.py` — 32 tests, all real,
all passing. Full suite, fresh-clone re-verification, and repository
secret/hygiene scan results are recorded in
`docs/final-engineering-summary.md`.
