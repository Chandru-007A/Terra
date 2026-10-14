"""
Crop yield prediction router powered by Gradient Boosting Regressor.
"""

from fastapi import APIRouter, HTTPException
from backend.app.schemas.yield_pred import YieldPredictionRequest, YieldPredictionResponse
from backend.app.ml.model_registry import registry

router = APIRouter(prefix="/predict", tags=["Yield Prediction"])


@router.post("/yield", response_model=YieldPredictionResponse)
def predict_yield(payload: YieldPredictionRequest):
    """
    Predicts expected harvest yield (quintals/acre) and financial performance
    for a chosen crop under specific soil, weather, water, and fertilizer conditions.
    """
    regressor = registry.get_yield_regressor()
    try:
        prediction = regressor.predict_yield(
            crop_id=payload.crop_id,
            n=payload.n,
            p=payload.p,
            k=payload.k,
            ph=payload.ph,
            temperature=payload.temperature,
            rainfall=payload.rainfall,
            water_available_kl=payload.water_available_kl,
            fertilizer_applied_kg=payload.fertilizer_applied_kg,
        )
        return YieldPredictionResponse(**prediction)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Yield prediction failed: {str(e)}")
