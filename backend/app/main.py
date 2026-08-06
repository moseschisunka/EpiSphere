"""
EpiSphere AI - Main FastAPI Application
Production-ready global public health surveillance platform
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

from app.core.config import settings
from app.core.limiter import limiter
from app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events.

    Schema changes are managed by Alembic migrations. Do not mutate production
    schema at application startup.
    """
    yield


app = FastAPI(
    title="EpiSphere AI API",
    description="AI-Powered Global Disease Surveillance and Outbreak Intelligence Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware (production)
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "EpiSphere AI",
        "version": "1.0.0",
        "status": "operational",
        "description": "Global Disease Surveillance and Outbreak Intelligence Platform"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
