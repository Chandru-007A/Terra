"""
Pydantic schemas for historical and active saved farm plans.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class PlanCrop(BaseModel):
    name: str
    acres: float


class PlanCreate(BaseModel):
    fieldId: Optional[str] = None
    fieldName: Optional[str] = None
    season: str
    strategy: str
    crops: List[PlanCrop]
    profit: str
    waterSaved: str
    fertilizerSaved: str
    status: str = "Current"


class PlanResponse(BaseModel):
    id: str
    fieldId: Optional[str] = None
    fieldName: Optional[str] = None
    season: str
    strategy: str
    crops: List[PlanCrop]
    profit: str
    waterSaved: str
    fertilizerSaved: str
    status: str
    createdAt: str


class PlanListResponse(BaseModel):
    plans: List[PlanResponse]
