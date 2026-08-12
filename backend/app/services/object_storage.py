"""Private object storage for durable report artifacts.

The local backend exists only for development and tests. Production must select
an S3-compatible bucket so generated reports do not disappear with a container.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from app.core.config import settings


class PrivateObjectStorage:
    """Store objects by opaque keys without exposing a filesystem path."""

    def __init__(self) -> None:
        self.backend = settings.OBJECT_STORAGE_BACKEND.lower()

    def store_file(self, source: Path, object_key: str, content_type: str) -> str:
        key = self._validate_key(object_key)
        if self.backend == "local":
            destination = settings.LOCAL_OBJECT_STORAGE_DIR / key
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            return key
        if self.backend == "s3":
            self._s3_client().upload_file(
                str(source),
                settings.OBJECT_STORAGE_BUCKET,
                key,
                ExtraArgs={
                    "ContentType": content_type,
                    "ServerSideEncryption": settings.OBJECT_STORAGE_SERVER_SIDE_ENCRYPTION,
                },
            )
            return key
        raise RuntimeError(f"Unsupported object storage backend: {self.backend}")

    def readiness(self) -> dict[str, str]:
        if self.backend == "local":
            ready = settings.LOCAL_OBJECT_STORAGE_DIR.exists() and settings.LOCAL_OBJECT_STORAGE_DIR.is_dir()
            return {"status": "ready" if ready else "failed", "backend": "local"}
        if self.backend == "s3":
            try:
                self._s3_client().head_bucket(Bucket=settings.OBJECT_STORAGE_BUCKET)
            except Exception:
                return {"status": "failed", "backend": "s3"}
            return {"status": "ready", "backend": "s3"}
        return {"status": "failed", "backend": self.backend}

    @staticmethod
    def _validate_key(object_key: str) -> str:
        key = object_key.strip().lstrip("/")
        if not key or ".." in Path(key).parts:
            raise ValueError("Object storage key is invalid")
        return key

    @staticmethod
    def _s3_client():
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("S3 object storage requires boto3 to be installed") from exc
        return boto3.client(
            "s3",
            endpoint_url=settings.OBJECT_STORAGE_ENDPOINT_URL or None,
            region_name=settings.OBJECT_STORAGE_REGION or None,
            aws_access_key_id=settings.OBJECT_STORAGE_ACCESS_KEY,
            aws_secret_access_key=settings.OBJECT_STORAGE_SECRET_KEY,
        )
