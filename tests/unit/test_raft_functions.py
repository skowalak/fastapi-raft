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
        from app.raft.functions import State

        test_time = datetime.datetime.utcnow()
        state = FastAPIState()
        state.state = State.CANDIDATE
        state.term = 0
        state.candidature = threading.Thread()
        state.executor = threading.Thread()
        state.ping_time = test_time

        # execution
        from app.raft.functions import reset_candidate

        reset_candidate(state)

        # test
        assert state.state is State.FOLLOWER
        assert state.ping_time != test_time

    @pytest.mark.asyncio
    @mock.patch(follower_executor_thread)
    async def test_term_reset_case_leader(self, mock):
        # setup
        from app.raft.functions import State

        test_time = datetime.datetime.utcnow()
        state = FastAPIState()
        state.term = 0
        state.candidature = threading.Thread()
        state.executor = threading.Thread()
        state.state = State.LEADER

        # execution
        from app.raft.functions import reset_leader

        reset_leader(state)

        # test
        mock.assert_called_once()
        assert state.state is State.FOLLOWER

    @pytest.mark.asyncio
    async def test_term_reset_case_follower(self):
        # setup
        from app.raft.functions import State

        state = FastAPIState()
        state.term = 0
        state.state = State.FOLLOWER

        # execution
        from app.raft.functions import term_reset

        term_reset(state, 1, state.state)

        # test
        assert state.state is State.FOLLOWER
        assert state.term == 1

    @pytest.mark.asyncio
    @mock.patch("app.raft.functions.reset_candidate")
    async def test_term_reset_call_candidate(self, mock_candidate: mock.Mock):
        # setup
        from app.raft.functions import State

        state = FastAPIState()
        state.term = 0
        state.state = State.CANDIDATE

        # execute
        from app.raft.functions import term_reset

        term_reset(state, 1, state.state)

        # test
        assert state.term == 1
        mock_candidate.assert_called_once_with(state)

    @pytest.mark.asyncio
    @mock.patch("app.raft.functions.reset_leader")
    async def test_term_reset_call_leader(self, mock_leader: mock.Mock):
        # setup
        from app.raft.functions import State

        state = FastAPIState()
        state.term = 0
        state.state = State.LEADER

        # execute
        from app.raft.functions import term_reset

        term_reset(state, 1, state.state)

        # test
        assert state.term == 1
        mock_leader.assert_called_once_with(state)

    @pytest.mark.asyncio
    async def test_state_enum(self):
        from app.raft.functions import State

        assert State.CANDIDATE.value == "CANDIDATE"
        assert State.FOLLOWER.value == "FOLLOWER"
        assert State.LEADER.value == "LEADER"

    @pytest.mark.asyncio
    async def test_state_executor_stop(self):
        # setup
        from app.raft.functions import StateExecutorThread
        from fastapi.applications import State as FastAPIState

        def test_run_increment_one(self) -> None:
            state = self._args[0]
            while True:
                state.test_int += 1
                if self._stop_evt.is_set():
                    break

        test_state = FastAPIState()
        test_state.test_int = 0
        test_executor = StateExecutorThread(args=(test_state,))
        test_executor.run = test_run_increment_one.__get__(
            test_executor, StateExecutorThread
        )

        # execute
        test_executor.stop()  # set stop flag before starting so loop runs once
        test_executor.start()
        test_executor.join()

        # test
        assert test_state.test_int == 1

    @pytest.mark.asyncio
    @pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")
    async def test_be_follower(self):
        # setup
        from datetime import datetime, timedelta
        from fastapi.applications import State as FastAPIState

        test_state = FastAPIState()
        test_state.ping_time = datetime.utcnow()
        test_state.timeout = timedelta(
            milliseconds=0
        )  # always smaller than utcnow difference

        # execute
        from app.raft.functions import be_follower

        be_follower(test_state)

        # test
        from app.raft.functions import CandidateExecutorThread

        assert isinstance(test_state.candidature, CandidateExecutorThread)
        assert not test_state.candidature.is_alive()

        # cleanup
        test_state.candidature.stop()
        test_state.candidature.join()
