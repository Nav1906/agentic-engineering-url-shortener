# Governed URL Shortener — Agentic SDLC Assessment

A production-oriented URL shortener that doubles as the demonstration
domain for a governed, stateful, non-linear agentic software-engineering
orchestration system. The orchestration engine — not the URL shortener — is
the primary object of evaluation. See
`.specify/memory/constitution.md` for why.

## Start here

- **Run it**: [specs/001-governed-url-shortener/quickstart.md](specs/001-governed-url-shortener/quickstart.md) —
  real, executed commands only.
- **Requirements**: [specs/001-governed-url-shortener/spec.md](specs/001-governed-url-shortener/spec.md) (Approved)
- **Plan and architecture**: [specs/001-governed-url-shortener/plan.md](specs/001-governed-url-shortener/plan.md) (9/10 ADRs Accepted)
- **Architecture Decision Records**: [docs/adr/](docs/adr/)
- **Task plan**: [specs/001-governed-url-shortener/tasks.md](specs/001-governed-url-shortener/tasks.md) (103 tasks, 42 groups)
- **Governance history**: [docs/governance/](docs/governance/)

## The one open item

ADR-0006 (credential-isolation for the human-approval surface) remains
**Rejected** — its macOS `sandbox-exec` mechanism failed a direct
feasibility spike; a replacement (a separate OS user) was designed but
never executed (no privileged command has been run). As a direct
consequence, the approval-gate endpoints are **fail-closed**: they exist,
are role/revision-checked, and are tested, but no real approval can
currently succeed against this codebase, by design, until you accept a
replacement mechanism. See `src/api/auth.py`'s module docstring and
`tasks.md` T100–T103 for the full, disclosed detail.

## Quick facts

- Python 3.12, FastAPI, SQLite (WAL mode), no external services, no Docker.
- `uv run pytest tests/` — 159 real tests, all passing as of the last
  commit on this branch.
- Three required scenarios (greenfield/brownfield/ambiguous) each run as a
  standalone script against real code: `scripts/demo_*.py`.
