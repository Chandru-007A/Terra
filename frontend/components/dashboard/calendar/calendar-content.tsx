"use client"

import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  ChevronLeft,
  ChevronRight,
  Droplets,
  Sprout,
  Sparkles,
  Scissors,
  Calendar as CalendarIcon,
  Plus,
  Trash2,
  Check,
} from "lucide-react"
import { useState, useEffect, useCallback } from "react"
import { toast } from "sonner"
import {
  apiGetCalendarEvents,
  apiCreateCalendarEvent,
  apiDeleteCalendarEvent,
  apiToggleCalendarEvent,
  ApiCalendarEvent,
} from "@/lib/calendar"
import { useField } from "@/lib/field-context"

interface AgriEvent {
  id: string
  crop: string
  emoji: string
  title: string
  year: number
  month: number // 0-based (Jan=0)
  day: number
  type: "sowing" | "irrigation" | "fertilizer" | "harvest" | "custom"
  instructions: string
  badge: string
  color: string
  fieldId?: string
  fieldName?: string
  completed?: boolean
  status?: string
}

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
]

function getDaysInMonth(year: number, month: number): number {
  return new Date(year, month + 1, 0).getDate()
}

function getFirstDayOffset(year: number, month: number): number {
  return new Date(year, month, 1).getDay()
}

const DEFAULT_EVENTS: AgriEvent[] = [
  {
    id: "evt-1", crop: "Mustard", emoji: "🌼",
    title: "Sowing Window & Seed Treatment",
    year: 2026, month: 9, day: 15, // Oct 15
    type: "sowing",
    instructions: "Treat seeds with Trichoderma (5g/kg) and sow at 3-4 cm depth.",
    badge: "Mustard · 1 acre", color: "bg-amber-500",
  },
  {
    id: "evt-2", crop: "Chickpea", emoji: "🫘",
    title: "Rhizobium Inoculation & Sowing",
    year: 2026, month: 9, day: 20,
    type: "sowing",
    instructions: "Inoculate with Rhizobium culture; sow in furrows spaced 30 cm.",
    badge: "Chickpea · 3 acres", color: "bg-emerald-600",
  },
  {
    id: "evt-3", crop: "Onion", emoji: "🧅",
    title: "Transplanting Seedlings to Raised Beds",
    year: 2026, month: 9, day: 28,
    type: "sowing",
    instructions: "Transplant 6-8 week sturdy seedlings on raised bed furrows.",
    badge: "Onion · 3 acres", color: "bg-rose-500",
  },
  {
    id: "evt-4", crop: "Wheat", emoji: "🌾",
    title: "Main Rabi Wheat Sowing",
    year: 2026, month: 10, day: 5, // Nov 5
    type: "sowing",
    instructions: "Line sowing with seed-cum-fertilizer drill at 100 kg/ha rate.",
    badge: "Wheat · 3 acres", color: "bg-yellow-600",
  },
  {
    id: "evt-5", crop: "Mustard", emoji: "🌼",
    title: "Rosette Stage First Irrigation",
    year: 2026, month: 10, day: 14,
    type: "irrigation",
    instructions: "Provide first protective irrigation at 30 days after sowing.",
    badge: "Mustard · Critical Stage", color: "bg-cyan-500",
  },
  {
    id: "evt-6", crop: "Wheat", emoji: "🌾",
    title: "Crown Root Initiation (CRI) Irrigation",
    year: 2026, month: 10, day: 26,
    type: "irrigation",
    instructions: "Most critical watering window (21 DAS); moisture stress here drops yield 30%.",
    badge: "Wheat · Critical Stage", color: "bg-cyan-500",
  },
  {
    id: "evt-7", crop: "Onion", emoji: "🧅",
    title: "First Nitrogen Top-Dressing",
    year: 2026, month: 10, day: 28,
    type: "fertilizer",
    instructions: "Apply 25 kg/acre Urea before scheduled micro-irrigation.",
    badge: "Onion · NPK Split", color: "bg-purple-500",
  },
  {
    id: "evt-8", crop: "Chickpea", emoji: "🫘",
    title: "Branching & Pre-Flowering Light Watering",
    year: 2026, month: 11, day: 8, // Dec 8
    type: "irrigation",
    instructions: "Single supplementary light irrigation; avoid flooding roots.",
    badge: "Chickpea · Low Water", color: "bg-cyan-500",
  },
  {
    id: "evt-9", crop: "Mustard", emoji: "🌼",
    title: "Siliqua Maturity & Harvest Window",
    year: 2027, month: 0, day: 25, // Jan 25
    type: "harvest",
    instructions: "Harvest early morning when 75% pods turn yellowish-brown to avoid shattering.",
    badge: "Mustard · 7 q/acre", color: "bg-green-600",
  },
]

const weekDays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

const EVENT_TYPE_COLORS: Record<string, string> = {
  sowing: "bg-emerald-600",
  irrigation: "bg-cyan-500",
  fertilizer: "bg-purple-500",
  harvest: "bg-green-600",
  custom: "bg-primary",
}

export function CalendarContent() {
  const { selectedField } = useField()
  // Start at current calendar month
  const now = new Date()
  const [year, setYear] = useState(2026)
  const [month, setMonth] = useState(10) // November 2026 (0-based)
  const [filterType, setFilterType] = useState<string>("all")
  const [selectedDay, setSelectedDay] = useState<number>(26)
  const [events, setEvents] = useState<AgriEvent[]>(DEFAULT_EVENTS)
  const [addEventOpen, setAddEventOpen] = useState(false)
  const [newEvent, setNewEvent] = useState({
    crop: "", emoji: "🌱", title: "", type: "custom", instructions: "", day: "",
  })
  const [eventErrors, setEventErrors] = useState<Record<string, string>>({})
  const [savingEvent, setSavingEvent] = useState(false)

  const loadEvents = useCallback(async () => {
    try {
      const data = await apiGetCalendarEvents()
      if (data && data.length > 0) {
        setEvents(
          data.map((d) => ({
            id: d.id,
            crop: d.crop,
            emoji: d.emoji || "🌱",
            title: d.title,
            year: d.year,
            month: d.month,
            day: d.day,
            type: d.type as AgriEvent["type"],
            instructions: d.instructions || "",
            badge: d.badge || `${d.crop} · Event`,
            color: d.color || EVENT_TYPE_COLORS[d.type] || "bg-primary",
            fieldId: d.fieldId,
            fieldName: d.fieldName,
            completed: Boolean(d.completed),
            status: d.status || (d.completed ? "completed" : "pending"),
          }))
        )
      }
    } catch {}
  }, [])

  useEffect(() => {
    loadEvents()
    const handleUpdate = () => loadEvents()
    if (typeof window !== "undefined") {
      window.addEventListener("terra:calendar-updated", handleUpdate)
    }
    return () => {
      if (typeof window !== "undefined") {
        window.removeEventListener("terra:calendar-updated", handleUpdate)
      }
    }
  }, [loadEvents])

  const daysInMonth = getDaysInMonth(year, month)
  const offsetBlanks = getFirstDayOffset(year, month)

  const goToPrev = () => {
    if (month === 0) { setMonth(11); setYear((y) => y - 1) }
    else setMonth((m) => m - 1)
    setSelectedDay(1)
  }

  const goToNext = () => {
    if (month === 11) { setMonth(0); setYear((y) => y + 1) }
    else setMonth((m) => m + 1)
    setSelectedDay(1)
  }

  const filteredEvents = events.filter((ev) => {
    if (filterType !== "all" && ev.type !== filterType) return false
    return ev.year === year && ev.month === month
  })

  const dayEvents = filteredEvents.filter((ev) => ev.day === selectedDay)

  const getEventIcon = (type: string) => {
    switch (type) {
      case "irrigation": return <Droplets className="w-3.5 h-3.5 text-cyan-500" />
      case "fertilizer": return <Sparkles className="w-3.5 h-3.5 text-purple-500" />
      case "harvest": return <Scissors className="w-3.5 h-3.5 text-green-500" />
      default: return <Sprout className="w-3.5 h-3.5 text-emerald-500" />
    }
  }

  const validateEvent = () => {
    const errs: Record<string, string> = {}
    if (!newEvent.title.trim()) errs.title = "Event title is required"
    if (!newEvent.crop.trim()) errs.crop = "Crop/subject name is required"
    const d = Number(newEvent.day)
    if (!newEvent.day || isNaN(d) || d < 1 || d > daysInMonth)
      errs.day = `Enter a day between 1 and ${daysInMonth}`
    return errs
  }

  const handleToggleComplete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    try {
      const updated = await apiToggleCalendarEvent(id)
      setEvents((prev) =>
        prev.map((ev) =>
          ev.id === id
            ? { ...ev, completed: updated.completed, status: updated.status }
            : ev
        )
      )
      toast.success(
        updated.completed
          ? "Activity marked as completed! Seasonal progress updated."
          : "Activity marked as pending."
      )
      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent("terra:calendar-updated", { detail: updated }))
      }
    } catch {
      toast.error("Failed to toggle completion status")
    }
  }

  const handleAddEvent = async () => {
    const errs = validateEvent()
    setEventErrors(errs)
    if (Object.keys(errs).length > 0) return
    setSavingEvent(true)

    try {
      const saved = await apiCreateCalendarEvent({
        crop: newEvent.crop.trim(),
        emoji: newEvent.emoji || "🌱",
        title: newEvent.title.trim(),
        year,
        month,
        day: Number(newEvent.day),
        type: newEvent.type,
        instructions: newEvent.instructions.trim() || "Custom farm event.",
        fieldId: selectedField?.id,
        fieldName: selectedField?.name,
        badge: `${newEvent.crop.trim()} · Custom`,
        color: EVENT_TYPE_COLORS[newEvent.type] || "bg-primary",
      })

      const evt: AgriEvent = {
        id: saved.id,
        crop: saved.crop,
        emoji: saved.emoji || "🌱",
        title: saved.title,
        year: saved.year,
        month: saved.month,
        day: saved.day,
        type: saved.type as AgriEvent["type"],
        instructions: saved.instructions || "",
        badge: saved.badge || `${saved.crop} · Custom`,
        color: saved.color || EVENT_TYPE_COLORS[saved.type] || "bg-primary",
        fieldId: saved.fieldId,
        fieldName: saved.fieldName,
        completed: Boolean(saved.completed),
        status: saved.status || "pending",
      }
      setEvents((prev) => [...prev, evt])
      setSelectedDay(Number(newEvent.day))
      setNewEvent({ crop: "", emoji: "🌱", title: "", type: "custom", instructions: "", day: "" })
      setEventErrors({})
      setAddEventOpen(false)
      toast.success(`Event "${evt.title}" saved & scheduled for reminders`)
      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent("terra:calendar-updated", { detail: saved }))
      }
    } catch (err: any) {
      toast.error(err.message || "Failed to save event")
    } finally {
      setSavingEvent(false)
    }
  }

  const handleDeleteEvent = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    try {
      await apiDeleteCalendarEvent(id)
      setEvents((prev) => prev.filter((ev) => ev.id !== id))
      toast.success("Event deleted")
      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent("terra:calendar-updated", { detail: { id, deleted: true } }))
      }
    } catch {
      toast.error("Failed to delete event")
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Month & Filter Navigation */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Button variant="outline" size="icon" onClick={goToPrev}>
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <span className="font-semibold min-w-[160px] text-center text-foreground">
            {MONTH_NAMES[month]} {year}
          </span>
          <Button variant="outline" size="icon" onClick={goToNext}>
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>

        <div className="flex flex-wrap gap-2 items-center">
          {[
            ["all", "All"],
            ["sowing", "Sowing"],
            ["irrigation", "Irrigation"],
            ["fertilizer", "Fertilizer"],
            ["harvest", "Harvest"],
          ].map(([val, label]) => (
            <Button
              key={val}
              variant={filterType === val ? "default" : "outline"}
              size="sm"
              className="text-xs h-8"
              onClick={() => setFilterType(val)}
            >
              {label}
            </Button>
          ))}
          <Button
            size="sm"
            className="text-xs h-8 gap-1 ml-1"
            onClick={() => {
              setNewEvent((p) => ({ ...p, day: String(selectedDay) }))
              setAddEventOpen(true)
            }}
          >
            <Plus className="w-3.5 h-3.5" />
            Add Event
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Calendar Grid */}
        <Card className="lg:col-span-2 p-6">
          <div className="grid grid-cols-7 gap-2 mb-4">
            {weekDays.map((day) => (
              <div key={day} className="text-center text-xs font-semibold text-muted-foreground py-2">
                {day}
              </div>
            ))}
          </div>

          <div className="grid grid-cols-7 gap-2">
            {Array.from({ length: offsetBlanks }, (_, i) => (
              <div key={`blank-${i}`} className="aspect-square opacity-0" />
            ))}
            {Array.from({ length: daysInMonth }, (_, i) => i + 1).map((day) => {
              const hasEvents = filteredEvents.some((e) => e.day === day)
              const isSelected = day === selectedDay

              return (
                <button
                  key={day}
                  onClick={() => setSelectedDay(day)}
                  className={`
                    aspect-square rounded-lg flex flex-col items-center justify-center text-xs font-medium relative
                    transition-all duration-200 hover:scale-105 border
                    ${
                      isSelected
                        ? "bg-primary text-primary-foreground shadow-lg border-primary"
                        : hasEvents
                        ? "bg-secondary/70 border-primary/40 text-foreground font-semibold"
                        : "border-transparent hover:bg-secondary/40 text-foreground"
                    }
                  `}
                >
                  <span>{day}</span>
                  {hasEvents && (
                    <span
                      className={`w-1.5 h-1.5 rounded-full mt-1 ${
                        isSelected ? "bg-primary-foreground" : "bg-emerald-500"
                      }`}
                    />
                  )}
                </button>
              )
            })}
          </div>

          <div className="mt-6 pt-4 border-t border-border flex items-center justify-between text-xs text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500" /> Agricultural Operations scheduled
            </span>
            <span>Click any day to inspect field tasks</span>
          </div>
        </Card>

        {/* Selected Day Field Operations */}
        <Card className="p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-base text-foreground">
                Operations on {MONTH_NAMES[month]} {selectedDay}
              </h3>
              <Badge variant="outline" className="text-xs">
                {MONTH_NAMES[month].slice(0, 3)} {selectedDay}
              </Badge>
            </div>

            {dayEvents.length === 0 ? (
              <div className="py-6 text-center text-muted-foreground space-y-2">
                <CalendarIcon className="w-8 h-8 mx-auto opacity-30" />
                <p className="text-sm">No operations scheduled on this date.</p>
                <p className="text-xs opacity-75">Regular farm scouting and moisture monitoring recommended.</p>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-2 gap-1 text-xs"
                  onClick={() => {
                    setNewEvent((p) => ({ ...p, day: String(selectedDay) }))
                    setAddEventOpen(true)
                  }}
                >
                  <Plus className="w-3 h-3" />
                  Add event on this day
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                {dayEvents.map((event, index) => (
                  <div
                    key={event.id}
                    className="p-3.5 rounded-lg border border-border bg-card hover:shadow-md transition-all duration-300 animate-slide-in"
                    style={{ animationDelay: `${index * 100}ms` }}
                  >
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-md bg-secondary/80 mt-0.5">
                        {getEventIcon(event.type)}
                      </div>
                      <div className="flex-1 space-y-1">
                        <div className="flex items-center justify-between gap-2">
                          <h4 className="font-semibold text-sm text-foreground">
                            {event.emoji} {event.crop}
                          </h4>
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <Button
                              variant={event.completed ? "default" : "outline"}
                              size="sm"
                              className={`h-6 px-2 text-[10px] gap-1 transition-all ${
                                event.completed
                                  ? "bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm"
                                  : "border-border hover:border-emerald-500 hover:text-emerald-600 dark:hover:text-emerald-400"
                              }`}
                              onClick={(e) => handleToggleComplete(e, event.id)}
                              title={event.completed ? "Mark pending" : "Mark as completed"}
                            >
                              <Check className="w-3 h-3" />
                              {event.completed ? "Done" : "Complete"}
                            </Button>
                            <Badge variant="secondary" className="text-[10px] capitalize">
                              {event.type}
                            </Badge>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-5 w-5 text-muted-foreground hover:text-destructive"
                              onClick={(e) => handleDeleteEvent(e, event.id)}
                              title="Delete event"
                            >
                              <Trash2 className="w-3 h-3" />
                            </Button>
                          </div>
                        </div>
                        <p className={`text-xs font-medium ${event.completed ? "line-through text-muted-foreground" : "text-foreground/90"}`}>
                          {event.title}
                        </p>
                        <p className="text-[11px] text-muted-foreground leading-relaxed">
                          {event.instructions}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="mt-6 pt-4 border-t border-border bg-muted/20 p-3 rounded-lg text-xs space-y-1">
            <p className="font-medium text-foreground flex items-center gap-1.5">
              <Sprout className="w-3.5 h-3.5 text-primary" /> Integrated Advisory
            </p>
            <p className="text-muted-foreground text-[11px]">
              Schedules are calculated from optimal sowing dates and agronomic phenological stages.
            </p>
          </div>
        </Card>
      </div>

      {/* Add Event Modal */}
      <Dialog open={addEventOpen} onOpenChange={setAddEventOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Add Farm Event — {MONTH_NAMES[month]} {year}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>Day *</Label>
                <Input
                  type="number"
                  placeholder={`1–${daysInMonth}`}
                  min={1}
                  max={daysInMonth}
                  value={newEvent.day}
                  onChange={(e) => setNewEvent((p) => ({ ...p, day: e.target.value }))}
                />
                {eventErrors.day && <p className="text-xs text-destructive">{eventErrors.day}</p>}
              </div>
              <div className="space-y-1.5">
                <Label>Event Type</Label>
                <Select
                  value={newEvent.type}
                  onValueChange={(v) => setNewEvent((p) => ({ ...p, type: v }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="sowing">🌱 Sowing</SelectItem>
                    <SelectItem value="irrigation">💧 Irrigation</SelectItem>
                    <SelectItem value="fertilizer">✨ Fertilizer</SelectItem>
                    <SelectItem value="harvest">✂️ Harvest</SelectItem>
                    <SelectItem value="custom">📌 Custom</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>Crop / Subject *</Label>
              <Input
                placeholder="e.g. Onion, Wheat, General"
                value={newEvent.crop}
                onChange={(e) => setNewEvent((p) => ({ ...p, crop: e.target.value }))}
              />
              {eventErrors.crop && <p className="text-xs text-destructive">{eventErrors.crop}</p>}
            </div>
            <div className="space-y-1.5">
              <Label>Event Title *</Label>
              <Input
                placeholder="e.g. First irrigation after sowing"
                value={newEvent.title}
                onChange={(e) => setNewEvent((p) => ({ ...p, title: e.target.value }))}
              />
              {eventErrors.title && <p className="text-xs text-destructive">{eventErrors.title}</p>}
            </div>
            <div className="space-y-1.5">
              <Label>Instructions (optional)</Label>
              <Input
                placeholder="e.g. Apply at 6 AM, use drip irrigation"
                value={newEvent.instructions}
                onChange={(e) => setNewEvent((p) => ({ ...p, instructions: e.target.value }))}
              />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setAddEventOpen(false)}>Cancel</Button>
            <Button onClick={handleAddEvent} disabled={savingEvent}>
              {savingEvent ? "Adding…" : "Add Event"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
