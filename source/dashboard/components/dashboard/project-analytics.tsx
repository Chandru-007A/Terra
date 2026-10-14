"use client"

import { Card } from "@/components/ui/card"
import { useState } from "react"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts"

const chartData = [
  { day: "Onion", value: 222, label: "Onion · ₹2.22L" },
  { day: "Wheat", value: 69, label: "Wheat · ₹69,000" },
  { day: "Chickpea", value: 91, label: "Chickpea · ₹91,200" },
  { day: "Mustard", value: 21.5, label: "Mustard · ₹21,500" },
]

const barColors = ["#059669", "#047857", "#10b981", "#065f46"]

export function ProjectAnalytics() {
  const [hoveredBar, setHoveredBar] = useState<number | null>(null)
  const maxValue = Math.max(...chartData.map((d) => d.value))
  const average = chartData.reduce((acc, d) => acc + d.value, 0)

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-foreground text-background px-3 py-2 rounded-lg text-xs font-semibold shadow-lg">
          <p className="font-bold">₹{Number(payload[0].value) >= 100 ? `${(Number(payload[0].value) / 100).toFixed(2)}L` : `${Number(payload[0].value).toLocaleString()}k`}</p>
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
        <h2 className="text-xl font-semibold text-foreground">Crop-wise Profit</h2>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <div className="w-2 h-2 rounded-full bg-emerald-600"></div>
          <span>Profit per crop (₹ thousand)</span>
        </div>
      </div>

      <div className="h-64 mb-4 relative">
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
              ticks={[0, 50, 100, 150, 200, 250]}
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
                  fill={barColors[index]}
                  className="transition-all duration-300"
                  style={{
                    filter:
                      hoveredBar === index ? "brightness(1.2) drop-shadow(0 4px 8px rgba(5, 150, 105, 0.4))" : "none",
                    transformOrigin: "center bottom",
                  }}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Summary stats */}
      <div className="pt-4 border-t border-muted/50 flex items-center justify-between">
        <div className="text-sm">
          <span className="text-muted-foreground">Total profit: </span>
          <span className="font-semibold text-foreground">₹4.04L</span>
        </div>
        <div className="text-sm">
          <span className="text-muted-foreground">Best crop: </span>
          <span className="font-semibold text-emerald-600">Onion</span>
        </div>
      </div>
    </Card>
  )
}
