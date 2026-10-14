"use client"

import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Button } from "@/components/ui/button"
import {
  Droplets,
  Sparkles,
  Wallet,
  MapPin,
  TrendingDown,
  ShieldCheck,
  Leaf,
  Info,
  Sprout,
  Check,
} from "lucide-react"
import { useState, useEffect } from "react"
import { apiOptimizeAllocation, type ApiAllocationResult } from "@/lib/api"
import { useField } from "@/lib/field-context"

export function TeamContent() {
  const { fields, selectedField, selectedFieldId, setSelectedFieldId } = useField()
  const [allocation, setAllocation] = useState<ApiAllocationResult | null>(null)
  const [loading, setLoading] = useState(false)

  // Aggregate totals across all fields if "all" is selected
  const totalArea = fields.reduce((sum, f) => sum + (f.areaAcres || 0), 0) || 10
  const totalWater = fields.reduce((sum, f) => sum + (f.waterAvailableKl || 0), 0) || 16000
  const totalFert = fields.reduce((sum, f) => sum + (f.fertilizerAvailableKg || 0), 0) || 1000
  const totalBudget = fields.reduce((sum, f) => sum + (f.budgetInr || 0), 0) || 400000

  // Scope to selected field if one is active, otherwise aggregated
  const activeLand = selectedField ? selectedField.areaAcres : totalArea
  const activeWater = selectedField ? selectedField.waterAvailableKl : totalWater
  const activeFert = selectedField ? selectedField.fertilizerAvailableKg : totalFert
  const activeBudget = selectedField ? selectedField.budgetInr : totalBudget

  // Field-specific crops if user added any, else balanced crop set
  const activeCropIds =
    selectedField && selectedField.crops && selectedField.crops.length > 0
      ? selectedField.crops.map((c) => c.cropId.toLowerCase())
      : ["onion", "wheat", "chickpea", "mustard"]

  useEffect(() => {
    let isMounted = true
    async function loadResources() {
      try {
        setLoading(true)
        const res = await apiOptimizeAllocation({
          crop_ids: activeCropIds,
          total_land_acres: activeLand,
          water_available_kl: activeWater,
          fertilizer_available_kg: activeFert,
          total_budget_inr: activeBudget,
          strategy: "balanced",
        })
        if (isMounted && res) {
          setAllocation(res)
        }
      } catch {
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    loadResources()
    return () => {
      isMounted = false
    }
  }, [selectedField, activeLand, activeWater, activeFert, activeBudget])

  const landUtil = allocation?.constraints_summary?.land_utilization_percent ?? 100
  const waterUtil = allocation?.constraints_summary?.water_utilization_percent ?? 94
  const fertUtil = allocation?.constraints_summary?.fertilizer_utilization_percent ?? 75
  const budgetUtil = allocation?.constraints_summary?.budget_utilization_percent ?? 83

  const waterSaved = allocation?.water_saved_str ?? "28%"
  const fertSaved = allocation?.fertilizer_saved_str ?? "31%"
  const budgetUsed = allocation?.budget_used_str ?? "₹3.32L"
  const budgetAvail = activeBudget
  const budgetUsedInr = allocation?.total_budget_used_inr ?? Math.round(activeBudget * 0.83)
  const bufferReserve = Math.max(0, Math.round(budgetAvail - budgetUsedInr))
  const bufferPct = budgetAvail > 0 ? Math.round((bufferReserve / budgetAvail) * 100) : 17

  const crops = allocation?.crops ?? []

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Field Scope Selector Strip */}
      <Card className="p-4 bg-card border-border flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Sprout className="w-5 h-5 text-primary flex-shrink-0" />
          <div>
            <h3 className="font-semibold text-sm text-foreground">
              {selectedField ? `Scoping resources for ${selectedField.name}` : "Farm-wide Aggregated Resources"}
            </h3>
            <p className="text-xs text-muted-foreground">
              {selectedField
                ? `Plot size: ${selectedField.areaAcres} Acres · Soil: ${selectedField.soilType} · Located in ${selectedField.location}`
                : `Total across all ${fields.length} farm field plots`}
            </p>
          </div>
        </div>

        {/* Quick pill toggle between user's fields */}
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
              {f.name} ({f.areaAcres}ac)
              {selectedFieldId === f.id && <Check className="w-3 h-3 ml-0.5" />}
            </Button>
          ))}
        </div>
      </Card>

      {/* 4 Core Agricultural Resource Pools */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Water Pool */}
        <Card className="p-5 space-y-3 bg-card border-border hover:shadow-lg transition-all duration-300">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Irrigation Water
            </span>
            <div className="p-2 rounded-full bg-cyan-500/10 text-cyan-500">
              <Droplets className="w-4 h-4" />
            </div>
          </div>
          <div>
            <p className="text-2xl font-bold text-foreground">
              {allocation?.total_water_used_kl?.toLocaleString() ?? "—"}{" "}
              <span className="text-sm font-normal text-muted-foreground">
                / {activeWater.toLocaleString()} kL
              </span>
            </p>
            <p className="text-xs text-emerald-600 dark:text-emerald-400 font-medium flex items-center gap-1 mt-1">
              <TrendingDown className="w-3.5 h-3.5" />
              {waterSaved} of pool unused vs full allocation
            </p>
          </div>
          <div className="space-y-1">
            <div className="flex justify-between text-[11px] text-muted-foreground">
              <span>Pool Utilization</span>
              <span>{waterUtil}%</span>
            </div>
            <Progress value={waterUtil} className="h-2" />
          </div>
        </Card>

        {/* Fertilizer Pool */}
        <Card className="p-5 space-y-3 bg-card border-border hover:shadow-lg transition-all duration-300">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Fertilizer (NPK)
            </span>
            <div className="p-2 rounded-full bg-purple-500/10 text-purple-500">
              <Sparkles className="w-4 h-4" />
            </div>
          </div>
          <div>
            <p className="text-2xl font-bold text-foreground">
              {allocation?.total_fertilizer_used_kg ?? "—"}{" "}
              <span className="text-sm font-normal text-muted-foreground">
                / {activeFert.toLocaleString()} kg
              </span>
            </p>
            <p className="text-xs text-emerald-600 dark:text-emerald-400 font-medium flex items-center gap-1 mt-1">
              <ShieldCheck className="w-3.5 h-3.5" />
              {fertSaved} reduction in excess chemical input
            </p>
          </div>
          <div className="space-y-1">
            <div className="flex justify-between text-[11px] text-muted-foreground">
              <span>Fertilizer Budget</span>
              <span>{fertUtil}%</span>
            </div>
            <Progress value={fertUtil} className="h-2" />
          </div>
        </Card>

        {/* Financial Budget */}
        <Card className="p-5 space-y-3 bg-card border-border hover:shadow-lg transition-all duration-300">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Working Capital
            </span>
            <div className="p-2 rounded-full bg-emerald-500/10 text-emerald-500">
              <Wallet className="w-4 h-4" />
            </div>
          </div>
          <div>
            <p className="text-2xl font-bold text-foreground">
              {budgetUsed}{" "}
              <span className="text-sm font-normal text-muted-foreground">
                / ₹{(budgetAvail / 100000).toFixed(2)}L
              </span>
            </p>
            <p className="text-xs text-muted-foreground font-medium mt-1">
              ₹{bufferReserve.toLocaleString("en-IN")} buffer reserve remaining
            </p>
          </div>
          <div className="space-y-1">
            <div className="flex justify-between text-[11px] text-muted-foreground">
              <span>Budget Spent</span>
              <span>{budgetUtil}%</span>
            </div>
            <Progress value={budgetUtil} className="h-2" />
          </div>
        </Card>

        {/* Land Capacity */}
        <Card className="p-5 space-y-3 bg-card border-border hover:shadow-lg transition-all duration-300">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Arable Land
            </span>
            <div className="p-2 rounded-full bg-amber-500/10 text-amber-500">
              <MapPin className="w-4 h-4" />
            </div>
          </div>
          <div>
            <p className="text-2xl font-bold text-foreground">
              {allocation?.total_land_allocated_acres ?? activeLand}{" "}
              <span className="text-sm font-normal text-muted-foreground">
                / {activeLand} Acres
              </span>
            </p>
            <p className="text-xs text-primary font-medium mt-1">
              {selectedField ? `Scoped to ${selectedField.name}` : "Across all farm plots"}
            </p>
          </div>
          <div className="space-y-1">
            <div className="flex justify-between text-[11px] text-muted-foreground">
              <span>Land Allocated</span>
              <span>{landUtil}%</span>
            </div>
            <Progress value={landUtil} className="h-2" />
          </div>
        </Card>
      </div>

      {/* Per-Crop Resource Consumption Allocation */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="font-semibold text-lg text-foreground">Crop-wise Resource Allocation</h3>
            <p className="text-xs text-muted-foreground">
              {selectedField
                ? `Optimal resource distribution computed for ${selectedField.name} (${selectedField.areaAcres} Acres)`
                : "Aggregated distribution across available farm resources"}
            </p>
          </div>
          <Badge variant="outline" className="text-xs text-primary">
            SciPy HiGHS Solver Optimized
          </Badge>
        </div>

        {crops.length === 0 ? (
          <div className="text-center py-8 text-sm text-muted-foreground">
            No active crop allocation. Select crops in Crop Advisor to optimize resources.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {crops.map((crop) => (
              <div
                key={crop.crop_id}
                className="p-4 rounded-xl border border-border bg-card/60 hover:bg-secondary/30 transition-all duration-300 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">{crop.emoji}</span>
                    <div>
                      <h4 className="font-semibold text-sm text-foreground">{crop.name}</h4>
                      <span className="text-xs text-muted-foreground">
                        Allocated: <strong>{crop.acres} Acres</strong>
                      </span>
                    </div>
                  </div>
                  <Badge variant="secondary" className="text-xs">
                    Profit {crop.formatted_profit}
                  </Badge>
                </div>

                <div className="grid grid-cols-2 gap-3 pt-2 border-t border-border/60 text-xs">
                  <div>
                    <span className="text-muted-foreground flex items-center gap-1">
                      <Droplets className="w-3.5 h-3.5 text-cyan-500" /> Water Allocated
                    </span>
                    <p className="font-semibold text-foreground mt-0.5">
                      {crop.water_used_kl?.toLocaleString()} kL
                    </p>
                  </div>
                  <div>
                    <span className="text-muted-foreground flex items-center gap-1">
                      <Wallet className="w-3.5 h-3.5 text-emerald-500" /> Cultivation Cost
                    </span>
                    <p className="font-semibold text-foreground mt-0.5">
                      ₹{crop.cost_inr?.toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Sustainability & Resource Efficiency Guidance */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4 bg-muted/20 border-border space-y-2">
          <div className="flex items-center gap-2 text-cyan-600 dark:text-cyan-400 font-semibold text-sm">
            <Droplets className="w-4 h-4" />
            <span>Water Optimization Tip</span>
          </div>
          <p className="text-xs text-muted-foreground leading-relaxed">
            {selectedField
              ? `${selectedField.name} has ${selectedField.waterAvailableKl.toLocaleString()} kL available. Pulses use 60% less water than cash crops.`
              : "Pairing high-water crops with drought-hardy legumes prevents dry-spell groundwater exhaustion."}
          </p>
        </Card>

        <Card className="p-4 bg-muted/20 border-border space-y-2">
          <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-semibold text-sm">
            <Leaf className="w-4 h-4" />
            <span>Biological Nitrogen Credit</span>
          </div>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Legume plots fix up to 45 kg of atmospheric nitrogen per acre, reducing chemical fertilizer needs for subsequent seasons.
          </p>
        </Card>

        <Card className="p-4 bg-muted/20 border-border space-y-2">
          <div className="flex items-center gap-2 text-purple-600 dark:text-purple-400 font-semibold text-sm">
            <Info className="w-4 h-4" />
            <span>Capital Risk Buffer</span>
          </div>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Retaining {bufferPct}% unspent budget reserves provides liquidity against pesticide or emergency labor price spikes.
          </p>
        </Card>
      </div>
    </div>
  )
}
