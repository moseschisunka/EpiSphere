import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request

from app.core.config import Settings, settings
from app.core.dependencies import ServicePrincipal, get_agent_or_admin, get_interop_agent_or_admin, get_news_agent_or_admin
from app.core.security import create_access_token
from app.db.models import Base, Role, User
from app.schemas.public_datasets import WhoGhoIngestRequest


def make_request(headers: dict[str, str]) -> Request:
    return Request({
        "type": "http",
        "method": "POST",
        "path": "/api/v1/news",
        "headers": [(key.lower().encode(), value.encode()) for key, value in headers.items()],
    })


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_agent_api_key_returns_explicit_service_principal(monkeypatch):
    db = make_session()
    monkeypatch.setattr(settings, "AGENT_API_KEY", "agent-secret")

    principal = get_agent_or_admin(make_request({"X-API-Key": "agent-secret"}), db)

    assert isinstance(principal, ServicePrincipal)
    assert principal.name == "n8n"
    assert principal.auth_method == "x-api-key"
    db.close()


def test_news_agent_key_is_scoped_and_separately_identified(monkeypatch):
    db = make_session()
    monkeypatch.setattr(settings, "AGENT_API_KEY", "legacy-secret")
    monkeypatch.setattr(settings, "NEWS_AGENT_API_KEY", "news-secret")

    principal = get_news_agent_or_admin(make_request({"X-API-Key": "news-secret"}), db)
    assert principal.name == "n8n-news"

    with pytest.raises(Exception) as exc_info:
        get_news_agent_or_admin(make_request({"X-API-Key": "legacy-secret"}), db)
    assert exc_info.value.status_code == 401
    db.close()


def test_interop_agent_key_does_not_fall_back_to_legacy_shared_key(monkeypatch):
    db = make_session()
    monkeypatch.setattr(settings, "AGENT_API_KEY", "legacy-secret")
    monkeypatch.setattr(settings, "INTEROP_AGENT_API_KEY", "interop-secret")

    principal = get_interop_agent_or_admin(make_request({"X-API-Key": "interop-secret"}), db)
    assert principal.name == "n8n-interop"

    with pytest.raises(Exception) as exc_info:
        get_interop_agent_or_admin(make_request({"X-API-Key": "legacy-secret"}), db)
    assert exc_info.value.status_code == 401
    db.close()


def test_wrong_or_disabled_agent_api_key_is_rejected(monkeypatch):
    db = make_session()
    request = make_request({"X-API-Key": "wrong-secret"})

    monkeypatch.setattr(settings, "AGENT_API_KEY", "agent-secret")
    with pytest.raises(Exception) as wrong_key:
        get_agent_or_admin(request, db)
    assert wrong_key.value.status_code == 401

    monkeypatch.setattr(settings, "AGENT_API_KEY", "")
    with pytest.raises(Exception) as disabled_key:
        get_agent_or_admin(make_request({"X-API-Key": "agent-secret"}), db)
    assert disabled_key.value.status_code == 401
    db.close()


def test_malformed_admin_subject_fails_closed_instead_of_raising_value_error(monkeypatch):
    db = make_session()
    monkeypatch.setattr(settings, "AGENT_API_KEY", "")
    token = create_access_token({"sub": "not-an-integer"})

    with pytest.raises(Exception) as exc_info:
        get_agent_or_admin(make_request({"Authorization": f"Bearer {token}"}), db)

    assert exc_info.value.status_code == 401
    db.close()


def test_admin_bearer_token_is_accepted(monkeypatch):
    db = make_session()
    monkeypatch.setattr(settings, "AGENT_API_KEY", "")
    role = Role(name="admin", description="Administrator")
    db.add(role)
    db.flush()
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password="test-hash",
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id)})

    authenticated_user = get_agent_or_admin(
        make_request({"Authorization": f"Bearer {token}"}), db
    )

    assert authenticated_user.id == user.id
    db.close()


def test_who_indicator_code_rejects_path_injection_shape():
    with pytest.raises(ValueError):
        WhoGhoIngestRequest(indicator_code="../../etc/passwd", disease_id=2)


def test_who_ingest_rejects_non_positive_disease_id():
    with pytest.raises(ValueError):
        WhoGhoIngestRequest(indicator_code="CHOLERA_0001", disease_id=0)


def test_production_settings_fail_closed_without_integration_secrets():
    with pytest.raises(ValueError, match="NEWS_AGENT_API_KEY"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="a-real-production-secret",
            NEWS_AGENT_API_KEY="",
            DATASET_AGENT_API_KEY="",
            N8N_ENCRYPTION_KEY="",
        )
