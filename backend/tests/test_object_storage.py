import pytest
from pydantic import ValidationError

from app.core.config import Settings


def production_settings(**overrides):
    values = {
        "ENVIRONMENT": "production",
        "SECRET_KEY": "a-strong-production-secret",
        "NEWS_AGENT_API_KEY": "news-key",
        "DATASET_AGENT_API_KEY": "dataset-key",
        "INTEROP_AGENT_API_KEY": "interop-key",
        "N8N_ENCRYPTION_KEY": "n8n-encryption-key",
        "EMAIL_VERIFICATION_REQUIRED": True,
        "MFA_REQUIRED_FOR_PRIVILEGED": True,
        "SMTP_HOST": "smtp.example.test",
        "SMTP_USER": "episphere",
        "SMTP_PASSWORD": "smtp-password",
        "WORKER_HEARTBEAT_REQUIRED": True,
    }
    values.update(overrides)
    return values


def test_production_rejects_container_local_object_storage():
    with pytest.raises(ValidationError, match="OBJECT_STORAGE_BACKEND must be s3"):
        Settings(**production_settings())


def test_production_accepts_explicit_s3_object_storage_configuration():
    configured = Settings(**production_settings(
        OBJECT_STORAGE_BACKEND="s3",
        OBJECT_STORAGE_BUCKET="episphere-private-reports",
        OBJECT_STORAGE_ACCESS_KEY="access-key",
        OBJECT_STORAGE_SECRET_KEY="secret-key",
    ))

    assert configured.OBJECT_STORAGE_BACKEND == "s3"
