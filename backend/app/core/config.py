"""
Application configuration using Pydantic settings
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "EpiSphere AI"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # Database (defaults to SQLite for local development)
    DATABASE_URL: str = "sqlite:///./episphere.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    AGENT_API_KEY: str = ""

    # CORS / hosts
    CORS_ORIGINS: str | List[str] = ["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"]
    ALLOWED_HOSTS: str | List[str] = ["episphere.ai", "*.episphere.ai"]

    # File uploads
    UPLOAD_DIR: Path = Path("uploads")
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: List[str] = [".csv", ".xlsx", ".xls"]

    # Interoperability
    DHIS2_URL: str = ""
    DHIS2_USERNAME: str = ""
    DHIS2_PASSWORD: str = ""
    DHIS2_TIMEOUT_SECONDS: int = 30

    # Email (for notifications)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@episphere.ai"

    # ML/AI Settings
    ML_MODEL_DIR: Path = Path("models")
    FORECAST_HORIZON_DAYS: int = 30
    OUTBREAK_DETECTION_WINDOW: int = 14  # days

    @field_validator("SECRET_KEY")
    @classmethod
    def reject_default_secret_in_production(cls, value: str, info):
        env = info.data.get("ENVIRONMENT", "development")
        if env.lower() in {"production", "prod"} and value == "change-this-secret-key-in-production":
            raise ValueError("SECRET_KEY must be configured in production")
        return value

    @field_validator("CORS_ORIGINS", "ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, str):
            import json
            return json.loads(v)
        return v

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()

# Create necessary local directories
settings.UPLOAD_DIR.mkdir(exist_ok=True)
settings.ML_MODEL_DIR.mkdir(exist_ok=True)


