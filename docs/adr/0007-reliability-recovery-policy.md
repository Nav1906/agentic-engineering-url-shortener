# ADR-0007: Retry, Timeout, Fallback, Rollback/Compensation, Safe-Stop, and Write-Contention Policy

## Status

**Accepted** (Revision 3). Approved by the human candidate at Human Gate 4,
2026-09-10. Revision 3 (2026-09-10) corrected two
defects a further Human Gate 4 review round found: (1) Revision 2 claimed an
in-band exception was automatically safe to retry without reconciliation —
wrong, since a side effect can precede the exception; (2) "3 attempts with
backoff 1s/2s/4s" miscounted — 3 attempts have exactly 2 intervening waits,
not 3. Both corrected below, alongside more realistic subprocess timeouts
requested at the same review round. **Numeric values remain proposals
requiring your approval.**

## Context

Unchanged core requirements (FR-401–FR-406). ADR-0005 Revision 3 now
requires reconciliation before any retry of an `externally_observable_
uncertain` stage, triggered by **exception, timeout, or stale lease alike**
— this ADR's retry description must match that, not the narrower Revision 2
claim.

## Decision Drivers (unchanged, plus)

- "Safe to retry" must be defined identically in this ADR and ADR-0005 —
  no daylight between them on what counts as reconciled.
- Backoff/attempt counts must be arithmetically consistent when stated.
- Per-attempt timeouts must reflect the actual subprocess being bounded — a
  Claude Code invocation and a full `pytest` run are not 5–10 second
  operations, and proposing numbers that pretend otherwise is not a
  credible policy.

## Options Considered

Write-contention options unchanged from Revision 2 (Option A — `busy_timeout`
+ bounded retry, reusing the existing retry mechanism — remains superior to
a bespoke write-serialization queue, for the same reasons already recorded).

## Decision

**Retry safety, corrected (aligned with ADR-0005 Revision 3)**: a retry is
issued for a stage execution **only** when one of the following holds:
- The stage's `effect_class` is `idempotent` (safe regardless of when a
  failure occurred, including mid-effect).
- The stage's `effect_class` is `externally_observable_uncertain` **and**
  ADR-0005's `check_effect()` reconciliation has returned `not_completed` —
  required after **any** non-success outcome for such a stage: an exception
  raised during `execute()`, a timeout, or a stale/expired lease. **Revision
  2's claim that an in-band exception alone was safe to retry without this
  check is withdrawn** — a side effect can occur before the exception that
  reports it, and an exception's presence says nothing about which side of
  that boundary the failure fell on. If `check_effect()` returns `unknown`,
  the stage goes to `awaiting_reconciliation` (ADR-0005), never a blind
  retry and never a blind failure.

**Failure classification**: unchanged — transient vs. permanent, per
operation type.

**Retry ceiling and backoff, corrected (`PVT-002`, proposed)**: maximum
**3 attempts**, with exactly **2 intervening waits**: **1 second** after
attempt 1, **2 seconds** after attempt 2 (attempt 1 → wait 1s → attempt 2 →
wait 2s → attempt 3 → done). The prior "1s/2s/4s" description implied a
4th attempt or miscounted the interval-to-attempt relationship; this is the
corrected, arithmetically consistent statement of the same intended
ceiling. **Still proposed, not approved.**

**Per-attempt timeouts, corrected and split by realistic subprocess type
(`PVT-003`, proposed — revised numbers)**:
- **Internal, in-process/database operation** (e.g., a domain write, a
  claim statement): **5 seconds** — unchanged from Revision 2, still
  realistic for this class.
- **`pytest` subprocess (Testing adapter)**: **300 seconds (5 minutes)** —
  Revision 2's "10 seconds for external-dependency-simulating" was not
  written with an actual test suite in mind; a real suite covering
  FR-101–FR-606's breadth will not complete in 10 seconds.
- **Claude Code subprocess (Implementation/Documentation/Architecture-
  Design/Task-Decomposition/Checklist/Analyze adapters, ADR-0005)**:
  **600 seconds (10 minutes)** — a real agent invocation performing file
  edits and its own tool calls is not bounded by a single-digit-second
  timeout; proposing one would either be routinely exceeded (defeating the
  point of a timeout) or would require the adapter to lie about its own
  bound.
- All three remain **proposed**, not approved — explicitly flagged as
  needing your confirmation given how consequential they are to whether the
  system can do real work at all within its own reliability policy.

**Exhaustion → terminal outcome**: unchanged — `failed_permanent` →
fallback if defined, else `safe_stopped`.

**Rollback vs. compensation**: unchanged from Revision 2.

**Write-contention policy**: unchanged from Revision 2 — `PRAGMA
busy_timeout = 2000` (2s) baseline, every writer path wraps its transaction
in this ADR's bounded-retry policy treating `SQLITE_BUSY`/`SQLITE_LOCKED` as
transient. **Terminology correction**: SQLite **serializes writes** under
its single-writer lock — it does not provide concurrent row-level writers;
WAL mode's concurrency benefit is for **readers** running alongside the one
writer, not for multiple simultaneous writers. This policy's job is to
handle write *attempts* arriving concurrently and being safely serialized
with bounded waiting, not to claim SQLite parallelizes writes.

**Safe-stop**: unchanged from Revision 2 (including the
`awaiting_reconciliation`-exhaustion trigger).

## Rationale

Both corrections remove a false safety claim rather than adding new
mechanism — the fix is definitional precision (what counts as "safe to
retry," what the numbers actually mean), which is exactly the kind of
bounded correction this round calls for, not new infrastructure.

## Consequences

- **Positive**: "safe to retry" is now identically defined in this ADR and
  ADR-0005, with no gap for a side-effecting-then-exceptioning stage to fall
  through uncaught.
- **Negative**: realistic Claude/test timeouts (10 minutes, 5 minutes) mean
  a genuinely stuck stage takes materially longer to reach `safe_stopped`
  than Revision 2's numbers implied — an honest trade-off, not one to hide.
- **Operational**: unchanged.
- **Testing**: a new test specifically covers "exception after side effect"
  for an `externally_observable_uncertain` stage, asserting reconciliation
  runs rather than an immediate blind retry.
- **Governance**: unchanged.

## Risks and Mitigations

- **Risk**: 10-minute/5-minute timeouts mean a demonstration run could take
  a long time to reach a terminal state if something is genuinely stuck.
  **Mitigation**: this is the honest cost of realistic numbers; a shorter
  demo-specific override remains available the same way the approval-gate
  timeout already has a separate, shorter demo-script value (plan.md §5).

## Reversibility

**High** for all numeric parameters. **Moderate** for the retry-safety
semantics (coupled to ADR-0005, as in Revision 2).

## Traceability

- Requirements: FR-401–FR-406, FR-109, FR-110.
- Specification sections: `PVT-002`, `PVT-003`.
- Plan sections: plan.md §6.
- Related: ADR-0005 Revision 3 (reconciliation triggers), ADR-0009 (analytics
  write-contention handling, now on the normal path per that ADR's own
  revision).
- Prior review: Human Gate 4 findings, Rounds 1–2 (2026-09-10),
  `docs/governance/gate-4-review-2026-09-10.md`.
- Expected tasks: retry-and-timeout, fallback, rollback-or-compensation,
  safe-stop task groups.

## Validation

**Planned, not yet executed** (no code exists yet): the Revision 2 retry/
timeout/safe-stop tests, plus (a) a new "exception after side effect"
reconciliation test; (b) a backoff-timing test asserting exactly two waits
(1s, 2s) across three attempts; (c) a contention test per writer path
asserting bounded retry then observable failure, never a hang. When
executed, output will be retained as evidence.
