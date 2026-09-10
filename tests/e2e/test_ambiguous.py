"""T086 e2e wrapper: real subprocess execution of scripts/demo_ambiguous.py,
including the real approval-gate pause never being auto-approved through the
real endpoint (see the script's own module docstring for the disclosed
demonstration-substitute limitation)."""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_ambiguous_script_runs_and_passes():
    result = subprocess.run(
        [sys.executable, "scripts/demo_ambiguous.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "SCENARIO C (AMBIGUOUS) PASSED" in result.stdout
    assert "awaiting_approval (suspended, NOT proceeding to implementation)" in result.stdout
