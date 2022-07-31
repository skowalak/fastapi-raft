"""Functions and function container objects for Raft."""
import datetime
import enum
import logging
import subprocess
import threading
from http import HTTPStatus

import requests
from fastapi.applications import State as FastAPIState

from app.api.v1.models import RaftMessageSchema, RaftStateException

logger: logging.Logger = logging.getLogger(__name__)


class State(enum.Enum):
    """Possible states a nodes state machine can hold."""

    FOLLOWER = "FOLLOWER"
    CANDIDATE = "CANDIDATE"
    LEADER = "LEADER"


class StateExecutorThread(threading.Thread):
    """
    These threads execute sending heartbeats and votes.
    Needs to implement a method to gracefully stop as to not corrupt internal
    state.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stop_evt = threading.Event()

    def stop(self) -> None:
        """Gracefully stop state executor thread."""
        self._stop_evt.set()

    def stopped(self) -> bool:
        """Check if state executor is done stopping.

        Returns
        -------
        bool
            True if Thread can be joined.
        """
        return self._stop_evt.is_set()


class FollowerExecutorThread(StateExecutorThread):
    """Models the behaviour of a node in the State.FOLLOWER state."""

    def run(self) -> None:
        state = self._args[0]
        state.state = State.FOLLOWER
        state.ping_time = datetime.datetime.utcnow()
        # run payload follower script
        subprocess.Popen(["/bin/sh", state.follower_script])
        while not self._stop_evt.wait(timeout=state.heartbeat_repeat):
            be_follower(state)


class CandidateExecutorThread(StateExecutorThread):
    """Models the behaviour of a node in the State.CANDIDATE state."""

    def run(self) -> None:
        state = self._args[0]
        state.state = State.CANDIDATE
        state.possible_voters = state.replicas.copy()
        state.actual_voters = []
        if state.replicas:
            state.term += 1
            state.vote = state.id
            state.my_votes = 1
        else:
            # no nodes left except us? no need to be a candidate
            return

        while not self._stop_evt.wait(timeout=state.heartbeat_repeat):
            try:
                be_candidate(state)
            except RaftStateException:  # end of candidature
                return


class LeaderExecutorThread(StateExecutorThread):
    """Models the behaviour of a node in the State.LEADER state."""

    def run(self) -> None:
        state = self._args[0]
        state.state = State.LEADER
        # run payload leader script
        subprocess.Popen(["/bin/sh", state.leader_script])
        while not self._stop_evt.wait(timeout=state.heartbeat_repeat):
            try:
                be_leader(state)
            except RaftStateException:  # end of leadership
                return


def be_follower(state: FastAPIState) -> None:
    """
    Start the follower process, while the app is listening for the other nodes.

    Parameters
    ----------
    state : FastAPIState
        global state object
    """
    # check if time since last ping is over
    if datetime.datetime.utcnow() - state.ping_time > state.timeout:
        # previous leader timed out, time to be a candidate
        state.candidature = CandidateExecutorThread(args=(state,))
        state.candidature.start()


def be_candidate(state: FastAPIState) -> None:
    """
    Start the candidate process, this will be run in parallel to retrying to
    reach the old leader for a heartbeat.

    Parameters
    ----------
    state : FastAPIState
        global state object

    Raises
    ------
    RaftStateException
        when candidature needs to be ended (i.e. becoming leader next)
    """
    for replica in state.possible_voters.keys():
        if replica in state.actual_voters:
            # already voted for us, skip
            continue

        # ask replica to vote for us
        try:
            response = requests.put(
                f"http://{replica}/api/v1/raft/vote",
                json=RaftMessageSchema.from_state_object(state).dict(),
                timeout=0.5,
            )
        except requests.RequestException as error:
            logger.info("got error: %s", str(error))
            continue
        response_data = response.json()
        if response.status_code == HTTPStatus.OK:
            # we got a vote
            state.actual_voters.append(replica)
            state.my_votes += 1
            if state.my_votes > len(state.replicas) // 2:
                # we have the majority
                logger.info("got majority of votes, becoming leader")
                state.state = State.LEADER
                state.executor = LeaderExecutorThread(args=(state,))
                state.executor.start()
                raise RaftStateException()  # end candidature
        else:
            # we did not get a vote
            if state.term < response_data["error"]["term"]:
                term_reset(state, response_data["error"]["term"])


def be_leader(state: FastAPIState) -> None:
    """
    Send heartbeats / log appends to followers.

    We do not send log appends, because this is a demo and we don't have any
    data to send.

    Parameters
    ----------
    state : FastAPIState
        global state object

    Raises
    ------
    RaftStateException
        when candidature needs to be ended (i.e. becoming leader next)
    """

    followers = state.replicas.copy()
    for replica, _ in followers.items():
        try:
            response = requests.post(
                f"http://{replica}/api/v1/raft/log",
                json=RaftMessageSchema.from_state_object(state).dict(),
                timeout=0.5,
            )
        except requests.RequestException as error:
            logger.info("got error: %s", str(error))
            continue
        response_data = response.json()
        if response.status_code != HTTPStatus.OK:
            logger.info("leader got newer term, resetting")
            if state.term < response_data["error"]["term"]:
                term_reset(state, response_data["error"]["term"])


def reset_candidate(state: FastAPIState) -> None:
    """
    Term reset in the candidate state.

    Parameters
    ----------
    state : FastAPIState
        global state object
    """
    # stop running election
    if state.candidature.is_alive():
        state.candidature.stop()
    state.ping_time = datetime.datetime.utcnow()
    state.state = State.FOLLOWER  # now we are only a follower


def reset_leader(state: FastAPIState) -> None:
    """
    Term reset in the leader state.

    Parameters
    ----------
    state : FastAPIState
        global state object
    """
    if state.executor.is_alive():
        state.executor.stop()  # stop leadership
    state.state = State.FOLLOWER
    state.executor = FollowerExecutorThread(args=(state,))
    state.executor.start()  # start becoming a follower


def term_reset(
    state: FastAPIState, next_term: int, current_role: State = State.FOLLOWER
) -> None:
    """
    Handles a term reset / a term update

    Parameters
    ----------
    state : FastAPIState
        global state object

    next_term : int
        the received term

    current_role : State
        the role, this reset was triggered in
    """
    logger.debug("resetting current term: %s", state.term)
    if next_term > state.term:
        logger.debug("term update: %s -> %s", state.term, next_term)
    state.term = next_term
    if current_role is State.CANDIDATE:
        reset_candidate(state)
    elif current_role is State.LEADER:
        reset_leader(state)
