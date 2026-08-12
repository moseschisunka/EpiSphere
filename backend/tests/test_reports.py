import asyncio
from datetime import date, datetime
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1.endpoints import reports as reports_endpoint
from app.api.v1.endpoints.reports import generate_report, list_reports
from app.db.models import Base, Report, ReportType, Role, User
from app.schemas.report import ReportRequest


def test_list_reports_preserves_report_metadata():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()

    role = Role(name="epidemiologist", description="Epidemiology user")
    session.add(role)
    session.flush()
    user = User(
        username="epi",
        email="epi@example.com",
        hashed_password="test-hash",
        role_id=role.id,
    )
    session.add(user)
    session.flush()
    session.add(
        Report(
            title="Weekly bulletin",
            report_type=ReportType.WEEKLY_BULLETIN,
            file_format="pdf",
            generated_by=user.id,
            report_metadata={"row_count": 12, "quality_score": 0.95},
        )
    )
    session.commit()

    response = asyncio.run(list_reports(current_user=user, db=session))

    assert len(response) == 1
    assert response[0].report_metadata == {"row_count": 12, "quality_score": 0.95}

    session.close()


def test_generate_report_serializes_report_metadata(monkeypatch):
    report = SimpleNamespace(
        id=7,
        title="Weekly bulletin",
        report_type=ReportType.WEEKLY_BULLETIN,
        country_id=None,
        disease_id=None,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 7),
        file_path="reports/weekly.pdf",
        file_format="pdf",
        generated_by=3,
        generated_at=datetime(2026, 1, 8),
        report_metadata={"row_count": 12},
    )

    class FakeReportService:
        def __init__(self, db):
            self.db = db

        async def generate_report(self, **kwargs):
            return report

    monkeypatch.setattr(reports_endpoint, "ReportService", FakeReportService)
    response = asyncio.run(generate_report(
        ReportRequest(
            report_type=ReportType.WEEKLY_BULLETIN,
            title="Weekly bulletin",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 7),
        ),
        current_user=SimpleNamespace(id=3),
        db=object(),
    ))

    assert response.report_metadata == {"row_count": 12}
