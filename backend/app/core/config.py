"""
Application configuration using Pydantic settings
"""

from pydantic_settings import BaseSettings
from typing import List
import os
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
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # File uploads
    UPLOAD_DIR: Path = Path("uploads")
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: List[str] = [".csv", ".xlsx", ".xls"]
    
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
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Create necessary directories
settings.UPLOAD_DIR.mkdir(exist_ok=True)
settings.ML_MODEL_DIR.mkdir(exist_ok=True)
