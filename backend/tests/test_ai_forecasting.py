import asyncio
from datetime import date, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, Country, Disease, Case, Forecast, Alert
from app.ml.outbreak_detection import OutbreakDetectionEngine
from app.ml.forecasting import ForecastingPipeline
from app.services.outbreak_detection_service import OutbreakDetectionService


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def test_outbreak_engine_detects_transparent_statistical_signal():
    start = date.today() - timedelta(days=50)
    dates = [start + timedelta(days=i) for i in range(50)]
    values = [2] * 42 + [4, 5, 7, 9, 12, 15, 18, 22]

    result = OutbreakDetectionEngine(window_size=14).detect_outbreak(
        dates=dates,
        daily_cases=values,
        country_name="Zambia",
        disease_name="Cholera",
    )

    assert result["alert_triggered"] is True
    assert "ewma" in result["method_results"]
    assert "farrington" in result["method_results"]
    assert result["metadata"]["threshold_profile"]["min_cases"] == 1
    assert "Recommended action" in result["explanation"]


def test_forecasting_pipeline_uses_rolling_backtest_and_excludes_lstm_from_auto():
    start = date.today() - timedelta(days=90)
    dates = [start + timedelta(days=i) for i in range(90)]
    values = [10 + (i % 7) + i * 0.1 for i in range(90)]

    result = asyncio.run(ForecastingPipeline().generate_forecast(dates, values, horizon_days=7))
    metrics = result["accuracy_metrics"]

    assert result["model_type"] != "lstm"
    assert "lstm" not in metrics["candidate_models"]
    assert metrics["validation_method"] == "rolling_origin"
    assert metrics["rolling_backtest"]
    assert "drift_monitoring" in metrics
    assert len(result["forecast_data"]["upper_bound"]) == 7


def test_lstm_request_is_audited_as_disabled_placeholder():
    start = date.today() - timedelta(days=45)
    dates = [start + timedelta(days=i) for i in range(45)]
    values = [5 + (i % 3) for i in range(45)]

    result = asyncio.run(ForecastingPipeline().generate_forecast(dates, values, horizon_days=3, model_type="lstm"))

    assert result["model_type"] == "simple_trend"
    assert result["model_note"] == "lstm_placeholder_disabled_simple_trend_used"


def test_detection_service_persists_forecast_interval_exceedance_metadata():
    db = make_session()
    country = Country(name="Zambia", iso_code="ZMB", iso_code_2="ZM", population=20_000_000)
    disease = Disease(name="Cholera", code="A00")
    db.add_all([country, disease])
    db.flush()

    start = date.today() - timedelta(days=39)
    for i in range(40):
        value = 2 if i < 38 else 20
        db.add(Case(country_id=country.id, disease_id=disease.id, date=start + timedelta(days=i), daily_cases=value, cumulative_cases=value))

    forecast_dates = [(date.today() - timedelta(days=1)).isoformat(), date.today().isoformat()]
    db.add(Forecast(
        country_id=country.id,
        disease_id=disease.id,
        forecast_date=date.today() - timedelta(days=3),
        model_type="seasonal_naive",
        horizon_days=3,
        forecast_data={"dates": forecast_dates, "values": [2, 2], "lower_bound": [0, 0], "upper_bound": [5, 5]},
        accuracy_metrics={"model_version": "test"},
    ))
    db.commit()

    result = OutbreakDetectionService(db).run_detection(country.id, disease.id)
    alert = db.query(Alert).first()

    assert result["alert_triggered"] is True
    assert alert is not None
    assert alert.detection_metadata is not None
    assert "method_results" in alert.detection_metadata
