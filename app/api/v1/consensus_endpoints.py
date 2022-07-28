import structlog
from app.api.exceptions import BadRequestException, NotImplementedException
from app.api.v1.models import (
    AppendLogRequestSchema,
    AppendLogResponseSchema,
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


@consensus_router.get("/vote")
async def get_vote(
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
    if state.replicas.get(v_req.sender_id):
        await logger.info(f"vote requested from {v_req.sender_id}.")
    else:
        # We do not know this node (not discovered)
        await logger.info(f"reject unknown node {v_req.sender_id}")
        raise BadRequestException(message=f"Node ID {v_req.sender_id} unknown.")

    # check if term is correct
    if state.term > v_req.term:
        # requests term is out of date, rejecting
        await logger.info(f"reject outdated term ({v_req.term}) vote request")
        raise BadRequestException(message=f"Outdated term: {v_req.term}.")

    elif state.term == v_req.term:
        # terms match
        await logger.debug(f"current term {state.term} == {v_req.term}")
        if not state.vote or state.vote == v_req.sender_id:
            # we want to vote for this node
            return V1ApiResponse(data=VoteResponseSchema(term=state.term))
        else:
            # we do not want to vote for this node
            raise BadRequestException(message=f"Did not vote for {v_req.sender_id}.")

    elif state.term < v_req.term:
        # own term is outdated
        await logger.info(f"term {state.term} out of date by {v_req.term - state.term}")
        state.term = v_req.term
        await logger.debug(f"updated term: {state.term}")
        # if leader, step down, then vote
        background_tasks.add_task(functions.term_reset, state)
        state.vote = v_req.sender_id

    return V1ApiResponse(data=VoteRequestSchema(term=state.term))


@consensus_router.post("/log")
async def append_log(request: Request, log_appendix: AppendLogRequestSchema):
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
    return V1ApiResponse(data=AppendLogResponseSchema)
