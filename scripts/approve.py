#!/usr/bin/env python3
"""T101: human-invoked approval CLI (ADR-0006 Revision 5).

Reads the RAW token for --identity from the local raw-token file
(local-secrets/approval_tokens.raw.json, chmod 600) -- never accepts a
token or identity as a request parameter the SERVER would trust; the
server only ever trusts what it derives from verifying the token itself
(src/api/auth.py::resolve_identity). This script's --identity flag is
purely a local lookup key into the operator's own raw-token file, never
sent to the server as an identity claim.

Usage:
    uv run python3 scripts/approve.py \\
        --identity alice --workflow <workflow_id> --gate requirements_approval \\
        --decision approve --rationale "looks complete and testable"

Run scripts/bootstrap_credentials.py first if no credentials exist yet.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.api.credentials import read_raw_token

DEFAULT_BASE_URL = "http://localhost:8000"


def submit_decision(
    base_url: str,
    workflow_id: str,
    gate_id: str,
    decision: str,
    token: str,
    rationale: str | None,
) -> dict:
    """Submits the decision to the real approval endpoint, using ONLY the
    verified-token Authorization header for identity -- decision,
    rationale, gate ID, and the workflow's own artifact revision (server-
    resolved, not client-asserted) are exactly what FR-310 requires be
    recorded."""
    url = f"{base_url}/workflows/{workflow_id}/gates/{gate_id}/{decision}"
    body = json.dumps({"rationale": rationale}).encode()
    request = urllib.request.Request(
        url, data=body, method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()
        print(f"ERROR {exc.code}: {detail}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--identity", required=True, help="local lookup key into your own raw-token file")
    parser.add_argument("--workflow", required=True, dest="workflow_id")
    parser.add_argument("--gate", required=True, dest="gate_id")
    parser.add_argument("--decision", required=True, choices=["approve", "reject"])
    parser.add_argument("--rationale", default=None)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args()

    try:
        token = read_raw_token(args.identity)
    except (FileNotFoundError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    result = submit_decision(
        args.base_url, args.workflow_id, args.gate_id, args.decision, token, args.rationale,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
