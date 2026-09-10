"""T043: 61st request in a minute from one IP is rejected (PVT-007).

Uses a fresh, isolated Starlette app rather than the shared src.api.main.app
singleton -- that module-level app persists its middleware state (including
the rate-limit bucket) across every test in the same pytest process, which
would make this test's outcome depend on unrelated tests' request counts
run earlier in the same session. A dedicated minimal app isolates the
behavior under test from that shared-state artifact.
"""
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.middleware.rate_limit import RateLimitMiddleware, reset_all


def test_61st_request_in_a_minute_rejected():
    reset_all()  # _BUCKETS is module-level, shared with src.api.main.app's
    # middleware too -- reset explicitly rather than relying on a fresh
    # FastAPI app instance, since the bucket storage isn't per-instance.
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    with TestClient(app) as client:
        for _ in range(60):
            resp = client.get("/ping")
            assert resp.status_code == 200
        resp = client.get("/ping")
        assert resp.status_code == 429
