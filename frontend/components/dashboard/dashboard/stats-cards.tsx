"use client"

import { ArrowUpRight, TrendingUp } from "lucide-react"
import { Card } from "@/components/ui/card"
import { useEffect, useState } from "react"
import { apiOptimizeAllocation } from "@/lib/api"
import { useField } from "@/lib/field-context"

export function StatsCards() {
  const { fields, selectedField } = useField()
  const [hoveredCard, setHoveredCard] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [stats, setStats] = useState<any[]>([])

  // Aggregate or field-scoped values
  const totalArea = fields.reduce((sum, f) => sum + (f.areaAcres || 0), 0) || 10
  const totalWater = fields.reduce((sum, f) => sum + (f.waterAvailableKl || 0), 0) || 16000
  const totalFert = fields.reduce((sum, f) => sum + (f.fertilizerAvailableKg || 0), 0) || 1000
  const totalBudget = fields.reduce((sum, f) => sum + (f.budgetInr || 0), 0) || 400000

  const activeLand = selectedField ? selectedField.areaAcres : totalArea
  const activeWater = selectedField ? selectedField.waterAvailableKl : totalWater
  const activeFert = selectedField ? selectedField.fertilizerAvailableKg : totalFert
  const activeBudget = selectedField ? selectedField.budgetInr : totalBudget

  const activeCropIds =
    selectedField && selectedField.crops && selectedField.crops.length > 0
      ? selectedField.crops.map((c) => c.cropId.toLowerCase())
      : ["onion", "wheat", "chickpea", "mustard"]

  useEffect(() => {
    let isMounted = true
    async function fetchLiveAllocation() {
      try {
        setIsLoading(true)
        const res = await apiOptimizeAllocation({
          crop_ids: activeCropIds,
          total_land_acres: activeLand,
          water_available_kl: activeWater,
          fertilizer_available_kg: activeFert,
          total_budget_inr: activeBudget,
          strategy: selectedField?.activeStrategy?.toLowerCase() || "balanced",
        })
        if (isMounted && res && res.status === "Optimal") {
          const fieldTag = selectedField ? `for ${selectedField.name}` : "across all fields"
          setStats([
            {
              title: "Expected Profit",
              value: res.expected_profit_str,
              increase: `${res.profit_increase_percent}% LP optimized ${fieldTag}`,
              bgColor: "bg-primary",
              textColor: "text-primary-foreground",
              delay: "0ms",
            },
            {
              title: "Expected Production",
              value: res.expected_production_str,
              increase: `Across ${res.crops?.length || 0} crops (${activeLand} ac)`,
              bgColor: "bg-card",
              textColor: "text-foreground",
              delay: "100ms",
            },
            {
              title: "Water Unused",
              value: res.water_saved_str,
              increase: `${res.water_saved_percent}% of ${activeWater.toLocaleString()} kL pool unused`,
              bgColor: "bg-card",
              textColor: "text-foreground",
              delay: "200ms",
            },
            {
              title: "Budget Used",
              value: res.budget_used_str,
              subtitle: `of ₹${(activeBudget / 100000).toFixed(2)}L budget limit`,
              bgColor: "bg-card",
              textColor: "text-foreground",
              delay: "300ms",
            },
          ])
        }
      } catch {
        if (isMounted) {
          setStats([])
        }
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    fetchLiveAllocation()
    return () => {
      isMounted = false
    }
  }, [selectedField, activeLand, activeWater, activeFert, activeBudget])

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="bg-card text-foreground p-4 shadow-lg">
            <div className="animate-pulse">
              <div className="h-3 bg-muted rounded mb-3 w-1/2" />
              <div className="h-8 bg-muted rounded mb-2" />
              <div className="h-3 bg-muted rounded w-3/4" />
            </div>
          </Card>
        ))}
      </div>
    )
  }

  if (stats.length === 0) {
    return (
      <Card className="p-4 text-center text-xs text-muted-foreground">
        Unable to load live resource allocations. Verify backend connection.
      </Card>
    )
  }

  return (
    <div className="space-y-2">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {stats.map((stat, index) => (
          <Card
            key={stat.title}
            onMouseEnter={() => setHoveredCard(index)}
            onMouseLeave={() => setHoveredCard(null)}
            style={{ animationDelay: stat.delay }}
            className={`${stat.bgColor} ${stat.textColor} p-4 transition-all duration-500 ease-out animate-slide-in-up cursor-pointer ${
              hoveredCard === index ? "scale-105 shadow-2xl" : "shadow-lg"
            }`}
          >
            <div className="flex items-start justify-between mb-3">
              <h3 className="text-xs font-medium opacity-90">{stat.title}</h3>
              <div
                className={`w-6 h-6 rounded-full ${
                  stat.bgColor === "bg-primary" ? "bg-primary-foreground/20" : "bg-primary"
                } flex items-center justify-center transition-transform duration-300 ${
                  hoveredCard === index ? "rotate-45" : ""
                }`}
              >
                <ArrowUpRight
                  className={`w-3 h-3 ${stat.bgColor === "bg-primary" ? "text-primary-foreground" : "text-primary-foreground"}`}
                />
              </div>
            </div>
            <p className="text-3xl font-bold mb-2">{stat.value}</p>
            <div className="flex items-center gap-1.5 text-xs opacity-80">
              {stat.increase && (
                <>
                  <TrendingUp className="w-3 h-3" />
                  <span>{stat.increase}</span>
                </>
              )}
              {stat.subtitle && <span>{stat.subtitle}</span>}
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
