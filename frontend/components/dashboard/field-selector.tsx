"use client"

import { useState } from "react"
import { useField } from "@/lib/field-context"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  SelectSeparator,
} from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Sprout, Plus, Layers, MapPin } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"

interface FieldSelectorProps {
  allowAll?: boolean
  className?: string
}

export function FieldSelector({ allowAll = true, className = "" }: FieldSelectorProps) {
  const { fields, selectedFieldId, selectedField, setSelectedFieldId, createField } = useField()
  const [modalOpen, setModalOpen] = useState(false)
  const [name, setName] = useState("")
  const [area, setArea] = useState("")
  const [soilType, setSoilType] = useState("Black Cotton (Vertisol)")
  const [location, setLocation] = useState("Nashik, Maharashtra")
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState(false)

  const validate = () => {
    const errs: Record<string, string> = {}
    if (!name.trim()) errs.name = "Field name is required"
    if (!area.trim() || isNaN(Number(area)) || Number(area) <= 0)
      errs.area = "Enter valid acreage (> 0)"
    if (!soilType) errs.soilType = "Select soil type"
    if (!location.trim()) errs.location = "Enter location"
    return errs
  }

  const handleSaveField = async () => {
    const errs = validate()
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
      // toast shown in context
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <div className={`flex items-center gap-2 ${className}`}>
        <Select
          value={selectedFieldId}
          onValueChange={(val) => {
            if (val === "__add_new__") {
              setModalOpen(true)
            } else {
              setSelectedFieldId(val as string | "all")
            }
          }}
        >
          <SelectTrigger className="h-9 min-w-[190px] max-w-[260px] text-xs font-medium bg-card border-border hover:bg-secondary/40 transition-colors">
            <div className="flex items-center gap-2 truncate">
              {selectedFieldId === "all" ? (
                <>
                  <Layers className="w-3.5 h-3.5 text-primary flex-shrink-0" />
                  <span className="truncate">All Fields ({fields.length})</span>
                </>
              ) : selectedField ? (
                <>
                  <Sprout className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
                  <span className="truncate font-semibold">{selectedField.name}</span>
                  <Badge variant="outline" className="text-[10px] py-0 px-1 font-normal ml-auto">
                    {selectedField.areaAcres}ac
                  </Badge>
                </>
              ) : (
                <>
                  <Sprout className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
                  <span className="text-muted-foreground">Select Field</span>
                </>
              )}
            </div>
          </SelectTrigger>
          <SelectContent className="max-w-[280px]">
            {allowAll && (
              <SelectItem value="all" className="text-xs">
                <div className="flex items-center gap-2">
                  <Layers className="w-3.5 h-3.5 text-primary" />
                  <span>All Fields ({fields.length} plots)</span>
                </div>
              </SelectItem>
            )}

            {fields.map((f) => (
              <SelectItem key={f.id} value={f.id} className="text-xs">
                <div className="flex items-center justify-between gap-3 w-full">
                  <div className="flex items-center gap-1.5 truncate">
                    <Sprout className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
                    <span className="font-medium truncate">{f.name}</span>
                  </div>
                  <span className="text-[10px] text-muted-foreground whitespace-nowrap">
                    {f.areaAcres} ac · {f.soilType.split(" ")[0]}
                  </span>
                </div>
              </SelectItem>
            ))}

            <SelectSeparator />
            <SelectItem value="__add_new__" className="text-xs text-primary font-medium focus:text-primary">
              <div className="flex items-center gap-1.5">
                <Plus className="w-3.5 h-3.5" />
                <span>+ Add New Field...</span>
              </div>
            </SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Reusable Add Field Modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sprout className="w-5 h-5 text-primary" />
              Add New Farm Field
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-1.5">
              <Label htmlFor="selector-field-name">Field Name *</Label>
              <Input
                id="selector-field-name"
                placeholder="e.g. North Field, South Field"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
              {errors.name && <p className="text-xs text-destructive">{errors.name}</p>}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="selector-field-area">Area (Acres) *</Label>
              <Input
                id="selector-field-area"
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
              <Label htmlFor="selector-field-soil">Soil Type *</Label>
              <Select value={soilType} onValueChange={setSoilType}>
                <SelectTrigger id="selector-field-soil">
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
              {errors.soilType && <p className="text-xs text-destructive">{errors.soilType}</p>}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="selector-field-location">Location / District *</Label>
              <Input
                id="selector-field-location"
                placeholder="e.g. Nashik, Maharashtra"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
              />
              {errors.location && <p className="text-xs text-destructive">{errors.location}</p>}
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveField} disabled={saving}>
              {saving ? "Saving…" : "Save Field"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
