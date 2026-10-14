"""
SQLAlchemy Field model representing individual farmer farm fields/plots.
Single source of truth for field-specific soil, area, resources, and crops.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey
from backend.app.database import Base


class Field(Base):
    __tablename__ = "fields"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id"), index=True, nullable=False)
    name = Column(String(128), nullable=False)
    area_acres = Column(Float, nullable=False)
    soil_type = Column(String(128), nullable=False)
    location = Column(String(128), nullable=False)

    # Soil nutrient values (N, P, K, pH)
    n = Column(Float, default=80.0, nullable=False)
    p = Column(Float, default=45.0, nullable=False)
    k = Column(Float, default=70.0, nullable=False)
    ph = Column(Float, default=7.2, nullable=False)

    # Resource pools scoped to this field
    water_available_kl = Column(Float, default=16000.0, nullable=False)
    fertilizer_available_kg = Column(Float, default=1000.0, nullable=False)
    budget_inr = Column(Float, default=400000.0, nullable=False)

    # JSON-encoded array of crop plans on this field: [{"crop_id": "...", "name": "...", "acres": 2.0, "season": "Rabi 2026-27"}]
    crops_json = Column(Text, default="[]", nullable=False)

    # Active optimization plan tracking
    active_plan_id = Column(String(64), nullable=True)
    active_strategy = Column(String(64), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
