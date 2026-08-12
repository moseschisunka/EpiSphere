import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1.endpoints.reports import list_reports
from app.db.models import Base, Report, ReportType, Role, User


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
