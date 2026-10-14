"use client"

import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Droplets, Leaf, CloudSun } from "lucide-react"
import Link from "next/link"
import { useField } from "@/lib/field-context"

export function Reminders() {
  const { selectedField } = useField()

  const fieldName = selectedField?.name || "your farm"
  const soilType = selectedField?.soilType ? selectedField.soilType.toLowerCase() : "black soil"

  return (
    <Card
      className="p-6 transition-all duration-500 hover:shadow-xl animate-slide-in-up"
      style={{ animationDelay: "500ms" }}
    >
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-foreground">AI Recommendations</h2>
        {selectedField && (
          <span className="text-xs text-muted-foreground font-medium">{selectedField.name}</span>
        )}
      </div>

      <div className="space-y-4">
        <div className="bg-card border border-border rounded-xl p-4 transition-all duration-300 hover:shadow-lg hover:scale-[1.02]">
          <div className="flex items-start gap-3">
            <Droplets className="w-5 h-5 text-sky-600 mt-0.5" />
            <div>
              <h3 className="font-semibold text-foreground mb-1">
                {selectedField ? `Irrigation advice for ${selectedField.name}` : "Reduce irrigation by 25%"}
              </h3>
              <p className="text-sm text-muted-foreground">
                {selectedField
                  ? `Allocated pool: ${selectedField.waterAvailableKl.toLocaleString()} kL. Pair high-water crops with pulses to preserve groundwater.`
                  : "Rain expected in 2 days. Save roughly 800 kL this cycle."}
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3 mt-4">
            <Leaf className="w-5 h-5 text-emerald-600 mt-0.5" />
            <div>
              <h3 className="font-semibold text-foreground mb-1">
                {selectedField ? `Crop suitability for ${selectedField.name}` : "Sow onion this week"}
              </h3>
              <p className="text-sm text-muted-foreground">
                {selectedField
                  ? `Conditions calibrated for ${soilType} (${selectedField.areaAcres} acres). Check top AI recommended crops.`
                  : "Conditions are ideal for your black soil field."}
              </p>
            </div>
          </div>

          <Link href="/dashboard/crop-advisor" className="block w-full">
            <Button
              variant="outline"
              className="w-full mt-4 bg-transparent hover:bg-primary/10 hover:text-primary transition-all duration-300"
            >
              <CloudSun className="w-4 h-4 mr-2" />
              View 6 recommendations
            </Button>
          </Link>
        </div>
      </div>
    </Card>
  )
}
