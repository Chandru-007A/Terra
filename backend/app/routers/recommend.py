"""
Crop recommendation router powered by Machine Learning and Agronomic scoring.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from backend.app.schemas.crop import (
    CropRecommendationRequest,
    CropRecommendationResponse,
    CropItem,
)
from backend.app.data.crop_database import CROPS_DATABASE, get_crop, list_crops
from backend.app.ml.model_registry import registry

router = APIRouter(prefix="/recommend", tags=["Crop Recommendation"])


@router.post("/crops", response_model=CropRecommendationResponse)
def recommend_crops(payload: CropRecommendationRequest):
    """
    Predicts suitable crops based on soil nutrients (N, P, K, pH)
    and weather conditions (temperature, humidity, rainfall).
    """
    classifier = registry.get_crop_classifier()
    recommendations = classifier.predict_suitability(
        n=payload.n,
        p=payload.p,
        k=payload.k,
        ph=payload.ph,
        temperature=payload.temperature,
        humidity=payload.humidity,
        rainfall=payload.rainfall,
        season=payload.season,
        top_k=payload.top_k,
    )

    crop_items = []
    for idx, rec in enumerate(recommendations, start=1):
        item = CropItem(
            id=idx,
            crop_id=rec["crop_id"],
            emoji=rec["emoji"],
            title=rec["title"],
            suitability=rec["suitability"],
            status=rec["status"],
            yield_str=rec["yield"],
            sow=rec["sow"],
            profit=rec["profit"],
            water=rec["water"],
            variant=rec["variant"],
            expected_yield_q=rec["expected_yield_q"],
            expected_profit=rec["expected_profit"],
            water_requirement_kl=rec["water_requirement_kl"],
            fertilizer_kg=rec["fertilizer_kg"],
            cost_per_acre=rec["cost_per_acre"],
            market_price_per_q=rec["market_price_per_q"],
            key_advantages=rec["key_advantages"],
            irrigation_advice=rec["irrigation_advice"],
        )
        crop_items.append(item)

    return CropRecommendationResponse(count=len(crop_items), crops=crop_items)


@router.get("/crops", response_model=List[dict])
def get_all_crops(season: Optional[str] = Query(None, description="Optional season filter (Rabi, Kharif, Zaid, All)")):
    """Lists all registered crops with their agronomic profiles."""
    crops = list_crops(season)
    return [c.model_dump() for c in crops]


@router.get("/crops/{crop_id}", response_model=dict)
def get_crop_details(crop_id: str):
    """Retrieves in-depth agronomic and economic details for a specific crop."""
    crop = get_crop(crop_id)
    if not crop:
        raise HTTPException(status_code=404, detail=f"Crop '{crop_id}' not found in database")
    return crop.model_dump()
