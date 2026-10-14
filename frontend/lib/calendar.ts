// lib/calendar.ts - Client for persistent farm calendar events
import { apiFetch } from "./api"

export interface ApiCalendarEvent {
  id: string
  userId: string
  crop: string
  emoji: string
  title: string
  year: number
  month: number // 0-based
  day: number
  type: "sowing" | "irrigation" | "fertilizer" | "harvest" | "custom"
  instructions: string
  fieldId?: string
  fieldName?: string
  badge?: string
  color?: string
  completed?: boolean
  completedAt?: string
  status?: string
  createdAt?: string
}

export interface CalendarEventCreateInput {
  crop: string
  emoji?: string
  title: string
  year: number
  month: number
  day: number
  type: string
  instructions?: string
  fieldId?: string
  fieldName?: string
  badge?: string
  color?: string
  completed?: boolean
  status?: string
}

export async function apiGetCalendarEvents(fieldId?: string): Promise<ApiCalendarEvent[]> {
  const url = fieldId && fieldId !== "all" 
    ? `/calendar/events?field_id=${encodeURIComponent(fieldId)}` 
    : "/calendar/events"
  return apiFetch<ApiCalendarEvent[]>(url, { method: "GET" })
}

export async function apiCreateCalendarEvent(input: CalendarEventCreateInput): Promise<ApiCalendarEvent> {
  return apiFetch<ApiCalendarEvent>("/calendar/events", {
    method: "POST",
    body: JSON.stringify(input),
  })
}

export async function apiToggleCalendarEvent(id: string): Promise<ApiCalendarEvent> {
  return apiFetch<ApiCalendarEvent>(`/calendar/events/${id}/toggle`, {
    method: "PATCH",
  })
}

export async function apiUpdateCalendarEvent(id: string, updates: Partial<ApiCalendarEvent>): Promise<ApiCalendarEvent> {
  return apiFetch<ApiCalendarEvent>(`/calendar/events/${id}`, {
    method: "PATCH",
    body: JSON.stringify(updates),
  })
}

export async function apiDeleteCalendarEvent(id: string): Promise<void> {
  return apiFetch<void>(`/calendar/events/${id}`, {
    method: "DELETE",
  })
}

