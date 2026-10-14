"use client"

import { useState, useRef, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Sun, Moon, Laptop } from "lucide-react"
import { useTheme } from "@/components/theme-provider"
import { useAuth } from "@/components/auth/AuthProvider"
import {
  apiGetNotificationPreferences,
  apiUpdateNotificationPreferences,
  apiGetWeatherStatus,
  requestBrowserNotificationPermission,
  WeatherStatus,
  NotificationPreferences,
} from "@/lib/notifications"
import { toast } from "sonner"

export function SettingsContent() {
  const { theme, resolvedTheme, setTheme } = useTheme()
  const { user, updateProfile } = useAuth()
  const photoInputRef = useRef<HTMLInputElement>(null)
  const [themeMounted, setThemeMounted] = useState(false)

  useEffect(() => {
    setThemeMounted(true)
  }, [])

  const [name, setName] = useState(user?.name || "")
  const [email, setEmail] = useState(user?.email || "")
  const [village, setVillage] = useState(user?.village || "")
  const [district, setDistrict] = useState(user?.district || "")
  const [farmSizeAcres, setFarmSizeAcres] = useState(user?.farmSizeAcres?.toString() || "")
  const [soilType, setSoilType] = useState(user?.soilType || "")
  const [language, setLanguage] = useState(user?.language || "English")
  const [saving, setSaving] = useState(false)
  const [photoUrl, setPhotoUrl] = useState<string | null>(null)

  // Notification Preferences State
  const [prefs, setPrefs] = useState<NotificationPreferences>({
    emailNotifications: true,
    pushNotifications: true,
    cropReminders: true,
    weatherAlerts: true,
    reminderDaysBefore: 2,
    heavyRainThresholdMm: 35.0,
    extremeHeatThresholdC: 36.0,
    drySpellDaysThreshold: 5,
  })
  const [weatherStatus, setWeatherStatus] = useState<WeatherStatus | null>(null)
  const [permissionState, setPermissionState] = useState<string>("default")

  useEffect(() => {
    if (typeof window !== "undefined" && "Notification" in window) {
      setPermissionState(Notification.permission)
    }

    apiGetNotificationPreferences()
      .then((data) => {
        if (data) setPrefs(data)
      })
      .catch(() => {})

    apiGetWeatherStatus()
      .then((ws) => {
        if (ws) setWeatherStatus(ws)
      })
      .catch(() => {})
  }, [])

  const handleTogglePref = async (key: keyof NotificationPreferences, value: boolean) => {
    if (key === "pushNotifications" && value) {
      const perm = await requestBrowserNotificationPermission()
      setPermissionState(perm)
      if (perm === "denied") {
        toast.warning(
          "Browser notifications blocked. Please allow notifications in your browser site permissions."
        )
      } else if (perm === "granted") {
        toast.success("Browser push notifications permission granted!")
      }
    }

    const updated = { ...prefs, [key]: value }
    setPrefs(updated)
    try {
      await apiUpdateNotificationPreferences({ [key]: value })
      toast.success(
        `${
          key === "cropReminders"
            ? "Crop reminders"
            : key === "weatherAlerts"
            ? "Weather alerts"
            : key === "pushNotifications"
            ? "Push notifications"
            : "Email notifications"
        } ${value ? "enabled" : "disabled"}`
      )
    } catch {
      toast.error("Failed to update notification preference")
    }
  }

  const handleSave = async () => {
    setSaving(true)
    const result = await updateProfile({
      name: name.trim() || undefined,
      village: village.trim() || undefined,
      district: district.trim() || undefined,
      farmSizeAcres: farmSizeAcres ? Number(farmSizeAcres) : undefined,
      soilType: soilType.trim() || undefined,
      language: language.trim() || undefined,
    })
    setSaving(false)

    if ("error" in result) {
      toast.error(result.error)
    } else {
      toast.success("Profile updated successfully")
    }
  }

  const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (file.size > 2 * 1024 * 1024) {
      toast.error("Photo must be smaller than 2 MB")
      return
    }
    if (!file.type.startsWith("image/")) {
      toast.error("Please select a valid image file (JPG, PNG, GIF)")
      return
    }
    const reader = new FileReader()
    reader.onload = (ev) => {
      setPhotoUrl(ev.target?.result as string)
      toast.success("Profile photo updated")
    }
    reader.readAsDataURL(file)
  }

  const initials = user?.name
    ?.split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2) || "FP"

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl">
      <Card className="p-6">
        <h3 className="font-semibold text-lg mb-6">Profile Information</h3>
        <div className="space-y-6">
          <div className="flex items-center gap-4">
            <Avatar className="w-20 h-20">
              {photoUrl ? (
                <AvatarImage src={photoUrl} alt={user?.name || "User"} />
              ) : user?.name ? (
                <AvatarFallback className="text-2xl">{initials}</AvatarFallback>
              ) : (
                <AvatarImage src="/profile.jpg" alt={user?.name || "User"} />
              )}
            </Avatar>
            <div>
              <input
                ref={photoInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handlePhotoChange}
              />
              <Button variant="outline" onClick={() => photoInputRef.current?.click()}>
                Change Photo
              </Button>
              <p className="text-xs text-muted-foreground mt-2">JPG, PNG or GIF. Max size 2MB</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name">Full Name</Label>
              <Input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" disabled />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="village">Village</Label>
              <Input id="village" value={village} onChange={(e) => setVillage(e.target.value)} placeholder="Nashik" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="district">District</Label>
              <Input id="district" value={district} onChange={(e) => setDistrict(e.target.value)} placeholder="Maharashtra" />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="farmSizeAcres">Farm Size (acres)</Label>
              <Input id="farmSizeAcres" type="number" value={farmSizeAcres} onChange={(e) => setFarmSizeAcres(e.target.value)} placeholder="10" min="0" step="0.1" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="soilType">Soil Type</Label>
              <Input id="soilType" value={soilType} onChange={(e) => setSoilType(e.target.value)} placeholder="Black cotton soil" />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="language">Language</Label>
            <Input id="language" value={language} onChange={(e) => setLanguage(e.target.value)} placeholder="English" />
          </div>

          <Button className="bg-primary hover:bg-primary/90" onClick={handleSave} disabled={saving}>
            {saving ? "Saving..." : "Save Changes"}
          </Button>
        </div>
      </Card>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-lg text-foreground">Notifications</h3>
          {weatherStatus && (
            <Badge variant="outline" className="text-xs py-1 border-primary/30 text-primary">
              Live Weather: Open-Meteo
            </Badge>
          )}
        </div>

        <div className="space-y-4">
          {/* Email Notifications */}
          <div className="flex items-center justify-between py-3 border-b border-border">
            <div>
              <p className="font-medium text-foreground">Email notifications</p>
              <p className="text-sm text-muted-foreground">Receive email about your account activity</p>
            </div>
            <Switch
              checked={prefs.emailNotifications}
              onCheckedChange={(checked) => handleTogglePref("emailNotifications", checked)}
            />
          </div>

          {/* Push Notifications */}
          <div className="flex items-center justify-between py-3 border-b border-border">
            <div>
              <div className="flex items-center gap-2">
                <p className="font-medium text-foreground">Push notifications</p>
                {permissionState === "granted" && (
                  <Badge variant="secondary" className="text-[10px] text-emerald-600 bg-emerald-500/10">
                    Browser Allowed
                  </Badge>
                )}
                {permissionState === "denied" && (
                  <Badge variant="destructive" className="text-[10px]">
                    Blocked
                  </Badge>
                )}
              </div>
              <p className="text-sm text-muted-foreground">Receive push notifications in your browser</p>
            </div>
            <Switch
              checked={prefs.pushNotifications}
              onCheckedChange={(checked) => handleTogglePref("pushNotifications", checked)}
            />
          </div>

          {/* Crop Reminders */}
          <div className="flex items-center justify-between py-3 border-b border-border">
            <div>
              <p className="font-medium text-foreground">Crop reminders</p>
              <p className="text-sm text-muted-foreground">Get reminded about sowing and harvest dates</p>
            </div>
            <Switch
              checked={prefs.cropReminders}
              onCheckedChange={(checked) => handleTogglePref("cropReminders", checked)}
            />
          </div>

          {/* Weather Alerts */}
          <div className="flex items-center justify-between py-3 border-b border-border last:border-0">
            <div>
              <p className="font-medium text-foreground">Weather alerts</p>
              <p className="text-sm text-muted-foreground">Notifications about weather changes affecting crops</p>
            </div>
            <Switch
              checked={prefs.weatherAlerts}
              onCheckedChange={(checked) => handleTogglePref("weatherAlerts", checked)}
            />
          </div>
        </div>

        <div className="mt-4 p-3 bg-secondary/30 rounded-lg text-xs text-muted-foreground border border-border/60">
          <p className="font-medium text-foreground mb-1">ℹ️ Delivery & Weather Information</p>
          <p>
            In-app alerts update automatically while the application is open. Weather alerts use verified live meteorological forecasts from <strong>Open-Meteo</strong> with hourly cache refresh.
          </p>
        </div>
      </Card>

      <Card className="p-6">
        <h3 className="font-semibold text-lg mb-4 text-foreground">Appearance</h3>
        <p className="text-xs text-muted-foreground mb-4">
          Customize Terra's interface theme. Your preference is persisted across browser refreshes and login sessions.
        </p>

        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-3.5 rounded-lg border border-border bg-secondary/20">
            <div>
              <p className="font-medium text-foreground">Dark Mode</p>
              <p className="text-sm text-muted-foreground">
                Current theme: <strong className="text-foreground capitalize">{themeMounted ? (theme || "system") : "loading…"}</strong>
                {themeMounted && theme === "system" && resolvedTheme ? ` (${resolvedTheme} active)` : ""}
              </p>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1 p-1 bg-secondary/60 rounded-lg border border-border">
                <Button
                  id="theme-btn-light"
                  type="button"
                  variant={theme === "light" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => {
                    setTheme("light")
                    toast.success("Theme set to Light")
                  }}
                  className="text-xs h-7 gap-1 px-2.5"
                >
                  <Sun className="w-3.5 h-3.5" /> Light
                </Button>
                <Button
                  id="theme-btn-dark"
                  type="button"
                  variant={theme === "dark" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => {
                    setTheme("dark")
                    toast.success("Theme set to Dark")
                  }}
                  className="text-xs h-7 gap-1 px-2.5"
                >
                  <Moon className="w-3.5 h-3.5" /> Dark
                </Button>
                <Button
                  id="theme-btn-system"
                  type="button"
                  variant={theme === "system" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => {
                    setTheme("system")
                    toast.success("Theme set to System preference")
                  }}
                  className="text-xs h-7 gap-1 px-2.5"
                >
                  <Laptop className="w-3.5 h-3.5" /> System
                </Button>
              </div>

              <Switch
                id="theme-switch"
                checked={themeMounted && (resolvedTheme === "dark" || theme === "dark")}
                onCheckedChange={(checked) => {
                  const next = checked ? "dark" : "light"
                  setTheme(next)
                  toast.success(`Theme switched to ${checked ? "Dark" : "Light"}`)
                }}
                aria-label="Toggle dark mode"
              />
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}