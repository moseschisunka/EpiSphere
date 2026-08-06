from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, Country, Disease, Case
from app.schemas.interop_extract import AggregateCaseMetric, DataExtractResponse

def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()

def test_interop_deidentified_metric_schema():
    metric = AggregateCaseMetric(
        disease_name="COVID-19",
        country_name="Zambia",
        iso_code="ZMB",
        date="2026-08-01",
        daily_cases=45,
        daily_deaths=1,
        daily_recovered=40,
        cumulative_cases=1200,
        cumulative_deaths=15,
        subnational_region="Lusaka",
        source="Ministry of Health"
    )
    response = DataExtractResponse(
        status="success",
        total_records=1,
        extracted_at="2026-08-07T00:00:00",
        metrics=[metric]
    )

    assert response.status == "success"
    assert response.total_records == 1
    assert response.metrics[0].disease_name == "COVID-19"
    assert response.metrics[0].iso_code == "ZMB"

def test_database_interop_data_query():
    db = make_session()
    country = Country(name="Zambia", iso_code="ZMB", iso_code_2="ZM", population=20_000_000)
    disease = Disease(name="COVID-19", code="U07.1")
    db.add_all([country, disease])
    db.flush()

    case_record = Case(
        country_id=country.id,
        disease_id=disease.id,
        date=date.today(),
        daily_cases=100,
        daily_deaths=2,
        daily_recovered=90,
        cumulative_cases=5000,
        cumulative_deaths=50,
        source="CDC Interop"
    )
    db.add(case_record)
    db.commit()

    cases = db.query(Case).join(Country).join(Disease).filter(Country.iso_code == "ZMB").all()
    assert len(cases) == 1
    assert cases[0].daily_cases == 100
    assert cases[0].disease.name == "COVID-19"
