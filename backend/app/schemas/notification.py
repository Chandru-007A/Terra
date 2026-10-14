"""
Pydantic schemas for Notifications and Notification Preferences.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    id: str
    userId: str
    title: str
    message: str
    type: str  # "crop_reminder", "weather_alert", "calendar_event", "system"
    severity: str  # "info", "warning", "critical", "success"
    read: bool
    dismissed: bool
    fieldId: Optional[str] = None
    fieldName: Optional[str] = None
    cropName: Optional[str] = None
    linkUrl: Optional[str] = None
    dedupKey: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    createdAt: str

    model_config = ConfigDict(populate_by_name=True)


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    unreadCount: int
    totalCount: int
    lastChecked: str


class NotificationPreferenceUpdate(BaseModel):
    emailNotifications: Optional[bool] = None
    pushNotifications: Optional[bool] = None
    cropReminders: Optional[bool] = None
    weatherAlerts: Optional[bool] = None
    reminderDaysBefore: Optional[int] = None
    heavyRainThresholdMm: Optional[float] = None
    extremeHeatThresholdC: Optional[float] = None
    drySpellDaysThreshold: Optional[int] = None


class NotificationPreferenceResponse(BaseModel):
    emailNotifications: bool
    pushNotifications: bool
    cropReminders: bool
    weatherAlerts: bool
    reminderDaysBefore: int
    heavyRainThresholdMm: float
    extremeHeatThresholdC: float
    drySpellDaysThreshold: int


class WeatherStatusResponse(BaseModel):
    provider: str
    status: str
    lastChecked: str
    monitoredLocations: List[str]
    activeAlertsCount: int
