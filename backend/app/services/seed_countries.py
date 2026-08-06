import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.db.models import Region, Country

logger = logging.getLogger(__name__)

REGIONS = [
    {"name": "Africa", "code": "AFR", "description": "WHO African Region"},
    {"name": "Americas", "code": "AMR", "description": "WHO Region of the Americas"},
    {"name": "Europe", "code": "EUR", "description": "WHO European Region"},
    {"name": "Eastern Mediterranean", "code": "EMR", "description": "WHO Eastern Mediterranean Region"},
    {"name": "South-East Asia", "code": "SEAR", "description": "WHO South-East Asia Region"},
    {"name": "Western Pacific", "code": "WPR", "description": "WHO Western Pacific Region"},
]

COUNTRIES = [
    {"name": "United States", "iso_code": "USA", "iso_code_2": "US", "region_code": "AMR", "population": 331002651, "latitude": 37.0902, "longitude": -95.7129},
    {"name": "China", "iso_code": "CHN", "iso_code_2": "CN", "region_code": "WPR", "population": 1439323776, "latitude": 35.8617, "longitude": 104.1954},
    {"name": "India", "iso_code": "IND", "iso_code_2": "IN", "region_code": "SEAR", "population": 1380004385, "latitude": 20.5937, "longitude": 78.9629},
    {"name": "Brazil", "iso_code": "BRA", "iso_code_2": "BR", "region_code": "AMR", "population": 212559417, "latitude": -14.235, "longitude": -51.9253},
    {"name": "Nigeria", "iso_code": "NGA", "iso_code_2": "NG", "region_code": "AFR", "population": 206139589, "latitude": 9.082, "longitude": 8.6753},
    {"name": "Russia", "iso_code": "RUS", "iso_code_2": "RU", "region_code": "EUR", "population": 145934462, "latitude": 61.524, "longitude": 105.3188},
    {"name": "Japan", "iso_code": "JPN", "iso_code_2": "JP", "region_code": "WPR", "population": 126476461, "latitude": 36.2048, "longitude": 138.2529},
    {"name": "Mexico", "iso_code": "MEX", "iso_code_2": "MX", "region_code": "AMR", "population": 128932753, "latitude": 23.6345, "longitude": -102.5528},
    {"name": "Germany", "iso_code": "DEU", "iso_code_2": "DE", "region_code": "EUR", "population": 83783942, "latitude": 51.1657, "longitude": 10.4515},
    {"name": "United Kingdom", "iso_code": "GBR", "iso_code_2": "GB", "region_code": "EUR", "population": 67886011, "latitude": 55.3781, "longitude": -3.436},
    {"name": "France", "iso_code": "FRA", "iso_code_2": "FR", "region_code": "EUR", "population": 65273511, "latitude": 46.2276, "longitude": 2.2137},
    {"name": "Italy", "iso_code": "ITA", "iso_code_2": "IT", "region_code": "EUR", "population": 60461826, "latitude": 41.8719, "longitude": 12.5674},
    {"name": "South Africa", "iso_code": "ZAF", "iso_code_2": "ZA", "region_code": "AFR", "population": 59308690, "latitude": -30.5595, "longitude": 22.9375},
    {"name": "Kenya", "iso_code": "KEN", "iso_code_2": "KE", "region_code": "AFR", "population": 53771296, "latitude": -1.2921, "longitude": 36.8219},
    {"name": "Egypt", "iso_code": "EGY", "iso_code_2": "EG", "region_code": "EMR", "population": 102334404, "latitude": 26.8206, "longitude": 30.8025},
    {"name": "Australia", "iso_code": "AUS", "iso_code_2": "AU", "region_code": "WPR", "population": 25499884, "latitude": -25.2744, "longitude": 133.7751},
    {"name": "Canada", "iso_code": "CAN", "iso_code_2": "CA", "region_code": "AMR", "population": 37742154, "latitude": 56.1304, "longitude": -106.3468},
    {"name": "Argentina", "iso_code": "ARG", "iso_code_2": "AR", "region_code": "AMR", "population": 45195774, "latitude": -38.4161, "longitude": -63.6167},
    {"name": "Saudi Arabia", "iso_code": "SAU", "iso_code_2": "SA", "region_code": "EMR", "population": 34813871, "latitude": 23.8859, "longitude": 45.0792},
    {"name": "Indonesia", "iso_code": "IDN", "iso_code_2": "ID", "region_code": "SEAR", "population": 273523615, "latitude": -0.7893, "longitude": 113.9213},
    {"name": "Pakistan", "iso_code": "PAK", "iso_code_2": "PK", "region_code": "EMR", "population": 220892340, "latitude": 30.3753, "longitude": 69.3451},
    {"name": "Bangladesh", "iso_code": "BGD", "iso_code_2": "BD", "region_code": "SEAR", "population": 164689383, "latitude": 23.685, "longitude": 90.3563},
    {"name": "Ethiopia", "iso_code": "ETH", "iso_code_2": "ET", "region_code": "AFR", "population": 114963588, "latitude": 9.145, "longitude": 40.4897},
    {"name": "Philippines", "iso_code": "PHL", "iso_code_2": "PH", "region_code": "WPR", "population": 109581078, "latitude": 12.8797, "longitude": 121.774},
    {"name": "Vietnam", "iso_code": "VNM", "iso_code_2": "VN", "region_code": "WPR", "population": 97338579, "latitude": 14.0583, "longitude": 108.2772},
    {"name": "Turkey", "iso_code": "TUR", "iso_code_2": "TR", "region_code": "EUR", "population": 84339067, "latitude": 38.9637, "longitude": 35.2433},
    {"name": "Iran", "iso_code": "IRN", "iso_code_2": "IR", "region_code": "EMR", "population": 83992949, "latitude": 32.4279, "longitude": 53.688},
    {"name": "Thailand", "iso_code": "THA", "iso_code_2": "TH", "region_code": "SEAR", "population": 69799978, "latitude": 15.87, "longitude": 100.9925},
    {"name": "Tanzania", "iso_code": "TZA", "iso_code_2": "TZ", "region_code": "AFR", "population": 59734218, "latitude": -6.369, "longitude": 34.8888},
    {"name": "Spain", "iso_code": "ESP", "iso_code_2": "ES", "region_code": "EUR", "population": 46754778, "latitude": 40.4637, "longitude": -3.7492},
    {"name": "Colombia", "iso_code": "COL", "iso_code_2": "CO", "region_code": "AMR", "population": 50882891, "latitude": 4.5709, "longitude": -74.2973},
    {"name": "Uganda", "iso_code": "UGA", "iso_code_2": "UG", "region_code": "AFR", "population": 45741007, "latitude": 1.3733, "longitude": 32.2903},
    {"name": "Sudan", "iso_code": "SDN", "iso_code_2": "SD", "region_code": "EMR", "population": 43849260, "latitude": 12.8628, "longitude": 30.2176},
    {"name": "Ukraine", "iso_code": "UKR", "iso_code_2": "UA", "region_code": "EUR", "population": 43733762, "latitude": 48.3794, "longitude": 31.1656},
    {"name": "Iraq", "iso_code": "IRQ", "iso_code_2": "IQ", "region_code": "EMR", "population": 40222493, "latitude": 33.2232, "longitude": 43.6793},
    {"name": "Afghanistan", "iso_code": "AFG", "iso_code_2": "AF", "region_code": "EMR", "population": 38928346, "latitude": 33.9391, "longitude": 67.7099},
    {"name": "Poland", "iso_code": "POL", "iso_code_2": "PL", "region_code": "EUR", "population": 37846611, "latitude": 51.9194, "longitude": 19.1451},
    {"name": "Morocco", "iso_code": "MAR", "iso_code_2": "MA", "region_code": "EMR", "population": 36910560, "latitude": 31.7917, "longitude": -7.0926},
    {"name": "Peru", "iso_code": "PER", "iso_code_2": "PE", "region_code": "AMR", "population": 32971854, "latitude": -9.19, "longitude": -75.0152},
    {"name": "Malaysia", "iso_code": "MYS", "iso_code_2": "MY", "region_code": "WPR", "population": 32365999, "latitude": 4.2105, "longitude": 101.9758},
    {"name": "Uzbekistan", "iso_code": "UZB", "iso_code_2": "UZ", "region_code": "EUR", "population": 33469203, "latitude": 41.3775, "longitude": 64.5853},
    {"name": "Venezuela", "iso_code": "VEN", "iso_code_2": "VE", "region_code": "AMR", "population": 28435940, "latitude": 6.4238, "longitude": -66.5897},
    {"name": "Nepal", "iso_code": "NPL", "iso_code_2": "NP", "region_code": "SEAR", "population": 29136808, "latitude": 28.3949, "longitude": 84.124},
    {"name": "Ghana", "iso_code": "GHA", "iso_code_2": "GH", "region_code": "AFR", "population": 31072940, "latitude": 7.9465, "longitude": -1.0232},
    {"name": "Yemen", "iso_code": "YEM", "iso_code_2": "YE", "region_code": "EMR", "population": 29825964, "latitude": 15.5527, "longitude": 48.5164},
    {"name": "Madagascar", "iso_code": "MDG", "iso_code_2": "MG", "region_code": "AFR", "population": 27691018, "latitude": -18.7669, "longitude": 46.8691},
    {"name": "North Korea", "iso_code": "PRK", "iso_code_2": "KP", "region_code": "SEAR", "population": 25778816, "latitude": 40.3399, "longitude": 127.5101},
    {"name": "South Korea", "iso_code": "KOR", "iso_code_2": "KR", "region_code": "WPR", "population": 51269185, "latitude": 35.9078, "longitude": 127.7669},
    {"name": "Taiwan", "iso_code": "TWN", "iso_code_2": "TW", "region_code": "WPR", "population": 23816775, "latitude": 23.6978, "longitude": 120.9605},
    {"name": "Syria", "iso_code": "SYR", "iso_code_2": "SY", "region_code": "EMR", "population": 17500658, "latitude": 34.8021, "longitude": 38.9968},
    {"name": "Sri Lanka", "iso_code": "LKA", "iso_code_2": "LK", "region_code": "SEAR", "population": 21413249, "latitude": 7.8731, "longitude": 80.7718},
]

async def seed_countries_and_regions(db: AsyncSession | Session):
    is_async = isinstance(db, AsyncSession)
    
    try:
        region_map = {}
        for r_data in REGIONS:
            if is_async:
                res = await db.execute(select(Region).filter_by(code=r_data["code"]))
                region = res.scalar_one_or_none()
            else:
                region = db.query(Region).filter_by(code=r_data["code"]).first()
                
            if not region:
                region = Region(name=r_data["name"], code=r_data["code"], description=r_data.get("description", ""))
                db.add(region)
                if is_async:
                    await db.flush()
                else:
                    db.flush()
            
            region_map[r_data["code"]] = region.id
            
        for c_data in COUNTRIES:
            if is_async:
                res = await db.execute(select(Country).filter_by(iso_code=c_data["iso_code"]))
                country = res.scalar_one_or_none()
            else:
                country = db.query(Country).filter_by(iso_code=c_data["iso_code"]).first()
                
            region_id = region_map.get(c_data["region_code"])
            
            if not country:
                country = Country(
                    name=c_data["name"],
                    iso_code=c_data["iso_code"],
                    iso_code_2=c_data["iso_code_2"],
                    region_id=region_id,
                    population=c_data["population"],
                    latitude=c_data["latitude"],
                    longitude=c_data["longitude"]
                )
                db.add(country)
            else:
                country.name = c_data["name"]
                country.iso_code_2 = c_data["iso_code_2"]
                country.region_id = region_id
                country.population = c_data["population"]
                country.latitude = c_data["latitude"]
                country.longitude = c_data["longitude"]
                
        if is_async:
            await db.commit()
        else:
            db.commit()
            
        return {"status": "success", "regions_seeded": len(REGIONS), "countries_seeded": len(COUNTRIES)}
    except Exception as e:
        logger.error(f"Error seeding countries: {e}")
        if is_async:
            await db.rollback()
        else:
            db.rollback()
        raise e
