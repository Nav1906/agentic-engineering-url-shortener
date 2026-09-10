"""GET /{shortCode} (T028-030, T034; FR-103, FR-104, FR-105).

FR-105/ADR-0009: the analytics write MUST happen strictly after the
redirect response has been sent — never before, never in the same
transaction as the redirect-authorizing lookup. FastAPI's BackgroundTasks
runs after the response is transmitted, which is exactly this ordering.
"""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import RedirectResponse

from src.domain import analytics as analytics_module
from src.domain.short_link import get_short_link
from src.observability.audit import record_event
from src.persistence.db import get_connection

router = APIRouter()


def _write_analytics_after_response(short_code: str) -> None:
    """Runs strictly after the HTTP response has already been sent."""
    conn = get_connection()
    try:
        analytics_module.enqueue_redirect_event(conn, short_code)
        analytics_module.drain_outbox(conn)
    finally:
        conn.close()


@router.get("/{short_code}")
def resolve_short_link(short_code: str, background_tasks: BackgroundTasks):
    conn = get_connection()
    try:
        link = get_short_link(conn, short_code)
        if link is None:
            record_event(
                conn, "system", "resolve_short_link", f"short_code:{short_code}",
                "not_found", "unknown short code",
            )
            from fastapi import HTTPException

            from src.api.schemas import ErrorResponse

            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(error="not_found", message="unknown short code", requirement_ref="FR-103").model_dump(),
            )
        if link.is_expired:
            record_event(
                conn, "system", "resolve_short_link", f"short_code:{short_code}",
                "gone", "expired short code — no analytics increment (FR-104)",
            )
            from fastapi import HTTPException

            from src.api.schemas import ErrorResponse

            raise HTTPException(
                status_code=410,
                detail=ErrorResponse(error="gone", message="short code has expired", requirement_ref="FR-104").model_dump(),
            )
        if link.status == "deleted":
            from fastapi import HTTPException

            from src.api.schemas import ErrorResponse

            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(error="not_found", message="short code has been deleted").model_dump(),
            )

        # Response constructed and about to be sent; analytics write is
        # scheduled for strictly AFTER transmission via BackgroundTasks.
        background_tasks.add_task(_write_analytics_after_response, short_code)
        return RedirectResponse(url=link.destination_url, status_code=302)
    finally:
        conn.close()
