import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base
from app.services.public_dataset_service import PublicDatasetService
from app.db.models import Country, Disease, Case

@pytest.fixture
def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

def test_ingest_csv_url_success(make_session):
    db = make_session
    
    country = Country(name="Zambia", iso_code="ZMB", iso_code_2="ZM")
    disease = Disease(name="Cholera", code="A00")
    db.add_all([country, disease])
    db.commit()

    mock_csv_content = """Country,Date,Cases,Deaths
ZMB,2023-01-01,50,2
ZMB,2023-01-02,30,1
UNKNOWN,2023-01-03,10,0
"""
    
    mapping = {
        "country_iso": "Country",
        "date": "Date",
        "daily_cases": "Cases",
        "daily_deaths": "Deaths"
    }

    with patch("httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = mock_csv_content
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = PublicDatasetService.ingest_csv_url(
            db=db,
            url="http://test.com/data.csv",
            mapping=mapping,
            disease_id=disease.id,
            dry_run=False
        )

        assert result["success"] is True
        assert result["records_imported"] == 2 # 1 unknown country skipped

        cases = db.query(Case).filter(Case.disease_id == disease.id).all()
        assert len(cases) == 2
        assert cases[0].daily_cases == 50
        assert cases[1].daily_cases == 30

def test_ingest_who_gho_success(make_session):
    db = make_session
    
    country = Country(name="Zambia", iso_code="ZMB", iso_code_2="ZM")
    disease = Disease(name="Cholera", code="A00")
    db.add_all([country, disease])
    db.commit()

    mock_who_data = {
        "value": [
            {"SpatialDim": "ZMB", "TimeDim": "2023", "NumericValue": "1000"},
            {"SpatialDim": "ZMB", "TimeDim": "2024", "NumericValue": "500"},
            {"SpatialDim": "XYZ", "TimeDim": "2024", "NumericValue": "10"} # skipped
        ]
    }

    with patch("httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_who_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = PublicDatasetService.ingest_who_gho(
            db=db,
            indicator_code="CHOLERA_TEST",
            disease_id=disease.id,
            dry_run=False
        )

        assert result["success"] is True
        assert result["records_imported"] == 2

        cases = db.query(Case).filter(Case.disease_id == disease.id).all()
        assert len(cases) == 2
        assert cases[0].daily_cases == 1000
