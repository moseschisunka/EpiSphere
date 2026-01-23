"""Data upload and validation service"""

import pandas as pd
import io
from typing import Dict, List, Any
from datetime import datetime
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import Case, Country, Disease, AuditLog, AuditAction
from app.core.config import settings


class DataUploadService:
    """Service for handling data uploads"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def upload_file(
        self,
        file: UploadFile,
        country_id: int,
        disease_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """Upload and process CSV/Excel file"""
        
        # Validate file extension
        file_ext = file.filename.split('.')[-1].lower()
        if file_ext not in ['csv', 'xlsx', 'xls']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file format. Supported: CSV, XLSX, XLS"
            )
        
        # Read file
        contents = await file.read()
        
        try:
            if file_ext == 'csv':
                df = pd.read_csv(io.BytesIO(contents))
            else:
                df = pd.read_excel(io.BytesIO(contents))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error reading file: {str(e)}"
            )
        
        # Validate required columns
        required_columns = ['date', 'daily_cases']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        # Validate country and disease
        country = self.db.query(Country).filter(Country.id == country_id).first()
        if not country:
            raise HTTPException(status_code=404, detail="Country not found")
        
        disease = self.db.query(Disease).filter(Disease.id == disease_id).first()
        if not disease:
            raise HTTPException(status_code=404, detail="Disease not found")
        
        # Process and validate data
        validated_cases = []
        errors = []
        
        for idx, row in df.iterrows():
            try:
                # Parse date
                date_value = pd.to_datetime(row['date']).date()
                
                # Get values with defaults
                daily_cases = int(row.get('daily_cases', 0))
                cumulative_cases = int(row.get('cumulative_cases', 0))
                daily_deaths = int(row.get('daily_deaths', 0))
                cumulative_deaths = int(row.get('cumulative_deaths', 0))
                daily_recovered = int(row.get('daily_recovered', 0)) if pd.notna(row.get('daily_recovered')) else None
                cumulative_recovered = int(row.get('cumulative_recovered', 0)) if pd.notna(row.get('cumulative_recovered')) else None
                
                # Validate logical consistency
                if daily_cases < 0 or cumulative_cases < 0:
                    errors.append(f"Row {idx + 2}: Negative case values")
                    continue
                
                # Check if case already exists
                existing = self.db.query(Case).filter(
                    Case.country_id == country_id,
                    Case.disease_id == disease_id,
                    Case.date == date_value
                ).first()
                
                if existing:
                    # Update existing record
                    existing.daily_cases = daily_cases
                    existing.cumulative_cases = cumulative_cases
                    existing.daily_deaths = daily_deaths
                    existing.cumulative_deaths = cumulative_deaths
                    if daily_recovered is not None:
                        existing.daily_recovered = daily_recovered
                    if cumulative_recovered is not None:
                        existing.cumulative_recovered = cumulative_recovered
                    existing.updated_at = datetime.utcnow()
                    validated_cases.append(existing)
                else:
                    # Create new case
                    new_case = Case(
                        country_id=country_id,
                        disease_id=disease_id,
                        date=date_value,
                        daily_cases=daily_cases,
                        cumulative_cases=cumulative_cases,
                        daily_deaths=daily_deaths,
                        cumulative_deaths=cumulative_deaths,
                        daily_recovered=daily_recovered,
                        cumulative_recovered=cumulative_recovered,
                        source=file.filename
                    )
                    validated_cases.append(new_case)
            
            except Exception as e:
                errors.append(f"Row {idx + 2}: {str(e)}")
                continue
        
        # Bulk insert/update
        if validated_cases:
            for case in validated_cases:
                if case.id is None:  # New case
                    self.db.add(case)
            
            self.db.commit()
            
            # Audit log
            audit_log = AuditLog(
                user_id=user_id,
                action=AuditAction.UPLOAD,
                resource_type="case",
                details={
                    "filename": file.filename,
                    "rows_processed": len(validated_cases),
                    "errors": len(errors),
                    "country_id": country_id,
                    "disease_id": disease_id
                }
            )
            self.db.add(audit_log)
            self.db.commit()
        
        return {
            "success": True,
            "rows_processed": len(validated_cases),
            "errors": errors,
            "message": f"Successfully processed {len(validated_cases)} case records"
        }
