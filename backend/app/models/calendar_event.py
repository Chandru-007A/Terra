"""
SQLAlchemy model for Crop Calendar Events.
"""

from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean
from backend.app.database import Base


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(String(64), primary_key=True, index=True, default=lambda: f"evt-{uuid.uuid4().hex[:10]}")
    user_id = Column(String(64), index=True, nullable=False)
    field_id = Column(String(64), nullable=True)
    field_name = Column(String(128), nullable=True)
    crop = Column(String(128), nullable=False)
    emoji = Column(String(16), default="🌱")
    title = Column(String(256), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)  # 0-based to align with frontend
    day = Column(Integer, nullable=False)
    type = Column(String(32), nullable=False)  # "sowing", "irrigation", "fertilizer", "harvest", "custom"
    instructions = Column(Text, nullable=True)
    badge = Column(String(128), nullable=True)
    color = Column(String(64), nullable=True)
    completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(32), default="pending", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

