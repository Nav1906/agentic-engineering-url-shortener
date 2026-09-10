# Quickstart: Governed Agentic URL Shortener

**Status**: Reconciled from "planned" to real, executed commands during
`/speckit-implement` (2026-09-10). Every command below has actually been run
against real code in this repository — see the commit history for the exact
`pytest`/`mypy`/`ruff` output each change was verified against. Sections
still describing planned-but-not-yet-built behavior are labeled **(not yet
implemented)** explicitly, never left ambiguous.

Full schemas: [contracts/openapi.yaml](./contracts/openapi.yaml). Full
persisted-entity detail: [data-model.md](./data-model.md). Architecture
rationale: [docs/adr/](../../docs/adr/) (9 of 10 Accepted; ADR-0006 remains
Rejected — see below).

## Prerequisites

- `uv` (installs and pins Python 3.12 automatically — no separate Python
  install needed; this repo's `.python-version` pins 3.12)
- No external services, no Docker, no cloud account (ADR-0003, ADR-0010)

## Setup

```bash
git clone <repo-url> && cd agentic-engineering-url-shortener
uv sync                                   # installs pinned dependencies (ADR-0002), real
uv run uvicorn src.api.main:app --reload  # starts the app on http://localhost:8000
```

`uv run scripts/bootstrap_credentials.py` from the original plan is **not
run here** — that script, and `scripts/approve.py`, remain explicitly
**BLOCKED** (tasks.md T100/T101) pending an accepted replacement for
ADR-0006's still-Rejected credential-isolation mechanism. See "Human
approval" below for what is and isn't currently possible as a result.

## Run the test suite

```bash
uv run pytest tests/ -v        # real: 159 passed as of this reconciliation
uv run mypy src/                # real: Success, no issues found in 40 source files
uv run ruff check src/ tests/   # real: All checks passed
uv run --with openapi-spec-validator openapi-spec-validator \
  specs/001-governed-url-shortener/contracts/openapi.yaml   # real: OK
```

## Golden-path validation: URL shortener domain

```bash
bash scripts/smoke.sh   # real: runs a live server and exercises the full
                         # golden path below in one command; also runnable
                         # step by step:

curl -s -X POST http://localhost:8000/short-links \
  -H "Content-Type: application/json" \
  -d '{"destination_url": "https://example.com/some/long/path"}'
# Real: 201, { "short_code": "...", "idempotent_replay": false, ... } (FR-101, FR-102)

curl -sI http://localhost:8000/<short_code>
# Real: 302 redirect to the destination_url (FR-103)

curl -s http://localhost:8000/short-links/<short_code>/analytics
# Real: successful_redirect_count: 1, completeness_status: "complete" (FR-105, FR-107)
# (the count updates shortly after the redirect response — it's written by
# a FastAPI BackgroundTask strictly after the response is sent, ADR-0009)

curl -s -X POST http://localhost:8000/short-links \
  -H "Content-Type: application/json" \
  -d '{"destination_url": "javascript:alert(1)"}'
# Real: 400 (FR-101 negative path)

curl -s -X DELETE http://localhost:8000/short-links/<short_code>
# Real: 204
```

## Idempotency validation (AMB-001, FR-112/113)

```bash
curl -s -X POST http://localhost:8000/short-links \
  -H "Content-Type: application/json" -H "Idempotency-Key: demo-key-1-min-16-chars" \
  -d '{"destination_url": "https://example.com/a"}'
# repeat the identical request -- real: same short_code, idempotent_replay: true

curl -s -X POST http://localhost:8000/short-links \
  -H "Content-Type: application/json" -H "Idempotency-Key: demo-key-1-min-16-chars" \
  -d '{"destination_url": "https://example.com/DIFFERENT"}'
# Real: 409 (FR-113 -- same key, different payload)
```

## Orchestration workflow validation (FR-201–FR-206)

```bash
curl -s -X POST http://localhost:8000/workflows \
  -H "Content-Type: application/json" \
  -d '{"requirement": "demo requirement", "scenario": "greenfield"}'
# Real: 201, a workflow id (FR-201)

curl -s http://localhost:8000/workflows/<workflow_id>
# Real: stages, dependency edges (depends_on), decision lineage (FR-204, FR-206)

curl -s http://localhost:8000/workflows/<workflow_id>/audit-events
curl -s http://localhost:8000/workflows/<workflow_id>/policy-evaluations
# Real: both implemented (src/api/routers/workflow_evidence.py)
```

The full DAG mechanics (parallel dispatch, atomic claiming, reaper,
reconciliation, retry/fallback/safe-stop, replanning) are exercised by
`src/orchestration/` directly, not yet wired to a stage-execution HTTP
trigger endpoint -- see `tests/orchestration/` for real, passing evidence
of every one of these mechanisms (eligibility, parallel sync, atomic claim
under concurrency, reaper, reconciliation, retry-safety, backoff timing,
subprocess timeouts, fallback, rollback/compensation, safe-stop + resume,
replanning cascade, worktree invalidation).

## Human approval -- fail-closed by design (ADR-0006 unresolved)

```bash
curl -s -X POST http://localhost:8000/workflows/<workflow_id>/gates/requirements_approval/approve \
  -H "Authorization: Bearer whatever-token"
# Real: 401 unauthenticated -- ALWAYS, in a genuine deployment of this code,
# because no credential-provisioning path is wired (T100/T101 remain
# BLOCKED). This is deliberate fail-closed behavior, not a bug -- see
# src/api/auth.py's module docstring and tasks.md T066.
```

The role/revision-binding logic itself (which role a gate requires, FR-313's
wrong-gate rejection, FR-310's required fields) is real and tested via
`tests/contract/test_approvals.py`, using a TEST-ONLY credential-registration
helper never reachable from application code -- see that file's own
docstring for why this doesn't contradict the fail-closed claim above.

## Retry / safe-stop demonstration (FR-401–FR-406)

Real, passing evidence in `tests/orchestration/test_retry_safety.py`,
`test_backoff_timing.py`, `test_subprocess_timeouts.py`, `test_fallback.py`,
`test_rollback_compensation.py`, `test_safe_stop.py`,
`test_safe_stop_resume.py` -- exactly 3 attempts / 2 waits (1s, 2s),
per-subprocess timeouts (5s/300s/600s), retry gated on reconciliation,
deterministic fallback-or-safe-stop, and safe-stop resumable only via an
explicit call.

## Analytics failure-isolation demonstration (AMB-007, ADR-0009 Rev. 3)

Real, passing evidence in `tests/analytics/`:
`test_unclean_shutdown.py` proves the sticky `degraded_since_unclean_shutdown_at`
flag is set on crash-window detection, stays sticky across repeated crashes,
and that acknowledging it clears only the forward-looking warning -- never
historical per-code `completeness_status`, which stays `incomplete` forever
once set. `test_completeness_status.py` proves the one-way `incomplete`
transition. `test_ordering.py` proves the overcount defect this design
exists to prevent cannot occur (no enqueue == no count).

## Three required scenarios

```bash
uv run python3 scripts/demo_greenfield.py    # real: SCENARIO A (GREENFIELD) PASSED
uv run python3 scripts/demo_brownfield.py    # real: SCENARIO B (BROWNFIELD) PASSED
uv run python3 scripts/demo_ambiguous.py     # real: SCENARIO C (AMBIGUOUS) PASSED
```

Each script's own module docstring discloses its pre-selected input/change
and, for the ambiguous scenario, an explicit limitation: the clarification
decision is recorded via decision-lineage/audit directly rather than
through the real (fail-closed) approval endpoint, since faking a credential
there would misrepresent what this system currently does.

## Reliability and audit metrics

```bash
curl -s http://localhost:8000/metrics/reliability
# Real: demonstration_data: true always; mttr_seconds null until a
# recovered-failure event exists (ADR-0008); unrecovered_failure_count
# reported separately, never folded into mttr_seconds.
```

## Not yet implemented (disclosed, not silently dropped)

- `scripts/bootstrap_credentials.py`, `scripts/approve.py`, `local-secrets/`
  setup, and a final agent-isolation launcher -- all explicitly BLOCKED
  (tasks.md T100–T103) pending an accepted ADR-0006 replacement.
- Executable postcondition validators with retained artifact-hash evidence
  (T062) and isolated per-execution `git worktree`s with controller-only
  promotion (T061) -- the DAG/reconciliation/replanning mechanics that
  don't depend on these are real and tested; these two specific ADR-0005
  refinements are not yet built.
- A stage-execution HTTP trigger wiring the orchestration engine's DAG
  mechanics to actually run against a submitted requirement end-to-end via
  the API (currently exercised directly via `src/orchestration/` in tests
  and the three scenario scripts, not yet via a single HTTP call).
- The broader test-suite sweep groups (T087, T088, T090 as literal 1:1 full
  "sweep" tasks distinct from the many real tests already in
  `tests/unit/contract/orchestration/...`), the Final Engineering Summary,
  Reviewer Navigation Guide, and Traceability Matrix documents (T097–T099).

## Reset

```bash
rm -rf data/   # deletes all persisted state; re-run to start clean
```
