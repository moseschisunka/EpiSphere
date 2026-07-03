"""
Database initialization script
Creates initial roles, countries, regions, and diseases
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.db.models import Role, Country, Region, Disease, NewsArticle, SourceSystem, CodeSystem, StandardConcept, DHIS2Mapping


def init_roles(db: Session):
    """Initialize user roles"""
    roles = [
        {"name": "public", "description": "Public user - read-only access"},
        {"name": "country_data_officer", "description": "Country data officer - can upload data"},
        {"name": "epidemiologist", "description": "Epidemiologist - full analytics access"},
        {"name": "admin", "description": "Administrator - full system access"},
        {"name": "clinician", "description": "Clinician - manage patient encounters"},
        {"name": "pharmacist", "description": "Pharmacist - dispense medications"},
        {"name": "facility_admin", "description": "Facility Admin - manage facility users"}
    ]
    
    for role_data in roles:
        existing = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not existing:
            role = Role(**role_data)
            db.add(role)
            print(f"Created role: {role_data['name']}")
    
    db.commit()


def init_regions(db: Session):
    """Initialize WHO regions"""
    regions = [
        {"name": "African Region", "code": "AFRO"},
        {"name": "Region of the Americas", "code": "AMRO"},
        {"name": "South-East Asia Region", "code": "SEARO"},
        {"name": "European Region", "code": "EURO"},
        {"name": "Eastern Mediterranean Region", "code": "EMRO"},
        {"name": "Western Pacific Region", "code": "WPRO"}
    ]
    
    for region_data in regions:
        existing = db.query(Region).filter(Region.name == region_data["name"]).first()
        if not existing:
            region = Region(**region_data)
            db.add(region)
            print(f"Created region: {region_data['name']}")
    
    db.commit()


def init_countries(db: Session):
    """Initialize sample countries"""
    # Sample countries - in production, load from a comprehensive list
    countries = [
        {"name": "United States", "iso_code": "USA", "iso_code_2": "US", "population": 331900000},
        {"name": "United Kingdom", "iso_code": "GBR", "iso_code_2": "GB", "population": 67000000},
        {"name": "Canada", "iso_code": "CAN", "iso_code_2": "CA", "population": 38000000},
        {"name": "Germany", "iso_code": "DEU", "iso_code_2": "DE", "population": 83000000},
        {"name": "France", "iso_code": "FRA", "iso_code_2": "FR", "population": 67000000},
        {"name": "India", "iso_code": "IND", "iso_code_2": "IN", "population": 1380000000},
        {"name": "China", "iso_code": "CHN", "iso_code_2": "CN", "population": 1400000000},
        {"name": "Brazil", "iso_code": "BRA", "iso_code_2": "BR", "population": 215000000},
        {"name": "Nigeria", "iso_code": "NGA", "iso_code_2": "NG", "population": 218000000},
        {"name": "South Africa", "iso_code": "ZAF", "iso_code_2": "ZA", "population": 60000000},
    ]
    
    for country_data in countries:
        existing = db.query(Country).filter(Country.iso_code == country_data["iso_code"]).first()
        if not existing:
            country = Country(**country_data)
            db.add(country)
            print(f"Created country: {country_data['name']}")
    
    db.commit()


def init_diseases(db: Session):
    """Initialize diseases"""
    diseases = [
        {"name": "COVID-19", "code": "U07.1", "description": "Coronavirus disease 2019"},
        {"name": "Influenza", "code": "J09-J11", "description": "Seasonal influenza"},
        {"name": "Dengue", "code": "A90", "description": "Dengue fever"},
        {"name": "Malaria", "code": "B50-B54", "description": "Malaria"},
        {"name": "Cholera", "code": "A00", "description": "Cholera"},
        {"name": "Measles", "code": "B05", "description": "Measles"},
        {"name": "Tuberculosis", "code": "A15-A19", "description": "Tuberculosis"},
    ]
    
    for disease_data in diseases:
        existing = db.query(Disease).filter(Disease.name == disease_data["name"]).first()
        if not existing:
            disease = Disease(**disease_data)
            db.add(disease)
            print(f"Created disease: {disease_data['name']}")
    
    db.commit()


def init_news(db: Session):
    """Initialize news articles"""
    articles = [
        {
            "title": "Global Flu Trends 2025",
            "summary": "Influenza cases are rising globally. Here's what you need to know.",
            "content": "The 2025 flu season has seen a 15% increase in cases compared to last year. Experts recommend vaccination and hygiene practices. New strains identified include...",
            "source": "WHO",
            "image_url": "https://source.unsplash.com/random/800x600/?flu,hospital",
            "is_public": True
        },
        {
            "title": "New Malaria Vaccine Rollout",
            "summary": "Breakthrough malaria vaccine shows 77% efficacy in trials.",
            "content": "A new malaria vaccine developed by key researchers has shown promising results in Phase 3 trials. Distribution in high-risk regions is set to begin next month...",
            "source": "EpiSphere Science",
            "image_url": "https://source.unsplash.com/random/800x600/?vaccine,lab",
            "is_public": True
        },
        {
            "title": "Healthy Living Tips for Summer",
            "summary": "Stay hydrated and safe during the heatwave.",
            "content": "As temperatures rise, heat exhaustion becomes a major risk. Drink plenty of water, avoid direct sun during peak hours, and check on vulnerable neighbors...",
            "source": "Public Health Dept",
            "image_url": "https://source.unsplash.com/random/800x600/?water,sun",
            "is_public": True
        }
    ]

    for article_data in articles:
        existing = db.query(NewsArticle).filter(NewsArticle.title == article_data["title"]).first()
        if not existing:
            article = NewsArticle(**article_data)
            db.add(article)
            print(f"Created article: {article_data['title']}")
    
    db.commit()


def init_data_governance(db: Session):
    """Initialize source systems, terminology scaffolding, and DHIS2 mapping defaults."""
    source = db.query(SourceSystem).filter(SourceSystem.code == "manual_upload").first()
    if not source:
        db.add(SourceSystem(
            name="Manual Upload",
            code="manual_upload",
            system_type="manual_upload",
            owner="EpiSphere",
            is_active=True,
        ))
        print("Created source system: manual_upload")

    systems = [
        {"name": "ICD-10", "uri": "http://hl7.org/fhir/sid/icd-10", "version": "2019", "owner": "WHO"},
        {"name": "ICD-11", "uri": "https://icd.who.int/browse11", "version": "2024", "owner": "WHO"},
        {"name": "SNOMED CT", "uri": "http://snomed.info/sct", "version": "international", "owner": "SNOMED International"},
        {"name": "LOINC", "uri": "http://loinc.org", "version": "current", "owner": "Regenstrief Institute"},
        {"name": "DHIS2", "uri": "https://dhis2.org", "version": "2", "owner": "DHIS2"},
    ]
    for system_data in systems:
        existing = db.query(CodeSystem).filter(
            CodeSystem.name == system_data["name"],
            CodeSystem.version == system_data["version"],
        ).first()
        if not existing:
            db.add(CodeSystem(**system_data))
            print(f"Created code system: {system_data['name']}")
    db.commit()

    icd10 = db.query(CodeSystem).filter(CodeSystem.name == "ICD-10").first()
    if icd10:
        for disease in db.query(Disease).all():
            if not disease.code:
                continue
            existing = db.query(StandardConcept).filter(
                StandardConcept.code_system_id == icd10.id,
                StandardConcept.code == disease.code,
            ).first()
            if not existing:
                db.add(StandardConcept(
                    code_system_id=icd10.id,
                    code=disease.code,
                    display=disease.name,
                    concept_type="disease",
                    is_active=True,
                ))
                print(f"Created standard disease concept: {disease.name}")

    mapping = db.query(DHIS2Mapping).filter(DHIS2Mapping.dataset == "aggregate/dataValueSets").first()
    if not mapping:
        db.add(DHIS2Mapping(
            dataset="aggregate/dataValueSets",
            endpoint_path="api/dataValueSets",
            payload_type="aggregate",
            required_fields=["dataValues"],
            description="Default DHIS2 aggregate data value set payload.",
            is_active=True,
        ))
        print("Created DHIS2 mapping: aggregate/dataValueSets")

    db.commit()


def main():
    """Main initialization function"""
    print("Initializing database...")
    
    
    # Initialize data
    db = SessionLocal()
    try:
        init_roles(db)
        init_regions(db)
        init_countries(db)
        init_diseases(db)
        init_news(db)
        init_data_governance(db)
        print("\nDatabase initialization complete!")
    except Exception as e:
        print(f"Error during initialization: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()


