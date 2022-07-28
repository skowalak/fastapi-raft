from fastapi import FastAPI
from fastapi.applications import State as FastAPIState
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.routing import APIRouter
from starlette.requests import Request
from starlette.responses import JSONResponse
import structlog
import structlog._frames

import logging
import logging.config
import sys

from app.api.exceptions import ApiException, BadRequestException
from app.api.models import ApiResponse, ApiErrorResponse
from app.api.v1.consensus_endpoints import consensus_router
from app.api.v1.health_endpoints import health_router
from app.config import Settings, get_settings
from app.raft.discovery import discover_replicas
from app.raft.datastructures import ReplicatedLog, State


def create_app(settings: Settings) -> FastAPI:
    """
    Creates the FastAPI app. The FastAPI app will manage endpoints and routes.

    Returns
    -------
    FastAPI
        The FastAPI app.
    """
    lcl_app: FastAPI = FastAPI(
        title=settings.FASTAPI_TITLE,
        description=settings.FASTAPI_DESCR,
        contact={"name": settings.FASTAPI_MAINT, "email": settings.FASTAPI_EMAIL},
        openapi_url=settings.FASTAPI_SCHEM,
        docs_url=settings.FASTAPI_DOCS,
        redoc_url=None,
        root_path=settings.ROOT_PATH,
    )
    api_router = APIRouter()
    """
    Global API Router, parent to all version-specific routers under it.
    """
    api_router.include_router(consensus_router, prefix="/v1/raft", tags=["raft", "v1"])
    api_router.include_router(health_router, prefix="/v1/health", tags=["health", "v1"])

    lcl_app.include_router(api_router, prefix=settings.API_PREFIX)

    return lcl_app


def logging_setup(settings: Settings):
    log_level = settings.LOGGING

    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=log_level)
    logger = logging.getLogger()
    logger.setLevel(log_level)

    def add_app_context(logger, method_name, event_dict):
        f, name = structlog._frames._find_first_app_frame_and_name(
            ["logging", __name__]
        )
        event_dict["file"] = f.f_code.co_filename
        event_dict["line"] = f.f_lineno
        event_dict["function"] = f.f_code.co_name
        return event_dict

    structlog.configure(
        logger_factory=structlog.stdlib.LoggerFactory(),
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            add_app_context,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(indent=2, sort_keys=True),
        ],
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.TimeStamper("iso", utc=True),
            # structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.AsyncBoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.config.dictConfig(settings.LOGGING_CONFIG)


def raft_setup(state: FastAPIState, settings: Settings):
    """Set values needed for Raft"""
    state.id = settings.HOSTNAME  # own id
    state.state = State.FOLLOWER  # state of own state machine
    state.term = 0  # current term
    state.log = ReplicatedLog()  # state of the current replicated log
    # discover other services
    state.replicas = discover_replicas(settings)
    if len(state.replicas) % 2 != 0:
        # there is an even number of nodes in the cluster (counting self) - this
        # can't work
        raise ValueError("Even number of nodes in cluster.")
    state.vote = None  # id of the node we voted for
    state.leader = None  # id if the node that is leader


settings: Settings = get_settings()
app: FastAPI = create_app(settings)
logging_setup(settings)
raft_setup(app.state, settings)


@app.exception_handler(ApiException)
def api_exception_handler(request: Request, e: ApiException) -> JSONResponse:
    """
    Global FastAPI exception handler for base class of all informative
    exceptions (everything except 5xx). Whenever an ApiException is raised in a
    route, the handler will catch and transform it into an error JSONReponse
    that will be delivered as response to the request.

    Parameters
    ----------
    request
        The incoming HTTP request.
    e
        The ApiException that got caught.

    Returns
    -------
    JSONResponse
        The response to be sent.
    """
    e.id = f"{settings.APP_NAME}.{e.id}"
    json_compatible_response = jsonable_encoder(
        ApiErrorResponse(error=e, apiVersion="1.0"), exclude_none=True
    )
    response = JSONResponse(content=json_compatible_response, status_code=e.status_code)
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exception):
    return api_exception_handler(
        request, BadRequestException(details={"errors": exception.errors()})
    )
