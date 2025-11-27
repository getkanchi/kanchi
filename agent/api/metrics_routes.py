"""Prometheus metrics endpoint."""

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest


def create_router(app_state) -> APIRouter:  # noqa: ARG001 - signature kept for consistency
    """Expose Prometheus metrics."""
    router = APIRouter()

    @router.get("/metrics")
    async def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return router
