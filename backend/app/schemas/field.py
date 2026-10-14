"""
Pydantic schemas for farm field management and field-scoped operations.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class FieldCropItem(BaseModel):
    cropId: str
    name: str
    acres: float
    sow: Optional[str] = None
    season: Optional[str] = None
    status: Optional[str] = "in"


class FieldCreate(BaseModel):
    name: str
    areaAcres: float = Field(gt=0, description="Field area in acres, must be greater than zero")
    soilType: str
    location: str
    waterAvailableKl: Optional[float] = None
    fertilizerAvailableKg: Optional[float] = None
    budgetInr: Optional[float] = None
    crops: Optional[List[FieldCropItem]] = None


class FieldUpdate(BaseModel):
    name: Optional[str] = None
    areaAcres: Optional[float] = Field(default=None, gt=0)
    soilType: Optional[str] = None
    location: Optional[str] = None
    n: Optional[float] = None
    p: Optional[float] = None
    k: Optional[float] = None
    ph: Optional[float] = None
    waterAvailableKl: Optional[float] = None
    fertilizerAvailableKg: Optional[float] = None
    budgetInr: Optional[float] = None
    crops: Optional[List[FieldCropItem]] = None
    activePlanId: Optional[str] = None
    activeStrategy: Optional[str] = None


class FieldResponse(BaseModel):
    id: str
    userId: str
    name: str
    areaAcres: float
    soilType: str
    location: str
    n: float
    p: float
    k: float
    ph: float
    waterAvailableKl: float
    fertilizerAvailableKg: float
    budgetInr: float
    crops: List[FieldCropItem]
    activePlanId: Optional[str] = None
    activeStrategy: Optional[str] = None
    createdAt: str
