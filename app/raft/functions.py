import datetime
import logging
import threading
from http import HTTPStatus

import requests
from app.api.v1.models import (
    HeartbeatRequestSchema,
    RaftStateException,
    State,
    VoteRequestSchema,
)
from fastapi.applications import State as FastAPIState

logger: logging.Logger = logging.getLogger(__name__)


class StateExecutorThread(threading.Thread):
    """
    These threads execute sending heartbeats and votes.
    Needs to implement a method to gracefully stop as to not corrupt internal
    state.
    """

    def __init__(self, *args, **kwargs):
        super(StateExecutorThread, self).__init__(*args, **kwargs)
        self._stop_evt = threading.Event()

    def stop(self) -> None:
        self._stop_evt.set()

    def stopped(self) -> bool:
        return self._stop_evt.is_set()


class FollowerExecutorThread(StateExecutorThread):
    """Models the behaviour of a node in the State.FOLLOWER state."""

    def run(self, state: FastAPIState) -> None:
        state.state = State.FOLLOWER
        state.ping_time = datetime.datetime.utcnow()
        while not self._stop_evt.wait(timeout=1):
            be_follower(state)


class CandidateExecutorThread(StateExecutorThread):
    """Models the behaviour of a node in the State.CANDIDATE state."""

    def run(self, state: FastAPIState) -> None:
        state.state = State.CANDIDATE
        if state.replicas:
            state.term += 1
            state.vote = state.id
            state.my_votes = 1
        else:
            # no nodes left except us? no need to be a candidate
            return

        while not self._stop_evt.wait(timeout=1):
            try:
                be_candidate(state)
            except RaftStateException:  # end of candidature
                break


class LeaderExecutorThread(StateExecutorThread):
    """Models the behaviour of a node in the State.LEADER state."""

    def run(self, state: FastAPIState) -> None:
        state.state = State.LEADER
        while not self._stop_evt.wait(timeout=1):
            try:
                be_leader(state)
            except RaftStateException:  # end of leadership
                break


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
        state.candidature = CandidateExecutorThread()
        state.candidature.start(state)


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
    vote_for = state.replicas.copy()
    for replica, replica_ip in vote_for.items():
        # ask replica to vote for us
        try:
            response = requests.put(
                f"http://{replica}/api/v1/raft/vote",
                json=VoteRequestSchema(term=state.term).json(),
            )
        except requests.exceptions.ConnectionError as error:
            logger.info(f"got error: {str(error)}")
            continue
        response_data = response.json()
        if response.status_code == HTTPStatus.OK:
            # we got a vote
            del vote_for[replica]
            state.my_votes += 1
            if state.my_votes > len(state.replicas) // 2:
                # we have the majority
                logging.info("got majority of votes, becoming leader")
                state.executor = LeaderExecutorThread()
                state.executor.start(state)
                raise RaftStateException()  # end candidature
        else:
            # we did not get a vote
            if state.term < response_data["term"]:
                term_reset(state, response_data["term"])


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
    for replica, replica_ip in followers.items():
        try:
            response = requests.post(
                f"http://{replica}/api/v1/raft/log",
                json=HeartbeatRequestSchema(term=state.term),
            )
        except requests.exceptions.ConnectionError as error:
            logger.info(f"got error: {str(error)}")
            continue
        response_data = response.json()
        if response.status_code != HTTPStatus.OK:
            if state.term < response_data["term"]:
                term_reset(state, response_data["term"])


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
        state.candidature.join()
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
        state.executor.join()  # wait for stop
    state.state = State.FOLLOWER
    state.executor = FollowerExecutorThread()
    state.executor.start(state)  # start becoming a follower


def term_reset(state: FastAPIState, next_term: int) -> None:
    """
    Handles a term reset / a term update

    Parameters
    ----------
    state : FastAPIState
        global state object
    """
    logger.debug(f"term update: {state.term} -> {next_term}")
    state.term = next_term
    if state.state is State.CANDIDATE:
        reset_candidate(state)
    elif state.state is State.LEADER:
        reset_leader(state)
    elif state.state is State.FOLLOWER:
        state.ping_time = datetime.datetime.utcnow()
