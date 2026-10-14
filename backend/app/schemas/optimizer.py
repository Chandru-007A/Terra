"""
Pydantic schemas for linear programming resource optimization.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class CropAllocationItem(BaseModel):
    crop_id: str
    name: str
    emoji: str
    acres: float
    expected_yield_q: float
    expected_profit_inr: float
    formatted_profit: str
    water_used_kl: float
    cost_inr: float
    profit_margin_percent: float
    status: str


class AllocationRequest(BaseModel):
    crop_ids: List[str] = Field(
        default=["onion", "wheat", "chickpea", "mustard"],
        description="Shortlisted candidate crops to allocate land between"
    )
    total_land_acres: float = Field(default=10.0, ge=0.5, le=10000.0)
    water_available_kl: float = Field(default=16000.0, ge=100.0)
    fertilizer_available_kg: float = Field(default=1000.0, ge=10.0)
    total_budget_inr: float = Field(default=400000.0, ge=5000.0)
    strategy: str = Field(default="balanced", description="'balanced', 'max_profit', 'water_saver', or 'low_budget'")
    custom_bounds: Optional[Dict[str, Dict[str, float]]] = None


class ConstraintsSummary(BaseModel):
    land_utilization_percent: float
    water_utilization_percent: float
    fertilizer_utilization_percent: float
    budget_utilization_percent: float


class AllocationResponse(BaseModel):
    strategy: str
    status: str  # "Optimal" or "Infeasible"
    error: Optional[str] = None      # present when status == "Infeasible"
    warning: Optional[str] = None    # present when some crop IDs were unknown
    total_land_allocated_acres: float
    total_land_available_acres: float
    total_water_used_kl: float
    total_water_available_kl: float
    water_saved_percent: float
    water_saved_str: str
    total_fertilizer_used_kg: float
    total_fertilizer_available_kg: float
    fertilizer_saved_percent: float
    fertilizer_saved_str: str
    total_budget_used_inr: float
    total_budget_available_inr: float
    budget_used_str: str
    expected_total_production_q: float
    expected_production_str: str
    expected_net_profit_inr: float
    expected_profit_str: str
    profit_increase_percent: float
    profit_vs_max_percent: Optional[float] = None
    crops: List[CropAllocationItem]
    constraints_summary: ConstraintsSummary



class StrategyComparisonRequest(BaseModel):
    crop_ids: List[str] = Field(default=["onion", "wheat", "chickpea", "mustard"])
    total_land_acres: float = Field(default=10.0)
    water_available_kl: float = Field(default=16000.0)
    fertilizer_available_kg: float = Field(default=1000.0)
    total_budget_inr: float = Field(default=400000.0)


class StrategyComparisonResponse(BaseModel):
    strategies: List[AllocationResponse]
