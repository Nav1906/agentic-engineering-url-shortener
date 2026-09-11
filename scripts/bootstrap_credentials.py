#!/usr/bin/env python3
"""T100: generates role-specific human-approval credentials for this local
demonstration deployment. Human Gate 4, ADR-0006 Revision 5 -- previously
BLOCKED (T100 was one of T100-T103), unblocked because external-agent
execution is now permanently excluded from this prototype's trusted
boundary (src/orchestration/adapters/launcher.py always fails closed).

Run this ONCE per local deployment:
    uv run python3 scripts/bootstrap_credentials.py

Tokens are printed to stdout exactly once, here, at creation time. There
is no command that reads them back later -- write them down now, or use
scripts/approve.py, which reads the local raw-token file directly (see
that script's own docstring for why that's safe: it runs locally, as the
same operator, reading a file only that operator's OS account can read).

Re-running this script without --force refuses to overwrite existing
credentials (it would silently invalidate every token already handed to
an operator). Same-OS-user compromise is explicitly OUTSIDE this
prototype's threat model -- see docs/threat-model.md.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.api.credentials import bootstrap, hashed_config_path, raw_tokens_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force", action="store_true",
        help="overwrite existing credentials (invalidates all previously issued tokens)",
    )
    args = parser.parse_args()

    try:
        raw_tokens = bootstrap(force=args.force)
    except FileExistsError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print("Pass --force to overwrite (this invalidates every existing token).", file=sys.stderr)
        sys.exit(1)

    print("Credentials provisioned. These raw tokens will NEVER be printed again:")
    print()
    for identity, token in raw_tokens.items():
        print(f"  {identity}: {token}")
    print()
    print(f"Raw tokens written to:    {raw_tokens_path()} (chmod 600)")
    print(f"Hashed config written to: {hashed_config_path()} (chmod 600)")
    print()
    print("Same-OS-user compromise is outside this prototype's threat model")
    print("(see docs/threat-model.md). Use scripts/approve.py to submit a")
    print("real human approval decision using these credentials.")


if __name__ == "__main__":
    main()
