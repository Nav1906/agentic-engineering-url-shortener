"""Versioned policy manifest loader (T049; Constitution Principle VI)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

DEFAULT_MANIFEST_PATH = Path(__file__).resolve().parents[2] / "config" / "policies.yaml"


class ManifestError(ValueError):
    pass


def load_manifest(path: Path = DEFAULT_MANIFEST_PATH) -> dict[str, Any]:
    with open(path) as f:
        data = yaml.safe_load(f)
    if "version" not in data:
        raise ManifestError("policy manifest missing required 'version' field")
    if "policies" not in data or not isinstance(data["policies"], list):
        raise ManifestError("policy manifest missing required 'policies' list")
    for policy in data["policies"]:
        if "id" not in policy:
            raise ManifestError(f"policy entry missing 'id': {policy!r}")
    return data


def policy_ids(manifest: dict[str, Any]) -> list[str]:
    return [p["id"] for p in manifest["policies"]]
