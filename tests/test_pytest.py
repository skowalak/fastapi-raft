import pytest
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_get_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_invalid_path(client: TestClient):
    response = client.get("/wkkekfnoi")
    assert response.status_code == 404
