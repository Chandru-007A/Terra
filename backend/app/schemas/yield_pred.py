"""
Pydantic schemas for yield prediction.
"""

from typing import Optional, Dict
from pydantic import BaseModel, Field


class YieldPredictionRequest(BaseModel):
    crop_id: str
    n: float = Field(default=80.0, ge=0.0, le=500.0, description="Soil nitrogen (kg/ha), 0–500")
    p: float = Field(default=45.0, ge=0.0, le=500.0, description="Soil phosphorus (kg/ha), 0–500")
    k: float = Field(default=60.0, ge=0.0, le=500.0, description="Soil potassium (kg/ha), 0–500")
    ph: float = Field(default=7.0, ge=3.5, le=10.5, description="Soil pH, 3.5–10.5")
    temperature: float = Field(default=22.0, ge=-5.0, le=55.0, description="Temperature (°C), −5 to 55")
    rainfall: float = Field(default=450.0, ge=0.0, le=10000.0, description="Seasonal rainfall (mm), 0–10000")
    water_available_kl: Optional[float] = Field(default=None, ge=0.0)
    fertilizer_applied_kg: Optional[float] = Field(default=None, ge=0.0)



class ConfidenceInterval(BaseModel):
    lower_q_per_acre: float
    upper_q_per_acre: float


class YieldPredictionResponse(BaseModel):
    crop_id: str
    crop_name: str
    emoji: str
    expected_yield_q_per_acre: float
    confidence_interval_95: ConfidenceInterval
    # Clarifies that confidence_interval_95 is a heuristic, not a validated CI
    prediction_range_note: Optional[str] = None
    benchmark_yield_q_per_acre: float
    yield_gap_percent: float
    market_price_per_q: float
    gross_revenue_per_acre: float
    cultivation_cost_per_acre: float
    expected_profit_per_acre: float
    profit_margin_percent: float
    water_required_kl_per_acre: float
    fertilizer_required_kg_per_acre: float

