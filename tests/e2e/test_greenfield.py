"""T084 e2e wrapper: real subprocess execution of scripts/demo_greenfield.py."""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_greenfield_script_runs_and_passes():
    result = subprocess.run(
        [sys.executable, "scripts/demo_greenfield.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "SCENARIO A (GREENFIELD) PASSED" in result.stdout
