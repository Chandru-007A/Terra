"""
API Router for Farm Calendar Events.
Provides persistent storage, querying, creation, and deletion of agricultural events
with automatic integration into the crop reminder system.
"""

from datetime import datetime, timezone
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.calendar_event import CalendarEvent
from backend.app.models.field import Field
from backend.app.models.notification import Notification
from backend.app.schemas.calendar import CalendarEventCreate, CalendarEventUpdate, CalendarEventResponse
from backend.app.routers.auth import get_current_user_id

router = APIRouter(prefix="/calendar", tags=["Calendar"])

# Standard baseline events for Indian Rabi season
DEFAULT_SEED_EVENTS = [
    {
        "crop": "Mustard", "emoji": "🌼",
        "title": "Sowing Window & Seed Treatment",
        "year": 2026, "month": 9, "day": 15,
        "type": "sowing",
        "instructions": "Treat seeds with Trichoderma (5g/kg) and sow at 3-4 cm depth.",
        "badge": "Mustard · 1 acre", "color": "bg-amber-500",
    },
    {
        "crop": "Chickpea", "emoji": "🫘",
        "title": "Rhizobium Inoculation & Sowing",
        "year": 2026, "month": 9, "day": 20,
        "type": "sowing",
        "instructions": "Inoculate with Rhizobium culture; sow in furrows spaced 30 cm.",
        "badge": "Chickpea · 3 acres", "color": "bg-emerald-600",
    },
    {
        "crop": "Onion", "emoji": "🧅",
        "title": "Transplanting Seedlings to Raised Beds",
        "year": 2026, "month": 9, "day": 28,
        "type": "sowing",
        "instructions": "Transplant 6-8 week sturdy seedlings on raised bed furrows.",
        "badge": "Onion · 3 acres", "color": "bg-rose-500",
    },
    {
        "crop": "Wheat", "emoji": "🌾",
        "title": "Main Rabi Wheat Sowing",
        "year": 2026, "month": 10, "day": 5,
        "type": "sowing",
        "instructions": "Line sowing with seed-cum-fertilizer drill at 100 kg/ha rate.",
        "badge": "Wheat · 3 acres", "color": "bg-yellow-600",
    },
    {
        "crop": "Mustard", "emoji": "🌼",
        "title": "Rosette Stage First Irrigation",
        "year": 2026, "month": 10, "day": 14,
        "type": "irrigation",
        "instructions": "Provide first protective irrigation at 30 days after sowing.",
        "badge": "Mustard · Critical Stage", "color": "bg-cyan-500",
    },
    {
        "crop": "Wheat", "emoji": "🌾",
        "title": "Crown Root Initiation (CRI) Irrigation",
        "year": 2026, "month": 10, "day": 26,
        "type": "irrigation",
        "instructions": "Most critical watering window (21 DAS); moisture stress here drops yield 30%.",
        "badge": "Wheat · Critical Stage", "color": "bg-cyan-500",
    },
    {
        "crop": "Onion", "emoji": "🧅",
        "title": "First Nitrogen Top-Dressing",
        "year": 2026, "month": 10, "day": 28,
        "type": "fertilizer",
        "instructions": "Apply 25 kg/acre Urea before scheduled micro-irrigation.",
        "badge": "Onion · NPK Split", "color": "bg-purple-500",
    },
    {
        "crop": "Chickpea", "emoji": "🫘",
        "title": "Branching & Pre-Flowering Light Watering",
        "year": 2026, "month": 11, "day": 8,
        "type": "irrigation",
        "instructions": "Single supplementary light irrigation; avoid flooding roots.",
        "badge": "Chickpea · Low Water", "color": "bg-cyan-500",
    },
    {
        "crop": "Mustard", "emoji": "🌼",
        "title": "Siliqua Maturity & Harvest Window",
        "year": 2027, "month": 0, "day": 25,
        "type": "harvest",
        "instructions": "Harvest early morning when 75% pods turn yellowish-brown to avoid shattering.",
        "badge": "Mustard · 7 q/acre", "color": "bg-green-600",
    },
]


def event_to_response(e: CalendarEvent) -> CalendarEventResponse:
    return CalendarEventResponse(
        id=e.id,
        userId=e.user_id,
        crop=e.crop,
        emoji=e.emoji or "🌱",
        title=e.title,
        year=e.year,
        month=e.month,
        day=e.day,
        type=e.type,
        instructions=e.instructions or "",
        fieldId=e.field_id,
        fieldName=e.field_name,
        badge=e.badge,
        color=e.color,
        completed=bool(getattr(e, "completed", False)),
        completedAt=e.completed_at.isoformat() if getattr(e, "completed_at", None) else None,
        status=getattr(e, "status", "completed" if getattr(e, "completed", False) else "pending") or "pending",
        createdAt=e.created_at.isoformat() if e.created_at else "",
    )


@router.get("/events", response_model=List[CalendarEventResponse])
def get_calendar_events(
    field_id: Optional[str] = None,
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Retrieves all calendar events for the user, optionally filtered by field. Seeds defaults on first access."""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    query = db.query(CalendarEvent).filter(CalendarEvent.user_id == user_id)

    # Initial check if user has any events
    user_event_count = query.count()

    if user_event_count == 0:
        # Seed defaults for user
        user_field = db.query(Field).filter(Field.user_id == user_id).first()
        f_id = user_field.id if user_field else None
        f_name = user_field.name if user_field else "North Field"

        for se in DEFAULT_SEED_EVENTS:
            ev = CalendarEvent(
                id=f"evt-{uuid.uuid4().hex[:10]}",
                user_id=user_id,
                field_id=f_id,
                field_name=f_name,
                crop=se["crop"],
                emoji=se["emoji"],
                title=se["title"],
                year=se["year"],
                month=se["month"],
                day=se["day"],
                type=se["type"],
                instructions=se["instructions"],
                badge=se["badge"],
                color=se["color"],
                completed=False,
                status="pending",
                created_at=datetime.now(timezone.utc),
            )
            db.add(ev)
        db.commit()
        query = db.query(CalendarEvent).filter(CalendarEvent.user_id == user_id)

    if field_id and field_id != "all":
        field_obj = db.query(Field).filter(Field.id == field_id, Field.user_id == user_id).first()
        if field_obj:
            query = query.filter(
                (CalendarEvent.field_id == field_id) |
                (CalendarEvent.field_name.ilike(field_obj.name))
            )
        else:
            query = query.filter(CalendarEvent.field_id == field_id)

    events = query.order_by(CalendarEvent.year, CalendarEvent.month, CalendarEvent.day).all()
    return [event_to_response(e) for e in events]


@router.post("/events", response_model=CalendarEventResponse, status_code=status.HTTP_201_CREATED)
def create_calendar_event(
    payload: CalendarEventCreate,
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Creates a new calendar event for the user and associates it with the field."""
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    field_name = payload.fieldName
    if payload.fieldId and not field_name:
        f = db.query(Field).filter(Field.id == payload.fieldId, Field.user_id == user_id).first()
        if f:
            field_name = f.name

    ev_id = f"evt-{uuid.uuid4().hex[:10]}"
    is_completed = bool(payload.completed)
    event = CalendarEvent(
        id=ev_id,
        user_id=user_id,
        field_id=payload.fieldId,
        field_name=field_name or "Farm Plot",
        crop=payload.crop.strip(),
        emoji=payload.emoji or "🌱",
        title=payload.title.strip(),
        year=payload.year,
        month=payload.month,
        day=payload.day,
        type=payload.type,
        instructions=payload.instructions or "",
        badge=payload.badge or f"{payload.crop.strip()} · Event",
        color=payload.color or "bg-primary",
        completed=is_completed,
        completed_at=datetime.now(timezone.utc) if is_completed else None,
        status="completed" if is_completed else (payload.status or "pending"),
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    return event_to_response(event)


@router.patch("/events/{event_id}/toggle", response_model=CalendarEventResponse)
def toggle_calendar_event(
    event_id: str,
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Toggles completion status for a calendar event."""
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    event.completed = not bool(event.completed)
    if event.completed:
        event.completed_at = datetime.now(timezone.utc)
        event.status = "completed"
    else:
        event.completed_at = None
        event.status = "pending"

    db.commit()
    db.refresh(event)
    return event_to_response(event)


@router.patch("/events/{event_id}", response_model=CalendarEventResponse)
def update_calendar_event(
    event_id: str,
    payload: CalendarEventUpdate,
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Updates an existing calendar event (e.g. status, dates, completion)."""
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    update_data = payload.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        if field_name == "completed":
            event.completed = bool(value)
            if event.completed and not event.completed_at:
                event.completed_at = datetime.now(timezone.utc)
                event.status = "completed"
            elif not event.completed:
                event.completed_at = None
                event.status = "pending"
        elif field_name == "fieldId":
            event.field_id = value
        elif field_name == "fieldName":
            event.field_name = value
        elif hasattr(event, field_name):
            setattr(event, field_name, value)

    db.commit()
    db.refresh(event)
    return event_to_response(event)


@router.delete("/events/{event_id}")
def delete_calendar_event(
    event_id: str,
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Deletes a calendar event."""
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    db.delete(event)
    # Also clean up unread notifications linked to this event
    db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.dedup_key.like(f"crop_reminder:{event_id}:%")
    ).delete(synchronize_session=False)

    db.commit()
    return {"status": "success", "message": f"Event '{event_id}' deleted"}

