# Reliability Summary

**Purpose**: one of the 13 required `/speckit-converge` outputs (guide
Section 22). Consolidates reliability/recovery content already documented
in [final-engineering-summary.md §11–§13](final-engineering-summary.md)
into a single reviewable artifact — cross-referenced, not duplicated.
**Generated**: 2026-09-11, during the convergence pass.

## Failure classes and recovery mechanics

| Mechanism | Specification | Evidence |
|---|---|---|
| Retry ceiling / backoff | Exactly 3 attempts, 2 waits (1s, 2s) | `src/orchestration/retry_policy.py`, `tests/orchestration/test_backoff_timing.py` |
| Per-subprocess timeouts | Distinct value per type: internal 5s, pytest 300s, Claude 600s | `tests/orchestration/test_subprocess_timeouts.py` |
| Retry gating | Never issued blind — gated on prior effect reconciliation | `reaper.py`, `tests/orchestration/test_retry_safety.py`, `test_reconciliation.py` |
| Fallback / safe-stop on exhaustion | Deterministic: fallback path if one exists, else safe-stop | `tests/orchestration/test_fallback.py`, `test_safe_stop.py` |
| Rollback vs. compensation | Rollback claimed only where transactionally feasible; compensation used for externally-observed effects | `tests/orchestration/test_rollback_compensation.py` |
| Safe-stop resume | Resumable only via an explicit, separately-invoked function — no automatic resume path anywhere in the module | `tests/orchestration/test_safe_stop_resume.py` |
| Stale-worker / crash recovery | Lease-based periodic reaper detection; `recover_on_startup` wired into the app lifespan (T106) so it runs before the live scheduler starts | `reaper.py`, `tests/orchestration/test_reaper_periodic.py`, `tests/persistence/test_restart_recovery.py` |
| Dynamic replanning / invalidation | Invalidates exactly the affected downstream artifacts/approvals — no broader, no narrower | `replanning.py`, `tests/orchestration/test_replanning_cascade.py`, `test_replan_worktree_invalidation.py` |
| Atomic claiming under concurrency | Compare-and-swap claim, proven under real concurrent threads | `scheduler.py`, `tests/orchestration/test_atomic_claim.py` |
| SQLite write-contention handling | `busy_timeout` + bounded retry on every writer path (domain, orchestration, audit, analytics drain) | `src/persistence/` |
| Analytics durability under crash | Sticky `degraded_since_unclean_shutdown_at` flag; acknowledgment clears only the forward-looking warning, never historical per-code `completeness_status` | `tests/analytics/test_unclean_shutdown.py` (5 tests), `test_completeness_status.py`, `test_ordering.py` |

## MTTR definition and measurement

Population is **recovered events only** — an audit event whose
`recovery_of_event_id` points at the failure it resolves. Unrecovered
failures are counted separately and never blended into the MTTR figure.
`src/observability/metrics.py::compute_mttr_seconds`,
`tests/observability/test_mttr.py` (4 tests: no-failures, single-recovered,
unrecovered-excluded, mixed). **No numeric MTTR target is proposed** — a
target requires this definitional work to exist first (it now does), but
proposing a number was explicitly out of scope for this timebox (Human
Gate 3 correction, recorded in `spec.md`). `/metrics/reliability` always
sets `demonstration_data: true` — never presented as a production
statistic (`tests/contract/test_metrics.py`).

## Reliability test inventory

`uv run pytest tests/orchestration/` — 66 passed.
`uv run pytest tests/analytics/` — covered in the full-suite count.
`uv run pytest tests/observability/` — MTTR + audit + correlation tests.

## Residual reliability risks (disclosed)

- Reaper detection is periodic, not instantaneous — a stale lease is
  detected on the next sweep, not the instant a worker dies. Bounded, not
  eliminated.
- No cross-process/cross-machine failover — this is a single local
  process by design (ADR-0010); reliability claims are scoped to
  within-process crash/restart recovery, not multi-node HA.
- Compensation, not true rollback, is used for any externally-observed
  effect — by design, since true rollback is infeasible for those effect
  classes, not an oversight.
