"""
SQLAlchemy Plan model for historical and active farm resource allocation plans.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from backend.app.database import Base


class Plan(Base):
    __tablename__ = "plans"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id"), index=True, nullable=False)
    field_id = Column(String(64), ForeignKey("fields.id"), index=True, nullable=True)
    field_name = Column(String(128), nullable=True)
    season = Column(String(64), nullable=False)
    strategy = Column(String(64), nullable=False)
    crops_json = Column(Text, nullable=False)  # JSON-encoded array of {name, acres}
    profit = Column(String(64), nullable=False)  # Formatted string like "₹4.04L"
    water_saved = Column(String(64), nullable=False)  # Formatted string like "27%"
    fertilizer_saved = Column(String(64), nullable=False)  # Formatted string like "22%"
    status = Column(String(32), nullable=False, default="Current")  # "Current" or "Completed"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
