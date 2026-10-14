"""
Agricultural Datasets & Provenance Router for TERRA.

Exposes endpoints for querying:
- Acquired public dataset provenance and metadata
- Real empirical district yield benchmarks (DES / Ministry of Agriculture records)
- NASA POWER agroclimate profiles
- Honest ML model evaluations against real benchmark observations
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from backend.app.data.real_data_pipeline import pipeline

router = APIRouter(prefix="/data", tags=["Agricultural Datasets & Provenance"])


@router.get("/provenance")
def get_dataset_provenance():
    """
    Returns the comprehensive machine-readable provenance catalog
    for all acquired public agricultural datasets (DES India, NASA POWER, ICAR).
    """
    try:
        return pipeline.load_provenance_catalog()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load provenance catalog: {str(e)}")


@router.get("/benchmarks/{crop_id}")
def get_crop_yield_benchmarks(
    crop_id: str,
    season: Optional[str] = Query(None, description="Optional season filter ('Kharif', 'Rabi', 'Zaid', 'Whole Year')")
):
    """
    Returns empirical yield distribution statistics (median, mean, p10, p90, IQR)
    from 122,400+ official Indian district-wise crop production records.
    """
    benchmarks = pipeline.get_real_yield_benchmarks(crop_id=crop_id.lower(), season=season)
    if benchmarks.get("count") == 0:
        raise HTTPException(status_code=404, detail=benchmarks.get("message"))
    return benchmarks


@router.get("/climate/{district_id}")
def get_district_climate(district_id: str):
    """
    Returns NASA POWER seasonal agro-climatic profile for a specified district
    (e.g. 'nashik_maharashtra', 'ludhiana_punjab', 'thanjavur_tamil_nadu').
    """
    profiles = pipeline.load_district_climate_profiles()
    key = district_id.lower()
    if key not in profiles:
        available = list(profiles.keys())
        raise HTTPException(
            status_code=404,
            detail=f"District '{district_id}' not found. Available districts: {available}"
        )
    return profiles[key]


@router.get("/evaluation/classifier")
def get_classifier_real_data_evaluation(
    n_folds: int = Query(5, ge=2, le=10, description="Number of cross-validation folds")
):
    """
    Evaluates the Crop Suitability Classifier on the 2,200-sample Atharva Ingle / Kaggle benchmark.
    Returns empirical cross-validation metrics across 22 augmented crop clusters.
    """
    try:
        return pipeline.evaluate_classifier_on_real_data(n_folds=n_folds)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@router.get("/evaluation/regressor")
def get_regressor_real_data_benchmarks():
    """
    Benchmarks Terra yield base potential against empirical district yield distributions
    from 122,427 official Indian agricultural records across 19 crops (DES India).
    NOTE: Regional macro-benchmarking does not validate farm-level NPK/water prediction accuracy.
    """
    try:
        return pipeline.benchmark_regressor_against_real_yields()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmarking failed: {str(e)}")
