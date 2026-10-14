"use client"

import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Check,
  Save,
  Sprout,
  Info,
} from "lucide-react"
import { useState, useEffect } from "react"
import { apiCompareStrategies, type ApiAllocationResult } from "@/lib/api"
import { addPlan } from "@/lib/history"
import { useAuth } from "@/components/auth/AuthProvider"
import { useField } from "@/lib/field-context"
import { toast } from "sonner"

export function AnalyticsContent() {
  const { user } = useAuth()
  const { fields, selectedField, selectedFieldId, setSelectedFieldId, updateField } = useField()
  const [strategies, setStrategies] = useState<ApiAllocationResult[]>([])
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  const activeLand = selectedField ? selectedField.areaAcres : 10
  const activeWater = selectedField ? selectedField.waterAvailableKl : 16000
  const activeFert = selectedField ? selectedField.fertilizerAvailableKg : 1000
  const activeBudget = selectedField ? selectedField.budgetInr : 400000
  const activeCropIds =
    selectedField && selectedField.crops && selectedField.crops.length > 0
      ? selectedField.crops.map((c) => c.cropId.toLowerCase())
      : ["onion", "wheat", "chickpea", "mustard"]

  useEffect(() => {
    let isMounted = true
    async function loadStrategies() {
      try {
        setLoading(true)
        const res = await apiCompareStrategies({
          crop_ids: activeCropIds,
          total_land_acres: activeLand,
          water_available_kl: activeWater,
          fertilizer_available_kg: activeFert,
          total_budget_inr: activeBudget,
        })
        if (isMounted && res && res.strategies && res.strategies.length > 0) {
          setStrategies(res.strategies)
          // If field has an active strategy, pre-select it
          if (selectedField?.activeStrategy) {
            const idx = res.strategies.findIndex((s) => s.strategy === selectedField.activeStrategy)
            if (idx >= 0) setSelectedIndex(idx)
          }
        }
      } catch {
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    loadStrategies()
    return () => {
      isMounted = false
    }
  }, [selectedField, activeLand, activeWater, activeFert, activeBudget])

  const currentStrategies: ApiAllocationResult[] = strategies

  const activeStrat = currentStrategies[selectedIndex] || currentStrategies[0]

  const strategyDescriptions: Record<string, string> = {
    Balanced:
      "Multi-objective compromise: blends high-margin crops with water-saving pulses to spread economic risk and protect groundwater.",
    "Max Profit":
      "Commercial focus: concentrates acreage on the highest revenue crop (Onion) up to soil and irrigation capacity bounds.",
    "Water Saver":
      "Drought-resilient focus: minimizes seasonal water consumption by prioritizing deep-rooted pulses and oilseeds with guaranteed income floors.",
    "Low Budget":
      "Working capital conservation: minimizes upfront cultivation cash requirements while maintaining positive profit margins.",
  }

  const handleApplyStrategy = async () => {
    if (!user) {
      toast.error("Please log in to apply this strategy")
      return
    }
    if (!activeStrat) {
      toast.error("No strategy selected")
      return
    }
    setSaving(true)
    try {
      const planPayload = {
        fieldId: selectedField?.id,
        fieldName: selectedField?.name || "All Fields",
        season: "Rabi 2026-27",
        strategy: activeStrat.strategy,
        crops: activeStrat.crops.map((c) => ({ name: c.name, acres: c.acres })),
        profit: activeStrat.expected_profit_str,
        waterSaved: activeStrat.water_saved_str,
        fertilizerSaved: activeStrat.fertilizer_saved_str,
        status: "Current" as const,
      }
      await addPlan(user.id, planPayload)

      if (selectedField) {
        await updateField(selectedField.id, {
          activeStrategy: activeStrat.strategy,
        })
      }

      toast.success(
        `${activeStrat.strategy} strategy applied as active plan for ${selectedField?.name || "your farm"}!`
      )
    } catch {
      toast.error("Failed to apply plan")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Field Selector Banner */}
      <Card className="p-4 bg-card border-border flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Sprout className="w-5 h-5 text-primary flex-shrink-0" />
          <div>
            <h3 className="font-semibold text-sm text-foreground">
              {selectedField ? `Strategy optimization for ${selectedField.name}` : "Farm-wide Strategy Comparison"}
            </h3>
            <p className="text-xs text-muted-foreground">
              {selectedField
                ? `Input bounds: ${selectedField.areaAcres} Acres · ${selectedField.waterAvailableKl.toLocaleString()} kL water · ₹${(selectedField.budgetInr / 100000).toFixed(2)}L capital`
                : "Aggregated simulation across all farm acreage"}
            </p>
          </div>
        </div>

        {/* Quick field toggle */}
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
              className="text-xs h-7 px-2.5 gap-1"
              onClick={() => setSelectedFieldId(f.id)}
            >
              {f.name}
              {selectedFieldId === f.id && <Check className="w-3 h-3 ml-0.5" />}
            </Button>
          ))}
        </div>
      </Card>

      {/* Strategy Selector Tabs */}
      {currentStrategies.length === 0 ? (
        <Card className="p-8 text-center text-sm text-muted-foreground">
          {loading ? "Calculating linear programming allocations with SciPy..." : "No strategies available."}
        </Card>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {currentStrategies.map((strat, idx) => {
            const isSelected = selectedIndex === idx
            const isActiveSaved = selectedField?.activeStrategy === strat.strategy
            return (
              <Card
                key={strat.strategy}
                onClick={() => setSelectedIndex(idx)}
                className={`p-4 cursor-pointer transition-all duration-300 border ${
                  isSelected
                    ? "border-primary bg-primary/5 shadow-xl scale-105"
                    : "border-border hover:bg-secondary/40 hover:scale-102"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-1">
                    <Badge variant={isSelected ? "default" : "outline"} className="text-xs">
                      {strat.strategy}
                    </Badge>
                    {isActiveSaved && (
                      <Badge variant="secondary" className="text-[10px] bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
                        Active
                      </Badge>
                    )}
                  </div>
                  {isSelected && <Check className="w-4 h-4 text-primary" />}
                </div>
                <p className="text-2xl font-bold text-foreground mb-1">
                  {strat.expected_profit_str}
                </p>
                <div className="text-xs text-muted-foreground flex justify-between">
                  <span>Water saved: <strong className="text-primary">{strat.water_saved_str}</strong></span>
                  <span>Budget: {strat.budget_used_str}</span>
                </div>
              </Card>
            )
          })}
        </div>
      )}

      {/* Selected Strategy Deep-Dive */}
      {activeStrat && (
        <Card className="p-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-border">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h3 className="text-xl font-bold text-foreground">
                  {activeStrat.strategy} Strategy Overview
                </h3>
                <Badge variant="secondary" className="text-xs">
                  {activeStrat.status}
                </Badge>
                {selectedField?.activeStrategy === activeStrat.strategy && (
                  <Badge className="text-xs bg-emerald-600 text-white">
                    Currently Active on {selectedField.name}
                  </Badge>
                )}
              </div>
              <p className="text-xs text-muted-foreground max-w-2xl leading-relaxed">
                {strategyDescriptions[activeStrat.strategy] ||
                  "Optimized multi-resource agricultural planning."}
              </p>
            </div>

            <Button
              onClick={handleApplyStrategy}
              disabled={saving}
              className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90"
            >
              <Save className="w-4 h-4" />
              {saving ? "Applying..." : "Apply as Active Plan"}
            </Button>
          </div>

          {/* Crops Acreage Breakdown */}
          <div className="mt-6 space-y-4">
            <h4 className="font-semibold text-sm text-foreground">
              Recommended Land Allocation ({activeStrat.total_land_allocated_acres} Acres Scoped for {selectedField ? selectedField.name : "Farm"})
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              {activeStrat.crops.map((c) => (
                <div
                  key={c.crop_id}
                  className="p-3.5 rounded-lg border border-border bg-card/60 hover:shadow-md transition-all space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-2xl">{c.emoji}</span>
                    <Badge variant="outline" className="text-[10px]">
                      {c.acres} Acres
                    </Badge>
                  </div>
                  <div>
                    <h5 className="font-semibold text-sm text-foreground">{c.name}</h5>
                    <p className="text-xs text-primary font-medium">{c.formatted_profit} profit</p>
                  </div>
                  <div className="text-[11px] text-muted-foreground border-t border-border/50 pt-1.5 flex justify-between">
                    <span>Yield: {c.expected_yield_q} q</span>
                    <span>Water: {c.water_used_kl} kL</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>
      )}

      {/* Side-by-Side Comparison Matrix */}
      {currentStrategies.length > 0 && (
        <Card className="p-6">
          <h4 className="font-semibold text-base text-foreground mb-4">
            Strategy Comparison Matrix ({selectedField ? selectedField.name : "All Fields"})
          </h4>
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="text-[11px] uppercase bg-muted/30 text-muted-foreground border-b border-border">
                <tr>
                  <th className="py-3 px-4">Strategy</th>
                  <th className="py-3 px-4">Expected Profit</th>
                  <th className="py-3 px-4">Water Saved</th>
                  <th className="py-3 px-4">Fertilizer Saved</th>
                  <th className="py-3 px-4">Production</th>
                  <th className="py-3 px-4">Budget Required</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {currentStrategies.map((strat, i) => (
                  <tr
                    key={strat.strategy}
                    onClick={() => setSelectedIndex(i)}
                    className={`cursor-pointer transition-colors ${
                      selectedIndex === i ? "bg-primary/10 font-semibold" : "hover:bg-secondary/40"
                    }`}
                  >
                    <td className="py-3.5 px-4 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-primary" />
                      {strat.strategy}
                    </td>
                    <td className="py-3.5 px-4 font-bold text-foreground">{strat.expected_profit_str}</td>
                    <td className="py-3.5 px-4 text-primary font-semibold">{strat.water_saved_str}</td>
                    <td className="py-3.5 px-4 text-emerald-600 dark:text-emerald-400 font-semibold">{strat.fertilizer_saved_str}</td>
                    <td className="py-3.5 px-4">{strat.expected_production_str}</td>
                    <td className="py-3.5 px-4 text-muted-foreground">{strat.budget_used_str}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  )
}
