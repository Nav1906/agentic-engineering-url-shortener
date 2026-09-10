# ADR-0010: Deployment and Local Execution Model

## Status

**Accepted.** Approved by the human candidate at Human Gate 4, 2026-09-10.

## Context

Spec Constraints require the system to "run locally in a demonstrable,
reviewable way" with no hosted/cloud deployment assumed. A reviewer must be
able to go from a fresh clone to a running, testable system quickly.

## Decision Drivers

- Minimize setup steps for an unfamiliar reviewer.
- No external infrastructure dependency (consistent with ADR-0001/0003).
- Must support the quickstart guide's "prerequisites, setup commands, test/run
  commands, expected outcomes" structure directly.

## Options Considered

**A. Plain local process: `uv run uvicorn app.main:app`, SQLite file created
on first run, no containerization.**
- Advantages: fewest possible prerequisites (just Python + `uv`, already
  established in this repository's own SpecKit tooling); fastest path from
  clone to running; matches how this repository has already been operated
  (`uv tool install`, no Docker anywhere so far).
- Disadvantages: relies on the reviewer's local Python environment matching
  expectations — mitigated by pinning the Python version and dependencies via
  a lockfile.
- Risks: none material.
- Implementation impact: minimal.
- Assessment implications: fastest reviewer path — directly serves the
  guide's "reviewer navigation" and quickstart requirements.

**B. Docker container, `docker run` as the single entry point.**
- Advantages: environment-hermetic, removes "works on my machine" risk.
- Disadvantages: adds Docker as a hard prerequisite the reviewer may not have
  installed; a build step before first run; disproportionate for a
  single-process, single-file-database prototype.
- Risks: none material, but no offsetting benefit large enough to justify the
  added prerequisite for this specific project's scale.
- Implementation impact: low-moderate (a Dockerfile to write and maintain).
- Assessment implications: slower first-run experience for a reviewer without
  Docker already running.

## Decision

**Option A** — a plain local process, started via `uv run uvicorn
app.main:app --reload` for development and `uv run uvicorn app.main:app` for
a non-reloading demonstration run, with the SQLite database file created
automatically on first run under `data/app.db` (gitignored). A `uv.lock`
(or `requirements.txt` pinned via `uv pip compile`) fully pins the
dependency set for reproducibility.

## Rationale

Consistent with ADR-0001 (single process) and ADR-0003 (single-file
database), this keeps the "clone → run → verify" path as short as possible,
which directly serves reviewer usability — a stated concern throughout the
guide (reviewer navigation guide, quickstart requirements) — without adding
infrastructure this prototype's scale doesn't need.

## Consequences

- **Positive**: minimal reviewer friction; the existing repository tooling
  (`uv`) is already established, so this introduces no new tool family.
- **Negative**: no environment isolation beyond Python's own virtual
  environment (via `uv`) — disclosed as a prototype-scope choice, not a
  production deployment recommendation.
- **Operational**: `uv run ...` is the entire operational surface; stopping
  the process and deleting `data/app.db` fully resets state.
- **Testing**: `uv run pytest` runs the full suite with no additional setup.
- **Governance**: a future move to containerized/cloud deployment is a
  material architecture change requiring its own ADR (FR-306).

## Risks and Mitigations

- **Risk**: reviewer's local Python version mismatch. **Mitigation**: pinned
  Python version in `pyproject.toml`, verified by `uv run` itself refusing to
  run under an incompatible interpreter.

## Reversibility

**High.** Adding a Dockerfile later (Option B) is additive, not a
replacement — it would wrap the same `uv run` entry point without requiring
any application-code change.

## Traceability

- Requirements: spec Constraints ("must run locally, demonstrable").
- Specification sections: Constraints, Exclusions (no hosted deployment).
- Plan sections: plan.md Technical Context (Target Platform), quickstart.md.
- Expected tasks: engineering-baseline, setup-and-quickstart task groups.

## Validation

Validated by: a fresh-clone verification — cloning the repository into a
clean directory and running the quickstart's documented commands end-to-end,
with the actual command output retained as evidence (this is explicitly
listed in the guide's Final Step-by-Step Execution Sequence, step 61: "Verify
setup from a clean clone").
