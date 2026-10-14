"""
SQLAlchemy models for Notifications and User Notification Preferences.
"""

from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime, Text
from backend.app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(64), primary_key=True, index=True, default=lambda: f"notif-{uuid.uuid4().hex[:10]}")
    user_id = Column(String(64), index=True, nullable=False)
    title = Column(String(256), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(32), nullable=False)  # "crop_reminder", "weather_alert", "calendar_event", "system"
    severity = Column(String(32), default="info")  # "info", "warning", "critical", "success"
    read = Column(Boolean, default=False, nullable=False)
    dismissed = Column(Boolean, default=False, nullable=False)
    field_id = Column(String(64), nullable=True)
    field_name = Column(String(128), nullable=True)
    crop_name = Column(String(128), nullable=True)
    link_url = Column(String(256), nullable=True)
    dedup_key = Column(String(128), index=True, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(String(64), primary_key=True, index=True, default=lambda: f"pref-{uuid.uuid4().hex[:10]}")
    user_id = Column(String(64), unique=True, index=True, nullable=False)
    email_notifications = Column(Boolean, default=True, nullable=False)
    push_notifications = Column(Boolean, default=True, nullable=False)
    crop_reminders = Column(Boolean, default=True, nullable=False)
    weather_alerts = Column(Boolean, default=True, nullable=False)
    reminder_days_before = Column(Integer, default=2, nullable=False)
    heavy_rain_threshold_mm = Column(Float, default=35.0, nullable=False)
    extreme_heat_threshold_c = Column(Float, default=36.0, nullable=False)
    dry_spell_days_threshold = Column(Integer, default=5, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
