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
from app.db.models import IngestionJobStatus
from app.services.covid_data_service import CovidDataService
from app.services.ingestion_jobs import claim_next_job, complete_job, fail_job, request_cancel

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
    raise ValueError(f"Unsupported ingestion job type: {job.job_type}")


def process_one(worker_id: str) -> bool:
    db = SessionLocal()
    try:
        job = claim_next_job(db, worker_id=worker_id)
        if not job:
            return False
        if job.status == IngestionJobStatus.CANCEL_REQUESTED:
            request_cancel(db, job)
            return True
        try:
            result = asyncio.run(execute_job(job))
            complete_job(db, job, result)
        except Exception as exc:  # worker must retain failure for retry/DLQ
            fail_job(db, job, str(exc))
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
