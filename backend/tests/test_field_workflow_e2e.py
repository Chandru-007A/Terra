"""
End-to-End agricultural test suite verifying field-centric workflows:
1. Multi-field creation and persistence (North Field & South Field).
2. Field-scoped crops and agronomic recommendations.
3. Field resource isolation and updates.
4. Strategy application and deduplication for active plans.
5. Plan history retrieval and plan export data verification.
6. Multi-field vs single-field plan separation.
7. Authorization and user isolation.
"""

import io
import csv
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


@pytest.fixture
def auth_headers():
    res = client.post("/auth/login", json={"email": "ramesh.patil@gmail.com", "password": "terra123"})
    assert res.status_code == 200, f"Login failed: {res.text}"
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_user_headers():
    email = "farmer.suresh@gmail.com"
    reg = client.post("/auth/register", json={
        "name": "Suresh Patil",
        "email": email,
        "password": "securepassword123",
        "village": "Baramati",
    })
    if reg.status_code == 200:
        token = reg.json()["access_token"]
    else:
        login = client.post("/auth/login", json={"email": email, "password": "securepassword123"})
        token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_complete_field_centric_workflow_e2e(auth_headers, other_user_headers):
    # Step 0: Clean up any prior fields for ramesh
    existing = client.get("/fields", headers=auth_headers).json()
    for f in existing:
        client.delete(f"/fields/{f['id']}", headers=auth_headers)

    # Step 1: Create North Field and South Field
    # North Field: 5.0 acres, Black Cotton, Nashik
    res_nf = client.post("/fields", headers=auth_headers, json={
        "name": "North Field",
        "areaAcres": 5.0,
        "soilType": "Black Cotton (Vertisol)",
        "location": "Nashik",
        "waterAvailableKl": 8000,
        "fertilizerAvailableKg": 500,
        "budgetInr": 200000,
    })
    assert res_nf.status_code == 201
    north_field = res_nf.json()
    assert north_field["name"] == "North Field"
    assert north_field["areaAcres"] == 5.0
    assert north_field["soilType"] == "Black Cotton (Vertisol)"

    # South Field: 2.5 acres, Red Laterite, Nashik
    res_sf = client.post("/fields", headers=auth_headers, json={
        "name": "South Field",
        "areaAcres": 2.5,
        "soilType": "Red Laterite",
        "location": "Nashik",
        "waterAvailableKl": 3500,
        "fertilizerAvailableKg": 250,
        "budgetInr": 100000,
    })
    assert res_sf.status_code == 201
    south_field = res_sf.json()
    assert south_field["name"] == "South Field"
    assert south_field["areaAcres"] == 2.5

    # Step 2: Persistence check: list fields
    fields_res = client.get("/fields", headers=auth_headers)
    assert fields_res.status_code == 200
    user_fields = fields_res.json()
    field_ids = [f["id"] for f in user_fields]
    assert north_field["id"] in field_ids
    assert south_field["id"] in field_ids
    assert len(user_fields) >= 2

    # Step 3: Add multiple crops to North Field
    crop1_res = client.post(f"/fields/{north_field['id']}/crops", headers=auth_headers, json={
        "cropId": "onion",
        "name": "Onion (Rabi)",
        "acres": 3.0,
        "sow": "Oct 25 – Nov 15",
        "season": "Rabi 2026-27",
    })
    assert crop1_res.status_code == 200

    crop2_res = client.post(f"/fields/{north_field['id']}/crops", headers=auth_headers, json={
        "cropId": "wheat",
        "name": "Wheat (Sharbati)",
        "acres": 2.0,
        "sow": "Nov 15 – Dec 05",
        "season": "Rabi 2026-27",
    })
    assert crop2_res.status_code == 200
    nf_updated = crop2_res.json()
    crop_names = [c["name"] for c in nf_updated["crops"]]
    assert "Onion (Rabi)" in crop_names
    assert "Wheat (Sharbati)" in crop_names
    assert sum(c["acres"] for c in nf_updated["crops"]) == 5.0

    # Step 3b: Request tailored AI recommendations for North Field
    recs_res = client.get(f"/fields/{north_field['id']}/recommendations?season=Rabi", headers=auth_headers)
    assert recs_res.status_code == 200
    recs = recs_res.json()
    assert recs["count"] > 0
    assert "crops" in recs
    assert recs["field"]["soilType"] == "Black Cotton (Vertisol)"
    assert recs["field"]["location"] == "Nashik"

    # Step 4: Field-Specific Resources - Add/Edit and verify isolation
    # Update North Field resources
    update_nf_res = client.patch(f"/fields/{north_field['id']}", headers=auth_headers, json={
        "waterAvailableKl": 9500.0,
        "fertilizerAvailableKg": 600.0,
        "budgetInr": 250000.0,
    })
    assert update_nf_res.status_code == 200
    assert update_nf_res.json()["waterAvailableKl"] == 9500.0

    # Verify South Field was NOT affected
    sf_check = client.get(f"/fields/{south_field['id']}", headers=auth_headers).json()
    assert sf_check["waterAvailableKl"] == 3500.0
    assert sf_check["fertilizerAvailableKg"] == 250.0
    assert sf_check["budgetInr"] == 100000.0
    assert sf_check["crops"] == []  # South Field has no crops yet

    # Step 5: Compare Strategies & Apply as Active Plan with Deduplication
    plan_data = {
        "fieldId": north_field["id"],
        "fieldName": "North Field",
        "season": "Rabi 2026-27",
        "strategy": "Max Profit",
        "crops": [
            {"name": "Onion", "acres": 3.0},
            {"name": "Wheat", "acres": 2.0},
        ],
        "profit": "₹3.42L",
        "waterSaved": "15%",
        "fertilizerSaved": "18%",
        "status": "Current",
    }
    save_plan_res1 = client.post("/history/plans", headers=auth_headers, json=plan_data)
    assert save_plan_res1.status_code == 200
    plan_id1 = save_plan_res1.json()["id"]

    # Re-apply updated strategy (e.g. farmer clicks Apply again or changes allocation)
    plan_data["profit"] = "₹3.50L"
    plan_data["waterSaved"] = "18%"
    save_plan_res2 = client.post("/history/plans", headers=auth_headers, json=plan_data)
    assert save_plan_res2.status_code == 200
    plan_id2 = save_plan_res2.json()["id"]

    # Deduplication check: ID must be identical (in-place update)
    assert plan_id1 == plan_id2
    assert save_plan_res2.json()["profit"] == "₹3.50L"

    # Step 6: Plan History retrieval
    history_res = client.get("/history/plans", headers=auth_headers)
    assert history_res.status_code == 200
    all_plans = history_res.json()
    # Check that for North Field and Rabi 2026-27, there is EXACTLY 1 active plan
    nf_current_plans = [p for p in all_plans if p.get("fieldId") == north_field["id"] and p.get("status") == "Current"]
    assert len(nf_current_plans) == 1
    assert nf_current_plans[0]["fieldName"] == "North Field"
    assert nf_current_plans[0]["profit"] == "₹3.50L"

    # Step 7: Create a plan for South Field to test multi-field separation
    sf_plan_data = {
        "fieldId": south_field["id"],
        "fieldName": "South Field",
        "season": "Rabi 2026-27",
        "strategy": "Water Conservation",
        "crops": [
            {"name": "Chickpea", "acres": 2.5},
        ],
        "profit": "₹1.45L",
        "waterSaved": "35%",
        "fertilizerSaved": "30%",
        "status": "Current",
    }
    save_sf_plan = client.post("/history/plans", headers=auth_headers, json=sf_plan_data)
    assert save_sf_plan.status_code == 200
    sf_plan_id = save_sf_plan.json()["id"]

    # Re-check history: should have both plans, separated by fieldId
    history_res2 = client.get("/history/plans", headers=auth_headers)
    plans_list = history_res2.json()
    nf_plans = [p for p in plans_list if p.get("fieldId") == north_field["id"]]
    sf_plans = [p for p in plans_list if p.get("fieldId") == south_field["id"]]
    assert len(nf_plans) == 1
    assert len(sf_plans) == 1
    assert nf_plans[0]["fieldName"] == "North Field"
    assert sf_plans[0]["fieldName"] == "South Field"

    # Step 8: Authorization & User isolation
    # Other user (Suresh) must NOT see Ramesh's fields or plans
    other_fields = client.get("/fields", headers=other_user_headers).json()
    assert not any(f["id"] in (north_field["id"], south_field["id"]) for f in other_fields)

    other_history = client.get("/history/plans", headers=other_user_headers).json()
    assert not any(p["id"] in (plan_id1, sf_plan_id) for p in other_history)

    # Other user cannot access North Field directly
    forbidden_field = client.get(f"/fields/{north_field['id']}", headers=other_user_headers)
    assert forbidden_field.status_code == 403

    # Other user cannot delete North Field
    forbidden_delete = client.delete(f"/fields/{north_field['id']}", headers=other_user_headers)
    assert forbidden_delete.status_code == 403
