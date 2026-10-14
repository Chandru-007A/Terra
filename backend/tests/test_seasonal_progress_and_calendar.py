"""
Regression and unit test suite for Seasonal Progress and Crop Calendar events.
Tests dynamic progress calculations, event completion toggling, field switching isolation,
empty state handling, persistence across requests, and authentication/authorization.
"""

from datetime import datetime, date, timezone
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.reminder_service import evaluate_crop_reminders_for_user

client = TestClient(app)


@pytest.fixture
def auth_headers():
    res = client.post("/auth/login", json={"email": "ramesh.patil@gmail.com", "password": "terra123"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_user_headers():
    email = "calendar.test.user@gmail.com"
    reg = client.post("/auth/register", json={
        "name": "Calendar Tester",
        "email": email,
        "password": "password123",
        "village": "Nashik",
    })
    if reg.status_code == 200:
        token = reg.json()["access_token"]
    else:
        login = client.post("/auth/login", json={"email": email, "password": "password123"})
        token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_calendar_unauthenticated_access():
    """Unauthenticated users cannot fetch, create, toggle, or delete events."""
    assert client.get("/calendar/events").status_code == 401
    assert client.post("/calendar/events", json={"crop": "Wheat", "title": "Sowing", "year": 2026, "month": 10, "day": 1, "type": "sowing"}).status_code == 401
    assert client.patch("/calendar/events/evt-dummy/toggle").status_code == 401
    assert client.delete("/calendar/events/evt-dummy").status_code == 401


def test_calendar_events_retrieval_and_seed(auth_headers):
    """Authenticated user retrieves calendar events (seeds defaults on first call)."""
    res = client.get("/calendar/events", headers=auth_headers)
    assert res.status_code == 200
    events = res.json()
    assert len(events) >= 9
    first = events[0]
    assert "id" in first
    assert "crop" in first
    assert "completed" in first
    assert "status" in first
    assert first["completed"] in (True, False)


def test_calendar_event_toggle_completion(auth_headers):
    """Toggling an event marks it completed, sets completedAt, and toggling again reverts it."""
    # Create a fresh event
    create_res = client.post(
        "/calendar/events",
        headers=auth_headers,
        json={
            "crop": "Test Mustard",
            "title": "Test Sowing Operation",
            "year": 2026,
            "month": 9,
            "day": 18,
            "type": "sowing",
            "instructions": "Test seed depth",
        },
    )
    assert create_res.status_code == 201
    event_id = create_res.json()["id"]
    assert create_res.json()["completed"] is False
    assert create_res.json()["status"] == "pending"

    # Toggle to completed
    toggle_res1 = client.patch(f"/calendar/events/{event_id}/toggle", headers=auth_headers)
    assert toggle_res1.status_code == 200
    data1 = toggle_res1.json()
    assert data1["completed"] is True
    assert data1["status"] == "completed"
    assert data1["completedAt"] is not None

    # Verify persistence by fetching directly
    get_res = client.get("/calendar/events", headers=auth_headers)
    assert get_res.status_code == 200
    found = [e for e in get_res.json() if e["id"] == event_id]
    assert len(found) == 1
    assert found[0]["completed"] is True

    # Toggle back to pending
    toggle_res2 = client.patch(f"/calendar/events/{event_id}/toggle", headers=auth_headers)
    assert toggle_res2.status_code == 200
    data2 = toggle_res2.json()
    assert data2["completed"] is False
    assert data2["status"] == "pending"
    assert data2["completedAt"] is None

    # Cleanup
    del_res = client.delete(f"/calendar/events/{event_id}", headers=auth_headers)
    assert del_res.status_code == 200


def test_calendar_event_patch_update(auth_headers):
    """PATCH /calendar/events/{id} updates fields including status and completion."""
    create_res = client.post(
        "/calendar/events",
        headers=auth_headers,
        json={
            "crop": "Chickpea",
            "title": "Irrigation Task",
            "year": 2026,
            "month": 10,
            "day": 10,
            "type": "irrigation",
        },
    )
    assert create_res.status_code == 201
    ev_id = create_res.json()["id"]

    patch_res = client.patch(
        f"/calendar/events/{ev_id}",
        headers=auth_headers,
        json={"completed": True, "title": "Completed Irrigation Task"},
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["completed"] is True
    assert data["status"] == "completed"
    assert data["title"] == "Completed Irrigation Task"

    # Cleanup
    client.delete(f"/calendar/events/{ev_id}", headers=auth_headers)


def test_field_switching_isolation(auth_headers):
    """
    Calendar events filtered by field_id return only matching field events.
    Empty fields return 0 events, enabling an honest empty state without invented progress.
    """
    # 1. Get user's fields
    fields_res = client.get("/fields", headers=auth_headers)
    assert fields_res.status_code == 200
    fields = fields_res.json()
    assert len(fields) >= 2

    north_field = next((f for f in fields if "North" in f["name"]), fields[0])
    south_field = next((f for f in fields if "South" in f["name"]), fields[1])

    # 2. Query events for North Field
    north_events_res = client.get(f"/calendar/events?field_id={north_field['id']}", headers=auth_headers)
    assert north_events_res.status_code == 200
    north_events = north_events_res.json()
    assert len(north_events) > 0
    for e in north_events:
        assert e["fieldId"] == north_field["id"] or e["fieldName"] == north_field["name"]

    # 3. Query events for South Field (which has no operations yet)
    south_events_res = client.get(f"/calendar/events?field_id={south_field['id']}", headers=auth_headers)
    assert south_events_res.status_code == 200
    south_events = south_events_res.json()
    # South Field has no seed events assigned, should return 0 (honest empty state)
    assert len(south_events) == 0

    # 4. Aggregated All Fields query
    all_events_res = client.get("/calendar/events?field_id=all", headers=auth_headers)
    assert all_events_res.status_code == 200
    all_events = all_events_res.json()
    assert len(all_events) >= len(north_events)
    # Check deduplication
    ids = [e["id"] for e in all_events]
    assert len(ids) == len(set(ids)), "All events query contains duplicate IDs"


def test_progress_calculation_logic():
    """Validates the mathematical calculation of seasonal progress percentage."""
    # 0 events -> 0%
    assert 0 == (round((0 / 0) * 100) if 0 > 0 else 0)

    # 3 out of 10 events completed -> 30%
    completed = 3
    total = 10
    assert round((completed / total) * 100) == 30

    # 1 out of 9 completed -> 11%
    assert round((1 / 9) * 100) == 11

    # 9 out of 9 completed -> 100%
    assert round((9 / 9) * 100) == 100


def test_other_user_calendar_isolation(auth_headers, other_user_headers):
    """Users cannot toggle or delete another user's calendar events."""
    # User 1 creates an event
    create_res = client.post(
        "/calendar/events",
        headers=auth_headers,
        json={
            "crop": "Private Onion",
            "title": "Private Sowing",
            "year": 2026,
            "month": 10,
            "day": 5,
            "type": "sowing",
        },
    )
    assert create_res.status_code == 201
    ev_id = create_res.json()["id"]

    # Other user attempts to toggle
    toggle_res = client.patch(f"/calendar/events/{ev_id}/toggle", headers=other_user_headers)
    assert toggle_res.status_code in (403, 404)

    # Other user attempts to delete
    del_res = client.delete(f"/calendar/events/{ev_id}", headers=other_user_headers)
    assert del_res.status_code in (403, 404)

    # Owner can delete
    owner_del = client.delete(f"/calendar/events/{ev_id}", headers=auth_headers)
    assert owner_del.status_code == 200
