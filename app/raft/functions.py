import datetime
from fastapi.applications import State as FastAPIState
from app.raft.datastructures import State


def reset_candidate(state: FastAPIState) -> None:
    # TODO (skowalak): stop election
    state.ping_time = datetime.datetime.utcnow()
    state.state = State.FOLLOWER


def reset_leader(state: FastAPIState) -> None:
    # TODO (skowalak): stop leader state
    # TODO (skowalak): start follower state
    pass


def term_reset(state: FastAPIState) -> None:
    """
    Handles a term reset / a term update

    Parameters
    ----------
    state : FastAPIState
        global state object
    """
    if state.state == State.CANDIDATE:
        reset_candidate(state)
    elif state.state == State.LEADER:
        reset_leader(state)
