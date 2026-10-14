"""
API Router for Notifications, Weather Alerts, and Farmer Reminders.
Handles in-app notification storage, deduplication, read/unread states, and user preferences.
"""

from datetime import datetime, timezone
import json
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.notification import Notification, NotificationPreference
from backend.app.models.field import Field
from backend.app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationPreferenceUpdate,
    NotificationPreferenceResponse,
    WeatherStatusResponse,
)
from backend.app.routers.auth import get_current_user_id
from backend.app.services.weather_service import (
    evaluate_weather_alerts_for_field,
    get_live_forecast,
)
from backend.app.services.reminder_service import evaluate_crop_reminders_for_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def get_or_create_preferences(db: Session, user_id: str) -> NotificationPreference:
    """Retrieves or creates default notification preferences for a user."""
    pref = db.query(NotificationPreference).filter(NotificationPreference.user_id == user_id).first()
    if not pref:
        pref = NotificationPreference(
            user_id=user_id,
            email_notifications=True,
            push_notifications=True,
            crop_reminders=True,
            weather_alerts=True,
            reminder_days_before=2,
            heavy_rain_threshold_mm=35.0,
            extreme_heat_threshold_c=36.0,
            dry_spell_days_threshold=5,
        )
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref


def run_notification_sync(db: Session, user_id: str) -> int:
    """
    Evaluates both crop reminders and live weather alerts against user preferences.
    Inserts newly discovered alerts with deterministic deduplication keys.
    Returns count of new notifications created.
    """
    pref = get_or_create_preferences(db, user_id)
    new_count = 0
    now = datetime.now(timezone.utc)

    # 1. Evaluate Crop Reminders if enabled
    if pref.crop_reminders:
        candidate_reminders = evaluate_crop_reminders_for_user(
            db, user_id, reminder_days_before=pref.reminder_days_before
        )
        for cand in candidate_reminders:
            dedup = cand.get("dedup_key")
            existing = (
                db.query(Notification)
                .filter(Notification.user_id == user_id, Notification.dedup_key == dedup)
                .first()
            )
            if not existing:
                notif = Notification(
                    user_id=user_id,
                    title=cand["title"],
                    message=cand["message"],
                    type=cand["type"],
                    severity=cand.get("severity", "info"),
                    read=False,
                    dismissed=False,
                    field_id=cand.get("field_id"),
                    field_name=cand.get("field_name"),
                    crop_name=cand.get("crop_name"),
                    link_url=cand.get("link_url"),
                    dedup_key=dedup,
                    metadata_json=json.dumps(cand.get("metadata", {})),
                    created_at=now,
                )
                db.add(notif)
                new_count += 1

    # 2. Evaluate Weather Alerts if enabled
    if pref.weather_alerts:
        user_fields = db.query(Field).filter(Field.user_id == user_id).all()
        for f in user_fields:
            if not f.location:
                continue
            try:
                crops_list = json.loads(f.crops_json or "[]")
            except Exception:
                crops_list = []

            field_alerts = evaluate_weather_alerts_for_field(
                field_id=f.id,
                field_name=f.name,
                location=f.location,
                crops=crops_list,
                heavy_rain_threshold=pref.heavy_rain_threshold_mm,
                extreme_heat_threshold=pref.extreme_heat_threshold_c,
                dry_spell_days=pref.dry_spell_days_threshold,
            )
            for alert in field_alerts:
                dedup = alert.get("dedup_key")
                existing = (
                    db.query(Notification)
                    .filter(Notification.user_id == user_id, Notification.dedup_key == dedup)
                    .first()
                )
                if not existing:
                    notif = Notification(
                        user_id=user_id,
                        title=alert["title"],
                        message=alert["message"],
                        type=alert["type"],
                        severity=alert.get("severity", "warning"),
                        read=False,
                        dismissed=False,
                        field_id=f.id,
                        field_name=f.name,
                        crop_name=alert.get("crop_name"),
                        link_url=alert.get("link_url"),
                        dedup_key=dedup,
                        metadata_json=json.dumps(alert.get("metadata", {})),
                        created_at=now,
                    )
                    db.add(notif)
                    new_count += 1

    if new_count > 0:
        db.commit()

    return new_count


def notif_to_response(n: Notification) -> NotificationResponse:
    meta = None
    if n.metadata_json:
        try:
            meta = json.loads(n.metadata_json)
        except Exception:
            pass
    return NotificationResponse(
        id=n.id,
        userId=n.user_id,
        title=n.title,
        message=n.message,
        type=n.type,
        severity=n.severity,
        read=n.read,
        dismissed=n.dismissed,
        fieldId=n.field_id,
        fieldName=n.field_name,
        cropName=n.crop_name,
        linkUrl=n.link_url,
        dedupKey=n.dedup_key,
        metadata=meta,
        createdAt=n.created_at.isoformat() if n.created_at else "",
    )


@router.get("", response_model=NotificationListResponse)
def get_notifications(
    type_filter: Optional[str] = Query(None, description="Filter by type: 'crop_reminder', 'weather_alert'"),
    unread_only: bool = Query(False, description="Filter unread only"),
    auto_sync: bool = Query(True, description="Run evaluation sync on fetch"),
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Retrieves the user's active notifications.
    Automatically evaluates upcoming crop reminders and live weather alerts.
    """
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view notifications",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if auto_sync:
        try:
            run_notification_sync(db, user_id)
        except Exception as e:
            logger.error(f"Error during notification sync: {e}")

    query = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.dismissed == False)
    )

    if type_filter:
        query = query.filter(Notification.type == type_filter)
    if unread_only:
        query = query.filter(Notification.read == False)

    notifications = query.order_by(Notification.created_at.desc()).all()

    unread_count = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.dismissed == False, Notification.read == False)
        .count()
    )

    now = datetime.now(timezone.utc)
    return NotificationListResponse(
        notifications=[notif_to_response(n) for n in notifications],
        unreadCount=unread_count,
        totalCount=len(notifications),
        lastChecked=now.isoformat(),
    )


@router.post("/sync")
def sync_notifications(
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Explicitly triggers evaluation of crop reminders and weather alerts."""
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    created = run_notification_sync(db, user_id)
    unread = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.dismissed == False, Notification.read == False)
        .count()
    )
    return {
        "status": "success",
        "newNotificationsCount": created,
        "unreadCount": unread,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_as_read(
    notification_id: str,
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Marks a single notification as read."""
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notif.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    notif.read = True
    db.commit()
    db.refresh(notif)
    return notif_to_response(notif)


@router.post("/mark-all-read")
def mark_all_notifications_as_read(
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Marks all unread notifications for the user as read."""
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    count = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.read == False)
        .update({"read": True})
    )
    db.commit()
    return {"status": "success", "markedReadCount": count}


@router.delete("/{notification_id}")
def dismiss_notification(
    notification_id: str,
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Dismisses a notification from the user's active view."""
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notif.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    notif.dismissed = True
    db.commit()
    return {"status": "success", "message": f"Notification '{notification_id}' dismissed"}


@router.delete("/dismiss-all")
def dismiss_all_notifications(
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Dismisses all active notifications for the current user."""
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    count = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.dismissed == False)
        .update({"dismissed": True})
    )
    db.commit()
    return {"status": "success", "dismissedCount": count}


@router.get("/preferences", response_model=NotificationPreferenceResponse)
def get_preferences(
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Retrieves user's notification preferences."""
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    pref = get_or_create_preferences(db, user_id)
    return NotificationPreferenceResponse(
        emailNotifications=pref.email_notifications,
        pushNotifications=pref.push_notifications,
        cropReminders=pref.crop_reminders,
        weatherAlerts=pref.weather_alerts,
        reminderDaysBefore=pref.reminder_days_before,
        heavyRainThresholdMm=pref.heavy_rain_threshold_mm,
        extremeHeatThresholdC=pref.extreme_heat_threshold_c,
        drySpellDaysThreshold=pref.dry_spell_days_threshold,
    )


@router.put("/preferences", response_model=NotificationPreferenceResponse)
@router.patch("/preferences", response_model=NotificationPreferenceResponse)
def update_preferences(
    payload: NotificationPreferenceUpdate,
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Updates user's notification preferences."""
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    pref = get_or_create_preferences(db, user_id)

    if payload.emailNotifications is not None:
        pref.email_notifications = payload.emailNotifications
    if payload.pushNotifications is not None:
        pref.push_notifications = payload.pushNotifications
    if payload.cropReminders is not None:
        pref.crop_reminders = payload.cropReminders
    if payload.weatherAlerts is not None:
        pref.weather_alerts = payload.weatherAlerts
    if payload.reminderDaysBefore is not None:
        pref.reminder_days_before = max(0, min(14, payload.reminderDaysBefore))
    if payload.heavyRainThresholdMm is not None:
        pref.heavy_rain_threshold_mm = max(5.0, payload.heavyRainThresholdMm)
    if payload.extremeHeatThresholdC is not None:
        pref.extreme_heat_threshold_c = max(20.0, payload.extremeHeatThresholdC)
    if payload.drySpellDaysThreshold is not None:
        pref.dry_spell_days_threshold = max(2, payload.drySpellDaysThreshold)

    db.commit()
    db.refresh(pref)
    return NotificationPreferenceResponse(
        emailNotifications=pref.email_notifications,
        pushNotifications=pref.push_notifications,
        cropReminders=pref.crop_reminders,
        weatherAlerts=pref.weather_alerts,
        reminderDaysBefore=pref.reminder_days_before,
        heavyRainThresholdMm=pref.heavy_rain_threshold_mm,
        extremeHeatThresholdC=pref.extreme_heat_threshold_c,
        drySpellDaysThreshold=pref.dry_spell_days_threshold,
    )


@router.get("/weather-status", response_model=WeatherStatusResponse)
def get_weather_status(
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Returns status of live weather provider monitoring user fields."""
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    fields = db.query(Field).filter(Field.user_id == user_id).all()
    locations = list({f.location for f in fields if f.location})

    active_alerts = (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.type == "weather_alert",
            Notification.dismissed == False,
        )
        .count()
    )

    now = datetime.now(timezone.utc)
    return WeatherStatusResponse(
        provider="Open-Meteo Live Forecast API (WMO compliant)",
        status="active" if locations else "no_locations_configured",
        lastChecked=now.isoformat(),
        monitoredLocations=locations,
        activeAlertsCount=active_alerts,
    )
