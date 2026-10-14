"""
SQLAlchemy User model for farmers and agricultural planners.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime
from backend.app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    village = Column(String(128), nullable=True)
    district = Column(String(128), nullable=True)
    farm_size_acres = Column(Float, nullable=True, default=10.0)
    soil_type = Column(String(128), nullable=True, default="Black cotton soil")
    language = Column(String(64), nullable=True, default="English")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
