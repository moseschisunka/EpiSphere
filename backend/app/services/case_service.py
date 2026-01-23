"""Case data service"""

from typing import List, Optional
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from app.db.models import Case, Country, Disease
from app.schemas.case import CaseStats


class CaseService:
    """Service for case data operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_case_stats(
        self,
        country_id: Optional[int] = None,
        disease_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[CaseStats]:
        """Get case statistics for dashboard"""
        query = self.db.query(
            Case,
            Country.name.label("country_name"),
            Disease.name.label("disease_name")
        ).join(Country).join(Disease)
        
        if country_id:
            query = query.filter(Case.country_id == country_id)
        if disease_id:
            query = query.filter(Case.disease_id == disease_id)
        if start_date:
            query = query.filter(Case.date >= start_date)
        if end_date:
            query = query.filter(Case.date <= end_date)
        
        results = query.order_by(desc(Case.date)).all()
        
        stats_list = []
        for case, country_name, disease_name in results:
            # Calculate incidence per 100k if population available
            country = self.db.query(Country).filter(Country.id == case.country_id).first()
            population = country.population if country else None
            incidence_per_100k = None
            if population and population > 0:
                incidence_per_100k = (case.cumulative_cases / population) * 100000
            
            # Calculate CFR
            cfr = None
            if case.cumulative_cases > 0:
                cfr = (case.cumulative_deaths / case.cumulative_cases) * 100
            
            # Calculate 7-day growth rate
            growth_rate = self._calculate_growth_rate(case.country_id, case.disease_id, case.date)
            
            stats = CaseStats(
                country_id=case.country_id,
                country_name=country_name,
                disease_id=case.disease_id,
                disease_name=disease_name,
                date=case.date,
                daily_cases=case.daily_cases,
                cumulative_cases=case.cumulative_cases,
                daily_deaths=case.daily_deaths,
                cumulative_deaths=case.cumulative_deaths,
                incidence_per_100k=incidence_per_100k,
                cfr=cfr,
                growth_rate=growth_rate
            )
            stats_list.append(stats)
        
        return stats_list
    
    def _calculate_growth_rate(self, country_id: int, disease_id: int, current_date: date) -> Optional[float]:
        """Calculate 7-day growth rate"""
        try:
            # Get cases 7 days ago and today
            date_7_days_ago = current_date - timedelta(days=7)
            
            case_today = self.db.query(Case).filter(
                and_(
                    Case.country_id == country_id,
                    Case.disease_id == disease_id,
                    Case.date == current_date
                )
            ).first()
            
            case_7_days_ago = self.db.query(Case).filter(
                and_(
                    Case.country_id == country_id,
                    Case.disease_id == disease_id,
                    Case.date == date_7_days_ago
                )
            ).first()
            
            if not case_today or not case_7_days_ago:
                return None
            
            if case_7_days_ago.cumulative_cases == 0:
                return None
            
            # Calculate growth rate: ((current - past) / past) * 100
            growth_rate = ((case_today.cumulative_cases - case_7_days_ago.cumulative_cases) / 
                          case_7_days_ago.cumulative_cases) * 100
            
            return round(growth_rate, 2)
        
        except Exception:
            return None
    
    def get_7day_moving_average(
        self,
        country_id: int,
        disease_id: int,
        end_date: date
    ) -> Optional[float]:
        """Calculate 7-day moving average of daily cases"""
        start_date = end_date - timedelta(days=6)
        
        result = self.db.query(func.avg(Case.daily_cases)).filter(
            and_(
                Case.country_id == country_id,
                Case.disease_id == disease_id,
                Case.date >= start_date,
                Case.date <= end_date
            )
        ).scalar()
        
        return float(result) if result else None
