"""Entrypoint and setup functions.

* FastAPI app factory
* logging setup
* start inital Raft thread

"""

import datetime
import logging
import logging.config
import random
import sys

from fastapi import FastAPI
from fastapi.applications import State as FastAPIState
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api.exceptions import ApiException, BadRequestException
from app.api.models import ApiErrorResponse
from app.api.v1.consensus_endpoints import consensus_router
from app.config import Settings, get_settings
from app.raft.discovery import discover_replicas, get_replica_name_by_hostname
from app.raft.functions import FollowerExecutorThread, State


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
    lcl_app.include_router(consensus_router, prefix="/api/v1/raft", tags=["raft", "v1"])

    return lcl_app


def logging_setup(settings: Settings):
    """
    Set up python stdlib logging.

    Parameters
    ----------
    settings : Settings
        configuration object
    """
    log_level = settings.LOGGING

    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=log_level)
    lcl_logger = logging.getLogger()
    lcl_logger.setLevel(log_level)

    logging.config.dictConfig(settings.LOGGING_CONFIG)


def raft_setup(state: FastAPIState, settings: Settings):
    """Set values needed for Raft"""
    state.app_name = get_replica_name_by_hostname(settings.HOSTNAME)
    state.id = settings.HOSTNAME  # own id
    state.state = State.FOLLOWER  # state of own state machine
    state.leader_script = settings.SCRIPT_LEADER_PATH
    state.follower_script = settings.SCRIPT_FOLLOWER_PATH
    state.term = 0  # current term
    # discover other services
    state.replicas = discover_replicas(settings.APP_NAME, state.id)
    if len(state.replicas) % 2 != 0:
        # there is an even number of nodes in the cluster (counting self) - this
        # can't work
        raise ValueError("Even number of nodes in cluster.")
    state.vote = None  # id of the node we voted for
    state.timeout = datetime.timedelta(
        milliseconds=random.randrange(  # nosec (bandit: not used for security/crypto)
            settings.ELECTION_TIMEOUT_LOWER_MILLIS,
            settings.ELECTION_TIMEOUT_UPPER_MILLIS,
        )
    )
    state.heartbeat_repeat = (
        settings.HEARTBEAT_REPEAT_MILLIS / 1000
    )  # need to be float seconds
    state.leader = None  # id of the node that is leader


app_settings: Settings = get_settings()
app: FastAPI = create_app(app_settings)
logging_setup(app_settings)
logger = logging.getLogger(__name__)
raft_setup(app.state, app_settings)
app.state.executor = FollowerExecutorThread(args=(app.state,))
app.state.executor.start()


@app.exception_handler(ApiException)
def api_exception_handler(request: Request, error: ApiException) -> JSONResponse:
    """
    Global FastAPI exception handler for base class of all informative
    exceptions (everything except 5xx). Whenever an ApiException is raised in a
    route, the handler will catch and transform it into an error JSONReponse
    that will be delivered as response to the request.

    Parameters
    ----------
    request
        The incoming HTTP request.
    error
        The ApiException that got caught.

    Returns
    -------
    JSONResponse
        The response to be sent.
    """
    error.id = f"{app_settings.APP_NAME}.{error.id}"
    json_compatible_response = jsonable_encoder(
        ApiErrorResponse(error=error, apiVersion="1.0"), exclude_none=True
    )
    # add raft info to error response
    json_compatible_response["error"]["sender"] = request.app.state.app_name
    json_compatible_response["error"]["term"] = request.app.state.term
    json_compatible_response["error"]["id"] = request.app.state.id
    response = JSONResponse(
        content=json_compatible_response, status_code=error.status_code
    )
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exception):
    """Redirect pydantic validation errors to main error handler

    Parameters
    ----------
    request : Request
        The request that caused the error
    exception : RequestValidationError
        The exception thrown by Pydantic

    Returns
    -------
    Function call to the main exception handler
        Handled BadRequestException
    """
    logger.warning("request validation exception: %s", str(exception))
    return api_exception_handler(
        request, BadRequestException(details={"errors": exception.errors()})
    )
