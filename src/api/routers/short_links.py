"""POST /short-links, GET .../analytics, DELETE /short-links/{shortCode}
(T023, T025-027, T032, T041; FR-101,102,104,108,112,113,114,116)."""
from __future__ import annotations

from typing import Literal, cast

from fastapi import APIRouter, Header, HTTPException

from src.api.schemas import (
    ErrorResponse,
    ShortLinkAnalyticsSummary,
    ShortLinkCreateRequest,
    ShortLinkCreateResponse,
)
from src.domain import analytics as analytics_module
from src.domain.idempotency import (
    IdempotencyConflict,
    IdempotencyKeyTooShort,
    check_replay,
    validate_key_length,
)
from src.domain.idempotency import (
    record as record_idempotency,
)
from src.domain.short_link import (
    ShortCodeGenerationExhausted,
    create_short_link,
    delete_short_link,
    get_short_link,
)
from src.domain.validation import ValidationError
from src.observability.audit import record_event
from src.persistence.db import get_connection

router = APIRouter()


@router.post("/short-links", response_model=ShortLinkCreateResponse, status_code=201)
def create_short_link_endpoint(
    body: ShortLinkCreateRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    conn = get_connection()
    try:
        if idempotency_key is not None:
            try:
                validate_key_length(idempotency_key)
            except IdempotencyKeyTooShort as exc:
                raise HTTPException(
                    status_code=400,
                    detail=ErrorResponse(
                        error="idempotency_key_too_short", message=str(exc), requirement_ref="plan.md-sec8"
                    ).model_dump(),
                ) from exc
            try:
                existing_code = check_replay(conn, idempotency_key, body.destination_url, body.expires_at)
            except IdempotencyConflict as exc:
                record_event(
                    conn, "system", "create_short_link_idempotency_conflict",
                    f"idempotency_key:{idempotency_key}", "rejected", str(exc),
                )
                raise HTTPException(
                    status_code=409,
                    detail=ErrorResponse(error="idempotency_conflict", message=str(exc), requirement_ref="FR-113").model_dump(),
                ) from exc
            if existing_code is not None:
                link = get_short_link(conn, existing_code)
                assert link is not None  # existing_code came from our own idempotency record
                return ShortLinkCreateResponse(
                    short_code=link.short_code,
                    destination_url=link.destination_url,
                    created_at=link.created_at,
                    expires_at=link.expires_at,
                    idempotent_replay=True,
                )

        try:
            link = create_short_link(conn, body.destination_url, body.expires_at)
        except ValidationError as exc:
            record_event(
                conn, "system", "create_short_link_rejected",
                f"destination_url:{body.destination_url!r}", "rejected", str(exc),
            )
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(error="validation_error", message=str(exc), requirement_ref="FR-101/FR-114").model_dump(),
            ) from exc
        except ShortCodeGenerationExhausted as exc:
            raise HTTPException(
                status_code=503,
                detail=ErrorResponse(error="short_code_exhausted", message=str(exc), requirement_ref="ADR-0004").model_dump(),
            ) from exc

        if idempotency_key is not None:
            record_idempotency(conn, idempotency_key, body.destination_url, body.expires_at, link.short_code)

        record_event(
            conn, "system", "create_short_link", f"short_code:{link.short_code}",
            "created", "valid request, new short link created",
        )
        return ShortLinkCreateResponse(
            short_code=link.short_code,
            destination_url=link.destination_url,
            created_at=link.created_at,
            expires_at=link.expires_at,
            idempotent_replay=False,
        )
    finally:
        conn.close()


@router.get("/short-links/{short_code}/analytics", response_model=ShortLinkAnalyticsSummary)
def get_analytics(short_code: str):
    conn = get_connection()
    try:
        link = get_short_link(conn, short_code)
        if link is None:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(error="not_found", message="unknown short code").model_dump(),
            )
        summary = analytics_module.get_summary(conn, short_code)
        status = analytics_module.effective_completeness_status(conn, short_code)
        return ShortLinkAnalyticsSummary(
            short_code=short_code,
            successful_redirect_count=summary["successful_redirect_count"] if summary else 0,
            last_successful_redirect_at=summary["last_successful_redirect_at"] if summary else None,
            completeness_status=cast(
                'Literal["complete", "degraded", "incomplete"]', status
            ),  # runtime-guaranteed by the DB CHECK constraint on this column
        )
    finally:
        conn.close()


@router.delete("/short-links/{short_code}", status_code=204)
def delete_short_link_endpoint(short_code: str):
    conn = get_connection()
    try:
        deleted = delete_short_link(conn, short_code)
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(error="not_found", message="unknown short code").model_dump(),
            )
        record_event(
            conn, "system", "delete_short_link", f"short_code:{short_code}",
            "deleted", "explicit deletion request (idempotency record retained, FR-116)",
        )
        return
    finally:
        conn.close()
