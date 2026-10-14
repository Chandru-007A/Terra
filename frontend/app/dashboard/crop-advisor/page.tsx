"use client"

import { Sidebar } from "@/components/dashboard/dashboard/sidebar"
import { Header } from "@/components/dashboard/dashboard/header"
import { TasksContent } from "@/components/dashboard/tasks/tasks-content"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useState, useEffect } from "react"
import { toast } from "sonner"
import { useField } from "@/lib/field-context"
import { Sprout } from "lucide-react"

const KNOWN_CROPS = [
  { id: "onion", label: "Onion (Rabi)", sow: "Oct 25 – Nov 15", season: "Rabi" },
  { id: "wheat", label: "Wheat (Rabi)", sow: "Nov 1 – Nov 25", season: "Rabi" },
  { id: "chickpea", label: "Chickpea (Gram)", sow: "Oct 15 – Nov 10", season: "Rabi" },
  { id: "mustard", label: "Mustard (Rabi)", sow: "Oct 10 – Oct 31", season: "Rabi" },
  { id: "sorghum", label: "Sorghum (Rabi Jowar)", sow: "Oct 1 – Oct 20", season: "Rabi" },
  { id: "safflower", label: "Safflower", sow: "Oct 5 – Nov 5", season: "Rabi" },
  { id: "potato", label: "Potato (Rabi)", sow: "Oct 15 – Nov 15", season: "Rabi" },
  { id: "garlic", label: "Garlic (Rabi)", sow: "Oct 20 – Nov 15", season: "Rabi" },
  { id: "lentil", label: "Lentil (Masoor)", sow: "Oct 20 – Nov 15", season: "Rabi" },
  { id: "rice", label: "Rice (Kharif)", sow: "Jun 15 – Jul 10", season: "Kharif" },
  { id: "soybean", label: "Soybean (Kharif)", sow: "Jun 20 – Jul 15", season: "Kharif" },
  { id: "maize", label: "Maize (Kharif)", sow: "Jun 10 – Jul 5", season: "Kharif" },
  { id: "pigeonpea", label: "Pigeon pea (Arhar)", sow: "Jun 15 – Jul 15", season: "Kharif" },
  { id: "cotton", label: "Cotton (Kharif)", sow: "May 15 – Jun 15", season: "Kharif" },
  { id: "groundnut", label: "Groundnut (Kharif)", sow: "Jun 15 – Jul 10", season: "Kharif" },
  { id: "sugarcane", label: "Sugarcane", sow: "Year-round", season: "Year-round" },
  { id: "tomato", label: "Tomato", sow: "Year-round", season: "Year-round" },
  { id: "watermelon", label: "Watermelon (Zaid)", sow: "Jan 15 – Feb 15", season: "Zaid" },
  { id: "mungbean", label: "Green Gram (Mung)", sow: "Feb 15 – Mar 15", season: "Zaid" },
]

export default function CropAdvisorPage() {
  const { fields, selectedField, selectedFieldId, setSelectedFieldId, addCrop } = useField()
  const [addCropOpen, setAddCropOpen] = useState(false)
  const [targetFieldId, setTargetFieldId] = useState("")
  const [cropId, setCropId] = useState("")
  const [acres, setAcres] = useState("")
  const [season, setSeason] = useState("Rabi 2026-27")
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState(false)

  // Default to selected field or first field
  useEffect(() => {
    if (selectedField) {
      setTargetFieldId(selectedField.id)
    } else if (fields.length > 0 && (!targetFieldId || targetFieldId === "all")) {
      setTargetFieldId(fields[0].id)
    }
  }, [selectedField, fields, targetFieldId])

  const validate = () => {
    const errs: Record<string, string> = {}
    if (!targetFieldId || targetFieldId === "all") errs.targetFieldId = "Select a specific field"
    if (!cropId) errs.cropId = "Select a crop"
    if (!acres || isNaN(Number(acres)) || Number(acres) <= 0)
      errs.acres = "Enter valid area in acres (e.g. 2.0)"
    return errs
  }

  const handleAddCrop = async () => {
    const errs = validate()
    setErrors(errs)
    if (Object.keys(errs).length > 0) return
    setSaving(true)

    const cropObj = KNOWN_CROPS.find((c) => c.id === cropId)
    const fieldObj = fields.find((f) => f.id === targetFieldId)
    const fieldName = fieldObj?.name || "Field"

    try {
      await addCrop(targetFieldId, {
        cropId,
        name: cropObj?.label || cropId,
        acres: Number(acres),
        sow: cropObj?.sow || "Seasonal window",
        season,
        status: "in",
      })

      // Ensure view focuses on the target field
      if (selectedFieldId !== targetFieldId) {
        setSelectedFieldId(targetFieldId)
      }

      toast.success(`${cropObj?.label || cropId} added to ${fieldName} (${acres} acres)`)
      setCropId("")
      setAcres("")
      setErrors({})
      setAddCropOpen(false)
    } catch {
      // Toast displayed by context
    } finally {
      setSaving(false)
    }
  }

  const openAddCropModal = () => {
    if (selectedField && selectedField.id !== "all") {
      setTargetFieldId(selectedField.id)
    } else if (fields.length > 0) {
      setTargetFieldId(fields[0].id)
    }
    if (!cropId && KNOWN_CROPS.length > 0) {
      setCropId(KNOWN_CROPS[0].id)
    }
    if (!acres) {
      setAcres("2.0")
    }
    setErrors({})
    setAddCropOpen(true)
  }

  return (
    <div className="flex min-h-screen bg-background">
      <div className="hidden lg:block">
        <Sidebar />
      </div>

      <main className="flex-1 p-4 lg:p-6 lg:ml-64">
        <Header
          title="Crop Advisor"
          description="AI-powered crop recommendations tailored to your field's soil chemistry and weather."
          actions={
            <Button
              id="btn-add-crop-to-plan"
              className="w-full sm:w-auto h-9 text-sm bg-primary text-primary-foreground hover:bg-primary/90 transition-all duration-300 hover:shadow-lg hover:shadow-primary/30 hover:scale-105"
              onClick={openAddCropModal}
            >
              + Add Crop to Plan
            </Button>
          }
        />

        <div className="mt-6">
          <TasksContent onOpenAddCrop={openAddCropModal} />
        </div>
      </main>

      {/* Add Crop Modal */}
      <Dialog open={addCropOpen} onOpenChange={setAddCropOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sprout className="w-5 h-5 text-primary" />
              Add Crop to Field Plan
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            {/* Field selector */}
            <div className="space-y-1.5">
              <Label htmlFor="field-select">Target Farm Field *</Label>
              <Select value={targetFieldId} onValueChange={setTargetFieldId}>
                <SelectTrigger id="field-select">
                  <SelectValue placeholder="Select farm field" />
                </SelectTrigger>
                <SelectContent>
                  {fields.map((f) => (
                    <SelectItem key={f.id} value={f.id}>
                      {f.name} ({f.areaAcres} Acres · {f.soilType.split(" ")[0]})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.targetFieldId && <p className="text-xs text-destructive">{errors.targetFieldId}</p>}
            </div>

            {/* Crop selector */}
            <div className="space-y-1.5">
              <Label htmlFor="crop-select">Crop *</Label>
              <Select value={cropId} onValueChange={setCropId}>
                <SelectTrigger id="crop-select">
                  <SelectValue placeholder="Select crop" />
                </SelectTrigger>
                <SelectContent>
                  {KNOWN_CROPS.map((c) => (
                    <SelectItem key={c.id} value={c.id}>
                      {c.label} · {c.season}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.cropId && <p className="text-xs text-destructive">{errors.cropId}</p>}
            </div>

            {/* Area */}
            <div className="space-y-1.5">
              <Label htmlFor="crop-acres">Acreage Allocation *</Label>
              <Input
                id="crop-acres"
                type="number"
                placeholder="e.g. 3.0"
                min="0.1"
                step="0.1"
                value={acres}
                onChange={(e) => setAcres(e.target.value)}
              />
              {errors.acres && <p className="text-xs text-destructive">{errors.acres}</p>}
            </div>

            {/* Season */}
            <div className="space-y-1.5">
              <Label htmlFor="crop-season">Crop Season</Label>
              <Select value={season} onValueChange={setSeason}>
                <SelectTrigger id="crop-season">
                  <SelectValue placeholder="Select season" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Rabi 2026-27">Rabi 2026-27 (Winter)</SelectItem>
                  <SelectItem value="Kharif 2026">Kharif 2026 (Monsoon)</SelectItem>
                  <SelectItem value="Zaid 2026">Zaid 2026 (Summer)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <p className="text-xs text-muted-foreground">
              This crop plan will be persisted against the selected field and factored into resource budgeting and optimizer models.
            </p>
          </div>
          <DialogFooter className="gap-2">
            <Button id="btn-cancel-crop" variant="outline" onClick={() => setAddCropOpen(false)}>Cancel</Button>
            <Button id="btn-save-crop" onClick={handleAddCrop} disabled={saving}>
              {saving ? "Saving…" : "Save Crop"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}