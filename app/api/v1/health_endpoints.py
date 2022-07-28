import structlog
from app.api.v1.models import V1ApiResponse
from fastapi import APIRouter, Response

logger: structlog.stdlib.AsyncBoundLogger = structlog.get_logger(__name__)
health_router: APIRouter = APIRouter()


@health_router.get(
    "/",
    response_model=V1ApiResponse,
    response_model_exclude_none=True,
)
async def get_health():
    """
    Returns 200 OK if service is up.
    """
    return Response("healthy")
