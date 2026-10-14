"""
Resource optimization router powered by SciPy Linear Programming (HiGHS).
Solves optimal land, water, fertilizer, and budget allocations.
"""

from fastapi import APIRouter
from backend.app.schemas.optimizer import (
    AllocationRequest,
    AllocationResponse,
    StrategyComparisonRequest,
    StrategyComparisonResponse,
)
from backend.app.optimizer.linear_programming import optimizer

router = APIRouter(prefix="/optimize", tags=["Resource Optimization"])


@router.post("/allocate", response_model=AllocationResponse)
def optimize_allocation(payload: AllocationRequest):
    """
    Solves linear programming to find optimal land allocation (acres per crop)
    under available water, fertilizer, budget, and strategy preferences.
    """
    result = optimizer.solve_allocation(
        crop_ids=payload.crop_ids,
        total_land_acres=payload.total_land_acres,
        water_available_kl=payload.water_available_kl,
        fertilizer_available_kg=payload.fertilizer_available_kg,
        total_budget_inr=payload.total_budget_inr,
        strategy=payload.strategy,
        custom_bounds=payload.custom_bounds,
    )
    return AllocationResponse(**result)


@router.post("/strategies", response_model=StrategyComparisonResponse)
def compare_strategies(payload: StrategyComparisonRequest):
    """
    Compares 4 distinct agricultural resource strategies side-by-side:
    - Balanced: Multi-objective diversification
    - Max Profit: Maximum commercial return
    - Water Saver: Lowest water consumption with baseline profit guarantee
    - Low Budget: Lowest cultivation expenditure with baseline yield guarantee
    """
    results = optimizer.compare_strategies(
        crop_ids=payload.crop_ids,
        total_land_acres=payload.total_land_acres,
        water_available_kl=payload.water_available_kl,
        fertilizer_available_kg=payload.fertilizer_available_kg,
        total_budget_inr=payload.total_budget_inr,
    )
    allocations = [AllocationResponse(**res) for res in results]
    return StrategyComparisonResponse(strategies=allocations)
