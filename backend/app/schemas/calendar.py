"""
Pydantic schemas for Calendar Events.
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict


class CalendarEventCreate(BaseModel):
    crop: str
    emoji: Optional[str] = "🌱"
    title: str
    year: int
    month: int
    day: int
    type: str  # "sowing", "irrigation", "fertilizer", "harvest", "custom"
    instructions: Optional[str] = None
    fieldId: Optional[str] = None
    fieldName: Optional[str] = None
    badge: Optional[str] = None
    color: Optional[str] = None
    completed: Optional[bool] = False
    status: Optional[str] = "pending"


class CalendarEventUpdate(BaseModel):
    crop: Optional[str] = None
    emoji: Optional[str] = None
    title: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    type: Optional[str] = None
    instructions: Optional[str] = None
    fieldId: Optional[str] = None
    fieldName: Optional[str] = None
    badge: Optional[str] = None
    color: Optional[str] = None
    completed: Optional[bool] = None
    status: Optional[str] = None


class CalendarEventResponse(BaseModel):
    id: str
    userId: str
    crop: str
    emoji: str
    title: str
    year: int
    month: int
    day: int
    type: str
    instructions: str
    fieldId: Optional[str] = None
    fieldName: Optional[str] = None
    badge: Optional[str] = None
    color: Optional[str] = None
    completed: bool = False
    completedAt: Optional[str] = None
    status: str = "pending"
    createdAt: str

    model_config = ConfigDict(populate_by_name=True)

