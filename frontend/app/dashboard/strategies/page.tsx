"use client"

import { Sidebar } from "@/components/dashboard/dashboard/sidebar"
import { Header } from "@/components/dashboard/dashboard/header"
import { AnalyticsContent } from "@/components/dashboard/analytics/analytics-content"
import { Button } from "@/components/ui/button"
import { useState } from "react"
import { toast } from "sonner"
import { useAuth } from "@/components/auth/AuthProvider"
import { apiCompareStrategies } from "@/lib/api"
import { useField } from "@/lib/field-context"

export default function StrategiesPage() {
  const { user } = useAuth()
  const { selectedField } = useField()
  const [exporting, setExporting] = useState(false)

  const handleExportReport = async () => {
    setExporting(true)
    try {
      const activeLand = selectedField ? selectedField.areaAcres : 10
      const activeWater = selectedField ? selectedField.waterAvailableKl : 16000
      const activeFert = selectedField ? selectedField.fertilizerAvailableKg : 1000
      const activeBudget = selectedField ? selectedField.budgetInr : 400000
      const activeCropIds =
        selectedField && selectedField.crops && selectedField.crops.length > 0
          ? selectedField.crops.map((c) => c.cropId.toLowerCase())
          : ["onion", "wheat", "chickpea", "mustard"]

      // Fetch live strategy comparison data scoped to field
      const res = await apiCompareStrategies({
        crop_ids: activeCropIds,
        total_land_acres: activeLand,
        water_available_kl: activeWater,
        fertilizer_available_kg: activeFert,
        total_budget_inr: activeBudget,
      })

      const strategies = res?.strategies ?? []
      const fieldTitle = selectedField ? selectedField.name : "All Farm Fields"

      const rows: string[][] = [
        ["Terra Strategy Comparison Report"],
        ["Generated", new Date().toLocaleString()],
        ["Farm Field", fieldTitle],
        ...(selectedField
          ? [
              ["Acreage", `${selectedField.areaAcres} Acres`],
              ["Soil Profile", selectedField.soilType],
              ["Location", selectedField.location],
            ]
          : []),
        [],
        ["Strategy", "Expected Profit", "Water Saved", "Fertilizer Saved", "Production", "Budget Used", "Status"],
        ...strategies.map((s) => [
          s.strategy,
          s.expected_profit_str,
          s.water_saved_str,
          s.fertilizer_saved_str,
          s.expected_production_str,
          s.budget_used_str,
          s.status,
        ]),
        [],
        ...strategies.flatMap((s) => [
          [`--- ${s.strategy} Crop Breakdown ---`],
          ["Crop", "Acres", "Expected Yield (q)", "Profit", "Water Used (kL)", "Cost"],
          ...s.crops.map((c) => [
            c.name,
            String(c.acres),
            String(c.expected_yield_q),
            c.formatted_profit,
            String(c.water_used_kl),
            `₹${c.cost_inr}`,
          ]),
          [],
        ]),
      ]

      const csv = rows.map((r) => r.join(",")).join("\n")
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" })
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      const slug = (selectedField?.name || "all-fields").toLowerCase().replace(/\s+/g, "-")
      a.download = `terra-${slug}-strategy-report-${new Date().toISOString().slice(0, 10)}.csv`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      toast.success(`Strategy report for ${fieldTitle} exported as CSV`)
    } catch {
      toast.error("Export failed. Check backend connection.")
    }
    setExporting(false)
  }

  return (
    <div className="flex min-h-screen bg-background">
      <div className="hidden lg:block">
        <Sidebar />
      </div>

      <main className="flex-1 p-4 lg:p-6 lg:ml-64">
        <Header
          title="Compare Strategies"
          description="Compare max-profit, water-saving, low-budget and balanced plans side by side."
          actions={
            <Button
              variant="outline"
              className="w-full sm:w-auto h-9 text-sm transition-all duration-300 hover:shadow-md hover:scale-105 bg-transparent"
              onClick={handleExportReport}
              disabled={exporting}
            >
              {exporting ? "Exporting…" : "Export Report"}
            </Button>
          }
        />

        <div className="mt-6">
          <AnalyticsContent />
        </div>
      </main>
    </div>
  )
}