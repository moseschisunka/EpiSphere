from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
import app.main as main_module


def test_app_health_endpoint_imports_and_responds():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_app_readiness_endpoint_checks_database(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    monkeypatch.setattr(main_module, "SessionLocal", sessionmaker(bind=engine))
    client = TestClient(app)
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
