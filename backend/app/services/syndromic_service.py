from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from typing import Dict, List, Any
from app.db.models import Encounter, Diagnosis, Facility

class SyndromicService:
    # Definition of syndromes based on simple keyword sets (In production, use Codes)
    SYNDROME_DEFINITIONS = {
        "Febrile Illness": ["fever", "chills", "high temp"],
        "Acute Respiratory": ["cough", "shortness of breath", "difficulty breathing", "sore throat"],
        "Gastrointestinal": ["diarrhea", "vomiting", "nausea", "abdominal pain"],
        "Neurological": ["seizure", "confusion", "stiff neck", "paralysis"]
    }
    SYNDROME_KEYS = {
        "Febrile Illness": "febrile_illness",
        "Acute Respiratory": "acute_respiratory",
        "Gastrointestinal": "gastrointestinal",
        "Neurological": "neurological",
    }

    @staticmethod
    def analyze_encounter(encounter: Encounter) -> List[str]:
        """Determine syndromes for a single encounter"""
        detected_syndromes = []
        # Check symptoms (Assuming list of strings for now)
        if not encounter.symptoms:
            return []
            
        symptoms_lower = [s.lower() for s in encounter.symptoms]
        
        for syndrome, keywords in SyndromicService.SYNDROME_DEFINITIONS.items():
            for kw in keywords:
                # Check for substring match in any symptom
                if any(kw in s for s in symptoms_lower):
                    detected_syndromes.append(syndrome)
                    break
        return detected_syndromes

    @staticmethod
    def get_facility_aggregates(db: Session, facility_id: int, start_date: date, end_date: date) -> Dict[str, int]:
        """Aggregate syndromes for a facility over a period"""
        encounters = db.query(Encounter).filter(
            Encounter.facility_id == facility_id,
            Encounter.date >= start_date,
            Encounter.date <= end_date
        ).all()
        
        totals = {s: 0 for s in SyndromicService.SYNDROME_DEFINITIONS.keys()}
        
        for enc in encounters:
            syndromes = SyndromicService.analyze_encounter(enc)
            for s in syndromes:
                totals[s] += 1
                
        return totals

    @staticmethod
    def get_national_trends(
        db: Session,
        days: int = 7,
        facility_id: int | None = None,
    ) -> List[Dict[str, Any]]:
        """Get daily totals, optionally constrained to one facility."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # This is inefficient for large datasets (fetching all encounters). 
        # In production, we'd use a materialised view or daily summary table.
        # For prototype, we'll iterate.
        query = db.query(Encounter).filter(Encounter.date >= start_date)
        if facility_id is not None:
            query = query.filter(Encounter.facility_id == facility_id)
        encounters = query.all()
        
        # Structure: {date: {syndrome: count}}
        daily_stats = {}
        
        for enc in encounters:
            d_str = enc.date.date().isoformat()
            if d_str not in daily_stats:
                daily_stats[d_str] = {s: 0 for s in SyndromicService.SYNDROME_DEFINITIONS.keys()}
            
            syndromes = SyndromicService.analyze_encounter(enc)
            for s in syndromes:
                daily_stats[d_str][s] += 1
                
        # Format for chart
        result = []
        current = start_date
        while current <= end_date:
            d_key = current.isoformat()
            stats = daily_stats.get(d_key, {s: 0 for s in SyndromicService.SYNDROME_DEFINITIONS.keys()})
            result.append({
                "date": d_key,
                **{SyndromicService.SYNDROME_KEYS[name]: count for name, count in stats.items()},
            })
            current += timedelta(days=1)
            
        return result
