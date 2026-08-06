"""DHS Analytics and Inferential Statistics Endpoints"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from app.services.dhs_analytics_service import DHSAnalyticsService, DHS_INDICATORS, DHS_COUNTRIES
import hashlib
import json
from app.core.cache import get_cache, set_cache

router = APIRouter()


class DescriptiveRequest(BaseModel):
    country_codes: List[str]
    indicator: str


class InferentialRequest(BaseModel):
    test_type: str  # t_test, welch_t_test, mann_whitney, anova, chi_square, correlation, linear_regression
    country_codes: List[str]
    indicator_x: str
    indicator_y: Optional[str] = None


@router.get("/datasets")
def get_dhs_datasets():
    """Retrieve metadata of supported DHS indicators, countries, and survey waves."""
    return DHSAnalyticsService.get_metadata()


@router.post("/descriptive")
def compute_descriptive_stats(req: DescriptiveRequest):
    """Compute comprehensive descriptive statistical parameters for selected DHS indicator across countries."""
    if req.indicator not in DHS_INDICATORS:
        raise HTTPException(status_code=400, detail=f"Unsupported indicator '{req.indicator}'. Valid: {list(DHS_INDICATORS.keys())}")
    
    # Check cache
    cache_key = f"dhs_desc_{hashlib.md5(json.dumps(req.model_dump(), sort_keys=True).encode()).hexdigest()}"
    cached_result = get_cache(cache_key)
    if cached_result:
        return cached_result

    result = DHSAnalyticsService.get_descriptive_stats(
        country_codes=req.country_codes,
        indicator=req.indicator
    )
    
    # Cache result for 1 hour
    set_cache(cache_key, result, expire_seconds=3600)
    return result


@router.post("/inferential")
def run_inferential_stats(req: InferentialRequest):
    """Execute hypothesis testing (T-Test, Mann-Whitney U, ANOVA, Chi-Square, Correlation, OLS Regression)."""
    valid_tests = {"t_test", "welch_t_test", "mann_whitney", "anova", "chi_square", "correlation", "linear_regression"}
    if req.test_type.lower() not in valid_tests:
        raise HTTPException(status_code=400, detail=f"Invalid test_type '{req.test_type}'. Must be one of {list(valid_tests)}")
    
    if req.indicator_x not in DHS_INDICATORS:
        raise HTTPException(status_code=400, detail=f"Unsupported indicator_x '{req.indicator_x}'")

    # Check cache
    cache_key = f"dhs_inf_{hashlib.md5(json.dumps(req.model_dump(), sort_keys=True).encode()).hexdigest()}"
    cached_result = get_cache(cache_key)
    if cached_result:
        return cached_result

    result = DHSAnalyticsService.run_inferential_analysis(
        test_type=req.test_type,
        country_codes=req.country_codes,
        indicator_x=req.indicator_x,
        indicator_y=req.indicator_y
    )
    
    # Cache result for 1 hour
    set_cache(cache_key, result, expire_seconds=3600)
    return result
