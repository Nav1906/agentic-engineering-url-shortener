"""T049: manifest parses, version field required."""
import pytest

from src.policy.manifest import ManifestError, load_manifest, policy_ids


def test_default_manifest_loads():
    manifest = load_manifest()
    assert manifest["version"] == "1.0.0"
    assert "dependency-secret-scan" in policy_ids(manifest)


def test_missing_version_rejected(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("policies:\n  - id: x\n")
    with pytest.raises(ManifestError):
        load_manifest(bad)


def test_missing_policy_id_rejected(tmp_path):
    bad = tmp_path / "bad2.yaml"
    bad.write_text("version: '1.0'\npolicies:\n  - description: no id here\n")
    with pytest.raises(ManifestError):
        load_manifest(bad)
