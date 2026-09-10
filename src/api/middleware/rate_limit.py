"""Rate limiting middleware (T043; PVT-007, 60 req/min/IP, proposed)."""
from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

LIMIT_PER_MINUTE = 60
WINDOW_SECONDS = 60.0

# Brownfield change (2026-09-10): /health is exempt so a monitoring probe
# is never itself the cause of a false "unavailable" reading. See the
# impact analysis recorded by scripts/demo_brownfield.py before this
# change was made, and tests/security/test_health_exempt_from_rate_limit.py
# for the regression coverage (including the guard that other endpoints
# remain normally rate-limited).
EXEMPT_PATHS = {"/health"}

# Module-level (not instance-level) so tests can reset it directly via
# reset_all(), independent of which FastAPI app object wraps the
# middleware. The shared src.api.main.app singleton persists for the whole
# pytest session, so instance-level state would otherwise accumulate
# requests across unrelated tests and eventually produce spurious 429s.
_BUCKETS: dict[str, deque] = defaultdict(deque)


def reset_all() -> None:
    """TEST-ONLY. Clears all rate-limit buckets."""
    _BUCKETS.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)
        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        bucket = _BUCKETS[client_ip]
        while bucket and now - bucket[0] > WINDOW_SECONDS:
            bucket.popleft()
        if len(bucket) >= LIMIT_PER_MINUTE:
            return JSONResponse(
                status_code=429,
                content={"error": "rate_limited", "message": "too many requests", "requirement_ref": "PVT-007"},
            )
        bucket.append(now)
        return await call_next(request)
