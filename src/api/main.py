"""FastAPI app entrypoint (T007). Startup gate: a marker-write failure MUST
prevent request-serving, not just log a warning (T038)."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.observability import system_status
from src.persistence.db import get_connection, init_schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = get_connection()
    try:
        init_schema(conn)
        # T038: if this raises, startup fails and no request is ever served —
        # FastAPI's lifespan context propagates the exception, which uvicorn
        # treats as a failed startup (no "Application startup complete").
        system_status.on_startup(conn)
    finally:
        conn.close()
    yield
    conn = get_connection()
    try:
        system_status.on_clean_shutdown(conn)
    finally:
        conn.close()


app = FastAPI(title="Governed URL Shortener", version="0.1.0", lifespan=lifespan)

from src.api.middleware.rate_limit import RateLimitMiddleware

app.add_middleware(RateLimitMiddleware)


def _get_conn():
    return get_connection()


from src.api.routers import (
    approvals,
    health,
    metrics,
    redirect,
    short_links,
    workflows,
)

app.include_router(short_links.router)
app.include_router(workflows.router)
app.include_router(health.router)
app.include_router(metrics.router)
app.include_router(approvals.router)
# redirect's catch-all GET /{short_code} must be registered LAST so it
# doesn't shadow the more specific routes above (e.g. /health, /workflows).
app.include_router(redirect.router)
