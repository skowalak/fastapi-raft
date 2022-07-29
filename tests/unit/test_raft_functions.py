import datetime
from unittest import mock
import threading
import pytest
from fastapi.applications import State as FastAPIState


class TestRaftFunctions:
    follower_executor_thread = "app.raft.functions.FollowerExecutorThread.start"

    @pytest.mark.asyncio
    async def test_term_reset_case_candidate(self):
        # setup
        from app.api.v1.models import State

        test_time = datetime.datetime.utcnow()
        state = FastAPIState()
        state.state = State.CANDIDATE
        state.term = 0
        state.candidature = threading.Thread()
        state.executor = threading.Thread()
        state.ping_time = test_time

        # execution
        from app.raft.functions import term_reset

        term_reset(state, 1)

        # test
        assert state.state is State.FOLLOWER
        assert state.ping_time != test_time
        assert state.term == 1

    @pytest.mark.asyncio
    @mock.patch(follower_executor_thread)
    async def test_term_reset_case_leader(self, mock):
        # setup
        from app.api.v1.models import State

        test_time = datetime.datetime.utcnow()
        state = FastAPIState()
        state.term = 0
        state.candidature = threading.Thread()
        state.executor = threading.Thread()
        state.state = State.LEADER

        # execution
        from app.raft.functions import term_reset

        term_reset(state, 1)

        # test
        mock.assert_called_once()
        assert state.state is State.FOLLOWER
        assert state.term == 1

    @pytest.mark.asyncio
    async def test_term_reset_case_follower(self):
        # setup
        from app.api.v1.models import State

        test_time = datetime.datetime.utcnow()
        state = FastAPIState()
        state.term = 0
        state.state = State.FOLLOWER

        # execution
        from app.raft.functions import term_reset

        term_reset(state, 1)

        # test
        assert state.state is State.FOLLOWER
        assert state.ping_time != test_time
        assert state.term == 1
