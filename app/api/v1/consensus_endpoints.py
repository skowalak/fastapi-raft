import structlog
from app.api.exceptions import BadRequestException
from app.api.v1.models import (
    HeartbeatRequestSchema,
    HeartbeatResponseSchema,
    RaftStatusResponseSchema,
    V1ApiResponse,
    VoteRequestSchema,
    VoteResponseSchema,
)
from app.config import Settings, get_settings
from app.raft import functions
from fastapi import APIRouter, Request, BackgroundTasks

logger: structlog.stdlib.AsyncBoundLogger = structlog.get_logger(__name__)
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
            app_name=state.app_name,
            id=state.id,
            state=state.state.value,
            term=state.term,
        )
    )


@consensus_router.put("/vote")
async def request_vote(
    request: Request, v_req: VoteRequestSchema, background_tasks: BackgroundTasks
):
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
        await logger.info(f"vote requested from {v_req.sender}.")
    else:
        # We do not know this node (not discovered)
        await logger.info(f"reject unknown node {v_req.sender}")
        raise BadRequestException(message=f"Node ID {v_req.sender} unknown.")

    # check if term is correct
    if state.term > v_req.term:
        # requests term is out of date, rejecting
        await logger.info(f"reject outdated term ({v_req.term}) vote request")
        raise BadRequestException(message=f"Outdated term: {v_req.term}.")

    elif state.term == v_req.term:
        # terms match
        await logger.debug(f"current term {state.term} == {v_req.term}")
        if not state.vote or state.vote == v_req.sender:
            # we want to vote for this node
            return V1ApiResponse(data=VoteResponseSchema(term=state.term))
        else:
            # we do not want to vote for this node
            raise BadRequestException(message=f"Did not vote for {v_req.sender}.")

    elif state.term < v_req.term:
        # own term is outdated
        await logger.info(f"term {state.term} out of date by {v_req.term - state.term}")
        # if leader, step down, then vote
        background_tasks.add_task(functions.term_reset, state, v_req.term)
        state.vote = v_req.sender

    return V1ApiResponse(data=VoteRequestSchema(term=state.term))


@consensus_router.post("/log")
async def append_log(
    request: Request, l_req: HeartbeatRequestSchema, background_tasks=BackgroundTasks
):
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
        await logger.info(f"heartbeat / log append from {l_req.sender}")
    else:
        # we do not know this node
        await logger.info(f"reject unknown node {l_req.sender}")
        raise BadRequestException(message=f"Node ID {l_req.sender} unknown.")

    # check if term is correct
    if state.term > l_req.term:
        # term out of date, rejecting
        await logger.info(f"reject outdated term {l_req.term} log append")
        raise BadRequestException(message=f"Outdated term: {l_req.term}")
    else:
        # term is current or newer
        background_tasks.add_task(functions.term_reset, state, l_req.term)
        state.leader = l_req.sender

    return V1ApiResponse(data=HeartbeatResponseSchema(term=state.term))
