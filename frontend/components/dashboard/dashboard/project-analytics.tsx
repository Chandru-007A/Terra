"use client"

import { Card } from "@/components/ui/card"
import { useState, useEffect } from "react"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts"
import { apiOptimizeAllocation } from "@/lib/api"
import { useField } from "@/lib/field-context"

export function ProjectAnalytics() {
  const { fields, selectedField } = useField()
  const [hoveredBar, setHoveredBar] = useState<number | null>(null)
  const [chartData, setChartData] = useState<any[]>([])
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
    async function loadLiveData() {
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
            day: c.name.split(" ")[0],
            value: Math.round(c.expected_profit_inr / 1000),
            label: `${c.name} · ${c.formatted_profit} (${c.acres} ac)`,
          }))
          setChartData(mapped)
        }
      } catch {
        if (isMounted) setChartData([])
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    loadLiveData()
    return () => {
      isMounted = false
    }
  }, [selectedField, activeLand, activeWater, activeFert, activeBudget])

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-foreground text-background px-3 py-2 rounded-lg text-xs font-semibold shadow-lg">
          <p className="font-bold">
            ₹
            {Number(payload[0].value) >= 100
              ? `${(Number(payload[0].value) / 100).toFixed(2)}L`
              : `${Number(payload[0].value).toLocaleString()}k`}
          </p>
          <p className="text-[10px] opacity-80">{payload[0].payload.label}</p>
        </div>
      )
    }
    return null
  }

  return (
    <Card
      className="p-6 transition-all duration-500 hover:shadow-xl animate-slide-in-up bg-gradient-to-br from-background to-muted/20"
      style={{ animationDelay: "400ms" }}
    >
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-foreground">Crop-wise Profit</h2>
          <p className="text-xs text-muted-foreground">
            {selectedField ? `Scoped to ${selectedField.name} (${selectedField.areaAcres} Acres)` : "All Farm Fields Allocation"}
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <div className="w-2 h-2 rounded-full bg-emerald-600"></div>
          <span>Profit per crop (₹ thousand)</span>
        </div>
      </div>

      <div className="h-64 mb-4 relative">
        {loading ? (
          <div className="h-full flex items-center justify-center text-xs text-muted-foreground">
            Calculating allocation...
          </div>
        ) : chartData.length === 0 ? (
          <div className="h-full flex items-center justify-center text-xs text-muted-foreground">
            No crop allocations available.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 20, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#10b981" />
                  <stop offset="100%" stopColor="#047857" />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="text-muted/20" />
              <XAxis
                dataKey="day"
                axisLine={false}
                tickLine={false}
                tick={{ fill: "currentColor", fontSize: 14 }}
                className="text-muted-foreground"
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fill: "currentColor", fontSize: 12 }}
                className="text-muted-foreground"
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: "transparent" }} />
              <Bar
                dataKey="value"
                fill="url(#barGradient)"
                radius={[12, 12, 12, 12]}
                maxBarSize={60}
                onMouseEnter={(data, index) => setHoveredBar(index)}
                onMouseLeave={() => setHoveredBar(null)}
              >
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={hoveredBar === index ? "#047857" : "url(#barGradient)"}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </Card>
  )
}
