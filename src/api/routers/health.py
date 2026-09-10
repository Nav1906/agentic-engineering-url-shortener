"""GET /health (T007, T083; FR-111, FR-115, FR-117)."""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter

from src.api.schemas import AnalyticsHealth, HealthStatus
from src.observability import system_status
from src.persistence.db import get_connection

router = APIRouter()


@router.get("/health", response_model=HealthStatus)
def get_health() -> HealthStatus:
    conn = get_connection()
    try:
        status_row = system_status.get_status(conn)
        degraded_since = status_row["degraded_since_unclean_shutdown_at"]
        analytics_status: Literal["degraded", "healthy"] = "degraded" if degraded_since else "healthy"
        return HealthStatus(
            status="healthy",
            analytics=AnalyticsHealth(
                status=analytics_status,
                degraded_since_unclean_shutdown_at=degraded_since,
            ),
        )
    finally:
        conn.close()
