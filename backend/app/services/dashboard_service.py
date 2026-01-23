"""Dashboard service"""

from typing import Optional
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from app.db.models import Case, Country, Disease, Alert, AlertSeverity
from app.schemas.dashboard import (
    GlobalStats, CountryStats, TimeSeriesPoint, DashboardResponse
)
from app.db.models import Case, Country, Disease, Alert, AlertSeverity, Facility, Encounter


class DashboardService:
    """Service for dashboard data aggregation"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_global_dashboard(
        self,
        disease_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> DashboardResponse:
        """Get global dashboard statistics"""
        
        # Default date range: last 30 days
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Build query
        query = self.db.query(Case)
        if disease_id:
            query = query.filter(Case.disease_id == disease_id)
        if start_date:
            query = query.filter(Case.date >= start_date)
        if end_date:
            query = query.filter(Case.date <= end_date)
        
        # Global stats
        total_cases = self.db.query(func.sum(Case.cumulative_cases)).filter(
            Case.date == end_date
        ).scalar() or 0
        
        total_deaths = self.db.query(func.sum(Case.cumulative_deaths)).filter(
            Case.date == end_date
        ).scalar() or 0
        
        total_countries = self.db.query(func.count(func.distinct(Case.country_id))).scalar() or 0
        
        active_diseases = self.db.query(func.count(func.distinct(Case.disease_id))).scalar() or 0
        
        active_alerts = self.db.query(func.count(Alert.id)).filter(
            Alert.status.in_(["triggered", "investigating"])
        ).scalar() or 0
        
        global_stats = GlobalStats(
            total_cases=int(total_cases),
            total_deaths=int(total_deaths),
            total_countries=int(total_countries),
            active_diseases=int(active_diseases),
            active_alerts=int(active_alerts),
            date_range_start=start_date,
            date_range_end=end_date
        )
        
        # Country stats
        country_query = self.db.query(
            Case.country_id,
            Country.name,
            Country.iso_code,
            Case.disease_id,
            Disease.name.label("disease_name"),
            func.max(Case.cumulative_cases).label("total_cases"),
            func.max(Case.cumulative_deaths).label("total_deaths"),
            func.max(Case.date).label("latest_date")
        ).join(Country).join(Disease)
        
        if disease_id:
            country_query = country_query.filter(Case.disease_id == disease_id)
        
        country_stats_list = country_query.group_by(
            Case.country_id, Country.name, Country.iso_code,
            Case.disease_id, Disease.name
        ).all()
        
        country_stats = []
        for stat in country_stats_list:
            country = self.db.query(Country).filter(Country.id == stat.country_id).first()
            population = country.population if country else None
            
            incidence_per_100k = None
            if population and population > 0:
                incidence_per_100k = (stat.total_cases / population) * 100000
            
            cfr = None
            if stat.total_cases > 0:
                cfr = (stat.total_deaths / stat.total_cases) * 100
            
            country_stats.append(CountryStats(
                country_id=stat.country_id,
                country_name=stat.name,
                iso_code=stat.iso_code,
                disease_id=stat.disease_id,
                disease_name=stat.disease_name,
                total_cases=int(stat.total_cases),
                total_deaths=int(stat.total_deaths),
                total_recovered=None,
                incidence_per_100k=incidence_per_100k,
                cfr=cfr,
                latest_date=stat.latest_date,
                daily_cases_7day_avg=None,
                growth_rate=None
            ))
        
        # Time series (aggregate daily cases globally)
        time_series_query = self.db.query(
            Case.date,
            func.sum(Case.daily_cases).label("daily_cases")
        )
        
        if disease_id:
            time_series_query = time_series_query.filter(Case.disease_id == disease_id)
        if start_date:
            time_series_query = time_series_query.filter(Case.date >= start_date)
        if end_date:
            time_series_query = time_series_query.filter(Case.date <= end_date)
        
        time_series_data = time_series_query.group_by(Case.date).order_by(Case.date).all()
        
        time_series = [
            TimeSeriesPoint(date=ts.date, value=float(ts.daily_cases))
            for ts in time_series_data
        ]
        
        # Alerts summary
        alerts_summary = {
            "low": self.db.query(func.count(Alert.id)).filter(
                Alert.severity == AlertSeverity.LOW,
                Alert.status.in_(["triggered", "investigating"])
            ).scalar() or 0,
            "moderate": self.db.query(func.count(Alert.id)).filter(
                Alert.severity == AlertSeverity.MODERATE,
                Alert.status.in_(["triggered", "investigating"])
            ).scalar() or 0,
            "high": self.db.query(func.count(Alert.id)).filter(
                Alert.severity == AlertSeverity.HIGH,
                Alert.status.in_(["triggered", "investigating"])
            ).scalar() or 0
        }
        
        # Top countries by cases
        top_countries = sorted(
            country_stats,
            key=lambda x: x.total_cases,
            reverse=True
        )[:10]
        
        return DashboardResponse(
            global_stats=global_stats,
            country_stats=country_stats,
            time_series=time_series,
            alerts_summary=alerts_summary,
            top_countries=top_countries
        )
    
    def get_country_dashboard(
        self,
        country_id: int,
        disease_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> dict:
        """Get country-level dashboard data"""
        
        country = self.db.query(Country).filter(Country.id == country_id).first()
        if not country:
            raise ValueError("Country not found")
        
        # Default date range: last 90 days
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=90)
        
        # Build query
        query = self.db.query(Case).filter(
            Case.country_id == country_id,
            Case.date >= start_date,
            Case.date <= end_date
        )
        
        if disease_id:
            query = query.filter(Case.disease_id == disease_id)
        
        cases = query.order_by(Case.date).all()
        
        # Time series
        time_series = [
            {
                "date": case.date.isoformat(),
                "daily_cases": case.daily_cases,
                "cumulative_cases": case.cumulative_cases,
                "daily_deaths": case.daily_deaths,
                "cumulative_deaths": case.cumulative_deaths
            }
            for case in cases
        ]
        
        # Calculate 7-day moving averages
        moving_averages = []
        for i in range(6, len(cases)):
            window = cases[i-6:i+1]
            avg = sum(c.daily_cases for c in window) / 7
            moving_averages.append({
                "date": cases[i].date.isoformat(),
                "value": round(avg, 2)
            })
        
        # Latest stats
        latest_case = cases[-1] if cases else None
        
        stats = {
            "country": {
                "id": country.id,
                "name": country.name,
                "iso_code": country.iso_code,
                "population": country.population
            },
            "time_series": time_series,
            "moving_averages": moving_averages,
            "latest_stats": {
                "date": latest_case.date.isoformat() if latest_case else None,
                "daily_cases": latest_case.daily_cases if latest_case else 0,
                "cumulative_cases": latest_case.cumulative_cases if latest_case else 0,
                "daily_deaths": latest_case.daily_deaths if latest_case else 0,
                "cumulative_deaths": latest_case.cumulative_deaths if latest_case else 0
            } if latest_case else None
        }
        
        return stats

    @staticmethod
    def get_facility_heatmap(db: Session) -> list:
        """
        Get aggregated case counts per facility for heatmap.
        Returns: [{lat, lon, count, name, type}, ...]
        """
        # Join Facility and Encounter to count visits
        results = db.query(
            Facility.name,
            Facility.type,
            Facility.location,
            func.count(Encounter.id).label("visit_count")
        ).join(Encounter)\
         .group_by(Facility.id)\
         .all()
         
        heatmap_data = []
        for row in results:
             if row.location and "," in row.location:
                 try:
                     parts = row.location.split(",")
                     if len(parts) >= 2:
                        lat, lon = float(parts[0]), float(parts[1])
                        heatmap_data.append({
                            "name": row.name,
                            "type": row.type,
                            "lat": lat,
                            "lon": lon,
                            "count": row.visit_count
                        })
                 except ValueError:
                     continue
        return heatmap_data
