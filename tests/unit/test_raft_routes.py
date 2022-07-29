from unittest.mock import patch
import datetime
import pytest
from fastapi.applications import State as FastAPIState


class TestRaftRoutes:
    @pytest.mark.asyncio
    async def test_term_reset_case_candidate(self):
        # setup
        from app.raft.datastructures import State

        test_time = datetime.datetime.utcnow()
        state = FastAPIState()
        state.state = State.CANDIDATE
        state.ping_time = test_time

        # execution
        from app.raft.functions import term_reset

        term_reset(state)

        # test
        assert state.state is State.FOLLOWER
        assert state.ping_time != test_time

    @pytest.mark.asyncio
    async def test_term_reset_case_leader(self):
        # setup
        from app.raft.datastructures import State

        test_time = datetime.datetime.utcnow()
        state = FastAPIState()
        state.state = State.LEADER

        # execution
        from app.raft.functions import term_reset

        term_reset(state)

        # test
        assert state.state is State.FOLLOWER
