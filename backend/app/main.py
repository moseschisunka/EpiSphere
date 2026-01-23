"""
EpiSphere AI - Main FastAPI Application
Production-ready global public health surveillance platform
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup: Create database tables (using sync engine for compatibility)
    from app.core.database import sync_engine
    Base.metadata.create_all(bind=sync_engine)
    yield
    # Shutdown: Cleanup if needed
    pass


app = FastAPI(
    title="EpiSphere AI API",
    description="AI-Powered Global Disease Surveillance and Outbreak Intelligence Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

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
        allowed_hosts=["episphere.ai", "*.episphere.ai"]
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
