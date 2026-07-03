from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.core.database import get_db
from app.services.public_health_service import PublicHealthService
from app.db.models import NewsArticle
from app.schemas import news as news_schema

router = APIRouter()

@router.get("/stats")
def get_public_stats(db: Session = Depends(get_db)):
    """Get national aggregated stats (Public)"""
    return PublicHealthService.get_national_stats(db)

@router.get("/provinces")
def get_provincial_stats(db: Session = Depends(get_db)):
    """Get provincial aggregates (Public)"""
    return PublicHealthService.get_provincial_aggregates(db)

@router.get("/map")
def get_public_map(db: Session = Depends(get_db)):
    """Get map data for public display (Public - Opt-in only)"""
    return PublicHealthService.get_public_map_data(db)

@router.get("/alerts")
def get_public_alerts(db: Session = Depends(get_db)):
    """Get sanitized alerts (Public)"""
    return PublicHealthService.get_public_alerts(db)

@router.get("/news", response_model=List[news_schema.NewsArticle])
def get_public_news(db: Session = Depends(get_db)):
    """Get health news articles (Public)"""
    return db.query(NewsArticle).filter(NewsArticle.is_public == True).order_by(NewsArticle.published_at.desc()).all()
