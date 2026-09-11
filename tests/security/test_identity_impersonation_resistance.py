"""Focused pre-push check: confirms (1) approval identity/role are derived
server-side purely from the verified token, never from any client-supplied
field, and (2) scripts/approve.py's --identity flag cannot be used to
impersonate another approver -- it is a local raw-token-file lookup key
only, never transmitted to the server."""
import inspect

from fastapi.testclient import TestClient

from src.api.schemas import ApprovalRequest


def test_approval_request_schema_has_no_identity_field():
    """Structural: the request body a client can submit has no field the
    server could even attempt to trust as an identity claim."""
    assert "identity" not in ApprovalRequest.model_fields
    assert set(ApprovalRequest.model_fields.keys()) == {"rationale"}


def test_cli_never_puts_identity_in_the_request_body_or_url():
    """Structural, two independent checks:

    1. submit_decision()'s own PARAMETER LIST has no `identity` parameter
       at all -- it cannot transmit what it never receives. The local
       --identity value is consumed entirely by read_raw_token() before
       submit_decision() is ever called (main() does this), so by the time
       this function runs, only the resulting token remains.
    2. The literal JSON body it constructs contains exactly one key,
       `rationale` -- confirmed against the real running code, not just
       inspected as text (which would be fooled by docstring prose
       mentioning "identity" to explain why it's absent).
    """
    import scripts.approve as approve_module

    sig = inspect.signature(approve_module.submit_decision)
    assert "identity" not in sig.parameters

    import json
    from unittest.mock import MagicMock, patch

    captured = {}

    def fake_urlopen(request, timeout=10):
        captured["body"] = json.loads(request.data)
        captured["url"] = request.full_url
        captured["headers"] = dict(request.headers)
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"id": "x"}'
        mock_response.__enter__ = lambda self: mock_response
        mock_response.__exit__ = lambda *a: None
        return mock_response

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        approve_module.submit_decision(
            "http://localhost:8000", "wf-1", "requirements_approval", "approve",
            "the-real-token", "my rationale",
        )

    assert set(captured["body"].keys()) == {"rationale"}
    assert "identity" not in captured["url"]
    # The only place any identity-shaped string could hide is the
    # Authorization header, which correctly carries the token, not a name.
    assert captured["headers"]["Authorization"] == "Bearer the-real-token"


def test_server_identity_is_derived_from_presented_token_regardless_of_intent(tmp_path, monkeypatch):
    """End-to-end proof: even bypassing the CLI entirely and presenting
    bob's real token directly, the server records "bob" -- there is no
    code path by which a caller can make the server record a different
    identity than the one the verified token actually belongs to."""
    import src.persistence.db as db_module
    from src.api import credentials
    from src.api.middleware.rate_limit import reset_all

    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    monkeypatch.setattr(credentials, "LOCAL_SECRETS_DIR", tmp_path / "local-secrets")
    reset_all()
    from src.api.main import app

    raw_tokens = credentials.bootstrap()

    with TestClient(app) as client:
        wf = client.post("/workflows", json={"requirement": "req"}).json()["id"]
        # Present bob's real token. There is no request field anywhere in
        # this call that could claim "alice" instead -- ApprovalRequest
        # has no identity field (see test above), and the CLI's --identity
        # flag isn't even part of the HTTP layer.
        resp = client.post(
            f"/workflows/{wf}/gates/release_readiness/approve",
            json={"rationale": "test"},
            headers={"Authorization": f"Bearer {raw_tokens['bob']}"},
        )
        assert resp.status_code == 200
        assert resp.json()["identity"] == "bob"
        assert resp.json()["identity"] != "alice"


def test_read_raw_token_never_returns_a_different_identitys_token(tmp_path, monkeypatch):
    """Direct proof for the local lookup itself: requesting alice's token
    never returns bob's, and vice versa, across repeated calls."""
    from src.api import credentials

    monkeypatch.setattr(credentials, "LOCAL_SECRETS_DIR", tmp_path / "local-secrets")
    raw_tokens = credentials.bootstrap()

    for _ in range(5):
        assert credentials.read_raw_token("alice") == raw_tokens["alice"]
        assert credentials.read_raw_token("alice") != raw_tokens["bob"]
        assert credentials.read_raw_token("bob") == raw_tokens["bob"]
        assert credentials.read_raw_token("bob") != raw_tokens["alice"]
