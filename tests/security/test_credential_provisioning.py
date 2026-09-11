"""T100: real credential provisioning (ADR-0006 Revision 5). Uses an
isolated tmp_path for LOCAL_SECRETS_DIR throughout -- never touches this
actual repository checkout's own local-secrets/ directory."""
import json
import stat

import pytest

from src.api import credentials


@pytest.fixture(autouse=True)
def isolated_secrets_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(credentials, "LOCAL_SECRETS_DIR", tmp_path / "local-secrets")
    yield


def test_bootstrap_creates_both_files_chmod_600():
    raw_tokens = credentials.bootstrap()

    raw_path = credentials.raw_tokens_path()
    hashed_path = credentials.hashed_config_path()
    assert raw_path.exists()
    assert hashed_path.exists()

    raw_mode = stat.S_IMODE(raw_path.stat().st_mode)
    hashed_mode = stat.S_IMODE(hashed_path.stat().st_mode)
    assert raw_mode == 0o600
    assert hashed_mode == 0o600

    assert set(raw_tokens.keys()) == {"alice", "bob"}


def test_raw_tokens_are_cryptographically_random_and_high_entropy():
    raw_tokens = credentials.bootstrap()
    for token in raw_tokens.values():
        assert len(token) >= 32  # base64url(32 bytes) is well over 32 chars
    # No two identities share a token.
    assert len(set(raw_tokens.values())) == len(raw_tokens)


def test_hashed_config_never_contains_raw_token():
    raw_tokens = credentials.bootstrap()
    hashed = credentials.load_hashed_config()
    serialized = json.dumps(hashed)
    for token in raw_tokens.values():
        assert token not in serialized


def test_verify_token_succeeds_for_provisioned_token_and_role():
    raw_tokens = credentials.bootstrap()
    result = credentials.verify_token(raw_tokens["alice"])
    assert result == ("alice", "reviewer_approver")
    result_bob = credentials.verify_token(raw_tokens["bob"])
    assert result_bob == ("bob", "release_owner")


def test_verify_token_fails_closed_for_unknown_token():
    credentials.bootstrap()
    assert credentials.verify_token("not-a-real-token") is None


def test_verify_token_fails_closed_before_bootstrap_ever_runs():
    assert credentials.verify_token("anything") is None


def test_bootstrap_refuses_to_overwrite_without_force():
    credentials.bootstrap()
    with pytest.raises(FileExistsError):
        credentials.bootstrap()


def test_bootstrap_force_generates_new_tokens_invalidating_old_ones():
    first = credentials.bootstrap()
    second = credentials.bootstrap(force=True)
    assert first["alice"] != second["alice"]
    assert credentials.verify_token(first["alice"]) is None  # old token now invalid
    assert credentials.verify_token(second["alice"]) == ("alice", "reviewer_approver")


def test_read_raw_token_returns_provisioned_value():
    raw_tokens = credentials.bootstrap()
    assert credentials.read_raw_token("alice") == raw_tokens["alice"]


def test_read_raw_token_missing_identity_raises():
    credentials.bootstrap()
    with pytest.raises(KeyError):
        credentials.read_raw_token("nonexistent-identity")


def test_read_raw_token_before_bootstrap_raises():
    with pytest.raises(FileNotFoundError):
        credentials.read_raw_token("alice")
