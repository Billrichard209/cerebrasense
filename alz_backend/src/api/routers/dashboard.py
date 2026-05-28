"""Dashboard data routes for longitudinal OASIS-2 monitoring."""

from __future__ import annotations

from fastapi import APIRouter
from src.api.services import build_dashboard_payload, build_oasis2_longitudinal_dashboard_payload

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/data")
def dashboard_data_route() -> dict[str, object]:
    """Return registry-driven longitudinal dashboard data."""

    return build_dashboard_payload()


@router.get("/longitudinal/oasis2/dashboard")
def oasis2_longitudinal_dashboard_route(
    run_name: str | None = None,
) -> dict[str, object]:
    """Return OASIS-2 longitudinal summary with subject-consensus metrics when available."""

    return build_oasis2_longitudinal_dashboard_payload(run_name=run_name)
