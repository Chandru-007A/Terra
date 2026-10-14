"use client"

import { Sidebar } from "@/components/dashboard/dashboard/sidebar"
import { Header } from "@/components/dashboard/dashboard/header"
import { TeamContent } from "@/components/dashboard/team/team-content"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useState, useEffect } from "react"
import { toast } from "sonner"
import { useField } from "@/lib/field-context"
import { Droplets, Sparkles, Wallet, Sprout } from "lucide-react"

export default function ResourcesPage() {
  const { fields, selectedField, updateField } = useField()
  const [addOpen, setAddOpen] = useState(false)
  const [targetFieldId, setTargetFieldId] = useState("")
  const [resType, setResType] = useState("water")
  const [quantity, setQuantity] = useState("")
  const [unit, setUnit] = useState("kL")
  const [notes, setNotes] = useState("")
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (selectedField) {
      setTargetFieldId(selectedField.id)
    } else if (fields.length > 0 && !targetFieldId) {
      setTargetFieldId(fields[0].id)
    }
  }, [selectedField, fields, targetFieldId])

  const RESOURCE_TYPES = [
    { id: "water", label: "Irrigation Water", defaultUnit: "kL", units: ["kL", "L", "m³"] },
    { id: "fertilizer_npk", label: "Fertilizer (NPK)", defaultUnit: "kg", units: ["kg", "bags"] },
    { id: "fertilizer_urea", label: "Urea", defaultUnit: "kg", units: ["kg", "bags"] },
    { id: "budget", label: "Working Capital / Budget", defaultUnit: "₹", units: ["₹", "Lakhs"] },
    { id: "pesticide", label: "Pesticide", defaultUnit: "L", units: ["L", "kg"] },
    { id: "seeds", label: "Seeds", defaultUnit: "kg", units: ["kg", "packets"] },
  ]

  const selectedType = RESOURCE_TYPES.find((r) => r.id === resType)

  const validate = () => {
    const errs: Record<string, string> = {}
    if (!targetFieldId) errs.targetFieldId = "Select a field"
    if (!resType) errs.resType = "Select a resource type"
    if (!quantity || isNaN(Number(quantity)) || Number(quantity) <= 0)
      errs.quantity = "Enter a valid positive quantity"
    if (!unit) errs.unit = "Select a unit"
    return errs
  }

  const handleAdd = async () => {
    const errs = validate()
    setErrors(errs)
    if (Object.keys(errs).length > 0) return
    setSaving(true)

    const targetField = fields.find((f) => f.id === targetFieldId)
    if (!targetField) {
      toast.error("Target field not found")
      setSaving(false)
      return
    }

    const qtyNum = Number(quantity)
    const updatePayload: Record<string, number> = {}

    // Unit conversion and field-specific persistence
    if (resType === "water") {
      let kl = qtyNum
      if (unit === "L") kl = qtyNum / 1000
      if (unit === "m³") kl = qtyNum // 1 m³ = 1 kL
      updatePayload.waterAvailableKl = (targetField.waterAvailableKl || 0) + kl
    } else if (resType === "fertilizer_npk" || resType === "fertilizer_urea") {
      let kg = qtyNum
      if (unit === "bags") kg = qtyNum * 50 // standard 50kg bag
      updatePayload.fertilizerAvailableKg = (targetField.fertilizerAvailableKg || 0) + kg
    } else if (resType === "budget") {
      let inr = qtyNum
      if (unit === "Lakhs") inr = qtyNum * 100000
      updatePayload.budgetInr = (targetField.budgetInr || 0) + inr
    }

    try {
      await updateField(targetFieldId, updatePayload)
      toast.success(
        `${selectedType?.label} added to ${targetField.name}: ${quantity} ${unit}${notes ? ` (${notes})` : ""}`
      )
      setQuantity("")
      setNotes("")
      setErrors({})
      setAddOpen(false)
    } catch {
      // Toast displayed in context
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="flex min-h-screen bg-background">
      <div className="hidden lg:block">
        <Sidebar />
      </div>

      <main className="flex-1 p-4 lg:p-6 lg:ml-64">
        <Header
          title="Resources"
          description="Monitor and allocate water, fertilizer, and working capital scoped per farm field."
          actions={
            <Button
              className="w-full sm:w-auto h-9 text-sm bg-primary text-primary-foreground hover:bg-primary/90 transition-all duration-300 hover:shadow-lg hover:shadow-primary/30 hover:scale-105"
              onClick={() => setAddOpen(true)}
            >
              + Add Resource
            </Button>
          }
        />

        <div className="mt-6">
          <TeamContent />
        </div>
      </main>

      {/* Add Resource Modal */}
      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Add Field Resource Quantity</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            {/* Target Field */}
            <div className="space-y-1.5">
              <Label>Farm Field *</Label>
              <Select value={targetFieldId} onValueChange={setTargetFieldId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select field" />
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

            {/* Resource Type */}
            <div className="space-y-1.5">
              <Label>Resource Type *</Label>
              <Select
                value={resType}
                onValueChange={(v) => {
                  setResType(v)
                  const t = RESOURCE_TYPES.find((r) => r.id === v)
                  if (t) setUnit(t.defaultUnit)
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select resource type" />
                </SelectTrigger>
                <SelectContent>
                  {RESOURCE_TYPES.map((r) => (
                    <SelectItem key={r.id} value={r.id}>{r.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.resType && <p className="text-xs text-destructive">{errors.resType}</p>}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>Quantity to Add *</Label>
                <Input
                  type="number"
                  placeholder="e.g. 1000"
                  min="0.1"
                  step="any"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                />
                {errors.quantity && <p className="text-xs text-destructive">{errors.quantity}</p>}
              </div>
              <div className="space-y-1.5">
                <Label>Unit *</Label>
                <Select value={unit} onValueChange={setUnit}>
                  <SelectTrigger>
                    <SelectValue placeholder="Unit" />
                  </SelectTrigger>
                  <SelectContent>
                    {(selectedType?.units ?? ["kL", "kg", "units"]).map((u) => (
                      <SelectItem key={u} value={u}>{u}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.unit && <p className="text-xs text-destructive">{errors.unit}</p>}
              </div>
            </div>

            <div className="space-y-1.5">
              <Label>Notes (optional)</Label>
              <Input
                placeholder="e.g. Pre-monsoon canal supply, Urea bag batch"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setAddOpen(false)}>Cancel</Button>
            <Button onClick={handleAdd} disabled={saving}>
              {saving ? "Saving…" : "Save Resource"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}