from datetime import date, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Alert, AlertSeverity, AlertStatus, Base, Case, Country, Disease
from app.services.dashboard_service import DashboardService


def test_global_dashboard_returns_authoritative_stats_and_coordinates():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()

    country = Country(
        name="Zambia",
        iso_code="ZMB",
        iso_code_2="ZM",
        population=20000000,
        latitude=-13.1339,
        longitude=27.8493,
    )
    disease = Disease(name="Malaria", code="B50")
    session.add_all([country, disease])
    session.flush()
    session.add(
        Case(
            country_id=country.id,
            disease_id=disease.id,
            date=date.today(),
            daily_cases=12,
            cumulative_cases=120,
            daily_deaths=1,
            cumulative_deaths=4,
            data_quality_score=0.9,
        )
    )
    session.commit()

    response = DashboardService(session).get_global_dashboard(
        disease_id=disease.id,
        start_date=date.today() - timedelta(days=1),
        end_date=date.today(),
    )

    assert response.global_stats.total_cases == 120
    assert response.global_stats.total_deaths == 4
    assert response.global_stats.total_countries == 1
    assert response.country_stats[0].latitude == -13.1339
    assert response.country_stats[0].longitude == 27.8493
    assert response.time_series[0].value == 12

    session.close()


def test_operations_dashboard_returns_alert_slas_and_reporting_delays():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    session = sessionmaker(bind=engine)()
    Base.metadata.create_all(bind=engine)
    country = Country(name="Zambia", iso_code="ZMB", iso_code_2="ZM")
    disease = Disease(name="Cholera", code="A00")
    session.add_all([country, disease]); session.flush()
    session.add(Case(country_id=country.id, disease_id=disease.id, date=date.today() - timedelta(days=8), daily_cases=1, cumulative_cases=1))
    session.add(Alert(country_id=country.id, disease_id=disease.id, severity=AlertSeverity.HIGH, status=AlertStatus.TRIGGERED, probability_score=.9, detection_method="cusum", explanation="signal", triggered_at=datetime.utcnow() - timedelta(hours=25)))
    session.commit()
    result = DashboardService(session).get_operations_dashboard()
    assert result["active_alerts"] == 1
    assert result["overdue_alerts"] == 1
    assert result["unassigned_alerts"] == 1
    assert result["reporting_delays"][0]["freshness_status"] == "watch"
    session.close()
