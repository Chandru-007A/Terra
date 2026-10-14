"use client"

import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Plus } from "lucide-react"
import { useState, useEffect } from "react"
import { apiOptimizeAllocation } from "@/lib/api"
import { useField } from "@/lib/field-context"
import Link from "next/link"

export function TeamCollaboration() {
  const { fields, selectedField } = useField()
  const [members, setMembers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

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
    async function loadLiveAllocation() {
      try {
        setLoading(true)
        const res = await apiOptimizeAllocation({
          crop_ids: activeCropIds,
          total_land_acres: activeLand,
          water_available_kl: activeWater,
          fertilizer_available_kg: activeFert,
          total_budget_inr: activeBudget,
          strategy: selectedField?.activeStrategy?.toLowerCase() || "balanced",
        })
        if (isMounted && res && res.crops && res.crops.length > 0) {
          const mapped = res.crops.map((c) => ({
            name: c.name,
            task: `${c.formatted_profit} expected profit · ${Math.round(c.profit_margin_percent)}% margin · ${c.acres} acres`,
            status: c.status || (c.acres >= 2.0 ? "Recommended" : "Stable"),
            statusColor:
              c.acres >= 2.0
                ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
                : "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
            avatar: c.emoji || "🌱",
          }))
          setMembers(mapped)
        }
      } catch {
        if (isMounted) setMembers([])
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    loadLiveAllocation()
    return () => {
      isMounted = false
    }
  }, [selectedField, activeLand, activeWater, activeFert, activeBudget])

  return (
    <Card
      className="p-6 transition-all duration-500 hover:shadow-xl animate-slide-in-up"
      style={{ animationDelay: "600ms" }}
    >
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-foreground">Crop Strategy Overview</h2>
          <p className="text-xs text-muted-foreground">
            {selectedField ? `Allocation scoped to ${selectedField.name}` : "Overview across all fields"}
          </p>
        </div>
        <Link href="/dashboard/crop-advisor">
          <Button variant="outline" size="sm" className="transition-all duration-300 hover:scale-105 bg-transparent">
            <Plus className="w-4 h-4 mr-1" />
            Add Crop
          </Button>
        </Link>
      </div>

      {loading ? (
        <div className="text-center py-6 text-xs text-muted-foreground">
          Loading crop strategy...
        </div>
      ) : members.length === 0 ? (
        <div className="text-center py-6 text-xs text-muted-foreground">
          No crop strategy active. Add crops or apply a strategy.
        </div>
      ) : (
        <div className="space-y-4">
          {members.map((member, index) => (
            <div
              key={member.name}
              className="flex items-center gap-4 p-3 rounded-lg hover:bg-secondary transition-all duration-300 cursor-pointer group"
              style={{ animationDelay: `${700 + index * 100}ms` }}
            >
              <Avatar className="w-10 h-10 border border-primary/20 transition-transform duration-300 group-hover:scale-110">
                <AvatarFallback className="text-base">{member.avatar}</AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-foreground text-sm truncate">{member.name}</p>
                <p className="text-xs text-muted-foreground truncate">{member.task}</p>
              </div>
              <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${member.statusColor}`}>
                {member.status}
              </span>
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}
