"""Executable postcondition validators (T062; ADR-0005 "Executable
Postconditions", FR-606).

Controller-run only -- these functions execute inside the SAME process as
the scheduler/promotion logic, never inside an isolated agent subprocess.
Built-in validators below execute NO untrusted code: they only inspect
files already written into an isolated worktree (T061) by a harmless
fixture worker. External-command validators (running an arbitrary command
a stage might request) are explicitly BLOCKED, for the same reason
T100-T103 are blocked: ADR-0006's isolation mechanism remains Rejected,
and running an untrusted command without a verified isolation boundary is
exactly the risk that control exists to prevent.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ValidatorResult:
    command: str
    exit_code: int
    passed: bool
    output_hash: str
    artifact_hashes: dict[str, str] = field(default_factory=dict)


class ExternalCommandValidatorBlocked(RuntimeError):
    """ADR-0006 unresolved -- running an untrusted external command through
    this validator path is not currently safe. See tasks.md T100-T103."""


def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hash_file(path: Path) -> str:
    return _hash_bytes(path.read_bytes())


def run_builtin_validator(name: str, worktree_path: Path, args: dict) -> ValidatorResult:
    """Deterministic, in-process, no subprocess, no untrusted code
    execution -- safe regardless of ADR-0006's status. A directory with no
    stray files ("looks clean") is NOT itself evidence -- these validators
    only pass when the specifically-required artifact is actually present
    and, for content_equals, actually matches."""
    if name == "file_exists":
        filename = args.get("filename", "output.txt")
        target = worktree_path / filename
        exists = target.is_file()
        artifact_hashes = {filename: _hash_file(target)} if exists else {}
        output = f"file_exists({filename}) -> {exists}"
        return ValidatorResult(
            command=f"builtin:file_exists:{filename}",
            exit_code=0 if exists else 1,
            passed=exists,
            output_hash=_hash_bytes(output.encode()),
            artifact_hashes=artifact_hashes,
        )

    if name == "content_equals":
        filename = args.get("filename", "output.txt")
        expected = args.get("expected", "")
        target = worktree_path / filename
        if not target.is_file():
            output = f"content_equals({filename}) -> file missing"
            return ValidatorResult(
                command=f"builtin:content_equals:{filename}",
                exit_code=1, passed=False,
                output_hash=_hash_bytes(output.encode()),
            )
        actual = target.read_text()
        passed = actual == expected
        output = f"content_equals({filename}) -> {passed}"
        return ValidatorResult(
            command=f"builtin:content_equals:{filename}",
            exit_code=0 if passed else 1,
            passed=passed,
            output_hash=_hash_bytes(output.encode()),
            artifact_hashes={filename: _hash_file(target)},
        )

    if name == "no_validator_ran":
        # Explicit representation of "validation has not run" -- always
        # fails closed. Used to prove no path to `succeeded` bypasses
        # validation by omitting it entirely.
        return ValidatorResult(
            command="builtin:no_validator_ran", exit_code=1, passed=False,
            output_hash=_hash_bytes(b"no validator ran"),
        )

    raise ValueError(f"unknown built-in validator {name!r}")


def run_external_command_validator(command: list[str], worktree_path: Path) -> ValidatorResult:
    """BLOCKED. See module docstring and tasks.md T100-T103. Never called
    by promote_or_reject -- external-command validation has no wired path
    into stage completion at all while ADR-0006 remains Rejected."""
    raise ExternalCommandValidatorBlocked(
        f"external-command validator {command!r} is blocked: ADR-0006's isolation "
        "mechanism remains Rejected, and executing an untrusted command without a "
        "verified isolation boundary is exactly the risk that control exists to "
        "prevent. See tasks.md T100-T103."
    )
