"""Disease endpoints"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.db.models import Disease

router = APIRouter()


@router.get("/", response_model=List[dict])
async def list_diseases(
    active_only: bool = True,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all diseases (public endpoint)"""
    query = db.query(Disease)
    if active_only:
        query = query.filter(Disease.is_active == True)
    
    diseases = query.offset(skip).limit(limit).all()
    return [
        {
            "id": d.id,
            "name": d.name,
            "code": d.code,
            "description": d.description,
            "is_active": d.is_active
        }
        for d in diseases
    ]


@router.get("/{disease_id}", response_model=dict)
async def get_disease(
    disease_id: int,
    db: Session = Depends(get_db)
):
    """Get disease by ID (public endpoint)"""
    disease = db.query(Disease).filter(Disease.id == disease_id).first()
    if not disease:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Disease not found"
        )
    
    return {
        "id": disease.id,
        "name": disease.name,
        "code": disease.code,
        "description": disease.description,
        "is_active": disease.is_active
    }
