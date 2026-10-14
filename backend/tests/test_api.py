"""
End-to-end API integration tests for all FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_root_and_health():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"


def test_recommend_crops_api():
    payload = {
        "n": 80.0,
        "p": 45.0,
        "k": 70.0,
        "ph": 7.2,
        "temperature": 22.0,
        "humidity": 60.0,
        "rainfall": 420.0,
        "season": "Rabi",
        "top_k": 6
    }
    res = client.post("/recommend/crops", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "crops" in data
    assert len(data["crops"]) > 0
    first_crop = data["crops"][0]
    assert "suitability" in first_crop
    assert "yield" in first_crop
    assert "profit" in first_crop


def test_predict_yield_api():
    payload = {
        "crop_id": "onion",
        "n": 110.0,
        "p": 55.0,
        "k": 75.0,
        "ph": 6.8,
        "temperature": 20.0,
        "rainfall": 450.0
    }
    res = client.post("/predict/yield", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["crop_id"] == "onion"
    assert data["expected_yield_q_per_acre"] > 0
    assert "confidence_interval_95" in data


def test_optimize_allocate_api():
    payload = {
        "crop_ids": ["onion", "wheat", "chickpea", "mustard"],
        "total_land_acres": 10.0,
        "water_available_kl": 16000.0,
        "fertilizer_available_kg": 1000.0,
        "total_budget_inr": 400000.0,
        "strategy": "balanced"
    }
    res = client.post("/optimize/allocate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["strategy"] == "Balanced"
    assert "crops" in data
    assert "expected_net_profit_inr" in data
    assert "water_saved_str" in data


def test_optimize_strategies_api():
    payload = {
        "crop_ids": ["onion", "wheat", "chickpea", "mustard"],
        "total_land_acres": 10.0,
        "water_available_kl": 16000.0,
        "fertilizer_available_kg": 1000.0,
        "total_budget_inr": 400000.0
    }
    res = client.post("/optimize/strategies", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["strategies"]) == 4


def test_auth_and_history_flow():
    # 1. Login with seeded demo credentials
    login_res = client.post("/auth/login", json={
        "email": "ramesh.patil@gmail.com",
        "password": "terra123"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Query /auth/me
    me_res = client.get("/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "ramesh.patil@gmail.com"

    # 3. Query /history/plans
    hist_res = client.get("/history/plans", headers=headers)
    assert hist_res.status_code == 200
    plans = hist_res.json()
    assert len(plans) > 0

    # 4. Save a new plan
    new_plan = {
        "season": "Rabi 2026-27",
        "strategy": "Water Saver",
        "crops": [
            {"name": "Chickpea", "acres": 6.0},
            {"name": "Mustard", "acres": 4.0}
        ],
        "profit": "₹2.68L",
        "waterSaved": "42%",
        "fertilizerSaved": "35%",
        "status": "Current"
    }
    save_res = client.post("/history/plans", json=new_plan, headers=headers)
    assert save_res.status_code == 200
    assert save_res.json()["strategy"] == "Water Saver"
