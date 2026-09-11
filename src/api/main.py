"""FastAPI app entrypoint (T007). Startup gate: a marker-write failure MUST
prevent request-serving, not just log a warning (T038). T106: also runs
crash recovery and starts/stops the in-process background scheduler here,
so a workflow created through the HTTP API progresses automatically."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.observability import system_status
from src.orchestration import live_scheduler
from src.orchestration.scheduler import recover_on_startup
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
        # T106 restart recovery: any stage left 'running' from a prior,
        # uncleanly-terminated process is forced to failed_transient before
        # the background scheduler starts claiming new work.
        recover_on_startup(conn)
    finally:
        conn.close()

    live_scheduler.start()  # T106: clean startup, periodic scheduling begins
    yield
    await live_scheduler.stop()  # T106: graceful shutdown before the process exits

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
    workflow_evidence,
    workflows,
)

app.include_router(short_links.router)
app.include_router(workflows.router)
app.include_router(workflow_evidence.router)
app.include_router(health.router)
app.include_router(metrics.router)
app.include_router(approvals.router)
# redirect's catch-all GET /{short_code} must be registered LAST so it
# doesn't shadow the more specific routes above (e.g. /health, /workflows).
app.include_router(redirect.router)
