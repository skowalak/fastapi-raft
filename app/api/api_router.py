"""
This router should be used in all API routes
"""

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from json import loads as json_loads
from typing import Callable
from uuid import uuid4
import structlog

logger: structlog.stdlib.AsyncBoundLogger = structlog.get_logger(__name__)


class ContextAndIdRoute(APIRoute):
    """
    Custom API Route, that intercepts a JSONResponse and injects the top-level
    properties `id` and `context`.
    """

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            request_id = str(uuid4())
            request_context = request.query_params.get("context")
            response: Response = await original_route_handler(request)

            if isinstance(response, JSONResponse):
                headers = response.headers.mutablecopy()
                del headers["content-length"]
                payload = json_loads(response.body)

                if payload:
                    if request_context:
                        payload["context"] = request_context
                    payload["id"] = request_id
                    return JSONResponse(
                        payload,
                        status_code=response.status_code,
                        headers=headers,
                        media_type=response.media_type,
                        background=response.background,
                    )

            return response

        return custom_route_handler


class CustomApiRouter(APIRouter):
    """
    APIRouter that injects a custom route_class `ContextAndIdRoute` after the
    standard route handler.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, route_class=ContextAndIdRoute, **kwargs)
