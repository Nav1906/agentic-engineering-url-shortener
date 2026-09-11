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
- **Plan and architecture**: [specs/001-governed-url-shortener/plan.md](specs/001-governed-url-shortener/plan.md) (all 10 ADRs Accepted)
- **Architecture Decision Records**: [docs/adr/](docs/adr/)
- **Task plan**: [specs/001-governed-url-shortener/tasks.md](specs/001-governed-url-shortener/tasks.md) (106/106 tasks complete)
- **Threat model**: [docs/threat-model.md](docs/threat-model.md)
- **Governance history**: [docs/governance/](docs/governance/)
- **Final Engineering Summary**: [docs/final-engineering-summary.md](docs/final-engineering-summary.md)

## The one thing to read before trusting the approval mechanism

ADR-0006 was accepted 2026-09-11 as **Revision 5, scope-limited**: this
prototype permanently excludes external-agent subprocess execution from
its trusted boundary, and that is what makes its real human-approval
credential mechanism (`scripts/bootstrap_credentials.py`,
`scripts/approve.py`) safe to run. **This does not claim same-user macOS
credential isolation is solved, and does not claim sandboxing.** See
[docs/threat-model.md](docs/threat-model.md) for exactly what is and isn't
defended against — read it before assuming more than it says.

## Quick facts

- Python 3.12, FastAPI, SQLite (WAL mode), no external services, no Docker.
- `uv run pytest tests/` — 237 real tests, all passing as of the last
  commit on this branch.
- Three required scenarios (greenfield/brownfield/ambiguous) each run as a
  standalone script against real code: `scripts/demo_*.py`.
- A workflow created via `POST /workflows` with `{"auto_execute": true}`
  progresses to completion automatically, driven by a real in-process
  background scheduler — no direct scheduler calls required.
