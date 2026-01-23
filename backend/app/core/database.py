"""
Database configuration and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import settings

# Create async engine for SQLAlchemy 2.0
# Convert postgresql:// to postgresql+asyncpg:// for async support (only if PostgreSQL)
if settings.DATABASE_URL.startswith("postgresql://"):
    async_database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(
        async_database_url,
        echo=settings.DEBUG,
        future=True
    )
else:
    # SQLite doesn't support async well, use sync engine
    engine = None

# For sync operations (migrations, etc.)
# SQLite requires connect_args for foreign keys
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

sync_engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True if not settings.DATABASE_URL.startswith("sqlite") else False,
    connect_args=connect_args
)

# Async session factory (only for PostgreSQL)
if engine is not None:
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
else:
    AsyncSessionLocal = None

# Sync session factory (for migrations)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)


async def get_async_db() -> AsyncSession:
    """Async database session dependency"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_db() -> Generator[Session, None, None]:
    """Sync database session dependency (for compatibility)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Import all models here so Alembic can detect them
from app.db.models import Base  # noqa
