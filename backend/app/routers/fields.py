"""
Farm fields router for managing field-specific land plots, soil profiles,
resource capacities, and crop plans. Single source of truth for farmer fields.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.field import Field
from backend.app.models.user import User
from backend.app.schemas.field import (
    FieldCreate,
    FieldUpdate,
    FieldResponse,
    FieldCropItem,
)
from backend.app.schemas.crop import CropItem, CropRecommendationResponse
from backend.app.ml.model_registry import registry
from backend.app.utils.security import get_current_user_id

router = APIRouter(prefix="/fields", tags=["Farm Fields"])

SOIL_NUTRIENT_DEFAULTS = {
    "black cotton": {"n": 65.0, "p": 40.0, "k": 85.0, "ph": 7.8},
    "red laterite": {"n": 45.0, "p": 25.0, "k": 40.0, "ph": 5.8},
    "alluvial": {"n": 90.0, "p": 55.0, "k": 75.0, "ph": 7.1},
    "sandy loam": {"n": 50.0, "p": 30.0, "k": 45.0, "ph": 6.5},
    "clay loam": {"n": 75.0, "p": 45.0, "k": 70.0, "ph": 7.2},
    "saline": {"n": 40.0, "p": 20.0, "k": 50.0, "ph": 8.4},
}


def get_soil_profile(soil_type: str):
    st_lower = soil_type.lower()
    for key, vals in SOIL_NUTRIENT_DEFAULTS.items():
        if key in st_lower:
            return vals
    return {"n": 80.0, "p": 45.0, "k": 70.0, "ph": 7.2}


def field_to_response(f: Field) -> FieldResponse:
    crops_list = []
    try:
        raw_crops = json.loads(f.crops_json or "[]")
        for c in raw_crops:
            crops_list.append(
                FieldCropItem(
                    cropId=c.get("cropId") or c.get("crop_id") or "crop",
                    name=c.get("name") or "Crop",
                    acres=float(c.get("acres", 0)),
                    sow=c.get("sow"),
                    season=c.get("season", "Rabi 2026-27"),
                    status=c.get("status", "in"),
                )
            )
    except Exception:
        crops_list = []

    created_str = (
        f.created_at.isoformat()
        if f.created_at
        else datetime.now(timezone.utc).isoformat()
    )

    return FieldResponse(
        id=f.id,
        userId=f.user_id,
        name=f.name,
        areaAcres=f.area_acres,
        soilType=f.soil_type,
        location=f.location,
        n=f.n,
        p=f.p,
        k=f.k,
        ph=f.ph,
        waterAvailableKl=f.water_available_kl,
        fertilizerAvailableKg=f.fertilizer_available_kg,
        budgetInr=f.budget_inr,
        crops=crops_list,
        activePlanId=f.active_plan_id,
        activeStrategy=f.active_strategy,
        createdAt=created_str,
    )


@router.get("", response_model=List[FieldResponse])
def get_user_fields(
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Lists all farm fields owned by the authenticated user."""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    fields = (
        db.query(Field)
        .filter(Field.user_id == user_id)
        .order_by(Field.created_at.asc())
        .all()
    )
    return [field_to_response(f) for f in fields]


@router.post("", response_model=FieldResponse, status_code=status.HTTP_201_CREATED)
def create_field(
    payload: FieldCreate,
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Creates a new validated field under the authenticated user."""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    clean_name = payload.name.strip()
    if not clean_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field name cannot be empty",
        )

    if payload.areaAcres <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field area must be greater than zero",
        )

    # Check for duplicate field name by this user to prevent double-clicks
    existing = (
        db.query(Field)
        .filter(Field.user_id == user_id, Field.name.ilike(clean_name))
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Field '{clean_name}' already exists on your farm",
        )

    # Soil defaults
    profile = get_soil_profile(payload.soilType)

    # Resource defaults scaled to field acreage if not explicitly provided
    water_default = (
        payload.waterAvailableKl
        if payload.waterAvailableKl is not None
        else round(payload.areaAcres * 1600.0, 1)
    )
    fert_default = (
        payload.fertilizerAvailableKg
        if payload.fertilizerAvailableKg is not None
        else round(payload.areaAcres * 100.0, 1)
    )
    budget_default = (
        payload.budgetInr
        if payload.budgetInr is not None
        else round(payload.areaAcres * 40000.0, 1)
    )

    crops_payload = []
    if payload.crops:
        crops_payload = [
            {
                "cropId": c.cropId,
                "name": c.name,
                "acres": c.acres,
                "sow": c.sow,
                "season": c.season,
                "status": c.status,
            }
            for c in payload.crops
        ]

    field_id = f"field-{uuid.uuid4().hex[:10]}"
    field = Field(
        id=field_id,
        user_id=user_id,
        name=clean_name,
        area_acres=float(payload.areaAcres),
        soil_type=payload.soilType.strip(),
        location=payload.location.strip(),
        n=profile["n"],
        p=profile["p"],
        k=profile["k"],
        ph=profile["ph"],
        water_available_kl=float(water_default),
        fertilizer_available_kg=float(fert_default),
        budget_inr=float(budget_default),
        crops_json=json.dumps(crops_payload),
        created_at=datetime.now(timezone.utc),
    )

    db.add(field)
    db.commit()
    db.refresh(field)

    return field_to_response(field)


@router.get("/{field_id}", response_model=FieldResponse)
def get_field(
    field_id: str,
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Retrieves a single field. Enforces ownership."""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    field = db.query(Field).filter(Field.id == field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    if field.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied: field belongs to another user")
    return field_to_response(field)


@router.put("/{field_id}", response_model=FieldResponse)
@router.patch("/{field_id}", response_model=FieldResponse)
def update_field(
    field_id: str,
    payload: FieldUpdate,
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Updates a field's parameters, resources, or crops. Enforces ownership."""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    field = db.query(Field).filter(Field.id == field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    if field.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied: field belongs to another user")

    if payload.name is not None and payload.name.strip():
        # Check name collision
        clean = payload.name.strip()
        collision = (
            db.query(Field)
            .filter(Field.user_id == user_id, Field.name.ilike(clean), Field.id != field_id)
            .first()
        )
        if collision:
            raise HTTPException(status_code=409, detail=f"Another field is already named '{clean}'")
        field.name = clean

    if payload.areaAcres is not None and payload.areaAcres > 0:
        field.area_acres = payload.areaAcres
    if payload.soilType is not None and payload.soilType.strip():
        field.soil_type = payload.soilType.strip()
        profile = get_soil_profile(payload.soilType)
        field.n = profile["n"]
        field.p = profile["p"]
        field.k = profile["k"]
        field.ph = profile["ph"]
    if payload.location is not None and payload.location.strip():
        field.location = payload.location.strip()
    if payload.n is not None:
        field.n = payload.n
    if payload.p is not None:
        field.p = payload.p
    if payload.k is not None:
        field.k = payload.k
    if payload.ph is not None:
        field.ph = payload.ph
    if payload.waterAvailableKl is not None and payload.waterAvailableKl >= 0:
        field.water_available_kl = payload.waterAvailableKl
    if payload.fertilizerAvailableKg is not None and payload.fertilizerAvailableKg >= 0:
        field.fertilizer_available_kg = payload.fertilizerAvailableKg
    if payload.budgetInr is not None and payload.budgetInr >= 0:
        field.budget_inr = payload.budgetInr
    if payload.crops is not None:
        field.crops_json = json.dumps([
            {
                "cropId": c.cropId,
                "name": c.name,
                "acres": c.acres,
                "sow": c.sow,
                "season": c.season,
                "status": c.status,
            }
            for c in payload.crops
        ])
    if payload.activePlanId is not None:
        field.active_plan_id = payload.activePlanId
    if payload.activeStrategy is not None:
        field.active_strategy = payload.activeStrategy

    db.commit()
    db.refresh(field)
    return field_to_response(field)


@router.delete("/{field_id}")
def delete_field(
    field_id: str,
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Deletes a field owned by the authenticated user."""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    field = db.query(Field).filter(Field.id == field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    if field.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied: field belongs to another user")

    db.delete(field)
    db.commit()
    return {"status": "success", "message": f"Field '{field.name}' deleted"}


@router.post("/{field_id}/crops", response_model=FieldResponse)
def add_crop_to_field(
    field_id: str,
    crop: FieldCropItem,
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Adds or updates a crop on a specific field plan."""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    field = db.query(Field).filter(Field.id == field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    if field.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        current_crops = json.loads(field.crops_json or "[]")
    except Exception:
        current_crops = []

    target_crop_id = crop.cropId.strip().lower()
    target_name = crop.name.strip().lower()

    if crop.status == "out":
        # Remove from active field crops
        current_crops = [
            c for c in current_crops
            if (c.get("cropId") or c.get("crop_id") or "").strip().lower() != target_crop_id
            and c.get("name", "").strip().lower() != target_name
        ]
    else:
        # Add or update in active field crops
        updated = False
        for c in current_crops:
            c_id = (c.get("cropId") or c.get("crop_id") or "").strip().lower()
            c_name = c.get("name", "").strip().lower()
            if c_id == target_crop_id or c_name == target_name:
                c["cropId"] = crop.cropId.strip()
                c["name"] = crop.name.strip()
                c["acres"] = float(crop.acres)
                c["sow"] = crop.sow or c.get("sow")
                c["season"] = crop.season or c.get("season")
                c["status"] = "in"
                updated = True
                break
        if not updated:
            current_crops.append({
                "cropId": crop.cropId.strip(),
                "name": crop.name.strip(),
                "acres": float(crop.acres),
                "sow": crop.sow,
                "season": crop.season,
                "status": "in",
            })

    field.crops_json = json.dumps(current_crops)
    db.commit()
    db.refresh(field)
    return field_to_response(field)


@router.delete("/{field_id}/crops/{crop_id}", response_model=FieldResponse)
def remove_crop_from_field(
    field_id: str,
    crop_id: str,
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Removes a crop assignment from a specific field plan."""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    field = db.query(Field).filter(Field.id == field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    if field.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        current_crops = json.loads(field.crops_json or "[]")
    except Exception:
        current_crops = []

    clean_id = crop_id.strip().lower()
    current_crops = [
        c for c in current_crops
        if (c.get("cropId") or c.get("crop_id") or "").strip().lower() != clean_id
        and c.get("name", "").strip().lower() != clean_id
    ]

    field.crops_json = json.dumps(current_crops)
    db.commit()
    db.refresh(field)
    return field_to_response(field)


@router.get("/{field_id}/recommendations", response_model=CropRecommendationResponse)
def get_field_recommendations(
    field_id: str,
    season: str = Query("Rabi", description="Season to recommend for"),
    top_k: int = Query(20, description="Maximum crops to return"),
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Generates AI crop recommendations specifically tailored to the field's soil chemistry and conditions."""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    field = db.query(Field).filter(Field.id == field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    if field.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    classifier = registry.get_crop_classifier()
    recommendations = classifier.predict_suitability(
        n=field.n,
        p=field.p,
        k=field.k,
        ph=field.ph,
        temperature=22.0 if season.lower() == "rabi" else 28.0,
        humidity=60.0 if season.lower() == "rabi" else 75.0,
        rainfall=420.0 if season.lower() == "rabi" else 850.0,
        season=season,
        top_k=top_k,
    )

    crop_items = []
    for idx, rec in enumerate(recommendations, start=1):
        item = CropItem(
            id=idx,
            crop_id=rec["crop_id"],
            emoji=rec["emoji"],
            title=rec["title"],
            suitability=rec["suitability"],
            status=rec["status"],
            yield_str=rec["yield"],
            sow=rec["sow"],
            profit=rec["profit"],
            water=rec["water"],
            variant=rec["variant"],
            expected_yield_q=rec["expected_yield_q"],
            expected_profit=rec["expected_profit"],
            water_requirement_kl=rec["water_requirement_kl"],
            fertilizer_kg=rec["fertilizer_kg"],
            cost_per_acre=rec["cost_per_acre"],
            market_price_per_q=rec["market_price_per_q"],
            key_advantages=rec["key_advantages"],
            irrigation_advice=rec["irrigation_advice"],
        )
        crop_items.append(item)

    return CropRecommendationResponse(
        count=len(crop_items),
        crops=crop_items,
        field={
            "id": field.id,
            "name": field.name,
            "soilType": field.soil_type,
            "location": field.location,
            "areaAcres": field.area_acres,
        },
    )
