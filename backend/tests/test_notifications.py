"""
Comprehensive test suite for Notifications, Crop Reminders, Weather Alerts, and Preferences.
Verifies authentication, isolation, deduplication, threshold triggers, and lifecycle operations.
"""

from datetime import datetime, date, timezone
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.weather_service import evaluate_weather_alerts_for_field

client = TestClient(app)


@pytest.fixture
def auth_headers():
    res = client.post("/auth/login", json={"email": "ramesh.patil@gmail.com", "password": "terra123"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_user_headers():
    email = "test.neighbor@gmail.com"
    reg = client.post("/auth/register", json={
        "name": "Neighbor Farmer",
        "email": email,
        "password": "password123",
        "village": "Pune",
    })
    if reg.status_code == 200:
        token = reg.json()["access_token"]
    else:
        login = client.post("/auth/login", json={"email": email, "password": "password123"})
        token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_unauthenticated_notifications_access():
    res = client.get("/notifications")
    assert res.status_code == 401

    res = client.post("/notifications/sync")
    assert res.status_code == 401

    res = client.get("/notifications/preferences")
    assert res.status_code == 401


def test_notifications_lifecycle_and_deduplication(auth_headers):
    # Reset preferences to all enabled
    client.put("/notifications/preferences", headers=auth_headers, json={
        "cropReminders": True,
        "weatherAlerts": True,
        "reminderDaysBefore": 2,
    })

    # 1. Fetch notifications
    res1 = client.get("/notifications", headers=auth_headers)
    assert res1.status_code == 200
    data1 = res1.json()
    assert "notifications" in data1
    assert "unreadCount" in data1
    initial_count = data1["totalCount"]

    # 2. Repeated sync must NOT create duplicate rows
    sync_res = client.post("/notifications/sync", headers=auth_headers)
    assert sync_res.status_code == 200
    assert sync_res.json()["newNotificationsCount"] == 0

    res2 = client.get("/notifications", headers=auth_headers)
    data2 = res2.json()
    assert data2["totalCount"] == initial_count

    # 3. Mark single as read
    if data2["notifications"]:
        item = data2["notifications"][0]
        mark_res = client.patch(f"/notifications/{item['id']}/read", headers=auth_headers)
        assert mark_res.status_code == 200
        assert mark_res.json()["read"] is True

        # 4. Mark all as read
        all_read = client.post("/notifications/mark-all-read", headers=auth_headers)
        assert all_read.status_code == 200
        check_unread = client.get("/notifications", headers=auth_headers).json()
        assert check_unread["unreadCount"] == 0

        # 5. Dismiss notification
        dismiss_res = client.delete(f"/notifications/{item['id']}", headers=auth_headers)
        assert dismiss_res.status_code == 200

        # Confirm dismissed item is excluded from active list
        after_dismiss = client.get("/notifications", headers=auth_headers).json()
        ids = [n["id"] for n in after_dismiss["notifications"]]
        assert item["id"] not in ids


def test_notification_preferences_controls(auth_headers):
    # Disable crop reminders
    res1 = client.put("/notifications/preferences", headers=auth_headers, json={
        "cropReminders": False,
        "weatherAlerts": True,
    })
    assert res1.status_code == 200
    assert res1.json()["cropReminders"] is False
    assert res1.json()["weatherAlerts"] is True

    # Re-enable crop reminders
    res2 = client.put("/notifications/preferences", headers=auth_headers, json={
        "cropReminders": True,
        "reminderDaysBefore": 3,
    })
    assert res2.status_code == 200
    assert res2.json()["cropReminders"] is True
    assert res2.json()["reminderDaysBefore"] == 3


def test_weather_alert_evaluation_with_thresholds():
    # Deterministic forecast data simulating extreme conditions
    mock_forecast = {
        "success": True,
        "provider": "Open-Meteo Weather Forecast API",
        "last_updated": "2026-10-14T02:00:00Z",
        "daily": {
            "time": ["2026-10-15", "2026-10-16", "2026-10-17", "2026-10-18", "2026-10-19"],
            "temperature_2m_max": [38.5, 34.0, 32.0, 31.0, 30.0],  # 38.5 exceeds 36.0 threshold
            "temperature_2m_min": [24.0, 22.0, 21.0, 20.0, 19.0],
            "precipitation_sum": [45.0, 0.0, 0.0, 0.0, 0.0],       # 45.0 exceeds 35.0 threshold
            "wind_speed_10m_max": [45.0, 15.0, 12.0, 10.0, 8.0],   # 45.0 exceeds 40.0 threshold
        }
    }

    alerts = evaluate_weather_alerts_for_field(
        field_id="field-mock-1",
        field_name="North Field",
        location="Nashik",
        crops=[{"name": "Onion"}],
        heavy_rain_threshold=35.0,
        extreme_heat_threshold=36.0,
        custom_forecast=mock_forecast,
    )

    alert_types = [a["title"] for a in alerts]
    assert any("Heavy Rainfall Alert" in t for t in alert_types)
    assert any("High Heat Spike" in t for t in alert_types)
    assert any("High Wind Alert" in t for t in alert_types)

    # Check alert structure and transparency
    rain_alert = next(a for a in alerts if "Heavy Rainfall" in a["title"])
    assert rain_alert["field_id"] == "field-mock-1"
    assert "North Field" in rain_alert["message"]
    assert rain_alert["metadata"]["rainfall_mm"] == 45.0
    assert rain_alert["metadata"]["provider"] == "Open-Meteo Weather Forecast API"


def test_calendar_events_and_reminder_flow(auth_headers):
    # 1. Fetch calendar events
    res = client.get("/calendar/events", headers=auth_headers)
    assert res.status_code == 200
    events = res.json()
    assert len(events) >= 5

    # 2. Create custom sowing event scheduled for next month
    create_res = client.post("/calendar/events", headers=auth_headers, json={
        "crop": "Garlic",
        "emoji": "🧄",
        "title": "Winter Garlic Planting",
        "year": 2026,
        "month": 10,  # November
        "day": 12,
        "type": "sowing",
        "instructions": "Plant cloves root-down 5cm deep.",
    })
    assert create_res.status_code == 201
    new_evt = create_res.json()
    assert new_evt["crop"] == "Garlic"
    assert new_evt["id"].startswith("evt-")

    # 3. Delete event cleans up
    del_res = client.delete(f"/calendar/events/{new_evt['id']}", headers=auth_headers)
    assert del_res.status_code == 200


def test_user_isolation(auth_headers, other_user_headers):
    # Fetch notifications for user 1
    u1_notifs = client.get("/notifications", headers=auth_headers).json()["notifications"]
    if u1_notifs:
        target_id = u1_notifs[0]["id"]
        # Other user trying to mark as read must get 403
        bad_read = client.patch(f"/notifications/{target_id}/read", headers=other_user_headers)
        assert bad_read.status_code == 403

        # Other user trying to dismiss must get 403
        bad_del = client.delete(f"/notifications/{target_id}", headers=other_user_headers)
        assert bad_del.status_code == 403
