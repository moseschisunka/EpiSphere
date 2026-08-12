from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
import app.main as main_module
from app.db.models import Base


def test_app_health_endpoint_imports_and_responds():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
    assert response.headers["X-Request-ID"]


def test_app_readiness_endpoint_checks_database(monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    monkeypatch.setattr(main_module, "SessionLocal", sessionmaker(bind=engine))
    client = TestClient(app)
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_component_readiness_reports_local_dependencies(monkeypatch, tmp_path):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(main_module, "SessionLocal", sessionmaker(bind=engine))
    monkeypatch.setattr(main_module.settings, "REDIS_REQUIRED", False)
    monkeypatch.setattr(main_module.settings, "UPLOAD_DIR", tmp_path)
    client = TestClient(app)

    response = client.get("/ready/components")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["components"]["database"]["status"] == "ready"
    assert payload["components"]["redis"]["status"] == "not_required"
    assert payload["components"]["ingestion_worker_queue"]["stale_running_jobs"] == 0


def test_request_id_is_preserved_and_metrics_are_exposed(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    monkeypatch.setattr(main_module, "SessionLocal", sessionmaker(bind=engine))
    client = TestClient(app)
    response = client.get("/health", headers={"X-Request-ID": "pilot-request-123"})
    metrics = client.get("/metrics")

    assert response.headers["X-Request-ID"] == "pilot-request-123"
    assert metrics.status_code == 200
    assert "episphere_http_requests_total" in metrics.text
