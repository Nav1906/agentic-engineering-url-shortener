# ADR-0009: Analytics Consistency, Counting Correctness, and Completeness Recovery

## Status

**Accepted** (Revision 3). Approved by the human candidate at Human Gate 4,
2026-09-10. Revision 3 (2026-09-10) superseded
Revision 2 after a further Human Gate 4 review found two defects in that
revision's core mechanism, not just its wording: (1) the "hard 20ms
fsync-with-abandon" timeout does not actually work — a synchronous OS write
call cannot be cancelled by an application-level timeout; timing out the
*wait* does not stop the *write*, which may still complete (or corrupt
partial state) after the code has already moved on. (2) Recording the count
**before** sending the response can durably record "a redirect was issued"
for a redirect that a subsequent crash prevented from ever being sent —
directly contradicting FR-105's own definition of the count ("reflects
only that this service issued the redirect response"), which Revision 2
misapplied its "not proof the destination page loaded" language to excuse.
This revision withdraws both the hard-timeout claim and the pre-response
ordering, and — per instruction — proposes the simplest conservative
redesign rather than adding new mechanism. **Any change to what the count
actually means, including the new system-wide integrity signal below,
requires your explicit specification approval — it is presented here as a
proposal, not a decided change to FR-107's contract.**

## Context

FR-105/106/107/115 require redirect availability to take priority over
analytics accuracy, with degradation observable and never silently
misreported as complete after recovery. Revision 2's WAL-file design
attempted to guarantee durability-before-response within a hard timeout;
neither half of that guarantee holds up: a blocking `fsync()` cannot be
safely abandoned from a single-threaded timeout without either leaking the
write or risking a torn/partial append, and recording intent before
confirmed transmission conflates "we decided to redirect" with "we actually
issued the redirect," which are different facts and only the second is what
FR-105 defines the count to mean.

## Decision Drivers

- Withdraw claims that don't hold under scrutiny rather than defend them.
- The count must reflect responses **actually issued**, not merely decided
  upon — closing the overcount path directly, not re-justifying it.
- No claimed timeout may block on a syscall it cannot actually cancel.
- Propose the **simplest** conservative design — reuse existing mechanisms
  (SQLite, ADR-0007's contention policy) rather than a second durability
  primitive, now that removing the pre-response ordering also removes the
  original reason (hot-path latency) for avoiding SQLite here.
- Explain, precisely, how uncertainty is detected and survives a restart —
  not asserted away.

## Options Considered

**A. Revision 2's pre-response WAL file with a hard-timeout abandon.**
- Disadvantages: **both defects above are confirmed, not stylistic** —
  superseded.

**B. Record the durability write *after* the response is sent (not before,
not in the same transaction as the lookup), directly in SQLite (no separate
WAL file), using ADR-0007's ordinary write-contention retry policy since
this step is no longer on the response-latency-sensitive path at all; detect
an unclean prior shutdown at startup and respond with a conservative,
system-wide integrity signal rather than guessing which specific short
codes might have been affected.**
- Advantages: **directly fixes the overcount defect** — nothing is counted
  that was not actually sent, by construction, since the write only happens
  after the send call returns; removes the unfixable hard-timeout claim
  entirely, since there is no longer any reason to bound this step tightly
  (the client already has their response); removes an entire second
  durability primitive (the WAL file) — a genuine simplification, not an
  addition, satisfying "avoid adding more infrastructure."
- Disadvantages: reopens a narrow window — if the process crashes between
  "response sent" and "write attempted," that specific event has **no
  record anywhere**, unlike Revision 2's (flawed) attempt to record it
  beforehand. This is now the central problem this ADR must answer
  honestly, not design around.
- Risks: without care, "no record" could be mistaken for "provably nothing
  happened" — addressed explicitly below (never infer `complete` from an
  empty backlog).
- Implementation impact: **lower** than Revision 2 (one fewer store, no
  custom timeout-cancellation logic that didn't work anyway).
- Assessment implications: a reviewer can force this exact crash window in
  a test and observe the honest, disclosed consequence — a real property to
  demonstrate, not a claimed guarantee that fails under inspection.

**C. Two-phase durability (e.g., pre-response "intent" write distinguished
from post-response "confirmed" write, reconciled by a background process)
to try to have both a pre-response record and no overcounting.**
- Disadvantages: this is the shape of a real fix, but it is meaningfully
  more infrastructure (a two-phase protocol, a reconciliation process
  distinguishing intent from confirmation) for a distinction (redirect
  latency variance in the tens-of-milliseconds range) the instruction
  explicitly asked not to over-engineer around. Rejected in favor of the
  simpler Option B, accepting Option B's narrow crash-window limitation as
  an honestly disclosed trade-off rather than engineering it away.

## Decision

**Option B.**

**Corrected request-time sequence**:
1. Look up the short link (read-only; FR-103, unrelated to analytics).
2. If valid and active: send the HTTP redirect response.
3. **After** the send call returns successfully: attempt, in its own SQLite
   transaction, to record the event — `INSERT INTO domain_analytics_outbox
   (event_id, short_code, redirected_at)` — subject to ADR-0007's ordinary
   bounded-retry/`busy_timeout` contention policy (no special-cased
   timeout; this step is off the hot path, so the general policy is
   sufficient and no bespoke mechanism is needed).
4. A background task (same process, triggered periodically and after each
   insert) drains undrained outbox rows into
   `domain_short_link_analytics_summary`, idempotently by `event_id` (an
   `applied_events(event_id) UNIQUE` check-and-insert in the same
   transaction as the count increment — unchanged pattern from Revision 1,
   now simply operating on data that arrives after the response instead of
   before).

**What this fixes, precisely**: no code path can record a count for a
redirect that was not actually sent — the write only happens after a
successful send. This directly satisfies FR-105 ("reflects only that this
service issued the redirect response") without needing to stretch its "not
proof the destination page loaded" clause to cover a different problem
(whether the response was issued at all).

**The remaining, honestly disclosed gap**: if the process crashes between
step 2 (response sent) and step 3 (write attempted or completed), that
event has no record in the outbox at all — not a `degraded` entry, not
anything. This cannot be eliminated without the two-phase machinery
rejected in Option C. It must instead be **detected in aggregate and
handled conservatively**, not silently absorbed.

**Detecting uncertainty across a restart (the actual answer to "how does
uncertainty survive restart")**: a single-row table,
`analytics_system_status (id=1, state, started_at, clean_shutdown_at)`, in
the **same SQLite database** as everything else (deliberately — see below
for why this matters). At process start: if the existing row shows
`state='running'` (i.e., no prior clean shutdown was ever recorded), the
**previous** process instance terminated uncleanly, and one or more
redirects **may** have been issued during its lifetime without a
surviving analytics record. The system cannot determine *which* short
codes were affected — no record exists for a lost event, by definition —
so the conservative response is **system-wide, not per-code**: set
`degraded_since_unclean_shutdown_at = <the detected prior state's
started_at>` (a durable, sticky field on the same status row), and expose
it via `/health`'s analytics sub-object (already planned) alongside every
per-code `completeness_status`. **Never inferred as cleared by an empty
outbox backlog** — an empty backlog after a restart proves nothing (the
lost events, if any, never reached the outbox at all, so there is nothing
for the backlog to show); only an explicit, audited operator
acknowledgment clears this system-wide flag, and clearing it never
retroactively asserts any specific short code's history was actually
complete — it only stops surfacing the general warning going forward.

**"What if both event storage and loss-marker storage fail?" — answered by
construction, not by a new mechanism**: `analytics_system_status` and
`domain_analytics_outbox`/`domain_short_link_analytics_summary` are **all
in the same SQLite database file**. There is no second store to fail
independently — if SQLite itself becomes unavailable, the *entire*
application is already in FR-109's general persistence-failure territory
(the domain package can't read/write short links either), which is a
whole-system concern this ADR does not need its own answer for. Keeping a
single store (rather than Revision 2's WAL-file-plus-SQLite split)
eliminates the asymmetric dual-failure question by removing the asymmetry,
not by adding a mechanism to handle it.

**Completeness status — three states retained, semantics tightened, no 4th
state added** (deliberately, to avoid adding to FR-107's "at least"
contract beyond what's necessary):
- `complete`: no undrained outbox rows for this short code, **and** no
  active `degraded_since_unclean_shutdown_at` flag is set system-wide.
- `degraded`: undrained outbox rows exist for this short code (drain is
  lagging) — self-heals to `complete` once drained, because the event
  genuinely was durably recorded (post-send) before this state was ever
  reported.
- `incomplete`: set when the post-send write **itself** observably fails
  (a caught SQLite error after exhausting ADR-0007's bounded retries) —
  this is a *known*, specific loss, distinct from the *unknown, aggregate*
  possibility the system-wide flag represents. Sticky, never auto-reverts.

**Contract addition — approved (Human Gate 4, 2026-09-10)**: the
system-wide `degraded_since_unclean_shutdown_at` signal was new relative to
FR-107's original "at least `complete` or `degraded`" per-short-code
contract; it is now **FR-117**, approved by the human candidate with these
explicit semantics: sticky after an unclean shutdown; operator
acknowledgment clears only the forward-looking warning, never historical
completeness; any short code already `incomplete` stays `incomplete` after
acknowledgment; historical uncertainty remains visible in analytics
evidence. It changes what "this short code shows `complete`" is allowed to
imply (it no longer implies "with certainty," only "with no known issue,
and no unresolved unclean-shutdown warning outstanding") — this semantic
shift is now part of the approved specification, not merely this ADR's
proposal. **The mechanism that implements it (this ADR overall) is now
also Accepted** (Human Gate 4, 2026-09-10) — the contract was approved
first, independently, as spec.md FR-117; the mechanism's acceptance
followed separately, not automatically from the contract's approval.

**Deduplication**: unchanged in mechanism from Revision 2 (`event_id`
uniqueness on the drain-apply step); client-level duplicate `GET` requests
remain intentionally undeduplicated, per FR-105's own definition (unchanged
disclosure from Revision 2).

## Rationale

Both defects Revision 2 had were attempts to guarantee something (a hard
timeout that cancels a blocking syscall; a pre-response record that
somehow doesn't overcount) that cannot actually be guaranteed without
either false claims or disproportionate machinery. The honest, simplest
fix is to stop claiming the guarantee, accept a narrow and disclosed
uncertainty window, and detect — rather than prevent — its aggregate
possibility across a restart.

## Consequences

- **Positive**: no code path can produce a false `complete` count for an
  unissued response (the overcount defect is closed); one fewer durability
  primitive than Revision 2; the restart-uncertainty question has a
  complete, honest answer instead of an implicit assumption.
- **Negative**: a narrow, genuine crash-window loss remains possible and is
  not engineered away — disclosed, not hidden, per the instruction to
  prefer honest disclosure over added infrastructure.
- **Operational**: no WAL file to rotate/manage (removed relative to
  Revision 2) — net operational simplification.
- **Testing**: the crash window (kill the process between response-send and
  outbox-write) is now a directly constructable, testable scenario with a
  defined expected outcome (an unclean-shutdown flag on next start), rather
  than a claimed-away edge case.
- **Governance**: the system-wide flag's set/clear transitions are audit
  events (FR-602); clearing it requires an authenticated operator action
  (reusing ADR-0006's approval mechanism, not a new one).

## Risks and Mitigations

- **Risk**: the system-wide flag is coarse — a single unclean shutdown
  degrades the *reported certainty* of every short code's status, even
  ones with no actual issue. **Mitigation**: this coarseness is the
  intentional, disclosed cost of not guessing at per-code attribution
  without evidence — a deliberate simplicity trade-off, not an oversight.
- **Risk**: an operator could clear the flag without genuinely
  investigating. **Mitigation**: the clearing action is audited with actor
  identity and rationale (reusing FR-310's approval-record fields), making
  a rubber-stamp clearing visible in the audit trail.

## Reversibility

**Moderate.** Reverting to a pre-response durability attempt would
reintroduce the overcount defect this revision exists to close — not
recommended regardless of ease.

## Traceability

- Requirements: FR-105, FR-106, FR-107, FR-115, FR-109, AMB-007.
- Specification sections: "Human Gate 3 Review" Clarifications entry for
  AMB-007; Planning Obligations.
- Plan sections: plan.md §2, §6.
- Related: ADR-0007 Revision 3 (the write-contention policy this ADR now
  relies on directly, with no bespoke exception).
- Prior review: Human Gate 4 findings, Rounds 1–2 (2026-09-10),
  `docs/governance/gate-4-review-2026-09-10.md`.
- Expected tasks: analytics task group.

## Validation

**Spike-verified (Human Gate 4, 2026-09-10;
`docs/governance/gate-4-spike-results-2026-09-10.md`, Spike 3 — real
SQLite DB, real forced write failures, real timing measurement; PASS on
all 9 scenarios)**: (b) the crash-window/unclean-shutdown scenario —
confirmed a fresh connection (simulating restart) correctly sets
`degraded_since_unclean_shutdown_at` from both the missing
`clean_shutdown_at` **and** an independent sentinel-file signal; (c)
empty-backlog-does-not-imply-complete — confirmed directly; a **new
scenario beyond the original plan**, explicitly requested at this
review round: the double-failure case (outbox write fails **and** the
loss-marker write also fails) — confirmed the design falls back to a
plain-file sentinel, independent of SQLite's own availability; also newly
confirmed: a durable running-marker gating request-serving, graceful
shutdown correctly refusing to mark itself clean while a sentinel/backlog
remains outstanding, and operator acknowledgment clearing the system-wide
flag **without** fabricating a `complete` status for any affected short
code — the specific property the instruction most emphasized ("operator
acknowledgment must not restore historical completeness"). (a) The
overcount scenario itself was not separately spiked as a standalone test
(the post-response ordering that prevents it is exercised implicitly by
every scenario above, since the write always occurs after a simulated
"response sent" point) — **not independently verified as its own test**,
disclosed rather than assumed covered. **FR-106's bounded-overhead
requirement**: exercised directly, not merely designed — a single real
write against the actual schema completed in 0.276ms, one data point well
under the proposed `PVT-001` (50ms) budget. **Corrected, per explicit
Human Gate 4 instruction**: a single spike measurement does not establish
a performance percentile (p95 or otherwise) — this is one sample under
uncontended, single-process, no-load conditions, not a load-representative
measurement. `PVT-001` is **provisionally approved as an implementation
target**, remaining explicitly labeled **unverified** until real
implementation-time tests measure it under representative conditions; the
0.276ms figure supports only "not obviously infeasible," nothing stronger.

**Still planned, not yet executed**: (d) the drain-worker
crash-and-reprocess deduplication test under real concurrent load (the
spike's `applied_events`-uniqueness logic was described and is consistent
with Spike 2's reconciliation pattern, but not separately re-executed
here); real multi-process concurrency and real disk-failure injection.
This spike establishes the protocol is sound against the specific failure
modes tested, in a single-process simulation — not that a full
implementation is bug-free, and not that this is fully verified.
