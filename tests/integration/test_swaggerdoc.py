from fastapi.testclient import TestClient
from app.config import Settings


def test_docs_html(client: TestClient, settings: Settings):
    response = client.get(settings.FASTAPI_DOCS)
    assert response.status_code == 200


def test_get_health(client: TestClient, settings: Settings):
    response = client.get(settings.FASTAPI_SCHEM)
    assert response.status_code == 200
