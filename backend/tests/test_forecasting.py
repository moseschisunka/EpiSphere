import asyncio
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, Disease, BiosafetyLevel
from app.ml.forecasting import ForecastingPipeline
from app.schemas.disease import DiseaseCreate, DiseaseResponse

def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()

def test_disease_biosafety_level_persistence():
    db = make_session()
    disease = Disease(
        name="Ebola Virus",
        code="A98.4",
        description="Ebola virus disease",
        biosafety_level=BiosafetyLevel.BSL4
    )
    db.add(disease)
    db.commit()

    fetched = db.query(Disease).filter_by(name="Ebola Virus").first()
    assert fetched is not None
    assert fetched.biosafety_level == BiosafetyLevel.BSL4
    assert fetched.biosafety_level.value == "BSL-4"

def test_disease_pydantic_schema_validation():
    data = DiseaseCreate(
        name="Lassa Fever",
        code="A96.2",
        biosafety_level=BiosafetyLevel.BSL4
    )
    assert data.biosafety_level == BiosafetyLevel.BSL4
    assert data.is_active is True

def test_exponential_smoothing_forecasting():
    start = date.today() - timedelta(days=60)
    dates = [start + timedelta(days=i) for i in range(60)]
    values = [15.0 + (i % 5) * 2.0 for i in range(60)]

    pipeline = ForecastingPipeline()
    result = asyncio.run(pipeline.generate_forecast(dates, values, horizon_days=10, model_type="exp_smoothing"))

    assert result["model_type"] == "exp_smoothing"
    assert len(result["forecast_data"]["values"]) == 10
    assert len(result["forecast_data"]["lower_bound"]) == 10
    assert len(result["forecast_data"]["upper_bound"]) == 10
    assert "exp_smoothing" in result["accuracy_metrics"]["candidate_models"]
