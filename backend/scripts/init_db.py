"""
Database initialization script
Creates initial roles, countries, regions, and diseases
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, sync_engine
from app.db.models import Base, Role, Country, Region, Disease


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


def main():
    """Main initialization function"""
    print("Initializing database...")
    
    # Create tables
    Base.metadata.create_all(bind=sync_engine)
    print("Tables created.")
    
    # Initialize data
    db = SessionLocal()
    try:
        init_roles(db)
        init_regions(db)
        init_countries(db)
        init_diseases(db)
        print("\nDatabase initialization complete!")
    except Exception as e:
        print(f"Error during initialization: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
