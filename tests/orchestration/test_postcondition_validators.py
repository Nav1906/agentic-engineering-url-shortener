"""T062: executable postcondition validators (FR-606, ADR-0005). Built-in
validators execute no untrusted code -- safe regardless of ADR-0006's
status. External-command validators are explicitly blocked, not silently
skipped."""
import pytest

from src.orchestration.validators import (
    ExternalCommandValidatorBlocked,
    run_builtin_validator,
    run_external_command_validator,
)


def test_file_exists_passes_when_file_present(tmp_path):
    (tmp_path / "output.txt").write_text("hello")
    result = run_builtin_validator("file_exists", tmp_path, {"filename": "output.txt"})
    assert result.passed is True
    assert result.exit_code == 0
    assert "output.txt" in result.artifact_hashes
    assert len(result.artifact_hashes["output.txt"]) == 64  # sha256 hex digest


def test_file_exists_fails_when_file_missing(tmp_path):
    """An empty, 'clean' directory is NOT itself evidence -- the required
    artifact must actually be present."""
    result = run_builtin_validator("file_exists", tmp_path, {"filename": "output.txt"})
    assert result.passed is False
    assert result.exit_code == 1
    assert result.artifact_hashes == {}


def test_content_equals_validator(tmp_path):
    (tmp_path / "output.txt").write_text("expected content")
    passing = run_builtin_validator(
        "content_equals", tmp_path, {"filename": "output.txt", "expected": "expected content"}
    )
    assert passing.passed is True
    failing = run_builtin_validator(
        "content_equals", tmp_path, {"filename": "output.txt", "expected": "wrong"}
    )
    assert failing.passed is False


def test_no_validator_ran_always_fails_closed(tmp_path):
    result = run_builtin_validator("no_validator_ran", tmp_path, {})
    assert result.passed is False


def test_unknown_validator_rejected(tmp_path):
    with pytest.raises(ValueError):
        run_builtin_validator("made_up_validator", tmp_path, {})


def test_external_command_validator_is_blocked(tmp_path):
    with pytest.raises(ExternalCommandValidatorBlocked):
        run_external_command_validator(["echo", "hello"], tmp_path)
