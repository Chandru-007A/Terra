// lib/notifications.ts - Client for notifications, reminders, weather alerts, and browser push
import { apiFetch } from "./api"

export interface AppNotification {
  id: string
  userId: string
  title: string
  message: string
  type: "crop_reminder" | "weather_alert" | "calendar_event" | "system"
  severity: "info" | "warning" | "critical" | "success"
  read: boolean
  dismissed: boolean
  fieldId?: string
  fieldName?: string
  cropName?: string
  linkUrl?: string
  dedupKey?: string
  metadata?: Record<string, any>
  createdAt: string
}

export interface NotificationListResponse {
  notifications: AppNotification[]
  unreadCount: number
  totalCount: number
  lastChecked: string
}

export interface NotificationPreferences {
  emailNotifications: boolean
  pushNotifications: boolean
  cropReminders: boolean
  weatherAlerts: boolean
  reminderDaysBefore: number
  heavyRainThresholdMm: number
  extremeHeatThresholdC: number
  drySpellDaysThreshold: number
}

export interface WeatherStatus {
  provider: string
  status: string
  lastChecked: string
  monitoredLocations: string[]
  activeAlertsCount: number
}

export async function apiGetNotifications(params?: {
  typeFilter?: string
  unreadOnly?: boolean
  autoSync?: boolean
}): Promise<NotificationListResponse> {
  const query = new URLSearchParams()
  if (params?.typeFilter && params.typeFilter !== "all") query.set("type_filter", params.typeFilter)
  if (params?.unreadOnly) query.set("unread_only", "true")
  if (params?.autoSync !== undefined) query.set("auto_sync", String(params.autoSync))

  const qs = query.toString() ? `?${query.toString()}` : ""
  return apiFetch<NotificationListResponse>(`/notifications${qs}`, { method: "GET" })
}

export async function apiSyncNotifications(): Promise<{
  status: string
  newNotificationsCount: number
  unreadCount: number
  timestamp: string
}> {
  return apiFetch("/notifications/sync", { method: "POST" })
}

export async function apiMarkNotificationAsRead(id: string): Promise<AppNotification> {
  return apiFetch<AppNotification>(`/notifications/${id}/read`, { method: "PATCH" })
}

export async function apiMarkAllNotificationsAsRead(): Promise<{ status: string; markedReadCount: number }> {
  return apiFetch("/notifications/mark-all-read", { method: "POST" })
}

export async function apiDismissNotification(id: string): Promise<{ status: string; message: string }> {
  return apiFetch(`/notifications/${id}`, { method: "DELETE" })
}

export async function apiDismissAllNotifications(): Promise<{ status: string; dismissedCount: number }> {
  return apiFetch("/notifications/dismiss-all", { method: "DELETE" })
}

export async function apiGetNotificationPreferences(): Promise<NotificationPreferences> {
  return apiFetch<NotificationPreferences>("/notifications/preferences", { method: "GET" })
}

export async function apiUpdateNotificationPreferences(
  prefs: Partial<NotificationPreferences>
): Promise<NotificationPreferences> {
  return apiFetch<NotificationPreferences>("/notifications/preferences", {
    method: "PUT",
    body: JSON.stringify(prefs),
  })
}

export async function apiGetWeatherStatus(): Promise<WeatherStatus> {
  return apiFetch<WeatherStatus>("/notifications/weather-status", { method: "GET" })
}

// Browser Push Notification Helpers
export async function requestBrowserNotificationPermission(): Promise<NotificationPermission> {
  if (typeof window === "undefined" || !("Notification" in window)) {
    return "denied"
  }
  try {
    const permission = await Notification.requestPermission()
    return permission
  } catch (err) {
    console.warn("Notification permission request error:", err)
    return "denied"
  }
}

export function showBrowserNotification(title: string, options?: NotificationOptions) {
  if (typeof window === "undefined" || !("Notification" in window)) return
  if (Notification.permission === "granted") {
    try {
      new Notification(title, {
        icon: "/favicon.ico",
        badge: "/favicon.ico",
        ...options,
      })
    } catch (e) {
      console.warn("Error showing browser notification:", e)
    }
  }
}
