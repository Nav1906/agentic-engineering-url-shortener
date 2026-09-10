# ADR-0004: Short-Code Generation and Collision Handling

## Status

**Accepted.** Approved by the human candidate at Human Gate 4, 2026-09-10.

## Context

FR-102 requires short-code uniqueness among active codes at creation time.
FR-108 (resolved via AMB-001) requires that resubmitting the same destination
URL without an idempotency key always mints a **new, distinct** code — which
rules out any deterministic (hash-of-URL) scheme.

## Decision Drivers

- Must satisfy FR-102 (uniqueness) and FR-108 (non-determinism per URL).
- Must be safe under concurrent creation (FR-110).
- Should not leak operational information (e.g., creation volume/order) beyond
  what's acceptable for a prototype.
- Timebox: no external coordination service.

## Options Considered

**A. Random base62 string, 7 characters, insert-with-UNIQUE-constraint,
retry on collision (bounded).**
- Advantages: satisfies non-determinism (FR-108) trivially; no coordination
  needed across concurrent requests beyond the database's own UNIQUE
  constraint; collision probability negligible at prototype scale (~3.5
  trillion possible codes).
- Disadvantages: a (vanishingly rare) collision costs one wasted
  generate-and-fail-insert cycle.
- Risks: a pathological collision storm would exhaust the bounded retry —
  mitigated by the retry bound being generous relative to the actual
  collision probability, and by FR-403's requirement to reach a deterministic
  terminal outcome (a clear `503`-class error) rather than looping forever.
- Implementation impact: low — a small generator function plus a
  retry-on-`IntegrityError` loop.
- Assessment implications: reviewer can directly verify uniqueness via the
  database UNIQUE constraint, not just application logic.

**B. Sequential integer ID (auto-increment) encoded as base62.**
- Advantages: collision-free by construction; simplest possible generator.
- Disadvantages: reveals creation order and approximate volume to anyone who
  can compare two codes; couples code allocation to a single monotonically
  increasing counter, which becomes a (minor) write-contention point under
  concurrent creation; offers no benefit over Option A given FR-108 already
  requires non-determinism handling regardless of the ID scheme.
- Risks: none material, but no offsetting advantage over A either.
- Implementation impact: low.
- Assessment implications: neutral.

**C. Deterministic hash of the destination URL (+ salt).**
- Disadvantages: **directly contradicts FR-108** (same URL without a key must
  yield different codes on each submission) unless the salt is randomized per
  request — at which point it is no longer meaningfully different from Option
  A, just needlessly more complex (hashing instead of direct random
  generation).
- Rejected without further analysis.

## Decision

**Option A** — random base62, 7 characters, retry-on-collision bounded to 5
attempts, surfacing a `503`-class error if exhausted (which FR-403 requires be
a deterministic terminal outcome, not a hang).

## Rationale

Simplest scheme that satisfies both FR-102 and FR-108 without introducing
coordination infrastructure or leaking operational metadata through code
ordering.

## Consequences

- **Positive**: uniqueness is enforced at the database layer, not just in
  application logic — stronger correctness guarantee under concurrency.
- **Negative**: (negligible) wasted work on the rare collision.
- **Operational**: none beyond the generator function itself.
- **Testing**: a concurrency test can force a collision (e.g., by shrinking
  the code alphabet/length in a test-only configuration) to verify the
  retry-and-bounded-failure path is real, not just theoretical.
- **Governance**: none beyond this ADR.

## Risks and Mitigations

- **Risk**: retry-bound exhaustion under adversarial/malformed load.
  **Mitigation**: rate limiting (spec Security area, deferred to the security
  design within plan.md) reduces the practical likelihood of sustained
  collision-inducing load.

## Reversibility

**High.** The code-generation function is fully encapsulated; swapping the
scheme later (e.g., to Option B) touches one module and requires no data
migration for existing codes.

## Traceability

- Requirements: FR-102, FR-108.
- Specification sections: AMB-001 resolution (Clarifications, Session
  2026-09-10).
- Plan sections: plan.md §2 (URL Shortener Architecture).
- Expected tasks: domain-model, URL-shortening task groups.

## Validation

**Planned, not yet executed** (corrected at Human Gate 4 review): a unit test
asserting two consecutive creations for the same destination URL (no key)
produce different codes (FR-108), and a persistence test confirming the
UNIQUE constraint actually rejects a forced duplicate insert (FR-102). Not
merely asserted in prose once run — but not yet run.
