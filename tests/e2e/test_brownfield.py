"""T085 e2e wrapper: real subprocess execution of scripts/demo_brownfield.py.

Note: the script itself shells out to the full pytest suite as its
regression-evidence step, so this wrapper's timeout is generous."""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_brownfield_script_runs_and_passes():
    result = subprocess.run(
        [sys.executable, "scripts/demo_brownfield.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False, timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "SCENARIO B (BROWNFIELD) PASSED" in result.stdout
