"use client"

import { Card } from "@/components/ui/card"
import { Plus, Sprout, Check } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useField } from "@/lib/field-context"
import { Badge } from "@/components/ui/badge"
import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { toast } from "sonner"

export function ProjectList() {
  const { fields, selectedFieldId, setSelectedFieldId, createField } = useField()
  const [modalOpen, setModalOpen] = useState(false)
  const [name, setName] = useState("")
  const [area, setArea] = useState("")
  const [soilType, setSoilType] = useState("Black Cotton (Vertisol)")
  const [location, setLocation] = useState("Nashik, Maharashtra")
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState(false)

  const handleAddPlot = async () => {
    const errs: Record<string, string> = {}
    if (!name.trim()) errs.name = "Field name is required"
    if (!area.trim() || isNaN(Number(area)) || Number(area) <= 0) errs.area = "Valid area required"
    setErrors(errs)
    if (Object.keys(errs).length > 0) return

    setSaving(true)
    try {
      const created = await createField({
        name: name.trim(),
        areaAcres: Number(area),
        soilType,
        location: location.trim(),
      })
      toast.success(`Field "${created.name}" created (${created.areaAcres} acres)`)
      setName("")
      setArea("")
      setErrors({})
      setModalOpen(false)
    } catch {
    } finally {
      setSaving(false)
    }
  }

  const plotColors = ["bg-emerald-600", "bg-rose-500", "bg-amber-600", "bg-cyan-600", "bg-indigo-600"]
  const plotIcons = ["🌾", "🧅", "🫘", "🌼", "🌱"]

  return (
    <>
      <Card
        className="p-6 transition-all duration-500 hover:shadow-xl animate-slide-in-up"
        style={{ animationDelay: "700ms" }}
      >
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-foreground">Farm Field Plots</h2>
            <p className="text-xs text-muted-foreground">Select a plot to view and scope analytics</p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setModalOpen(true)}
            className="transition-all duration-300 hover:scale-105 bg-transparent"
          >
            <Plus className="w-4 h-4 mr-1" />
            New Plot
          </Button>
        </div>

        {fields.length === 0 ? (
          <div className="text-center py-6 border border-dashed border-border rounded-xl">
            <Sprout className="w-8 h-8 mx-auto text-muted-foreground mb-2" />
            <p className="text-sm font-medium text-foreground">No farm fields created</p>
            <p className="text-xs text-muted-foreground mb-3">Add your first plot to track soil and crops</p>
            <Button size="sm" onClick={() => setModalOpen(true)}>
              + Add Field
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            {fields.map((field, index) => {
              const isSelected = selectedFieldId === field.id
              const color = plotColors[index % plotColors.length]
              const icon = plotIcons[index % plotIcons.length]
              return (
                <div
                  key={field.id}
                  onClick={() => setSelectedFieldId(field.id)}
                  className={`flex items-center gap-3 p-3 rounded-lg border transition-all duration-300 cursor-pointer group ${
                    isSelected
                      ? "border-primary bg-primary/10 shadow-sm"
                      : "border-border/60 hover:bg-secondary"
                  }`}
                  style={{ animationDelay: `${800 + index * 100}ms` }}
                >
                  <div
                    className={`${color} w-10 h-10 rounded-lg flex items-center justify-center text-xl text-white transition-transform duration-300 group-hover:scale-110 group-hover:rotate-6 flex-shrink-0`}
                  >
                    {icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <p className="font-semibold text-foreground text-sm truncate">{field.name}</p>
                      {isSelected && <Check className="w-3.5 h-3.5 text-primary flex-shrink-0" />}
                    </div>
                    <p className="text-xs text-muted-foreground truncate">
                      {field.areaAcres} Acres · {field.soilType.split(" ")[0]}
                      {field.crops && field.crops.length > 0 ? ` · ${field.crops.length} crop(s)` : ""}
                    </p>
                  </div>
                  <Badge variant={isSelected ? "default" : "outline"} className="text-[10px] whitespace-nowrap">
                    {isSelected ? "Active" : `${field.areaAcres} ac`}
                  </Badge>
                </div>
              )
            })}
          </div>
        )}
      </Card>

      {/* New Plot Modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Add New Field Plot</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-1.5">
              <Label>Plot / Field Name *</Label>
              <Input
                placeholder="e.g. North Field, South Field"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
              {errors.name && <p className="text-xs text-destructive">{errors.name}</p>}
            </div>
            <div className="space-y-1.5">
              <Label>Area (Acres) *</Label>
              <Input
                type="number"
                placeholder="e.g. 5.0"
                min="0.1"
                step="0.1"
                value={area}
                onChange={(e) => setArea(e.target.value)}
              />
              {errors.area && <p className="text-xs text-destructive">{errors.area}</p>}
            </div>
            <div className="space-y-1.5">
              <Label>Soil Type *</Label>
              <Select value={soilType} onValueChange={setSoilType}>
                <SelectTrigger>
                  <SelectValue />
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
            </div>
            <div className="space-y-1.5">
              <Label>Location / Village *</Label>
              <Input
                value={location}
                onChange={(e) => setLocation(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button onClick={handleAddPlot} disabled={saving}>
              {saving ? "Saving…" : "Save Plot"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
