import asyncio
import os
from typing import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

DB_URL = "sqlite://:memory:"
TESTUSER_UID = "2d12fe46-380d-40ba-815a-edc0a606281c"
TESTUSER__FN = "Carlos Matos"
TESTUSER_EML = "d70a6635-edac-42ea-81e6-9db15252802a@invalid.tld"

# hook called after creation of session object, before collection
def pytest_sessionstart(session: pytest.Session):
    # inject sqlite memdb here
    os.environ["PSQL_URL"] = DB_URL


async def init_db(db_url: str, create_db: bool = False, schemas: bool = False) -> None:
    # create database here
    if create_db:
        print(f"PYTEST: Database created. {db_url=}")
    if schemas:
        await Tortoise.generate_schemas()
        print(f"PYTEST: Schemas generated.")


async def init(db_url: str = DB_URL) -> None:
    pass  # empty, because database is initiated by service.


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def initialize_tests():
    await init()
    yield
    # tear down database here


@pytest.fixture(scope="session")
async def current_user():
    from app.api.auth import User

    return User(
        id=TESTUSER_UID,
        full_name=TESTUSER__FN,
        email=TESTUSER_EML,
    )


@pytest.fixture(scope="function")
def app(current_user):
    """
    Generate a new FastAPI app instance for every test case.
    """
    from app import main
    from app.api.auth import User, get_auth, get_user

    app = main.app
    # include _old_ auth dep for compatibility
    app.dependency_overrides[get_auth] = lambda: {"sub": current_user.id}
    auth_deps = [
        get_user,
    ]
    for dep in auth_deps:
        app.dependency_overrides[dep] = lambda: current_user

    return app


@pytest.fixture(scope="function")
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
def settings():
    from app.config import get_settings

    return get_settings()
