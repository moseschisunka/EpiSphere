"""Dashboard service."""

from typing import Optional
from datetime import date, timedelta
from statistics import median

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.db.models import Case, Country, Disease, Alert, AlertSeverity, AlertStatus, Facility, Encounter
from app.schemas.dashboard import GlobalStats, CountryStats, TimeSeriesPoint, DashboardResponse


class DashboardService:
    """Service for dashboard data aggregation with freshness and quality context."""

    def __init__(self, db: Session):
        self.db = db

    def get_global_dashboard(
        self,
        disease_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> DashboardResponse:
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        scoped_query = self.db.query(Case).filter(Case.date <= end_date)
        if disease_id:
            scoped_query = scoped_query.filter(Case.disease_id == disease_id)

        latest_subquery = scoped_query.with_entities(
            Case.country_id.label("country_id"),
            Case.disease_id.label("disease_id"),
            func.max(Case.date).label("latest_date"),
        ).group_by(Case.country_id, Case.disease_id).subquery()

        latest_rows = self.db.query(Case).join(
            latest_subquery,
            and_(
                Case.country_id == latest_subquery.c.country_id,
                Case.disease_id == latest_subquery.c.disease_id,
                Case.date == latest_subquery.c.latest_date,
            ),
        ).all()

        total_cases = sum(row.cumulative_cases or 0 for row in latest_rows)
        total_deaths = sum(row.cumulative_deaths or 0 for row in latest_rows)
        total_countries = len({row.country_id for row in latest_rows})
        active_diseases = len({row.disease_id for row in latest_rows})
        lags = [(end_date - row.date).days for row in latest_rows if row.date]
        latest_data_date = max((row.date for row in latest_rows), default=None)

        expected_groups = max(total_countries * max(active_diseases, 1), 1)
        expected_days = max((end_date - start_date).days + 1, 1)
        observed_points_query = self.db.query(func.count(Case.id)).filter(Case.date >= start_date, Case.date <= end_date)
        if disease_id:
            observed_points_query = observed_points_query.filter(Case.disease_id == disease_id)
        observed_points = observed_points_query.scalar() or 0
        data_completeness = min(observed_points / (expected_groups * expected_days), 1.0) if latest_rows else 0.0

        active_alerts = self.db.query(func.count(Alert.id)).filter(
            Alert.status.in_([
                AlertStatus.TRIGGERED,
                AlertStatus.ACKNOWLEDGED,
                AlertStatus.INVESTIGATING,
                AlertStatus.ESCALATED,
            ])
        ).scalar() or 0

        global_stats = GlobalStats(
            total_cases=int(total_cases),
            total_deaths=int(total_deaths),
            total_countries=int(total_countries),
            active_diseases=int(active_diseases),
            active_alerts=int(active_alerts),
            date_range_start=start_date,
            date_range_end=end_date,
            latest_data_date=latest_data_date,
            data_completeness=round(data_completeness, 3),
            median_reporting_lag_days=float(median(lags)) if lags else None,
        )

        country_stats = self._country_stats_from_latest(latest_rows, end_date)
        time_series = self._global_time_series(disease_id, start_date, end_date)
        alerts_summary = self._alerts_summary()
        top_countries = sorted(country_stats, key=lambda x: x.total_cases, reverse=True)[:10]

        return DashboardResponse(
            global_stats=global_stats,
            country_stats=country_stats,
            time_series=time_series,
            alerts_summary=alerts_summary,
            top_countries=top_countries,
        )

    def get_country_dashboard(
        self,
        country_id: int,
        disease_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        country = self.db.query(Country).filter(Country.id == country_id).first()
        if not country:
            raise ValueError("Country not found")

        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=90)

        query = self.db.query(
            Case.date,
            func.sum(Case.daily_cases).label("daily_cases"),
            func.sum(Case.cumulative_cases).label("cumulative_cases"),
            func.sum(Case.daily_deaths).label("daily_deaths"),
            func.sum(Case.cumulative_deaths).label("cumulative_deaths"),
            func.avg(Case.data_quality_score).label("data_quality_score"),
        ).filter(
            Case.country_id == country_id,
            Case.date >= start_date,
            Case.date <= end_date,
        )
        if disease_id:
            query = query.filter(Case.disease_id == disease_id)

        rows = query.group_by(Case.date).order_by(Case.date).all()
        time_series = [
            {
                "date": row.date.isoformat(),
                "daily_cases": int(row.daily_cases or 0),
                "cumulative_cases": int(row.cumulative_cases or 0),
                "daily_deaths": int(row.daily_deaths or 0),
                "cumulative_deaths": int(row.cumulative_deaths or 0),
                "data_quality_score": float(row.data_quality_score) if row.data_quality_score is not None else None,
            }
            for row in rows
        ]

        moving_averages = []
        for i in range(6, len(rows)):
            window = rows[i - 6:i + 1]
            avg = sum((row.daily_cases or 0) for row in window) / 7
            moving_averages.append({"date": rows[i].date.isoformat(), "value": round(avg, 2)})

        latest = rows[-1] if rows else None
        reporting_lag_days = (end_date - latest.date).days if latest else None
        expected_days = max((end_date - start_date).days + 1, 1)
        completeness = min(len(rows) / expected_days, 1.0)

        return {
            "country": {
                "id": country.id,
                "name": country.name,
                "iso_code": country.iso_code,
                "population": country.population,
            },
            "time_series": time_series,
            "moving_averages": moving_averages,
            "data_quality": {
                "date_range_start": start_date.isoformat(),
                "date_range_end": end_date.isoformat(),
                "latest_data_date": latest.date.isoformat() if latest else None,
                "reporting_lag_days": reporting_lag_days,
                "completeness": round(completeness, 3),
                "freshness_status": self._freshness_status(reporting_lag_days),
            },
            "latest_stats": {
                "date": latest.date.isoformat() if latest else None,
                "daily_cases": int(latest.daily_cases or 0) if latest else 0,
                "cumulative_cases": int(latest.cumulative_cases or 0) if latest else 0,
                "daily_deaths": int(latest.daily_deaths or 0) if latest else 0,
                "cumulative_deaths": int(latest.cumulative_deaths or 0) if latest else 0,
            } if latest else None,
        }

    def _country_stats_from_latest(self, latest_rows: list[Case], end_date: date) -> list[CountryStats]:
        stats: list[CountryStats] = []
        for row in latest_rows:
            population = row.country.population if row.country else None
            incidence_per_100k = (row.cumulative_cases / population) * 100000 if population and row.cumulative_cases else None
            cfr = (row.cumulative_deaths / row.cumulative_cases) * 100 if row.cumulative_cases else None
            reporting_lag = (end_date - row.date).days if row.date else None
            avg_7day = self._seven_day_average(row.country_id, row.disease_id, row.date)
            stats.append(CountryStats(
                country_id=row.country_id,
                country_name=row.country.name if row.country else "Unknown",
                iso_code=row.country.iso_code if row.country else "",
                disease_id=row.disease_id,
                disease_name=row.disease.name if row.disease else "Unknown",
                total_cases=int(row.cumulative_cases or 0),
                total_deaths=int(row.cumulative_deaths or 0),
                total_recovered=row.cumulative_recovered,
                incidence_per_100k=incidence_per_100k,
                cfr=cfr,
                latest_date=row.date,
                daily_cases_7day_avg=avg_7day,
                growth_rate=None,
                reporting_lag_days=reporting_lag,
                data_quality_score=row.data_quality_score,
                data_freshness_status=self._freshness_status(reporting_lag),
                latitude=row.country.latitude if row.country else None,
                longitude=row.country.longitude if row.country else None,
            ))
        return stats

    def _seven_day_average(self, country_id: int, disease_id: int, latest_date: date) -> Optional[float]:
        start = latest_date - timedelta(days=6)
        value = self.db.query(func.avg(Case.daily_cases)).filter(
            Case.country_id == country_id,
            Case.disease_id == disease_id,
            Case.date >= start,
            Case.date <= latest_date,
        ).scalar()
        return round(float(value), 2) if value is not None else None

    def _global_time_series(self, disease_id: Optional[int], start_date: date, end_date: date) -> list[TimeSeriesPoint]:
        query = self.db.query(Case.date, func.sum(Case.daily_cases).label("daily_cases")).filter(
            Case.date >= start_date,
            Case.date <= end_date,
        )
        if disease_id:
            query = query.filter(Case.disease_id == disease_id)
        rows = query.group_by(Case.date).order_by(Case.date).all()
        return [TimeSeriesPoint(date=row.date, value=float(row.daily_cases or 0)) for row in rows]

    def _alerts_summary(self) -> dict:
        return {
            "low": self.db.query(func.count(Alert.id)).filter(Alert.severity == AlertSeverity.LOW, Alert.status.in_([AlertStatus.TRIGGERED, AlertStatus.ACKNOWLEDGED, AlertStatus.INVESTIGATING, AlertStatus.ESCALATED])).scalar() or 0,
            "moderate": self.db.query(func.count(Alert.id)).filter(Alert.severity == AlertSeverity.MODERATE, Alert.status.in_([AlertStatus.TRIGGERED, AlertStatus.ACKNOWLEDGED, AlertStatus.INVESTIGATING, AlertStatus.ESCALATED])).scalar() or 0,
            "high": self.db.query(func.count(Alert.id)).filter(Alert.severity == AlertSeverity.HIGH, Alert.status.in_([AlertStatus.TRIGGERED, AlertStatus.ACKNOWLEDGED, AlertStatus.INVESTIGATING, AlertStatus.ESCALATED])).scalar() or 0,
        }

    def _freshness_status(self, lag_days: Optional[int]) -> str:
        if lag_days is None:
            return "unknown"
        if lag_days <= 7:
            return "fresh"
        if lag_days <= 14:
            return "watch"
        return "stale"

    @staticmethod
    def get_facility_heatmap(db: Session, facility_id: int | None = None) -> list:
        """Get aggregated encounter counts, optionally for one facility."""
        query = db.query(
            Facility.name,
            Facility.type,
            Facility.location,
            Facility.latitude,
            Facility.longitude,
            Facility.facility_code,
            Facility.admin1_code,
            Facility.admin2_code,
            func.count(Encounter.id).label("visit_count"),
        ).join(Encounter)
        if facility_id is not None:
            query = query.filter(Facility.id == facility_id)
        results = query.group_by(Facility.id).all()

        heatmap_data = []
        for row in results:
            lat = row.latitude
            lon = row.longitude
            if (lat is None or lon is None) and row.location and "," in row.location:
                try:
                    parts = row.location.split(",")
                    lat, lon = float(parts[0]), float(parts[1])
                except ValueError:
                    lat, lon = None, None
            if lat is None or lon is None:
                continue
            heatmap_data.append({
                "name": row.name,
                "type": row.type.value if hasattr(row.type, "value") else row.type,
                "facility_code": row.facility_code,
                "admin1_code": row.admin1_code,
                "admin2_code": row.admin2_code,
                "lat": lat,
                "lon": lon,
                "count": row.visit_count,
            })
        return heatmap_data
