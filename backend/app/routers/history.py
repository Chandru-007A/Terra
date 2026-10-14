"""
Plan history router for saving, querying, and managing seasonal farm plans.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.plan import Plan
from backend.app.models.user import User
from backend.app.schemas.plan import PlanCreate, PlanResponse, PlanCrop
from backend.app.utils.security import get_current_user_id

from backend.app.models.field import Field

router = APIRouter(prefix="/history", tags=["Plan History"])


def plan_to_response(p: Plan) -> PlanResponse:
    crops_list = []
    try:
        raw = json.loads(p.crops_json)
        crops_list = [PlanCrop(name=c.get("name", ""), acres=float(c.get("acres", 0))) for c in raw]
    except Exception:
        crops_list = []

    created_str = p.created_at.isoformat() if p.created_at else datetime.now(timezone.utc).isoformat()
    return PlanResponse(
        id=p.id,
        fieldId=getattr(p, "field_id", None),
        fieldName=getattr(p, "field_name", None),
        season=p.season,
        strategy=p.strategy,
        crops=crops_list,
        profit=p.profit,
        waterSaved=p.water_saved,
        fertilizerSaved=p.fertilizer_saved,
        status=p.status,
        createdAt=created_str,
    )


def seed_sample_plans_for_user(user_id: str, db: Session) -> List[Plan]:
    """Seeds the initial sample plans if demo user has no plans."""
    sample_plans = [
        Plan(
            id=f"plan-1-{uuid.uuid4().hex[:6]}",
            user_id=user_id,
            field_name="North Field",
            season="Rabi 2026-27",
            strategy="Balanced",
            crops_json=json.dumps([
                {"name": "Onion", "acres": 3.0},
                {"name": "Wheat", "acres": 3.0},
                {"name": "Chickpea", "acres": 3.0},
                {"name": "Mustard", "acres": 1.0},
            ]),
            profit="₹4.04L",
            water_saved="27%",
            fertilizer_saved="22%",
            status="Current",
            created_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        ),
        Plan(
            id=f"plan-2-{uuid.uuid4().hex[:6]}",
            user_id=user_id,
            field_name="North Field",
            season="Kharif 2026",
            strategy="Balanced",
            crops_json=json.dumps([
                {"name": "Soybean", "acres": 4.0},
                {"name": "Maize", "acres": 3.0},
                {"name": "Pigeon pea", "acres": 3.0},
            ]),
            profit="₹3.12L",
            water_saved="24%",
            fertilizer_saved="19%",
            status="Completed",
            created_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
        ),
        Plan(
            id=f"plan-3-{uuid.uuid4().hex[:6]}",
            user_id=user_id,
            field_name="South Field",
            season="Rabi 2025-26",
            strategy="Max Profit",
            crops_json=json.dumps([
                {"name": "Onion", "acres": 4.0},
                {"name": "Wheat", "acres": 3.0},
                {"name": "Chickpea", "acres": 3.0},
            ]),
            profit="₹4.21L",
            water_saved="18%",
            fertilizer_saved="12%",
            status="Completed",
            created_at=datetime(2025, 10, 1, tzinfo=timezone.utc),
        ),
        Plan(
            id=f"plan-4-{uuid.uuid4().hex[:6]}",
            user_id=user_id,
            field_name="South Field",
            season="Kharif 2025",
            strategy="Water Saver",
            crops_json=json.dumps([
                {"name": "Soybean", "acres": 3.0},
                {"name": "Pigeon pea", "acres": 4.0},
                {"name": "Maize", "acres": 3.0},
            ]),
            profit="₹2.78L",
            water_saved="38%",
            fertilizer_saved="27%",
            status="Completed",
            created_at=datetime(2025, 6, 1, tzinfo=timezone.utc),
        ),
    ]

    for sp in sample_plans:
        db.add(sp)
    db.commit()
    return sample_plans


@router.get("/plans", response_model=List[PlanResponse])
def get_user_plans(
    field_id: Optional[str] = Query(None, description="Optional field ID filter"),
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Lists saved plans for the authenticated farmer. Requires a valid Bearer token."""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    query = db.query(Plan).filter(Plan.user_id == user_id)
    if field_id:
        query = query.filter(Plan.field_id == field_id)
    plans = query.order_by(Plan.created_at.desc()).all()

    if not plans and user_id == "demo-user-1" and not field_id:
        # Seed initial sample plans only for the default demo user
        plans = seed_sample_plans_for_user(user_id, db)

    return [plan_to_response(p) for p in plans]


@router.post("/plans", response_model=PlanResponse)
def save_plan(
    payload: PlanCreate,
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Saves an optimized allocation plan into farmer's history. Requires a valid Bearer token."""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Ensure user exists (should always be true for authenticated requests)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user not found in database"
        )

    crops_payload = [{"name": c.name, "acres": c.acres} for c in payload.crops]

    # Deduplication & Reapplication:
    # If reapplying an active plan for the same field and season, update the existing record
    if payload.fieldId and payload.status == "Current":
        existing = (
            db.query(Plan)
            .filter(
                Plan.user_id == user_id,
                Plan.field_id == payload.fieldId,
                Plan.season == payload.season,
                Plan.status == "Current",
            )
            .first()
        )
        if existing:
            existing.strategy = payload.strategy
            existing.crops_json = json.dumps(crops_payload)
            existing.profit = payload.profit
            existing.water_saved = payload.waterSaved
            existing.fertilizer_saved = payload.fertilizerSaved
            if payload.fieldName:
                existing.field_name = payload.fieldName
            db.commit()
            db.refresh(existing)

            # Update active plan tracking on Field
            field = db.query(Field).filter(Field.id == payload.fieldId).first()
            if field:
                field.active_plan_id = existing.id
                field.active_strategy = payload.strategy
                db.commit()

            return plan_to_response(existing)

    new_id = f"plan-{int(datetime.now(timezone.utc).timestamp() * 1000)}"

    plan = Plan(
        id=new_id,
        user_id=user_id,
        field_id=payload.fieldId,
        field_name=payload.fieldName,
        season=payload.season,
        strategy=payload.strategy,
        crops_json=json.dumps(crops_payload),
        profit=payload.profit,
        water_saved=payload.waterSaved,
        fertilizer_saved=payload.fertilizerSaved,
        status=payload.status,
        created_at=datetime.now(timezone.utc),
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    if payload.fieldId:
        field = db.query(Field).filter(Field.id == payload.fieldId).first()
        if field:
            field.active_plan_id = plan.id
            field.active_strategy = payload.strategy
            db.commit()

    return plan_to_response(plan)


@router.get("/plans/{plan_id}", response_model=PlanResponse)
def get_plan(
    plan_id: str,
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Retrieves full details of a specific saved plan. Requires a valid Bearer token."""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied: plan belongs to a different user")
    return plan_to_response(plan)


@router.delete("/plans/{plan_id}")
def delete_plan(
    plan_id: str,
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Deletes a saved plan."""
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    db.delete(plan)
    db.commit()
    return {"status": "success", "message": f"Plan {plan_id} deleted"}
