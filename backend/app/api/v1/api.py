"""Main API router"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth, cases, alerts, forecast, reports, dashboard, users, countries, diseases,
    facilities, clinical, pharmacy, surveillance, interop, public, covid_ingest,
    news, locations, dhs_analytics, public_datasets
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(countries.router, prefix="/countries", tags=["countries"])
api_router.include_router(diseases.router, prefix="/diseases", tags=["diseases"])
api_router.include_router(cases.router, prefix="/cases", tags=["cases"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(forecast.router, prefix="/forecast", tags=["forecast"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(facilities.router, prefix="/facilities", tags=["facilities"])
api_router.include_router(clinical.router, prefix="/clinical", tags=["clinical"])
api_router.include_router(pharmacy.router, prefix="/pharmacy", tags=["pharmacy"])
api_router.include_router(surveillance.router, prefix="/surveillance", tags=["surveillance"])
api_router.include_router(interop.router, prefix="/interop", tags=["interop"])
api_router.include_router(public.router, prefix="/public", tags=["public"])
api_router.include_router(covid_ingest.router, prefix="/covid19", tags=["data-ingestion"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])
api_router.include_router(dhs_analytics.router, prefix="/dhs", tags=["dhs-analytics"])
api_router.include_router(public_datasets.router, prefix="/datasets", tags=["public-datasets"])
