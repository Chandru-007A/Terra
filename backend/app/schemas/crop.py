"""
Pydantic schemas for crop recommendation and catalog.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class CropRecommendationRequest(BaseModel):
    n: float = Field(default=80.0, description="Nitrogen content in soil (kg/ha or index)")
    p: float = Field(default=45.0, description="Phosphorus content in soil (kg/ha or index)")
    k: float = Field(default=60.0, description="Potassium content in soil (kg/ha or index)")
    ph: float = Field(default=7.0, description="Soil pH level (4.0 - 9.0)")
    temperature: float = Field(default=22.0, description="Ambient temperature (°C)")
    humidity: float = Field(default=60.0, description="Relative humidity (%)")
    rainfall: float = Field(default=450.0, description="Seasonal rainfall (mm)")
    season: Optional[str] = Field(default="Rabi", description="Season: 'Rabi', 'Kharif', 'Zaid', or 'All'")
    top_k: int = Field(default=10, description="Number of top crops to return")


class CropItem(BaseModel):
    id: Optional[int] = None
    crop_id: str
    emoji: str
    title: str
    suitability: str
    status: str  # "in" or "out"
    yield_str: str = Field(alias="yield")
    sow: str
    profit: str
    water: str
    variant: str  # "default", "secondary", "outline"
    expected_yield_q: float
    expected_profit: float
    water_requirement_kl: float
    fertilizer_kg: float
    cost_per_acre: float
    market_price_per_q: float
    key_advantages: List[str]
    irrigation_advice: str

    model_config = {"populate_by_name": True}


class CropRecommendationResponse(BaseModel):
    count: int
    crops: List[CropItem]
    field: Optional[dict] = None

