"""GET /metrics/reliability (T082; FR-603, FR-604). Always demonstration_data=true."""
from __future__ import annotations

from fastapi import APIRouter

from src.api.schemas import ReliabilityMetrics
from src.observability.metrics import compute_reliability_metrics
from src.persistence.db import get_connection

router = APIRouter()


@router.get("/metrics/reliability", response_model=ReliabilityMetrics)
def get_reliability_metrics() -> ReliabilityMetrics:
    conn = get_connection()
    try:
        data = compute_reliability_metrics(conn)
        assert data["demonstration_data"] is True  # FR-604: never optional
        return ReliabilityMetrics(**data)
    finally:
        conn.close()
