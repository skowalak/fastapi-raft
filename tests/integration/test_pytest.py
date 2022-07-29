import pytest
from fastapi.testclient import TestClient


class TestBasicRoutes:
    pytestmark = pytest.mark.skip(
        reason="currently not working due to discovery mechanism"
    )

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="")
    async def test_get_health(client: TestClient):
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="")
    async def test_get_invalid_path(client: TestClient):
        response = client.get("/wkkekfnoi")
        assert response.status_code == 404
