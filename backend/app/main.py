"""
EpiSphere AI - Main FastAPI Application
Production-ready global public health surveillance platform
"""

import time
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

from app.core.config import settings
from app.core.limiter import limiter
from app.core.logger import setup_logging
from app.core.database import SessionLocal
from app.core.metrics import request_metrics
from app.api.v1.api import api_router

logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events.

    Schema changes are managed by Alembic migrations. Do not mutate production
    schema at application startup.
    """
    logger.info(f"Starting EpiSphere AI in {settings.ENVIRONMENT} mode")
    yield
    logger.info("Shutting down EpiSphere AI")


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


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    supplied_request_id = request.headers.get("X-Request-ID", "").strip()
    request_id = supplied_request_id if 0 < len(supplied_request_id) <= 128 and supplied_request_id.isprintable() else str(uuid4())
    request.state.request_id = request_id
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        elapsed = time.perf_counter() - started
        request_metrics.observe(request.method, request.url.path, 500, elapsed)
        logger.exception("request failed", extra={"request_id": request_id})
        raise
    elapsed = time.perf_counter() - started
    request_metrics.observe(request.method, request.url.path, response.status_code, elapsed)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request completed",
        extra={"request_id": request_id, "status_code": response.status_code, "elapsed_seconds": round(elapsed, 6)},
    )
    return response

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


@app.get("/ready")
def readiness_check():
    """Readiness probe that verifies the application can reach its database."""
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.error("Readiness check failed: %s", exc)
        raise HTTPException(status_code=503, detail="Database is not ready") from exc
    return {"status": "ready"}


@app.get("/metrics", include_in_schema=False)
def metrics_endpoint():
    """Expose low-cardinality pilot metrics for a local collector."""
    return PlainTextResponse(request_metrics.render_prometheus(), media_type="text/plain; version=0.0.4")
