"use client"

import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Sprout,
  Droplets,
  Sparkles,
  Scissors,
  Check,
  Calendar as CalendarIcon,
  Plus,
  AlertCircle,
  Clock,
  ChevronDown,
  ChevronUp,
} from "lucide-react"
import { useEffect, useState, useMemo, useCallback } from "react"
import { useField } from "@/lib/field-context"
import { useAuth } from "@/components/auth/AuthProvider"
import { apiGetCalendarEvents, apiToggleCalendarEvent, ApiCalendarEvent } from "@/lib/calendar"
import { getHistory } from "@/lib/history"
import Link from "next/link"
import { toast } from "sonner"

const MONTH_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

interface StageMilestone {
  key: string
  name: string
  type: "sowing" | "irrigation" | "fertilizer" | "harvest" | "custom"
  icon: any
  events: ApiCalendarEvent[]
  dateLabel: string
  status: "Completed" | "In Progress" | "Upcoming" | "Overdue" | "Not Scheduled"
}

export function ProjectProgress() {
  const { user } = useAuth()
  const { selectedField, selectedFieldId, fields } = useField()
  const [events, setEvents] = useState<ApiCalendarEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [activePlanSeason, setActivePlanSeason] = useState<string | null>(null)
  const [progress, setProgress] = useState(0)
  const [showActivitiesList, setShowActivitiesList] = useState(false)
  const [togglingId, setTogglingId] = useState<string | null>(null)

  // 1. Fetch persistent calendar events and saved plans
  const loadCalendarData = useCallback(async () => {
    setLoading(true)
    try {
      const data = await apiGetCalendarEvents()
      setEvents(data || [])
    } catch {
      // offline/fallback
    } finally {
      setLoading(false)
    }
  }, [])

  const loadPlanData = useCallback(async () => {
    if (!user) return
    try {
      const plans = await getHistory(user.id, selectedField?.id)
      if (plans && plans.length > 0) {
        setActivePlanSeason(plans[0].season)
      } else {
        setActivePlanSeason(null)
      }
    } catch {}
  }, [user, selectedField?.id])

  useEffect(() => {
    loadCalendarData()
    loadPlanData()
  }, [user, loadCalendarData, loadPlanData])

  // Synchronize with external changes (e.g. from Crop Calendar or Crop Advisor)
  useEffect(() => {
    const handleCalendarUpdate = () => {
      loadCalendarData()
    }
    if (typeof window !== "undefined") {
      window.addEventListener("terra:calendar-updated", handleCalendarUpdate)
    }
    return () => {
      if (typeof window !== "undefined") {
        window.removeEventListener("terra:calendar-updated", handleCalendarUpdate)
      }
    }
  }, [loadCalendarData])

  // 2. Filter events strictly according to selected field
  const fieldEvents = useMemo(() => {
    if (!selectedFieldId || selectedFieldId === "all") {
      return events
    }
    return events.filter((ev) => {
      if (ev.fieldId && ev.fieldId === selectedFieldId) return true
      if (selectedField?.name && ev.fieldName && ev.fieldName.toLowerCase() === selectedField.name.toLowerCase()) {
        return true
      }
      return false
    })
  }, [events, selectedFieldId, selectedField])

  // 3. Determine active season from field crops, saved plans, or default
  const activeSeason = useMemo(() => {
    if (selectedField && selectedField.crops && selectedField.crops.length > 0) {
      const cropWithSeason = selectedField.crops.find((c) => c.season)
      if (cropWithSeason?.season) return cropWithSeason.season
    }
    if (activePlanSeason) return activePlanSeason
    return "Rabi 2026-27"
  }, [selectedField, activePlanSeason])

  // 4. Calculate dynamic progress based on real event statuses and dates
  const now = useMemo(() => new Date(), [])

  const { completedCount, upcomingCount, overdueCount, totalCount, dynamicPercentage } = useMemo(() => {
    const total = fieldEvents.length
    if (total === 0) {
      return {
        completedCount: 0,
        upcomingCount: 0,
        overdueCount: 0,
        totalCount: 0,
        dynamicPercentage: 0,
      }
    }

    let completed = 0
    let overdue = 0
    let upcoming = 0

    fieldEvents.forEach((ev) => {
      if (ev.completed) {
        completed++
      } else {
        const evDate = new Date(ev.year, ev.month, ev.day, 23, 59, 59)
        if (evDate < now) {
          overdue++
        } else {
          upcoming++
        }
      }
    })

    const pct = Math.round((completed / total) * 100)
    return {
      completedCount: completed,
      upcomingCount: upcoming,
      overdueCount: overdue,
      totalCount: total,
      dynamicPercentage: pct,
    }
  }, [fieldEvents, now])

  // Smooth progress animation matching target percentage
  useEffect(() => {
    const timer = setTimeout(() => {
      if (progress < dynamicPercentage) {
        setProgress((prev) => Math.min(prev + 1, dynamicPercentage))
      } else if (progress > dynamicPercentage) {
        setProgress((prev) => Math.max(prev - 1, dynamicPercentage))
      }
    }, 20)
    return () => clearTimeout(timer)
  }, [progress, dynamicPercentage])

  // 5. Construct meaningful agronomic stages from saved data
  const stages: StageMilestone[] = useMemo(() => {
    const stageDefs = [
      { key: "sowing", name: "Sowing & Nursery", type: "sowing" as const, icon: Sprout },
      { key: "irrigation", name: "Irrigation & Water", type: "irrigation" as const, icon: Droplets },
      { key: "fertilizer", name: "Fertilization & Nutrition", type: "fertilizer" as const, icon: Sparkles },
      { key: "custom", name: "Crop Maintenance", type: "custom" as const, icon: Clock },
      { key: "harvest", name: "Harvest Window", type: "harvest" as const, icon: Scissors },
    ]

    return stageDefs.map((def) => {
      const matchingEvents = fieldEvents.filter((ev) => ev.type === def.type)

      if (matchingEvents.length === 0) {
        // Check if field has planned crops for sowing
        if (def.key === "sowing" && selectedField?.crops && selectedField.crops.length > 0) {
          const sowWindows = selectedField.crops.map((c) => c.sow).filter(Boolean)
          const dateLabel = sowWindows.length > 0 ? sowWindows[0]! : "Seasonal window"
          return {
            ...def,
            events: [],
            dateLabel,
            status: "Upcoming" as const,
          }
        }
        return {
          ...def,
          events: [],
          dateLabel: "Not scheduled",
          status: "Not Scheduled" as const,
        }
      }

      // Sort matching events chronologically
      const sorted = [...matchingEvents].sort((a, b) => {
        const da = new Date(a.year, a.month, a.day).getTime()
        const db = new Date(b.year, b.month, b.day).getTime()
        return da - db
      })

      const first = sorted[0]
      const last = sorted[sorted.length - 1]
      const dateLabel =
        sorted.length === 1
          ? `${MONTH_SHORT[first.month]} ${first.day}`
          : `${MONTH_SHORT[first.month]} ${first.day} – ${MONTH_SHORT[last.month]} ${last.day}`

      const allCompleted = sorted.every((e) => e.completed)
      const hasOverdue = sorted.some((e) => !e.completed && new Date(e.year, e.month, e.day, 23, 59, 59) < now)
      const hasInProgress = sorted.some((e) => {
        const d = new Date(e.year, e.month, e.day)
        return !e.completed && Math.abs((d.getTime() - now.getTime()) / (1000 * 3600 * 24)) <= 5
      })

      let status: StageMilestone["status"] = "Upcoming"
      if (allCompleted) {
        status = "Completed"
      } else if (hasOverdue) {
        status = "Overdue"
      } else if (hasInProgress) {
        status = "In Progress"
      }

      return {
        ...def,
        events: sorted,
        dateLabel,
        status,
      }
    })
  }, [fieldEvents, selectedField, now])

  // Handle toggling completion of an event directly from dashboard
  const handleToggleEvent = async (eventId: string) => {
    setTogglingId(eventId)
    try {
      const updated = await apiToggleCalendarEvent(eventId)
      setEvents((prev) =>
        prev.map((e) =>
          e.id === eventId
            ? { ...e, completed: updated.completed, status: updated.status }
            : e
        )
      )
      toast.success(
        updated.completed
          ? `Marked "${updated.title}" as completed!`
          : `Marked "${updated.title}" as pending.`
      )
      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent("terra:calendar-updated", { detail: updated }))
      }
    } catch {
      toast.error("Failed to update activity status")
    } finally {
      setTogglingId(null)
    }
  }

  const circumference = 2 * Math.PI * 70
  const strokeDashoffset = circumference - (progress / 100) * circumference

  const hasNoData =
    !loading && totalCount === 0 && (!selectedField?.crops || selectedField.crops.length === 0)

  return (
    <Card
      id="seasonal-progress-card"
      className="p-4 transition-all duration-500 hover:shadow-xl animate-slide-in-up overflow-hidden bg-card border-border"
      style={{ animationDelay: "800ms" }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <h2 className="text-lg font-semibold text-foreground">Seasonal Progress</h2>
          <p className="text-xs text-muted-foreground">
            {selectedField ? selectedField.name : "All Fields"} · {activeSeason}
          </p>
        </div>
        <Badge
          variant="outline"
          className="text-[11px] font-medium border-border capitalize text-foreground"
        >
          {selectedField ? selectedField.name : "Aggregated"}
        </Badge>
      </div>

      <div className="flex flex-col items-center">
        {/* Animated Circular Gauge */}
        <div className="relative w-40 h-40 mb-4">
          <div
            className="absolute inset-0 rounded-full opacity-20"
            style={{
              background:
                "repeating-linear-gradient(45deg, transparent, transparent 6px, oklch(0.42 0.15 155) 6px, oklch(0.42 0.15 155) 12px)",
            }}
          />
          <svg className="w-full h-full -rotate-90 relative z-10" viewBox="0 0 160 160">
            <circle
              cx="80"
              cy="80"
              r="70"
              stroke="currentColor"
              strokeWidth="12"
              fill="none"
              className="text-muted/30"
            />
            <circle
              cx="80"
              cy="80"
              r="70"
              stroke="currentColor"
              strokeWidth="12"
              fill="none"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              className="text-primary transition-all duration-1000 ease-out"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span id="seasonal-progress-percentage" className="text-4xl font-bold text-foreground">
              {progress}%
            </span>
            <span className="text-xs text-muted-foreground mt-1 max-w-[120px] text-center truncate">
              {activeSeason}
            </span>
          </div>
        </div>

        {/* Dynamic Activity Count Indicators */}
        <div className="flex flex-wrap justify-center gap-3 text-xs mb-4">
          <div className="flex items-center gap-1.5" title="Completed agricultural activities">
            <div className="w-2.5 h-2.5 rounded-full bg-primary flex-shrink-0" />
            <span className="text-muted-foreground whitespace-nowrap">
              Completed ({completedCount})
            </span>
          </div>
          <div className="flex items-center gap-1.5" title="Upcoming planned operations">
            <div className="w-2.5 h-2.5 rounded-full bg-foreground flex-shrink-0" />
            <span className="text-muted-foreground whitespace-nowrap">
              Upcoming ({upcomingCount})
            </span>
          </div>
          {overdueCount > 0 ? (
            <div className="flex items-center gap-1.5" title="Overdue operations requiring attention">
              <div className="w-2.5 h-2.5 rounded-full bg-destructive flex-shrink-0" />
              <span className="text-destructive font-medium whitespace-nowrap">
                Overdue ({overdueCount})
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5" title="Pending tasks">
              <div
                className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                style={{
                  background:
                    "repeating-linear-gradient(45deg, transparent, transparent 2px, oklch(0.55 0.02 120) 2px, oklch(0.55 0.02 120) 4px)",
                }}
              />
              <span className="text-muted-foreground whitespace-nowrap">Pending</span>
            </div>
          )}
        </div>

        {/* Honest Empty State when Field has no crops or operations */}
        {loading ? (
          <div className="w-full py-8 text-center text-xs text-muted-foreground animate-pulse">
            Loading seasonal operations…
          </div>
        ) : hasNoData ? (
          <div
            id="seasonal-progress-empty-state"
            className="w-full bg-muted/20 border border-dashed border-border rounded-xl p-4 text-center space-y-2.5 animate-fade-in"
          >
            <div className="w-9 h-9 rounded-full bg-primary/10 text-primary flex items-center justify-center mx-auto">
              <Sprout className="w-4 h-4" />
            </div>
            <div>
              <p className="text-xs font-semibold text-foreground">
                No active operations for {selectedField ? selectedField.name : "this plot"}
              </p>
              <p className="text-[11px] text-muted-foreground mt-0.5 leading-relaxed">
                Add crops in Crop Advisor or schedule operational events in Crop Calendar to start tracking seasonal progress.
              </p>
            </div>
            <div className="flex flex-wrap items-center justify-center gap-2 pt-1">
              <Link href="/dashboard/crop-advisor">
                <Button size="sm" variant="outline" className="h-7 text-xs gap-1 bg-transparent hover:bg-primary/10">
                  <Plus className="w-3 h-3" />
                  Add Crop
                </Button>
              </Link>
              <Link href="/dashboard/calendar">
                <Button size="sm" variant="outline" className="h-7 text-xs gap-1 bg-transparent hover:bg-primary/10">
                  <CalendarIcon className="w-3 h-3" />
                  Schedule Event
                </Button>
              </Link>
            </div>
          </div>
        ) : (
          /* Meaningful Seasonal Stages & Milestones */
          <div className="w-full space-y-2 pt-2 border-t border-border">
            <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
              <span className="font-semibold text-foreground">Milestone Stages</span>
              <button
                type="button"
                onClick={() => setShowActivitiesList((p) => !p)}
                className="text-[11px] text-primary hover:underline flex items-center gap-0.5 font-medium"
              >
                {showActivitiesList ? "Hide Tasks" : `View Tasks (${totalCount})`}
                {showActivitiesList ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>
            </div>

            <div className="space-y-1.5">
              {stages.map((stage) => {
                const IconComponent = stage.icon
                const isCompleted = stage.status === "Completed"
                const isOverdue = stage.status === "Overdue"
                const isInProgress = stage.status === "In Progress"

                return (
                  <div
                    key={stage.key}
                    className="flex items-center justify-between p-2 rounded-lg bg-card/60 border border-border/80 hover:bg-muted/30 transition-all text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <div
                        className={`w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0 ${
                          isCompleted
                            ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                            : isOverdue
                            ? "bg-destructive/10 text-destructive"
                            : isInProgress
                            ? "bg-primary/10 text-primary"
                            : "bg-muted text-muted-foreground"
                        }`}
                      >
                        {isCompleted ? <Check className="w-3.5 h-3.5" /> : <IconComponent className="w-3.5 h-3.5" />}
                      </div>
                      <div>
                        <p className="font-medium text-foreground text-[11px]">{stage.name}</p>
                        <p className="text-[10px] text-muted-foreground">{stage.dateLabel}</p>
                      </div>
                    </div>

                    <Badge
                      variant="outline"
                      className={`text-[10px] px-1.5 py-0 border ${
                        isCompleted
                          ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/30"
                          : isOverdue
                          ? "bg-destructive/10 text-destructive border-destructive/30"
                          : isInProgress
                          ? "bg-primary/10 text-primary border-primary/30"
                          : "bg-muted/40 text-muted-foreground border-border"
                      }`}
                    >
                      {stage.status}
                    </Badge>
                  </div>
                )
              })}
            </div>

            {/* Collapsible Direct Task Checklist with Persistent Toggling */}
            {showActivitiesList && (
              <div className="mt-3 pt-2 border-t border-border space-y-1.5 max-h-56 overflow-y-auto pr-1 animate-fade-in">
                <p className="text-[11px] font-semibold text-foreground px-1">
                  Field Operations Checklist ({completedCount}/{totalCount})
                </p>
                {fieldEvents.map((ev) => (
                  <div
                    key={ev.id}
                    className="flex items-center justify-between p-2 rounded-md bg-secondary/30 hover:bg-secondary/60 border border-border text-xs transition-colors"
                  >
                    <div className="flex items-center gap-2 min-w-0 flex-1 mr-2">
                      <button
                        type="button"
                        onClick={() => handleToggleEvent(ev.id)}
                        disabled={togglingId === ev.id}
                        className={`w-4 h-4 rounded border flex items-center justify-center transition-colors flex-shrink-0 ${
                          ev.completed
                            ? "bg-emerald-600 border-emerald-600 text-white"
                            : "border-muted-foreground/50 hover:border-primary"
                        }`}
                        title={ev.completed ? "Mark pending" : "Mark completed"}
                      >
                        {ev.completed && <Check className="w-3 h-3 stroke-[3]" />}
                      </button>
                      <div className="min-w-0 flex-1">
                        <p
                          className={`text-[11px] font-medium truncate ${
                            ev.completed ? "line-through text-muted-foreground" : "text-foreground"
                          }`}
                        >
                          {ev.emoji} {ev.title}
                        </p>
                        <p className="text-[10px] text-muted-foreground">
                          {ev.crop} · {MONTH_SHORT[ev.month]} {ev.day}
                        </p>
                      </div>
                    </div>

                    <Badge variant="secondary" className="text-[9px] capitalize flex-shrink-0">
                      {ev.type}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  )
}
