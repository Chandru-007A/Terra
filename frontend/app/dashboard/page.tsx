"use client"

import { Sidebar } from "@/components/dashboard/dashboard/sidebar"
import { Header } from "@/components/dashboard/dashboard/header"
import { StatsCards } from "@/components/dashboard/dashboard/stats-cards"
import { ProjectAnalytics } from "@/components/dashboard/dashboard/project-analytics"
import { Reminders } from "@/components/dashboard/dashboard/reminders"
import { ProjectList } from "@/components/dashboard/dashboard/project-list"
import { TeamCollaboration } from "@/components/dashboard/dashboard/team-collaboration"
import { ProjectProgress } from "@/components/dashboard/dashboard/project-progress"
import { MobileAppCard } from "@/components/dashboard/dashboard/mobile-app-card"
import { TimeTracker } from "@/components/dashboard/dashboard/time-tracker"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useState } from "react"
import { toast } from "sonner"
import { getHistory } from "@/lib/history"
import { useAuth } from "@/components/auth/AuthProvider"
import { useField } from "@/lib/field-context"

export default function DashboardPage() {
  const { user } = useAuth()
  const { fields, selectedField, createField } = useField()
  const [addFieldOpen, setAddFieldOpen] = useState(false)
  const [newField, setNewField] = useState({ name: "", area: "", soilType: "Black Cotton (Vertisol)", location: "Nashik, Maharashtra" })
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [savingField, setSavingField] = useState(false)
  const [exportLoading, setExportLoading] = useState(false)

  const validateField = () => {
    const errs: Record<string, string> = {}
    if (!newField.name.trim()) errs.name = "Field name is required"
    if (!newField.area.trim() || isNaN(Number(newField.area)) || Number(newField.area) <= 0)
      errs.area = "Enter a valid area in acres (e.g. 5.0)"
    if (!newField.soilType) errs.soilType = "Select a soil type"
    if (!newField.location.trim()) errs.location = "Enter village/district"
    return errs
  }

  const handleAddField = async () => {
    const errs = validateField()
    setFieldErrors(errs)
    if (Object.keys(errs).length > 0) return
    setSavingField(true)
    try {
      const created = await createField({
        name: newField.name.trim(),
        areaAcres: Number(newField.area),
        soilType: newField.soilType,
        location: newField.location.trim(),
      })
      setNewField({ name: "", area: "", soilType: "Black Cotton (Vertisol)", location: "Nashik, Maharashtra" })
      setFieldErrors({})
      setAddFieldOpen(false)
      toast.success(`Field "${created.name}" created (${created.areaAcres} acres, ${created.soilType})`)
    } catch {
      // toast shown in context
    } finally {
      setSavingField(false)
    }
  }

  const handleExportPlan = async () => {
    if (!user) {
      toast.error("Please log in to export your plan")
      return
    }
    setExportLoading(true)
    try {
      // Fetch plans for selected field if one is selected, else all plans
      const plans = await getHistory(user.id, selectedField?.id)
      if (!plans || plans.length === 0) {
        // If no plans for this specific field, check all user plans
        const allPlans = await getHistory(user.id)
        if (!allPlans || allPlans.length === 0) {
          toast.error("No saved plans to export. Apply a strategy first.")
          setExportLoading(false)
          return
        }
        var latest = allPlans[0]
      } else {
        var latest = plans[0]
      }

      const fieldLabel = latest.fieldName || selectedField?.name || "All Fields"
      const csvRows = [
        ["Terra Farm Plan Export"],
        ["Generated", new Date().toLocaleString()],
        ["Farm Field", fieldLabel],
        ...(selectedField ? [
          ["Field Area", `${selectedField.areaAcres} Acres`],
          ["Soil Profile", selectedField.soilType],
          ["Location", selectedField.location],
        ] : []),
        [],
        ["Season", latest.season],
        ["Strategy", latest.strategy],
        ["Status", latest.status],
        ["Expected Profit", latest.profit],
        ["Water Saved", latest.waterSaved],
        ["Fertilizer Saved", latest.fertilizerSaved],
        [],
        ["Crop Allocations"],
        ["Crop Name", "Acres"],
        ...latest.crops.map((c) => [c.name, String(c.acres)]),
      ]
      const csvContent = csvRows.map((r) => r.join(",")).join("\n")
      const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" })
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      const slug = (latest.fieldName || "terra").toLowerCase().replace(/\s+/g, "-")
      a.download = `terra-${slug}-plan-${latest.season.replace(/\s+/g, "-")}.csv`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      toast.success(`Exported plan for ${fieldLabel}: ${latest.season}`)
    } catch {
      toast.error("Export failed. Please try again.")
    }
    setExportLoading(false)
  }

  return (
    <div className="flex min-h-screen bg-background">
      <div className="hidden lg:block">
        <Sidebar />
      </div>

      <main className="flex-1 p-3 md:p-4 lg:p-5 lg:ml-64">
        <Header
          actions={
            <>
              <Button
                className="w-full sm:w-auto h-9 text-sm bg-primary text-primary-foreground hover:bg-primary/90 transition-all duration-300 hover:shadow-lg hover:shadow-primary/30 hover:scale-105"
                onClick={() => setAddFieldOpen(true)}
              >
                + Add Field
              </Button>
              <Button
                variant="outline"
                className="w-full sm:w-auto h-9 text-sm transition-all duration-300 hover:shadow-md hover:scale-105 bg-transparent"
                onClick={handleExportPlan}
                disabled={exportLoading}
              >
                {exportLoading ? "Exporting…" : "Export Plan"}
              </Button>
            </>
          }
        />

        <div className="mt-4 md:mt-5 space-y-3 md:space-y-4">
          <StatsCards />

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 md:gap-4">
            <div className="lg:col-span-2 space-y-3 md:space-y-4">
              <ProjectAnalytics />
              <TeamCollaboration />
            </div>

            <div className="space-y-3 md:space-y-4">
              <Reminders />
              <ProjectProgress />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 md:gap-4">
            <ProjectList />
            <MobileAppCard />
            <TimeTracker />
          </div>
        </div>
      </main>

      {/* Add Field Modal */}
      <Dialog open={addFieldOpen} onOpenChange={setAddFieldOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Add New Field</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-1.5">
              <Label htmlFor="field-name">Field Name *</Label>
              <Input
                id="field-name"
                placeholder="e.g. North Plateau, Khet 1"
                value={newField.name}
                onChange={(e) => setNewField((p) => ({ ...p, name: e.target.value }))}
              />
              {fieldErrors.name && <p className="text-xs text-destructive">{fieldErrors.name}</p>}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="field-area">Area (Acres) *</Label>
              <Input
                id="field-area"
                type="number"
                placeholder="e.g. 2.5"
                min="0.1"
                step="0.1"
                value={newField.area}
                onChange={(e) => setNewField((p) => ({ ...p, area: e.target.value }))}
              />
              {fieldErrors.area && <p className="text-xs text-destructive">{fieldErrors.area}</p>}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="field-soil">Soil Type *</Label>
              <Select
                value={newField.soilType}
                onValueChange={(v) => setNewField((p) => ({ ...p, soilType: v }))}
              >
                <SelectTrigger id="field-soil">
                  <SelectValue placeholder="Select soil type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Black Cotton (Vertisol)">Black Cotton (Vertisol)</SelectItem>
                  <SelectItem value="Red Laterite">Red Laterite</SelectItem>
                  <SelectItem value="Alluvial">Alluvial</SelectItem>
                  <SelectItem value="Sandy Loam">Sandy Loam</SelectItem>
                  <SelectItem value="Clay Loam">Clay Loam</SelectItem>
                  <SelectItem value="Saline/Alkaline">Saline/Alkaline</SelectItem>
                </SelectContent>
              </Select>
              {fieldErrors.soilType && <p className="text-xs text-destructive">{fieldErrors.soilType}</p>}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="field-location">Village / District *</Label>
              <Input
                id="field-location"
                placeholder="e.g. Nashik, Maharashtra"
                value={newField.location}
                onChange={(e) => setNewField((p) => ({ ...p, location: e.target.value }))}
              />
              {fieldErrors.location && <p className="text-xs text-destructive">{fieldErrors.location}</p>}
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setAddFieldOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddField} disabled={savingField}>
              {savingField ? "Adding…" : "Add Field"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}