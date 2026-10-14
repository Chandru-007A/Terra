"use client"

import { useState, useEffect, useCallback } from "react"
import { useRouter } from "next/navigation"
import {
  Bell,
  CheckCheck,
  Check,
  X,
  RefreshCw,
  Settings,
  CloudRain,
  Sun,
  Wind,
  Droplets,
  Sprout,
  Scissors,
  Sparkles,
  Calendar,
  AlertTriangle,
  Info,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import {
  AppNotification,
  apiGetNotifications,
  apiMarkNotificationAsRead,
  apiMarkAllNotificationsAsRead,
  apiDismissNotification,
  apiDismissAllNotifications,
  apiGetWeatherStatus,
  WeatherStatus,
  showBrowserNotification,
} from "@/lib/notifications"
import { toast } from "sonner"

export function NotificationCenter() {
  const router = useRouter()
  const [open, setOpen] = useState(false)
  const [notifications, setNotifications] = useState<AppNotification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [totalCount, setTotalCount] = useState(0)
  const [weatherStatus, setWeatherStatus] = useState<WeatherStatus | null>(null)
  const [activeTab, setActiveTab] = useState<"all" | "crop_reminder" | "weather_alert" | "unread">("all")
  const [loading, setLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  const fetchNotifications = useCallback(async (isManual = false) => {
    if (isManual) setRefreshing(true)
    try {
      const res = await apiGetNotifications({ autoSync: true })
      setNotifications(res.notifications || [])
      setUnreadCount(res.unreadCount || 0)
      setTotalCount(res.totalCount || 0)

      // Also get weather status
      try {
        const ws = await apiGetWeatherStatus()
        setWeatherStatus(ws)
      } catch {}
    } catch (err) {
      // Offline fallback: keep existing notifications
    } finally {
      if (isManual) setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    fetchNotifications()
    // Poll safely every 60 seconds while app is open
    const interval = setInterval(() => {
      fetchNotifications()
    }, 60000)
    return () => clearInterval(interval)
  }, [fetchNotifications])

  const handleMarkAsRead = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    try {
      await apiMarkNotificationAsRead(id)
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, read: true } : n))
      )
      setUnreadCount((c) => Math.max(0, c - 1))
    } catch {
      toast.error("Failed to mark as read")
    }
  }

  const handleMarkAllRead = async () => {
    try {
      await apiMarkAllNotificationsAsRead()
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))
      setUnreadCount(0)
      toast.success("All notifications marked as read")
    } catch {
      toast.error("Failed to mark all as read")
    }
  }

  const handleDismiss = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    try {
      await apiDismissNotification(id)
      setNotifications((prev) => {
        const target = prev.find((n) => n.id === id)
        if (target && !target.read) {
          setUnreadCount((c) => Math.max(0, c - 1))
        }
        return prev.filter((n) => n.id !== id)
      })
      setTotalCount((c) => Math.max(0, c - 1))
    } catch {
      toast.error("Failed to dismiss notification")
    }
  }

  const handleDismissAll = async () => {
    try {
      await apiDismissAllNotifications()
      setNotifications([])
      setUnreadCount(0)
      setTotalCount(0)
      toast.success("All notifications dismissed")
    } catch {
      toast.error("Failed to dismiss notifications")
    }
  }

  const handleNotificationClick = async (notif: AppNotification) => {
    if (!notif.read) {
      try {
        await apiMarkNotificationAsRead(notif.id)
        setNotifications((prev) =>
          prev.map((n) => (n.id === notif.id ? { ...n, read: true } : n))
        )
        setUnreadCount((c) => Math.max(0, c - 1))
      } catch {}
    }
    setOpen(false)
    if (notif.linkUrl) {
      router.push(notif.linkUrl)
    }
  }

  const filteredList = notifications.filter((n) => {
    if (activeTab === "unread") return !n.read
    if (activeTab === "crop_reminder") return n.type === "crop_reminder"
    if (activeTab === "weather_alert") return n.type === "weather_alert"
    return true
  })

  const getNotificationIcon = (n: AppNotification) => {
    if (n.type === "weather_alert") {
      const cond = n.metadata?.condition || ""
      if (cond.includes("Rain")) return <CloudRain className="w-4 h-4 text-cyan-400" />
      if (cond.includes("Heat")) return <Sun className="w-4 h-4 text-amber-500" />
      if (cond.includes("Wind")) return <Wind className="w-4 h-4 text-purple-400" />
      if (cond.includes("Dry")) return <Droplets className="w-4 h-4 text-orange-400" />
      return <AlertTriangle className="w-4 h-4 text-amber-500" />
    }
    const t = n.metadata?.event_type || ""
    if (t === "harvest") return <Scissors className="w-4 h-4 text-green-500" />
    if (t === "irrigation") return <Droplets className="w-4 h-4 text-cyan-500" />
    if (t === "fertilizer") return <Sparkles className="w-4 h-4 text-purple-400" />
    return <Sprout className="w-4 h-4 text-emerald-500" />
  }

  const formatRelativeTime = (isoString: string) => {
    if (!isoString) return ""
    try {
      const d = new Date(isoString)
      const diffMs = Date.now() - d.getTime()
      const diffMins = Math.floor(diffMs / 60000)
      if (diffMins < 1) return "Just now"
      if (diffMins < 60) return `${diffMins}m ago`
      const diffHours = Math.floor(diffMins / 60)
      if (diffHours < 24) return `${diffHours}h ago`
      const diffDays = Math.floor(diffHours / 24)
      return `${diffDays}d ago`
    } catch {
      return ""
    }
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          id="terra-notification-bell-btn"
          aria-label="Farm Notifications"
          className="relative hover:bg-secondary transition-all duration-300 hover:scale-105 h-8 w-8"
        >
          <Bell className="w-4 h-4 text-foreground" />
          {unreadCount > 0 ? (
            <span
              id="terra-unread-notification-badge"
              className="absolute -top-1 -right-1 bg-destructive text-destructive-foreground text-[10px] font-bold h-4 min-w-[16px] px-1 rounded-full flex items-center justify-center animate-pulse"
            >
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          ) : (
            <span className="sr-only">No unread notifications</span>
          )}
        </Button>
      </PopoverTrigger>

      <PopoverContent
        align="end"
        sideOffset={8}
        className="w-[92vw] sm:w-[420px] p-0 shadow-2xl border-border bg-card/95 backdrop-blur-md rounded-xl overflow-hidden"
      >
        {/* Header */}
        <div className="p-3.5 border-b border-border bg-secondary/30 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-sm text-foreground">Notifications</span>
            {unreadCount > 0 ? (
              <Badge variant="destructive" className="text-[10px] h-4.5 px-1.5">
                {unreadCount} unread
              </Badge>
            ) : (
              <Badge variant="outline" className="text-[10px] h-4.5 px-1.5 text-muted-foreground">
                All caught up
              </Badge>
            )}
          </div>

          <div className="flex items-center gap-1">
            {unreadCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleMarkAllRead}
                title="Mark all as read"
                className="h-7 text-xs px-2 text-muted-foreground hover:text-foreground"
              >
                <CheckCheck className="w-3.5 h-3.5 mr-1 text-primary" />
                Mark read
              </Button>
            )}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => fetchNotifications(true)}
              title="Refresh alerts"
              className="h-7 w-7 text-muted-foreground hover:text-foreground"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
            </Button>
          </div>
        </div>

        {/* Live Weather Provider Disclosures */}
        {weatherStatus && (
          <div className="px-3.5 py-1.5 bg-primary/5 border-b border-border/50 text-[11px] text-muted-foreground flex items-center justify-between">
            <span className="flex items-center gap-1.5 truncate">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Live Weather: <strong className="text-foreground font-medium">Open-Meteo WMO API</strong>
            </span>
            <span className="text-[10px] text-muted-foreground shrink-0">
              {weatherStatus.monitoredLocations.length > 0
                ? weatherStatus.monitoredLocations.join(", ")
                : "Nashik"}
            </span>
          </div>
        )}

        {/* Filter Tabs */}
        <div className="flex items-center gap-1 p-2 border-b border-border/60 bg-muted/20">
          <Button
            variant={activeTab === "all" ? "secondary" : "ghost"}
            size="sm"
            onClick={() => setActiveTab("all")}
            className="text-xs h-7 px-2.5 rounded-md"
          >
            All ({totalCount})
          </Button>
          <Button
            variant={activeTab === "crop_reminder" ? "secondary" : "ghost"}
            size="sm"
            onClick={() => setActiveTab("crop_reminder")}
            className="text-xs h-7 px-2.5 rounded-md gap-1"
          >
            🌱 Reminders
          </Button>
          <Button
            variant={activeTab === "weather_alert" ? "secondary" : "ghost"}
            size="sm"
            onClick={() => setActiveTab("weather_alert")}
            className="text-xs h-7 px-2.5 rounded-md gap-1"
          >
            ⛅ Weather
          </Button>
          {unreadCount > 0 && (
            <Button
              variant={activeTab === "unread" ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setActiveTab("unread")}
              className="text-xs h-7 px-2.5 rounded-md text-primary font-medium"
            >
              Unread ({unreadCount})
            </Button>
          )}
        </div>

        {/* Notification List */}
        <div className="max-h-[360px] overflow-y-auto divide-y divide-border/50">
          {filteredList.length === 0 ? (
            <div className="p-8 text-center space-y-2">
              <div className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center mx-auto text-muted-foreground">
                <Bell className="w-5 h-5 opacity-60" />
              </div>
              <p className="text-sm font-medium text-foreground">No notifications</p>
              <p className="text-xs text-muted-foreground max-w-[240px] mx-auto">
                {activeTab === "all"
                  ? "You have no active alerts or reminders right now."
                  : `No ${activeTab.replace("_", " ")}s found.`}
              </p>
            </div>
          ) : (
            filteredList.map((notif) => (
              <div
                key={notif.id}
                onClick={() => handleNotificationClick(notif)}
                className={`
                  p-3.5 transition-colors cursor-pointer relative group flex items-start gap-3
                  ${notif.read ? "hover:bg-secondary/40 opacity-80" : "bg-primary/5 hover:bg-primary/10"}
                `}
              >
                {/* Type Icon */}
                <div
                  className={`
                    w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border
                    ${
                      notif.type === "weather_alert"
                        ? "bg-amber-500/10 border-amber-500/30"
                        : "bg-emerald-500/10 border-emerald-500/30"
                    }
                  `}
                >
                  {getNotificationIcon(notif)}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0 space-y-1">
                  <div className="flex items-center justify-between gap-1.5">
                    <p
                      className={`text-xs font-semibold truncate ${
                        notif.read ? "text-foreground/90" : "text-foreground"
                      }`}
                    >
                      {notif.title}
                    </p>
                    <span className="text-[10px] text-muted-foreground shrink-0">
                      {formatRelativeTime(notif.createdAt)}
                    </span>
                  </div>

                  <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
                    {notif.message}
                  </p>

                  {/* Context Badges */}
                  <div className="flex flex-wrap items-center gap-1.5 pt-1">
                    {notif.fieldName && (
                      <Badge variant="outline" className="text-[10px] h-4 px-1.5 bg-secondary/50">
                        {notif.fieldName}
                      </Badge>
                    )}
                    {notif.cropName && (
                      <Badge variant="outline" className="text-[10px] h-4 px-1.5 border-primary/30 text-primary">
                        {notif.cropName}
                      </Badge>
                    )}
                    {notif.metadata?.condition && (
                      <Badge variant="secondary" className="text-[10px] h-4 px-1.5">
                        {notif.metadata.condition}
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Item Actions */}
                <div className="flex items-center gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                  {!notif.read && (
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={(e) => handleMarkAsRead(e, notif.id)}
                      title="Mark as read"
                      className="h-6 w-6 text-muted-foreground hover:text-primary"
                    >
                      <Check className="w-3.5 h-3.5" />
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => handleDismiss(e, notif.id)}
                    title="Dismiss"
                    className="h-6 w-6 text-muted-foreground hover:text-destructive"
                  >
                    <X className="w-3.5 h-3.5" />
                  </Button>
                </div>

                {/* Unread dot */}
                {!notif.read && (
                  <span className="absolute left-1 top-4 w-1.5 h-1.5 rounded-full bg-primary" />
                )}
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="p-2.5 border-t border-border bg-secondary/20 flex items-center justify-between text-xs">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setOpen(false)
              router.push("/dashboard/settings")
            }}
            className="h-7 text-xs text-muted-foreground hover:text-foreground gap-1.5"
          >
            <Settings className="w-3.5 h-3.5" />
            Preferences
          </Button>

          {notifications.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDismissAll}
              className="h-7 text-[11px] text-muted-foreground hover:text-destructive"
            >
              Clear all
            </Button>
          )}
        </div>
      </PopoverContent>
    </Popover>
  )
}
