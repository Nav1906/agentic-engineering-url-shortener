"""Brownfield change regression test: /health must never be rate-limited,
even under sustained load, so a monitoring probe is never itself the cause
of a false 'unavailable' reading. Existing rate-limit behavior for other
endpoints (T043/PVT-007) must be unaffected -- see test_rate_limit.py."""
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.middleware.rate_limit import RateLimitMiddleware, reset_all


def test_health_never_rate_limited():
    reset_all()
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)

    @app.get("/health")
    def health():
        return {"status": "healthy"}

    with TestClient(app) as client:
        for _ in range(200):  # well beyond the 60/min limit
            resp = client.get("/health")
            assert resp.status_code == 200


def test_other_endpoints_still_rate_limited_normally():
    """Regression guard: the exemption must be specific to /health, not a
    blanket disabling of the rate limiter."""
    reset_all()
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)

    @app.get("/health")
    def health():
        return {"status": "healthy"}

    @app.get("/ping")
    def ping():
        return {"ok": True}

    with TestClient(app) as client:
        for _ in range(60):
            client.get("/ping")
        resp = client.get("/ping")
        assert resp.status_code == 429
        # /health remains unaffected even while /ping is limited.
        assert client.get("/health").status_code == 200
