"""FastAPI endpoint definitions for Raft operations.

* get status
* request vote
* append log / send heartbeat

"""
import datetime
import logging

from fastapi import APIRouter, Request

from app.api.exceptions import BadRequestException
from app.api.v1.models import (
    RaftMessageSchema,
    RaftStatusResponseSchema,
    V1ApiResponse,
)
from app.config import Settings, get_settings
from app.raft import functions

logger: logging.Logger = logging.getLogger(__name__)
settings: Settings = get_settings()
consensus_router: APIRouter = APIRouter()


@consensus_router.get("/")
async def get_state(request: Request):
    """
    Get the entire state of this node for the monitor.
    See `README.md` # usage-example

    Parameters
    ----------
    request : Request
        request object

    Returns
    -------
    V1ApiResponse[RaftStatusResponseSchema]
        the state as json
    """
    state = request.app.state
    return V1ApiResponse(
        data=RaftStatusResponseSchema(
            app_name=state.app_name.split(".", maxsplit=1)[0],
            id=state.id,
            state=state.state.value,
            term=state.term,
        )
    )


@consensus_router.put("/vote")
async def request_vote(request: Request, v_req: RaftMessageSchema):
    """
    Request a vote from this node.

    Parameters
    ----------
    request : Request
        The Starlette/FastAPI request object.

    Returns
    -------
    V1ApiResponse[VoteResponseSchema]
        Reponse object.
    """
    state = request.app.state

    # check if node is known
    if state.replicas.get(v_req.sender):
        logger.info("vote requested from %s", v_req.sender)
    else:
        # We do not know this node (not discovered)
        logger.info("reject unknown node %s", v_req.sender)
        # mypy problems with pydantic.dataclasses, so disabling the type check for this instance
        raise BadRequestException(message=f"Node app_name {v_req.sender} unknown.")  # type: ignore

    # check if term is correct
    if v_req.term < state.term:
        # requests term is out of date, rejecting
        logger.info("reject outdated term (%s) vote request", v_req.term)
        # mypy has problems with pydantic.dataclasses, so I am disabling the type check for this instance
        raise BadRequestException(message=f"Outdated term: {v_req.term}.")  # type: ignore

    if state.term == v_req.term:
        # terms match
        logger.debug("current term %s == %s", state.term, v_req.term)
        if not state.vote or state.vote == v_req.sender:
            # we want to vote for this node
            return V1ApiResponse(data=RaftMessageSchema.from_state_object(state))

        # we do not want to vote for this node
        # mypy problems with pydantic.dataclasses, so disabling the type check for this instance
        raise BadRequestException(message=f"Did not vote for {v_req.sender}.")  # type: ignore

    if v_req.term > state.term:
        # own term is outdated
        logger.info(
            "term %s out of date by %s",
            state.term,
            (v_req.term - state.term),
        )
        # if leader, step down, then vote
        functions.term_reset(state, v_req.term, state.state)
        state.vote = v_req.sender

    return V1ApiResponse(data=RaftMessageSchema.from_state_object(state))


@consensus_router.post("/log")
async def append_log(request: Request, l_req: RaftMessageSchema):
    """
    Append an entry to this nodes log. In Raft terms this may also be called a _heartbeat_.

    Parameters
    ----------
    request : Request
        The Starlette/FastAPI request object.

    Returns
    -------
    V1ApiResponse
        Reponse object.
    """
    state = request.app.state

    if state.replicas.get(l_req.sender):
        logger.info("heartbeat / log append from %s", l_req.sender)
    else:
        # we do not know this node
        logger.info("reject unknown node %s", l_req.sender)
        # mypy problems with pydantic.dataclasses, so disabling the type check for this instance
        raise BadRequestException(message=f"Node ID {l_req.sender} unknown.")  # type: ignore

    # check if term is correct
    if state.term > l_req.term:
        # term out of date, rejecting
        logger.info("reject outdated term %s log append", l_req.term)
        # mypy has problems with pydantic.dataclasses, so I am disabling the type check for this instance
        raise BadRequestException(message=f"Outdated term: {l_req.term}")  # type: ignore

    # term is current or newer
    state.ping_time = datetime.datetime.utcnow()
    functions.term_reset(state, l_req.term, state.state)
    state.leader = l_req.sender

    return V1ApiResponse(data=RaftMessageSchema.from_state_object(state))
