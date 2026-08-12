"""
EpiSphere AI - Main FastAPI Application
Production-ready global public health surveillance platform
"""

import time
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import func, text
from sqlalchemy.exc import SQLAlchemyError

from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

from app.core.config import settings
from app.core.limiter import limiter
from app.core.logger import setup_logging
from app.core.database import SessionLocal
from app.core.cache import redis_client
from app.core.metrics import request_metrics
from app.db.models import IngestionJob, IngestionJobStatus, WorkerHeartbeat
from app.api.v1.api import api_router
from app.services.object_storage import PrivateObjectStorage

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
    """Backward-compatible application liveness endpoint."""
    return {"status": "healthy"}


@app.get("/live")
async def liveness_check():
    """Process liveness only; dependency failures belong to readiness probes."""
    return {"status": "live"}


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


@app.get("/ready/components")
def component_readiness_check():
    """Return deployment readiness for the database, queue, Redis, and storage."""
    components = {}
    failures = []

    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
            queued_jobs = db.query(func.count(IngestionJob.id)).filter(
                IngestionJob.status == IngestionJobStatus.QUEUED
            ).scalar() or 0
            running_jobs = db.query(func.count(IngestionJob.id)).filter(
                IngestionJob.status == IngestionJobStatus.RUNNING
            ).scalar() or 0
            stale_cutoff = datetime.utcnow() - timedelta(minutes=settings.WORKER_STALE_AFTER_MINUTES)
            stale_running_jobs = db.query(func.count(IngestionJob.id)).filter(
                IngestionJob.status == IngestionJobStatus.RUNNING,
                IngestionJob.started_at.isnot(None),
                IngestionJob.started_at < stale_cutoff,
            ).scalar() or 0
            latest_worker_heartbeat = db.query(WorkerHeartbeat).filter(
                WorkerHeartbeat.worker_type == "ingestion"
            ).order_by(WorkerHeartbeat.last_heartbeat_at.desc()).first()
        components["database"] = {"status": "ready"}
        components["ingestion_worker_queue"] = {
            "status": "ready" if stale_running_jobs == 0 else "failed",
            "queued_jobs": queued_jobs,
            "running_jobs": running_jobs,
            "stale_running_jobs": stale_running_jobs,
        }
        if stale_running_jobs:
            failures.append("ingestion_worker_queue")
        heartbeat_age_seconds = None
        if latest_worker_heartbeat:
            heartbeat_age_seconds = max(0, int((datetime.utcnow() - latest_worker_heartbeat.last_heartbeat_at).total_seconds()))
        heartbeat_ready = latest_worker_heartbeat is not None and heartbeat_age_seconds <= settings.WORKER_HEARTBEAT_MAX_AGE_SECONDS
        components["ingestion_worker"] = {
            "status": "ready" if heartbeat_ready else ("missing" if latest_worker_heartbeat is None else "stale"),
            "worker_id": latest_worker_heartbeat.worker_id if latest_worker_heartbeat else None,
            "last_heartbeat_at": latest_worker_heartbeat.last_heartbeat_at if latest_worker_heartbeat else None,
            "heartbeat_age_seconds": heartbeat_age_seconds,
            "max_age_seconds": settings.WORKER_HEARTBEAT_MAX_AGE_SECONDS,
        }
        if settings.WORKER_HEARTBEAT_REQUIRED and not heartbeat_ready:
            failures.append("ingestion_worker")
    except SQLAlchemyError as exc:
        logger.error("Component readiness database check failed: %s", exc)
        components["database"] = {"status": "failed"}
        components["ingestion_worker_queue"] = {"status": "unknown"}
        failures.append("database")

    if settings.REDIS_REQUIRED:
        try:
            redis_client.ping()
            components["redis"] = {"status": "ready"}
        except Exception as exc:
            logger.error("Component readiness Redis check failed: %s", exc)
            components["redis"] = {"status": "failed"}
            failures.append("redis")
    else:
        components["redis"] = {"status": "not_required"}

    components["upload_storage"] = PrivateObjectStorage().readiness()
    if components["upload_storage"]["status"] == "failed":
        failures.append("upload_storage")

    payload = {"status": "ready" if not failures else "not_ready", "components": components}
    if failures:
        raise HTTPException(status_code=503, detail=payload)
    return payload


@app.get("/metrics", include_in_schema=False)
def metrics_endpoint():
    """Expose low-cardinality pilot metrics for a local collector."""
    return PlainTextResponse(request_metrics.render_prometheus(), media_type="text/plain; version=0.0.4")
