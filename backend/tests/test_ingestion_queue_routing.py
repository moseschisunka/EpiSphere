import asyncio
from types import SimpleNamespace

from fastapi import Response

from app.api.v1.endpoints import interop, public_datasets
from app.schemas.interop import DHIS2SyncRequest
from app.schemas.public_datasets import CsvIngestRequest


class _FakeDb:
    def add(self, _value):
        return None

    def commit(self):
        return None


def test_public_write_is_queued_even_without_explicit_enqueue(monkeypatch):
    job = SimpleNamespace(id=41)
    monkeypatch.setattr(public_datasets, "enqueue_job", lambda *args, **kwargs: job)
    request = SimpleNamespace(state=SimpleNamespace(request_id="request-41"))
    response = Response()
    payload = CsvIngestRequest(
        url="https://raw.githubusercontent.com/example/data.csv",
        mapping={"country_iso": "Country", "date": "Date", "daily_cases": "Cases"},
        disease_id=2,
        dry_run=False,
    )
    actor = SimpleNamespace(id=9, name="operator", auth_method="bearer")

    result = asyncio.run(public_datasets.ingest_csv_dataset.__wrapped__(request, response, payload, _FakeDb(), actor))

    assert response.status_code == 202
    assert result.job_id == 41


def test_dhis2_write_is_queued_even_without_explicit_enqueue(monkeypatch):
    job = SimpleNamespace(id=52)
    monkeypatch.setattr(interop, "enqueue_job", lambda *args, **kwargs: job)
    response = Response()
    payload = DHIS2SyncRequest(
        dataset="weekly_cases",
        payload={"orgUnit": "facility-1", "dataValues": []},
        dry_run=False,
    )
    actor = SimpleNamespace(id=12)

    result = interop.trigger_dhis2_sync(payload, response, _FakeDb(), actor)

    assert response.status_code == 202
    assert result.job_id == 52
