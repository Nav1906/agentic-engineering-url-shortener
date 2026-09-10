# Quickstart: Governed Agentic URL Shortener

**Status**: This guide describes the **planned** run/verify flow for a system
that has not been implemented yet (Human Gate 4 pending, no code exists). It
is written now so that `/speckit-implement` has a concrete, agreed target and
so a reviewer's expectations are set in advance — every command below will
become real during implementation, not before.

Full schemas: [contracts/openapi.yaml](./contracts/openapi.yaml). Full
persisted-entity detail: [data-model.md](./data-model.md). Architecture
rationale: [docs/adr/](../../docs/adr/) (all Proposed, pending Human Gate 4).

## Prerequisites

- Python 3.12+ (ADR-0002)
- `uv` (already required by this repository's SpecKit tooling)
- No external services, no Docker, no cloud account (ADR-0003, ADR-0010)

## Setup (planned)

```bash
git clone <repo-url> && cd agentic-engineering-url-shortener
uv sync                                   # installs pinned dependencies (ADR-0002)
uv run scripts/bootstrap_credentials.py   # generates local approver credentials (ADR-0006)
uv run uvicorn app.main:app --reload      # starts the app on http://localhost:8000
```

## Run the test suite

```bash
uv run pytest                 # unit, contract, integration, orchestration, security tests
uv run mypy src/               # static type check (ADR-0002, advisory gate)
```

**Expected outcome**: all tests pass; the actual pass/fail output is the
evidence retained per FR-606 — this quickstart does not itself claim tests
pass, only documents the command that produces that evidence.

## Golden-path validation: URL shortener domain

```bash
# 1. Create a short link
curl -s -X POST http://localhost:8000/short-links \
  -H "Content-Type: application/json" \
  -d '{"destination_url": "https://example.com/some/long/path"}'
# Expected: 201, { "short_code": "...", "idempotent_replay": false, ... } (FR-101, FR-102)

# 2. Resolve it
curl -sI http://localhost:8000/short-links/<short_code>   # replace with the actual path per contract
# Expected: 302 redirect to the destination_url (FR-103)

# 3. Check analytics
curl -s http://localhost:8000/short-links/<short_code>/analytics
# Expected: successful_redirect_count: 1, completeness_status: "complete" (FR-105, FR-107)

# 4. Reject an invalid URL
curl -s -X POST http://localhost:8000/short-links \
  -H "Content-Type: application/json" \
  -d '{"destination_url": "javascript:alert(1)"}'
# Expected: 400 (FR-101 negative path)
```

## Idempotency validation (AMB-001, FR-112/113)

```bash
curl -s -X POST http://localhost:8000/short-links \
  -H "Content-Type: application/json" -H "Idempotency-Key: demo-key-1" \
  -d '{"destination_url": "https://example.com/a"}'
# repeat the identical request — expect the same short_code, idempotent_replay: true
curl -s -X POST http://localhost:8000/short-links \
  -H "Content-Type: application/json" -H "Idempotency-Key: demo-key-1" \
  -d '{"destination_url": "https://example.com/DIFFERENT"}'
# Expected: 409 (FR-113 — same key, different payload)
```

## Orchestration workflow validation (FR-201–FR-206)

```bash
# 1. Ingest a requirement
curl -s -X POST http://localhost:8000/workflows \
  -H "Content-Type: application/json" \
  -d '{"requirement": "demo requirement", "scenario": "greenfield"}'
# Expected: 201, a workflow id and initial stage graph (FR-201)

# 2. Inspect it mid-flight
curl -s http://localhost:8000/workflows/<workflow_id>
# Expected: stages with explicit status, dependency edges, decision lineage (FR-204, FR-206)
```

## Human approval demonstration (FR-301–FR-313)

```bash
# Approve (using the generated reviewer/approver credential, never the raw
# token pasted into an agent session — see ADR-0006)
uv run scripts/approve.py --workflow <workflow_id> --gate requirements_approval --role reviewer_approver
# Expected: 200, ApprovalDecision recorded with identity/role/rationale/revision (FR-310)

# Negative test: attempt release with only the reviewer_approver credential
uv run scripts/approve.py --workflow <workflow_id> --gate release_readiness --role reviewer_approver
# Expected: 403 — a reviewer identity cannot authorize release (FR-312/FR-313, AMB-003)
```

## Retry / safe-stop demonstration (FR-401–FR-406)

Documented in the reliability test suite (`tests/reliability/`, planned) —
forces a transient failure via a test-only fault-injection flag and asserts
the bounded-retry-then-recover path, and separately forces retry exhaustion
with no fallback to assert `safe_stopped`. See ADR-0007 for the exact numbers
proposed for this policy.

## Analytics failure-isolation demonstration (AMB-007, ADR-0009 Rev. 3)

Documented in `tests/analytics/` (planned) — three scenarios:
1. Forces the analytics drain worker down, redirects through it (expect
   302, not blocked — the durability write happens *after* the response is
   sent, so drain-worker health never gates the redirect), observes
   `completeness_status: degraded`, restores the worker, observes it heal to
   `complete`.
2. Forces the post-send outbox write itself to fail (e.g., a forced SQLite
   error), confirms `completeness_status: incomplete` **does not** revert
   after the underlying issue resolves.
3. Kills the process between "response sent" and "outbox write attempted,"
   restarts it, and confirms `/health`'s
   `analytics.degraded_since_unclean_shutdown_at` becomes set — and that an
   empty outbox backlog alone does **not** clear it or imply `complete`.

## Three required scenarios

- **Greenfield**: `scripts/demo_greenfield.py` (planned) — submits a
  well-defined requirement and shows it proceeding without a forced
  clarification gate (Scenario A, spec.md).
- **Brownfield**: `scripts/demo_brownfield.py` (planned) — submits a change
  against the already-running system and shows the impact-analysis gate
  blocking implementation until reviewed (Scenario B).
- **Ambiguous requirement**: `scripts/demo_ambiguous.py` (planned) — submits
  a deliberately incomplete requirement and shows detection, suspension, and
  governed resumption after a recorded human decision (Scenario C).

## Reliability and audit metrics

```bash
curl -s http://localhost:8000/metrics/reliability
# Expected: demonstration_data: true always; mttr_seconds null until a
# recovered-failure event exists (ADR-0008); unrecovered_failure_count
# reported separately, never folded into mttr_seconds.
```

## Reset

```bash
rm -f data/app.db*      # deletes all persisted state; re-run bootstrap to start clean
```
