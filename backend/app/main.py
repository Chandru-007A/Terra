"""
FastAPI application entry point for TERRA
AI-Based Crop and Agricultural Resource Optimization System.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text
from backend.app.config import settings
from backend.app.database import engine, Base, SessionLocal
from backend.app.models.user import User
from backend.app.models.plan import Plan
from backend.app.models.field import Field
from backend.app.utils.security import hash_password
from backend.app.ml.model_registry import registry

from backend.app.routers.auth import router as auth_router
from backend.app.routers.recommend import router as recommend_router
from backend.app.routers.predict import router as predict_router
from backend.app.routers.optimize import router as optimize_router
from backend.app.routers.history import router as history_router
from backend.app.routers.data import router as data_router
from backend.app.routers.fields import router as fields_router
from backend.app.routers.notifications import router as notifications_router
from backend.app.routers.calendar import router as calendar_router


def seed_demo_data():
    """Initializes tables and seeds default demo farmer and baseline plans."""
    Base.metadata.create_all(bind=engine)

    # Migrate columns if existing sqlite table is missing field_id or field_name
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE plans ADD COLUMN field_id VARCHAR(64)"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE plans ADD COLUMN field_name VARCHAR(128)"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE calendar_events ADD COLUMN completed BOOLEAN DEFAULT 0"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE calendar_events ADD COLUMN completed_at DATETIME"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE calendar_events ADD COLUMN status VARCHAR(32) DEFAULT 'pending'"))
            conn.commit()
        except Exception:
            pass


    db = SessionLocal()
    try:
        demo_user = db.query(User).filter(User.id == "demo-user-1").first()
        if not demo_user:
            demo_user = User(
                id="demo-user-1",
                name="Ramesh Patil",
                email="ramesh.patil@gmail.com",
                password_hash=hash_password("terra123"),
                village="Nashik",
                district="Maharashtra",
                farm_size_acres=10.0,
                soil_type="Black cotton soil",
                language="English",
                created_at=datetime.now(timezone.utc)
            )
            db.add(demo_user)
            db.commit()
    finally:
        db.close()


# Ensure tables and demo user are initialized on load
seed_demo_data()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Seed database and warm ML models
    seed_demo_data()
    # Pre-train or warm ML models asynchronously
    try:
        registry.get_crop_classifier()
        registry.get_yield_regressor()
    except Exception as e:
        print(f"Warning warming models: {e}")
    yield
    # Shutdown


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Intelligent Crop Suitability Prediction & Classical SciPy Resource Optimization Engine",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(auth_router)
app.include_router(fields_router)
app.include_router(recommend_router)
app.include_router(predict_router)
app.include_router(optimize_router)
app.include_router(history_router)
app.include_router(data_router)
app.include_router(notifications_router)
app.include_router(calendar_router)


@app.get("/")
def root():
    return {
        "system": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "docs_url": "/docs",
        "endpoints": {
            "auth": "/auth/login, /auth/register, /auth/me",
            "fields": "/fields, /fields/{field_id}, /fields/{field_id}/crops, /fields/{field_id}/recommendations",
            "recommend": "/recommend/crops",
            "predict": "/predict/yield",
            "optimize": "/optimize/allocate, /optimize/strategies",
            "history": "/history/plans",
            "data": "/data/provenance, /data/benchmarks/{crop_id}, /data/climate/{district_id}, /data/evaluation/classifier, /data/evaluation/regressor"
        }
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/model-info")
def model_info():
    """
    Returns metadata about the ML models, data sources, and provenance.
    Does NOT run expensive CV evaluation — use /model-info/evaluate for that.
    """
    from backend.app.data.crop_database import ECONOMIC_DATA_PROVENANCE, CROP_DATA_VERSION
    from backend.app.data.weather_data import WEATHER_DATA_PROVENANCE

    classifier = registry.get_crop_classifier()
    regressor = registry.get_yield_regressor()

    return {
        "models": {
            "crop_classifier": classifier.get_model_info(),
            "yield_regressor": regressor.get_model_info(),
        },
        "data_provenance": {
            "economic_data": ECONOMIC_DATA_PROVENANCE,
            "weather_data": WEATHER_DATA_PROVENANCE,
            "crop_data_version": CROP_DATA_VERSION,
        },
        "disclaimer": (
            "All ML models are trained on SYNTHETIC data derived from ICAR/FAO "
            "agronomic principles. Predictions are indicative only and have NOT been "
            "validated against real farm records. Weather data sourced from NASA POWER "
            "Climatology API (CC BY 4.0). Economic data reflects GoI MSP 2024-25 — "
            "do not treat as current live market prices."
        ),
    }

