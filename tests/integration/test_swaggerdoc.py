import pytest

from fastapi.testclient import TestClient
from app.config import Settings


class TestSwaggerDocumentation:
    pytestmark = pytest.mark.skip(reason="does not work with discovery by DNS")

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="")
    async def test_docs_html(client: TestClient, settings: Settings):
        response = client.get(settings.FASTAPI_DOCS)
        assert response.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="")
    async def test_openapi(client: TestClient, settings: Settings):
        response = client.get(settings.FASTAPI_SCHEM)
        assert response.status_code == 200
        assert response.content_type == "application/json"
