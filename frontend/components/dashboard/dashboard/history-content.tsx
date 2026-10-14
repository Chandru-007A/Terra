"use client"

import { useEffect, useState, useCallback } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Save, History, Download, Trash2, RefreshCw, Sprout } from "lucide-react"
import { getHistory, addPlan, deletePlan, type Plan } from "@/lib/history"
import { useAuth } from "@/components/auth/AuthProvider"
import { useField } from "@/lib/field-context"
import { toast } from "sonner"

export function HistoryContent() {
  const { user } = useAuth()
  const { fields, selectedField, selectedFieldId, setSelectedFieldId } = useField()
  const [plans, setPlans] = useState<Plan[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const loadHistory = useCallback(async () => {
    if (!user) return
    setLoading(true)
    const fieldFilterId = selectedFieldId === "all" ? undefined : selectedFieldId
    const history = await getHistory(user.id, fieldFilterId)
    setPlans(history)
    setLoading(false)
  }, [user, selectedFieldId])

  useEffect(() => {
    if (user) {
      loadHistory()
    }
  }, [user, selectedFieldId, loadHistory])

  const handleSaveCurrentPlan = async () => {
    if (!user) {
      toast.error("Please log in to save a plan")
      return
    }
    setSaving(true)

    const activeLand = selectedField ? selectedField.areaAcres : 10
    const activeWater = selectedField ? selectedField.waterAvailableKl : 16000
    const activeFert = selectedField ? selectedField.fertilizerAvailableKg : 1000
    const activeBudget = selectedField ? selectedField.budgetInr : 400000
    const activeCropIds =
      selectedField && selectedField.crops && selectedField.crops.length > 0
        ? selectedField.crops.map((c) => c.cropId.toLowerCase())
        : ["onion", "wheat", "chickpea", "mustard"]

    let currentCrops = [
      { name: "Onion", acres: 3 },
      { name: "Wheat", acres: 3 },
      { name: "Chickpea", acres: 3 },
      { name: "Mustard", acres: 1 },
    ]
    let profit = "₹4.04L"
    let waterSaved = "27%"
    let fertilizerSaved = "22%"

    try {
      const { apiOptimizeAllocation } = await import("@/lib/api")
      const opt = await apiOptimizeAllocation({
        crop_ids: activeCropIds,
        total_land_acres: activeLand,
        water_available_kl: activeWater,
        fertilizer_available_kg: activeFert,
        total_budget_inr: activeBudget,
        strategy: "balanced",
      })
      if (opt && opt.crops) {
        currentCrops = opt.crops.map((c) => ({ name: c.name, acres: c.acres }))
        profit = opt.expected_profit_str || profit
        waterSaved = opt.water_saved_str || waterSaved
        fertilizerSaved = opt.fertilizer_saved_str || fertilizerSaved
      }
    } catch {}

    try {
      await addPlan(user.id, {
        fieldId: selectedField?.id,
        fieldName: selectedField?.name || "All Fields",
        season: "Rabi 2026-27",
        strategy: "Balanced",
        crops: currentCrops,
        profit,
        waterSaved,
        fertilizerSaved,
        status: "Current",
      })
      toast.success(`Plan saved to history for ${selectedField?.name || "your farm"}`)
      await loadHistory()
    } catch {
      toast.error("Failed to save plan. Please try again.")
    }
    setSaving(false)
  }

  const handleDelete = async (planId: string, season: string) => {
    if (!user) return
    setDeletingId(planId)
    try {
      await deletePlan(user.id, planId)
      setPlans((prev) => prev.filter((p) => p.id !== planId))
      toast.success(`Plan "${season}" removed`)
    } catch {
      toast.error("Failed to delete plan")
    }
    setDeletingId(null)
  }

  const handleExportPlan = (plan: Plan) => {
    const fieldName = plan.fieldName || "All Fields"
    const csvRows = [
      ["Terra Farm Plan Export"],
      ["Generated", new Date().toLocaleString()],
      ["Farm Field", fieldName],
      [],
      ["Season", plan.season],
      ["Strategy", plan.strategy],
      ["Status", plan.status],
      ["Expected Profit", plan.profit],
      ["Water Saved", plan.waterSaved],
      ["Fertilizer Saved", plan.fertilizerSaved],
      [],
      ["Crop Allocations"],
      ["Crop Name", "Acres"],
      ...plan.crops.map((c) => [c.name, String(c.acres)]),
    ]
    const csv = csvRows.map((r) => r.join(",")).join("\n")
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    const slug = (plan.fieldName || "terra").toLowerCase().replace(/\s+/g, "-")
    a.download = `terra-${slug}-plan-${plan.season.replace(/\s+/g, "-")}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    toast.success(`Exported: ${plan.season} (${fieldName})`)
  }

  const getStatusBadge = (status: "Current" | "Completed") => (
    <Badge variant={status === "Current" ? "default" : "secondary"} className="text-xs whitespace-nowrap">
      {status}
    </Badge>
  )

  const formatCrops = (crops: { name: string; acres: number }[]) =>
    crops.map((c) => `${c.name} (${c.acres}ac)`).join(" · ")

  if (loading) {
    return (
      <div className="space-y-6 animate-fade-in max-w-5xl">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-lg">Plan History</h3>
            <p className="text-sm text-muted-foreground">Your past season plans and how they performed.</p>
          </div>
        </div>
        <div className="animate-pulse space-y-4">
          {[1, 2, 3].map((i) => <div key={i} className="h-14 bg-muted rounded-lg" />)}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-5xl">
      {/* Field Filter Strip */}
      <Card className="p-4 bg-card border-border flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Sprout className="w-5 h-5 text-primary flex-shrink-0" />
          <div>
            <h3 className="font-semibold text-sm text-foreground">
              {selectedField ? `Showing Plans for ${selectedField.name}` : "All Fields History"}
            </h3>
            <p className="text-xs text-muted-foreground">
              {selectedField
                ? `Filtered to records saved under ${selectedField.name}`
                : "Complete record of all seasonal plans across your farm"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 flex-wrap">
          <Button
            size="sm"
            variant={selectedFieldId === "all" ? "default" : "outline"}
            className="text-xs h-7 px-2.5"
            onClick={() => setSelectedFieldId("all")}
          >
            All Fields
          </Button>
          {fields.map((f) => (
            <Button
              key={f.id}
              size="sm"
              variant={selectedFieldId === f.id ? "default" : "outline"}
              className="text-xs h-7 px-2.5"
              onClick={() => setSelectedFieldId(f.id)}
            >
              {f.name}
            </Button>
          ))}
        </div>
      </Card>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h3 className="font-semibold text-lg">Plan History</h3>
          <p className="text-sm text-muted-foreground">
            {plans.length} plan{plans.length === 1 ? "" : "s"} on record.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={loadHistory} className="gap-1.5">
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </Button>
          <Button onClick={handleSaveCurrentPlan} disabled={saving} className="gap-2">
            <Save className="w-4 h-4" />
            {saving ? "Saving…" : "Save current plan"}
          </Button>
        </div>
      </div>

      {plans.length === 0 ? (
        <Card className="p-8 text-center">
          <History className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
          <h4 className="font-medium text-lg mb-2">No plans recorded</h4>
          <p className="text-sm text-muted-foreground mb-4">
            {selectedField
              ? `No plans saved for ${selectedField.name} yet. Apply a strategy in Compare Strategies or save the current plan.`
              : "Your saved plans will appear here. Use \"Save current plan\" or apply a strategy in Compare Strategies."}
          </p>
          <Button onClick={handleSaveCurrentPlan} disabled={saving} className="gap-2">
            <Save className="w-4 h-4" />
            {saving ? "Saving…" : "Save your first plan"}
          </Button>
        </Card>
      ) : (
        <div className="space-y-3">
          {plans.map((plan) => (
            <Card key={plan.id} className="p-4 hover:shadow-md transition-all duration-200">
              <div className="flex flex-col gap-3">
                {/* Top row: season + field + strategy + status */}
                <div className="flex flex-wrap items-center gap-2 justify-between">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-foreground">{plan.season}</span>
                    {plan.fieldName && (
                      <Badge variant="secondary" className="text-xs bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                        🌱 {plan.fieldName}
                      </Badge>
                    )}
                    <Badge variant="outline" className="text-xs">{plan.strategy}</Badge>
                    {getStatusBadge(plan.status)}
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7"
                      title={`Export ${plan.season}`}
                      onClick={() => handleExportPlan(plan)}
                    >
                      <Download className="w-3.5 h-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-destructive hover:text-destructive"
                      title={`Delete ${plan.season}`}
                      disabled={deletingId === plan.id}
                      onClick={() => handleDelete(plan.id, plan.season)}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </div>

                {/* Crops row */}
                <p className="text-xs text-muted-foreground leading-relaxed">
                  <span className="font-medium text-foreground/80">Crops: </span>
                  {formatCrops(plan.crops)}
                </p>

                {/* Metrics row */}
                <div className="flex flex-wrap gap-4 text-sm">
                  <span className="font-bold text-primary">{plan.profit}</span>
                  <span className="text-emerald-600 dark:text-emerald-400 font-medium">
                    💧 {plan.waterSaved} water saved
                  </span>
                  <span className="text-blue-600 dark:text-blue-400 font-medium">
                    🌿 {plan.fertilizerSaved} fertilizer saved
                  </span>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}