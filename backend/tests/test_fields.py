"""
Unit and integration tests for /fields API endpoints:
Field creation, validation, isolation, duplicate prevention, and field-scoped recommendations.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


@pytest.fixture
def auth_headers():
    # Login as demo user
    res = client.post("/auth/login", json={"email": "ramesh.patil@gmail.com", "password": "terra123"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def second_user_headers():
    # Register a second farmer
    email = "other.farmer@gmail.com"
    reg = client.post("/auth/register", json={
        "name": "Suresh Kumar",
        "email": email,
        "password": "password123",
        "village": "Pune",
    })
    if reg.status_code == 200:
        token = reg.json()["access_token"]
    else:
        # Already registered in previous test run
        login = client.post("/auth/login", json={"email": email, "password": "password123"})
        token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_unauthenticated_fields_access():
    res = client.get("/fields")
    assert res.status_code == 401

    res = client.post("/fields", json={"name": "North Field", "areaAcres": 5.0, "soilType": "Black Cotton", "location": "Nashik"})
    assert res.status_code == 401


def test_create_and_list_fields(auth_headers):
    # Clean up existing test fields if any
    existing = client.get("/fields", headers=auth_headers).json()
    for f in existing:
        client.delete(f"/fields/{f['id']}", headers=auth_headers)

    # 1. Create North Field
    res1 = client.post("/fields", headers=auth_headers, json={
        "name": "North Field",
        "areaAcres": 5.0,
        "soilType": "Black Cotton (Vertisol)",
        "location": "Nashik",
        "waterAvailableKl": 8000,
        "fertilizerAvailableKg": 500,
        "budgetInr": 200000,
    })
    assert res1.status_code == 201
    nf = res1.json()
    assert nf["name"] == "North Field"
    assert nf["areaAcres"] == 5.0
    assert nf["waterAvailableKl"] == 8000
    assert nf["soilType"] == "Black Cotton (Vertisol)"

    # 2. Create South Field
    res2 = client.post("/fields", headers=auth_headers, json={
        "name": "South Field",
        "areaAcres": 2.5,
        "soilType": "Red Laterite",
        "location": "Nashik",
        "waterAvailableKl": 4000,
        "fertilizerAvailableKg": 250,
        "budgetInr": 100000,
    })
    assert res2.status_code == 201
    sf = res2.json()
    assert sf["name"] == "South Field"
    assert sf["areaAcres"] == 2.5

    # 3. List fields
    list_res = client.get("/fields", headers=auth_headers)
    assert list_res.status_code == 200
    fields = list_res.json()
    names = [f["name"] for f in fields]
    assert "North Field" in names
    assert "South Field" in names


def test_duplicate_field_name_prevention(auth_headers):
    # Attempt to create "North Field" again
    res = client.post("/fields", headers=auth_headers, json={
        "name": "North Field",
        "areaAcres": 5.0,
        "soilType": "Black Cotton (Vertisol)",
        "location": "Nashik",
    })
    assert res.status_code == 409
    assert "already exists" in res.json()["detail"]


def test_invalid_field_inputs(auth_headers):
    # Invalid zero area
    res = client.post("/fields", headers=auth_headers, json={
        "name": "Invalid Field",
        "areaAcres": 0,
        "soilType": "Alluvial",
        "location": "Nashik",
    })
    assert res.status_code in (400, 422)

    # Empty name
    res2 = client.post("/fields", headers=auth_headers, json={
        "name": "   ",
        "areaAcres": 2.0,
        "soilType": "Alluvial",
        "location": "Nashik",
    })
    assert res2.status_code == 400


def test_user_field_isolation(auth_headers, second_user_headers):
    # Suresh Kumar queries fields — should not see Ramesh's fields
    suresh_fields = client.get("/fields", headers=second_user_headers).json()
    ramesh_names = [f["name"] for f in client.get("/fields", headers=auth_headers).json()]

    for sf in suresh_fields:
        assert sf["name"] not in ("North Field", "South Field")

    # Suresh trying to access Ramesh's field directly
    ramesh_field_id = client.get("/fields", headers=auth_headers).json()[0]["id"]
    forbidden_res = client.get(f"/fields/{ramesh_field_id}", headers=second_user_headers)
    assert forbidden_res.status_code == 403


def test_field_scoped_crops_and_recommendations(auth_headers):
    fields = client.get("/fields", headers=auth_headers).json()
    nf = next(f for f in fields if f["name"] == "North Field")

    # Add crop to North Field
    add_crop = client.post(f"/fields/{nf['id']}/crops", headers=auth_headers, json={
        "cropId": "onion",
        "name": "Onion (Rabi)",
        "acres": 3.0,
        "sow": "Oct 25 – Nov 15",
        "season": "Rabi 2026-27",
    })
    assert add_crop.status_code == 200
    updated_field = add_crop.json()
    assert any(c["cropId"] == "onion" and c["acres"] == 3.0 for c in updated_field["crops"])

    # Get tailored recommendations for North Field
    rec_res = client.get(f"/fields/{nf['id']}/recommendations?season=Rabi", headers=auth_headers)
    assert rec_res.status_code == 200
    recs = rec_res.json()
    assert recs["count"] > 0
    assert len(recs["crops"]) > 0


def test_active_plan_deduplication(auth_headers):
    fields = client.get("/fields", headers=auth_headers).json()
    nf = next(f for f in fields if f["name"] == "North Field")

    # Apply Balanced strategy as active plan for North Field
    plan_payload = {
        "fieldId": nf["id"],
        "fieldName": "North Field",
        "season": "Rabi 2026-27",
        "strategy": "Balanced",
        "crops": [{"name": "Onion", "acres": 3.0}, {"name": "Wheat", "acres": 2.0}],
        "profit": "₹2.96L",
        "waterSaved": "28%",
        "fertilizerSaved": "25%",
        "status": "Current",
    }

    res1 = client.post("/history/plans", headers=auth_headers, json=plan_payload)
    assert res1.status_code == 200
    plan_id1 = res1.json()["id"]

    # Reapply updated strategy (e.g., changed to Max Profit)
    plan_payload["strategy"] = "Max Profit"
    plan_payload["profit"] = "₹3.40L"

    res2 = client.post("/history/plans", headers=auth_headers, json=plan_payload)
    assert res2.status_code == 200
    plan_id2 = res2.json()["id"]

    # Must update existing active plan for that field+season, NOT duplicate
    assert plan_id1 == plan_id2
    assert res2.json()["strategy"] == "Max Profit"
    assert res2.json()["profit"] == "₹3.40L"


def test_crop_removal_and_field_isolation(auth_headers):
    fields = client.get("/fields", headers=auth_headers).json()
    nf = next(f for f in fields if f["name"] == "North Field")
    sf = next(f for f in fields if f["name"] == "South Field")

    # Add Wheat to North Field
    add_wheat = client.post(f"/fields/{nf['id']}/crops", headers=auth_headers, json={
        "cropId": "wheat",
        "name": "Wheat (Rabi)",
        "acres": 2.0,
        "sow": "Nov 1 – Nov 25",
        "season": "Rabi 2026-27",
        "status": "in",
    })
    assert add_wheat.status_code == 200
    nf_crops = [c["cropId"] for c in add_wheat.json()["crops"]]
    assert "wheat" in nf_crops

    # Verify South Field still has NO crops
    sf_fresh = client.get(f"/fields/{sf['id']}", headers=auth_headers).json()
    assert sf_fresh["crops"] == []

    # Remove Wheat from North Field via DELETE endpoint
    del_wheat = client.delete(f"/fields/{nf['id']}/crops/wheat", headers=auth_headers)
    assert del_wheat.status_code == 200
    nf_after = [c["cropId"] for c in del_wheat.json()["crops"]]
    assert "wheat" not in nf_after
