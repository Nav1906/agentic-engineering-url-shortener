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

## Human approval -- real, end-to-end (ADR-0006 Revision 5, 2026-09-11)

```bash
uv run python3 scripts/bootstrap_credentials.py
# Real: prints two role-specific tokens (alice/reviewer_approver,
# bob/release_owner) exactly once. Write them down -- there is no
# read-back command.

uv run python3 scripts/approve.py --identity alice --workflow <workflow_id> \
  --gate requirements_approval --decision approve --rationale "looks complete"
# Real: 200, an ApprovalDecision JSON body (identity: "alice",
# role: "reviewer_approver", decision: "approved").

curl -s -X POST http://localhost:8000/workflows/<workflow_id>/gates/requirements_approval/approve \
  -H "Authorization: Bearer whatever-token"
# Real: still 401 for any token that wasn't actually provisioned --
# fail-closed remains the default for anything other than a real,
# bootstrapped token (src/api/auth.py::resolve_identity).
```

**Scope of this decision, stated plainly (docs/threat-model.md)**: this
prototype permanently excludes external-agent subprocess execution from
its trusted boundary (`src/orchestration/adapters/launcher.py` always
fails closed, T102) -- that is what makes a real credential-provisioning
path safe. This does **not** claim same-user macOS credential isolation is
solved: anything else running as the same OS user as this prototype can
still read `local-secrets/approval_tokens.raw.json` directly. Do not
represent this as sandboxing or as protection against operator-account
compromise -- see `docs/threat-model.md` for the exact, disclosed boundary.

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

## Not yet implemented / explicitly out of scope

As of 2026-09-11, all 106 tasks in `tasks.md` are complete (T100–T103
unblocked and implemented under ADR-0006 Revision 5; T104–T106 closed the
remaining engineering gaps). What remains is genuinely, permanently out of
scope for this release, not merely undone:

- **External-agent subprocess execution** (Claude Code or any other agent)
  -- permanently excluded by Human Gate 4 decision (ADR-0006 Revision 5),
  not a temporary gap. `src/orchestration/adapters/launcher.py` always
  fails closed; see `docs/threat-model.md`.
- **Same-OS-user credential isolation** -- explicitly not solved and not
  claimed to be; see `docs/threat-model.md`.

See `docs/final-engineering-summary.md` §19 for the full, current
disposition, including the small set of legitimately-deferred,
never-mandatory items (egress restriction, DNS-rebinding protection,
tamper-evident audit log, containerized deployment).

## Reset

```bash
rm -rf data/   # deletes all persisted state; re-run to start clean
```
