"""Run the durable ingestion worker.

The worker intentionally supports a small explicit handler registry. Unknown
job types are dead-lettered instead of executed dynamically from payload data.
"""

import argparse
import asyncio
import logging
import socket
import time

from app.core.database import SessionLocal
from app.db.models import IngestionJobStatus, User
from app.services.covid_data_service import CovidDataService
from app.services.ingestion_jobs import claim_next_job, complete_job, fail_job, record_worker_heartbeat, request_cancel
from app.services.interop_service import InteropService
from app.services.public_dataset_service import PublicDatasetService

logger = logging.getLogger(__name__)


async def execute_job(job) -> dict:
    if job.job_type == "owid_covid19":
        db = SessionLocal()
        try:
            result = await CovidDataService(db).ingest_owid_data(
                user_id=job.payload.get("user_id")
            )
            return result
        finally:
            db.close()
    if job.job_type in {"public_csv", "public_who_gho", "dhis2_sync", "dhis2_pull"}:
        db = SessionLocal()
        try:
            if job.job_type == "public_csv":
                return PublicDatasetService.ingest_csv_url(db=db, **job.payload)
            if job.job_type == "public_who_gho":
                return PublicDatasetService.ingest_who_gho(db=db, **job.payload)
            user = db.query(User).filter(User.id == job.payload.get("user_id")).first()
            if not user:
                raise ValueError("The durable job creator no longer exists")
            payload = dict(job.payload)
            payload.pop("user_id", None)
            if job.job_type == "dhis2_sync":
                return InteropService.sync_to_dhis2(db=db, user=user, **payload)
            return InteropService.pull_from_dhis2(db=db, user=user, **payload)
        finally:
            db.close()
    raise ValueError(f"Unsupported ingestion job type: {job.job_type}")


def process_one(worker_id: str) -> bool:
    db = SessionLocal()
    try:
        record_worker_heartbeat(db, worker_id=worker_id)
        job = claim_next_job(db, worker_id=worker_id)
        if not job:
            return False
        if job.status == IngestionJobStatus.CANCEL_REQUESTED:
            request_cancel(db, job)
            return True
        try:
            result = asyncio.run(execute_job(job))
            complete_job(db, job, result)
            record_worker_heartbeat(db, worker_id=worker_id, last_job_id=job.id)
        except Exception as exc:  # worker must retain failure for retry/DLQ
            fail_job(db, job, str(exc))
            record_worker_heartbeat(db, worker_id=worker_id, last_job_id=job.id, last_error=str(exc))
        return True
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run EpiSphere ingestion worker")
    parser.add_argument("--once", action="store_true", help="process at most one job")
    parser.add_argument("--poll-seconds", type=float, default=10.0)
    args = parser.parse_args()
    worker_id = f"{socket.gethostname()}-ingestion-worker"

    while True:
        processed = process_one(worker_id)
        if args.once or not processed:
            if args.once:
                return 0
            time.sleep(max(0.5, args.poll_seconds))


if __name__ == "__main__":
    raise SystemExit(main())
