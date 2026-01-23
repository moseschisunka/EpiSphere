from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from app.db.models import Facility, Encounter, Case, Alert, AlertSeverity

class PublicHealthService:
    
    @staticmethod
    def _privacy_filter(count: int, threshold: int = 5) -> Any:
        """Suppress small counts"""
        if count < threshold:
            return 0 # Or "Low" if returning string
        return count

    @staticmethod
    def get_national_stats(db: Session) -> Dict[str, Any]:
        """Get national aggregated stats (always visible)"""
        total_encounters = db.query(func.count(Encounter.id)).scalar() or 0
        total_facilities = db.query(func.count(Facility.id)).scalar() or 0
        
        # Syndromic Summary (Simple count of encounters with symptoms)
        # Note: In real app, reuse SyndromicService, but optimized for public view
        
        return {
            "total_visits_recorded": total_encounters,
            "participating_facilities": total_facilities,
            "alert_level": "Normal" # Placeholder, logic driven by Alerts
        }

    @staticmethod
    def get_provincial_aggregates(db: Session) -> List[Dict[str, Any]]:
        """Get stats aggregated by province"""
        # Join Facility -> Encounter
        results = db.query(
            Facility.province,
            func.count(Encounter.id).label("count")
        ).join(Encounter)\
         .filter(Facility.province != None)\
         .group_by(Facility.province)\
         .all()
         
        return [
            {"province": r.province, "visit_count": r.count}
            for r in results
        ]

    @staticmethod
    def get_public_map_data(db: Session) -> List[Dict[str, Any]]:
        """
        Get map data.
        1. Aggregated Province Centroids (Mocked or Calced).
        2. Individual Facilities IF public_visible=True.
        """
        # 1. Opt-in Facilities
        facilities = db.query(Facility).filter(Facility.public_visible == True).all()
        
        map_points = []
        for f in facilities:
            if f.location and "," in f.location:
                try:
                    lat, lon = map(float, f.location.split(","))
                    # Get count for this facility
                    count = db.query(func.count(Encounter.id)).filter(Encounter.facility_id == f.id).scalar() or 0
                    
                    map_points.append({
                        "type": "facility",
                        "name": f.name,
                        "lat": lat,
                        "lon": lon,
                        "count": PublicHealthService._privacy_filter(count)
                    })
                except:
                    continue
        
        # 2. Add Province Aggregates (Simplified: Just center points would be needed in real DB)
        
        return map_points

    @staticmethod
    def get_public_alerts(db: Session) -> List[Dict[str, Any]]:
        """Get high-level public alerts (sanitized)"""
        alerts = db.query(Alert).filter(
            Alert.severity.in_([AlertSeverity.MODERATE, AlertSeverity.HIGH]),
            Alert.status == "triggered"
        ).all()
        
        public_alerts = []
        for a in alerts:
            # Mask precise location if needed, or generalize
            public_alerts.append({
                "severity": a.severity,
                "message": f"Heightened activity detected for {a.disease_id} (monitoring ongoing)."
            })
            
        return public_alerts
