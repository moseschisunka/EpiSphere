import asyncio
from types import SimpleNamespace

import scripts.run_ingestion_worker as worker


class _FakeDb:
    def close(self):
        return None


def test_worker_dispatches_public_csv_jobs(monkeypatch):
    calls = {}
    monkeypatch.setattr(worker, "SessionLocal", lambda: _FakeDb())

    def ingest_csv_url(**kwargs):
        calls.update(kwargs)
        return {"success": True, "records_imported": 3}

    monkeypatch.setattr(worker.PublicDatasetService, "ingest_csv_url", ingest_csv_url)
    job = SimpleNamespace(
        job_type="public_csv",
        payload={
            "url": "https://raw.githubusercontent.com/example/data.csv",
            "mapping": {"country_iso": "Country"},
            "disease_id": 2,
            "dry_run": True,
        },
    )

    result = asyncio.run(worker.execute_job(job))

    assert result["records_imported"] == 3
    assert calls["db"].__class__ is _FakeDb
    assert calls["disease_id"] == 2


def test_worker_rejects_unknown_job_types():
    job = SimpleNamespace(job_type="arbitrary_runtime_code", payload={})

    try:
        asyncio.run(worker.execute_job(job))
    except ValueError as exc:
        assert "Unsupported ingestion job type" in str(exc)
    else:
        raise AssertionError("unknown job types must be rejected")
