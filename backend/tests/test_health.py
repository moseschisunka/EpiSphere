from fastapi.testclient import TestClient

from app.main import app


def test_app_health_endpoint_imports_and_responds():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
