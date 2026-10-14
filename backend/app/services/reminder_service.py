"""
Crop Reminder Service for Agricultural Calendar Events and Planned Crops.
Evaluates upcoming sowing, harvest, irrigation, and fertilizer windows
and generates deduplicated in-app notifications.
"""

from datetime import datetime, date, timezone
from typing import List, Dict, Any, Optional
import json
from sqlalchemy.orm import Session
from backend.app.models.calendar_event import CalendarEvent
from backend.app.models.field import Field


def evaluate_crop_reminders_for_user(
    db: Session,
    user_id: str,
    reminder_days_before: int = 2,
    eval_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Evaluates saved calendar events and field crop plans for upcoming agricultural milestones.
    Returns list of notification payloads with deterministic deduplication keys.
    """
    current_date = eval_date or datetime.now(timezone.utc).date()
    reminders: List[Dict[str, Any]] = []

    # 1. Evaluate user's Calendar Events
    events = db.query(CalendarEvent).filter(CalendarEvent.user_id == user_id).all()
    for ev in events:
        try:
            # month is 0-based from frontend (Jan=0, Oct=9, Nov=10)
            ev_date = date(ev.year, ev.month + 1, ev.day)
        except ValueError:
            continue

        # Skip already completed events
        if getattr(ev, "completed", False):
            continue

        days_until = (ev_date - current_date).days

        # Trigger if due today or within configured reminder days
        if 0 <= days_until <= reminder_days_before:
            time_label = "today" if days_until == 0 else f"in {days_until} day{'s' if days_until > 1 else ''}"
            icon = {
                "sowing": "🌱",
                "harvest": "✂️",
                "irrigation": "💧",
                "fertilizer": "✨",
            }.get(ev.type, "📌")

            stage_name = ev.type.capitalize()
            title = f"{icon} {stage_name} Reminder: {ev.crop} ({time_label})"
            message = (
                f"{ev.title} is scheduled for {ev_date.strftime('%b %d, %Y')} "
                f"({time_label}). {ev.instructions or ''}"
            ).strip()

            severity = "warning" if days_until <= 1 and ev.type in ("sowing", "harvest") else "info"

            # Deterministic dedup key based on event ID and due date
            dedup_key = f"crop_reminder:{ev.id}:{ev.type}:{ev_date.isoformat()}"

            reminders.append({
                "type": "crop_reminder",
                "severity": severity,
                "title": title,
                "message": message,
                "field_id": ev.field_id,
                "field_name": ev.field_name or "Farm Plot",
                "crop_name": ev.crop,
                "link_url": "/dashboard/calendar",
                "dedup_key": dedup_key,
                "metadata": {
                    "event_id": ev.id,
                    "event_type": ev.type,
                    "due_date": ev_date.isoformat(),
                    "days_until": days_until,
                },
            })

    # 2. Evaluate Field Planned Crops (from fields table)
    user_fields = db.query(Field).filter(Field.user_id == user_id).all()
    for f in user_fields:
        if not f.crops_json:
            continue
        try:
            crops_list = json.loads(f.crops_json)
        except Exception:
            crops_list = []

        for c in crops_list:
            c_name = c.get("name", "Crop")
            sow_window = c.get("sow", "")
            # If a field has a planned crop, provide actionable guidance reminder
            if sow_window:
                # E.g. "Oct 25 – Nov 15"
                dedup_key = f"crop_reminder:field_crop:{f.id}:{c.get('cropId', c_name)}:sow_window"
                reminders.append({
                    "type": "crop_reminder",
                    "severity": "info",
                    "title": f"🌱 Sowing Window: {c_name} on {f.name}",
                    "message": (
                        f"{c_name} is scheduled for sowing in window {sow_window} on {f.name} ({c.get('acres', f.area_acres)} acres). "
                        f"Review soil preparation, seed treatment, and fertilizer schedule."
                    ),
                    "field_id": f.id,
                    "field_name": f.name,
                    "crop_name": c_name,
                    "link_url": "/dashboard/crop-advisor",
                    "dedup_key": dedup_key,
                    "metadata": {
                        "field_id": f.id,
                        "crop_id": c.get("cropId"),
                        "sowing_window": sow_window,
                        "season": c.get("season", "Rabi"),
                    },
                })

    return reminders
