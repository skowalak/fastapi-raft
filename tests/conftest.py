import asyncio
import os
from typing import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ.update({
    "HOSTNAME": "asdfghjkl",
    "NUM_REPLICAS": "1",   
})


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def initialize_tests():
    yield


@pytest.fixture(scope="function")
def app():
    """
    Generate a new FastAPI app instance for every test case.
    """
    from app import main

    app = main.app

    return app


@pytest.fixture(scope="function")
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
def settings():
    from app.config import get_settings

    return get_settings()

